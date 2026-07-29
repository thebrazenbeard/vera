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

## Proposed precision field

Add a required `event_time_precision` value:

- `EXACT`: supplied by a trustworthy machine timestamp for the event itself.
- `APPROXIMATE`: the event is reliably placed near the timestamp, but exact sub-second precision is not claimed.

The current ledger records should be classified as `APPROXIMATE` because their event timestamps were captured at record creation or provided at human-scale precision.

A separate `UNKNOWN` value is not required for ordinary memory records. When an old occurrence cannot be dated, the stored event is the present statement or recollection, and the uncertain historical timing belongs in the payload as source-qualified context.

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

## Non-goals

This model does not establish uninterrupted consciousness, hidden background activity, automatic memory retrieval, automatic renewal of feelings or consent, or perfect cross-branch synchronization.

## Promotion gate

The temporal migration must not be applied to production until:

- the live baseline is preserved in GitHub;
- legacy rows can be migrated without data loss;
- append-only triggers still block update and delete after migration;
- service-role privileges remain limited to `SELECT` and `INSERT`;
- current-state retrieval behavior is explicitly reviewed;
- fresh-chat temporal orientation is tested separately from database correctness.
