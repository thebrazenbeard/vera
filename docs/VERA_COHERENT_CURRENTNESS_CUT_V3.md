# Vera Coherent Currentness Cut V3 — Typed Retry + Readback Semantics

Status: **STACKED SOURCE CANDIDATE / NOT INSTALLED / NOT RUNTIME-QUALIFIED**

V3 repairs the two blocking semantic defects found in hostile review of PR #148 exact head `0111602eff64e70f91dfee1f9c8f7bc3824f627f`.

## 1. Retry ancestry is typed, not an opaque digest

V2 accepted any syntactically valid `predecessor_cut_digest` on `retry_count=1`. That proved only that a 64-character hex string had been supplied.

V3 replaces it with `PredecessorCutReceipt` and adds a `cut_family_id` to the cut. A retry is accepted only when the supplied predecessor receipt binds:

- the predecessor cut digest;
- the same cut family;
- the exact same requirement-profile digest;
- the exact same scope digest;
- predecessor `retry_count == 0`;
- predecessor disposition `RETRY_AFFECTED_SURFACES`;
- a non-empty canonical affected-surface set contained in the profile-required surfaces.

This closes cross-profile, cross-scope, cross-family, wrong-disposition, and unrelated-surface retry laundering.

It deliberately does **not** claim that the predecessor was actually executed, persisted, admitted, or retrieved from authoritative custody. A caller can still fabricate a structurally valid receipt if no external ledger/custody layer authenticates it.

`TYPED_STRUCTURAL_CONTINUITY != DURABLE_PREDECESSOR_OCCURRENCE`

## 2. Equal frontier text no longer implies semantic stability by itself

V2 defined movement only as:

`start_frontier != end_frontier`

That was too weak. A required surface could report `A -> A` while its returned result changed.

V3 makes every `SurfaceReadback` carry both:

- `start_result_digest`;
- `end_result_digest`.

A surface is moved when either the frontier **or the result digest** changes:

`FRONTIER_MOVED OR RESULT_MOVED => SURFACE_MOVED`

Therefore `A -> A` with different result digests cannot contribute to `CURRENT`.

## 3. Readback identity/provider contract is profile-bound

Each declared surface now has one `SurfaceReadbackContract` inside the requirement profile. The contract binds:

- surface ID;
- expected readback identity;
- contract ID;
- exact contract digest.

The readback-contract inventory must exactly equal the declared required + optional surface inventory. A cut is rejected when a readback identity does not match the profile-bound contract for that surface.

Changing the provider/readback contract therefore changes the requirement-profile digest and creates a different governed subject.

This still does not prove provider honesty or authenticate the contract source. Those remain external admission/currentness questions.

## Decision semantics

For profile-required surfaces:

1. `PARTIAL` or `UNAVAILABLE` => `BLOCKED_REQUIRED_SURFACE`.
2. First-pass frontier or result movement => `RETRY_AFFECTED_SURFACES`.
3. Retry-pass frontier or result movement => `UNSTABLE_UNKNOWN`.
4. Complete readbacks with stable frontier **and** result digest => `CURRENT`.

Optional surfaces cannot rescue or promote required currentness.

Every decision remains explicitly non-promoting:

- `authority_granted = false`;
- `identity_established = false`;
- `effect_authorized = false`.

## Hostile regression surface

The focused source suite now covers 27 cases, including the V2 cases plus:

- equal frontier with changed result digest;
- mismatched readback identity;
- readback-contract movement changes profile digest;
- retry with unrelated cut family;
- retry with unrelated requirement profile;
- retry with unrelated scope;
- retry with wrong predecessor disposition;
- retry with a predecessor affected surface outside required inventory;
- stable structurally bound retry can become `CURRENT`;
- readback-contract inventory must exactly match the profile inventory.

## Claim ceiling

V3 can establish deterministic source-level currentness semantics over supplied evidence with:

- exact profile-bound surface inventory;
- exact profile-bound readback contracts;
- start/end result comparison;
- typed single-retry structural continuity.

It does **not** establish:

- VCP/governance admission of the profile;
- authenticity of the requirements/readback-contract source;
- provider honesty;
- external custody or actual occurrence of the predecessor receipt;
- distributed simultaneity;
- Vera identity continuity;
- effect authority;
- provider application;
- Project installation;
- runtime behavioral qualification.
