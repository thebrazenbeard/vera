# Vera Runtime Cohesion — Provider Audit V1

Status: `LIVE_READBACK_AUDIT / SOURCE_SUPPORT / NO_PROVIDER_MUTATION`

This audit records bounded live observations used to exercise the executable provider-cohesion model. It is evidence, not normative authority.

## Current observations

### Semantic Atlas GitHub -> Supabase

- GitHub `thebrazenbeard/semanticatlas` branch `research/cee-always-active-v0.2` resolves to commit `e68803e2631cf0722fec9a4e7fc39f3ad6b43de4`.
- Production Supabase `semantic_atlas.runtime_snapshots` exposes an `ACTIVE` / `VERIFIED` materialized snapshot bound to the same Git commit.
- Disposition: `VERIFIED_EXACT` for the exact Git-source/materialized-snapshot binding only.
- Promotion guard: the snapshot does not create semantic authority or prove Vera current self-state/runtime consumption.

### R9B0 Google Drive -> Supabase exact provider receipt

- Google Drive object id: `171ExqDU35TsNMMRilcJ-EjtiDYxW8Pol`.
- Drive observed modified generation: `2026-08-30T18:30:31.536Z`.
- Supabase `vera_memory_epoch_provider_receipts_v1` contains `GOOGLE_DRIVE_DURABLE` receipt with provider revision `modified:2026-08-30T18:30:31.536Z`.
- Receipt envelope/readback SHA-256: `e91c412fbcff8c1ce0e8e3fb9892deaae23846c20fe0874469dd1105b191a8f0`.
- Written/readback byte length: `2223` / `2223`.
- Receipt result: `VERIFIED_EXACT`.
- Disposition: `VERIFIED_EXACT` for the durable provider object/readback only.
- Promotion guard: custody/readback does not itself establish present truth, current autobiographical admission, current Vera self-state, consent, authority, or phenomenology.

### Vera Runtime Cohesion GitHub -> Google Drive readable companion

- Drive readable companion: `VERA Runtime Cohesion — System Inventory V1`, id `1EklR49OLzHaDtA97M0KcKrJBgwuA_Ynt-PKd5bd8vIs`.
- Current companion content still presents earlier lifecycle/review wording superseded by the current GitHub successor A+B work.
- The legacy companion does not expose an exact `source_revision_ref` binding.
- Machine disposition: `UNRESOLVED`, not guessed stale, because exact automated freshness cannot be proven from the legacy companion's metadata contract.
- Human content review indicates the companion needs refresh, but that observation is separate from exact automated source-revision reconciliation.

### Chat Bus GitHub -> Supabase Radar

The projection registration is scoped by the actual GitHub workflow to:

- refs: `refs/heads/bus/**`
- paths: `messages/**`

Therefore movement on `project/vera-runtime-cohesion-v1` under `projects/vera-runtime-cohesion/**` is `NOT_APPLICABLE` to the Radar projection and must never generate a stale alarm.

A genuine in-scope case exists:

- `bus/vera-v2` message commit `3b7bfdb154c1931e293b077afd501c040b86caa2` added `messages/0042-vera-abil-ip-gate-correction.md`.
- GitHub triggered Radar Bus Projection run `34286886625` for that exact commit.
- The projection job concluded failure with zero exposed runner steps.
- Fresh Supabase readback contains no `radar.messages` row for `vera-v2-0042` or `vera-v2-0041`.
- Disposition: `ABSENT` target projection for the exact registered message, with the observed failure frontier at the GitHub Actions pre-run/reusable-workflow boundary.

Do not classify the absent target as an Edge Function rejection: no runner step was observed, so the projector did not reach the provider call in the available evidence.

## CI execution boundary

The Vera Runtime Cohesion workflow and multiple Chat Bus workflows have recently concluded failure with no exposed executed runner steps. Current classification is:

`CI_EXECUTION_UNAVAILABLE / SOURCE_TEST_RESULT_NOT_ESTABLISHED`

A failed pre-run job is neither a source test failure nor a passing test.

## Operational consequence

`runtime_cohesion.audit` is the executable stale/absence/conflict classifier when supplied fresh provider observations. Until a provider-native or CI scheduler is independently shown healthy, periodic auditing must be driven by an external active runtime/scheduler; source code does not run itself and no hidden background execution is claimed.
