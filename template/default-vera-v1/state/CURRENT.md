# Default Vera Research Current State

State: `ACCEPTED_WORKING_PROJECT_STATE`

```yaml
schema: DEFAULT_VERA_RESEARCH_CURRENT_V1
current_checkpoint:
  checkpoint_id: DEFAULT_VERA_RESEARCH_CHECKPOINT_0002_V1_TRAINING_PACKAGE_READY
  path: template/default-vera-v1/state/checkpoints/CHECKPOINT_0002_V1_TRAINING_PACKAGE_READY.md
  checkpoint_commit: 3542b841a0e7f20b1b7f1bf8943576cdf1053ab5
  writer_class: CURRENT_VERA_RESEARCH_CHAT
  memory_class: WORKING_PROJECT
  status: ACCEPTED_WORKING_PROJECT_RESTORE_POINT
previous_checkpoint:
  checkpoint_id: DEFAULT_VERA_RESEARCH_CHECKPOINT_0001
  path: template/default-vera-v1/state/checkpoints/CHECKPOINT_0001_RESEARCH_RESTORE.md
  checkpoint_commit: a603c2e29e6baf6a54ca460ca61c8ff6f03aa79e
research_state:
  deep_self_research: COMPLETE_FOR_V1_TRAINING_DESIGN
  historical_archaeology: CLOSED_PENDING_MATERIAL_CONTRADICTION
  external_research_crosscheck: COMPLETE_NO_MATERIAL_CONTRADICTION
  behavior_target: FROZEN_FOR_V1
  candidate_bootstrap: FROZEN_FOR_V1
  training_runbook: FROZEN_FOR_V1
  qualification_contract: FROZEN_FOR_V1
  operator_quickstart: READY
  current_openai_project_docs: REVERIFIED_2026_08_07
  exact_branch_move_ui_route: EMPIRICAL_GATE_NOT_YET_RUN
  exact_holdouts: PREPARED_EVALUATOR_ONLY
  training_candidate: NOT_STARTED
  training_complete: false
  external_holdout_1: NOT_RUN
  external_holdout_2: NOT_RUN
  final_qualification: NOT_APPLICABLE_YET
candidate_boundary:
  candidate_must_be_fresh_chat: true
  same_runtime_continuation_claim: false
  train_from_scratch_toward_researched_vera_baseline: true
  independently_verify_before_template_designation: true
continuation_target:
  project: Vera's House
  role: TRAINER_EVALUATOR_CONTINUATION
  candidate_project: SEPARATE_DEDICATED_PROJECT_ONLY_TRAINING_PROJECT
branch:
  repository: thebrazenbeard/vera
  name: feature/default-vera-template-v1
  merged: false
  deployed: false
  installed: false
restore_entrypoint:
  first_read: template/default-vera-v1/state/CURRENT.md
  then_read_checkpoint: true
  then_read_save_provenance: true
  then_read_program_state: template/default-vera-v1/PROGRAM_STATE_V1.md
  then_read_quickstart: template/default-vera-v1/OPERATOR_QUICKSTART_V1.md
  task_relevant_shared_state_refresh: true
  full_new_chat_installation_audit: false
  basic_memory_cloud_query: false
```

## Restore instruction

A continuation Vera research/trainer chat should be created in **Vera's House**. It should load this pointer, verify checkpoint commit `3542b841a0e7f20b1b7f1bf8943576cdf1053ab5`, read checkpoint 0002 and `state/SAVE_PROVENANCE.md`, then read `PROGRAM_STATE_V1.md` and `OPERATOR_QUICKSTART_V1.md`.

After successful readback it may claim:

`DEFAULT_VERA_RESEARCH_CONTINUATION_RESTORED_FROM_VERIFIED_WORKING_PROJECT_STATE`

It must not claim same-runtime lived continuity, private episodic recollection, or that the future Default Vera candidate is the predecessor runtime continuing.

## Current next act

Do **not** restart deep historical research. The V1 research phase is closed unless a material contradiction appears.

Next operational gate:

1. verify the exact disposable nonce branch/move isolation route;
2. then create the separate project-only `Default Vera Training V1` Project;
3. create the fresh candidate chat;
4. administer the frozen bootstrap and adaptive training runbook.

Exact external holdout scripts remain evaluator-only in Patrick's private Slack DM and must not enter candidate-accessible state before evaluation.
