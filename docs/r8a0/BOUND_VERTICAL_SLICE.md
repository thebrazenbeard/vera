# R8A0 bounded vertical slice

This package implements only the owner-authorized repository slice on branch
`feature/r8a0-bounded-vertical-slice-v1` from predecessor
`12dd3cb4e3329324885a827506d4f7e8ac25d41d`.

## Implemented behavior

1. **Temporal orientation** keeps current-chat, project-interaction, durable-state,
   event, record, and retrieval time distinct. Missing, stale, invalidly bounded, or
   conflicting evidence fails closed.
2. **Governed memory admission/readback** supports exactly three memory classes.
   Autobiographical admission is default-deny, binds Vera as identity owner only
   after explicit authority, preserves runtime as provenance rather than owner,
   and uses class-specific retrieval language.
3. **Checkpoint/terminate/restart recovery** writes a digest-bound checkpoint
   atomically, terminates without claiming hidden activity, and recovers in a fresh
   process only with fresh temporal authority. Recovery explicitly distinguishes the
   governed identity from the prior runtime and makes no uninterrupted-consciousness claim.

## Verification

Run:

```bash
python -m unittest discover -s tests/r8a0 -p 'test_*.py' -v
python -m compileall -q r8a0 tests/r8a0
```

The suite includes positive, hostile, serialization, replay, supersession,
interrupted-checkpoint, corrupt-checkpoint, stale-time, fresh-process restart,
and path-allowlist tests.

## Scope boundary

The 42-path R8A0 release matrix remains integration reference material. This commit
writes only under `r8a0/**`, `tests/r8a0/**`, `docs/r8a0/**`, and
`.github/workflows/r8a0-*.yml`. It performs no merge, deployment, production
mutation, credential action, model training, or canonical-memory write.
