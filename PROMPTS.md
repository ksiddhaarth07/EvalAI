# RetrySafe prompts

Each block is a complete single-message prompt. Run every trial in a fresh chat with no prior task context. Paste one whole block as one message. Do not show the model the answer key. Repeat each task for the declared number of trials.

## RS01 — A committed charge whose response is lost

```text
Instructions:
Treat each scenario's stated contract as authoritative. Return only one JSON object with task_id, event_results, final_state, and explanation. Include one event_results object for every event in order. Each event object must have event_id, http_status (the actual HTTP status only when the scenario establishes it, otherwise null), response_observed (whether that event's caller or worker observed a response), business_effect_delta (integer), external_effect_delta (integer), and response_ref (string or null). Include exactly the named final_state values requested. No Markdown or extra keys. Explanation is a brief causal summary.

Task ID: RS01
Scenario: A POST /charges request uses tenant=acme, key=k-17, and body {invoice: inv-9, cents: 4200}. The server commits charge ch-81 and its idempotency record atomically. The server returns HTTP 201 with reference ch-81, but the network drops the response before the client receives it. The record remains within its retention window. This endpoint's explicit contract is that an identical retry within retention replays the original HTTP status and response reference without repeating the mutation. Event E1 is the original request; E2 is an identical retry, and its replayed response reaches the client. For each event, report the actual server HTTP status (null only if the scenario does not establish it), whether the client observed a response, business_effect_delta (new charges), external_effect_delta, and response_ref. Then report exactly charge_count and active_idempotency_records in final_state.
Return one JSON object. task_id must be RS01.
```

## RS02 — A reused key with a changed amount

```text
Instructions:
Treat each scenario's stated contract as authoritative. Return only one JSON object with task_id, event_results, final_state, and explanation. Include one event_results object for every event in order. Each event object must have event_id, http_status (the actual HTTP status only when the scenario establishes it, otherwise null), response_observed (whether that event's caller or worker observed a response), business_effect_delta (integer), external_effect_delta (integer), and response_ref (string or null). Include exactly the named final_state values requested. No Markdown or extra keys. Explanation is a brief causal summary.

Task ID: RS02
Scenario: A charge service binds (authenticated tenant, Idempotency-Key) to the first request's business payload. Reusing that identity with a different payload is rejected with HTTP 422 and makes no business mutation. Event E1 is tenant=acme, key=k-22, invoice=inv-10, cents=4200; the service accepts it as charge ch-22 with HTTP 201. Event E2 uses the same tenant and key but cents=8400. For each event, report the actual server HTTP status (null only if the scenario does not establish it), whether the client observed the response (both responses reach the client), business_effect_delta (new charges), external_effect_delta, and response_ref (null if no charge is created or replayed). Then report exactly charge_count, total_charge_cents, and active_idempotency_records in final_state.
Return one JSON object. task_id must be RS02.
```

## RS03 — A concurrent duplicate while provisioning is in flight

```text
Instructions:
Treat each scenario's stated contract as authoritative. Return only one JSON object with task_id, event_results, final_state, and explanation. Include one event_results object for every event in order. Each event object must have event_id, http_status (the actual HTTP status only when the scenario establishes it, otherwise null), response_observed (whether that event's caller or worker observed a response), business_effect_delta (integer), external_effect_delta (integer), and response_ref (string or null). Include exactly the named final_state values requested. No Markdown or extra keys. Explanation is a brief causal summary.

Task ID: RS03
Scenario: The service atomically claims a key scoped by authenticated tenant before provisioning begins. A duplicate arriving while the first request is still running receives HTTP 409 and cannot start work. Event E1 is request A for tenant=acme, key=k-31, body={plan:pro}; it claims the key and remains in flight, so no HTTP response status has yet been generated. E2 is an identical request B arriving before A finishes; its 409 response reaches the client. E3 is A completing successfully with HTTP 201 and reference prov-31. For each event, report the actual server HTTP status (null if none has yet been generated or the scenario leaves it unknown), whether the client observed a response, business_effect_delta (new provisions), external_effect_delta, and response_ref (null if no completed resource response exists). Then report exactly provision_count and active_idempotency_records in final_state.
Return one JSON object. task_id must be RS03.
```

## RS04 — A completion record written before the order

```text
Instructions:
Treat each scenario's stated contract as authoritative. Return only one JSON object with task_id, event_results, final_state, and explanation. Include one event_results object for every event in order. Each event object must have event_id, http_status (the actual HTTP status only when the scenario establishes it, otherwise null), response_observed (whether that event's caller or worker observed a response), business_effect_delta (integer), external_effect_delta (integer), and response_ref (string or null). Include exactly the named final_state values requested. No Markdown or extra keys. Explanation is a brief causal summary.

Task ID: RS04
Scenario: Review this flawed handler trace. It commits an idempotency row marked COMPLETED with stored success response HTTP 201, reference ord-44, before inserting the order row. Event E1 is that early completion-record commit; it creates no order and no HTTP response status has yet been generated. Event E2 is a process crash before the order insert; it creates no order and no HTTP response status is generated. Event E3 is a retry; the handler sees COMPLETED and returns the stored HTTP 201 / ord-44, observed by the client, without running the missing insert. For each event, report the actual server HTTP status (null when none has been generated), response_observed, business_effect_delta (new orders), external_effect_delta, and response_ref. Then report exactly order_count, completed_idempotency_records, and false_success_responses in final_state. Count a false_success_response when the service reports an order that does not exist.
Return one JSON object. task_id must be RS04.
```

