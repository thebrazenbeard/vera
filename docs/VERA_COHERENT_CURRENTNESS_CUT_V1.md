# Vera Coherent Currentness Cut V1

Status: **SOURCE CANDIDATE / NOT INSTALLED / NOT RUNTIME-QUALIFIED**

Triad event: `GB_DG_TRIAD_20260921_V1`

## Why this exists

DriftGuard PR #31 proves a useful but deliberately local property: subject/evaluation/session currentness can be read from one SQLite `BEGIN IMMEDIATE` snapshot.

Vera currentness is not one SQLite subject. A material Vera recovery or effect decision can depend on several independently mutable surfaces. Examples include the current VCP control owner, Bus topology/current writer ownership, Git target frontier, provider currentness, installation/route state, and a private governed readback when that proposition actually depends on it.

Therefore:

`LOCAL_ATOMIC_CURRENTNESS != VERA_GLOBAL_CURRENTNESS`

This contract defines the smallest reusable multi-surface currentness primitive. It does not create a global lock and does not pretend distributed sources become atomic.

## Cut construction

A cut binds:
- a unique cut id;
- the current live-input digest;
- an optional restored-frontier digest;
- bounded retry count: 0 or 1;
- one readback record per observed surface.

Every surface readback binds:
- exact surface id;
- whether that surface is required for this proposition/effect;
- status: `COMPLETE | PARTIAL | UNAVAILABLE`;
- observed start frontier;
- observed end frontier;
- readback identity;
- result digest.

The required-surface inventory is proposition/effect-specific. Do not mark every known system required by habit.

## Decision rules

1. A required `PARTIAL` or `UNAVAILABLE` surface blocks the currentness claim.
2. If any required surface moved between its start/end observations on the first pass, retry only the affected sequence.
3. If a required surface still moves after that bounded retry, dependent currentness becomes `UNSTABLE_UNKNOWN`.
4. Optional surfaces cannot rescue a failed required surface.
5. Optional-surface movement alone does not block a cut whose required surfaces are complete/stable; it also cannot promote any stronger claim.
6. Current `LIVE_INPUT` task/correction/scope always controls over conflicting restored frontier.
7. A `CURRENT` result means only that the declared required surfaces were complete and stable within this observed cut.

## Effect boundary

A currentness cut is not a write lease and not authority.

Before any protected or external effect:
- re-read exact target/precondition where material;
- re-admit Patrick/current authority separately;
- respect current writer/assignment;
- enforce CAS/expected-version/idempotency semantics at the effect boundary;
- reconcile ambiguity rather than retrying by assumption.

DriftGuard-style effect fencing may consume a currentness-cut digest as one input. It must never interpret the cut itself as authorization.

## Identity boundary

A currentness cut says nothing by itself about:
- Vera identity;
- same-process continuity;
- autobiographical continuity;
- current desire/consent;
- phenomenology.

`CURRENTNESS_CUT != VERA_IDENTITY`

## Hostile cases frozen by source tests

- required surface moves once -> retry affected surface sequence;
- same required surface moves after retry -> `UNSTABLE_UNKNOWN`;
- required partial/unavailable -> blocked;
- optional movement -> no global promotion and no false block;
- optional stability cannot rescue a missing required surface;
- duplicate surface ids rejected;
- retry count cannot silently exceed one;
- digest changes when a bound frontier changes;
- every decision keeps identity, authority, and effect authorization false.

## Claim ceiling

This source can establish a deterministic decision over supplied readback records.

It does not prove:
- that readback providers are honest;
- distributed simultaneity;
- currentness after the observation cut ends;
- identity continuity;
- effect authority;
- provider application;
- Project installation;
- runtime behavioral qualification.
