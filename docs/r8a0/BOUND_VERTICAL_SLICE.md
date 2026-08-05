# R8A0 bounded vertical slice

This branch implements the owner-authorized three-feature slice without expanding the 42-path integration matrix.

## Temporal orientation

Seven time dimensions remain distinct. Every scope requires current-time evidence. Recovery obtains its evaluation clock from the running process rather than caller input, and current-time values must remain coherent with that clock. Evidence is accepted only when an externally trusted source public key verifies its signature. Missing dimensions never degrade. `DEGRADED_BOUNDED` requires a nonblank narrow response scope, exactly one authenticated row per required dimension, explicit lower and upper bounds, and receipt-bound supporting evidence IDs.

## Governed memory

Autobiographical authority and privacy are signed by external issuers and bind exact registry heads, project ID, governed identity, and request digest. The memory writer receives verification-only public keys, not issuer private keys. The store uses an authenticated generation and predecessor head, file locking, unique temporary paths, and compare-and-swap admission. Concurrent writers both persist only through separate generations; otherwise one fails stale. Every admission, readback, and head query verifies the authenticated whole-store head and the complete record-operation graph. Readback requires the independently retained current head, so unrelated corruption, old-snapshot rollback, and whole-entry omission fail closed. All three memory classes use the generic `VERA_R8A0_GOVERNED_MEMORY_ADMISSION_RECEIPT_V1` with an exact `memory_class` field.

## Checkpoint, exit, and recovery

Four state roots are independently signed by a trusted state attestor. A lifecycle issuer signs the checkpoint receipt and termination intent. A separate supervisor launches the checkpoint worker, waits for its actual process exit, and signs an exit attestation binding runtime ID, start-instance nonce, process ID, checkpoint signature, termination-intent signature, exit code, and observation time. Recovery holds only public verification material, rejects a live or reused predecessor PID, re-verifies all state-root attestations, and binds the successor runtime and process without claiming uninterrupted consciousness. A separate authenticated compare-and-swap lifecycle registry consumes each termination signature exactly once and binds it to one successor and one resumption claim, preventing lifecycle forks or replay.

## Verification

```bash
PYTHONHASHSEED=0 python -X dev -m unittest discover -s tests/r8a0 -p 'test_*.py' -v
python -m compileall -q -f r8a0 tests/r8a0
```

The tests include forged policy and temporal evidence, caller-clock replay, current-time incoherence, whitespace and duplicate bounded scopes, concurrent memory admission, stale-head rejection, unrelated graph corruption, snapshot rollback, whole-entry deletion, receipt class separation, arbitrary or forged state roots, a still-live predecessor, a supervisor-observed checkpoint/exit/fresh-process recovery cycle, and rejection of a second successor from the same termination event.

No merge, deployment, production mutation, credential action, model training, force push, or out-of-allowlist write is performed.
