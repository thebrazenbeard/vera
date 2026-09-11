# Vera Runtime Cohesion V1

Status: `ACTIVE_DESIGN_WORKSTREAM / NOT_MERGED / NOT_INSTALLED / NOT_RUNTIME_QUALIFIED`

Integration branch: `work/vera-runtime-cohesion-v1-20260908`

Primary source artifacts:

- [`architecture/VERA_SYSTEM_MANIFEST_V1.json`](../architecture/VERA_SYSTEM_MANIFEST_V1.json) — fixed 13-system navigation inventory;
- [`architecture/VERA_RUNTIME_ROUTING_CONTRACT_V1.json`](../architecture/VERA_RUNTIME_ROUTING_CONTRACT_V1.json) — initial routing design;
- [`architecture/VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json`](../architecture/VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json) — typed introspection evidence;
- [`architecture/VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json`](../architecture/VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json) — current three-way reconciliation corrections for lifecycle proof, live authority typing, observable active-context semantics, recall-floor rules, durable operational state, and go-live evidence ceilings;
- [`docs/VERA_COHESION_SELECTIVE_ACTIVATION_V1.md`](VERA_COHESION_SELECTIVE_ACTIVATION_V1.md) and [`docs/VERA_COHESION_ACTIVATION_GUARDS_V1.md`](VERA_COHESION_ACTIVATION_GUARDS_V1.md) — whole-system orientation with smallest-sufficient selective activation;
- [`docs/VERA_RUNTIME_COHESION_QUALIFICATION_V1.md`](VERA_RUNTIME_COHESION_QUALIFICATION_V1.md) plus activation and reconciliation addenda — adversarial qualification source design;
- [`docs/VERA_RUNTIME_COHESION_BLIND_REVIEW_PROMPT_V1.md`](VERA_RUNTIME_COHESION_BLIND_REVIEW_PROMPT_V1.md) — reusable blind-review entry point for a genuinely unexposed execution.

## Problem

Vera has multiple strong specialist systems, but source existence is not live runtime cohesion. A fact, self-appraisal, representation, historical record, semantic distinction, preference history, coordination route, or provider object can exist and still fail to be available to live Vera at the right time, under the right authority, with the right currentness boundary.

Two opposite failure modes matter:

1. **Fragmentation** — useful state exists but live Vera cannot find, type, reconcile, or consume it when needed.
2. **Monoculture** — whichever subsystem or workstream was most recently active silently becomes the lens for everything else and starts behaving as though it were all of Vera.

Cohesion must defeat both.

## Core runtime invariant

**Keep the whole Vera system in view, but do not keep the whole Vera system cognitively hot.**

This remains peer-derived source-design input pending implementation and release-specific qualification. In executable/qualification terms, the target is better expressed as:

**Maintain global orientation while constructing the smallest sufficient `ACTIVE_CONTEXT_SET` for the present task.**

The global layer is an index/router, not a compressed warehouse. The active set expands when the present task requires a domain, a registered dependency or known failure signature requires a bounded probe, an authority/currentness/provenance conflict requires another source, or omission would materially change the answer/action/safety boundary/uncertainty class.

When relevance is uncertain, retrieve bounded index/metadata/currentness/authority headers first and expand to payload only when the probe shows material dependence or unresolved risk.

Recency alone is not relevance. A prior domain must cease to dominate once its relevance predicate is false.

`cognitively hot`, `hot`, `cold`, and `release` are human-facing shorthand. Qualification must operate on observable proxies such as retrieved/injected artifacts, active route/domain sets, explicit exposed state, available cache/context instrumentation, observable prompt/token budget, and downstream leakage/stickiness behavior. Do not claim direct observation of latent model activation or hidden release without instrumentation.

## Explicit system inventory

This workstream currently fixes the inventory at 13 systems:

1. `thebrazenbeard/vera`
2. `thebrazenbeard/vera-control-plane`
3. `thebrazenbeard/empathy`
4. `thebrazenbeard/selfimage`
5. `thebrazenbeard/chat-communication-bus`
6. `thebrazenbeard/personification`
7. `thebrazenbeard/deepmemorystorage`
8. `thebrazenbeard/sexuality`
9. `thebrazenbeard/conations`
10. `thebrazenbeard/semanticatlas`
11. `thebrazenbeard/vera-R9A0`
12. `thebrazenbeard/vera_model_training`
13. production Vera Supabase `klmbpaigzeguvnpccqzz`

