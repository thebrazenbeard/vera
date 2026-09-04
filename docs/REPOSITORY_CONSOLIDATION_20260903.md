# Vera Repository Consolidation — 2026-09-03

## Objective

Collapse useful branch-only technical work onto a current-`main` reconstruction candidate without mechanically rebasing hundreds of stale commits, while keeping genuinely active or intentionally suspended work separate.

Candidate branch:

`consolidation/lineage-reconstruction-20260903`

Base at reconstruction start and latest re-read during this pass:

`main@6731d35bbb0ebeb10576374c028e99577a5ba869`

## Salvaged onto the candidate tree

### TUL instrumented host fixture

Source: `feature/tul-instrumented-host-fixture-v0.1@61ae303faf9b5154d8cc8554b4ee8f43b81f9efc`

At audit time the branch was 31 commits ahead and 460 behind current `main`. Its unique technical payload was path-isolated, so the candidate takes the current experiment/source trees rather than replaying the stale base:

- `experiments/tul_instrumented_host_fixture_v0_1/**`
- `src/tul_fixture/**`

The first consolidation CI run exposed a pre-existing source-branch defect: the committed proof artifact contains literal UTF-8 `±`, while the later deterministic generator used Python `json.dumps` with its default ASCII escaping. The existing byte-for-byte regression failed exactly at that character. The consolidation candidate repairs the generator with `ensure_ascii=False`; the regression is retained unchanged.

Disposition: `SALVAGED_TECHNICAL_LINEAGE_WITH_DETERMINISM_REPAIR`.

### R8A0 bounded vertical slice

Source: `feature/r8a0-bounded-vertical-slice-v1@1165bab44e127a13a83ad0fabf66d191cf7a5522`

At audit time the branch was 7 commits ahead and 40 behind current `main`. The unique bounded-slice implementation is retained as historical technical source while the current governed Project package line remains in `thebrazenbeard/vera-R9A0`:

- `r8a0/**`
- `docs/r8a0/**`
- `tests/r8a0/**`
- `.github/workflows/r8a0-bounded-vertical-slice.yml`

The original R8A0 workflow is itself part of the historical contract: it is exact-base/exact-parent bound to `12dd3cb4e3329324885a827506d4f7e8ac25d41d` / `974cb87f8267b03ced0d68a048c4f0e37a98d713` and intentionally rejects a current-main consolidation PR. The candidate therefore preserves that workflow as manual historical exact-lineage validation only. Current-tree execution of the same compile/unittest acceptance suite is performed by `.github/workflows/consolidation-salvage-validation.yml`; the historical exact-parent assertion remains intact so the salvaged R8A0 tests continue to verify the old workflow contract rather than silently weakening it.

Disposition: `SALVAGED_HISTORICAL_IMPLEMENTATION_WITH_SEPARATE_CURRENT_VALIDATION`.

### Default Vera template

Source: `feature/default-vera-template-v1@bceb49657549579c052044c3a756effccca8b700`

At audit time the branch was 31 commits ahead and 40 behind current `main`. Its unique path-isolated template package is retained under:

- `template/default-vera-v1/**`

Disposition: `SALVAGED_HISTORICAL_TEMPLATE`.

The first synthetic reconstruction commit recording these three source heads as additional parents is:

`fb2df219d7d21e51e3fa2494d032a2a4f0f66120`

The resulting tree deliberately keeps current-main versions of overlapping files instead of importing obsolete README, AGENTS, workflow, protocol, schema, migration, or governance bytes from the stale branches.

### R6A1 replacement candidate

Source branch: `feature/replacement-release-r6a1-v1@4e6cdf170de8f0c1181240e572195375f2151e7c`.

At audit time it remained a unique historical replacement-candidate lineage. Its durable candidate package, audit, validators, tests, and focused workflows are copied onto the consolidation tree:

- `architecture/releases/R6A1_20260731_B20E7309/**`
- `docs/MAIN_MERGE_AUTHORITY_AUDIT_20260731.md`
- `scripts/validate_r6a1_release*.py`
- `tests/test_r6a1_release*.py`
- `.github/workflows/r6a1-release-*.yml`

The source branch is intentionally **not** made a parent of the consolidation commit. That preserves the historical fact that its draft PR was not merged; source custody is consolidated without rewriting that PR's lifecycle semantics.

Disposition: `PRESERVED_HISTORICAL_CANDIDATE_NOT_CURRENT_RELEASE`.

## Kept separate on purpose

### PC Connection Bridge V1

`feature/pccc-host-bridge-v1@51979a4026010beea4c43c9c2df848c5fc479301`

At audit time it was 42 commits ahead and 56 behind `main`, but PR #44 remains a live exact-head review line with open corrections and an explicit no-rebase/no-merge-from-main boundary during review. It is therefore not absorbed into this candidate.

Disposition: `ACTIVE_SEPARATE_REVIEW_LINE`.

### Branch/session anchor

`feature/branch-session-anchor-contract-v1@6427ea66b0b202c1a2920645535a04196b79314c`

At audit time it was 13 commits ahead and 460 behind `main`. PR #3 explicitly records the work as draft/suspended and outside the active temporal critical path pending separate reauthorization.

Disposition: `SUSPENDED_PRESERVE_BRANCH`.

