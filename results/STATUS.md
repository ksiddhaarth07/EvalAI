# Results status

**Completed evaluation:** Gemini 3.8 Flash UI label, task-set v2.1.0. The participant-provided capture contains all 24 task/trial pairs (RS01–RS08, trials 1–3). Raw visible responses and metadata are preserved in `gemini-3.8-flash-v2.1.0-raw.jsonl`; deterministic grades are in `gemini-3.8-flash-v2.1.0.jsonl`.

## Summary

- Score: **297.75 / 300 (99.25%)**; mean trial score **12.41 / 12.50**.
- Trial scores: **11.00–12.50** (88%–100%); population SD **2.63 percentage points**.
- Full-task trial pass rate: **22 / 24 (91.67%)**.
- pass³: **6 / 8 tasks (75%)**; RS01–RS06 passed every trial.
- Analyzer component-section pass rates: event trace **22 / 24**, final state **24 / 24**. These are section-level per-trial counts, not raw per-field denominators.
- Two non-perfect trials: RS07 trial 3 used event IDs instead of the expected report references; RS08 trial 2 reported one external effect for the charge event.
- Provider/model metadata: Gemini / “Gemini 3.8 Flash”; default web UI settings. A more specific stable version and sampling controls were not exposed.
- First-to-last recorded capture timestamps span **27m 58s**. Cost was not separately itemized by the UI.

## Excluded pilot

`pilot-chatgpt-web-ui-v2.0.0-2026-10-30.jsonl` contains an earlier RS01 response whose prompt did not specify the duplicate retry status. It is excluded from v2.1.0 results.

## Remaining submission actions

- Participant re-reviews the clarified RS01 reference and the two failure transcripts; complete the corresponding checklist in `HUMAN_REVIEW.md` only after personally checking them.
- Add the public video link to the README and record the participant's final rubric self-score.
- The results cover one model, so there is no cross-model comparison.
