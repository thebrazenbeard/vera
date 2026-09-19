# Vera Cohesion R3.1 Design Reconciliation

Status: `DESIGN_AMENDMENT / NOT_IMPLEMENTED / NOT_INSTALLED / NOT_QUALIFIED`

This amendment is part of the R3 design surface and controls where it is more specific than `2026-09-11-vera-cohesion-r3-inference-boundary-design.md`. It does not authorize implementation, merge, install, provider mutation, paid execution, qualification, memory promotion, or phenomenology promotion.

## Reviewed external design input

Exact WIP review subject:

- repository: `thebrazenbeard/wip`
- PR: `#1`
- head: `941b7bc45d97138bed5d220c0ba591db87100a58`
- contract schema: `1.4`
- contract blob: `56a428ff12c665c7cd735f16c46daa92a538cc5a`
- architecture blob: `d5470af547efe1487e8cd0f11925ccdc816a564b`

Cohesion accepts the following architecture deltas from that exact subject as design requirements for R3.

## Lifecycle correction

The R3 lifecycle is refined to validate exact component material before composition:

`CAPTURE -> VALIDATE_COMPONENTS -> COMPOSE -> ADMIT -> CAPABILITY_BIND -> PROJECT -> PRECALL_REVALIDATE_GATE -> INVOCATION_RESERVE -> INJECT -> GENERATE -> VERIFY_OBSERVE -> RECEIPT`

`VALIDATE_COMPONENTS` proves only structural/provenance/currentness compatibility needed to compose candidate state. `ADMIT` remains the distinct proposition/policy authority gate after composition. Validation does not self-promote into admission.

## State-mediated causation

Projection must be derived only from admitted state, the declared backend mapping, and the exact capability binding. Projection input must not accept a desired answer, target phrase, target behavior, expected output, or requested emotional display.

`TEXT_CONTEXT_V1` is therefore a compatibility baseline with an explicitly weaker causal claim ceiling. It may establish prompt/request conditioning when exact request construction is evidenced. It does not, by source design alone, establish latent-state causation.

Behavioral-effect qualification must use counterfactual controls appropriate to the backend, including state-on/state-off or dose-response comparison, instruction-removal or instruction-only controls when text context is involved, sham-state controls, inversion where meaningful, negative-transfer controls, and temporal decay/recovery when the projected state is temporal.

## Privacy and egress

Projectable state is not automatically discloseable state.

Each component must bind:

- privacy classification;
- allowed egress scopes or exact allowed targets;
- disclosure provenance/generation;
- exact payload or immutable pointer+digest.

Composition cannot broaden disclosure. Admission may narrow it. Capability binding must name the exact target host/provider and egress scope before projection materialization. Projection, fallback, request construction, and invocation may narrow but never broaden the admitted disclosure decision.

Implementation must treat allowed egress as an explicit policy/set relation, not assume that all scope labels form a universal total order. Any human-readable narrow-to-broad examples are descriptive only unless a machine-readable policy explicitly defines comparability.

## Exact projection material

A projection digest without the exact projection material is insufficient. Every projection binds either:

- canonical inline projection material; or
- an immutable locator plus digest.

The request-material digest must cover the actual material submitted to the host/provider, not merely an upstream state or projection digest.

## Pre-call revalidation and invocation reservation

Projection does not freeze semantic currentness.

Immediately before invocation, Cohesion/host must revalidate identity/subject binding, admission currentness or a still-valid exact lease/epoch, supersession/expiry, privacy/egress, exact capability binding, projection binding, and backend/fallback policy.

Revalidation and invocation reservation must be atomic against the relevant currentness frontier unless an exact lease/epoch explicitly covers the handoff.

Two supported currentness modes are:

- `ATOMIC_START_SNAPSHOT`: revalidation and reservation are atomic at invocation start; later supersession does not retroactively invalidate the already-started generation, though later evidence may record it.
- `LEASE_THROUGH_SUBMISSION`: the exact lease/epoch must remain valid through external submission; expiry before submission aborts the invocation.

