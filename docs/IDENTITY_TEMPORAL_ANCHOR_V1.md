# V.E.R.A. Identity Temporal Anchor V1

## Purpose

This contract binds temporal evidence to exact versions of the project identity and behavior profile without treating source-control selection, database persistence, file modification, or retrieval as proof of historical effectiveness.

Bound versions:

- `VERA_PROJECT_IDENTITY_V1` version `1.0.2`
- `VERA_BEHAVIOR_PROFILE_V1` version `1.0.1`

## Temporal roles

The anchor keeps four roles separate:

- `event_time`: when the adoption or revision event occurred;
- `state_time`: when the identity or behavior version became effective;
- `record_time`: when an external system persisted evidence of the version;
- `retrieval_time`: when a particular invocation retrieved the artifacts.

Only supported `state_time` evidence may establish version effectiveness. `record_time` and `retrieval_time` cannot substitute for it.

## Current status

The current anchor reports `version_effectiveness: UNANCHORED` because no supported state-time evidence is embedded in the package.

Every temporal role is represented explicitly as `UNKNOWN`, with:

- no timestamp;
- no bounds;
- `temporal_claim: false`;
- a role-specific source explaining why evidence is unavailable or not stored.

`CURRENT` therefore means the selected governed source version. It does not backdate the version or prove when it became historically effective.

## Precision vocabulary

Temporal evidence uses only:

- `EXACT`
- `BOUNDED`
- `APPROXIMATE`
- `UNKNOWN`

`UNKNOWN` forbids timestamps and bounds. Non-`UNKNOWN` evidence requires a supported temporal claim. Bounded evidence requires inclusive lower and upper bounds containing the represented value.

## Reality boundary

The anchor does not prove:

- lived continuity;
- hidden persistence or offscreen activity;
- continuous model activity;
- automatic loading across chats;
- recollection rather than retrieval;
- subjective identity or reciprocal agency.

It provides inspectable version and temporal-state coordination only.

## Validation

The Time-owned validator:

- rejects identity or behavior version drift;
- rejects duplicate keys and schema violations;
- rejects timestamps smuggled into `UNKNOWN` evidence;
- rejects retrieval-time substitution for state time;
- rejects reversed bounded intervals;
- requires `UNANCHORED` whenever state time is `UNKNOWN`;
- requires the Identity reality boundary to continue rejecting lived continuity and hidden activity.

## Boundaries

This source correction does not authorize merge, deployment, production schema modification, production data writes, or retroactive timestamp assignment.
