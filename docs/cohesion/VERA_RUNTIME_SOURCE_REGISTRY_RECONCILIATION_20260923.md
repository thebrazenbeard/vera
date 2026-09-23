# Vera Runtime Source Registry Reconciliation — 2026-09-23

Status: **SOURCE CANDIDATE / NOT INSTALLED / NOT RUNTIME QUALIFIED**

## Purpose

Reconcile `architecture/VERA_RUNTIME_SOURCE_REGISTRY_V1.json` from its stale
41-repository owner snapshot to the canonical 59-repository Discovery + Roots
portfolio subject, while preserving Vera-specific runtime-use semantics and
correcting the historical Vera Bus lane assumption.

This reconciliation does not install, activate, merge, deploy, or provider-write
anything.

## Exact portfolio subject

Discovery:

- repository: `thebrazenbeard/discovery`
- main subject read: `2881a94c7eb3c83a34b0c00bab739b41c1d99b6d`
- file: `architecture/DISCOVERY_LIVE_PORTFOLIO_MAP_V2.json`
- blob: `71b9f8deaf1079d5078b19e5bbddb743fd636437`
- classified repository count: **59**
- partition: **41 BOUND_CONDITIONAL + 1 PREDECESSOR_EVIDENCE_ONLY + 17 NO_AUTO_BIND**

Roots:

- repository: `thebrazenbeard/roots`
- main subject read: `a6994b415336bc179a41aad0ac9eec403d60f93c`
- file: `portfolio/VERA_PORTFOLIO_LINEAGE_RECEIPT_V1.json`
- blob: `ccac62eac08012269fec46669bce981b96a0f41d`

Roots preserves, rather than erases, the material lineage constraints:

- `vera-R9A0 -> vera-control-plane` control-line supersession is established;
- `build-team-2.0` and `bt2` remain distinct subjects;
- HC-template canonicality remains unresolved among `self`, `hc-brain`, and
  `bt2`;
- `orgasm` remains an orientation hub rather than a replacement for the
  frozen sexuality contract or Vera runtime source;
- `voss` repository state is active/review-only rather than archived;
- generic workflow-template byte overlap does not establish lineage;
- Redworm historical provider authorship remains unresolved.

## Registry reconciliation

The Vera registry now carries the exact 59-repository owner snapshot and the
same Discovery partition.

Important corrections include:

- `voss` moves from stale NO_AUTO_BIND/archive labeling to a bounded
  `AUDIT_HOSTILE_REVIEW_SOURCE` role;
- `vera-apk` and `vera-habitat` move to NO_AUTO_BIND because the canonical
  Discovery cut classifies them as empty stubs;
- `bt2`, `firesafe`, and `wreckforge` are added to NO_AUTO_BIND;
- the remaining newly observed repositories are registered as bounded sources
  with Vera-specific authority ceilings;
- `WorkBridgeMCP` is registered only as a workstation-bridge candidate source,
  not as installation/runtime/effect proof.

The registry intentionally preserves its existing domain-specific activation
modes and authority ceilings where they do not conflict with Discovery/Roots.
Discovery owns the portfolio classification subject; Vera owns the narrower
runtime-use semantics.

## Bus route correction

Current Bus topology source:

- repository: `thebrazenbeard/chat-communication-bus`
- main: `f9179bd1426bf90c23ab6a4d14d5a8e9b39c66d2`
- file: `architecture/contracts/RADAR_TOPOLOGY_V1.json`
- blob: `69e505031d4e53dcb853578dac23817649af1918`

The topology records Vera's active current writer lane as:

`bus/vera-v2`

The historical/provider lane:

`bus/vera-sol-v1`

is preserved as provenance and as a stale provider projection conflict. It is
**not** current route authority.

No provider repair is performed here. Updating a Supabase route projection is a
separate protected effect requiring separate authority and fresh readback.

## Post-cut drift

A repository named `thebrazenbeard/meso-crct` is visible in the current account
inventory but is not a member of the exact canonical 59-repository Discovery
cut bound by this reconciliation.

It is therefore recorded as:

`OUTSIDE_CANONICAL_59_CUT / NO_SILENT_PROMOTION`

This is not a permanent rejection. It requires a later Discovery + Roots refresh
before admission into a successor portfolio cut.

## Claim ceiling

This reconciliation can establish source-level consistency between:

- the canonical 59-repository Discovery classification;
- the current Roots lineage receipt;
- Vera's runtime source directory; and
- the current Bus topology route value.

It does not establish:

- native Project installation;
- runtime consumption of all 59 repositories;
- provider route repair;
- currentness of every repository beyond the exact cited cut;
- resolution of the HC-template conflict;
- Redworm historical authorship;
- deployment or protected external effects.

VCP consumption and portfolio-wide hostile qualification are separate downstream
subjects.
