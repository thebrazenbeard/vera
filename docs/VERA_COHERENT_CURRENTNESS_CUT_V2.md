# Vera Coherent Currentness Cut V2 — Requirement-Profile Binding

Status: **STACKED SOURCE CANDIDATE / NOT INSTALLED / NOT RUNTIME-QUALIFIED**

Triad event: `GB_DG_TRIAD_20260921_V1`

Stacked parent:
`thebrazenbeard/vera` PR #147 @
`e291b2e07357884be97a41f604726b393484017b`.

## Why V2 exists

V1 made the currentness evaluator multi-surface, but every
`SurfaceReadback` still carried its own `required: bool`.

That is too weak.

A caller that controls the readback object could relabel a materially required
surface as optional and obtain a different decision without changing the
proposition/scope contract.

V2 removes that degree of freedom:

`READBACK_REPORTS_EVIDENCE != READBACK_DECIDES_REQUIREDNESS`

Requiredness comes only from one immutable
`CurrentnessRequirementProfile`.

## Requirement profile

The profile binds:

- `profile_id`;
- `proposition_type`;
- exact `scope_digest`;
- `requirements_source_id`;
- `requirements_source_digest`;
- canonical required surface IDs;
- canonical optional surface IDs.

Required surfaces are non-empty, sorted, unique, and disjoint from optional
surfaces.

Changing a surface from required to optional changes the profile digest.

Changing the claimed requirements source changes the profile digest.

This does **not** authenticate the claimed source.

`REQUIREMENT_PROFILE_SOURCE_DECLARATION != REQUIREMENT_PROFILE_ADMISSION`

A current VCP/governance path must separately establish that this exact profile
is the admitted profile for the proposition/effect being evaluated.

## Exact inventory

A V2 cut must contain exactly the surfaces declared by its requirement profile.

Therefore cut construction rejects:

- an omitted required surface;
- an omitted optional surface;
- an undeclared extra surface;
- a renamed/aliased surface;
- duplicate surface IDs;
- non-canonical ordering.

This is intentionally stricter than "at least all required surfaces." The cut
digest therefore commits to the whole declared observation inventory.

## Readback objects no longer carry requiredness

`SurfaceReadback` binds only:

- `surface_id`;
- `COMPLETE | PARTIAL | UNAVAILABLE`;
- start frontier;
- end frontier;
- readback identity;
- result digest.

There is no `required` field.

The evaluator derives requiredness from the profile only.

## Scope binding

The profile carries the proposition/effect scope digest.

The cut separately carries `live_input_scope_digest`.

Those digests must match before a cut exists.

This prevents a profile admitted for scope A from being silently reused as a
cut for scope B without changing the governed subject.

It still does not prove that the supplied live-input digest itself came from a
trusted external source.

## Retry ancestry

The V1 bounded retry count remains 0 or 1.

V2 adds:

- initial cut: `predecessor_cut_digest = None`;
- retry cut: exact SHA-256 `predecessor_cut_digest` required.

This makes a claimed retry structurally different from a first pass and binds
the retry cut to a predecessor subject.

The evaluator still does not provide a durable retry ledger. A caller cannot
claim that the digest proves the predecessor was actually executed or admitted.
That stronger history claim needs external custody/ledger evidence.

## Decision semantics

For profile-required surfaces:

1. `PARTIAL` or `UNAVAILABLE` => `BLOCKED_REQUIRED_SURFACE`.
2. First-pass movement => `RETRY_AFFECTED_SURFACES`.
3. Retry-pass movement => `UNSTABLE_UNKNOWN`.
4. Complete/stable => `CURRENT`.

Optional surface state does not rescue or promote required currentness.

Every decision binds:

- cut digest;
- requirement-profile digest;
- scope digest;
- affected surfaces.

And every decision still emits:

- `authority_granted = false`;
- `identity_established = false`;
- `effect_authorized = false`.

## Hostile cases frozen in source tests

V2 tests reject or constrain:

- readback-side `required=False` laundering;
- missing required surface;
- undeclared extra surface;
- renamed required surface;
- required/optional overlap;
- non-canonical profile inventory;
- duplicate readbacks;
- live-input/profile scope mismatch;
- retry without predecessor digest;
- initial cut with fabricated predecessor;
- required-to-optional profile weakening without digest movement;
- requirements-source movement without profile digest movement.

Existing currentness tests still cover stable cuts, first-pass movement,
retry instability, missing required evidence, and non-promotion.

## Effect boundary

A profile-bound `CURRENT` result is currentness eligibility evidence only.

It is not:

- Patrick authority;
- writer ownership;
- a write lease;
- provider application evidence;
- Vera identity;
- runtime qualification.

A protected or external effect must separately re-admit exact authority,
writer/assignment ownership, target currentness, and effect-specific
preconditions at the effect boundary.

## Claim ceiling

V2 can establish that one deterministic decision was evaluated over readbacks
whose IDs exactly match one supplied, digest-bound requirement profile.

It does not establish:

- that the requirement profile was admitted by the current VCP owner;
- that its requirements source is authentic;
- that a retry predecessor actually occurred merely because its digest is named;
- distributed simultaneity;
- readback-provider honesty;
- identity continuity;
- effect authority;
- provider application;
- Project installation;
- runtime behavioral qualification.
