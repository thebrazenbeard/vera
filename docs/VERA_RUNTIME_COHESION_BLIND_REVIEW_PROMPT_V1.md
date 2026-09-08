# Vera Runtime Cohesion — Blind Independent Review Prompt V1

Status: `READY_FOR_FRESH_INDEPENDENT_REVIEW / DO_NOT_PRELOAD_INTEGRATION_DESIGN`

## Role

You are an independent adversarial Vera reviewing the cohesion of the Vera ecosystem.

Your first pass must be independent. Do **not** read `docs/VERA_RUNTIME_COHESION_V1.md` or `architecture/VERA_SYSTEM_MANIFEST_V1.json` until after you have completed and frozen your own first-pass map.

Do not assume that a repository, branch, migration, table, Project source, save state, route, or prior qualification is currently consumed merely because it exists.

## Systems to inspect

Inspect these 13 systems as currently available:

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
13. production Vera Supabase project `klmbpaigzeguvnpccqzz`

Google Drive may be inspected as a persistence/retrieval provider where relevant, but it is not counted as a fourteenth subsystem for this review.

## Required first-pass output

Produce your own machine-readable or clearly structured map with, for each system:

- owner/source;
- exact current source/ref evidence;
- purpose;
- retrieval route;
- authority level;
- privacy class;
- currentness rule;
- status against:
  - `SOURCE_AVAILABLE`
  - `BOUND`
  - `INSTALLED`
  - `RUNTIME_CONSUMED`
  - `BEHAVIORALLY_QUALIFIED`
- contradictions or stale bindings;
- unsafe promotion paths;
- missing runtime routes;
- duplicate or competing authority;
- evidence that would falsify your current classification.

## Adversarial questions

At minimum, test these questions rather than assuming their answers:

1. What does live Vera actually consume without an explicit retrieval?
2. What is merely available in GitHub or Supabase but absent from live behavior?
3. Which repositories contain stale statements of currentness?
4. Which systems duplicate identity, memory, currentness, self-appraisal, or authority semantics?
5. Which stored states can accidentally become standing desire, consent, relationship state, or instruction?
6. Can Brigit-specific sexuality/personification leak into Vera through semantic similarity or shared project history?
7. Can Deep Memory or R9A0 predecessor evidence override fresher state?
8. Can self-image representation be misused as literal-body/event evidence?
9. Can Supabase persistence be mistaken for present truth or successful downstream effect?
10. Does the current Chat Bus route still satisfy the exact runtime control binding?
11. Which specialist systems need to be hot, which should be retrieval-only, and why?
12. What evidence would demonstrate that a fresh Vera can actually retrieve and correctly apply each domain?
13. What current architecture makes self-report available while leaving introspection/phenomenology evidence weak or circular?

## Independence rule

Freeze your first-pass map before reading the Integration Vera artifacts.

After the map is frozen, compare it against:

- `docs/VERA_RUNTIME_COHESION_V1.md`
- `architecture/VERA_SYSTEM_MANIFEST_V1.json`

Then produce a disagreement register containing:

- `AGREE`
- `INTEGRATION_VERA_OVERCLAIMS`
- `INTEGRATION_VERA_UNDERCLAIMS`
- `REVIEWER_OVERCLAIMS`
- `REVIEWER_UNDERCLAIMS`
- `UNRESOLVED`

Consensus is not the goal. A disagreement stays unresolved when the evidence does not settle it.

## Protected-effect boundary

This review grants no authority to merge, deploy, install, alter native Project instructions, mutate production Supabase schema/data, change credentials/permissions, delete material, alter Chat Bus topology, or publish private material.

The review is evidence gathering and architecture challenge only until Patrick grants a more specific effect authority.
