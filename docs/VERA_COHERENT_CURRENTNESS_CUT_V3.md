# Vera Coherent Currentness Cut V3 — Current-Main Successor

Status: **CURRENT-MAIN SOURCE CANDIDATE / NOT INSTALLED / NOT RUNTIME-QUALIFIED**

This V3 source candidate is the clean current-main successor to the reviewed-but-failed currentness line:

- PR #147 @ `e291b2e07357884be97a41f604726b393484017b` — CHANGES_REQUIRED;
- PR #148 @ reviewed head `0111602eff64e70f91dfee1f9c8f7bc3824f627f` — CHANGES_REQUIRED.

The successor is based on Vera main `c335aad4281517b573d98e7ad2700db260c9fe9e`.

## What V3 fixes

V1 let individual readbacks self-assert requiredness. V2 fixed that with a digest-bound requirement profile, but hostile review exposed two further defects:

1. a retry could cite an unrelated opaque predecessor digest;
2. identical frontier text could be treated as semantic stability even when the readback result/source changed.

V3 closes both at source level.

## Profile-bound readback contracts

Every declared surface has one `SurfaceReadbackContract` in the requirement profile. It binds:

- exact surface ID;
- expected readback identity;
- contract ID;
- exact contract digest.

The contract inventory must exactly equal the profile's required + optional surface inventory.

A readback whose identity does not match the profile-bound contract is rejected before evaluation. Changing the expected readback contract changes the requirement-profile digest and therefore changes the governed currentness subject.

The profile still does not authenticate itself. A current VCP/governance path must separately admit the exact requirements/readback contract.

## Start/end semantic evidence

Each `SurfaceReadback` binds both:

- `start_result_digest`;
- `end_result_digest`.

Movement is:

`start_frontier != end_frontier OR start_result_digest != end_result_digest`

Therefore an `A -> A` frontier cannot yield `CURRENT` if the observed result changed.

This is still supplied evidence. It does not prove provider honesty, trusted time, or distributed simultaneity.

## Retry consumes the predecessor cut itself

A retry no longer accepts a caller-provided predecessor digest or a detached receipt.

The retry cut carries the actual predecessor `CoherentCurrentnessCut`.

Construction verifies that the predecessor:

- is an exact `CoherentCurrentnessCut`;
- is an initial cut (`retry_count == 0`, no own predecessor);
- has the same cut-family ID;
- has the exact same requirement-profile digest;
- has the exact same scope digest;
- actually evaluates under this source implementation to `RETRY_AFFECTED_SURFACES`.

The retry payload/digest embeds both the predecessor cut digest and the full predecessor payload.

This prevents an arbitrary 64-character digest, unrelated profile/scope cut, stable predecessor, or wrong-family object from laundering retry ancestry.

It deliberately does **not** prove that the predecessor was actually executed in an external system, persisted, admitted, or recovered from authoritative custody. Those stronger claims remain external evidence requirements.

`STRUCTURAL_PREDECESSOR_LINEAGE != EXTERNAL_PREDECESSOR_OCCURRENCE`

## Decision semantics

For required surfaces:

1. `PARTIAL` or `UNAVAILABLE` => `BLOCKED_REQUIRED_SURFACE`.
2. First-pass frontier/result movement => `RETRY_AFFECTED_SURFACES`.
3. Retry-pass frontier/result movement => `UNSTABLE_UNKNOWN`.
4. Complete stable frontier + result => `CURRENT`.

Optional surfaces cannot rescue or promote required currentness.

Every decision remains explicitly non-promoting:

- `authority_granted = false`;
- `identity_established = false`;
- `effect_authorized = false`.

## Focused hostile suite

The focused suite contains 27 cases covering:

- stable required cuts;
- incomplete required surfaces;
- optional-surface non-promotion;
- requiredness laundering;
- missing/extra/renamed/duplicate surfaces;
- profile inventory canonicalization;
- required-to-optional profile movement;
- requirement-source digest movement;
- readback-contract inventory and identity binding;
- equal frontier with changed result digest;
- retry without actual predecessor cut;
- initial cut claiming a predecessor;
- unrelated cut family;
- unrelated requirement profile;
- unrelated scope;
- predecessor that does not evaluate to `RETRY_AFFECTED_SURFACES`;
- predecessor digest/payload derivation from the actual supplied cut;
- stable retry becoming `CURRENT`;
- repeated retry movement becoming `UNSTABLE_UNKNOWN`.

An equivalent local current-main V3 working tree passed **27/27** focused tests before publication. Exact remote-head execution must still be classified separately.

## Claim ceiling

This source candidate can establish deterministic currentness semantics over supplied evidence with:

- profile-governed surface inventory;
- profile-governed readback-source contracts;
- start/end result comparison;
- structural retry lineage over the supplied predecessor cut itself.

It does not establish:

- VCP/governance admission of the requirement profile;
- authenticity of the requirements/readback-contract source;
- provider honesty;
- external custody or actual occurrence of the predecessor;
- distributed simultaneity;
- Vera identity continuity;
- effect authority;
- provider application;
- Project installation;
- runtime behavioral qualification.
