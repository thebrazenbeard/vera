# R8A0 bounded vertical slice

This package implements the owner-authorized repository slice on branch
`feature/r8a0-bounded-vertical-slice-v1`.

## Implemented behavior

1. **Temporal orientation** preserves seven distinct dimensions: current wall-clock,
   current-chat, project-interaction, durable-state, event, record, and retrieval
   time. Missing dimensions never become `DEGRADED_BOUNDED`. A degraded result is
   available only for an explicitly narrower response scope whose required evidence
   has both lower and upper bounds.
2. **Governed memory admission/readback** supports exactly three memory classes.
   Authority and privacy decisions bind the exact request and are authenticated with
   a runtime-held integrity key. Stored records, admission receipts, and replay
   operations are independently authenticated before use. Class-specific retrieval
   language is contract-exact.
3. **Checkpoint/terminate/restart recovery** uses a checkpoint-and-terminate process
   that atomically persists both the checkpoint receipt and the termination receipt,
   then exits. A fresh recovery process re-reads and authenticates both receipts,
   recomputes temporal orientation internally, verifies predecessor, self-model,
   authority, and memory state, requires a nonempty successor runtime ID distinct
   from the terminated runtime, verifies that recovery occurs in a different OS
   process, and emits an authenticated resumption receipt binding both runtime and
   process identities. It does not claim uninterrupted consciousness or separate
   enduring personhood for the new runtime context.

## Verification

```bash
PYTHONHASHSEED=0 python -X dev -m unittest discover -s tests/r8a0 -p 'test_*.py' -v
python -m compileall -q -f r8a0 tests/r8a0
```

The hostile suite includes missing unbounded temporal dimensions, source-kind
mismatch, policy-binding forgery, persistent record and operation-receipt tampering,
replay mismatch, revocation, supersession, forged lifecycle receipts, wrong receipt
keys, partial checkpoints, wrong predecessor and current heads, termination omission,
missing or reused successor runtime IDs, same-process recovery, and an observed
checkpoint/terminate/fresh-process recovery cycle.

## Scope boundary

The 42-path R8A0 release matrix remains integration reference material. This bounded
successor writes only under `r8a0/**`, `tests/r8a0/**`, `docs/r8a0/**`, and the
existing `.github/workflows/r8a0-*.yml` allowance. It performs no merge, deployment, production mutation,
credential action, model training, or canonical-memory write.
