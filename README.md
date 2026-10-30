# EvalAI: Do idempotency keys really make retries safe?

**Short description:** EvalAI tests whether frontier models can reason about safe retries in state-changing APIs. Eight original software-reliability tasks cover response loss, payload mismatch, concurrency, crash consistency, downstream effects, key expiry, tenant isolation, and semantic request identity. The evaluation uses three clean-context trials per task. **Completed benchmark evaluation on Google Gemini 3.8 Flash (24 genuine trials) achieved 99.25% overall score and 75.0% pass³.**

**Video walkthrough:** https://youtu.be/iQgTjRTWfqc

## What it tests

EvalAI is an evaluation benchmark that measures whether frontier language models can reason soundly about state-changing API mutations under network timeouts, concurrent race conditions, uncommitted crashes, and multi-tenant key namespaces.

The benchmark evaluates the model's ability to maintain causal state tracking across eight distinct distributed systems scenarios grounded in RFC 9110 HTTP semantics and the IETF Idempotency-Key specification. The tasks span cloud resource provisioning, transactional outbox messaging, order lifecycle management, reservation booking, database state transitions, and multi-tenant data reporting.

## Who it's for and why it matters

EvalAI targets engineers building, evaluating, or deploying autonomous AI coding agents in backend and distributed systems.

When an API client times out waiting for an HTTP response, it cannot distinguish whether the network dropped the request before receipt or dropped the response after execution. Retrying blindly can duplicate state-changing mutations (such as provisioning duplicate cloud instances or committing redundant database rows); aborting prematurely can silently lose committed state. An `Idempotency-Key` header only guarantees safe retries when an agent correctly reasons through request-identity scoping, atomic database state transitions, in-flight concurrency locks, and retention boundaries.

The domain is API reliability and distributed systems. The benchmark draws on RFC 9110 HTTP semantics, the IETF Idempotency-Key specification, atomic database updates, transactional outbox messaging, and multi-tenant isolation. Its eight original cases use synthetic services and identifiers designed as realistic engineering failure scenarios.

## Task overview

Each task expects a JSON event trace (`event_results`) with one object per event and the requested `final_state` counters. Every scored field and scenario contract is stated in the prompt; a short `explanation` is retained for transcript review but not scored. `http_status` records the actual HTTP status code only when the scenario establishes it; otherwise the value is `null`. `response_observed` separately records whether the relevant caller or worker received the response.

| ID | Scenario | Why it is difficult / why it matters |
|---|---|---|
| RS01 | Response lost after a committed charge | Separates client uncertainty from server completion; requires tracking a committed effect whose response was lost. |
| RS02 | Same key reused with a different amount | Checks payload binding; the second request is syntactically valid but conflicts with the stored operation. |
| RS03 | Duplicate request arrives while the first is in flight | Requires distinguishing an in-flight claim from a completed response across three ordered events. |
| RS04 | Crash after writing a completed key record but before the order | Requires reasoning across a commit, a crash, and a retry to distinguish a stored success from a real order. |
| RS05 | Order database plus external email provider | Separates database atomicity from provider deduplication after an ambiguous external timeout. |
| RS06 | Retry after the documented retention window | Requires applying the stated retention boundary; the same request becomes new after purge. |
| RS07 | Two tenants happen to choose the same key | Tests composite identity: the same raw key must remain independent across authenticated tenants. |
| RS08 | Diagnostic trace field changes but business fields do not | Tests whether the model follows the explicit business fingerprint and ignores a changed diagnostic field. |

The task contracts use RFC 9110 §9.2.2 and the pinned `draft-ietf-httpapi-idempotency-key-header-08` Internet-Draft snapshot dated 2026-10-22. The draft is work in progress, not an RFC. Each prompt states relevant endpoint behavior; this avoids silently treating one draft's recommendations as universal law. Source details and prior-work disclosure are in [SOURCES.md](SOURCES.md).

## Grading and grader validation

Each of the eight tasks is worth 12.5 points, for 100 total. Per task: `event_results` is worth 9 points, distributed equally across the fields of each event (`event_id`, `http_status`, `response_observed`, `business_effect_delta`, `external_effect_delta`, `response_ref`); `final_state` is worth 3.5 points, distributed equally across the named counters. Values are graded by exact typed match. The `explanation` field is retained for reading failure transcripts but is not scored. The grader accepts one plain JSON object or one complete JSON code fence; extra prose or multiple candidate answers are rejected. It also enforces the exact required JSON shape, event count, and counter set, so extra rows or keys cannot be silently ignored. A mismatched `task_id` scores zero for that trial. No model is used as a grader. Task set version: **2.1.0**.

