"""Deterministic exact-match grading for RetrySafe trace tasks."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

EVENT_FIELDS = ("event_id", "http_status", "response_observed", "business_effect_delta", "external_effect_delta", "response_ref")

def _same_typed_value(actual: Any, expected: Any) -> bool:
    return type(actual) is type(expected) and actual == expected

def load_tasks(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("scoring", {}).get("total_points") != 100 or len(data.get("tasks", [])) != 8:
        raise ValueError("Expected eight tasks totaling 100 points")
    seen = set()
    total = 0
    for task in data["tasks"]:
        if task["id"] in seen: raise ValueError(f"Duplicate task id {task['id']}")
        seen.add(task["id"])
        if set(task["expected"]) != {"event_results", "final_state"}: raise ValueError(f"Bad reference fields for {task['id']}")
        if [e["event_id"] for e in task["expected"]["event_results"]] != task["event_ids"]: raise ValueError(f"Bad reference event order for {task['id']}")
        if any(set(e) != set(EVENT_FIELDS) for e in task["expected"]["event_results"]): raise ValueError(f"Bad event schema for {task['id']}")
        if set(task["points"]) != {"event_trace", "final_state"}: raise ValueError(f"Bad point fields for {task['id']}")
        total += sum(task["points"].values())
    if total != 100: raise ValueError(f"Task weights total {total}, expected 100")
    return data

def parse_json_answer(raw: str) -> Any:
    if not isinstance(raw, str): raise json.JSONDecodeError("Answer must be text", str(raw), 0)
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) < 3 or not lines[0].startswith("```") or lines[-1].strip() != "```": raise json.JSONDecodeError("Expected one complete code fence", text, 0)
        text = "\n".join(lines[1:-1]).strip()
    return json.loads(text)

def grade_answer(task: dict[str, Any], answer: Any) -> dict[str, Any]:
    max_score = sum(task["points"].values())
    if not isinstance(answer, dict): return {"parseable": False, "task_id_match": False, "score": 0, "max_score": max_score, "field_scores": {}}
    id_match = answer.get("task_id") == task["id"]
    expected = task["expected"]
    expected_top = {"task_id", "event_results", "final_state", "explanation"}
    answer_events = answer.get("event_results")
    schema_valid = (set(answer) == expected_top and isinstance(answer.get("explanation"), str)
                    and isinstance(answer_events, list)
                    and len(answer_events) == len(expected["event_results"])
                    and all(isinstance(row, dict) and set(row) == set(EVENT_FIELDS) for row in answer_events)
                    and isinstance(answer.get("final_state"), dict)
                    and set(answer["final_state"]) == set(expected["final_state"]))
    if not schema_valid:
        return {"parseable": True, "task_id_match": id_match, "schema_valid": False,
                "score": 0, "max_score": max_score, "field_scores": {}}
    trace_points = task["points"]["event_trace"]
    state_points = task["points"]["final_state"]
    trace_fields = len(task["event_ids"]) * len(EVENT_FIELDS)
    event_correct = 0
    event_detail = []
    candidate_events = answer_events
    if isinstance(candidate_events, list):
        for index, reference in enumerate(expected["event_results"]):
            candidate = candidate_events[index] if index < len(candidate_events) and isinstance(candidate_events[index], dict) else {}
            field_ok = {key: _same_typed_value(candidate.get(key), reference[key]) for key in EVENT_FIELDS}
            event_correct += sum(field_ok.values())
            event_detail.append({"event_id": reference["event_id"], "fields": field_ok})
    state_ref = expected["final_state"]
    state = answer.get("final_state")
    state_fields = {key: isinstance(state, dict) and _same_typed_value(state.get(key), value) for key, value in state_ref.items()}
    trace_score = trace_points * event_correct / trace_fields if trace_fields else 0
    state_score = state_points * sum(state_fields.values()) / len(state_fields) if state_fields else 0
    if not id_match: trace_score = state_score = 0
    return {"parseable": True, "task_id_match": id_match, "schema_valid": True, "score": round(trace_score + state_score, 4), "max_score": max_score,
            "field_scores": {"event_trace": {"score": round(trace_score, 4), "max_score": trace_points, "correct_fields": event_correct, "total_fields": trace_fields, "events": event_detail},
                             "final_state": {"score": round(state_score, 4), "max_score": state_points, "fields": state_fields}}}
