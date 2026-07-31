# V.E.R.A. Identity Temporal Anchor V1

## Purpose

This contract binds one temporal-anchor identity to exact versions of the project identity and behavior profile without treating source-control selection, persistence, file metadata, source labels, model output, or retrieval as proof of historical effectiveness.

Bound versions:

- `VERA_PROJECT_IDENTITY_V1` version `1.0.2`
- `VERA_BEHAVIOR_PROFILE_V1` version `1.0.1`

The anchor ID includes both versions. Its deterministic SHA-256 subject binding covers the anchor operation, anchor version, identity ID and version, and behavior-profile ID and version.

## Root lineage

Temporal Anchor V1 is a versioned root anchor:

- `anchor_version: 1.0.0`
- `lineage_status: ROOT`
- `predecessor_anchor_ref: null`
- `supersedes_anchor_id: null`

A later identity or behavior version requires a new anchor identity and explicit predecessor lineage. The root artifact may not be silently mutated into a successor or used to backdate a revision.

## Temporal roles

The anchor keeps four roles separate:

- `event_time`: when the adoption or revision event occurred;
- `state_time`: when the identity or behavior version became effective;
- `record_time`: when an external system persisted evidence of the version;
- `retrieval_time`: when a particular invocation retrieved the artifacts.

Only externally verified `state_time` may establish version effectiveness. `record_time` and `retrieval_time` cannot substitute for it.

## Fail-closed V1 boundary

Temporal Anchor V1 can represent only:

- `version_effectiveness: UNANCHORED`
- `precision: UNKNOWN`
- `temporal_claim: false`
- no timestamps or bounds

This is intentional. A caller cannot create an anchored state by supplying a convincing source label, reference string, timestamp, or precision value.

Any anchored successor requires:

1. a separately reviewed verifier-owned temporal-evidence contract;
2. evidence bound to the exact identity version, behavior version, temporal role, value, bounds, and anchor subject;
3. a new version-bound anchor identity;
4. explicit predecessor lineage;
5. externally verified `state_time`;
6. preservation of the prior root anchor as history.

The backdating policy is `FORBIDDEN_WITHOUT_EXTERNALLY_VERIFIED_STATE_TIME`.

## Current status

Every temporal role is explicitly `UNKNOWN`, with:

- no timestamp;
- no bounds;
- `temporal_claim: false`;
- a role-specific explanation for unavailable or unstored evidence.

`CURRENT` means the selected governed source version. It does not prove when the version became historically effective.

## Reality boundary

The anchor does not prove:

- lived continuity;
- hidden persistence or offscreen activity;
- continuous model activity;
- automatic loading across chats;
- recollection rather than retrieval;
- subjective identity or reciprocal agency.

It provides inspectable version binding, explicit uncertainty, and governed successor requirements only.

## Validation

The Time-owned validator and hostile suite reject:

- identity or behavior version drift;
- generic or version-free anchor IDs;
- altered subject hashes;
- invented predecessor or supersession lineage;
- any non-`UNKNOWN` V1 temporal claim, including a plausible external source label;
- timestamps or bounds smuggled into `UNKNOWN`;
- retrieval-time substitution;
- weakened backdating policy;
- duplicate keys;
- removal of lived-continuity and hidden-activity boundaries.

## Boundaries

This correction does not authorize merge, deployment, production schema modification, production data writes, anchored-version adoption, or retroactive timestamp assignment.