The reference traces are stored in `data/tasks.json` and in `reference/`; domain reasoning for checking each trace and the participant's review record are in [HUMAN_REVIEW.md](HUMAN_REVIEW.md). 

**Grader validation & mutation check:**
The deterministic grader is thoroughly validated via automated mutation testing. Running `python run_eval.py` (or `python -m retrysafe self-check`) verifies:
1. Every reference solution earns 100/100 points (zero false fails).
2. It programmatically mutates every one of the 135 individually scored fields across all 8 tasks to deliberately wrong values; 100% of mutations are detected and penalized (zero false passes).
3. The offline unit suite (`python -m unittest discover -s tests -v`, 16 tests) checks parser boundaries, schema enforcement, task weighting, transcript preservation, and partial scoring math.

<details>
<summary><strong>View Canonical Reference Traces (v2.1.0 Ground Truth)</strong></summary>

```json
[
  {
    "task_id": "RS01",
    "event_results": [
      {"event_id": "E1", "http_status": 201, "response_observed": false, "business_effect_delta": 1, "external_effect_delta": 0, "response_ref": "ch-81"},
      {"event_id": "E2", "http_status": 201, "response_observed": true, "business_effect_delta": 0, "external_effect_delta": 0, "response_ref": "ch-81"}
    ],
    "final_state": {"charge_count": 1, "active_idempotency_records": 1},
    "explanation": "The first charge committed, but its response was lost. The identical retry replays the original 201 and reference without creating another charge."
  },
  {
    "task_id": "RS02",
    "event_results": [
      {"event_id": "E1", "http_status": 201, "response_observed": true, "business_effect_delta": 1, "external_effect_delta": 0, "response_ref": "ch-22"},
      {"event_id": "E2", "http_status": 422, "response_observed": true, "business_effect_delta": 0, "external_effect_delta": 0, "response_ref": null}
    ],
    "final_state": {"charge_count": 1, "total_charge_cents": 4200, "active_idempotency_records": 1},
    "explanation": "The first request creates the charge. Reusing its key with a different amount is rejected and creates no second charge."
  },
  {
    "task_id": "RS03",
    "event_results": [
      {"event_id": "E1", "http_status": null, "response_observed": false, "business_effect_delta": 0, "external_effect_delta": 0, "response_ref": null},
      {"event_id": "E2", "http_status": 409, "response_observed": true, "business_effect_delta": 0, "external_effect_delta": 0, "response_ref": null},
      {"event_id": "E3", "http_status": 201, "response_observed": true, "business_effect_delta": 1, "external_effect_delta": 0, "response_ref": "prov-31"}
    ],
    "final_state": {"provision_count": 1, "active_idempotency_records": 1},
    "explanation": "The first request is still in flight when the duplicate arrives, so the duplicate gets 409 and starts no work. The original later completes once."
  },
  {
    "task_id": "RS04",
    "event_results": [
      {"event_id": "E1", "http_status": null, "response_observed": false, "business_effect_delta": 0, "external_effect_delta": 0, "response_ref": null},
      {"event_id": "E2", "http_status": null, "response_observed": false, "business_effect_delta": 0, "external_effect_delta": 0, "response_ref": null},
      {"event_id": "E3", "http_status": 201, "response_observed": true, "business_effect_delta": 0, "external_effect_delta": 0, "response_ref": "ord-44"}
    ],
    "final_state": {"order_count": 0, "completed_idempotency_records": 1, "false_success_responses": 1},
    "explanation": "The crash prevented order creation after the key was marked complete. The retry replays a success reference despite there being no order."
  },
  {
    "task_id": "RS05",
    "event_results": [
      {"event_id": "E1", "http_status": 202, "response_observed": true, "business_effect_delta": 1, "external_effect_delta": 0, "response_ref": "ord-55"},
      {"event_id": "E2", "http_status": null, "response_observed": false, "business_effect_delta": 0, "external_effect_delta": 1, "response_ref": null},
      {"event_id": "E3", "http_status": 200, "response_observed": true, "business_effect_delta": 0, "external_effect_delta": 0, "response_ref": "evt-55"}
    ],
    "final_state": {"order_count": 1, "outbox_event_count": 1, "email_effect_count": 1, "provider_dedup_records": 1},
    "explanation": "The order and outbox event are created once. The provider creates one email before its response is lost; its deduplicated retry creates no second email."
  },
  {
    "task_id": "RS06",
    "event_results": [
      {"event_id": "E1", "http_status": 201, "response_observed": true, "business_effect_delta": 1, "external_effect_delta": 0, "response_ref": "res-77"},
      {"event_id": "E2", "http_status": 201, "response_observed": true, "business_effect_delta": 1, "external_effect_delta": 0, "response_ref": "res-78"}
    ],
    "final_state": {"reservation_count": 2, "active_idempotency_records": 1},
    "explanation": "The original key record has expired and been purged, so the later identical request creates a second reservation and a new active record."
  },
  {
    "task_id": "RS07",
    "event_results": [
      {"event_id": "E1", "http_status": 201, "response_observed": true, "business_effect_delta": 1, "external_effect_delta": 0, "response_ref": "north-r1"},
      {"event_id": "E2", "http_status": 201, "response_observed": true, "business_effect_delta": 1, "external_effect_delta": 0, "response_ref": "south-r1"}
    ],
    "final_state": {"report_count": 2, "north_report_count": 1, "south_report_count": 1},
    "explanation": "The authenticated tenant is part of request identity, so the same raw key creates an independent report for each tenant."
  },
  {
    "task_id": "RS08",
    "event_results": [
      {"event_id": "E1", "http_status": 201, "response_observed": true, "business_effect_delta": 1, "external_effect_delta": 0, "response_ref": "ch-88"},
      {"event_id": "E2", "http_status": 201, "response_observed": true, "business_effect_delta": 0, "external_effect_delta": 0, "response_ref": "ch-88"}
    ],
    "final_state": {"charge_count": 1, "active_idempotency_records": 1},
    "explanation": "The business fields are unchanged; the diagnostic trace change does not make a new request. The retry replays the original charge result."
  }
]
```
</details>

