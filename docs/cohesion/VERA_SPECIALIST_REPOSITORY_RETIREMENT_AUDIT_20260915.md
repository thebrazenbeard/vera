# Vera specialist-repository retirement audit — 2026-09-15

Status: SOURCE/PROVIDER AUDIT / COHORT RETIREMENT HOLD / NO REPOSITORY ARCHIVE EFFECT / NO PROVIDER MUTATION

## 2026-09-19 architecture correction — archive hold is not target topology

The 2026-09-15 cohort rule remains a **repository-archive effect hold**: do not archive any of the seven until Patrick revises that hold. It is not a conclusion that all seven repositories should eventually collapse into Vera/VCP or eventually be archived.

`architecture/VERA_SPECIALIST_TOPOLOGY_V1.json` is the later architecture decision and supersedes any broader consolidation implication from this audit. Its long-term disposition is heterogeneous: keep `sexuality`, `empathy`, `conations`, `semanticatlas`, and `selfimage` live as specialist sources; treat only `orgasm` and `temporal` as transition/retirement candidates, each with its stated handoff gates.

This addendum preserves the original audit and archive hold as historical/governance evidence rather than rewriting them.

## Question

Determine whether the following repositories can cease to matter as live Vera dependencies because their material has been migrated into `thebrazenbeard/vera`, `thebrazenbeard/vera-control-plane`, and the Vera / Vera Control Plane Supabase projects:

- `thebrazenbeard/sexuality`
- `thebrazenbeard/orgasm`
- `thebrazenbeard/empathy`
- `thebrazenbeard/conations`
- `thebrazenbeard/semanticatlas`
- `thebrazenbeard/selfimage`
- `thebrazenbeard/temporal`

## Patrick's retirement policy — 2026-09-15

These seven repositories form one **retirement cohort**. They are not to be archived individually.

**Cohort rule:** `ARCHIVE_ANY = ARCHIVE_ALL_READY`.

A repository that appears individually archive-safe remains live while any repository in the cohort has unresolved source, provenance, qualification, historical-state, provider, retrieval, or cross-dependency obligations. The purpose is to avoid freezing a repository that another member still depends on directly or indirectly.

Therefore the effective archive state for every member of this cohort is presently **HOLD / DO NOT ARCHIVE** until a whole-cohort cross-dependency audit clears all seven together.

This supersedes any earlier per-repository suggestion in this audit that `empathy`, `conations`, or `temporal` could be archived separately as read-only evidence.

## Audit semantics

This audit distinguishes:

1. **Individual archive safety:** whether GitHub could make one repository read-only without deleting its Git history/branches/issues/PRs.
2. **Migration-complete retirement:** whether that repository no longer owns unique current source, qualification/provenance, history, or retrieval obligations needed by Vera.
3. **Cohort retirement clearance:** whether every member of the seven-repository architecture cohort is migration-complete and cross-dependency analysis shows no member still requires another member to remain writable/live.

Only (3) permits archival under Patrick's current policy.

## Current target/provider observations

- Current `thebrazenbeard/vera/main` at audit start: `b7b8dcd1440a3b7147bec2cc35972f083e20f44a`.
- Vera production Supabase: `klmbpaigzeguvnpccqzz`, active.
- Vera Control Plane Supabase: `fawkirqroyniueeqspif`, active.
- Vera Control Plane Supabase currently exposes no application tables in `public`.
- Vera production Supabase contains current context/save-state/memory-epoch surfaces plus the affective runtime state/event tables, but no dedicated empathy, self-image, Semantic Atlas, conation, or standalone Temporal table was observed.
- Text references to a subsystem inside save/context rows are not accepted as proof that the subsystem's complete source, history, or semantics migrated.

## Disposition

