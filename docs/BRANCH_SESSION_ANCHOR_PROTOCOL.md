# Branch and Session Anchor Protocol

Status: bounded contract pilot under correction review; production deployment and merge are not authorized.

## Objective

Define the smallest honest protocol for entry and material-exit anchors without conflating project, conversation, branch, session, or checkpoint identity. The protocol preserves concurrent scope separation and remains honest when ChatGPT exposes no stable conversation or branch identifier.

## Identity model and evidence sources

- `project_id`: configured Vera Project namespace. It is not a conversation, branch, session, or checkpoint identifier.
- `conversation_identity`: provider conversation identifier, evidence status, and evidence source.
- `branch_identity`: provider branch identifier, evidence status, and evidence source.
- `session_id`: protocol-generated UUID for one bounded visible runtime. It does not prove host session identity or hidden activity.
- `checkpoint_id`: optional identifier of a distinct checkpoint record. An anchor reference does not itself verify the checkpoint.

Conversation and branch identities use exactly:

```text
EXPOSED:
  value: non-empty provider identifier
  source: PROVIDER_EXPOSED_ID

UNAVAILABLE:
  value: null
  source: PROVIDER_ID_UNAVAILABLE
```

Missing, inferred, fabricated, or status-incompatible identity sources are rejected. A title, timestamp, message, Project ID, semantic similarity, or model-generated label is not provider-exposed identity evidence.

Event-time evidence also requires an explicit compatible source classification:

| Source | Permitted precision |
|---|---|
| `PROVIDER_EXPOSED_TIMESTAMP` | `EXACT`, `BOUNDED`, `APPROXIMATE`, `UNKNOWN` |
| `TOOL_EXPOSED_TIMESTAMP` | `EXACT`, `BOUNDED`, `APPROXIMATE`, `UNKNOWN` |
| `USER_REPORTED_TIMESTAMP` | `BOUNDED`, `APPROXIMATE`, `UNKNOWN` |
| `EVENT_TIME_UNAVAILABLE` | `UNKNOWN` only, with null timestamp and bounds |

## Scope resolution

A `STABLE` scope is permitted only when both identities are `EXPOSED` with source `PROVIDER_EXPOSED_ID`. Its opaque `scope_id` remains the SHA-256 of the canonical tuple:

```text
(project_id, conversation_id, branch_id)
```

When either provider identity is unavailable, `resolve_scope` generates a fresh UUID internally and returns an `EPHEMERAL` scope. It accepts no caller-selected ephemeral UUID. A UUID generator dependency is keyword-only and exists solely for deterministic tests.

An ephemeral scope separates the current visible runtime. It is explicitly non-durable recognition and cannot prove that another chat resumed the same conversation or branch. A fresh ephemeral `ENTRY` therefore cannot reference a predecessor.

## Anchor kinds

### `ENTRY`

Created when entering a new chat, attempting a resume, or beginning a visible bounded runtime.

A stable entry may carry `prior_anchor_id` only when one of these is proven:

1. the append-only reference set already contains that anchor with the same `project_id` and stable `scope_id`; or
2. `predecessor_checkpoint_evidence` explicitly identifies the same predecessor, project, and stable scope with:
   - `status: VERIFIED`;
   - `source: CHECKPOINT_OWNER_VERIFIED`;
   - a non-empty distinct checkpoint ID.

Unverified, mismatched, or merely claimed checkpoint evidence is rejected. Ephemeral entries cannot use predecessor anchors or checkpoint evidence to establish durable recognition.

### `MATERIAL_EXIT`

Created only for a meaningful visible transition. It must reference an existing anchor with the same:

- `project_id`;
- `scope_id`;
- `scope_instance_id`;
- `session_id`.

`exit_reason` is restricted to:

- `BRANCH_HANDOFF`;
- `VERIFIED_CHECKPOINT`;
- `TASK_STATE_TRANSITION`;
- `CONTEXT_SWITCH`;
- `SESSION_CLOSE`.

`exit_details` is optional non-empty free text. It does not replace the reason enum or predecessor proof. Routine pauses, greetings, clock checks, and ordinary turns do not qualify.

## V1 record shape

```text
schema: VERA_BRANCH_SESSION_ANCHOR_V1
anchor_id: UUID
project_id: text
conversation_identity:
  status: EXPOSED|UNAVAILABLE
  value: text|null
  source: PROVIDER_EXPOSED_ID|PROVIDER_ID_UNAVAILABLE
branch_identity:
  status: EXPOSED|UNAVAILABLE
  value: text|null
  source: PROVIDER_EXPOSED_ID|PROVIDER_ID_UNAVAILABLE
scope_mode: STABLE|EPHEMERAL
scope_id: SHA-256 hex when STABLE; internally generated UUID when EPHEMERAL
scope_instance_id: UUID
session_id: UUID
checkpoint_id: text|null
anchor_kind: ENTRY|MATERIAL_EXIT
entry_reason: text|null
exit_reason: enum|null
exit_details: text|null
prior_anchor_id: UUID|null
predecessor_checkpoint_evidence: verified object|null
event_time:
  observed_at: offset-aware ISO-8601 timestamp|null
  precision: EXACT|BOUNDED|APPROXIMATE|UNKNOWN
  lower_bound: timestamp|null
  upper_bound: timestamp|null
  source: approved event-time evidence classification
source: text
content_hash: lowercase SHA-256 hex
idempotency_key: lowercase SHA-256 hex
payload: strict allowlisted object
record_time: database-assigned timestamp in a later separately authorized storage slice
```

