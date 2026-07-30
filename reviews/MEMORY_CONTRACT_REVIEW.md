# Memory Contract Review Summary

Status: READY_FOR_CI_AND_INDEPENDENT_REVIEW

Target branch: `feature/memory-cross-chat-contract-v1`
Base commit: `a0def4c6009d86181664fe246ebb1b0f5df30cb2`

The branch proposes a bounded neutral V3 memory correction. It adds explicit supersession lineage, append-only enforcement, database-assigned persistence time, receipt-producing save and recall functions, exact branch and caller-authorized privacy matching, required source evidence and semantic indexing, hard model-output classification, and isolated save/recall tests.

No production migration, production memory write, legacy-row mutation, merge, Time-system redesign, or Initiatives-system redesign is included.

Required review evidence:

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
- database lint passes.

Known limitations:

- validation uses a disposable local Supabase stack;
- semantic expansion is deferred;
- automatic ChatGPT recall hooks are not implemented;
- durable request idempotency and a stored receipt ledger are not included in this slice;
- production writer compatibility is not yet proven;
- real production cross-chat proof remains separately gated;
- temporal-field compatibility review is pending through the Supabase coordination ledger.
