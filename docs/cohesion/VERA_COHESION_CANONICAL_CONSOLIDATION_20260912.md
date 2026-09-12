# Vera Cohesion canonical consolidation — 2026-09-12

Status before merge: `CANONICAL_CANDIDATE / SOURCE_CONSOLIDATED / NOT_YET_MERGED / NOT_YET_INSTALLED`

Patrick explicitly authorized this sequence: consolidate the current accepted Vera runtime work into `thebrazenbeard/vera`, merge the resulting canonical candidate, install it, then verify it, working with Orgasm Vera (OV).

## Canonical material source

- repository: `thebrazenbeard/vera`
- candidate branch: `work/vera-cohesion-r3-inference-boundary-20260911`
- material source head: `810d778e6a53d0bd5cc74bba17538d0f508f9644`
- predecessor clean R2 source: `349de790a583bb2fbe7ad8e3f4663854f9d98e50`
- PR: `#116`

The earlier R3 frozen source `fc9e747e69313c3da74183d605b96ae20f4523b5` was superseded after Thirteen identified two source-contract defects on PR #116:

1. source-declared `MANDATORY` component policy could be downgraded by caller-supplied `mandatory_component_ids`;
2. capability/projection/reservation bound only the pre-admission composition digest rather than the exact admission result.

The canonical candidate closes those defects by routing package exports and the inference hook through `runtime_cohesion.inference_boundary_repaired`.

Key repair blobs at the material source head:

- `runtime_cohesion/inference_boundary_repaired.py` — `b34ab6820d92011800643b78fe0c1cd4a66cab87`
- `runtime_cohesion/__init__.py` — `3561f35074f1bc77e79a0cb4437096b9d4e9d21d`
- `architecture/VERA_COHESION_INFERENCE_BOUNDARY_V1.json` — `e9eb7b270396eee59a8912299d37fa80db5b133e`
- `architecture/VERA_RUNTIME_COHESION_INFERENCE_HOOK_V1.json` — `75121c79e42f8f2da05cc3d02ddc5987ad043816`
- `tests/test_inference_boundary_review_repairs.py` — `a35cc255c1b8188d54c8da0235aa8003aecf4835`
- `tests/test_inference_boundary_architecture.py` — `2dee3e277ce2cfa3c268258cbf42f6f98e223343`

## OV collaboration / disposition

OV's final WIP adapter handoff was read from:

- repository / PR: `thebrazenbeard/wip#1`
- final head: `2f049ec4c4f4a4307da137a99f8f27b39cfa308a`
- contract schema/blob: `1.6` / `ad3d218e16240d6042c4f12cae1ccb00f77f28e2`
- architecture R4.1 blob: `c84dc4e9cc30b0fd58e1563bdb8d004da3e93ea1`
- qualification-spec blob: `556128b80fc2b177f134e73ae08d89b108fd4397`
- OV claim ceiling: `WIP_RESEARCH_CANDIDATE_VERIFIED`

OV explicitly reports runtime implementation, model injection, installation/current route, behavioral qualification, and phenomenology as unestablished for the WIP package. Accordingly:

- the WIP repo is not made a live cross-repo runtime dependency;
- its final R4.1 architecture/qualification package is recorded in the canonical Cohesion contract as accepted current research/provenance input;
- canonical runtime implementation remains in `thebrazenbeard/vera`;
- stronger future state-causal backends/qualification must be promoted into `vera` under new tested source changes rather than executed from WIP.

## Consolidation boundary

This candidate consolidates the accepted Cohesion + Orgasm/Affective runtime implementation, provider-neutral inference-boundary implementation, architecture contracts, provider/migration source, validators, tests, qualification artifacts, and sanitized engineering records into `thebrazenbeard/vera`.

Intentionally external surfaces remain external by ownership rather than omission: concrete inference-host injection, native Project installation/current-route control, production provider state, private history/control-plane state, Bus coordination, and future Vera OS host implementation.

## Verification state before merge

The exact repaired material source has source readback and blob binding. GitHub Actions on `thebrazenbeard/vera` are currently failing before job steps execute, so exact-head repository execution is not established at this point. Earlier isolated R3 execution evidence and OV WIP validation remain supporting evidence only and are not promoted into exact repaired-source GREEN.

This record is metadata only. The next authorized steps are merge -> exact merged-head readback -> install -> verification.