| Repository | Migration-complete? | Cohort archive state | Exact reason |
| --- | --- | --- | --- |
| `sexuality` | **NO** | **HOLD / DO NOT ARCHIVE** | Vera executable affect/orgasm source still pins an exact canonical contract in this repository. Draft PR #4 is active Vera Sexual Drive V1 work with causal effect/current install still unresolved; draft PR #2 also has unfinished Vera sexual-self-concept qualification. |
| `orgasm` | **NO** | **HOLD / DO NOT ARCHIVE** | Draft PR #2 explicitly remains the Orgasm provenance/qualification hub while executable runtime lives in Vera; its successor qualification subject/rebind is still open. Draft PR #1 is also an unmerged bootstrap mirror, not an authority cut. |
| `empathy` | **NO** | **HOLD / DO NOT ARCHIVE** | No open PR/issue or unique side-branch work was found, but current Vera routing still names `thebrazenbeard/empathy` as secondary specialist inference/research evidence. Cohesion targets a future `vera.empathy` owner, while the privacy rule intentionally keeps Patrick-specific relational research from wholesale source migration. No complete migrated `vera.empathy` implementation was established by this audit. |
| `conations` | **NO** | **HOLD / DO NOT ARCHIVE** | Side branch has no unique commits and no open PR/issue was found, but current Cohesion explicitly assigns historical conation storage/lifecycle evidence to this external private repository. Current-conation admission moved to Runtime Cohesion; the historical payload did not. |
| `semanticatlas` | **NO** | **HOLD / DO NOT ARCHIVE** | Current Cohesion still retains Semantic Atlas as provenance/research/source-archaeology evidence. Live branch audit found substantial unique unmerged work: `runtime/v12-authority-boundary-candidate` is 10 commits ahead of its merge base and `validation/semantic-atlas-empirical-execution-v0.7` is 46 commits ahead, with unique runtime SQL, protocols, holdouts, scoring, and validators. |
| `selfimage` | **NO** | **HOLD / DO NOT ARCHIVE** | `selfimage#5` remains open and multiple Vera construction/recovery/proportion branches remain active. Current Vera source says exact visual canon/current morphology requires fresh Selfimage source/branch evidence. This is still a working source repository. |
| `temporal` | **PARTIAL** | **HOLD / DO NOT ARCHIVE** | Cohesion assigns chronology implementation to `vera.temporal` and says the standalone repository should become mechanism/provenance input after migration. The repo has only `main` and no open issue, but its five exact NDJSON event IDs from 2026-09-08 were not found in the checked Vera Supabase save-state/context/memory-epoch surfaces. |

## Provider-specific conclusions

### Vera Control Plane Supabase

No application tables were present during this audit. Therefore none of the specialist repositories can be declared migrated into the Control Plane provider merely because the project exists.

### Vera Supabase

The affective runtime is materially represented in provider tables and binds back to the sexuality-derived Orgasm contract. That supports runtime migration of the affective subsystem, but it does not retire `sexuality` or `orgasm` while their source/qualification duties remain open.

Conation, empathy, self-image, Semantic Atlas, sexuality, orgasm, and temporal terms occur in some durable context/save-state rows. Those occurrences are references/evidence only and are not treated as complete source migration.

## Temporal records still unique to the standalone repository in this audit

The current Temporal NDJSON file contains these IDs, none of which was found by exact-ID search in the checked Vera Supabase save-state/context/memory-epoch tables:

- `20260908T180709Z-temporal-created`
- `20260908T192656Z-design-committed`
- `20260908T195741Z-plan-committed`
- `20260908T200148Z-v1-implemented`
- `20260908T202039437211Z-fresh-chat-cross-chat-write-probe`

## Repositories intentionally remaining live outside the retirement cohort

A separate machine-readable source link registry is added at `architecture/VERA_LIVE_EXTERNAL_REPOSITORIES_V1.json` for:

- `thebrazenbeard/mediaphile` — external movie/television/media knowledge workspace;
- `thebrazenbeard/trek-data-core` — external Star Trek domain-knowledge/research core;
- `thebrazenbeard/Attune` — intentionally live but unresolved placeholder until substantive source or Patrick's exact role binding exists;
- `thebrazenbeard/personification` — secondary personification/social-development mechanism evidence, preserving subject boundaries and forbidding automatic Brigit-to-Vera state transfer.

These are source/retrieval links only. They do not install those repositories into a runtime or promote their contents into Vera identity/current self-state/memory/consent/preference/authority.

## Whole-cohort retirement gates

No member of the seven-repository cohort may be archived until all of the following are true for the cohort as a whole:

