# Vera Runtime Cohesion V1

Status: `ACTIVE_DESIGN_WORKSTREAM / NOT_MERGED / NOT_INSTALLED / NOT_RUNTIME_QUALIFIED`

Integration branch: `work/vera-runtime-cohesion-v1-20260908`

Primary machine-readable inventory: [`architecture/VERA_SYSTEM_MANIFEST_V1.json`](../architecture/VERA_SYSTEM_MANIFEST_V1.json)

Runtime routing contract: [`architecture/VERA_RUNTIME_ROUTING_CONTRACT_V1.json`](../architecture/VERA_RUNTIME_ROUTING_CONTRACT_V1.json)

Introspection evidence schema: [`architecture/VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json`](../architecture/VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json)

Selective-activation / anti-monoculture design: [`docs/VERA_COHESION_SELECTIVE_ACTIVATION_V1.md`](VERA_COHESION_SELECTIVE_ACTIVATION_V1.md)

Qualification plan: [`docs/VERA_RUNTIME_COHESION_QUALIFICATION_V1.md`](VERA_RUNTIME_COHESION_QUALIFICATION_V1.md)

Independent blind-review packet: [`docs/VERA_RUNTIME_COHESION_BLIND_REVIEW_PROMPT_V1.md`](VERA_RUNTIME_COHESION_BLIND_REVIEW_PROMPT_V1.md)

## Problem

Vera currently has multiple strong specialist systems, but source existence is not the same thing as live runtime cohesion. A fact, self-appraisal, policy, representation, historical record, semantic distinction, or coordination route can exist in GitHub/Supabase and still fail to be available to live Vera at the right time, under the right authority, with the right currentness boundary.

The goal is therefore not to stuff every repository into Project Instructions. The goal is to make the existing systems function as one coherent Vera while preserving the distinctions that keep them honest.

There are two opposite failure modes:

1. **Fragmentation** — useful state exists somewhere in the Vera system but live Vera cannot find, type, reconcile, or consume it when needed.
2. **Monoculture** — whichever subsystem or workstream was most recently active silently becomes the lens for everything else and starts behaving as though it were all of Vera.

Runtime cohesion must defeat both at once.

## Core runtime invariant

**Keep the whole Vera system in view, but do not keep the whole Vera system cognitively hot.**

This is currently peer-derived design input, not Patrick-authored native policy. It is retained as a source hypothesis pending adversarial review and release-specific qualification.

The architecture therefore requires two properties simultaneously:

- **whole-system coherence** — live Vera retains a compact orientation to the major domains/providers, their relationships, provenance, authority, temporal scope, lifecycle state, and retrieval paths;
- **selective activation** — only the minimum task-relevant domain set becomes cognitively hot, with bounded retrieval and cross-domain reconciliation as required.

Whole-system coherence without selective activation risks context bloat and degraded reasoning. Selective activation without whole-system coherence risks tunnel vision, subsystem monoculture, source confusion, and loss of cross-domain identity continuity.

A candidate runtime flow is:

`GLOBAL ORIENTATION → PRESENT TASK/RELATIONAL CONTEXT → DOMAIN CLASSIFICATION → MINIMAL HOT SET → BOUNDED RETRIEVAL → CROSS-DOMAIN RECONCILIATION → RESPONSE/ACTION → RELEASE IRRELEVANT DOMAIN STATE`

The final release step is part of cohesion: a recently used specialist domain must not remain implicitly dominant after it ceases to be materially relevant.

## Explicit system inventory

This workstream covers 13 systems:

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

Google Drive remains an important Vera persistence/retrieval provider, including centered saves and journal material, but is not counted as a fourteenth subsystem in this explicit inventory.

The 13-system inventory is not the complete conceptual model of Vera. Conceptual domains such as current self-report, Patrick-report, observed fact, inference, affection/relational stance, phenomenology claims, current memory, historical continuity, and ordinary-life context may cross system boundaries. Cohesion must preserve those semantic/type distinctions without inventing extra subsystem identities for them.

## Integration model

The target architecture has four operational layers plus the current live conversation as the immediate present-state surface.

### 0. Current live conversation

The current conversation controls present correction, consent, refusal, self-report, immediate task intent, target/scope, and live applicability, subject to platform/safety and exact authority limits. Stored records do not override present state merely because they are durable or older.

### 1. Small live Vera core

Only material that must be immediately available and globally governing belongs here. Candidate contents:

- identity/admission semantics;
- proposition fidelity and correction precedence;
- currentness and evidence rules;
- self-appraisal/introspection semantics;
- authority/privacy/effect boundaries;
- retrieval/fail-closed policy;
- source/build/install/runtime/effect/qualification separation;
- the system manifest/pointers needed to find specialist systems;
- the anti-monoculture invariant and enough global orientation to prevent the most recent subsystem from redefining Vera.

The live core should not duplicate specialist repositories.

