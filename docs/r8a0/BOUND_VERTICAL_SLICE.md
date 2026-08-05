# R8A0 bounded vertical slice

This package implements the owner-authorized repository slice on branch
`feature/r8a0-bounded-vertical-slice-v1`.

## Implemented behavior

1. **Temporal orientation** preserves seven distinct dimensions: current wall-clock,
   current-chat, project-interaction, durable-state, event, record, and retrieval
   time. The wall-clock helper produces only current-time evidence. Every semantic
   time requires its own source kind and digest. Missing, stale, invalidly bounded,
   or conflicting evidence fails closed.
2. **Governed memory admission/readback** supports exactly three memory classes.
   Admission resolves authority and privacy from trusted registries whose records
   bind the exact request digest; request-supplied truth labels are not accepted.
   Stored request and record digests are revalidated before readback. Class-specific
   retrieval language is contract-exact.
3. **Checkpoint/terminate/restart recovery** writes an atomic checkpoint bound to a
   verified predecessor, self-model head, authority state, and memory head. Recovery
   requires the expected checkpoint digest, a digest-valid termination receipt,
   predecessor-chain agreement, verified current heads, and fresh temporal authority.
   It does not claim same-runtime continuation or uninterrupted consciousness.

## Verification

```bash
python -m unittest discover -s tests/r8a0 -p 'test_*.py' -v
python -m compileall -q r8a0 tests/r8a0
```

The suite includes positive and hostile tests for separate temporal evidence,
false autobiographical admission, exact-request authority/privacy binding, stored
record tampering, replay and supersession, termination enforcement, predecessor and
head mismatches, interrupted/corrupt checkpoints, fresh-process restart, strict JSON,
and path scope.

## Scope boundary

The 42-path R8A0 release matrix remains integration reference material. This bounded
slice writes only under `r8a0/**`, `tests/r8a0/**`, and `docs/r8a0/**` in its successor
repair. It performs no merge, deployment, production mutation, credential action,
model training, or canonical-memory write.
