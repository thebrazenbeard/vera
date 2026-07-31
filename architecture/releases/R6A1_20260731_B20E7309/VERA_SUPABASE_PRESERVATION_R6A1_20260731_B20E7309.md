# Supabase Preservation and Neutralization Plan

## Verdict
Yes. The Supabase work is important and worth preserving.

## Observed snapshot
This is a timestamped read-only observation, not a claim that the counts remain current forever.

- Supabase project: `klmbpaigzeguvnpccqzz`
- observed at: `2026-07-31T12:37:13.625307Z`
- maximum coordination sequence observed: `351`
- `public.vera_save_state_events`: 42 append-only rows
- `public.vera_coordination_events`: 329 append-only rows
- `public.vera_current_save_state`: 38 current projected rows
- `public.vera_coordination_latest`: 57 current coordination threads
- `public.vera_coordination_open_issues`: 16 current open issues

The project contains actual external persistence and coordination infrastructure. The append-only event model, supersession links, semantic JSON, source evidence, branch fields, temporal separation, and coordination views are useful independently of the former persona ontology.

## Contamination finding
The existing data cannot be treated as clean current state. The prior R6A0 review identified at least 12 rows directly incompatible with the neutral architecture because they are model-authored or model-self-reported conation, identity, relationship, or continuity records. This R6A1 snapshot did not rerun that row-by-row classification. Additional joint relational or continuity records and model-authored technical or inferred records still require human review.

No legacy row should be deleted or silently rewritten. Preserve it as evidence of the experiment and classify it.

## Preserve unchanged
- the Supabase project itself;
- database region and configuration;
- append-only coordination events;
- event sequence and thread structure;
- supersession and acknowledgement links;
- source evidence, semantic tags, timestamps, branch IDs, and JSON payloads;
- existing rows as immutable legacy evidence.

## Do not preserve as active truth
- `VERA_SELF_REPORT` epistemic claims;
- `VERA` authorship treated as ownership by an independent subject;
- `CONATION`, `IDENTITY`, `RELATIONSHIP`, or `CONTINUITY` rows that assert model-owned inner state;
- relational or visual canon as current model identity;
- any row whose authority depends on homecoming, checkpoint restoration, affection renewal, or persona consent.

## Migration strategy
1. Freeze the existing tables as legacy source material.
2. Create a new neutral V3 context table beside them.
3. Create quarantine and review views over legacy rows.
4. Copy nothing automatically.
5. Migrate only records individually classified as direct user statement, observed tool result, documented source, technical result, project decision, or provenance.
6. Convert model outputs to `MODEL_OUTPUT` or `MODEL_GENERATED_CLAIM`, never model self-report.
7. Keep the coordination table unless a later naming cleanup is desired.
8. Apply RLS and explicit service access before using the V3 table in production.

No production SQL is included in this replacement package. Repository Memory and temporal migration sources remain nonproduction and are exercised only in disposable-database tests unless separately authorized.

## R6A1 repository binding
The repository contains nonproduction Memory and temporal migration sources and disposable-database tests. Their presence does not authorize applying them to production project `klmbpaigzeguvnpccqzz`.