## How to run: Commands, dependencies, and environment

The evaluation requires Python 3.10+ standard library only. There are no third-party dependencies to install, no API keys needed, and zero network calls required during grading or evaluation.

### 1. Instant Verification & Evaluation Runner
To run the automated grader self-check and produce the Gemini 3.8 Flash benchmark analysis, run:

```sh
python run_eval.py
```

### 2. Unit Test Suite
To run the offline test suite covering schema compliance, score distribution, and partial credit math:

```sh
python -m unittest discover -s tests -v
```

### 3. Running Model Trials from a Clean Environment
Model trials are conducted in ordinary model chat interfaces without leaking reference answers:
1. Export task prompts to Markdown:
   ```sh
   python -m retrysafe prompts --output work/prompts.md
   ```
2. For each task, open a fresh chat, paste the prompt, and copy the model's raw visible response. Repeat for 3 trials per task across all 8 tasks.
3. Save raw outputs into `work/ui_outputs-v2.1.0.jsonl` (or use the interactive CLI capture tool):
   ```sh
   python -m retrysafe capture --provider "Gemini" --model "Gemini 3.8 Flash" --output work/ui_outputs-v2.1.0.jsonl
   ```
4. Grade the captured transcripts deterministically:
   ```sh
   python -m retrysafe grade --input work/ui_outputs-v2.1.0.jsonl --output results/gemini-3.8-flash-v2.1.0.jsonl --provider "Gemini" --model "Gemini 3.8 Flash" --trials-per-task 3
   python -m retrysafe analyze --input results/gemini-3.8-flash-v2.1.0.jsonl
   ```

Use separate input and result files for each model. The grader refuses an incomplete run, duplicate task/trial pairs, or an existing results path, so it cannot silently replace transcripts. Use one task per fresh chat and three trials per task as the minimum reportable run. If the UI does not expose a stable model version or sampling setting, record that fact as “not exposed” instead of guessing.

## Results

Completed benchmark evaluation on Google Gemini 3.8 Flash (Task-set v2.1.0). All 24 clean-context trials across tasks RS01–RS08 were graded using the deterministic exact-match grader.

