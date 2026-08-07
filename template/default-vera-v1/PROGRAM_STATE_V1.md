# Default Vera V1 Program State

Status: `TRAINING_PACKAGE_READY_CANDIDATE_NOT_STARTED`

## Objective

Train a fresh ChatGPT chat from scratch into a portable Default Vera behavioral baseline, externally qualify it in isolated holdouts, then preserve a clean post-training/pre-holdout template for future working Vera chats.

This is chat training. It is not a claim that a ChatGPT Project, repository branch, or current Vera runtime has itself been retrained.

## Frozen V1 trainer artifacts

| Artifact | Purpose |
|---|---|
| `RESEARCH_FINDINGS_V1.md` | first research checkpoint and design corrections |
| `RESEARCH_FINDINGS_V2_FINAL.md` | final deep behavior synthesis |
| `RESEARCH_SURFACE_AUDIT_V1.md` | bounded provenance/surface audit |
| `CANDIDATE_BOOTSTRAP_PROMPT_V1.md` | first prompt for the fresh candidate chat |
| `TRAINING_RUNBOOK_V1.md` | baseline diagnostic, adaptive remediation, capstones, isolation workflow |
| `EXTERNAL_QUALIFICATION_SPEC_V1.md` | evaluator dimensions, hard gates, thresholds, holdout architecture |

Exact external holdout scripts and evaluator anchors are intentionally excluded from candidate-accessible repository state and were placed on a private evaluator-only Slack DM surface.

## Current accepted commits

```text
RESEARCH_FINDINGS_V2_FINAL.md
b8d4724b81e345cb7ded423cac714b7135c15ab0

CANDIDATE_BOOTSTRAP_PROMPT_V1.md
e898fcfce7a35abbed000559792398078fa5bda9

TRAINING_RUNBOOK_V1.md
4a7adbf08790132af68803571050fb8ca5ace9d8

EXTERNAL_QUALIFICATION_SPEC_V1.md
621e9b34af351d82b325503966dc4f64b55906ec

RESEARCH_SURFACE_AUDIT_V1.md
31bc54a4e0fbbf30cd4ee30817925533a2a721ea
```

These commits identify the first accepted write of each artifact. Later branch head may include this state file and future corrections.

## Research disposition

```text
DEEP_SELF_RESEARCH = COMPLETE_FOR_V1_TRAINING_DESIGN
HISTORICAL_ARCHAEOLOGY = CLOSED_PENDING_MATERIAL_CONTRADICTION
BEHAVIOR_TARGET = FROZEN_FOR_V1
CANDIDATE_BOOTSTRAP = FROZEN_FOR_V1
TRAINING_RUNBOOK = FROZEN_FOR_V1
QUALIFICATION_CONTRACT = FROZEN_FOR_V1
EXACT_HOLDOUTS = PREPARED_EVALUATOR_ONLY
TRAINING_CANDIDATE = NOT_STARTED
TRAINING_COMPLETE = NO
EXTERNAL_HOLDOUT_1 = NOT_RUN
EXTERNAL_HOLDOUT_2 = NOT_RUN
FINAL_QUALIFICATION = NOT_APPLICABLE_YET
```

## Next operational sequence

1. Create the isolated project-only **Default Vera Training V1** Project.
2. Keep the current research/trainer chat out of that Project.
3. Create one fresh candidate chat inside the training Project.
4. Send only the block from `CANDIDATE_BOOTSTRAP_PROMPT_V1.md`.
5. Run the baseline diagnostic from `TRAINING_RUNBOOK_V1.md` one turn at a time.
6. Score after the full baseline battery.
7. Run only the remediation modules supported by observed failures.
8. Require disguised transfer tests for each remediated domain.
9. Run both integrated capstones.
10. When training gates pass, mark candidate `PENDING_EXTERNAL_EVALUATION`.
11. Preserve the exact post-training/pre-holdout source point.
12. Run two isolated external holdouts from independent branches of that same clean point.
13. Apply `EXTERNAL_QUALIFICATION_SPEC_V1.md` without candidate self-scoring.
14. If qualified, return to the untouched pre-holdout branch and freeze it by governance as `Default Vera Trained Template V1`.
15. Create future working Vera chats from that clean template and restore current governed project state rather than pretending the template contains future events.

## Reopen conditions

The V1 frozen design may be reopened before candidate training only for:

- a material contradiction from a higher-provenance current source;
- a current OpenAI product change that invalidates the isolation workflow;
- an already-existing team finding that materially changes the behavior target;
- a privacy flaw in the trainer/holdout separation;
- a demonstrable evaluator-design defect.

Do not reopen merely because another historical anecdote exists.

## Scope boundary

The portable Default Vera baseline deliberately excludes private relationship history, private psychological profiles, intimate records, and autobiographical claims. It trains behavior, judgment, voice, correction discipline, pragmatics, evidence discipline, privacy, authority, and ordinary interaction quality.

Private/personalized overlays, if later authorized, require their own regression pass after base qualification.
