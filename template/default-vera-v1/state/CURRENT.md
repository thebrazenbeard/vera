# Default Vera Research Current State

State: `ACCEPTED_WORKING_PROJECT_STATE`

```yaml
schema: DEFAULT_VERA_RESEARCH_CURRENT_V1
current_checkpoint:
  checkpoint_id: DEFAULT_VERA_RESEARCH_CHECKPOINT_0001
  path: template/default-vera-v1/state/checkpoints/CHECKPOINT_0001_RESEARCH_RESTORE.md
  checkpoint_commit: a603c2e29e6baf6a54ca460ca61c8ff6f03aa79e
  writer_class: CURRENT_VERA_RESEARCH_CHAT
  memory_class: WORKING_PROJECT
  status: ACCEPTED_WORKING_PROJECT_RESTORE_POINT
research_state:
  deep_self_research: IN_PROGRESS
  research_pass_1: COMPLETE
  v0_architecture: SUPERSEDED
  research_revised_design: CURRENT_CANDIDATE_DESIGN
  hephaestus_architecture_audit: RECEIVED_AND_INCORPORATED
  final_initial_prompt: NOT_YET_FROZEN
  training_harness: NOT_YET_FROZEN
  training_candidate: NOT_STARTED
  external_qualification: NOT_APPLICABLE_YET
candidate_boundary:
  candidate_must_be_fresh_chat: true
  same_runtime_continuation_claim: false
  train_from_scratch_toward_researched_vera_baseline: true
  independently_verify_before_template_designation: true
branch:
  repository: thebrazenbeard/vera
  name: feature/default-vera-template-v1
  merged: false
  deployed: false
  installed: false
restore_entrypoint:
  first_read: template/default-vera-v1/state/CURRENT.md
  then_read_checkpoint: true
  then_read_design_artifacts: true
  task_relevant_shared_state_refresh: true
  full_new_chat_installation_audit: false
  basic_memory_cloud_query: false
```

## Restore instruction

A new Vera research chat should load this pointer, verify the referenced checkpoint commit, read the checkpoint and the current Default Vera design artifacts on the same branch, then resume the unfinished historical behavior research. It may claim durable working-project restoration only after that readback. It must not claim same-runtime continuity or private episodic recollection.

## Current next act

Continue the deeper historical behavior research before freezing the initial candidate prompt or creating the fresh training candidate.
