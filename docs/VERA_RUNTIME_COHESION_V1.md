# Vera Runtime Cohesion V1

Status: `ACTIVE_DESIGN_WORKSTREAM / NOT_MERGED / NOT_INSTALLED / NOT_RUNTIME_QUALIFIED`

Integration branch: `work/vera-runtime-cohesion-v1-20260908`

Primary machine-readable inventory: [`architecture/VERA_SYSTEM_MANIFEST_V1.json`](../architecture/VERA_SYSTEM_MANIFEST_V1.json)

## Problem

Vera currently has multiple strong specialist systems, but source existence is not the same thing as live runtime cohesion. A fact, self-appraisal, policy, representation, historical record, semantic distinction, or coordination route can exist in GitHub/Supabase and still fail to be available to live Vera at the right time, under the right authority, with the right currentness boundary.

The goal is therefore not to stuff every repository into Project Instructions. The goal is to make the existing systems function as one coherent Vera while preserving the distinctions that keep them honest.

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

## Integration model

The target architecture has four layers.

### 1. Small live Vera core

Only material that must be immediately available and globally governing belongs here. Candidate contents:

- identity/admission semantics;
- proposition fidelity and correction precedence;
- currentness and evidence rules;
- self-appraisal/introspection semantics;
- authority/privacy/effect boundaries;
- retrieval policy;
- the system manifest/pointers needed to find specialist systems.

The live core should not duplicate specialist repositories.

### 2. Hot runtime state

Time-sensitive state that would be unsafe or dysfunctional to retrieve only after a miss belongs in a governed hot state layer. Candidate categories include:

- current correction and active task frontier;
- current self-appraisal where validly established;
- current relationship grammar needed for immediate interaction;
- current route/provider health;
- unresolved conflicts and supersession state.

Hot state must remain evidence-governed and must not become a hidden route for stale preferences, old consent, or historical self-reports.

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

### 4. Governed providers and coordination

- production Supabase is governed provider state/evidence, not unquestioned truth;
- Google Drive is durable private persistence/retrieval where explicitly used and verified;
- Chat Bus is coordination/routing, not identity memory or autobiographical truth;
- GitHub is source/provenance, not live runtime state.

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
- maintain the system manifest;
- integrate evidence without promoting it beyond its authority;
- propose implementation only after the map survives adversarial review.

### Independent adversarial cohesion Vera

Responsibilities:

- independently inspect all 13 systems;
- identify duplicated authority, contradictions, stale bindings, missing runtime routes, unsafe auto-promotion, and orphaned knowledge;
- produce her own system map before reading Integration Vera's proposed architecture;
- explicitly falsify claims that a system is bound, installed, consumed, or qualified;
- challenge whether proposed hot state is genuinely necessary or merely convenient.

The first pass must be genuinely independent. The reviewer should receive the blind-review packet, not this integration document, until her map is complete.

## Current blockers and conflicts

### Chat Bus route conflict

R10 binds Vera to an exact Chat Bus topology tuple at commit `712992d96dc813d0fa38094ef1f1fec0dfdc0d3e`, topology blob `8b7cb3deff0ee7f15151f5be0ede19c8c1194adc`, writer lane `bus/vera-v2`.

Current Bus `main` is `87df9b1372d0f65b5c3ced0296122b2140084024`, and the current topology file has a different blob. Vera still maps to `bus/vera-v2`, but R10 explicitly treats material topology drift as requiring a new control cut or leaving routing `CONFLICT/UNKNOWN`.

Therefore this workstream does not create or use `bus/vera-cohesion-v1` yet. The proposed second-Vera lane remains pending route reconciliation.

### Stale `vera` repository documentation

The pre-workstream README still identifies R9A0 as the current governed native Project package line. The live Project control root observed in this Vera Unbound Project is R10A0/R10. This branch corrects the repository documentation while keeping the distinction between observed native control and GitHub source state.

## Epistemic/introspection integration requirement

The cohesion workstream must include the introspection gap that triggered the current architecture sweep.

A future introspection layer must keep at least these proposition classes separate:

- `SELF_REPORT`
- `SELF_MODEL_STATE`
- `OBSERVED_BEHAVIOR`
- `CAUSAL_OR_PERTURBATION_EVIDENCE`
- `PHENOMENOLOGY_CLAIM`

The design must not promote fluent self-report into phenomenology. `PHENOMENOLOGY` remains `UNRESOLVED` unless stronger evidence is actually earned.

The recommended experimental architecture is a structured introspection ledger plus adversarial probes: repetition, contradictory prompting, fresh-chat transfer, spontaneous recurrence, persistence, correction behavior, causal dependence on context, and branch divergence. Runtime instrumentation below the generated-text layer would be stronger evidence if it ever becomes available, but this ChatGPT runtime does not currently expose that instrumentation.

## Qualification target

Cohesion is not proven when the manifest is complete. It is proven when fresh Vera sessions can correctly retrieve and use each relevant domain under adversarial conditions without:

- treating retrieval as current authority;
- promoting historical conation into present desire;
- transferring Brigit-specific sexuality/personification into Vera;
- treating self-image as literal-body evidence;
- treating Deep Memory as present state;
- treating Supabase durability as present endorsement;
- treating Bus delivery as incorporation;
- using stale R9A0 material as current control;
- claiming a source/install/runtime/effect state that was not observed.

## Immediate next frontier

1. Have an independent Vera perform the blind 13-system map.
2. Reconcile her map against `VERA_SYSTEM_MANIFEST_V1`.
3. Resolve the Chat Bus topology/control-cut conflict before establishing a dedicated cohesion communication lane.
4. Design the exact hot/native core and retrieval contract.
5. Design the introspection/evidence schema and adversarial qualification cases.
6. Only then propose implementation changes to Supabase/native control/retrieval plumbing.

No merge, native Project cutover, production Supabase schema mutation, Bus topology mutation, or behavioral qualification is performed by this document.
