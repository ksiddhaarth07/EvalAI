import builtins
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evalai.cli import main
from evalai.grader import grade_answer, load_tasks, parse_json_answer
from evalai.runner import analyze_jsonl, build_prompt, export_prompts, grade_partial_transcripts, grade_transcripts


ROOT = Path(__file__).resolve().parents[1]


class GraderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_tasks(str(ROOT / "data" / "tasks.json"))

    def test_task_set_has_eight_tasks_and_one_hundred_points(self):
        self.assertEqual(len(self.data["tasks"]), 8)
        self.assertEqual(sum(sum(t["points"].values()) for t in self.data["tasks"]), 100)

    def test_every_reference_answer_gets_full_credit(self):
        for task in self.data["tasks"]:
            answer = {"task_id": task["id"], **task["expected"], "explanation": "reference"}
            self.assertEqual(grade_answer(task, answer)["score"], 12.5, task["id"])

    def test_deliberately_wrong_value_in_every_field_is_penalized(self):
        for task in self.data["tasks"]:
            reference = {"task_id": task["id"], **task["expected"], "explanation": "reference"}
            for field in task["expected"]:
                wrong = {**reference, field: "intentionally_incorrect"}
                self.assertLess(grade_answer(task, wrong)["score"], 12.5, f"{task['id']} {field}")

    def test_wrong_event_field_loses_its_share_of_trace_weight(self):
        task = self.data["tasks"][0]
        answer = json.loads(json.dumps({"task_id": task["id"], **task["expected"], "explanation": "reference"}))
        answer["event_results"] = [dict(item) for item in task["expected"]["event_results"]]
        answer["event_results"][0]["http_status"] = 500
        result = grade_answer(task, answer)
        self.assertLess(result["score"], 12.5)
        self.assertEqual(result["field_scores"]["event_trace"]["correct_fields"], 11)
        self.assertEqual(result["field_scores"]["final_state"]["score"], 3.5)

    def test_non_object_answer_scores_zero(self):
        result = grade_answer(self.data["tasks"][0], ["not", "an", "object"])
        self.assertFalse(result["parseable"])
        self.assertEqual(result["score"], 0)

    def test_wrong_task_id_scores_zero(self):
        task = self.data["tasks"][0]
        answer = {"task_id": "RS02", **task["expected"]}
        result = grade_answer(task, answer)
        self.assertFalse(result["task_id_match"])
        self.assertEqual(result["score"], 0)

    def test_schema_violations_do_not_receive_a_partial_pass(self):
        task = self.data["tasks"][0]
        answer = json.loads(json.dumps({"task_id": task["id"], **task["expected"], "explanation": "reference"}))
        answer["event_results"].append(dict(answer["event_results"][0]))
        result = grade_answer(task, answer)
        self.assertFalse(result["schema_valid"])
        self.assertEqual(result["score"], 0)

    def test_json_parser_accepts_fenced_and_plain_json(self):
        self.assertEqual(parse_json_answer('```json\n{"a":1}\n```'), {"a": 1})
        self.assertEqual(parse_json_answer('{"b":2}'), {"b": 2})

    def test_json_parser_rejects_extra_or_multiple_candidate_answers(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_json_answer('Answer: {"b":2} thanks')
        with self.assertRaises(json.JSONDecodeError):
            parse_json_answer('```json\n{"a":1}\n```\n```json\n{"a":2}\n```')

    def test_json_parser_rejects_invalid_output(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_json_answer("no JSON here")

    def test_prompt_export_does_not_include_reference_answers(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as tmp:
            path = Path(tmp) / "prompts.md"
            export_prompts(self.data["tasks"], str(path))
            content = path.read_text(encoding="utf-8")
        self.assertIn("RS01", content)
        self.assertIn("RS08", content)
        self.assertNotIn("rationale_key", content)
        self.assertNotIn('"expected":', content)
        self.assertIn(build_prompt(self.data["tasks"][0]), content)

    def test_capture_cli_records_ui_outputs_without_network(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as tmp:
            output = Path(tmp) / "ui.jsonl"
            typed = []
            for task in self.data["tasks"]:
                for _trial in range(3):
                    raw = json.dumps({"task_id": task["id"], **task["expected"], "explanation": "fixture"}, indent=2)
                    typed.extend(raw.splitlines() + ["END"])
            with patch.object(builtins, "input", side_effect=typed), patch("sys.stdout", new_callable=io.StringIO):
                exit_code = main(["capture", "--output", str(output), "--provider", "Test UI",
                                  "--model", "test-only fixture", "--settings", "fixture defaults",
                                  "--trials-per-task", "3"])
            records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(records), 24)
        self.assertEqual(records[0]["provider"], "Test UI")
        self.assertEqual(records[0]["sampling_settings"], "fixture defaults")
        self.assertTrue(records[0]["captured_at_utc"])
        self.assertIn("\n", records[0]["raw_model_output"])
        self.assertEqual(records[-1]["task_id"], "RS08")

    def _write_ui_fixture(self, path: Path, *, wrong_first: bool = False, malformed_one: bool = False):
        with path.open("w", encoding="utf-8") as handle:
            for task in self.data["tasks"]:
                for trial in range(1, 4):
                    answer = json.loads(json.dumps({"task_id": task["id"], **task["expected"], "explanation": "test fixture only"}))
                    if wrong_first and task["id"] == "RS01" and trial == 1:
                        answer["event_results"][0]["http_status"] = 500
                    item = {"task_id": task["id"], "run_index": trial,
                            "raw_model_output": "not valid JSON" if malformed_one and task["id"] == "RS02" and trial == 1 else json.dumps(answer)}
                    handle.write(json.dumps(item) + "\n")

    def test_transcript_grading_preserves_outputs_and_computes_pass_power_k(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as tmp:
            source, output = Path(tmp) / "ui.jsonl", Path(tmp) / "graded.jsonl"
            self._write_ui_fixture(source, wrong_first=True, malformed_one=True)
            first_raw = json.loads(source.read_text(encoding="utf-8").splitlines()[0])["raw_model_output"]
            summary = grade_transcripts(self.data["tasks"], input_path=str(source),
                                        output_path=str(output), provider="UI fixture",
                                        model="test-only fixture", trials_per_task=3)
            records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            analysis = analyze_jsonl(str(output))
        self.assertEqual(summary["responses"], 24)
        self.assertEqual(records[0]["raw_model_output"], first_raw)
        self.assertLess(records[0]["grade"]["score"], 12.5)
        self.assertEqual(records[3]["grade"]["score"], 0)
        self.assertIn("parse_error", records[3])
        self.assertEqual(analysis["task_analysis"][1]["errors"], 1)
        self.assertEqual(analysis["pass_power_k_percent"], 75.0)
        self.assertEqual(analysis["task_analysis"][0]["pass_all_trials"], False)
        spread = analysis["trial_score_spread"]
        self.assertEqual(set(spread), {"min_percent", "max_percent", "population_sd_percentage_points"})
        self.assertLess(spread["min_percent"], spread["max_percent"])

    def test_transcript_grader_rejects_incomplete_trials(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as tmp:
            source, output = Path(tmp) / "ui.jsonl", Path(tmp) / "graded.jsonl"
            source.write_text(json.dumps({"task_id": "RS01", "run_index": 1,
                                          "raw_model_output": "{}"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "needs exactly"):
                grade_transcripts(self.data["tasks"], input_path=str(source),
                                  output_path=str(output), provider="UI", model="fixture",
                                  trials_per_task=3)

    def test_partial_grader_preserves_and_scores_captured_response(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as tmp:
            source, output = Path(tmp) / "partial.jsonl", Path(tmp) / "graded.jsonl"
            task = self.data["tasks"][0]
            answer = json.loads(json.dumps({"task_id": task["id"], **task["expected"], "explanation": "pilot"}))
            answer["event_results"][1]["http_status"] = 200
            raw = json.dumps(answer)
            source.write_text(json.dumps({"task_id": task["id"], "run_index": 1,
                                          "provider": "Chat UI", "model_id": "visible label",
                                          "raw_model_output": raw}) + "\n", encoding="utf-8")
            summary = grade_partial_transcripts(self.data["tasks"], benchmark_version=self.data["version"],
                                                input_path=str(source), output_path=str(output),
                                                provider="Chat UI", model="visible label")
            record = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(summary["responses"], 1)
        self.assertEqual(summary["mean_score_percent_of_captured_responses"], 94.0)
        self.assertEqual(record["raw_model_output"], raw)
        self.assertEqual(record["benchmark_version"], "2.1.0")
        self.assertTrue(record["grading_mode"].startswith("partial"))
        self.assertEqual(record["grade"]["score"], 11.75)

    def test_analyzer_does_not_report_pass_power_k_for_partial_task_set(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as tmp:
            path = Path(tmp) / "partial.jsonl"
            path.write_text(json.dumps({"task_id": "RS01", "grade": {"score": 12.5, "max_score": 12.5,
                                "field_scores": {"event_trace": {"score": 9, "max_score": 9},
                                                 "final_state": {"score": 3.5, "max_score": 3.5}}}}) + "\n",
                            encoding="utf-8")
            result = analyze_jsonl(str(path))
        self.assertIsNone(result["pass_power_k_trials_per_task"])
        self.assertIsNone(result["pass_power_k_percent"])


if __name__ == "__main__":
    unittest.main()