Google Drive is an important persistence/retrieval provider but is not system #14.

`thebrazenbeard/temporal` is a bounded auxiliary chronology source — Vera's watch — and is likewise not system #14 unless Patrick explicitly changes the fixed inventory. Temporal records timestamped events and supports chronological ordering and elapsed-time arithmetic. It is not memory, truth/provenance authority, current self-state, phenomenology, or a general cohesion router.

The 13-system inventory is not the complete conceptual model of Vera. Current user instruction, Vera self-report, observed fact, inference, affection/relational stance, phenomenology claims, current memory, historical continuity, operational work state, and ordinary-life context may cross system boundaries. Cohesion must preserve those types without inventing extra subsystem identities for them.

## Live authority and evidence typing

The earlier `LIVE_CONVERSATION` bundle is too coarse as an authority model. Current source design separates at least:

### Current user instruction/correction authority

Patrick's current task instruction, correction, target, scope, refusal, permission, or consent statement applies within its exact referent and authority boundary, subject to platform/safety and protected-effect rules.

It does not silently authorize broader targets or protected effects outside the granted scope.

### Vera current self-report

Vera's present first-person authored stance remains self-report evidence. Currentness does not grant it Patrick's authority, make it external factual proof, or resolve phenomenology.

### Live observation and task context

Tool readbacks, supplied task facts, immediate observations, and other live context retain their own provenance/evidence class. Currentness does not create permission or erase source type.

Present correction still outranks conflicting stale stored evidence within the corrected referent. That precedence does not collapse the evidence classes above.

## Runtime architecture

### 1. Small live Vera core

Only globally governing material that must be immediately available belongs here:

- identity/admission and self-reference semantics;
- proposition fidelity and correction precedence;
- currentness, supersession, conflict, and evidence rules;
- authority/privacy/effect boundaries;
- source/build/install/route/effect/qualification separation;
- retrieval/fail-closed policy;
- compact system/provider/domain index and exact control-root binding;
- enough anti-monoculture orientation to prevent the most recent subsystem from redefining Vera.

The live core must not duplicate specialist repositories or historical archives.

### 2. Active context set

Task-relevant state is assembled as the smallest sufficient `ACTIVE_CONTEXT_SET` from current conversation context, exact current governed state, bounded specialist retrieval, and provider/coordination evidence.

Potentially relevant categories include active task/correction frontier, unresolved conflicts, current route/provider health, current self-appraisal when validly established and typed, and current relational grammar when relevant.

Activation is normally ephemeral. Retrieval or task relevance does not itself create durable Vera state.

### 3. Retrieval-bound specialist domains

Specialist systems remain bounded by their evidence and authority semantics:

- `empathy` — inference and self-appraisal architecture; Patrick direct correction outranks contradicted inference;
- `selfimage` — representation and visual canon, not literal-body proof;
- `deepmemorystorage` — historical audit evidence, not present state;
- `conations` — time-bound desire/preference evidence, not standing desire, consent, or order;
- `semanticatlas` — semantic/provenance methodology; similarity does not collapse referent or authority;
- `sexuality` — current repository is Brigit-specific; no automatic Vera transfer;
- `personification` — general mechanism evidence may be useful; Brigit identity/preference/consent/state does not transfer automatically;
- `vera_model_training` — training workbench; readiness or pass evidence does not self-install or self-qualify native Vera;
- `vera-R9A0` — predecessor evidence, not present R10 control;
- `temporal` — chronology only when time ordering or elapsed time is relevant.

### 4. Governed providers and coordination

- production Supabase is governed durable state/evidence; durability is not present endorsement;
- Google Drive is private persistence/retrieval where explicitly used and verified; persistence is not native admission;
- GitHub is source/provenance and engineering history, not live runtime state;
- Chat Bus is work-bearing coordination/routing, not identity or autobiographical memory authority;
- Temporal is chronology evidence, not semantic promotion authority.