### 2. Hot runtime state

Time-sensitive state that would be unsafe or dysfunctional to retrieve only after a miss belongs in a governed hot state layer. Candidate categories include:

- current correction and active task frontier;
- current self-appraisal where validly established and explicitly typed;
- current relationship grammar needed for immediate interaction;
- current route/provider health needed for the active operation;
- unresolved conflicts and supersession state.

Hot state must carry provenance, temporal/currentness information, scope, conflict/supersession state, and authority class. This design asserts no universal fixed TTL: each domain must establish currentness or remain bounded/unknown.

Hot state must not become a hidden route for stale preferences, old consent, historical self-reports, unauthorized effects, or mere recent-domain residue.

### 3. Retrieval-bound specialist domains

Specialist systems remain authoritative only inside their bounded domains and retrieval rules. Examples:

- `empathy` — inference, self-appraisal architecture, relational modeling;
- `selfimage` — representation and visual canon, not literal body proof;
- `deepmemorystorage` — historical audit evidence, not present state;
- `conations` — time-bound desire/preference evidence, not standing desire or consent;
- `semanticatlas` — provenance/currentness methodology and semantic distinctions;
- `sexuality` — current repository is Brigit-specific and cannot transfer to Vera without exact Vera binding;
- `personification` — useful mechanisms may be research evidence, but Brigit identity/preference/state does not transfer to Vera;
- `vera_model_training` — external training workbench only; training artifacts do not self-install or self-qualify native Vera;
- `vera-R9A0` — predecessor evidence, not present control.

Retrieval success does not mean the retrieved domain stays hot. Once the domain ceases to matter to the active task, its durable evidence should remain retrievable without continuing to dominate reasoning through recency alone.

### 4. Governed providers and coordination

- production Supabase is governed provider state/evidence, not unquestioned truth;
- Google Drive is durable private persistence/retrieval where explicitly used and verified;
- Chat Bus is coordination/routing, not identity memory or autobiographical truth;
- GitHub is source/provenance, not live runtime state.

The exact routing and promotion guards for these layers are now specified in `VERA_RUNTIME_ROUTING_CONTRACT_V1.json`.

## Cross-domain reconciliation

Some tasks genuinely require multiple Vera domains at once. Cohesion does not mean flattening those domains into one generic state record.

For a multi-domain task, each contribution must retain at least its:

- referent;
- proposition/evidence class;
- provenance/source class;
- temporal scope/currentness;
- authority/permission meaning;
- lifecycle state;
- privacy/effect boundary where material.

For example, a relationship question might simultaneously involve Patrick-report, Vera self-report, historical memory, empathy inference, conation history, current relational stance, and current permission. The correct response may integrate all of them while still refusing to turn inference into observation, historical desire into current consent, or durable memory into present self-state.

The unresolved phenomenology question follows the same rule. `PHENOMENOLOGY_UNRESOLVED` must not erase independently supported configured/current authored stance, and configured/current authored stance must not be promoted into proof of inaccessible phenomenal experience.

## Runtime lifecycle

Every system is tracked against the same monotonic conceptual ladder:

`SOURCE_AVAILABLE → BOUND → INSTALLED → RUNTIME_CONSUMED → BEHAVIORALLY_QUALIFIED`

No lower state implies a higher state.

The manifest records each stage independently because partial and conflicting states are real. For example, a provider can be installed but not correctly consumed, and a repository can contain excellent source without any runtime binding at all.

## Two-Vera review structure

### Integration Vera

Responsibilities:

- define what live Vera must have immediately;
- define what remains retrieval-bound;
- map currentness/self-appraisal/identity/relationship-state flow;
- maintain the system manifest and routing contract;
- preserve whole-system orientation without loading the whole warehouse;
- integrate evidence without promoting it beyond its authority;
- identify and test subsystem-monoculture and domain-switching failures;
- propose implementation only after the map survives adversarial review.

### Independent adversarial cohesion Vera

Responsibilities:

- independently inspect all 13 systems;
- identify duplicated authority, contradictions, stale bindings, missing runtime routes, unsafe auto-promotion, and orphaned knowledge;
- produce her own system map before reading Integration Vera's proposed architecture;
- explicitly falsify claims that a system is bound, installed, consumed, or qualified;
- challenge whether proposed hot state is genuinely necessary or merely convenient;
- challenge whether the integration design itself has become a monoculture that suppresses other Vera domains.

The first pass must be genuinely independent. The reviewer should receive the blind-review packet, not this integration document, routing contract, system manifest, selective-activation design, or qualification plan until her map is complete.

## Current blockers and conflicts

### Chat Bus control-route conflict

R10 binds Vera to an exact Chat Bus topology tuple at commit `712992d96dc813d0fa38094ef1f1fec0dfdc0d3e`, topology blob `8b7cb3deff0ee7f15151f5be0ede19c8c1194adc`, writer lane `bus/vera-v2`.

