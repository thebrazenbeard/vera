# Memory Contract Review Summary

Status: READY_FOR_CI_AND_INDEPENDENT_REVIEW

Target branch: feature/memory-cross-chat-contract-v1
Base commit: a0def4c6009d86181664fe246ebb1b0f5df30cb2

The branch proposes a bounded neutral V3 memory correction. It adds explicit supersession lineage, append-only enforcement, database-assigned persistence time, receipt-producing save and recall functions, exact branch and privacy filtering, and isolated save/recall tests.

No production migration, production memory write, legacy-row mutation, merge, Time-system redesign, or Initiatives-system redesign is included.

Required review evidence:

- current state follows explicit lineage rather than timestamp recency;
- second roots, stale forks, and cross-branch predecessors are rejected;
- update and delete are blocked;
- client roles cannot access governed memory;
- save and recall each produce database-confirmed receipts;
- recall executes in a separate database invocation;
- superseded, foreign-branch, privacy-mismatched, rejected, disputed, and default-excluded model-generated records do not leak;
- database lint passes.

Known limitations:

- validation uses a disposable local Supabase stack;
- semantic expansion is deferred;
- automatic ChatGPT recall hooks are not implemented;
- production writer compatibility is not yet proven;
- real production cross-chat proof remains separately gated;
- temporal-field compatibility review is pending through the Supabase coordination ledger.
