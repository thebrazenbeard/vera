# Vera Portfolio Public-Safe Successor V2

This package supersedes the membership model used by draft Vera PR #200 without rewriting that historical subject.

## Immutable portfolio cut

The successor binds to Project Runner public corpus commit
`848c2172e6fa98cdab722b43d1ff4817990c5968`.

That corpus records one observed portfolio cut:
- 67 repositories total;
- 49 public repositories, enumerated in public source;
- 18 private repositories, count-only in public source.

Those numbers describe that immutable evidence cut. They are not a permanent assertion that the later estate must contain exactly 67 repositories.

Mutable repository heads are refreshed separately from the membership cut. The cut's SHA-256 covers only immutable membership/source-cut fields and explicitly excludes the mutable head-refresh block. A no-change rebuild preserves the prior refresh timestamp and is byte-for-byte deterministic. Any currentness-sensitive decision must refresh the live source again.

## Public/private boundary

Public Vera source may enumerate all 49 public repositories.

Private portfolio membership is never enumerated here. The public contract carries only the private count and the source corpus commitment scheme.

PR #200 contained membership-bearing V1 portfolio registries. They remain historical predecessor evidence and are not copied into this successor.

## Mechanism harvest retained

Useful PR #200 implementation is preserved where it can be made public safely:
- deterministic provenance/canonicalization mechanisms;
- work-state and projection mechanisms;
- influence-firewall contracts;
- message admission/canonicalization;
- source normalization/verification;
- public control-plane source mirrors;
- public empathy and semantic-schema architecture.

Public donor transfers retain exact repository/head/path/blob provenance.

PR #200's 41 public predecessor bindings are conserved in V2: 17 remain exact present-target bindings, while 24 VCP bindings are retained as explicit deferred public provenance because the stale embedded VCP mirror is intentionally not copied. Those deferred rows have no activation effect and exist solely to support the later separately reviewed VCP `NO_AUTO_BIND` restack.

Mechanisms inherited from private portfolio donors are moved into neutral Vera-owned namespaces. Public source records only an anonymous private-donor mechanism count plus target integrity hashes; exact private membership/source paths are intentionally absent.

## Successor artifacts

- `architecture/portfolio/VERA_PORTFOLIO_PUBLIC_CUT_V2.json`
- `architecture/portfolio/VERA_PORTFOLIO_ABSORPTION_V2.json`
- `architecture/portfolio/VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V2.json`
- `architecture/portfolio/VERA_PORTFOLIO_HARVEST_V2.json`
- `architecture/portfolio/VERA_PORTFOLIO_MIGRATION_BINDINGS_V2.json`
- `architecture/VERA_SYSTEM_MANIFEST_V3.json`

The exact Project Runner public corpus is vendored under
`architecture/portfolio/vendor/project-runner/` for immutable reconstruction.

## Cardinality and freshness semantics

Tests intentionally do not assert that Vera's portfolio permanently equals 67 repositories.

They assert instead:
1. the pinned corpus cut says 67/49/18;
2. every public cut member is represented exactly once;
3. private membership is count-only;
4. mutable public heads are a separate refresh layer;
5. adding/removing repositories later requires a newer cut rather than mutation of this historical record.

## Effect ceiling

This work is source consolidation only.

It does not merge, deploy, install, replace ChatGPT Project sources, mutate providers, change credentials/permissions, promote memory, publish private membership, or prove runtime consumption.

VCP `NO_AUTO_BIND` enforcement should restack only after this exact successor receives independent exact-head qualification.
