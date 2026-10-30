"""Copy-ready prompt export and grading for manually captured model UI trials."""
from __future__ import annotations

import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .grader import grade_answer, parse_json_answer


SYSTEM_PROMPT = """Treat each scenario's stated contract as authoritative. Return only one JSON object with task_id, event_results, final_state, and explanation. Include one event_results object for every event in order. Each event object must have event_id, http_status (the actual HTTP status only when the scenario establishes it, otherwise null), response_observed (whether that event's caller or worker observed a response), business_effect_delta (integer), external_effect_delta (integer), and response_ref (string or null). Include exactly the named final_state values requested. No Markdown or extra keys. Explanation is a brief causal summary."""


def build_prompt(task: dict[str, Any]) -> str:
    return (f"Instructions:\n{SYSTEM_PROMPT}\n\n"
            f"Task ID: {task['id']}\nScenario: {task['prompt']}\n"
            f"Return one JSON object. task_id must be {task['id']}.")


def export_prompts(tasks: list[dict[str, Any]], output: str) -> None:
    """Write prompts for use in a model's normal chat interface; no model is contacted."""
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write("# RetrySafe prompts\n\n")
        handle.write("Each block is a complete single-message prompt. Run every trial in a fresh chat with no prior task context. Paste one whole block as one message. Do not show the model the answer key. Repeat each task for the declared number of trials.\n")
        for task in tasks:
            prompt = build_prompt(task)
            handle.write(f"\n## {task['id']} — {task['title']}\n\n")
            handle.write("```text\n" + prompt + "\n```\n")


