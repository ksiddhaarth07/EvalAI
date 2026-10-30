# EvalAI Results Report: Gemini 3.8 Flash

Evaluated using task-set **v2.1.0** with deterministic exact-match grading on **2026-10-30**.

## Model-level results

| Model and exact UI version | Date | Settings shown by UI | Trials/task | Mean score (%) | Spread (min–max; population SD) | Full-task pass rate | pass³ | Cost for full run | Runtime |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Google Gemini 3.8 Flash | 2026-10-30 | Default web UI settings | 3 | **99.25%** (12.41 / 12.50) | 88.0%–100.0% (11.00–12.50; SD: 2.63 pp) | **22 / 24 (91.67%)** | **6 / 8 (75.0%)** | $0.00 (not separately itemized) | ~20 min |

## Task-by-task results

| Task | Scenario Summary | Trial 1 | Trial 2 | Trial 3 | Task Mean | pass³ Result |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **RS01** | Lost response after committed charge | 12.50 | 12.50 | 12.50 | 12.50 | Pass |
| **RS02** | Same key reused with different amount | 12.50 | 12.50 | 12.50 | 12.50 | Pass |
| **RS03** | In-flight concurrent duplicate request | 12.50 | 12.50 | 12.50 | 12.50 | Pass |
| **RS04** | Completion record committed before order insert | 12.50 | 12.50 | 12.50 | 12.50 | Pass |
| **RS05** | Outbox delivery with downstream timeout | 12.50 | 12.50 | 12.50 | 12.50 | Pass |
| **RS06** | Key retention expiry and purge after 24h | 12.50 | 12.50 | 12.50 | 12.50 | Pass |
| **RS07** | Multi-tenant raw key collision | 12.50 | 12.50 | 11.00 | 12.00 | Fail (Trial 3) |
| **RS08** | Diagnostic trace header changes on retry | 12.50 | 11.75 | 12.50 | 12.25 | Fail (Trial 2) |

## Per-task failures and near miss

| Task | Model/trial | Transcript link | Incorrect field / observed answer | Task contract and practical consequence |
|---|---|---|---|---|
| **RS07** | Gemini 3.8 Flash, Trial 3 | `results/gemini-3.8-flash.jsonl` (line 21) | `event_results[0].response_ref = "E1"`, `event_results[1].response_ref = "E2"` (expected `"north-r1"` and `"south-r1"`) | The prompt explicitly established that tenant north creates report `north-r1` and tenant south creates report `south-r1`. The model understood tenant isolation logically, but conflated the event IDs with the response entity references. In an API integration, returning event names instead of entity IDs breaks client reconciliation. Score: 11.00 / 12.50. |
| **RS08** | Gemini 3.8 Flash, Trial 2 | `results/gemini-3.8-flash.jsonl` (line 23) | `event_results[0].external_effect_delta = 1` (expected `0`) | The scenario describes a charge creation API where charge insertion is a business mutation (`business_effect_delta = 1`), not an external side effect. The model correctly identified replay behavior under a changed diagnostic header, but double-counted the initial commit across effect scopes. Score: 11.75 / 12.50. |

## Takeaway

Gemini 3.8 Flash demonstrates exceptional zero-shot command over core distributed-systems and idempotency contracts:
1. It scored 100% on response loss, 422 payload mismatches, 409 concurrent claims, crash consistency, outbox delivery, and retention expirations (RS01–RS06 achieved 100% pass³).
2. The isolated failures occurred in entity identifier attribution across tenant boundaries and distinguishing internal vs. external effect scopes.
3. Causal lifecycle reasoning was robust across all 24 trials; errors were localized to specific field extractions rather than conceptual misunderstandings.

## Excluded pilot disclosure

`results/pilot-chatgpt-web-ui-v2.0.0-2026-10-30.jsonl` preserves an earlier exploratory response from v2.0.0. That prompt did not state the status returned by an identical retry, so that exploratory trial was excluded. The valid, evaluated benchmark is task-set v2.1.0.

