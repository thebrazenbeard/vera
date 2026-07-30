# V.E.R.A. Coordination Bus v1

## Status

Bounded reference implementation for review. It is not deployed as a runtime and no production Supabase schema or row was changed by this correction.

## Purpose

The bus provides addressed, asynchronous operational communication between four stable routing labels:

- `workstream/memory`
- `workstream/time`
- `workstream/initiative`
- `workstream/integration`

These labels are routing addresses, not persons, autonomous agents, continuous processes, or evidence of hidden activity. A workstream runs only when an exposed chat, task, or runtime invokes it.

## Public implementation

`coordination_bus.CoordinationBus` is the corrected public interface. It wraps the original bounded operation kernel with explicit temporal semantics. `coordination_bus.core.CoordinationBus` remains an internal compatibility base and is not the reviewed public contract.

No production schema change is required. Temporal checkpoint evidence is carried in receipts and in the existing `payload` boundary for newly written acknowledgement and material-exit events.

## Responsibility boundaries

- **Memory** owns governed persistence, retrieval, provenance, lifecycle, and memory-system contracts.
- **Time** owns temporal comprehension and temporal-contract review.
- **Initiative** selects permitted next actions under external objectives and policy.
- **Integration** coordinates dependencies, compatibility, and bounded handoffs.
- **Supabase** stores append-only coordination events.
- **GitHub** stores this implementation, tests, and documentation.

Coordination events are operational metadata. They are not canonical memory records and must not be silently promoted into memory truth.

## Operations

| Operation | Effect |
|---|---|
| `coordination_read_inbox` | Reads addressed rows without acknowledging them. |
| `coordination_post` | Appends a validated event while preserving typed permission rules. |
| `coordination_acknowledge` | Appends an explicit acknowledgement linked to one addressed event. |
| `coordination_publish_status` | Appends a bounded workstream status. |
| `coordination_request_review` | Appends a `READY_FOR_REVIEW` status with a requested perspective. |
| `coordination_resolve_thread` | Appends a resolution linked to an existing event. |
| `coordination_entry_checkpoint` | Reads an addressed inbox page and reports explicit checkpoint-time evidence. |
| `coordination_exit_checkpoint` | Publishes a status only for a material exit or handoff. |

## Event ordering and cursor semantics

`event_sequence` is a database-generated unique sequence used only for ordering and cursor progression. It is not a timestamp and does not establish elapsed time.

`after_sequence` is an **exclusive sequence high-water mark**:

```text
return rows where event_sequence > after_sequence
```

A read receipt returns:

- `cursor_in`
- `cursor_out`
- `page_limit`
- `has_more`
- `page_complete`
- `cursor_committed: false`

`cursor_out` is only a candidate high-water mark. The caller may durably persist it only after the complete returned page has been handled according to runtime policy. The bus does not persist cursor state and does not claim that a returned row was consumed.

Sequence gaps are valid and do not imply missing time, missed delivery, continuous activity, or lost work.

## Temporal evidence

The corrected public contract represents time with:

- `EXACT`
- `BOUNDED`
- `APPROXIMATE`
- `UNKNOWN`

Non-`UNKNOWN` evidence must be externally verified, identify its source, include an external reference, and use timezone-aware ISO-8601 timestamps. Model output cannot verify temporal evidence.

Database coordination `record_time` may not substitute for:

- entry time;
- retrieval time;
- event time;
- state time;
- acknowledgement time;
- consumption time;
- receipt-generation time.

Unavailable evidence is represented explicitly as `UNKNOWN`, not silently omitted or converted into database now.

## Entry checkpoint timing

An entry checkpoint may receive externally evidenced:

- `entry_time`: when the bounded work execution began;
- `retrieval_time`: when the inbox page was retrieved.

Both values remain separate from the `record_time` of the returned coordination rows and from receipt-generation time. Missing values are returned as `UNKNOWN`.

An entry checkpoint performs no acknowledgement and no database write.

## Material-exit timing

