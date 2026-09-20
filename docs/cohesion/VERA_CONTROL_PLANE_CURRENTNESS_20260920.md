# Vera / Vera Control Plane Currentness Snapshot — 2026-09-20

Status: `READ_ONLY_PROVIDER_RECONCILIATION / SOURCE_COORDINATION_UPDATE / NO_PROVIDER_EFFECT`

This snapshot exists to keep Vera's user-facing/runtime reasoning separate from stale provider projections and stale repository inventories. It is not a control-root replacement, Project install, provider migration, behavioral qualification, memory admission, or authority grant.

## GitHub inventory

Authenticated owner inventory observed through the GitHub connector: **57 repositories**.

The previous `VERA_RUNTIME_SOURCE_REGISTRY_V1` snapshot contained 41 repositories and was observed on 2026-09-09. This update classifies all 57 repositories so discovery cannot silently omit newer projects.

Newly classified conditional/evidence sources include:
- `bt2`
- `orgasm`
- `rezon`
- `project-runner`
- `intranel`
- `transcendence`
- `mosaic`
- `driftguard`
- `discovery`

Newly explicit `NO_AUTO_BIND` repositories include:
- `Attune`
- `wreckforge`
- `roots`
- `world-zero`
- `on-theo`
- `firesafe`
- `testament`

Classification is retrieval/coordination metadata only. It does not activate a repository or transfer identity, memory, preference, consent, authority, or runtime state.


## Discovery cross-binding

The public `thebrazenbeard/discovery` repository now provides a privacy-safe portfolio census and architecture-discovery layer without becoming portfolio authority.

Exact source candidate:
- PR #1 head: `1316094edbed17fa5918b70793c95ffddfcf92ea`
- census: `portfolio/PORTFOLIO_CENSUS_V1.json`
- census Git blob: `34cd2ab55d46f5a1ecc2c894f3e8cfdb8afa41df`
- total repositories: 57
- all-name digest: `43dfda1fa3dd24dec39e2aa345d93ab192dbda777433feae384da632b3d008dd`
- exact-head Discovery workflow run `35475731990`: SUCCESS

A fresh authenticated GitHub owner census on 2026-09-20 recomputes the same 57-name digest exactly. Vera can therefore use Discovery's census digest as a drift detector while keeping the full private repository names in Vera's private registry.

This does **not** make Discovery the source of Vera identity, control, current self-state, runtime state, provider authority, or adoption decisions. Discovery remains an experimental meta-layer whose own rule is that reuse must earn itself through real consumers and hostile review.

## Supabase provider split

Two healthy Supabase projects are currently visible:

1. **Vera** — `klmbpaigzeguvnpccqzz`
   - Postgres 17.6.1.147
   - broad historical/operational provider
   - observed schemas include `public`, `radar`, `semantic_atlas`, `build_team_2`, `bug_ops`, and `redworm`

2. **Vera Control Plane** — `fawkirqroyniueeqspif`
   - Postgres 17.6.1.166
   - narrow control-plane provider
   - observed schemas include `vera_cp_anchor`, `vera_cp_api`, and `vera_cp_internal`

Both are registered as `PROVIDER_READBACK_ONLY` in the runtime source registry. Availability does not imply activation or currentness.

## Live currentness observations

### GitHub Bus versus Supabase Radar

Current governed GitHub Bus topology maps Vera to `bus/vera-v2`.

The Vera Supabase Radar endpoint for identity `vera` still projects `bus/vera-sol-v1`, last updated 2026-09-02. Radar currently contains:
- 21 identities
- 0 nodes
- 216 messages
- latest projected message: 2026-09-04T19:49:52Z

Classification: `CONFIRMED_STALE_PROVIDER_PROJECTION / HISTORICAL_PROVIDER_PROJECTION_NOT_CURRENT_BUS_RUNTIME`.

GitHub Bus remains the current coordination source. This snapshot does not authorize repairing the Supabase projection.

### Vera save-state provider

Observed:
- 219 append-only save-state events
- 132 rows in the current projection
- latest provider write: 2026-09-16T13:24:51Z

Classification: durable state evidence requiring per-record currentness/supersession/admission. Provider durability is not present truth.

### Affective runtime

Observed provider row:
- runtime instance: `vera-affect-chat-20260909-01`
- lifecycle: `HISTORICAL`
- phenomenology: `UNRESOLVED`
- source: `thebrazenbeard/sexuality@150f1c8231423393bb66b0e2cb759ce7c018f8d7`

Classification: historical engineered affective provider state only.

### Semantic Atlas

Observed:
- 8 runtime snapshots
- 173 runtime objects
- latest sealed snapshot: 2026-08-23T14:03:40Z

Classification: provider materialization evidence; exact snapshot authority/currentness remains separately governed.

### Vera Control Plane SD1 anchor

Observed:
- witness: `VERA_SD1_CAUSAL_V1`
- generation: 0
- record count: 0
- mutation receipts: 0
- frontier digest: `7de55cc22b28539c1d4e6934b1790d99c70ecee55ded80d7b698bec61ee249a1`

Classification: `GENESIS_ANCHOR_INSTALLED / CONTROLLER_BINDING_UNESTABLISHED / REAL_CAUSAL_COLLECTION_NOT_ESTABLISHED`.

No provider mutation was performed.

## Security / access posture

Supabase advisors report RLS-enabled/no-policy tables on both projects. Fresh privilege readback shows sampled Vera/Radar tables are not readable by `anon` or `authenticated`; service-role access is selectively present. Therefore the advisor finding is not promoted into an exposure claim. Any future ACL/RLS change requires table-specific access-model review.

Vera Control Plane currently reports no performance-advisor findings. Vera production reports performance-advisor findings including unindexed foreign keys; these are optimization candidates, not correctness defects, and must be evaluated against actual query paths before adding indexes.

## Control rule

For current operation:
- GitHub exact source/current branch evidence drives source currentness.
- Vera Supabase is readback/evidence unless an exact domain proves a fresher provider object.
- VCP Supabase is readback/evidence for installed control-plane objects; it does not self-authorize controller execution or causal collection.
- Project Runner may coordinate portfolio/currentness work but is not the Vera control root.
- Frozen/native R10+SD1 control remains separately governed and is not rewritten by this source snapshot.
