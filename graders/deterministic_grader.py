"""Deterministic exact-match grader interface for EvalAI.

Exports the core grading functions and enforces strict schema, exact typing,
and equal point distribution across events and state counters.
"""
from evalai.grader import EVENT_FIELDS, grade_answer, load_tasks, parse_json_answer

__all__ = ["EVENT_FIELDS", "grade_answer", "load_tasks", "parse_json_answer"]

