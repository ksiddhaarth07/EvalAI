# Results report template

Use the same task-set version, task prompts, and deterministic grader for each model. The planned report requires three fresh-chat trials for every task. Do not fill a result row until the matching raw outputs are captured and graded.

## Model-level results

| Model and exact UI version | Date | Settings shown by UI | Trials/task | Mean score (%) | Spread (min–max; population SD) | Full-task pass rate | pass^3 | Cost for full run | Runtime |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| [Model, version] | [Date] | [Settings or “not exposed”] | 3 | [Mean] | [Range; SD] | [Rate] | [Rate] | [Measured or “not separately itemized”] | [Measured] |

## Per-task failures and near miss

For each failure, cite the task/trial and the exact raw transcript record, identify the incorrect field and model answer, and explain the expected result from the task contract. Include a close answer and what it missed. Distinguish observed facts from interpretation.

| Task | Model/trial | Transcript link | Incorrect field / observed answer | Task contract and practical consequence |
|---|---|---|---|---|
| [Task] | [Model, trial] | [Path/record] | [Field/value] | [Evidence-based explanation] |

## Takeaway

[State only the main failure pattern supported by the completed trials, what it indicates, and what would address it.]

## Excluded pilot disclosure

`results/pilot-chatgpt-web-ui-v2.0.0-2026-10-30.jsonl` preserves an earlier ChatGPT response and its exact prompt. That prompt did not state the status returned by an identical retry, so the earlier mechanical score is withdrawn and the response is excluded from benchmark results. The valid evaluation uses the clarified task-set version 2.1.0.