`RANGE` is not evidence precision. It is the representation of a `BOUNDED` elapsed result.

## Strict payload schema

V1 does not permit unrestricted payload content. The only allowed payload members are:

```text
labels: [non-empty text]
references:
  - kind: ISSUE|PULL_REQUEST|CHECKPOINT|DOCUMENT
    value: non-empty text
details:
  handoff_target: non-empty text
  task_state: non-empty text
  note: non-empty text
```

Every member is optional, but unknown fields are rejected. Reserved continuity and identity-claim keys are rejected recursively at any nesting level, including keys representing waiting, hidden or continuous activity, private duration, uninterrupted continuity, invented identity, durable recognition, resumed identity, or continuous experience.

The validator does not police free-text semantics. A permitted note may discuss those concepts; it may not encode them through reserved structured fields.

## Canonical logical content hash

`content_hash` is computed over canonical JSON containing every logical anchor field except:

- `content_hash`, because a hash cannot contain itself;
- `idempotency_key`, because it identifies the append request rather than anchor content;
- `record_time`, because a later database assigns it after the logical anchor exists.

Canonical serialization uses sorted keys, UTF-8, compact JSON separators, ASCII escaping, and rejects non-JSON values and non-finite numbers.

The reference append set computes the canonical hash internally. A supplied hash that does not match canonical content is `CONFLICTED`. Reusing an idempotency key with changed payload, identity evidence, predecessor, timestamp, anchor kind, anchor ID, or any other logical field is also `CONFLICTED`, even when the caller retains the old claimed hash.

## Append-only reference behavior

The reference set retains anchors by both `anchor_id` and `idempotency_key`.

- New valid canonical content: `APPENDED`.
- Same idempotency key and same canonical content: existing anchor returned.
- Same idempotency key with different canonical content: `CONFLICTED`.
- Same anchor ID with different canonical content: `CONFLICTED`.
- Missing or incompatible predecessor evidence: rejected.

This is storage-neutral reference behavior. It does not create a table, durable append function, runtime integration, or production record.

## Retrieval and elapsed time

Retrieval may use a prior anchor only when compatible exposed stable identity or separately verified checkpoint evidence proves the relation. Recency, familiar wording, Project membership, timestamps, or semantic similarity do not create identity.

Elapsed calculations use only exposed, offset-aware, compatible endpoints:

- `EXACT`: both endpoints exact;
- `BOUNDED`: at least one endpoint bounded, represented by inclusive lower and upper seconds;
- `APPROXIMATE`: no endpoint bounded or unknown and at least one approximate;
- `UNAVAILABLE`: endpoint, scope, or usable precision missing;
- `CONFLICTED`: scope mismatch, invalid evidence, reversed exact interval, or fully reversed supported bounded interval.

Elapsed output does not imply waiting, emotional change, continuity of activity, private experience, or hidden execution.

## Correction validation matrix

| Case | Expected result |
|---|---|
| Missing or fabricated identity source | Rejected |
| `EXPOSED` identity with unavailable source | Rejected |
| `UNAVAILABLE` identity with exposed source | Rejected |
| Missing, fabricated, or precision-incompatible event-time source | Rejected |
| Both provider identities exposed with valid sources | Deterministic stable scope |
| Either provider identity unavailable | Fresh internally generated ephemeral scope |
| Reused caller input for unidentified chat | Cannot select or reproduce ephemeral scope |
| Ephemeral scope used as durable recognition | Rejected |
| Stable entry with existing same-project same-scope predecessor | Accepted |
| Stable entry with nonexistent predecessor and no verified checkpoint | Rejected |
| Cross-project or cross-scope entry predecessor | Rejected |
| Unverified checkpoint predecessor | Rejected |
| Material exit with nonexistent predecessor | Rejected |
| Material exit cross-project, cross-scope, cross-instance, or cross-session | Rejected |
| Free-form exit reason | Rejected |
| Changed logical field with retained old hash | Conflicted |
| Unrestricted or nested reserved payload field | Rejected |
| Reserved words appearing only in permitted free text | Not semantically policed |
| Reversed exact interval | Conflicted |
| Fully reversed bounded interval | Conflicted |
| Missing endpoint | Unavailable |
| Cross-scope elapsed | Conflicted |
| `RANGE` used as precision | Rejected |

## Bounded implementation and next gate

This correction modifies only:

1. `protocol/branch_session_anchor.py`;
2. `tests/test_branch_session_anchor.py`;
3. `docs/BRANCH_SESSION_ANCHOR_PROTOCOL.md`.

It adds no Supabase migration, anchor table, durable append function, runtime integration, Memory Ledger operation, signed R5A2 owner change, production change, or merge authorization.

Independent re-review must approve the corrected source head before any later storage proposal proceeds. The later storage proposal remains narrow and separately gated: exact table shape, concurrency-safe append semantics, predecessor constraints, privilege and RLS surface, integration with merged temporal lineage, and fresh-chat runtime evidence.