def grade_transcripts(tasks: list[dict[str, Any]], *, input_path: str, output_path: str,
                      provider: str, model: str, trials_per_task: int,
                      benchmark_version: str = "2.1.0") -> dict[str, Any]:
    """Score exact raw outputs copied from genuine model UI trials; never generates output."""
    if trials_per_task < 1:
        raise ValueError("trials_per_task must be positive")
    by_id = {task["id"]: task for task in tasks}
    items: list[dict[str, Any]] = []
    with open(input_path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid input JSONL at line {line_number}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Input line {line_number} must be a JSON object")
            task_id = item.get("task_id")
            if task_id not in by_id:
                raise ValueError(f"Input line {line_number}: unknown task_id {task_id!r}")
            raw = item.get("raw_model_output")
            if not isinstance(raw, str):
                raise ValueError(f"Input line {line_number}: raw_model_output must be a string")
            run_index = item.get("run_index")
            if not isinstance(run_index, int) or not 1 <= run_index <= trials_per_task:
                raise ValueError(f"Input line {line_number}: run_index must be 1..{trials_per_task}")
            items.append({**item, "task_id": task_id, "raw_model_output": raw, "run_index": run_index})
    if not items:
        raise ValueError("Input file contains no model responses")
    counts = Counter(item["task_id"] for item in items)
    mismatched = {task_id: counts.get(task_id, 0) for task_id in by_id
                  if counts.get(task_id, 0) != trials_per_task}
    if mismatched:
        raise ValueError(f"Each of the {len(by_id)} tasks needs exactly {trials_per_task} trials; actual counts: {mismatched}")
    run_keys = [(item["task_id"], item["run_index"]) for item in items]
    if len(run_keys) != len(set(run_keys)):
        raise ValueError("Duplicate task_id/run_index pair in input")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    total_score = 0.0
    with out.open("x", encoding="utf-8", newline="\n") as handle:
        for item in items:
            task = by_id[item["task_id"]]
            record: dict[str, Any] = {
                "timestamp_utc": item.get("timestamp_utc") or item.get("captured_at_utc") or datetime.now(timezone.utc).isoformat(),
                "captured_at_utc": item.get("captured_at_utc"),
                "benchmark": "RetrySafe", "benchmark_version": benchmark_version,
                "task_id": task["id"], "run_index": item["run_index"],
                "provider": item.get("provider") or provider,
                "model_id": item.get("model_id") or model,
                "sampling_settings": item.get("sampling_settings", "Not exposed by UI"),
                "prompt": build_prompt(task), "raw_model_output": item["raw_model_output"]
            }
            try:
                answer = parse_json_answer(item["raw_model_output"])
                record["parsed_answer"] = answer
                grade = grade_answer(task, answer)
                record["grade"] = grade
                total_score += grade["score"]
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                record["parse_error"] = str(exc)
                record["grade"] = grade_answer(task, None)
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    possible = 12.5 * len(items)
    return {"output": str(out), "provider": provider, "model_id": model,
            "tasks": len(by_id), "trials_per_task": trials_per_task, "responses": len(items),
            "score_points": round(total_score, 2), "possible_points": round(possible, 2),
            "score_percent": round(100 * total_score / possible, 2)}


def grade_partial_transcripts(tasks: list[dict[str, Any]], *, benchmark_version: str,
                              input_path: str, output_path: str,
                              provider: str, model: str) -> dict[str, Any]:
    """Grade genuine captured rows without claiming a complete benchmark run."""
    by_id = {task["id"]: task for task in tasks}
    seen: set[tuple[str, int]] = set()
    items: list[dict[str, Any]] = []
    with open(input_path, encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid input JSONL at line {line_number}: {exc}") from exc
            if not isinstance(item, dict) or item.get("task_id") not in by_id:
                raise ValueError(f"Input line {line_number}: unknown or missing task_id")
            run_index = item.get("run_index")
            if type(run_index) is not int or run_index < 1:
                raise ValueError(f"Input line {line_number}: run_index must be a positive integer")
            key = (item["task_id"], run_index)
            if key in seen:
                raise ValueError(f"Duplicate task_id/run_index pair: {key}")
            seen.add(key)
            if not isinstance(item.get("raw_model_output"), str):
                raise ValueError(f"Input line {line_number}: raw_model_output must be text")
            items.append(item)
    if not items:
        raise ValueError("Input file contains no model responses")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    total_score = 0.0
    possible = 0.0
    with out.open("x", encoding="utf-8", newline="\n") as handle:
        for item in items:
            task = by_id[item["task_id"]]
            record: dict[str, Any] = {
                "benchmark": "RetrySafe", "benchmark_version": benchmark_version,
                "grading_mode": "partial; not a complete benchmark run",
                "task_id": task["id"], "run_index": item["run_index"],
                "provider": item.get("provider") or provider,
                "model_id": item.get("model_id") or model,
                "sampling_settings": item.get("sampling_settings", "Not exposed by UI"),
                "captured_at_utc": item.get("captured_at_utc"),
                "prompt": build_prompt(task), "raw_model_output": item["raw_model_output"]
            }
            try:
                answer = parse_json_answer(item["raw_model_output"])
                record["parsed_answer"] = answer
                grade = grade_answer(task, answer)
                record["grade"] = grade
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                record["parse_error"] = str(exc)
                record["grade"] = grade_answer(task, None)
                grade = record["grade"]
            total_score += grade["score"]
            possible += grade["max_score"]
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"output": str(out), "grading_mode": "partial; not a complete benchmark run",
            "responses": len(items), "score_points": round(total_score, 2),
            "possible_points": round(possible, 2),
            "mean_score_percent_of_captured_responses": round(100 * total_score / possible, 2)}


def analyze_jsonl(path: str) -> dict[str, Any]:
    """Report total score, field/task accuracy, and strict pass^k across trials."""
    records = []
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
    if not records:
        raise ValueError("No run records found")
    fields = ("event_trace", "final_state")
    task_stats: dict[str, dict[str, Any]] = {}
    field_stats = {field: {"correct": 0, "attempts": 0} for field in fields}
    score_sum = 0.0
    max_sum = 0.0
    full_trial_passes = 0
    for record in records:
        task_id = record.get("task_id", "UNKNOWN")
        stats = task_stats.setdefault(task_id, {"attempts": 0, "score_points": 0.0, "full_passes": 0, "errors": 0})
        stats["attempts"] += 1
        grade = record.get("grade")
        if record.get("parse_error") or not isinstance(grade, dict):
            grade = {"score": 0, "max_score": 12.5, "field_scores": {}}
            stats["errors"] += 1
        score = float(grade.get("score", 0))
        score_sum += score
        max_sum += float(grade.get("max_score", 12.5))
        stats["score_points"] += score
        stats["full_passes"] += int(score == 12.5)
        full_trial_passes += int(score == 12.5)
        for field in fields:
            item = grade.get("field_scores", {}).get(field)
            correct = bool(item and item.get("score") == item.get("max_score")) if isinstance(item, dict) else False
            field_stats[field]["attempts"] += 1
            field_stats[field]["correct"] += int(correct)
    task_rows = []
    for task_id, stats in sorted(task_stats.items()):
        n = stats["attempts"]
        task_rows.append({"task_id": task_id, "trials": n, "errors": stats["errors"],
                          "mean_points_out_of_12_5": round(stats["score_points"] / n, 2),
                          "pass_rate_percent": round(100 * stats["full_passes"] / n, 2),
                          "pass_all_trials": stats["full_passes"] == n})
    for stats in field_stats.values():
        stats["accuracy_percent"] = round(100 * stats["correct"] / stats["attempts"], 2)
    trial_counts = {row["trials"] for row in task_rows}
    pass_power_k_eligible = len(task_rows) == 8 and len(trial_counts) == 1
    return {"trials": len(records), "tasks_observed": len(task_stats),
            "score_points": round(score_sum, 2), "possible_points": round(max_sum, 2),
            "mean_score_percent": round(100 * score_sum / max_sum, 2),
            "trial_score_spread": {"min_percent": round(100 * min(float(r.get("grade", {}).get("score", 0)) / float(r.get("grade", {}).get("max_score", 12.5)) for r in records), 2),
                                   "max_percent": round(100 * max(float(r.get("grade", {}).get("score", 0)) / float(r.get("grade", {}).get("max_score", 12.5)) for r in records), 2),
                                   "population_sd_percentage_points": round(100 * statistics.pstdev(float(r.get("grade", {}).get("score", 0)) / float(r.get("grade", {}).get("max_score", 12.5)) for r in records), 2)},
            "full_task_pass_rate_percent": round(100 * full_trial_passes / len(records), 2),
            "pass_power_k_trials_per_task": next(iter(trial_counts)) if pass_power_k_eligible else None,
            "pass_power_k_percent": round(100 * sum(r["pass_all_trials"] for r in task_rows) / len(task_rows), 2) if pass_power_k_eligible else None,
            "k_definition": "A task passes pass^k only if all k independent trials earn full task credit; benchmark pass^k is the share of tasks meeting that condition.",
            "field_analysis": field_stats, "task_analysis": task_rows}
