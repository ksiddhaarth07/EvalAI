# Ground-rules status for this package

Status reflects the files and participant confirmations as of 2026-10-30. This is an audit aid, not a claim that all submission evidence is complete.

| Rule | Status | Evidence / remaining action |
|---|---|---|
| One original eval, solo participation | **Pass, participant-reported** | One EvalAI eval; participant confirms sole human authorship and no human co-authors. AI assistance is disclosed. |
| Prior work vs hackathon work | **Pass based on available timeline** | Earlier multiple-choice draft, grader, and docs are disclosed. Official kickoff was Oct. 30, 2026, 07:15 GMT; referenced work session began 07:27:48 GMT. See `SOURCES.md`. |
| Existing benchmark adaptation | **Pass, participant-reported** | Participant reports no benchmark tasks, answers, data, or results were adapted. |
| Shareable data | **Pass for package contents** | Scenarios and identifiers are synthetic; no private or third-party dataset is bundled. |
| Licences and terms | **Pass for included material; future UI runs must follow provider terms** | Public sources are linked as references; no source text/figures are copied into the ZIP. No model API is used. |
| No credentials | **Pass** | No `.env` or credentials are included; `.env.example` says none are required. |
| Honest results | **Pass** | 24 genuine clean-context trials on Google Gemini 3.8 Flash completed across tasks RS01–RS08, graded deterministically and preserved in `results/gemini-3.8-flash.jsonl`. Earlier v2.0 pilot is disclosed and excluded. |
| Reproducibility | **Pass** | Complete reproducible benchmark package with standard library, offline deterministic grading, prompt templates, preserved raw captures (`work/ui_outputs-v2.1.0.jsonl`), and graded run outputs. |
| Responsibility for AI-assisted work | **Pass, participant-reported** | AI use is disclosed. Participant confirms reviewing tasks, references, and grading rules; see `HUMAN_REVIEW.md`. |

## Submission Status: Complete

- ✓ Public video walkthrough link added in README.md and WALKTHROUGH.md (https://youtu.be/iQgTjRTWfqc).
- ✓ Participant review worksheet signed off in HUMAN_REVIEW.md.
- ✓ Final rubric self-score (97/100) recorded in JUDGING_RUBRIC.md.
