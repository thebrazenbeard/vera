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

## Canonical temporal evidence precision

The active R5A2 temporal owner defines evidence confidence as:

- `EXACT`: the event timestamp and its precision are directly supported by a trustworthy source.
- `BOUNDED`: the event is known to fall within an inclusive lower and upper timestamp.
- `APPROXIMATE`: the timestamp is a useful estimate, but defensible hard bounds are unavailable.
- `UNKNOWN`: the available evidence does not support a precision classification.

`RANGE` is not a peer precision category. It is the storage representation of `BOUNDED` evidence.

The database stores bounded evidence with:

- `event_time_lower_bound`: inclusive earliest supported timestamp;
- `event_time_upper_bound`: inclusive latest supported timestamp;
- `event_time`: the best supported timestamp, constrained to lie inside the interval.

Both bound columns are required for `BOUNDED` evidence and must be `NULL` for `EXACT`, `APPROXIMATE`, and `UNKNOWN` evidence. Lower bounds may not exceed upper bounds.

Existing ledger rows are conservatively backfilled as `APPROXIMATE` with no bounds. The migration does not retroactively claim exactness or invent an interval that was never recorded.

Elapsed-result status is a separate concept owned by the R5A2 temporal runtime:

- `EXACT`
- `BOUNDED`
- `APPROXIMATE`
- `UNAVAILABLE`
- `CONFLICTED`

Those result statuses are not stored in `event_time_precision`.

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

The R5A2 Project-native runtime already specifies this behavior. This database pilot hardens durable event storage and lineage; it does not by itself provide general branch/session identity, automatic anchor creation, or end-to-end runtime execution.

## Reproducible free validation path

The pilot is validated in an isolated local Supabase stack started by GitHub Actions on a standard public-repository runner.

The workflow:

1. checks out the repository;
2. installs and verifies Supabase CLI `2.101.0`;
3. starts disposable local containers;
4. replays the versioned baseline migrations;
5. loads representative legacy rows;
6. applies the promoted temporal migrations;
7. validates legacy preservation, precision and bounds, lineage, privileges, append-only enforcement, and lint;
8. destroys the local stack.

This path uses no production memory rows, no Supabase preview branch, and no paid hosted test environment.

A hosted Supabase branch may still be useful later for end-to-end platform testing, but it is not required for database migration validation.

## Non-goals

This model does not establish uninterrupted consciousness, hidden background activity, automatic memory retrieval, automatic renewal of feelings or consent, perfect cross-branch synchronization, or a proven Ledger restore path.

Durable branch/session anchoring is a later architecture phase and must not be smuggled into this bounded correction cycle.

## Promotion gate

The temporal migration must not be applied to production until:

- the live baseline is preserved in GitHub;
- the pinned free local CI workflow passes from a clean baseline;
- legacy rows can be migrated without data loss;
- canonical precision and bounded storage constraints pass positive and negative tests;
- append-only triggers still block update and delete after migration;
- service-role privileges remain limited to `SELECT` and `INSERT`;
- current-state retrieval follows explicit supersession lineage;
- conflict cases are rejected or surfaced rather than timestamp-resolved;
- independent re-review accepts the corrected head;
- fresh-chat temporal orientation is tested separately from database correctness.
