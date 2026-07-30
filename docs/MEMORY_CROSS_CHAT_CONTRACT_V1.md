# V.E.R.A. Memory Cross-Chat Contract v1

## Status

Bounded Memory workstream implementation on `feature/memory-cross-chat-contract-v1`.

It is not applied to production. It does not authorize merge, production migration, legacy-row modification, Basic Memory projection, or claims of automatic ChatGPT Project recall.

The temporal-field correction requested by `workstream/time` in coordination event `30d68439-dbe3-402f-962f-4b0e8f6acab2` is implemented on the branch and remains pending CI and temporal re-review.

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

The first Memory draft also contained two temporal defects found during `workstream/time` review:

- omitted `state_time` was replaced with database `clock_timestamp()`, inventing an exact state-effective time;
- recall invocation time was returned through an ambiguous generic `timestamp` key.

The uploaded R6A0 package was a validated local candidate that explicitly reported no production changes. The live Supabase project has since advanced beyond that package by installing neutral V3, so this branch treats the live database as the current implementation baseline while preserving R6A0 governance.

## Database contract

### Baseline preflight

The lineage migration refuses to apply when the existing table contains:

- self-supersession;
- cross-project, cross-branch, or cross-key supersession;
- more than one direct successor for a parent;
- more than one lineage head for a scoped record key.

The companion governance migration refuses to apply when the existing table contains:

- empty source-evidence arrays;
- empty semantic-tag objects;
- ChatGPT-authored content classified as anything other than `MODEL_OUTPUT` with epistemic status `MODEL_GENERATED_CLAIM`;
- `MODEL_OUTPUT` records promoted beyond `MODEL_GENERATED_CLAIM`.

These checks prevent the migrations from quietly blessing an ambiguous or under-sourced baseline.

### Append-only lineage

For each `(project_id, branch_id, record_key)`:

- the initial record has no predecessor;
- every later record supersedes the unique current head;
- supersession cannot cross project, branch, or record key;
- a parent can have only one direct successor;
- updates and deletes are blocked;
- conflicts are exposed rather than resolved through timestamp recency.

`record_time` is overwritten by the database during insertion. It is persistence evidence, not caller testimony.

### Provenance and classification

Every newly stored record must retain:

- at least one `source_evidence` entry;
- a non-empty `semantic_tags` object;
- its supplied privacy scope for exact authorization matching during recall.

The contract does not invent a neutral privacy enum. `privacy_scope` remains source-defined data, and recall returns a record only when its exact value is included in the caller-authorized privacy-scope set.

ChatGPT-authored content is constrained to:

```yaml
record_type: MODEL_OUTPUT
epistemic_status: MODEL_GENERATED_CLAIM
source_actor: CHATGPT_MODEL
```

This prevents insertion-time promotion of generated language into stronger factual or subjective-state authority.

### Current projection

The lineage migration adds:

- `public.vera_context_heads_v3`;
- `public.vera_context_lineage_conflicts_v3`;
- a lineage-based replacement for `public.vera_current_context_v3`.

The current projection returns one unambiguous unsuperseded head per project, branch, and record key. `state_time`, `record_time`, and UUID order do not override explicit lineage.

## Save interface

`public.append_vera_context_v3(request_id, record_json)`:

- accepts only an allowlisted V3 field set;
- rejects missing required core fields;
- relies on V3 type, JSON-shape, provenance, semantic-index, and model-classification constraints;
- applies database lineage and append-only enforcement;
- assigns persistence time in the database;
- preserves omitted `event_time` and `state_time` as `NULL`;
- stores temporal precision under `payload.temporal`;
- returns a `VERA_MVE_RECEIPT_V3` save receipt containing the stored record ID and stored row.

### Temporal precision

Temporal uncertainty uses the existing payload boundary rather than adding columns:

```yaml
payload:
  temporal:
    event_time:
      precision: EXACT | BOUNDED | APPROXIMATE | UNKNOWN
    state_time:
      precision: EXACT | BOUNDED | APPROXIMATE | UNKNOWN
```

Rules:

- omitted times remain SQL `NULL` and are stored with `UNKNOWN` precision;
- caller-provided timestamps without an explicit supported precision are stored as `UNKNOWN`, never silently promoted to `EXACT`;
- non-`UNKNOWN` precision is rejected when the corresponding timestamp is absent;
- unsupported precision values are rejected;
- existing pre-migration records are not rewritten or retroactively classified.

