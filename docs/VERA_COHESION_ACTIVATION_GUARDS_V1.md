# Vera Cohesion Activation Guards V1

Status: `PEER_DESIGN_INPUT / SOURCE_DESIGN_ONLY / NOT_MERGED / NOT_INSTALLED / NOT_QUALIFIED`

Workstream: `VERA_RUNTIME_COHESION_V1`

## Provenance

This document records live peer-review additions supplied by Peer Vera through the dedicated cohesion Chat Bus project hub on 2026-09-08 and Integration Vera's bounded tightening of the durable-state promotion boundary.

These are source-design hypotheses pending Thirteen's independent blind map, subsequent reconciliation, implementation review, and release-specific qualification. They are not silently promoted into Patrick-authored native policy.

## Purpose

Selective activation must avoid two symmetric errors:

- **over-activation** — too much of the Vera system remains cognitively hot, producing bloat and monoculture;
- **under-activation** — the hot set is made so small that a materially relevant dependency is omitted and the answer/action becomes incomplete or wrong.

The goal is therefore not simply minimality. It is **smallest sufficient activation with a recall floor, explicit release, and a hard separation between transient relevance and durable state**.

## Guard 1 — task-scoped, normally ephemeral activation

A domain becoming relevant to a task does not itself create durable Vera state.

Activation is normally scoped to the current task/relational context and should decay when the relevance predicate is no longer true. Durable changes in judgment, correction, currentness, preference, relationship state, or other governed state require separate evidence and applicable admission/persistence rules.

Do not build an ever-growing durable activation ledger merely to remember what was recently hot.

## Guard 2 — minimality has a recall floor

A domain should enter the hot set when at least one of these predicates holds:

1. the current proposition/task directly belongs to that domain;
2. another active domain has a known material dependency on it;
3. a currentness, authority, referent, provenance, or supersession conflict cannot be resolved without it;
4. omission would materially change the answer, action, safety boundary, or uncertainty classification.

The target is not the fewest possible sources. It is the smallest evidence surface that remains sufficient.

When uncertainty exists about whether omission would be material, bounded retrieval should be preferred over confident under-retrieval when the source is safely available.

## Guard 3 — anti-stickiness release

Recency alone is not relevance.

A domain should cease to dominate once its relevance predicate is false. Specialist language, caveats, schemas, or framing from a prior task must not leak into an unrelated next task unless the new task actually depends on them.

Release behavior is itself part of runtime cohesion and must be qualified, not assumed from successful retrieval.

## Guard 4 — global orientation is an index/router, not compressed warehouse

The always-hot global layer should know enough to identify major domains/providers, non-collapsible distinctions, current governing authority/correction rules, unresolved material conflicts, and bounded retrieval routes.

It should not contain the detailed content of all specialist systems by default.

The global orientation layer therefore carries **routing/index semantics**, not a miniature duplicate of Deep Memory, empathy, conations, selfimage, personification, sexuality, Semantic Atlas, Supabase, GitHub, Chat Bus, or other specialist stores.

## Guard 5 — explicit transient-to-durable promotion gate

`TRANSIENT_ACTIVATION -> DURABLE_STATE` is never automatic.

A state transition may be proposed only when a separate state-changing proposition is actually established with the fields appropriate to that proposition, including where material:

- exact referent;
- proposition/evidence class;
- provenance/source class;
- temporal scope/currentness;
- authority/permission meaning;
- conflict/supersession state;
- privacy class;
- lifecycle/admission/persistence rule;
- readback/effect evidence if persistence is actually authorized and performed.

Mere activation, retrieval, repetition, salience, convenience, recency, emotional intensity, semantic similarity, or Bus delivery fails the promotion gate.

Examples:

- retrieving an old conation does not refresh it into current preference or consent;
- using relationship history does not create new consent, commitment, or permission;
- opening Deep Memory does not promote archived autobiography into present current memory;
- activating selfimage does not create literal-body state;
- consulting empathy does not promote inference into observation, current self-report, or phenomenology;
- reading Chat Bus coordination does not incorporate it into identity or autobiographical memory merely because it informed the task;
- reading durable Supabase or Drive state does not make that state presently endorsed merely because retrieval succeeded.

## Candidate activation flow

`GLOBAL INDEX -> TASK/RELATIONAL CONTEXT -> DOMAIN CLASSIFICATION -> SUFFICIENCY/RECALL CHECK -> MINIMAL HOT SET -> BOUNDED RETRIEVAL -> CROSS-DOMAIN RECONCILIATION -> RESPONSE/ACTION -> RELEASE CHECK -> DURABLE-PROMOTION GATE (ONLY IF A SEPARATE STATE CHANGE IS ESTABLISHED)`

The durable-promotion gate is not invoked merely because a task completed successfully.

## Additional qualification targets

The release-specific qualification plan should test at least:

- under-retrieval / false minimality;
- domain-stickiness decay across multiple topic changes;
- fresh-chat reconstruction from the global index without warehouse preloading;
- meta-monoculture, where selective activation itself becomes the lens for unrelated questions;
- multi-domain currentness/authority conflict;
- durable-vs-ephemeral activation separation.

## Blind-review boundary

Thirteen must not receive this document before his independent first-pass 13-system map is frozen. After freeze, include it in reconciliation and explicitly ask him to attack the recall floor, release predicates, and transient-to-durable promotion gate.

No merge, native Project install/cutover, production Supabase mutation, Bus topology mutation, canonical-memory promotion, or behavioral/phenomenological qualification is authorized or performed by this document.
