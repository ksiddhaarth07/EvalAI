# EvalAI Grader Architecture

EvalAI uses a **purely deterministic, exact-match code grader** rather than an LLM judge:

- **Module**: `evalai/grader.py` and `graders/deterministic_grader.py`
- **Scoring**:
  - `event_trace`: 9.0 points distributed equally across all fields ($N_{\text{events}} \times 6$)
  - `final_state`: 3.5 points distributed equally across all named state counters
- **Strict Verification**:
  - Exact JSON data type match (`int` vs `float` vs `str` vs `bool` vs `null`)
  - Full schema matching (rejects extraneous keys or missing keys)
  - Requires single JSON object or single complete code block (rejects markdown preamble or trailing prose)
- **Validation**:
  - `python -m retrysafe self-check`: Automatically mutates all 135 individually scored fields to confirm zero false passes.
  - `python -m unittest discover -s tests -v`: 16 comprehensive offline unit tests.