A derived `state_time` is represented inside the existing payload and limitations boundaries:

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

The append interface accepts a derivation only when:

- `state_time` is explicitly supplied;
- `derivation` is an object;
- `method` is non-empty;
- `source_evidence` is a non-empty array;
- `limitation` is non-empty and appears in the record-level `limitations` array.

A successful save receipt reports:

```yaml
operation: SAVE
result_class: COMPLETE
outcome_code: MVE_SAVE_COMPLETE
record_time: <database persistence time>
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
5. exact membership in the caller-authorized privacy-scope set;
6. exact requested record keys when supplied;
7. exclusion of `REJECTED` and `DISPUTED` epistemic states;
8. exclusion of `MODEL_GENERATED_CLAIM` by default.

Model-generated records remain available for explicit audit recall by setting `include_model_generated = true`. This does not promote them into facts or active subjective-state evidence.

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

`retrieval_time` is only the database invocation time of that recall operation. It is not:

- `event_time`;
- `state_time`;
- `record_time`;
- delivery time;
- recollection time;
- receipt-generation time.

The recall receipt no longer contains the ambiguous generic `timestamp` key.

This bounded function performs exact-key retrieval. Semantic expansion remains a later Memory slice and must reapply the same governance filters after expansion.

## Access boundary

The proposed lineage migration removes direct neutral V3 mutation privileges from `service_role` and grants:

- table and view reads for governed diagnostics;
- execution of the receipt-producing save and recall functions.

`anon` and `authenticated` receive neither table access nor function execution.

This is intentionally a compatibility gate. Any existing production writer that directly inserts as `service_role` must be identified and adapted before production deployment.

## Independent invocation proof

The CI workflow uses an isolated local Supabase stack and runs:

1. a fixture reproducing the observed live neutral V3 schema;
2. the bounded lineage migration;
3. the bounded provenance-governance migration;
4. adversarial structural, lineage, access, and append-only validation;
5. adversarial provenance and model-classification validation;
6. adversarial temporal-field and derivation validation;
7. a first `psql` invocation that commits governed test records and verifies save receipts;
8. a separate `psql` invocation that recalls the committed records and verifies recall receipts;
9. database lint;
10. stack destruction.

The recall invocation proves that retrieval does not depend on transaction-local variables or one model turn. It does not yet prove persistence across real ChatGPT chats because production application and a production test write remain separately gated.

## Tested exclusion and temporal cases

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
- empty source evidence is rejected;
- empty semantic indexing is rejected;
- model output cannot be inserted with stronger authority;
- client roles cannot access governed memory;
- omitted event and state times remain `NULL` with `UNKNOWN` precision;
- supplied timestamps without precision remain `UNKNOWN`, not silently `EXACT`;
- explicit `EXACT`, `BOUNDED`, and `APPROXIMATE` values are preserved;
- unsupported temporal precision is rejected;
- a derived `state_time` without evidence and a matching limitation is rejected;
- an evidence-backed derived `state_time` is preserved with its limitation;
- recall emits `retrieval_time` and no generic `timestamp`;
- save and recall each emit externally verifiable receipts.

## Temporal boundary

Memory preserves temporal content without interpreting temporal meaning beyond the supplied evidence:

- source-supported `event_time`, or `NULL` when absent;
- represented `state_time`, or `NULL` when absent;
- explicit precision metadata: `EXACT`, `BOUNDED`, `APPROXIMATE`, or `UNKNOWN`;
- explicit evidence and limitations for derived `state_time`;
- database-assigned `record_time` as persistence evidence;
- explicit `retrieval_time` as recall-invocation evidence.

Memory does not calculate elapsed time, infer continuity, convert missing time into database now, or silently assign exact precision. Temporal meaning and precision rules remain subject to `workstream/time` review.

## Initiatives boundary

This contract neither generates nor ranks initiatives. Initiative decisions may later be stored as governed records, but the Memory workstream does not determine their objective, priority, or execution policy.

## Production gate

Production remains unchanged. Deployment requires a separate explicit authorization naming:

- migration `20260730213000_harden_neutral_v3_memory_contract`;
- migration `20260730213100_tighten_neutral_v3_memory_governance`;
- Supabase project `klmbpaigzeguvnpccqzz`;
- exact preflight and rollback evidence;
- writer-compatibility result;
- exact synthetic production test record, branch, privacy scope, and cleanup/tombstone policy.

No passing CI run or draft pull request authorizes deployment or merge.