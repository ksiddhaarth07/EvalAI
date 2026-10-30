# Five-minute video walkthrough script

Keep the final recording at five minutes or less. The guide recommends about 1 minute for the problem, 1.5 minutes for a task and its grading, 2 minutes for results and transcripts, and 30 seconds for the takeaway.

**Public Video Walkthrough:** https://youtu.be/iQgTjRTWfqc

## 0:00–0:45 — What is this Eval & What Does it Test?

“Hi everyone, I’m Siddhaarth. Today I’m presenting **EvalAI**—an evaluation benchmark built to test frontier AI models on stateful software reasoning.

AI models can write code and explain syntax in seconds. But an eval’s job is to find what AI *can’t* do yet.

In software engineering, reasoning about network retries and idempotency is notoriously tricky. When an API call times out, the model must track multiple possible states: did the request fail before execution, or did the response drop after execution? 

We built EvalAI to answer one core question: **Can frontier models accurately track complex state machines across network retries, or do they fail on edge cases?**”

**Show:** `README.md` overview at the top.

## 0:45–1:40 — How the Eval Works: Tasks, Outputs & Grader

“We designed **eight original single-turn tasks** covering lost responses, payload conflicts, concurrency locks, crashes, outbox timeouts, retention expiry, and tenant isolation.

In each task, the input prompt describes a real sequence of API events. 

The model's expected output is a structured JSON trace containing:
- The HTTP status code,
- Whether the caller observed the response,
- The business effect count,
- And the final system state counters.

Everything the grader checks is explicitly specified in the prompt. There are no trick questions.”

“Now let’s look at the eval harness. I’m running `python run_eval.py`.

Our grader is **purely code-based and deterministic**—we do not use an LLM as a judge.

To ensure the grader is reliable, the harness first runs a **mutation self-check**. It takes all eight reference solutions and deliberately changes all 135 scored fields to wrong values. It confirms that 100% of wrong answers are caught and rejected—meaning zero false passes.

Then, the harness evaluates the transcripts and computes the benchmark statistics.”

**Show:** `tasks/RS01.json`, then terminal running `python run_eval.py`.

## 1:40–2:30 — Model Trials & Benchmark Scores

“We ran **24 independent trials** on Google’s frontier model, **Gemini 3.8 Flash**—running 3 clean trials per task in fresh chats to prevent history leakage.

Here are the benchmark results:
- **Mean Score:** **99.25%**
- **Trial Pass Rate:** **91.67%** (22 out of 24 trials scored 100%)
- **pass^k (pass³):** **75.0%** (6 out of 8 tasks passed all 3 trials consistently)

The model showed strong performance on the first six tasks. But on Tasks 7 and 8, the eval successfully revealed where the model falls short.”

**Show:** `README.md` Results Table and breakdown metrics.

## 2:30–3:45 — Transcript Walkthrough: Where the Model Failed

“Let's inspect the actual model transcripts.

In **Task RS07, Trial 3**, two different tenants used the same idempotency key string. 

The model correctly recognized that tenant scoping makes these distinct requests. But look at the output failure: for the entity reference, the model output the raw event names `E1` and `E2` instead of the domain identifiers `north-r1` and `south-r1`. It failed to preserve entity reference attribution across tenant boundaries, scoring 11.0 out of 12.5.”

“Now look at our near-miss in **Task RS08, Trial 2**.

Here, a diagnostic header changed while the core request payload remained identical. Gemini correctly identified that this was an idempotent replay, scoring 11.75 out of 12.5.

What tripped it up was **side-effect scoping**: on Event 1, it recorded `external_effect_delta: 1` instead of `0`. It misclassified an internal database state update as an external downstream side effect.”

**Show:** `transcripts/failure_rs07_trial3.json` and `transcripts/failure_rs08_trial2.json`.

## 3:45–4:30 — Conclusion & Eval Takeaway

“This brings us to what this eval teaches us about AI limitations:

Many people assume LLMs cannot follow multi-step distributed logic. But our eval proves that frontier models are actually very good at temporal state machines—handling locks, crashes, and retention windows.

Where models fail is in **semantic boundary attribution**—confusing event IDs with entity names across tenant scopes, and confusing internal mutations with external side effects.

This eval shows that when using AI agents for critical backend infrastructure, unconstrained text prompting is not enough—we must enforce schema validation and entity boundaries.”

**Show:** `README.md` Main failure mode and hot take section.

## 4:30–4:50 — Reproducibility & Sign-Off

“Everything—the 8 tasks, reference solutions, deterministic grader, 24 raw transcripts, and the runner harness—is packaged in our 89 KB ZIP file. Every task was personally verified and signed off in `HUMAN_REVIEW.md`.

Anyone can reproduce these exact results in seconds using standard Python 3.10 with zero external dependencies.

Thank you for your time!”

**Show:** `HUMAN_REVIEW.md` sign-off table.