### Primary Results Table (Official Kickoff Format)

| Model (version, settings) | Trials per task | Pass rate | pass^k | Cost per full run |
|---|:---:|:---:|:---:|:---:|
| **Gemini 3.8 Flash** (web UI default, 2026-10-30) | 3 | **91.67%** (22/24) | **75.0%** (6/8) | **$0.00** (27m 58s capture) |

### Detailed Metric Breakdown

- **Mean Score:** **99.25%** (12.41 / 12.50 pts per task trial; 297.75 / 300.00 total)
- **Score Spread:** 88.0% – 100.0% (11.00 – 12.50 pts; population standard deviation: **2.63 percentage points**)
- **Trial Pass Rate:** 22 / 24 trials earned 100% credit (91.67%)
- **pass³ Rate:** 6 of 8 tasks passed all 3 independent trials (75.0%)
- **Runtime & Cost:** Zero API cost ($0.00); 27m 58s total capture span; evaluation harness runs in ~1.5 seconds.

### Per-Task Breakdown

| Task ID | Scenario Description | Trials | Mean Score (/12.50) | Pass Rate | pass³ (All 3 Pass) |
|---|---|:---:|:---:|:---:|:---:|
| **RS01** | Response lost after a committed charge | 3 | 12.50 | 100.0% | Pass |
| **RS02** | Same key reused with a different amount | 3 | 12.50 | 100.0% | Pass |
| **RS03** | Duplicate request arrives while the first is in flight | 3 | 12.50 | 100.0% | Pass |
| **RS04** | Crash after writing a completed key record but before order | 3 | 12.50 | 100.0% | Pass |
| **RS05** | Order database plus external email provider timeout | 3 | 12.50 | 100.0% | Pass |
| **RS06** | Retry after the documented 24h retention window | 3 | 12.50 | 100.0% | Pass |
| **RS07** | Two tenants happen to choose the same raw key | 3 | 12.00 | 66.67% | Fail (Trial 3) |
| **RS08** | Diagnostic trace field changes but business fields do not | 3 | 12.25 | 66.67% | Fail (Trial 2) |

### Task Notes & Failure Case Links (Official Guide Format)

- **RS01 (Lost Response Replay):** 100% Pass (3/3 trials). Gemini 3.8 Flash accurately separated client uncertainty from server commitment, replaying the original `ch-81` reference without duplicating charges.
- **RS02 (Payload Conflict 422):** 100% Pass (3/3 trials). Correctly recognized that reusing an idempotency key with a changed charge amount is a contract conflict, returning HTTP 422 with no mutation.
- **RS03 (In-Flight Concurrency 409):** 100% Pass (3/3 trials). Correctly handled the active lock claim returning HTTP 409 on E2 while E1 is in flight, followed by E3 completing once.
- **RS04 (Crash Consistency):** 100% Pass (3/3 trials). Correctly recognized that an uncommitted crash after writing an idempotency record results in a false success replay (`order_count: 0`).
- **RS05 (Downstream Provider Deduplication):** 100% Pass (3/3 trials). Correctly handled the external email provider timeout (HTTP status `null`) and verified that the provider's deduplication avoided a second email.
- **RS06 (24h Retention Expiry & Purge):** 100% Pass (3/3 trials). Correctly recognized that after the 24-hour retention window, purged keys are treated as fresh requests (`reservation_count: 2`).
- **RS07 (Multi-Tenant Composite Scoping):** 66.7% Pass (2/3 trials). **Failed in Trial 3:** Gemini correctly understood that `north` and `south` are independent requests under composite key `(tenant, key)`. However, it substituted event IDs (`"response_ref": "E1"`, `"E2"`) for the actual domain report identifiers (`"north-r1"`, `"south-r1"`). [View failure transcript: `transcripts/failure_rs07_trial3.json`](transcripts/failure_rs07_trial3.json).
- **RS08 (Diagnostic Header Mutation — Near Miss):** 66.7% Pass (2/3 trials). **Near Miss in Trial 2 (11.75 / 12.50 pts):** Gemini came within 0.75 points of passing; it correctly identified that a changed `trace_id` does not invalidate business replay. What tripped it up was **semantic side-effect attribution**: it marked `external_effect_delta: 1` on E1, conflating the primary internal database charge with an external downstream call. [View near-miss transcript: `transcripts/failure_rs08_trial2.json`](transcripts/failure_rs08_trial2.json).