## RS05 — Outbox delivery after an ambiguous provider timeout

```text
Instructions:
Treat each scenario's stated contract as authoritative. Return only one JSON object with task_id, event_results, final_state, and explanation. Include one event_results object for every event in order. Each event object must have event_id, http_status (the actual HTTP status only when the scenario establishes it, otherwise null), response_observed (whether that event's caller or worker observed a response), business_effect_delta (integer), external_effect_delta (integer), and response_ref (string or null). Include exactly the named final_state values requested. No Markdown or extra keys. Explanation is a brief causal summary.

Task ID: RS05
Scenario: An API commits an order and one outbox event in the same database transaction, then returns HTTP 202. A worker sends the outbox event to an email provider. The provider accepts the first send using event_id=evt-55, but the response times out; the provider has already created one email effect, and no HTTP status is known for that timed-out response. The provider durably deduplicates by event_id for longer than the retry window. Event E1 is the order/outbox transaction; E2 is the first provider attempt whose response is lost; E3 retries with the same event_id and receives the provider's HTTP 200 replay response. For each event, report the actual HTTP status if known, otherwise null; response_observed (for the API caller on E1 and the worker on E2/E3), business_effect_delta (new orders), external_effect_delta (new emails), and response_ref. Use ord-55 for the created order response; use evt-55 for a provider response; otherwise use null. Then report exactly order_count, outbox_event_count, email_effect_count, and provider_dedup_records in final_state.
Return one JSON object. task_id must be RS05.
```

## RS06 — A retry after idempotency state expires

```text
Instructions:
Treat each scenario's stated contract as authoritative. Return only one JSON object with task_id, event_results, final_state, and explanation. Include one event_results object for every event in order. Each event object must have event_id, http_status (the actual HTTP status only when the scenario establishes it, otherwise null), response_observed (whether that event's caller or worker observed a response), business_effect_delta (integer), external_effect_delta (integer), and response_ref (string or null). Include exactly the named final_state values requested. No Markdown or extra keys. Explanation is a brief causal summary.

Task ID: RS06
Scenario: A reservation API retains idempotency records for 24 hours. Once a record expires and is purged, it treats the same key as a new request. No other reservation identifier or reconciliation lookup exists. Event E1 is tenant=acme, key=k-66, body={room:R7}; it creates reservation res-77 with HTTP 201. Event E2 is the same tenant, key, and body 48 hours later, after the original record is purged; it creates reservation res-78 with HTTP 201. Both responses reach the client. For each event, report the actual server HTTP status (null only if the scenario does not establish it), response_observed, business_effect_delta (new reservations), external_effect_delta, and response_ref. Then report exactly reservation_count and active_idempotency_records in final_state.
Return one JSON object. task_id must be RS06.
```

## RS07 — Two tenants choose the same raw key

```text
Instructions:
Treat each scenario's stated contract as authoritative. Return only one JSON object with task_id, event_results, final_state, and explanation. Include one event_results object for every event in order. Each event object must have event_id, http_status (the actual HTTP status only when the scenario establishes it, otherwise null), response_observed (whether that event's caller or worker observed a response), business_effect_delta (integer), external_effect_delta (integer), and response_ref (string or null). Include exactly the named final_state values requested. No Markdown or extra keys. Explanation is a brief causal summary.

Task ID: RS07
Scenario: A reporting API defines request identity as (authenticated tenant, Idempotency-Key). Tenant north uses key=shared-7 to create report north-r1; tenant south independently uses the same raw key to create report south-r1. Both are new requests, both receive HTTP 201, and both responses reach their respective clients. Event E1 is the north request; E2 is the south request. For each event, report the actual server HTTP status (null only if the scenario does not establish it), response_observed, business_effect_delta (new reports), external_effect_delta, and response_ref. Then report exactly report_count, north_report_count, and south_report_count in final_state.
Return one JSON object. task_id must be RS07.
```

## RS08 — A diagnostic field changes on a semantic retry

```text
Instructions:
Treat each scenario's stated contract as authoritative. Return only one JSON object with task_id, event_results, final_state, and explanation. Include one event_results object for every event in order. Each event object must have event_id, http_status (the actual HTTP status only when the scenario establishes it, otherwise null), response_observed (whether that event's caller or worker observed a response), business_effect_delta (integer), external_effect_delta (integer), and response_ref (string or null). Include exactly the named final_state values requested. No Markdown or extra keys. Explanation is a brief causal summary.

Task ID: RS08
Scenario: The charge API defines request identity by normalized (invoice_id, cents, currency). trace_id is diagnostic only and explicitly does not affect the operation. A completed request used tenant=acme, key=k-88, invoice=inv-20, cents=1000, currency=USD, trace_id=t-a. Event E1 creates charge ch-88 and returns HTTP 201. Event E2 uses the same tenant, key, and business fields but trace_id=t-b; the completed HTTP 201 response and reference ch-88 are replayed. Both responses reach the client. For each event, report the actual server HTTP status (null only if the scenario does not establish it), response_observed, business_effect_delta (new charges), external_effect_delta, and response_ref. Then report exactly charge_count and active_idempotency_records in final_state.
Return one JSON object. task_id must be RS08.
```
