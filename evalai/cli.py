"""Command line tools for a no-API EvalAI evaluation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

from .grader import grade_answer, load_tasks
from .runner import analyze_jsonl, export_prompts, grade_partial_transcripts, grade_transcripts


ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evalai", description="Run EvalAI without model APIs")
    sub = parser.add_subparsers(dest="command", required=True)
    prompts = sub.add_parser("prompts", help="export the task prompts for a model chat UI")
    prompts.add_argument("--output", default="work/prompts.md")
    capture = sub.add_parser("capture", help="paste genuine UI answers into a local JSONL transcript file")
    capture.add_argument("--output", default="work/ui_outputs-v2.1.0.jsonl")
    capture.add_argument("--provider", default="Gemini", help="UI name, e.g. Gemini")
    capture.add_argument("--model", default="Gemini 3.8 Flash", help="model label/version displayed by the UI")
    capture.add_argument("--settings", default="Default web UI settings", help="sampling settings shown by the UI, or state that they are not exposed")
    capture.add_argument("--trials-per-task", type=int, default=3)
    grade = sub.add_parser("grade", help="score captured model UI transcripts")
    grade.add_argument("--input", required=True)
    grade.add_argument("--output", default="results/gemini-run.jsonl")
    grade.add_argument("--provider", default="Gemini")
    grade.add_argument("--model", default="Gemini 3.8 Flash")
    grade.add_argument("--trials-per-task", type=int, default=3)
    partial = sub.add_parser("grade-partial", help="grade captured genuine responses without claiming a full run")
    partial.add_argument("--input", required=True)
    partial.add_argument("--output", required=True)
    partial.add_argument("--provider", default="Gemini")
    partial.add_argument("--model", default="Gemini 3.8 Flash")
    check = sub.add_parser("self-check", help="offline answer-key and grader sanity check")
    check.add_argument("--tasks", default=str(ROOT / "data" / "tasks.json"))
    analyze = sub.add_parser("analyze", help="summarize a saved run by task, field, and pass^k")
    analyze.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    tasks_path = getattr(args, "tasks", str(ROOT / "data" / "tasks.json"))
    data = load_tasks(tasks_path)
    if args.command == "self-check":
        errors = []
        checked_fields = 0
        for task in data["tasks"]:
            reference = {"task_id": task["id"], **task["expected"], "explanation": "offline reference"}
            if grade_answer(task, reference)["score"] != 12.5:
                errors.append(f"{task['id']}: reference solution did not earn full credit")
            for event_index, event in enumerate(task["expected"]["event_results"]):
                for field, value in event.items():
                    wrong = json.loads(json.dumps(reference))
                    wrong["event_results"][event_index][field] = ("__wrong__" if value != "__wrong__" else "__wrong_2__")
                    checked_fields += 1
                    if grade_answer(task, wrong)["score"] == 12.5:
                        errors.append(f"{task['id']} {event['event_id']}.{field}: incorrect value earned full credit")
            for field, value in task["expected"]["final_state"].items():
                wrong = json.loads(json.dumps(reference))
                wrong["final_state"][field] = ("__wrong__" if value != "__wrong__" else "__wrong_2__")
                checked_fields += 1
                if grade_answer(task, wrong)["score"] == 12.5:
                    errors.append(f"{task['id']} final_state.{field}: incorrect value earned full credit")
        result = {"tasks": len(data["tasks"]), "total_points": data["scoring"]["total_points"],
                  "reference_solutions_pass": not any("reference solution" in e for e in errors),
                  "individual_scored_fields_checked": checked_fields,
                  "deliberately_wrong_values_rejected": not any("incorrect value" in e for e in errors),
                  "errors": errors}
        print(json.dumps(result, indent=2))
        return 1 if errors else 0
    try:
        if args.command == "prompts":
            export_prompts(data["tasks"], args.output)
            print(json.dumps({"prompts_file": args.output, "tasks": len(data["tasks"]),
                              "api_calls": 0}, indent=2))
        elif args.command == "capture":
            if args.trials_per_task < 1:
                parser.error("--trials-per-task must be positive")
            if not args.provider.strip() or not args.model.strip():
                parser.error("--provider and --model must identify the chat UI and model label")
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("x", encoding="utf-8", newline="\n") as handle:
                print("Paste each model's visible answer copied from its normal chat UI. Type END on its own line to finish each response.")
                for task in data["tasks"]:
                    for trial in range(1, args.trials_per_task + 1):
                        print(f"\n{task['id']} trial {trial}/{args.trials_per_task} — {task['title']}")
                        lines = []
                        while True:
                            line = input()
                            if line == "END":
                                break
                            lines.append(line)
                        handle.write(json.dumps({"task_id": task["id"], "run_index": trial,
                                                 "provider": args.provider, "model_id": args.model,
                                                 "sampling_settings": args.settings,
                                                 "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                                                 "raw_model_output": "\n".join(lines)}, ensure_ascii=False) + "\n")
                        handle.flush()
            print(json.dumps({"transcripts_file": str(out), "tasks": len(data["tasks"]),
                              "trials_per_task": args.trials_per_task, "api_calls": 0}, indent=2))
        elif args.command == "grade":
            if not args.provider.strip() or not args.model.strip():
                parser.error("--provider and --model must identify the chat UI and model label")
            summary = grade_transcripts(data["tasks"], input_path=args.input, output_path=args.output,
                                        provider=args.provider, model=args.model,
                                        trials_per_task=args.trials_per_task,
                                        benchmark_version=data["version"])
            print(json.dumps(summary, indent=2))
        elif args.command == "grade-partial":
            if not args.provider.strip() or not args.model.strip():
                parser.error("--provider and --model must identify the chat UI and model label")
            summary = grade_partial_transcripts(data["tasks"], benchmark_version=data["version"],
                                                input_path=args.input, output_path=args.output,
                                                provider=args.provider, model=args.model)
            print(json.dumps(summary, indent=2))
        else:
            print(json.dumps(analyze_jsonl(args.input), indent=2))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0
