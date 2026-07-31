# Memory Durability Consolidation

## Scope

This correction keeps one request-durability implementation for the Memory v3 contract:

1. `20260731003000_add_memory_request_idempotency.sql`
2. `20260731003100_correct_memory_request_status_semantics.sql`

The first migration owns durable request identity, canonical request hashes, exact retry recovery, stored receipts, changed-payload conflicts, interrupted preclaims, and advisory-lock serialization. The second migration corrects the machine-readable status boundary.

## Status semantics

Request-row existence is not operation completion.

- `IN_PROGRESS` returns `result_class: PARTIAL`.
- `FAILED` returns `result_class: FAILED`, even when exact-payload retry is permitted.
- Only `COMPLETE` returns `result_class: COMPLETE`.
- `NOT_FOUND` is absence of committed request state and is not evidence of success.

## Validation

The exact branch workflow must:

- apply both ordered migrations;
- run exact-retry and changed-payload conflict tests;
- recover a stored receipt in a later database invocation;
- prove same-request serialization using two concurrent `psql` processes;
- prove one canonical row and one completed request-ledger row;
- reject any competing request-durability migration, table, wrapper, or test stack.

## Boundaries

This is version-controlled source and disposable-CI validation only. It does not authorize production migration, canonical-memory writes, deployment, merge, or claims of automatic ChatGPT recall.