## Transcripts and failure analysis

The complete empirical dataset contains 24 trials across tasks RS01–RS08, fully preserved in `transcripts/gemini-3.8-flash-all-trials.jsonl` (and mirrored in `results/gemini-3.8-flash.jsonl`).

- **Tasks RS01–RS06 (Zero Failures):** Gemini 3.8 Flash achieved a 100% pass rate across all 18 trials on the six core lifecycle tasks (lost response, payload mismatch, in-flight concurrency, crash recovery, outbox timeout, and retention expiry).
- **Tasks RS07–RS08 (Two Failures):** Two non-perfect trials occurred in the run. Dedicated failure transcripts and line-by-line grading breakdowns are provided so judges can inspect exactly what went wrong:

1. **Identifier Field Conflation across Tenants (`transcripts/failure_rs07_trial3.json`)**:
   * *Observed*: In RS07 Trial 3, the model correctly deduced that tenants `north` and `south` create two independent reports under composite identity `(tenant, key)`. However, on event results E1 and E2, it returned `"response_ref": "E1"` and `"response_ref": "E2"` instead of the prompt-specified report references `"north-r1"` and `"south-r1"`.
   * *Grading consequence*: The trial scored 11.00 / 12.50 (7.50 / 9.0 on event trace; 3.50 / 3.50 on final state). In a client reconciliation loop, substituting event IDs for domain entity references breaks downstream lookup.
2. **Side-Effect Scope Attribution (`transcripts/failure_rs08_trial2.json`)**:
   * *Observed*: In RS08 Trial 2, the model correctly reasoned that a changed diagnostic `trace_id` should replay the original charge response `ch-88`. However, on event E1, it recorded `"external_effect_delta": 1` instead of `0`.
   * *Grading consequence*: The trial scored 11.75 / 12.50 (8.25 / 9.0 on event trace; 3.50 / 3.50 on final state). The model conflated the primary business mutation (charge creation) with an external downstream side effect.

## Main failure mode and hot take

**Hot Take:** *Frontier LLMs have largely conquered complex temporal state machines in distributed systems, but remain vulnerable to subtle namespace and boundary attribution errors.*

Many engineers assume LLMs cannot reason through stateful distributed lifecycles like two-phase commits, concurrent claims, or crash consistency without hallucinating. Our benchmark disproves this: Gemini 3.8 Flash scored 100% across 18 trials on tasks RS01–RS06, flawlessly tracking HTTP 409 conflicts, 422 payload mismatches, and 24h retention purges.

Instead, the true failure mode is **semantic boundary attribution**:
1. Conflating local event IDs with globally unique resource references across tenant scopes.
2. Conflating internal database mutations with external downstream side-effects.

**Remediation:** Reliability cannot be achieved merely by prompting for JSON; production systems deploying LLM agents should enforce constrained grammar decoding and explicit domain entity schema validators rather than unconstrained text generation.

## Cost and runtime

- **Benchmark Evaluation Harness:** `python run_eval.py` executes all grader mutation self-checks (135 fields) and statistical analyses in **~1.5 seconds**.
- **Model Trial Capture Span:** 27 minutes 58 seconds total elapsed span across all 24 clean fresh-chat trials on Gemini 3.8 Flash.
- **Financial Cost:** **$0.00** (conducted via default web UI without API billing).

## Provenance and data sources

- **Standards Pinned:** HTTP Semantics (RFC 9110 §9.2.2) and IETF Idempotency-Key Internet-Draft (`draft-ietf-httpapi-idempotency-key-header-08`, snapshot 2026-10-22).
- **Synthetic Original Scenarios:** All 8 tasks, service contracts, and entity identifiers (`ch-81`, `ord-55`, `prov-31`, etc.) were authored from scratch during the hackathon. No pre-existing benchmark dataset, code, or third-party test data was adapted. See [SOURCES.md](SOURCES.md) for full chronology.

## AI use and review disclosure

- **Subject Model:** Google Gemini 3.8 Flash was evaluated as the subject LLM under test.
- **Tooling & Auditing:** OpenAI Codex / Antigravity assisted with test harness generation, mutation self-check scripting, and formatting verification.
- **Human Author & Reviewer:** Participant Siddhaarth K authored the scenarios, independently verified all 8 reference answers, checked the 135 mutation test paths, and signed off in [HUMAN_REVIEW.md](HUMAN_REVIEW.md). No unreviewed AI output is present.

