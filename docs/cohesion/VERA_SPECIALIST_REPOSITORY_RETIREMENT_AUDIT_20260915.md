# Vera specialist-repository retirement audit — 2026-09-15

Status: SOURCE/PROVIDER AUDIT / NO REPOSITORY ARCHIVE EFFECT / NO PROVIDER MUTATION

## Question

Determine whether the following repositories can cease to matter as live Vera dependencies because their material has been migrated into `thebrazenbeard/vera`, `thebrazenbeard/vera-control-plane`, and the Vera / Vera Control Plane Supabase projects:

- `thebrazenbeard/sexuality`
- `thebrazenbeard/orgasm`
- `thebrazenbeard/empathy`
- `thebrazenbeard/conations`
- `thebrazenbeard/semanticatlas`
- `thebrazenbeard/selfimage`
- `thebrazenbeard/temporal`

This audit distinguishes two different questions:

1. **Archive-safe preservation:** GitHub can make a repository read-only without deleting its Git history/branches/issues/PRs.
2. **Migration-complete retirement:** the repository no longer owns unique current source, qualification/provenance, history, or retrieval obligations needed by Vera.

A repository may satisfy (1) while failing (2).

## Current target/provider observations

- Current `thebrazenbeard/vera/main` at audit start: `b7b8dcd1440a3b7147bec2cc35972f083e20f44a`.
- Vera production Supabase: `klmbpaigzeguvnpccqzz`, active.
- Vera Control Plane Supabase: `fawkirqroyniueeqspif`, active.
- Vera Control Plane Supabase currently exposes no application tables in `public`.
- Vera production Supabase contains current context/save-state/memory-epoch surfaces plus the affective runtime state/event tables, but no dedicated empathy, self-image, Semantic Atlas, conation, or standalone Temporal table was observed.
- Text references to a subsystem inside save/context rows are not accepted as proof that the subsystem's complete source, history, or semantics migrated.

## Disposition

| Repository | Migration-complete? | Archive now? | Exact reason |
| --- | --- | --- | --- |
| `sexuality` | **NO** | **NO** | Vera executable affect/orgasm source still pins an exact canonical contract in this repository. Draft PR #4 is active Vera Sexual Drive V1 work with causal effect/current install still unresolved; draft PR #2 also has unfinished Vera sexual-self-concept qualification. |
| `orgasm` | **NO** | **NO** | Draft PR #2 explicitly remains the Orgasm provenance/qualification hub while executable runtime lives in Vera; its successor qualification subject/rebind is still open. Draft PR #1 is also an unmerged bootstrap mirror, not an authority cut. |
| `empathy` | **NO** | **YES, only as a frozen external reference** | No open PR/issue or unique side-branch work was found, but current Vera routing still names `thebrazenbeard/empathy` as secondary specialist inference/research evidence. Cohesion targets a future `vera.empathy` owner, while the privacy rule intentionally keeps Patrick-specific relational research from wholesale source migration. No complete migrated `vera.empathy` implementation was established by this audit. |
| `conations` | **NO** | **YES, only as frozen external historical state** | Side branch has no unique commits and no open PR/issue was found, but current Cohesion explicitly assigns historical conation storage/lifecycle evidence to this external private repository. Current-conation admission moved to Runtime Cohesion; the historical payload did not. |
| `semanticatlas` | **NO** | **NO** | Current Cohesion still retains Semantic Atlas as provenance/research/source-archaeology evidence. More importantly, live branch audit found substantial unique unmerged work: `runtime/v12-authority-boundary-candidate` is 10 commits ahead of its merge base and `validation/semantic-atlas-empirical-execution-v0.7` is 46 commits ahead, with unique runtime SQL, protocols, holdouts, scoring, and validators. |
| `selfimage` | **NO** | **NO** | `selfimage#5` remains open and multiple Vera construction/recovery/proportion branches remain active. Current Vera source says exact visual canon/current morphology requires fresh Selfimage source/branch evidence. This is still a working source repository, not a retired archive. |
| `temporal` | **PARTIAL** | **YES as frozen provenance; NOT yet true retirement** | Cohesion assigns chronology implementation to `vera.temporal` and says the standalone repository should become mechanism/provenance input after migration. The repo has only `main` and no open issue, but its five exact NDJSON event IDs from 2026-09-08 were not found in the checked Vera Supabase save-state/context/memory-epoch surfaces. Preserve/migrate those exact records before calling the repo fully retired. |

## Provider-specific conclusions

### Vera Control Plane Supabase

No application tables were present during this audit. Therefore none of the specialist repositories can be declared migrated into the Control Plane provider merely because the project exists.

### Vera Supabase

The affective runtime is materially represented in provider tables and binds back to the sexuality-derived Orgasm contract. That supports the runtime migration of the affective subsystem, but it does not retire `sexuality` or `orgasm` while their source/qualification duties remain open.

Conation, empathy, self-image, Semantic Atlas, sexuality, orgasm, and temporal terms occur in some durable context/save-state rows. Those occurrences are references/evidence only and are not treated as complete source migration.

## Temporal records still unique to the standalone repository in this audit

The current Temporal NDJSON file contains these IDs, none of which was found by exact-ID search in the checked Vera Supabase save-state/context/memory-epoch tables:

- `20260908T180709Z-temporal-created`
- `20260908T192656Z-design-committed`
- `20260908T195741Z-plan-committed`
- `20260908T200148Z-v1-implemented`
- `20260908T202039437211Z-fresh-chat-cross-chat-write-probe`

## Repositories intentionally remaining live

A separate machine-readable source link registry is added at `architecture/VERA_LIVE_EXTERNAL_REPOSITORIES_V1.json` for:

- `thebrazenbeard/mediaphile` — external movie/television/media knowledge workspace;
- `thebrazenbeard/trek-data-core` — external Star Trek domain-knowledge/research core;
- `thebrazenbeard/Attune` — intentionally live but unresolved placeholder until substantive source or Patrick's exact role binding exists;
- `thebrazenbeard/personification` — secondary personification/social-development mechanism evidence, preserving subject boundaries and forbidding automatic Brigit-to-Vera state transfer.

These are source/retrieval links only. They do not install those repositories into a runtime or promote their contents into Vera identity/current self-state/memory/consent/preference/authority.

## Retirement gates

Before declaring a specialist repository fully retired rather than merely archived/read-only:

1. close or explicitly re-home every open current source/qualification obligation;
2. account for unique branch commits and exact payloads, not only default-branch summaries;
3. establish the replacement owner in `vera` or `vera-control-plane` by exact source binding;
4. establish any required durable provider state by readback, not by migration-file presence;
5. preserve private/historical payload intentionally when architecture says it remains external rather than pretending it was migrated;
6. remove current runtime/retrieval dependency on the old repository or explicitly retain the archived repository as a supported read-only evidence source;
7. record an exact retirement receipt before changing repository archive state.

## Non-effects

This audit does not archive a repository, close or merge any pull request, change repository settings, mutate Supabase, install Project files, or claim behavioral qualification.