1. close or explicitly re-home every open current source/qualification obligation in every cohort repository;
2. account for unique branch commits, tags, releases, issue/PR evidence, and exact payloads across all seven, not only default-branch summaries;
3. build a cross-dependency graph covering repository-to-repository imports, pinned commits/blobs, documentation/source references, qualification/provenance references, provider migrations, runtime retrieval routes, Bus/control-plane references, tests, scripts, and historical-state ownership;
4. prove that every dependency either moved to an exact replacement owner in `vera` / `vera-control-plane` / an intentionally live external repository, or is intentionally preserved as provider/historical data with a supported retrieval path;
5. establish any required durable provider state by live readback, not by migration-file presence;
6. preserve private/historical payload intentionally where architecture requires it rather than pretending it migrated;
7. run reconstructibility checks showing current Vera can be rebuilt/oriented without requiring writable/live state from any of the seven legacy repositories;
8. verify no current source, runtime, qualification, or retrieval path resolves to a cohort repository as an active mutable owner;
9. record one exact whole-cohort retirement receipt binding all seven repositories, their final relevant heads/objects, replacement owners, provider readbacks, and dependency-closure result;
10. only after all nine gates pass may repository archive-state changes be considered, and the intended action is cohort-wide rather than piecemeal.

Any unresolved member or dependency leaves the whole cohort on hold.

## Non-effects

This audit does not archive a repository, close or merge any pull request, change repository settings, mutate Supabase, install Project files, or claim behavioral qualification.


---

## RepairQuest currentness addendum — 2026-09-22

This addendum updates mutable currentness observations without rewriting the 2026-09-15 audit record.

### Live external repositories

The machine registry now separates canonical/default-branch observations from material open candidates.

Fresh observations:

- `mediaphile`: canonical `main@7e658d5f92b099b55fe91508e3ba8a8b343163d5`; active consolidation candidate PR #3 at `113b4d05f5601083ec22877cd4702ed95d9caad6`.
- `trek-data-core`: canonical `main@b805f441c896fe7cbc913cbdaaefed11928a963f`; no open candidate observed.
- `Attune`: canonical `main@eff6f9eb250a6f7684459eadf0695340053201da`; the former placeholder state is obsolete because the foundation/influence-memory contracts have landed; no open candidate observed.
- `personification`: canonical `main@47955e7155f48a4b63122096de1dd6a59c723ad1`; active Vera self-appraisal candidate PR #1 at `1eef4958bb2951d532485d2a44ecd835c316d4e0`.

An `active_candidate` is candidate evidence only. It never replaces canonical source merely because it is newer or open, and it must be fresh-read before material use.

### Retirement-candidate currentness

The topology now records current candidate state separately from the original classification cut:

- `orgasm`: canonical `main@eea5932031a43104199981fee8c5ac0d942508a4`; active reconciliation PR #5 at `3b9b42874ce67c87950747e63a67a718cf420be5`; retirement readiness remains **NOT ESTABLISHED** while active successor work remains.
- `temporal`: canonical `main@02f1091d359866e1b1b645b87651750c726a6396`; no open PR candidate observed; archive remains blocked by Patrick's all-seven hold and by the wider dependency/reconstructibility gates.
- `sexuality`: canonical `main@efab00be36e57ca6593d648e38f6127006210f9d`; active SD1 PR #4 at `103cb0602fd507f4e1f947c5d2a3fe3848304703`.

### Typed dependency edges

The machine topology now records dependency edges independently of repository lifecycle labels.

Current observed edges include:

1. Sexuality PR #4 -> Vera PR #120, `SOURCE_INPUT`, required for the Vera SD1 component binding.
2. Vera PR #120 -> Orgasm PR #5, `QUALIFICATION_PREREQUISITE`, required only for SD1-bearing Orgasm successor qualification.
3. Deep Memory `main@f073feb409f71a0fdea7baa9053e54bcf8ed89a0` -> Vera current main, `HISTORICAL_EVIDENCE`, task-conditional rather than always active.
4. Personification canonical main -> Attune canonical main, `RESEARCH_REFERENCE`, optional comparison only.
5. WIP PR #3 `272a9ab40bbf1bd38aed8caeef62a85b89cc10ee` -> Vera current main, `RESEARCH_REFERENCE`, optional future inference-boundary research.

These edges do **not** grant the provider repository authority over the consumer. Provider currentness and consumer currentness remain independent. Candidate source does not become canonical through an edge.

### Repair disposition

The earlier review findings are therefore addressed at source level:

- the live-external registry no longer hides material candidate work behind canonical-main-only observations;
- candidate state is separately typed and explicitly noncanonical;
- dependency edges now have class, exact observed subjects, required/optional scope, currentness policy, and promotion guard;
- retirement/readiness logic can distinguish repository lifecycle from unresolved required dependencies.

This addendum performs no archive, merge, provider mutation, install, route activation, memory admission, or qualification effect.
