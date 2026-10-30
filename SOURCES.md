# Sources and prior work

The participant reports that no tasks, answer keys, datasets, or results from an existing benchmark were used. The scenarios and identifiers are synthetic and original to EvalAI (formerly working-titled RetrySafe). This originality account is participant-reported.

## Prior work and hackathon work

**Disclosure:** The participant confirms they are the sole human participant and author; Codex/ChatGPT were AI tools, not human co-authors. The participant reports that the earlier draft was not adapted from an existing benchmark. The official event page lists the challenge kickoff as October 30, 2026, 07:15 GMT (12:45 PM Asia/Kolkata). The referenced project chat was created at 07:27:48 GMT (12:57:48 PM Asia/Kolkata), and the earliest files in this workspace have creation times after 1:12 PM Asia/Kolkata. The available chronology therefore places the earlier RetrySafe drafts after the official kickoff, not as pre-hackathon work.

| Stage | Materials |
|---|---|
| Before the hackathon kickoff | No RetrySafe project materials are evidenced in the available project/chat record. |
| Built after kickoff, before the current event-trace version | The project domain (safe retries/idempotency for state-changing APIs), initial task scenarios, an eight-task multiple-choice draft, its grader, and supporting documentation existed, as reported by the participant and reflected in the project history. |
| Current event-trace version | Version 2.1.0 clarifies that RS01 replays the original response status, defines when an unknown HTTP status is null, and adds reproducible grading for partial captures. It updates the reference prompts, grader, transcript capture and analysis tools, tests, README, prompts, review worksheet, and report template. Codex assisted with research, drafting, implementation, and documentation. |
| Pre-existing sources used as references | RFC 9110, the IETF HTTPAPI idempotency-key draft, AWS Builders' Library, and AWS Well-Architected guidance listed below. No source text, figures, or dataset is included in the benchmark package. |
The participant reports no existing-benchmark adaptation and no prior benchmark dataset or results. The first ChatGPT UI response is retained as an excluded pilot: its v2.0.0 prompt did not state what status the duplicate retry returns, so its initial mechanical score is withdrawn. It is not counted as a model result. If new information changes this account, update it before submission.
The packaging, trial-count, pass^k, transcript, and judging-rubric requirements were checked against the participant guide PDF supplied by the participant. The published event kickoff time was checked on the [official HackerRank event page](https://www.hackerrank.com/event/micro1-eval-hackathon). That 22-page PDF is not included in the submission ZIP.

1. **RFC 9110, HTTP Semantics, §9.2.2 (2022).** Defines idempotent methods by intended server effect and explains the conditions for automatic retry. https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2
2. **IETF HTTPAPI Working Group, draft-ietf-httpapi-idempotency-key-header-08 (2026-10-22 snapshot).** Current Internet-Draft describing key uniqueness, expiration policy, optional fingerprints, duplicate retries, concurrent requests, and error cases. It is work in progress and may change; RetrySafe pins this version only as a reference. https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header-08
3. **AWS Builders' Library, “Making retries safe with idempotent APIs.”** Engineering discussion of caller-provided request identifiers, semantic equivalence, late requests, and atomicity of idempotency records with mutations. https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-apis/
4. **AWS Well-Architected Framework, REL04-BP04, “Make all responses idempotent.”** Production guidance on idempotent service APIs. https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_prevent_interaction_failure_idempotent.html

These sources informed the domain and review checklist. The synthetic service names, traces, requests, task wording, labels, answer keys, and scoring implementation in this package are newly authored. The draft is not an RFC; the individual task contract supplies the facts needed to answer each case.
