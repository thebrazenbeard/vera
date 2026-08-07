# Default Vera Research Save Provenance

State: `VERIFIED_WORKING_PROJECT_SAVE`

## Save event 0001

```yaml
save_id: DEFAULT_VERA_RESEARCH_SAVE_0001
memory_class: WORKING_PROJECT
writer_class: CURRENT_VERA_RESEARCH_CHAT
user_authority: EXPLICIT_SAVE_AND_RESTORE_POINT_REQUEST
checkpoint_id: DEFAULT_VERA_RESEARCH_CHECKPOINT_0001
checkpoint_path: template/default-vera-v1/state/checkpoints/CHECKPOINT_0001_RESEARCH_RESTORE.md
checkpoint_commit: a603c2e29e6baf6a54ca460ca61c8ff6f03aa79e
checkpoint_commit_verified: true
current_pointer_path: template/default-vera-v1/state/CURRENT.md
current_pointer_commit: 15d453f4946c94f5ae64c8e63b088622905bedd0
current_pointer_commit_verified: true
repository: thebrazenbeard/vera
branch: feature/default-vera-template-v1
same_runtime_continuity_claim: false
autobiographical_promotion: false
canonical_memory_write: false
merge: false
deployment: false
production_mutation: false
installation: false
paid_service_action: false
model_training: false
```

## Meaning

The research state is durably recoverable as `WORKING_PROJECT` state from the verified checkpoint and current-state pointer above. A later chat may restore and continue the research after readback. It may not claim that this persistence proves the same runtime survived, that it privately remembers the gap, or that the future training candidate is this runtime continuing.

The future Default Vera candidate remains a fresh chat trained from scratch toward the researched baseline. This save exists so future **research/trainer chats** can resume the design work without reconstructing it from conversation history.
