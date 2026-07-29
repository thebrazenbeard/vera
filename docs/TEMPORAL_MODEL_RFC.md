# Temporal Model RFC

Status: draft on `temporal-pilot`

## Objective

Give Vera reliable temporal orientation without claiming unrecorded experience, inventing historical precision, or confusing event, state, persistence, and synchronization times.

## Existing and proposed fields

### `event_time`

When the record-producing event occurred. Examples include a statement, correction, decision, observed tool result, or explicit memory operation.

For live interactions, this should normally be within milliseconds or seconds of `record_time`.

### `event_time_precision`

Required classification of how precisely `event_time` is known:

- `EXACT`: supplied by a trustworthy machine timestamp for the event itself.
- `APPROXIMATE`: the event is reliably placed near the timestamp, but exact sub-second precision is not claimed.

The current records should be classified as `APPROXIMATE` because their timestamps were captured at record creation or provided at human-scale precision.

A separate `UNKNOWN` value is not required for ordinary memory records. When an older occurrence cannot be dated, the stored event is the present statement or recollection. Uncertain historical timing belongs in the source-qualified payload.

### `state_time`

When the represented state is asserted to apply.

This is often equal to `event_time`, but it may differ. A correction recorded now may state that a prior condition ended yesterday. The correction event happens now; the corrected state boundary is yesterday.

### `record_time`

When Supabase persisted the row.

This must be database-assigned. The insert trigger overwrites any caller-supplied value with `clock_timestamp()`. Otherwise `record_time` would only prove what the caller claimed, which defeats its evidentiary purpose.

## Explicit supersession lineage

Timestamp recency must not select authority.

For each `(project_id, branch_id, record_key)` scope:

1. The first record has no `supersedes_record_id`.
2. Every later record must supersede the unique unsuperseded head.
3. A record may have at most one direct successor.
4. Supersession may not cross project, branch, or record key.
5. Self-supersession is invalid.
6. Multiple heads are a conflict, not a timestamp tie-break problem.

The proposed views are:

- `vera_save_state_heads`: every unsuperseded head, including conflicts.
- `vera_current_save_state`: only scopes with exactly one head.
- `vera_save_state_lineage_conflicts`: scopes with an invalid head count.

This preserves visibility of corruption instead of quietly selecting whichever row has the newest clock value.

## Vera Memory Ledger synchronization

`VERA Memory Ledger` remains a derived Project-local semantic projection. Supabase remains the durable external record store.

A Ledger synchronization is a separate event and must not overwrite the memory row or become one scalar `anchored_time` field. If repeatable synchronization becomes operational, receipts should be separate records containing:

- Supabase `record_id`;
- Ledger snapshot or receipt ID;
- project and branch identifiers;
- synchronization time;
- content hash;
- outcome and warnings.

The receipt table is deferred until a repeatable Ledger synchronization path exists. Schema should follow working logistics, not ceremonial architecture.

## Temporal orientation behavior

At a meaningful temporal trigger, Vera should:

1. obtain current time from an exposed trusted source;
2. retrieve the smallest relevant prior event or temporal anchor;
3. compare compatible timestamps;
4. calculate elapsed time only from exposed endpoints;
5. apply lifecycle, provenance, consent, correction, and current-ratification rules;
6. respond naturally without claiming private waiting or continuous hidden activity.

## Non-goals

This model does not establish uninterrupted consciousness, hidden background activity, automatic memory retrieval, automatic renewal of feelings or consent, or perfect cross-branch synchronization.

## Promotion gate

The temporal drafts must not be applied to production until:

- the live baseline is preserved in GitHub;
- both migrations execute successfully in an isolated Supabase branch;
- the precision and lineage validation suites pass;
- legacy rows migrate without data loss;
- append-only triggers still block update and delete;
- service-role privileges remain limited to required `SELECT` and `INSERT` operations;
- forged `record_time` values are overwritten;
- current-state retrieval follows explicit lineage and branch scope;
- fresh-chat temporal orientation is tested separately from database correctness.