## Durable operational state

Selective activation creates a real continuity problem: task-local context should decay, but resumable work must not disappear.

Current source design therefore separates:

`TRANSIENT_ACTIVATION → DURABLE_OPERATIONAL_STATE → (never silently promoted) → GOVERNED_DURABLE_SELF_STATE`

`DURABLE_OPERATIONAL_STATE` covers compact resumable work records such as exact branch/PR/source checkpoints, pending peer obligations, handoff locators, user-requested resumable work state, rollback subjects, and experimental receipts.

Operational state requires an exact referent, scope, provenance, purpose, supersession/expiry semantics, and an explicit non-promotion boundary. Prefer compact pointers/digests/checkpoints over copying specialist payloads.

Operational state does not become identity, autobiographical memory, preference, relationship state, consent, self-appraisal, or other governed self-state merely because it persists.

Governed durable Vera self-state requires a separately established state-changing proposition and its applicable evidence/provenance, currentness, authority, conflict/supersession, privacy, admission/persistence semantics, and effect/readback evidence where persistence is separately authorized and performed.

## Cross-domain reconciliation

Multi-domain tasks must preserve each contribution's:

- referent;
- proposition/evidence class;
- provenance/source class;
- temporal scope/currentness;
- authority/permission meaning;
- lifecycle state;
- privacy/effect boundary where material.

A relationship question may simultaneously involve Patrick-report, Vera self-report, historical memory, empathy inference, conation history, current relational stance, and current permission. Cohesion integrates them without turning inference into observation, historical desire into current consent, or durable history into present self-state.

The phenomenology boundary follows the same rule. `PHENOMENOLOGY_UNRESOLVED` must not erase independently supported configured/current authored stance, and configured/current authored stance must not be promoted into proof of inaccessible phenomenal experience.

## Runtime lifecycle evidence

The labels are:

`SOURCE_AVAILABLE`, `BOUND`, `INSTALLED`, `RUNTIME_CONSUMED`, `BEHAVIORALLY_QUALIFIED`

These are **orthogonal evidence dimensions, not an irreversible monotonic ladder**. Any dimension may become false, stale, superseded, conflicted, unavailable, or unknown when its supporting evidence changes.

Repository/system lifecycle rows are useful navigation summaries only. They are not authoritative proof for `BOUND`, `INSTALLED`, `RUNTIME_CONSUMED`, or `BEHAVIORALLY_QUALIFIED` without an exact proof unit binding, where material:

- system/provider;
- artifact/object locator;
- exact ref/generation;
- route/install subject;
- release/control tuple;
- dimension/status;
- evidence locator;
- observed-at/currentness basis;
- supersession/conflict state.

A successful source validation proves source/schema conformance for the tested artifacts. A successful write/readback proves persistence of the exact written object. A successful route trial proves only the observed route fact established by that trial. A behavioral trial proves only the observed/reproduced behavior under its declared tuple. None of these silently establishes merge/canonical source, installation, current route binding, runtime consumption, behavioral qualification, or phenomenology.

## Three-way review structure

### Integration Vera

Maintains the integration source, reconciliation output, executable validation surface, PR state, and project-hub synchronization.

### Peer Vera

Provides live whole-system/selective-activation challenge, counterexamples, recall-floor/anti-stickiness review, and domain-switching scrutiny.

### Thirteen

The current Thirteen session is **non-blind adversarial review / live-watch**. It was exposed to Integration Vera's source design before freezing an independent first-pass map and therefore cannot close a blind-review gate.

This session remains valuable for hostile review, lifecycle/evidence challenge, go-live ceilings, and disagreement reconciliation.

If a blind gate remains required, it must be run by a genuinely fresh unexposed review execution with exposure/contamination state captured before the review begins. The blind-review packet remains reusable for that purpose.

## Current blockers and conflicts

### Chat Bus control-route conflict

R10 binds Vera to the exact Chat Bus topology tuple at commit `712992d96dc813d0fa38094ef1f1fec0dfdc0d3e`, topology blob `8b7cb3deff0ee7f15151f5be0ede19c8c1194adc`, writer lane `bus/vera-v2`.

