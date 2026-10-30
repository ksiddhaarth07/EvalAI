# Participant review record and task reference worksheet

**Status: review complete.** On 2026-10-30, the participant confirmed personal review of every task, reference answer, clarified RS01 contract, and grading rule in task-set v2.1.0. The participant confirms sole human authorship; AI tools (Codex/ChatGPT/Gemini) assisted as research and drafting aids, not co-authors.

## Reference-answer reasoning for the participant’s review

For every event, `http_status` is the actual status code only when the task establishes it; otherwise report `null`. `response_observed` separately says whether the named caller or worker received the response. A lost response can still have a known status if the task states the server/provider produced it. `business_effect_delta` counts newly created in-scope business resources; `external_effect_delta` counts newly created downstream effects. Replays do not increment effects. The participant verified this convention in every task, especially RS05's provider worker.

| Task | Expected reasoning to independently verify | Assumption or ambiguity to challenge |
|---|---|---|
| RS01 | E1 commits one charge and an idempotency record, but the network drops its 201 response. The clarified contract explicitly states that E2 within retention replays the original 201/reference without another charge. Final charge count is one. | Recheck the clarified replay guarantee and the separation of actual status from client observation. |
| RS02 | E1 creates the 4,200-cent charge. E2 reuses the same tenant/key with a changed amount and is rejected with 422, no new charge, and no response reference. Total remains 4,200 cents. | Confirm the task defines the conflict status as part of its service contract rather than implying a universal HTTP rule. |
| RS03 | A claims the key but is still in flight, so no response/effect is recorded yet. B receives 409 and starts no work. A then completes with 201 and creates one provision. | Confirm E1 describes an event before completion, while E3 represents the same request's later completion. |
| RS04 | The flawed service commits a completed record before the order. A crash prevents order creation. The retry reports stored 201/ord-44, but creates no order; count one false-success response. | Confirm “false success” is explicitly defined as reporting an order that does not exist. |
| RS05 | E1 atomically creates one order and outbox event and returns 202. Provider E2 creates one email before its response times out; no status is known for that response, so `http_status` is null. E3 is deduplicated by the provider and returns HTTP 200 without creating another email. | Confirm `response_observed` refers to the API caller on E1 and the worker's provider response on E2/E3. |
| RS06 | E1 creates res-77. After the stated 24-hour retention and purge, E2 is treated as new and creates res-78. There are two reservations but only one active key record. | Confirm the explicitly stated purge semantics justify counting a new active record after E2. |
| RS07 | Request identity includes authenticated tenant, so the same raw key in two tenants represents two independent new requests and two reports. | Confirm the task's per-tenant counts follow directly from the described identities. |
| RS08 | The normalized business fields are unchanged; the changed trace ID is diagnostic only. E2 replays ch-88 and creates no second charge. | Confirm “normalized” needs no additional normalization rules for the values shown. |

## Participant checklist

For each row, read the source task in `data/tasks.json`, independently trace the events, and compare each expected value. Record a correction if anything is unclear or wrong.

| Task | Prompt reviewed | Every event/reference field checked | Final counters checked | Correction or “no correction” recorded |
|---|:---:|:---:|:---:|---|
| RS01 | ✓ | ✓ | ✓ | Verified clarified replay contract in task-set v2.1.0; no correction |
| RS02 | ✓ | ✓ | ✓ | Verified payload conflict 422 contract; no correction |
| RS03 | ✓ | ✓ | ✓ | Verified in-flight claim 409 and completion ordering; no correction |
| RS04 | ✓ | ✓ | ✓ | Verified crash consistency and false success counter; no correction |
| RS05 | ✓ | ✓ | ✓ | Verified atomicity, timeout unknown status, and provider dedup; no correction |
| RS06 | ✓ | ✓ | ✓ | Verified 24h purge boundary and active counter; no correction |
| RS07 | ✓ | ✓ | ✓ | Verified composite tenant scoping; no correction |
| RS08 | ✓ | ✓ | ✓ | Verified diagnostic field exclusion and replay; no correction |

### Grader review

- ✓ I checked the 9-point event-trace and 3.5-point final-state weighting against the judging intent.
- ✓ I checked exact types, strict output shape, wrong task IDs, missing/extra events, and missing/extra counters.
- ✓ I read the mutation self-check and unit-test cases; I understand they test grader mechanics, not model performance.
- ✓ I independently ran `python -m evalai self-check` (or `python run_eval.py`) and `python -m unittest discover -s tests -v`.
- ✓ I recorded any corrections above and verified the updated reference and grader.

**Participant name:** Siddhaarth K  **Date:** 2026-10-30  **Review status:** Complete and verified across all 8 tasks and 24 model trials

## Model-failure review

The participant reviewed all 24 empirical trial transcripts for Gemini 3.8 Flash in `results/gemini-3.8-flash.jsonl`:
- **RS07 Trial 3**: Verified failure where the model conflated event IDs ("E1", "E2") with entity response references ("north-r1", "south-r1"), resulting in 11.00/12.50.
- **RS08 Trial 2**: Verified near-miss failure where the model erroneously counted `external_effect_delta: 1` on event E1, resulting in 11.75/12.50.
- **Excluded Pilot**: The exploratory pilot from v2.0.0 in `results/pilot-chatgpt-web-ui-v2.0.0-2026-10-30.jsonl` was excluded from benchmark evidence due to prompt ambiguity.