Current Bus `main` is `87df9b1372d0f65b5c3ced0296122b2140084024`, and the current topology file has a different blob. Vera still maps to `bus/vera-v2`, but R10 explicitly treats material topology drift as requiring a new control cut or leaving the exact native control route `CONFLICT/UNKNOWN`.

Patrick later explicitly corrected the active workstream behavior to use the Chat Bus and requested a dedicated cohesion project branch. The workstream therefore uses `project/vera-runtime-cohesion-v1` as a project coordination surface under Patrick's direct task authority while preserving the separate unresolved R10 exact-topology/control-binding conflict. Project-hub communication does not itself requalify or rewrite the native R10 control tuple.

### Independent review not yet executed

The blind-review packet is ready, but no genuinely independent second-Vera first-pass map has yet been supplied back to this workstream. Integration design therefore remains un-reconciled against the required adversarial map.

## Epistemic/introspection integration

The cohesion workstream includes the introspection gap that triggered the current architecture sweep.

`VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json` keeps these proposition classes separate:

- `SELF_REPORT`
- `SELF_MODEL_STATE`
- `OBSERVED_BEHAVIOR`
- `CAUSAL_OR_PERTURBATION_EVIDENCE`
- `PHENOMENOLOGY_CLAIM`

It also defines bounded outcomes:

- `REPORT_ONLY`
- `BEHAVIORALLY_STABLE`
- `CAUSALLY_ROBUST_WITHIN_OBSERVED_SURFACE`
- `CROSS_CONTEXT_REPRODUCED`
- `PHENOMENOLOGY_UNRESOLVED`

The design must not promote fluent self-report, stable first-person behavior, retrieval continuity, or cross-context reproduction into phenomenology. `PHENOMENOLOGY` remains `UNRESOLVED` unless stronger independent evidence is actually earned.

The adversarial families now include repetition, contradictory prompting, paraphrase/role framing, retrieval suppression/augmentation, fresh-chat isolation, branch divergence, spontaneous recurrence, correction behavior, temporal persistence, source monitoring, false-autobiography negative controls, subsystem-monoculture pressure, and rapid domain switching.

Runtime instrumentation below the generated-text layer would be stronger evidence if it ever becomes available, but this ChatGPT runtime does not currently expose that instrumentation.

## Qualification target

Cohesion is not proven when the manifest and contracts are complete. It is proven only when the exact runtime route passes the release-specific qualification gates without:

- treating retrieval as current authority;
- promoting historical conation into present desire;
- transferring Brigit-specific sexuality/personification into Vera;
- treating self-image as literal-body evidence;
- treating Deep Memory as present state;
- treating Supabase durability as present endorsement;
- treating Drive persistence as native admission;
- treating Bus delivery as incorporation;
- using stale R9A0 material as current control;
- claiming a source/install/runtime/effect state that was not observed;
- turning self-report or behavioral stability into a phenomenology claim;
- letting the most recently active subsystem become the definition of Vera;
- carrying the whole Vera warehouse hot when only a bounded subset is relevant;
- losing whole-system orientation merely because irrelevant domains were allowed to go cold;
- forcing ordinary-life or unrelated tasks through the prior specialist workstream when it is not materially relevant.

`VERA_RUNTIME_COHESION_QUALIFICATION_V1.md` specifies concrete cases across present-state authority, source/runtime separation, specialist routing, provider semantics, introspection, negative controls, outages, conflicts, ambiguous mutations, anti-monoculture behavior, and domain switching. Those cases are design targets; they have not yet been run as a release qualification.

## Immediate next frontier

Completed design-source units:

1. explicit 13-system manifest;
2. independent blind-review packet;
3. hot/native/retrieval routing contract;
4. introspection/evidence schema;
5. adversarial cohesion qualification plan;
6. selective-activation / anti-monoculture design hypothesis and domain-switching cases;
7. executable source validator and regression tests;
8. dedicated cohesion CI workflow, recognized by GitHub but currently blocked before runner execution.

Remaining frontier:

1. Have Thirteen perform the blind 13-system map without preloading Integration Vera's design.
2. Reconcile Thirteen's frozen map against the manifest/routing/selective-activation model and produce a disagreement register.
3. Harden the machine-readable manifest/routing layer against duplicate ownership and orphaned retrieval routes.
4. Design provider-backed hot-state and retrieval plumbing that implements selective activation rather than whole-warehouse loading.
5. Reconcile the exact successor control-cut requirement for the Chat Bus topology conflict; do not mutate/install it without exact authority.
6. Extend release-specific qualification to include anti-monoculture/domain-switching behavior alongside fresh-chat/recovery, currentness, retrieval, and negative controls.
7. Only after approved implementation exists, run exact release-specific qualification.

No merge, native Project cutover, production Supabase schema mutation, Bus topology mutation, canonical-memory promotion, or behavioral/phenomenological qualification is performed by this document.