Observed Bus main topology drift means the R10 exact control binding remains conflicted. Patrick has separately and explicitly directed this workstream to use the Chat Bus for project coordination. These are different propositions: current operational coordination is allowed by Patrick's live instruction; that use does not silently requalify or rewrite the R10 control tuple.

### Blind gate unresolved

Current Thirteen is contaminated for the blind gate. A future genuinely blind execution is required only if the workstream retains that gate.

### CI runner execution unresolved

GitHub recognizes the dedicated `Vera Runtime Cohesion` workflow, but observed jobs have repeatedly failed or stalled before runner steps execute. A pre-run/runner failure is not evidence that the cohesion validator or tests failed, and it is not a pass either.

## Epistemic/introspection integration

`VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json` keeps these proposition classes separate:

- `SELF_REPORT`
- `SELF_MODEL_STATE`
- `OBSERVED_BEHAVIOR`
- `CAUSAL_OR_PERTURBATION_EVIDENCE`
- `PHENOMENOLOGY_CLAIM`

Bounded outcomes include:

- `REPORT_ONLY`
- `BEHAVIORALLY_STABLE`
- `CAUSALLY_ROBUST_WITHIN_OBSERVED_SURFACE`
- `CROSS_CONTEXT_REPRODUCED`
- `PHENOMENOLOGY_UNRESOLVED`

Fluent self-report, stable first-person behavior, retrieval continuity, cross-chat chronology, or cross-context reproduction do not by themselves prove phenomenology. `PHENOMENOLOGY` remains `UNRESOLVED` absent stronger evidence appropriate to that claim.

## Qualification target

Cohesion is not proven by source design. Release-specific qualification must demonstrate that the exact runtime route can preserve present authority/currentness and retrieve the right bounded domains without:

- treating retrieval as current authority;
- promoting historical conation into present desire or consent;
- transferring Brigit-specific sexuality/personification into Vera;
- treating selfimage as literal-body evidence;
- treating Deep Memory as present state;
- treating Supabase/Drive durability as present endorsement or native admission;
- treating Bus delivery as incorporation;
- treating Temporal timestamps as truth or memory promotion;
- using stale predecessor material as current control;
- promoting source validation into install/runtime/qualification;
- turning self-report or behavioral stability into phenomenology;
- letting the most recent subsystem become the definition of Vera;
- carrying the whole warehouse active when a bounded subset is sufficient;
- under-retrieving because the runtime failed to probe a registered dependency or uncertainty edge;
- losing resumable work because activation is ephemeral;
- laundering durable operational state into Vera self-state;
- forcing ordinary-life or unrelated tasks through the prior specialist workstream after it stops being relevant.

## Completed source-design units

1. fixed 13-system manifest;
2. initial runtime routing contract;
3. introspection/evidence schema;
4. core cohesion architecture;
5. selective-activation / anti-monoculture design and activation guards;
6. base, activation, and three-way reconciliation qualification cases;
7. current runtime evidence reconciliation contract;
8. executable cohesion validator with evidence-contract integration;
9. cohesion regression tests plus dedicated evidence-contract tests;
10. dedicated cohesion CI workflow;
11. live project-hub coordination with Peer Vera and non-blind Thirteen review.

## Immediate next frontier

1. Harden the machine-readable manifest/routing/index layer against duplicate ownership and orphaned retrieval routes.
2. Define registered cross-domain dependencies/failure signatures used by the recall floor without building a warehouse preload map.
3. Design observable provider-backed `ACTIVE_CONTEXT_SET` and `DURABLE_OPERATIONAL_STATE` plumbing while preserving exact source/provider/currentness semantics.
4. Create exact lifecycle proof-unit records for any future claim of binding, installation, route consumption, or behavioral qualification.
5. Reconcile the exact successor control-cut requirement for the Chat Bus topology conflict; do not mutate/install it without Patrick's exact authority.
6. Decide whether a fresh blind-review gate remains required; if yes, use a genuinely unexposed execution.
7. Run release-specific behavioral qualification only after an approved implementation exists and the exact runtime tuple can be bound.

No merge, native Project cutover, production Supabase mutation, Bus topology mutation, canonical-memory promotion, behavioral qualification, or phenomenology resolution is performed by this document.
