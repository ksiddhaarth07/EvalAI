# EvalAI Transcripts

This directory contains representative raw model transcripts from the 24 clean-context trials on Google Gemini 3.8 Flash (task-set v2.1.0):

- `gemini-3.8-flash-all-trials.jsonl`: Complete raw model outputs across all 24 trials (tasks RS01–RS08, trials 1–3).
- `failure_rs07_trial3.json`: Detailed transcript and grading breakdown for RS07 Trial 3 (Score: 11.00/12.50). Demonstrates entity identifier conflation where the model output `"response_ref": "E1"` and `"E2"` instead of `"north-r1"` and `"south-r1"`.
- `failure_rs08_trial2.json`: Detailed transcript and grading breakdown for RS08 Trial 2 (Score: 11.75/12.50). Demonstrates side-effect scope conflation where the model output `"external_effect_delta": 1` instead of `0` on event E1.

