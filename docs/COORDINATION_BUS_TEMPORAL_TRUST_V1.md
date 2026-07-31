# Coordination Bus Temporal Evidence Trust Boundary V1

## Status

Bounded correction for draft PR #8. It adds no production schema, runtime, or
data migration and authorizes no merge.

## Problem corrected

The first temporal layer validated caller-provided `source`, `verified`, and
`reference_id` fields. A hostile caller could invent a timestamp, label it
`HOST`, and claim verification. The representation looked authoritative but
had no external trust boundary.

A later verifier-envelope correction authenticated temporal evidence but bound
some claims only to broad subjects such as an event ID or thread. That allowed
a valid envelope to be replayed after other operation inputs changed.

## Public contract

`coordination_bus.CoordinationBus` is the strict public facade.

Non-`UNKNOWN` temporal evidence is accepted only inside a
`TemporalEvidenceEnvelope` authenticated by an injected
`TemporalEvidenceVerifier`. Raw `TemporalEvidence` is accepted only when its
precision is `UNKNOWN`.

Each envelope binds:

- envelope schema;
- registered issuer identity;
- temporal role;
- complete evidence body, including value, precision, and bounds;
- an exact canonical operation-subject digest;
- an opaque verification token.

The verifier, not the caller or model output, decides whether the envelope is
authentic and correctly bound.

## Exact role and subject bindings

### Entry and retrieval time

Entry checkpoint evidence is bound to the full inbox query:

```text
operation: coordination_entry_checkpoint
actor_workstream: <workstream>
target_branch: <same workstream>
after_sequence: <exclusive cursor>
limit: <page limit>
include_acknowledged: false
```

An envelope cannot be replayed for another workstream, cursor, page size, or
acknowledgement-filter policy.

### Acknowledgement and consumption time

Acknowledgement evidence is bound to:

```text
operation: coordination_acknowledge
actor_workstream: <addressed target>
source_event_id: <event ID>
thread_key: <source thread>
summary: <exact acknowledgement summary>
payload: <canonical payload>
reference_data: <canonical reference data>
```

Changing the event, actor, thread, summary, payload, or references invalidates
the envelope. `consumption_time` remains `UNKNOWN` unless independently issued
for that same complete operation subject.

### Material-exit event and state time

Exit evidence is bound to the complete proposed transition:

```text
operation: coordination_exit_checkpoint
actor_workstream: <publisher>
thread_key: <thread>
target_branch: <target or null>
objective: <exact objective>
summary: <exact summary>
material: <boolean>
status: <status>
active_issue: <issue or null>
acknowledges_event_id: <event or null>
reference_data: <canonical reference data>
```

Changing any transition field invalidates previously issued evidence.

### Receipt-generation time

Receipt evidence is bound to a digest of the operation, actor, result class,
thread, event identity, sequence, target, and deterministic base result hash.
Receipt time remains excluded from the public deterministic `result_hash`.

## Reference authority

`HmacTemporalEvidenceAuthority` is a reference issuer/verifier for tests and
bounded runtimes. Its secret must remain outside untrusted callers and is not
committed by this project. Production may inject another verifier implementing
the same protocol.

An invalid, raw, forged, unregistered-issuer, wrong-role, wrong-subject, or
post-issuance-modified claim fails closed. Invalid receipt-time evidence becomes:

```text
precision: UNKNOWN
source: UNVERIFIED_RECEIPT_TIME_REJECTED
```

## Preserved temporal distinctions

- `event_sequence` is ordering, not time.
- `record_time` is database persistence time only.
- `entry_time`, `retrieval_time`, `event_time`, `state_time`,
  `acknowledgement_time`, `consumption_time`, and `receipt_time` remain distinct.
- `after_sequence` is an exclusive sequence high-water mark candidate.
- Cursor commitment remains a runtime durability decision.
- Acknowledgement does not prove consumption or processing completion.
- Missing optional evidence remains explicit `UNKNOWN`.

## Preserved boundaries

This correction does not claim:

- chat wake-up;
- continuous or hidden activity;
- delivery time;
- processing completion from acknowledgement;
- consumption without evidence;
- exactly-once delivery;
- production deployment;
- production schema modification.