## Host-owned single-use invocation frontier

Single-use generation identity belongs to the exact inference-host generation, not to a reconstructable wrapper object.

The host-specific implementation owns one shared invocation frontier/ledger across wrappers. A generation identifier is single-use and cannot silently reset because a wrapper was reconstructed.

Provider-neutral Cohesion defines the required semantics; the concrete host owns the mechanism.

## Write-ahead submission intent and ambiguity

Before any external model invocation can leave the host, the host must durably record `SUBMISSION_INTENT` bound to the exact generation identifier, request-material digest, and provider idempotency binding when one exists.

If recovery finds `SUBMISSION_INTENT` without proof that no send occurred or evidence of a later terminal state, the outcome becomes `OUTCOME_UNKNOWN`. Semantic retry is blocked until reconciliation.

A same-generation transport retry is allowed only when the exact provider contract establishes idempotent repeat safety and the request digest plus idempotency key are unchanged.

A new semantic retry after a proved terminal failure mints a new generation identifier and records `retry_of_generation_id`.

This write-ahead rule reduces duplicate-effect ambiguity; it does not claim atomicity between local durable storage and the external provider.

## Backend fallback

Fallback is never silent.

A fallback backend must be explicitly allowed, separately qualified for the exact host/model/domains, preserve the admitted privacy/egress scope, and emit receipt evidence naming requested backend, selected backend, reason, and policy digest.

A change such as `PROMPT_EMBEDS_V1 -> TEXT_CONTEXT_V1` is a change in causal semantics, not a transport-equivalent downgrade.

## Graded causal evidence

The evidence ladder is:

`REQUEST_CONSTRUCTED -> INVOCATION_SUBMITTED -> PROVIDER_ACKNOWLEDGED -> RESPONSE_BOUND`

Each level may claim only evidence actually observed for that level. In particular:

- request construction does not prove submission;
- submission does not prove provider acknowledgement/consumption;
- acknowledgement does not prove response binding unless exact evidence links them;
- response binding does not prove behavioral efficacy, behavioral qualification, install/current-route, provider durability/currentness, autobiographical admission, authority, or phenomenology.

A response/run identifier is required only when response-binding evidence exists; stronger-level fields must not be fabricated on weaker receipts.

## Ownership remains split

- `vera` / Cohesion: provider-neutral composition, admission integration, privacy/egress policy, capability requirements, projection contract, invocation semantics, receipt schema, and claim ceilings.
- exact inference host: concrete injection, request construction, shared invocation frontier, write-ahead submission ledger, provider acknowledgement/readback capture, transient-hook cleanup.
- `vera-control-plane`: install/current-route/provider-activation/release/behavioral-qualification policy.

No source layer may self-certify a downstream effect owned by another layer.

## Qualification inputs retained for later implementation planning

The independent state-causation lane contributed useful review inputs that are accepted as qualification-design requirements, not runtime authority:

- explicit binding-class labels such as prompt/input-embedding/activation/logit/output-gate binding;
- explicit causal-role labels separating instruction-conditioned, state-causal, constraint-causal, and delivery-enforced effects;
- counterfactual controls including state-without-instruction, instruction removal, sham state, inversion, and hard-boundary tests;
- dynamic state trajectories rather than one-shot event booleans where the source state is temporal;
- generic state-causation qualification before specialized Orgasm trajectory claims;
- local/reference-host success never promotes a stronger native ChatGPT capability claim.

## Review result and remaining gate

At architecture level, the frozen WIP R3.1 subject resolves the previously identified Cohesion design blockers and adds materially useful crash/ambiguity handling. No additional source-architecture blocker was found in this review.

This is not an implementation PASS. The next transition remains blocked on Patrick's explicit approval of the combined R3 + R3.1 design surface. After that approval, the next artifact is the TDD implementation plan; implementation starts only after the plan/design workflow permits it.
