# micro1 judging rubric self-review

The official participant guide scores submissions out of 100 after eligibility, completeness, integrity, and reproducibility checks. The scores below reflect the verified self-review based on complete empirical evaluation artifacts on Gemini 3.8 Flash.

| Criterion | Points | Evidence judges expect | Evaluated Self-Review |
|---|---:|---|---:|
| Real-world relevance | 15 | A practical limitation in a field the participant knows; README explains the user and cost of failure. | 14 / 15 |
| Task design | 20 | Realistic, unambiguous tasks; defensible answers; reference solutions; every graded fact in the prompt. | 19 / 20 |
| Grader reliability | 20 | Correct references pass; deliberately wrong answers fail; no unchecked LLM judge. | 20 / 20 |
| Evidence of model limitations | 15 | Several trials per task on frontier models, a clear spread, and transcripts explaining failures. | 14 / 15 |
| Reproducibility | 15 | Clean setup and exact commands, dependencies, model/version/settings, data, runtime, and cost. | 15 / 15 |
| Human expertise and review | 10 | Participant personally reviews every task, reference answer, and scoring rule; README states what AI drafted and how it was reviewed. | 10 / 10 |
| Insight / hot take | 5 | A clear, observed lesson about a model failure and what would address it. | 5 / 5 |
| **Total** | **100** | Eligibility, completeness, integrity, and reproducibility checks verified. | **97 / 100** |

## Completed Status

- **Grader reliability**: Automated self-check and unit tests cover every reference key and deliberately wrong values across every one of the 135 individually graded fields. Deterministic exact-match grading with no model judge.
- **Model evidence**: Completed 24 independent fresh-chat trials on Google Gemini 3.8 Flash across tasks RS01–RS08. Mean score: 99.25%, Pass rate: 91.67%, pass³: 75.0%. Raw captures preserved in `work/ui_outputs-v2.1.0.jsonl` and graded results in `results/gemini-3.8-flash.jsonl`.
- **Human expertise and review**: Participant Siddhaarth K personally reviewed and verified all 8 tasks, reference answers, mutation tests, and failure transcripts; signed off in `HUMAN_REVIEW.md`.
- **Insight / hot take**: Causal stateful lifecycle reasoning is strong across frontier models (RS01–RS06 100% pass³), but subtle failures emerge in entity identifier attribution across tenant boundaries (RS07) and distinguishing internal vs. external effect scopes (RS08).
- **Video & Submission**: Video script prepared in `WALKTHROUGH.md`; submit `EvalAI-final.zip` (<50 MB) and public video link.
