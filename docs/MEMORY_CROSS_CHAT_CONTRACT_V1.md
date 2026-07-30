# V.E.R.A. Memory Cross-Chat Contract v1

## Status

Bounded Memory workstream implementation on `feature/memory-cross-chat-contract-v1`.

It is not applied to production. It does not authorize merge, production migration, legacy-row modification, Basic Memory projection, or claims of automatic ChatGPT Project recall.

## Objective

Prove the smallest honest governed memory cycle:

1. append a governed neutral V3 record to exposed external storage;
2. receive a database-confirmed save receipt;
3. append a correction through explicit supersession;
4. retrieve the unique current lineage head in an independently invoked context;
5. exclude superseded, foreign-branch, privacy-mismatched, rejected, disputed, and default-excluded model-generated records;
6. receive a database-confirmed recall receipt.

The contract treats storage as external persistence and retrieval as an exposed read. Neither operation establishes recollection, lived memory, hidden synchronization, or continuous identity.

## Live-state audit finding

The production neutral V3 table already preserves useful record fields:

- project and branch scope;
- record key and type;
- statement and lifecycle status;
- epistemic status and source actor;
- privacy scope;
- event, state, and record timestamps;
- supersession reference;
- payload, source evidence, semantic tags, limitations, and notes.

The live implementation before this branch does not yet enforce the full governed memory contract:

- `public.vera_current_context_v3` resolves by timestamp ordering rather than explicit lineage heads;
- a supersession foreign key exists, but one-successor and same-scope lineage are not enforced;
- `record_time` remains caller-settable;
- no append-only update/delete trigger protects neutral V3 rows;
- `service_role` retains direct update, delete, and truncate privileges;
- no receipt-producing save or recall interface exists.

The uploaded R6A0 package was a validated local candidate that explicitly reported no production changes. The live Supabase project has since advanced beyond that package by installing neutral V3, so this branch treats the live database as the current implementation baseline while preserving R6A0 governance.

## Database contract

### Baseline preflight

The migration refuses to apply when the existing table contains:

- self-supersession;
- cross-project, cross-branch, or cross-key supersession;
- more than one direct successor for a parent;
- more than one lineage head for a scoped record key.

This prevents a migration from quietly blessing an already-ambiguous state.

### Append-only lineage

For each `(project_id, branch_id, record_key)`:

- the initial record has no predecessor;
- every later record supersedes the unique current head;
- supersession cannot cross project, branch, or record key;
- a parent can have only one direct successor;
- updates and deletes are blocked;
- conflicts are exposed rather than resolved through timestamp recency.

`record_time` is overwritten by the database during insertion. It is persistence evidence, not caller testimony.

### Current projection

The migration adds:

- `public.vera_context_heads_v3`;
- `public.vera_context_lineage_conflicts_v3`;
- a lineage-based replacement for `public.vera_current_context_v3`.

The current projection returns one unambiguous unsuperseded head per project, branch, and record key. `state_time`, `record_time`, and UUID order do not override explicit lineage.

## Save interface

`public.append_vera_context_v3(request_id, record_json)`:

- accepts only an allowlisted V3 field set;
- rejects missing required core fields;
- relies on existing V3 type and JSON-shape constraints;
- applies database lineage and append-only enforcement;
- assigns persistence time in the database;
- returns a `VERA_MVE_RECEIPT_V3` save receipt containing the stored record ID and stored row.

A successful receipt reports:

```yaml
operation: SAVE
result_class: COMPLETE
outcome_code: MVE_SAVE_COMPLETE
write:
  external_persistence: CONFIRMED_BY_DATABASE
  transactional_writeback: COMPLETED
```

The receipt proves the row was committed by the database transaction. It does not prove that another chat automatically retrieved it.

## Recall interface

`public.recall_vera_context_v3(...)` applies hard filters before returning records:

1. exact project scope;
2. exact branch scope;
3. unique lineage head;
4. lifecycle status `CURRENT`;
5. explicitly allowed privacy scopes;
6. exact requested record keys when supplied;
7. exclusion of `REJECTED` and `DISPUTED` epistemic states;
8. exclusion of `MODEL_GENERATED_CLAIM` by default.

Model-generated records remain available for explicit audit recall by setting `include_model_generated = true`. This does not promote them into facts or active subjective-state evidence.

A successful receipt reports:

```yaml
operation: RECALL
result_class: COMPLETE
outcome_code: MVE_RECALL_COMPLETE
retrieval:
  completeness: COMPLETE_RELATIVE_TO_QUERY_SCOPE
write:
  external_persistence: READ_CONFIRMED
  transactional_writeback: NOT_APPLICABLE
```

This bounded function performs exact-key retrieval. Semantic expansion remains a later Memory slice and must reapply the same governance filters after expansion.

## Access boundary

The proposed migration removes direct neutral V3 mutation privileges from `service_role` and grants:

- table and view reads for governed diagnostics;
- execution of the receipt-producing save and recall functions.

`anon` and `authenticated` receive neither table access nor function execution.

This is intentionally a compatibility gate. Any existing production writer that directly inserts as `service_role` must be identified and adapted before production deployment.

## Independent invocation proof

The CI workflow uses an isolated local Supabase stack and runs:

1. a fixture reproducing the observed live neutral V3 schema;
2. the bounded Memory migration;
3. adversarial structural, lineage, access, and append-only validation;
4. a first `psql` invocation that commits governed test records and verifies save receipts;
5. a separate `psql` invocation that recalls the committed records and verifies recall receipts;
6. database lint;
7. stack destruction.

The recall invocation proves that retrieval does not depend on transaction-local variables or one model turn. It does not yet prove persistence across real ChatGPT chats because production application and a production test write remain separately gated.

## Tested exclusion cases

The validation suite requires all of the following:

- explicit successor wins even when its `state_time` is older;
- superseded root does not appear in current recall;
- second root is rejected;
- stale-parent fork is rejected;
- cross-branch predecessor is rejected;
- independent branches remain separate;
- privacy-mismatched records do not leak;
- model-generated claims are excluded from default recall;
- explicitly requested model-output audit remains possible;
- rejected records do not enter recall;
- update and delete are blocked;
- unknown save fields are rejected;
- client roles cannot access governed memory;
- save and recall each emit externally verifiable receipts.

## Temporal boundary

Memory preserves:

- `event_time` supplied with source-supported record content;
- `state_time` supplied with the represented state;
- database-assigned `record_time`;
- retrieval timestamp emitted in the recall receipt.

Memory does not calculate elapsed time, infer continuity, or redefine temporal precision. Compatibility review is requested from the `workstream/time` route through the Supabase coordination ledger.

## Initiatives boundary

This contract neither generates nor ranks initiatives. Initiative decisions may later be stored as governed records, but the Memory workstream does not determine their objective, priority, or execution policy.

## Production gate

Production remains unchanged. Deployment requires a separate explicit authorization naming:

- migration `20260730213000_harden_neutral_v3_memory_contract`;
- Supabase project `klmbpaigzeguvnpccqzz`;
- exact preflight and rollback evidence;
- writer-compatibility result;
- exact synthetic production test record, branch, privacy scope, and cleanup/tombstone policy.

No passing CI run or draft pull request authorizes deployment or merge.