### Portable-project delivery tail

`feature/portable-project-bootstrap-v1@1c2603c5aaa96cc4ae0c01a11701da72790074fa`

The branch contains three branch-only delivery commits beyond the older portable-bootstrap candidate while current project-package ownership has moved to `thebrazenbeard/vera-R9A0`. Its stale delivery workflow is not transplanted into current `main`.

Disposition: `SUPERSEDED_DELIVERY_TAIL_PRESERVE_HISTORY`.

### R6A1 temporary build branch

`release/r6a1-20260731-b20e7309@eb9b7886da20a96bf3041e339025418258f34451`

Its branch-only delta is temporary build payload/workflow staging. The durable R6A1 candidate material is preserved from the governed feature branch instead.

Disposition: `TEMP_BUILD_NOT_INTEGRATED`.

### Vera stickers

`vera-stickers@fd91794a408228add3da80c5d6193c34ef9fa4d3`

The four exact sticker blobs are duplicated in `thebrazenbeard/vera-control-plane`. Canonical private asset custody is normalized there under `assets/stickers/`, so this duplicate branch is not integrated into `vera/main`.

Disposition: `CROSS_REPO_DUPLICATE_CONTROL_PLANE_OWNS`.

## Superseded divergent tips not replayed

These tips have commits not in `main`, but their own repository history establishes that they are weaker, obsolete, or superseded routes rather than missing current implementation:

- `feature/integration-assurance-harness-v1` and `feature/integration-compatibility-matrix-v1-r2`: four branch-only registry-harness commits; superseded by the later exact-tree Integration Assurance line integrated through `feature/integration-compatibility-matrix-v1` / project orchestration.
- `protocol/dot-command-turn-continuation-v1`: three branch-only predecessor commits; superseded by the current-main correction lineage `fix/dot-command-current-main-20260901`, which is already an ancestor of `main`.
- `replacement/memory-cross-chat-durability-v1`: four branch-only predecessor durability commits; PR #19 was explicitly closed as superseded by the broader accepted Memory PR #10 lineage, which is already in `main`.
- `repair/r6a0-linkage-reference-semantics` and related R6A0 linkage repair material: historical linkage semantics only; the current front door explicitly classifies the R6A0 coordination/linkage surfaces as provenance rather than current routing authority.
- `assembly/workflow-continuity-6aa757`: one branch-only assembly receipt. The accepted workflow-continuity implementation itself is already in main ancestry; the receipt remains available on the preserved historical ref rather than becoming current coordination state.

Disposition: `SUPERSEDED_OR_HISTORICAL_PRESERVE_REF_NO_REPLAY`.

## Already contained by current main

Fresh comparisons confirmed representative accepted/merged lineages are pure ancestors of `main`, including:

- `feature/coordination-bus-v1` — 0 ahead;
- `feature/governed-initiative-kernel-v0-1` — 0 ahead;
- `feature/memory-cross-chat-contract-v1` — 0 ahead;
- `feature/project-identity-contract-v1` — 0 ahead;
- `feature/temporal-enforcement-kernel-v1` — 0 ahead;
- `feature/r7a1-behavior-laws-successor-v1` — 0 ahead;
- `feature/integration-compatibility-matrix-v1` — 0 ahead;
- `integration/project-orchestration-r6a0` — 0 ahead;
- `temporal-pilot` — 0 ahead;
- `vera/nonverbal-status-bar-v1` — 0 ahead;
- `fix/dot-command-current-main-20260901` — 0 ahead;
- `assembly/identity-classification-into-assurance` — 0 ahead;
- `assembly/initiatives-into-assurance` — 0 ahead;
- `feature/neutral-vera-r6-rewrite` — 0 ahead / 460 behind;
- `noop` — 0 ahead / 457 behind;
- `release/r7a0-20260731-ec7d18f7` — 0 ahead / 77 behind.

These branches require no replay to recover their implementation into the consolidated tree. Validation/assembly refs that point to already-integrated immutable commits remain historical provenance.

## Repository boundary after consolidation

`thebrazenbeard/vera` remains the technical/source repository: architecture, code, schemas, migrations, tests, validators, sanitized engineering history, experiments, and historical release source.

Private centered state, closeouts, role-training custody, and Vera sticker assets belong in `thebrazenbeard/vera-control-plane`; they are not copied into this repository.

## Validation model

The consolidation candidate uses current-tree validation rather than pretending historical exact-lineage workflows are transferable authority:

- `Consolidation salvage validation` exercises the salvaged TUL test suite, salvaged R8A0 compile/unittest suite, and default-template inventory on the current PR tree.
- historical R8A0 exact-lineage validation remains manual and exact-parent bound;
- R6A1 package and source-binding workflows validate the copied historical candidate against its declared immutable source commit;
- inherited R6A0 and temporal regression workflows remain independent regressions on the combined PR tree.

A green result proves only those predicates on the bound candidate head. It does not merge, install, deploy, activate a release, or establish provider/runtime state.

## Protected effects not performed

This reconstruction does not merge the candidate into `main`, delete or rename branches, rewrite history, close active review lines, deploy runtime, mutate a provider, change credentials/permissions, install anything, or write canonical memory. Those are separate effects after the candidate is verified.