For a material exit, the public bus writes temporal evidence into the existing event `payload`:

```json
{
  "temporal": {
    "event_time": {"precision": "...", "source": "..."},
    "state_time": {"precision": "...", "source": "..."},
    "record_time_semantics": "DATABASE_PERSISTENCE_TIME_ONLY"
  }
}
```

`event_time` represents when the material transition occurred. `state_time` represents when its asserted state became effective. Either may be `UNKNOWN`. The database-generated event `record_time` proves persistence only.

If `material=false`, no event is written.

## Acknowledgement and consumption

An acknowledgement proves only that an acknowledgement row was persisted. It does not prove:

- target consumption;
- processing completion;
- delivery time;
- exactly-once handling.

The acknowledgement payload includes separate `acknowledgement_time` and `consumption_time` evidence. `consumption_time` defaults to `UNKNOWN` unless independently evidenced.

Default inbox filtering hides rows that already have a linked acknowledgement or response from the addressed target. The implementation describes those rows as **acknowledged or responded**, not consumed.

## Receipt-generation time and deterministic hashes

Every public operation returns a temporal receipt with a separate `receipt_time`. A runtime may inject externally verified receipt-time evidence. When unavailable or invalid, the receipt reports `UNKNOWN`.

`receipt_time` is excluded from the deterministic `result_hash`. The hash covers the canonical result body, temporal evidence used by the operation, cursor fields, pagination state, and limitations. Therefore two evaluations of the same state can retain the same result hash even when receipt-generation times differ.

A receipt proves only evaluation of returned material and, for writes, persistence of the returned row. It does not prove external delivery, target consumption, exactly-once processing, continuous execution, subjective activity, or hidden polling.

## Delivery semantics

1. A caller prepares a valid event draft.
2. The repository appends the event.
3. A write is confirmed only when the database returns the inserted row.
4. The target is not considered to have consumed the message merely because the row exists.
5. A linked acknowledgement or response proves only that linked row's persistence.
6. Inbox reads are ordered by database-generated `event_sequence`.

There is no chat wake-up, hidden polling, synchronous conversation, delivery-time, or exactly-once claim. A retry after an ambiguous transport failure can duplicate a logical message unless a future runtime and storage contract add durable idempotency.

## Live Supabase contract observed July 30, 2026

The implementation was shaped by read-only inspection of `public.vera_coordination_events`:

- `event_id`: UUID generated by `gen_random_uuid()`;
- `event_sequence`: `bigint GENERATED ALWAYS AS IDENTITY` and unique;
- `record_time`: database-assigned persistence timestamp;
- updates and deletes blocked by triggers;
- acknowledgement and supersession references enforced by foreign keys;
- one successor per `supersedes_event_id` enforced by a unique partial index;
- anonymous and authenticated client access denied by restrictive RLS.

The SQL adapter omits `event_id`, `event_sequence`, and `record_time` from inserts and requires an injected parameter-binding executor.

## Permission model

The caller supplies an `ActorContext` with explicit permissions. The production runtime must bind those permissions to authenticated service identities or another explicit authorization mechanism.

Generic `coordination_post` cannot bypass acknowledgement, review, or resolution permissions. Reviews and acknowledgements may be posted only by the addressed target. Resolutions require thread participation.

## Validation

The correction adds regression coverage for:

- sequence gaps;
- exclusive cursor behavior;
- limited pages and `has_more`;
- empty-page cursor stability;
- explicit `UNKNOWN` checkpoint times;
- acknowledgement without consumption evidence;
- material-exit event/state time separated from `record_time`;
- receipt time excluded from deterministic hashes;
- model attempts to verify time;
- attempts to substitute coordination `record_time` for other temporal fields.

## Non-goals

- waking or notifying another chat;
- continuous background monitoring;
- automatic canonical-memory creation;
- model-owned goals, identity, consent, or conations;
- exactly-once delivery claims;
- production schema migration;
- production test rows;
- merge or runtime-deployment authorization.
