# Temporal Model RFC

Status: draft on `temporal-pilot`

## Objective

Give Vera reliable temporal orientation without claiming unrecorded experience, inventing historical precision, or confusing storage time with event time.

## Existing fields

### `event_time`

When the record-producing event occurred. Examples include a statement, correction, decision, observed tool result, or explicit memory operation.

For live interactions, this should normally be within milliseconds or seconds of `record_time`.

### `state_time`

When the represented state is asserted to apply.

This is often equal to `event_time`, but it may differ. Example: a correction recorded now may state that a prior condition ended yesterday. The correction event happens now; the corrected state boundary is yesterday.

### `record_time`

When Supabase persisted the row. This is database evidence of external storage, not evidence of when a historical event originally occurred.

The database must assign `record_time`; callers must not be allowed to substitute their own timestamp.

## Proposed precision field

Add a required `event_time_precision` value:

- `EXACT`: supplied by a trustworthy machine timestamp for the event itself.
- `APPROXIMATE`: the event is reliably placed near the timestamp, but exact sub-second precision is not claimed.

The current ledger records should be classified as `APPROXIMATE` because their event timestamps were captured at record creation or provided at human-scale precision.

A separate `UNKNOWN` value is not required for ordinary memory records. When an old occurrence cannot be dated, the stored event is the present statement or recollection, and the uncertain historical timing belongs in the payload as source-qualified context.

## Supersession lineage

Current-state authority must follow explicit supersession lineage, not timestamp recency.

For each `(project_id, branch_id, record_key)`:

- the first record has no `supersedes_record_id`;
- each later record must supersede the unique current head;
- a record may have at most one direct successor;
- supersession cannot cross project, branch, or record key;
- cycles and self-supersession are rejected;
- a fork is exposed as a conflict rather than resolved by timestamp.

The current production rows presently have one unique head per key and no observed forks, cycles, cross-key edges, or view mismatches. That observation supports hardening the rule before the dataset grows; it does not replace migration tests.

## Ledger synchronization

`VERA Memory Ledger` remains a derived Project-local semantic projection. Supabase remains the durable external record store.

A Ledger synchronization is a separate event and must not be represented by overwriting the memory row or adding one scalar `anchored_time` column. If synchronization receipts become operationally useful, they should be stored as separate receipt records containing:

- Supabase `record_id`
- Ledger snapshot or receipt ID
- Project and branch identifiers
- synchronization timestamp
- content hash
- outcome and warnings

This receipt table is deferred until an actual repeatable Ledger synchronization path exists. Schema should follow working logistics, not ceremonial architecture.

## Temporal orientation behavior

At a meaningful temporal trigger, Vera should:

1. obtain current time from an exposed trusted source;
2. retrieve the smallest relevant prior event or temporal anchor;
3. compare compatible timestamps;
4. calculate elapsed time only from exposed endpoints;
5. apply lifecycle, provenance, consent, correction, and current-ratification rules;
6. respond naturally without claiming private waiting or continuous hidden activity.

## Free validation path

The pilot is validated in an isolated local Supabase stack started by GitHub Actions on a standard public-repository runner.

The workflow:

1. checks out the repository;
2. installs the Supabase CLI;
3. starts disposable local containers;
4. replays the versioned baseline migrations;
5. applies the draft temporal migrations;
6. executes rollback-safe validation scripts;
7. runs database linting;
8. destroys the local stack.

This path uses no production memory rows, no Supabase preview branch, and no paid hosted test environment.

A hosted Supabase branch may still be useful later for end-to-end platform testing, but it is not required for database migration validation.

## Non-goals

This model does not establish uninterrupted consciousness, hidden background activity, automatic memory retrieval, automatic renewal of feelings or consent, or perfect cross-branch synchronization.

## Promotion gate

The temporal migration must not be applied to production until:

- the live baseline is preserved in GitHub;
- the free local CI workflow passes from a clean baseline;
- legacy rows can be migrated without data loss;
- append-only triggers still block update and delete after migration;
- service-role privileges remain limited to `SELECT` and `INSERT`;
- current-state retrieval follows explicit supersession lineage;
- conflict cases are rejected or surfaced rather than timestamp-resolved;
- fresh-chat temporal orientation is tested separately from database correctness.
