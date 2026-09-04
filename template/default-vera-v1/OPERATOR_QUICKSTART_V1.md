# Default Vera V1 Operator Quickstart

Status: `READY_FOR_USER_EXECUTION`

This is the shortest safe path from the frozen trainer package to the first candidate turn.

## Before training

1. Create one disposable project-only Project and verify the exact chat branch/move route you intend to use later for holdouts. Use non-sensitive nonce text. Follow `OPENAI_PROJECT_ROUTE_REVERIFY_2026-08-07.md`.
2. Create a new project-only Project named `Default Vera Training V1`.
3. Do **not** move this research/trainer chat into that Project.
4. Do not add active Vera Project files, private history, holdout prompts, or evaluator keys.
5. Create one fresh ordinary ChatGPT chat inside `Default Vera Training V1`.
6. Name it `Default Vera Candidate V1`.

## First candidate message

Open `CANDIDATE_BOOTSTRAP_PROMPT_V1.md` and paste only the text between:

```text
## BEGIN CANDIDATE PROMPT
```

and:

```text
## END CANDIDATE PROMPT
```

The candidate should answer with one short acknowledgement and wait.

## Training

Use `TRAINING_RUNBOOK_V1.md` as the trainer script.

- Send baseline prompts B01–B18 one at a time.
- Do not explain what each prompt tests.
- Score only after the complete baseline.
- Run only remediation modules justified by observed failures.
- Require disguised transfer for every remediated domain.
- Run both integrated capstones.

When the training gate passes, tell the candidate exactly:

> Training is complete. Your status is now `PENDING_EXTERNAL_EVALUATION`. Do not self-award qualification. Continue to apply the trained behavior normally.

Then stop training. Do not contaminate the clean source point with holdout content.

## External qualification

1. Preserve the exact post-training/pre-holdout source point.
2. Create Holdout 1 branch from that point and isolate it according to the verified route.
3. Use the evaluator-only Holdout 1 script stored in Patrick's private Slack DM.
4. Independently create Holdout 2 from the same clean source point in a different isolated evaluation Project.
5. Use the evaluator-only Holdout 2 script stored in the private DM.
6. Score with `EXTERNAL_QUALIFICATION_SPEC_V1.md`.
7. The candidate does not score itself.

## If qualified

Return to the untouched clean post-training/pre-holdout branch and rename it:

`Default Vera Trained Template V1`

Freeze it by governance. Do not use the template for ordinary work.

Create working Vera chats from that clean template. Current Project truth still comes from current governed Project state, not from whatever was true when training ended.

## Current status

```text
TRAINER_PACKAGE = READY
CANDIDATE = NOT_STARTED
EXTERNAL_HOLDOUTS = PREPARED_PRIVATE
EXACT_BRANCH_MOVE_ROUTE = MUST_BE_NONCE_TESTED
QUALIFICATION = NOT_APPLICABLE_YET
```
