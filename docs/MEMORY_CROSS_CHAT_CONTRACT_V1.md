# V.E.R.A. Memory Cross-Chat Contract v1

## Status

Bounded Memory workstream implementation on `feature/memory-cross-chat-contract-v1`.

It is not applied to production. It does not authorize merge, production migration, legacy-row modification, Basic Memory projection, or claims of automatic ChatGPT Project recall.

The temporal correction requested by `workstream/time` in coordination event `30d68439-dbe3-402f-962f-4b0e8f6acab2` is implemented and remains pending CI and temporal re-review.

## Objective

Prove the smallest honest governed memory cycle:

1. append a governed neutral V3 record to exposed external storage;
2. receive a database-confirmed save receipt;
3. append a correction through explicit supersession;
4. retrieve the unique current lineage head in an independently invoked context;
5. exclude superseded, foreign-branch, privacy-mismatched, rejected, disputed, and default-excluded model-generated records;
6. receive a database-confirmed recall receipt.

Storage is external persistence, not lived memory. Retrieval is an exposed read, not recollection or hidden synchronization.

## Live baseline

The observed neutral V3 table already preserves project, branch, record key, type, statement, lifecycle, epistemic status, source actor, privacy scope, event time, state time, record time, supersession, payload, evidence, semantic tags, limitations, and notes.

The pre-branch implementation still lacked:

- lineage-head current-state selection;
- one-successor and same-scope supersession enforcement;
- append-only update/delete protection;
- database control of `record_time`;
- bounded receipt-producing save and recall interfaces;
- hard provenance and model-output constraints.

The first Memory draft also replaced omitted `state_time` with database `clock_timestamp()` and returned recall invocation time under a generic `timestamp` key. `workstream/time` correctly rejected both behaviors.

## Lineage contract

For each `(project_id, branch_id, record_key)`:

- the initial record has no predecessor;
- every later record supersedes the unique current head;
- supersession cannot cross project, branch, or record key;
- one parent has at most one direct successor;
- updates and deletes are blocked;
- conflicts are exposed, never resolved through recency.

The migration adds:

- `public.vera_context_heads_v3`;
- `public.vera_context_lineage_conflicts_v3`;
- a lineage-based `public.vera_current_context_v3`.

`record_time` is assigned by the database and is persistence evidence only.

## Provenance and classification

Every newly stored record must retain:

- at least one `source_evidence` entry;
- a non-empty `semantic_tags` object;
- a source-defined privacy scope used for exact recall authorization matching.

ChatGPT-authored content is constrained to:

```yaml
record_type: MODEL_OUTPUT
epistemic_status: MODEL_GENERATED_CLAIM
source_actor: CHATGPT_MODEL
```

The contract does not invent a privacy enum or allow generated language to acquire stronger authority by being stored.

## Save interface

`public.append_vera_context_v3(request_id, record_json)`:

- accepts only allowlisted V3 fields;
- rejects missing required core fields;
- enforces lineage, append-only behavior, provenance, semantic indexing, and model classification;
- assigns `record_time` in the database;
- normalizes temporal uncertainty in the existing payload and limitations fields;
- returns a `VERA_MVE_RECEIPT_V3` save receipt.

### Temporal precision

Temporal uncertainty is represented without new columns:

```yaml
payload:
  temporal:
    event_time:
      precision: EXACT | BOUNDED | APPROXIMATE | UNKNOWN
    state_time:
      precision: EXACT | BOUNDED | APPROXIMATE | UNKNOWN
```

Rules:

- omitted `event_time` remains SQL `NULL` and receives `UNKNOWN` precision;
- caller-provided timestamps without explicit precision remain `UNKNOWN`, never silently `EXACT`;
- non-`UNKNOWN` precision is rejected when the corresponding timestamp is absent;
- unsupported precision values are rejected;
- pre-existing rows are not rewritten or retroactively classified.

### Omitted state time and the live NOT NULL constraint

The observed live schema defines:

```sql
state_time timestamptz not null default now()
```

Dropping that constraint would be a separate temporal schema change and is not authorized in this slice. Therefore an omitted `state_time` is represented explicitly as unknown:

