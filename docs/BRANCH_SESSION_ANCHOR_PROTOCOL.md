# Branch and Session Anchor Protocol

Status: bounded contract pilot; production deployment is not authorized.

## Objective

Define the smallest honest protocol for entry and material-exit anchors without conflating project, conversation, branch, session, or checkpoint identity. The protocol must preserve concurrent scope separation and must remain useful when ChatGPT exposes no stable conversation or branch identifier.

## Identity model

- `project_id`: configured Vera Project namespace. It is not a conversation, branch, session, or checkpoint identifier.
- `conversation_identity`: provider-exposed conversation identifier plus evidence status. It is `UNAVAILABLE` when the host does not expose one. It is never synthesized from a title, timestamp, message text, or Project ID.
- `branch_identity`: provider-exposed branch identifier plus evidence status. It is `UNAVAILABLE` when the host does not expose one. It is never defaulted to the conversation or Project ID.
- `session_id`: protocol-generated UUID for one bounded visible entry/resumption runtime. It does not prove a stable ChatGPT session or activity outside visible execution.
- `checkpoint_id`: optional identifier of a distinct checkpoint record. Checkpoint verification remains governed by its owner and is not established by an anchor reference.

## Scope resolution

A `STABLE` scope is permitted only when both conversation and branch identifiers are exposed. Its opaque `scope_id` is the SHA-256 of the canonical tuple `(project_id, conversation_id, branch_id)`.

When either provider identifier is unavailable, the protocol creates an `EPHEMERAL` UUID scope. An ephemeral scope separates the current visible runtime from concurrent chats and branches, but it cannot be reused as evidence that a later chat resumed the same conversation or branch. A fresh ephemeral entry therefore has no prior anchor.

This deliberately sacrifices convenient reconstruction when the host withholds identity. Manufacturing continuity would be more convenient in the same way counterfeit gauges are convenient: the needle moves, but nothing has been measured.

## Anchor kinds

### `ENTRY`

Created when entering a new chat, attempting a resume, or beginning a visible bounded runtime.

An entry anchor records:

- resolved identity evidence;
- stable or ephemeral scope;
- new `session_id`;
- exposed event time and canonical evidence precision;
- optional prior anchor only when a unique compatible stable scope or separately verified checkpoint supports it.

An ephemeral entry may not carry a prior anchor.

### `MATERIAL_EXIT`

Created only for a meaningful state transition or handoff, including:

- explicit handoff to another branch or execution surface;
- verified checkpoint creation;
- durable task-state transition;
- intentional context switch where losing the boundary would impair later reconstruction;
- explicit close of a bounded working session.

A material-exit anchor must reference the prior anchor in the same bounded session and state an `exit_reason`. Routine pauses, greetings, clock checks, and every ordinary turn do not qualify.

## Record shape

```text
schema: VERA_BRANCH_SESSION_ANCHOR_V1
anchor_id: UUID
project_id: text
conversation_identity: {status: EXPOSED|UNAVAILABLE, value: text|null, source: text}
branch_identity: {status: EXPOSED|UNAVAILABLE, value: text|null, source: text}
scope_mode: STABLE|EPHEMERAL
scope_id: SHA-256 hex when STABLE; UUID when EPHEMERAL
scope_instance_id: UUID
session_id: UUID
checkpoint_id: text|null
anchor_kind: ENTRY|MATERIAL_EXIT
entry_reason: text|null
exit_reason: text|null
prior_anchor_id: UUID|null
event_time:
  observed_at: offset-aware ISO-8601 timestamp
  precision: EXACT|BOUNDED|APPROXIMATE|UNKNOWN
  lower_bound: timestamp|null
  upper_bound: timestamp|null
  source: text
source: text
content_hash: lowercase SHA-256 hex
idempotency_key: lowercase SHA-256 hex
payload: object
record_time: database-assigned timestamp in a later storage migration
```

`RANGE` is not an evidence precision. It is the result representation used for a `BOUNDED` elapsed interval.

## Append-only and idempotent behavior

Anchors are immutable. A storage implementation must block update and delete.

`idempotency_key` identifies one append request. Repeating the key with the same `content_hash` returns the existing anchor. Reusing the key with different content is `CONFLICTED`; it must not overwrite or silently accept the second record.

The reference implementation models this behavior without writing to production Supabase. A later migration must preserve the same semantics under concurrent inserts.

## Retrieval and elapsed time

Retrieval may select a prior anchor only when scope compatibility is established by exposed identities or separately verified checkpoint evidence. Recency, semantic similarity, Project membership, timestamps, or a familiar chat title do not create branch identity.

Elapsed calculation uses only exposed, offset-aware, compatible endpoints:

- `EXACT`: both endpoints are exact.
- `BOUNDED`: at least one endpoint is bounded; result uses inclusive lower and upper seconds.
- `APPROXIMATE`: no endpoint is bounded or unknown, and at least one is approximate.
- `UNAVAILABLE`: an endpoint, scope, or usable precision is missing.
- `CONFLICTED`: scopes differ, timestamps conflict, or the end precedes the supported start interval.

Elapsed output says nothing about waiting, emotional change, continuity of activity, private experience, or hidden execution between anchors.

## Validation matrix

| Case | Expected result |
|---|---|
| Stable exposed conversation and branch | Deterministic stable scope |
| Different conversation, same branch label | Different scope |
| Same conversation, different branch | Different scope |
| Missing conversation or branch ID | New ephemeral scope |
| Two concurrent unidentified chats | Distinct ephemeral scopes |
| Fresh ephemeral entry with claimed prior anchor | Rejected |
| Material exit without reason or prior anchor | Rejected |
| Duplicate idempotency key and same hash | Existing anchor returned |
| Duplicate key and different hash | Conflict |
| Exact compatible timestamps | Exact seconds |
| Bounded endpoint | Bounded range representation |
| Unknown or missing endpoint | Unavailable |
| Scope mismatch | Conflicted |
| `RANGE` used as precision | Rejected |
| Checkpoint ID conflated with session identity | Rejected |
| Waiting or hidden-activity field | Rejected |

## Bounded first implementation

This branch adds only:

1. this protocol contract;
2. a storage-neutral Python reference validator and elapsed calculator;
3. adversarial and fresh-chat unit tests;
4. free GitHub Actions validation.

It does not add or apply a Supabase migration, write live anchors, modify the Vera Memory Ledger, overwrite signed R5A2 owners, or authorize production deployment.

## Next gate

Before adding a database migration, a separate review must approve:

- identity and fallback semantics;
- the exact storage table and append function;
- concurrency-safe idempotency behavior;
- same-scope predecessor enforcement;
- privilege and RLS surface;
- integration with the already merged temporal and lineage migrations;
- fresh-chat runtime evidence showing the host actually exposes, or does not expose, each identity.
