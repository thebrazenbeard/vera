# Coordination Bus Temporal Evidence Trust Boundary V1

## Status

Bounded correction for draft PR #8. It adds no production schema, runtime, or
data migration and authorizes no merge.

## Problem corrected

The prior temporal layer required callers to provide:

- `precision`;
- `source`;
- `verified`;
- `reference_id`;
- timestamp values or bounds.

That shape validated syntax, but a hostile caller could invent a timestamp,
write `source="HOST"`, set `verified=true`, and pass validation. The claim was
self-certified rather than externally verified.

## Public contract

`coordination_bus.CoordinationBus` now accepts non-`UNKNOWN` temporal evidence
only in `TemporalEvidenceEnvelope`.

Each envelope binds:

- envelope schema;
- trusted issuer identifier;
- temporal role;
- operation subject;
- complete temporal evidence body;
- opaque verification token.

The runtime injects a `TemporalEvidenceVerifier`. The verifier, not the caller,
decides whether the envelope is authentic and correctly bound to the expected
role and subject.

Raw `TemporalEvidence` remains accepted only when its precision is `UNKNOWN`.
A raw non-`UNKNOWN` claim fails closed with an `INVALID` receipt.

## Role and subject bindings

Entry checkpoint evidence is bound to:

```text
coordination-entry:<workstream>:after_sequence=<cursor>:limit=<page-limit>
```

Acknowledgement and consumption evidence is bound to:

```text
coordination-acknowledgement:event_id=<addressed-event-id>
```

Material-exit evidence is bound to:

```text
coordination-exit:<workstream>:thread_key=<thread>:target_branch=<target>
```

Receipt-generation evidence is bound to a digest of the operation, actor,
result class, thread, event identity, target, and deterministic base result
hash.

An envelope issued for one role, event, cursor page, thread, target, or result
cannot be replayed as evidence for another.

## Reference authority

`HmacTemporalEvidenceAuthority` is a reference issuer/verifier for tests and
bounded runtimes. Its HMAC secret must remain outside untrusted callers and is
not committed by this project.

Production may inject another verifier, including:

- a host-runtime verifier;
- a signed-token verifier;
- an external time-attestation service;
- a hardware-backed clock attestation verifier.

The bus depends only on the verifier protocol.

## Receipt behavior

A missing receipt-time provider returns `UNKNOWN`.

An invalid, raw, forged, wrong-role, or wrong-subject receipt-time claim is
rejected and represented as:

```text
precision: UNKNOWN
source: UNVERIFIED_RECEIPT_TIME_REJECTED
```

Receipt time remains excluded from deterministic `result_hash`.

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