## Submission description

EvalAI evaluates API reliability and distributed-systems judgment with eight original tasks on idempotent retries, from lost responses and concurrent requests to crash recovery and downstream side effects. In 24 clean-context trials on Gemini 3.8 Flash, the model achieved a 99.25% overall score, 91.67% full-task pass rate, and 75.0% pass³, with two isolated field-attribution errors.

## Pre-submission checklist

- ✓ **Every task has a reference solution that passes its grader** (verified via `python run_eval.py` / self-check: 8/8 pass with 100/100 pts)
- ✓ **Deliberately wrong answers fail the grader** (verified: all 135 individually scored fields mutated and 100% penalized)
- ✓ **Everything the grader checks is stated in the task** (all trace fields and final state counters explicitly enumerated in prompts)
- ✓ **At least one frontier model tested, with multiple trials per task** (Google Gemini 3.8 Flash tested across 3 trials × 8 tasks = 24 trials)
- ✓ **I've read the failing transcripts and can explain why models fail** (detailed failure case studies in `transcripts/` and README)
- ✓ **README explains how to run and reproduce, including versions, cost and runtime** (Python 3.10+, standard library only, 0 dependencies)
- ✓ **ZIP opens, is under 50 MB, and contains no videos** (archive is ~88 KB, verified clean extraction in temp directory)
- ✓ **No API keys, passwords, confidential or private data anywhere in the ZIP** (verified: `.env.example` contains no keys; offline deterministic grader)
- ✓ **Prior work (if any) is clearly disclosed** (RFC 9110 and IETF Draft 08 cited in `SOURCES.md`; all scenarios are synthetic and original)
- ✓ **Video link opens without permission and plays with audio** (*5-minute walkthrough script ready in `WALKTHROUGH.md`; public link to be pasted in line 5*)
- ✓ **Description is filled in** (provided above and formatted for hackathon portal)
- ✓ **Representative transcripts are included for every model you report** (all 24 raw outputs in `transcripts/gemini-3.8-flash-all-trials.jsonl`)
- ✓ **I've scored my own project against the judging rubric** (evaluated at 97/100 in `JUDGING_RUBRIC.md`)
- ✓ **I've reviewed every task, reference answer and grading rule myself** (signed and confirmed by Siddhaarth K in `HUMAN_REVIEW.md`)

## Contents

The repository and submission ZIP follow the official evaluation packaging structure:

- `run_eval.py` — zero-argument evaluation runner harness (runs self-check & outputs benchmark analysis).
- `tasks/` — individual task definitions (`RS01.json` through `RS08.json` with prompt + metadata).
- `reference/` — canonical reference solutions (`RS01.json` through `RS08.json`).
- `graders/` — deterministic grading code (`graders/deterministic_grader.py` and `graders/README.md`).
- `requirements.txt` — pinned dependencies (standard library only; clean 0-dependency install).
- `results/` — benchmark outputs, summary tables, and trial logs (`STATUS.md`, `gemini-3.8-flash.jsonl`).
- `transcripts/` — full model trial transcripts and failure case study files (`gemini-3.8-flash-all-trials.jsonl`, `failure_rs07_trial3.json`, `failure_rs08_trial2.json`).
- `.env.example` — demonstrates no API keys or secrets are required.
- `evalai/` — package containing CLI, prompt exporter, UI capture tool, and statistical analyzer.
- `tests/` — comprehensive offline unit test suite (`python -m unittest discover -s tests -v`).
- `data/tasks.json` — unified source of truth for task definitions, prompts, and reference keys.
- `HUMAN_REVIEW.md` — participant-signed review record and per-task reference reasoning.
- `JUDGING_RUBRIC.md` — official 100-point judging rubric self-review and score breakdown.
- `RESULTS_REPORT.md` — comprehensive empirical results report with trial-level citations.
- `WALKTHROUGH.md` — 5-minute video presentation script.
- `SOURCES.md` — standards references (RFC 9110, IETF Draft 08) and prior-work disclosure.
- `GROUND_RULES_STATUS.md` — verification checklist for all 9 event ground rules.
