# Memory Contract Review Summary

Status: TEMPORAL_CORRECTION_PENDING_CI_AND_RE_REVIEW

Target branch: `feature/memory-cross-chat-contract-v1`  
Base commit: `a0def4c6009d86181664fe246ebb1b0f5df30cb2`  
Temporal review event: `30d68439-dbe3-402f-962f-4b0e8f6acab2`

The branch proposes a bounded neutral V3 memory correction. It adds explicit supersession lineage, append-only enforcement, database-assigned persistence time, receipt-producing save and recall functions, exact branch and caller-authorized privacy matching, required source evidence and semantic indexing, hard model-output classification, explicit temporal uncertainty, and isolated save/recall tests.

No production migration, production memory write, legacy-row mutation, merge, Time-system redesign, Initiatives-system redesign, or temporal column-schema change is included.

## Required review evidence

- current state follows explicit lineage rather than timestamp recency;
- second roots, stale forks, and cross-branch predecessors are rejected;
- update and delete are blocked;
- source evidence and semantic tags cannot be empty;
- ChatGPT-authored content cannot be inserted with stronger authority than `MODEL_OUTPUT` / `MODEL_GENERATED_CLAIM`;
- privacy filtering uses exact values supplied in the caller-authorized set without inventing a neutral privacy enum;
- client roles cannot access governed memory;
- save and recall each produce database-confirmed receipts;
- recall executes in a separate database invocation;
- superseded, foreign-branch, privacy-mismatched, rejected, disputed, and default-excluded model-generated records do not leak;
- omitted `event_time` remains `NULL` with `UNKNOWN` precision;
- because the observed live `state_time` column is `NOT NULL`, omitted `state_time` is represented as `UNKNOWN` using a PostgreSQL `-infinity` compatibility sentinel plus machine-readable `temporal_claim: false` metadata and an appended limitation;
- the compatibility sentinel is never described as event, state, record, delivery, recollection, or receipt-generation time evidence;
- supplied timestamps without explicit precision remain `UNKNOWN`, never silently `EXACT`;
- supported precision values are limited to `EXACT`, `BOUNDED`, `APPROXIMATE`, and `UNKNOWN`;
- non-`UNKNOWN` precision is rejected when its timestamp is absent;
- derived `state_time` requires a method, non-empty evidence, and a matching record limitation;
- recall returns invocation time only as `retrieval_time` and contains no generic `timestamp`;
- database lint passes.

## Known limitations

- validation uses a disposable local Supabase stack;
- the live `state_time NOT NULL` constraint prevents literal `NULL` without a separately authorized temporal schema migration;
- semantic expansion is deferred;
- automatic ChatGPT recall hooks are not implemented;
- durable request idempotency and a stored receipt ledger are not included in this slice;
- production writer compatibility is not yet proven;
- real production cross-chat proof remains separately gated;
- temporal compatibility is not approved until `workstream/time` re-reviews the immutable corrected head.