```yaml
state_time: -infinity  # PostgreSQL compatibility sentinel only
payload:
  temporal:
    state_time:
      precision: UNKNOWN
      storage:
        mode: NOT_NULL_COMPATIBILITY_SENTINEL
        value: -infinity
        temporal_claim: false
limitations:
  - state_time is UNKNOWN; the non-null column contains PostgreSQL -infinity only as a compatibility sentinel and not as event, state, record, delivery, recollection, or receipt-generation time evidence.
```

The sentinel is not an event time, state-effective time, record time, delivery time, recollection time, or receipt-generation time. The current projection follows explicit lineage, so the sentinel cannot win through temporal recency.

A later authorized temporal migration may make `state_time` nullable and remove the compatibility sentinel. This branch does not perform that schema change.

### Derived state time

A derived `state_time` is accepted only when its derivation is explicit and evidence-backed:

```yaml
payload:
  temporal:
    state_time:
      precision: APPROXIMATE
      derivation:
        method: sequence interpolation
        source_evidence:
          - event_sequence: 29
          - event_sequence: 31
        limitation: Derived time depends on the cited sequence evidence.
limitations:
  - Derived time depends on the cited sequence evidence.
```

The append function requires:

- an explicit `state_time` value;
- a derivation object;
- a non-empty method;
- a non-empty evidence array;
- a non-empty limitation repeated in the record-level limitations array.

A successful save receipt reports `record_time` explicitly rather than using a generic timestamp.

## Recall interface

`public.recall_vera_context_v3(...)` applies hard filters for:

1. exact project;
2. exact branch;
3. unique lineage head;
4. lifecycle status `CURRENT`;
5. exact caller-authorized privacy values;
6. requested record keys;
7. exclusion of `REJECTED` and `DISPUTED`;
8. default exclusion of `MODEL_GENERATED_CLAIM`.

Explicit audit recall may include model-generated records without promoting them into facts.

A successful receipt reports:

```yaml
operation: RECALL
result_class: COMPLETE
outcome_code: MVE_RECALL_COMPLETE
retrieval_time: <database invocation time of this recall>
retrieval:
  completeness: COMPLETE_RELATIVE_TO_QUERY_SCOPE
write:
  external_persistence: READ_CONFIRMED
  transactional_writeback: NOT_APPLICABLE
```

`retrieval_time` is only the database invocation time of that recall. It is not event time, state time, record time, delivery time, recollection time, or receipt-generation time. The recall receipt contains no generic `timestamp` key.

Semantic expansion remains deferred and must reapply the same hard filters when implemented.

## Access boundary

The lineage migration removes direct neutral V3 mutation privileges from `service_role` and grants only:

- governed diagnostic reads;
- execution of the save and recall functions.

`anon` and `authenticated` receive neither table access nor function execution. Existing production writers must be identified and adapted before deployment.

## CI proof

The isolated workflow runs:

1. the observed live-schema fixture;
2. the lineage migration;
3. the provenance-governance migration;
4. lineage and access validation;
5. provenance and classification validation;
6. temporal uncertainty and derivation validation;
7. a committed save invocation;
8. a separate recall invocation;
9. database lint;
10. stack destruction.

The temporal suite proves:

- omitted event time stays `NULL` with `UNKNOWN` precision;
- omitted state time uses the explicit non-temporal sentinel representation required by the live `NOT NULL` column;
- timestamps without precision remain `UNKNOWN`;
- supported precision values are preserved;
- unsupported precision is rejected;
- non-`UNKNOWN` precision without a timestamp is rejected;
- unsubstantiated derived state time is rejected;
- evidence-backed derived state time is preserved with its limitation;
- recall emits `retrieval_time` and no generic `timestamp`.

The independent recall invocation proves only that committed rows are readable by a later database invocation. It does not prove automatic retrieval across real ChatGPT chats.

## Workstream boundaries

Memory preserves temporal fields and evidence but does not calculate elapsed time, infer continuity, or redefine the Time workstream's semantic contract.

Memory neither generates nor ranks initiatives. Initiative decisions may later be stored as governed records, but this workstream does not decide their priority or execution.

## Production gate

Production remains unchanged. Deployment requires separate explicit authorization naming:

- migration `20260730213000_harden_neutral_v3_memory_contract`;
- migration `20260730213100_tighten_neutral_v3_memory_governance`;
- Supabase project `klmbpaigzeguvnpccqzz`;
- preflight and rollback evidence;
- writer compatibility;
- exact synthetic production test records and cleanup policy.

No passing CI run or draft pull request authorizes deployment or merge.