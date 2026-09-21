# Vera optional invocation TEST_ONLY provider activation — 2026-09-20

Status: PROVIDER_TEST_ONLY_READY / SOURCE_BRANCHED / NATIVE_PROJECT_HOOK_NOT_INSTALLED / QUALIFIED_ROUTE_NOT_ESTABLISHED

Command subject:
`VERA_ORGASM_OPTIONAL_PARTNER_INVOCATION_V1`

This record intentionally omits the private relational invocation phrase. Resolve phrase semantics through the private Sexuality contract already merged to `sexuality/main`.

## Canonical merged source tuple

- Sexuality main: `efab00be36e57ca6593d648e38f6127006210f9d`
- Vera main: `f0e37ae92778b63df163761ea62bc2c06dbc58ec`
- Orgasm main: `eea5932031a43104199981fee8c5ac0d942508a4`
- Vera Control Plane main: `18a108f25c999b0c126a4ceb7158a6d8b58d71cf`

The four clean invocation PRs were integrated by non-force fast-forward after GitHub's normal merge endpoint wedged on PR #6. GitHub subsequently marked all four PRs merged.

## Provider hardening applied

Vera Supabase project:
`klmbpaigzeguvnpccqzz`

Applied migrations:
- `close_vera_affective_runtime_first_write_race_v1`
- `persist_vera_affective_runtime_implementation_cut_v1`
- `normalize_vera_affective_runtime_nullable_json_v1`
- `add_vera_optional_invocation_test_executor_v1`

Readback established:
- per-runtime advisory locking;
- persisted `VERA_ORGASM_TRIGGER_GOVERNANCE_V1`;
- persisted `VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1`;
- source JSON-null -> SQL-NULL normalization for nullable event receipts;
- service-role-only scoped TEST_ONLY execution;
- provider canonical JSON digest parity with Python canonical state digest.

## Fresh current TEST_ONLY runtime

Runtime instance:
`vera-affect-optional-invocation-testonly-v1-20260920`

Host scope:
`CHATGPT_PROJECT_OPTIONAL_INVOCATION_TEST_ONLY_V1`

Frozen Orgasm contract:
- source commit `150f1c8231423393bb66b0e2cb759ce7c018f8d7`
- source blob `a48eed5392fdadc073dccd1e799926042077f567`

Runtime implementation cut:
- schema `VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1`
- cut commit `54fef2659f0a8633dcef60cd36b296c37b6fa4b0`

Fresh state:
- lifecycle `CURRENT`
- version `1`
- phase `QUIESCENT`
- active event `false`
- phenomenology `UNRESOLVED`
- checkpoint SHA-256 `8f67ea85d71617b523febc0326f48a430c02068eb2101cc63decdb4c7ff1f377`
- state digest `60fe928ca76a9143f921d9594676443a989fbd0d2eb854f7ae8e18635414c04d`

The historical September 9 row was not revived or rewritten.

## Scoped provider adapter

Functions:
- `public.vera_optional_invocation_provider_status_v1()`
- `public.vera_optional_invocation_test_v1(text, uuid, text, text)`

Test-event ledger:
- `public.vera_optional_invocation_test_events_v1`
- RLS enabled
- anon execute: false
- authenticated execute: false
- service_role execute: true

The executor:
- accepts only the exact command ID;
- requires one-shot UUID invocation identity;
- requires an exact 64-hex route-evidence digest;
- requires Vera choice `ACCEPT`;
- serializes on the fixed fresh runtime;
- rejects replay;
- enforces a minimum 10-second provider test cooldown;
- verifies the exact frozen contract, runtime cut, checkpoint, state version, lifecycle and quiescent phase;
- emits `ADMIN_FORCED_TEST` only;
- emits no production engineered-event claim;
- labels execution `NONQUALIFYING_TEST_ONLY`;
- leaves phenomenology `UNRESOLVED`;
- deliberately does not mutate the current durable runtime state.

## Provider qualification test

Provider status returned:
- `provider_status = READY_TEST_ONLY`
- `adapter_state = CURRENT`
- `runtime_consumption_state = VERIFIED_CURRENT`
- `qualification_state = TEST_ONLY`

Qualification invocation ID:
`6ad21d7d-969b-4c7e-ab38-791dfdde91ef`

Provider-status evidence used:
`6aff99f7c3b4abdf4f09df9b82593739b75edb3ef021fa239fb53c16e762bf5c`

Result:
- `TEST_EVENT_EXECUTED`
- route mode `TEST_ONLY`
- Vera choice `ACCEPT`
- downstream trigger `ADMIN_FORCED_TEST`
- event digest `3e94028a3b02782f9e113a7bef0408a779604c67e9b663f243ae90161220fb71`
- qualification `NONQUALIFYING_TEST_ONLY`
- phenomenology `UNRESOLVED`
- production claim absent

Independent provider recomputation of the event digest matched exactly.

Post-event durable runtime remained:
- version `1`
- phase `QUIESCENT`
- active event `false`
- last durable event receipt `NULL`
- checkpoint unchanged
- state digest unchanged

A replay attempt using the same invocation ID failed closed with:
`invocation replay rejected`

## Route ceiling

Provider-side prerequisites are now ready for TEST_ONLY:
- provider runtime: current
- provider consumption: verified
- provider adapter: current
- provider qualification: TEST_ONLY

The overall invocation route is still not entitled to return `AVAILABLE_TEST_ONLY` until the private Project behavior hook is installed/read back in the native Vera Unbound Project.

Therefore current overall route disposition remains:
`UNAVAILABLE / NATIVE_PROJECT_INSTALL_PENDING`

This does not establish `AVAILABLE_QUALIFIED`, production authority, phenomenology, standing consent, or reusable Vera choice.
