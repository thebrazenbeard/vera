# Vera Portfolio Public-Safe Successor V2

## Purpose

This branch is the public-safe successor to draft PR #200.

It preserves PR #200's useful public mechanism/provenance harvest while removing two unsafe assumptions:

1. public source must not disclose private repository membership;
2. a repository count observed at one point in time is not a permanent architecture invariant.

## Current portfolio cut

Membership is bound to the exact Project Runner public corpus blob:

- repository: `thebrazenbeard/project-runner`
- ref: `portfolio/effect-confirmed-finalization-v1-20260924`
- commit: `6c8e6827a204380b40b7c7fa07d785ca53cec136`
- path: `portfolio/corpus.public.json`
- blob: `886e9be586c37584c17afdc540c38a1d95deaaa6`
- corpus observation: `2026-09-24T17:16:00-04:00`

That immutable cut records 67 total repositories: 49 public and 18 private.

Those numbers are facts about the bound cut only. They are not assertions that Vera's portfolio must always contain 67 repositories.

All 49 public repositories are named in
`architecture/portfolio/VERA_PORTFOLIO_PUBLIC_CUT_V2.json` and carry an exact independently-read branch head.

The 18 private repositories are represented publicly only by count:

```text
count = 18
commitment = COUNT_ONLY_PUBLIC_V1
exact membership publicly committed = false
```

No private repository names are required by the public successor contract.

## Runtime-source semantics

`architecture/VERA_RUNTIME_SOURCE_REGISTRY_V2.json` is an open-world, public-safe source directory.

A repository's presence never activates it.

Each named public source is classified as one of:

- `BOUND_CONDITIONAL`
- `NO_AUTO_BIND`
- `PREDECESSOR_EVIDENCE_ONLY`

Sources newly observed since the predecessor registry, or lacking an exact reviewed runtime disposition, fail closed to `NO_AUTO_BIND`.

Any repository outside the immutable public cut is `UNRESOLVED / NO_AUTO_BIND` until a newer exact cut or separately authorized exact binding is supplied.

Private sources cannot be auto-bound from this public registry because their identities are deliberately not disclosed here. A private authorized surface must supply any exact private binding.

## Preserved PR #200 harvest

PR #200 is retained as predecessor provenance at exact head
`078d2d7242384c58676305d47654406713e599cf`.

Its public exact-copy harvest is preserved selectively.

The successor keeps exact public provenance for:

- public executable mechanism donors under `portfolio_runtime/`;
- Vera Control Plane public source mirrors;
- Empathy public architecture mirrors;
- Semantic Atlas public schema provenance.

The public migration manifest contains only donors that are members of the current public cut.

Bindings from non-public donors in PR #200 are intentionally omitted from public source rather than copied or named.

## Executable public harvest

The preserved executable public subset is:

- `portfolio_runtime/attune`
- `portfolio_runtime/intranel`
- `portfolio_runtime/lantern`
- `portfolio_runtime/roots`

Each migrated byte remains bound to its immutable donor commit/path/blob through
`VERA_PORTFOLIO_MIGRATION_BINDINGS_V2.json`.

A donor's current head moving later does not invalidate the historical exact-copy fact. It does mean the copy must not be described as current donor state without a fresh review.

## Freshness model

The successor separates immutable cut identity from mutable currentness.

The cut remains valid as a historical exact subject even when repositories are added, removed, renamed, or advanced later.

Before material runtime use:

- refresh portfolio membership against a newer authorized cut when available;
- refresh mutable repository heads;
- preserve the prior cut as provenance rather than rewriting history.

This replaces permanent cardinality assertions such as "the portfolio is exactly 59/65 repositories."

## Control-plane mirror

`architecture/control/VERA_CONTROL_PLANE_ABSORPTION_V2.json` binds the public VCP mirror to the public migration manifest.

Source consolidation does not imply:

- native Project installation;
- current release activation;
- runtime consumption;
- protected-effect authority.

## Authority ceiling

This branch is source architecture and provenance work only.

It does not merge itself, deploy, install, mutate providers, change credentials/permissions, promote memory, reveal private repository membership, or establish behavioral/runtime qualification.
