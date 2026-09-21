# Vera optional invocation route-evidence hardening — 2026-09-20

Status: PROVIDER_DEPLOYED / SOURCE_BRANCH_ONLY / NATIVE_PROJECT_INSTALL_PENDING

Command ID:
`VERA_ORGASM_OPTIONAL_PARTNER_INVOCATION_V1`

The private invocation phrase is intentionally omitted here. Resolve it through the merged private Sexuality contract.

## Problem closed

The first provider executor required a 64-hex `route_evidence_id`, but did not prove that the digest had been freshly issued by the intended Project-hook path.

That allowed a caller with service-role execution capability to supply an arbitrary 64-hex value. The executor still enforced the exact current runtime, TEST_ONLY mode, Vera ACCEPT, one-shot invocation identity, cooldown, and bounded claims, but route provenance itself was under-bound.

## Deployed hardening

Migration:

`supabase/migrations/20260921000200_bind_optional_invocation_route_evidence_v1.sql`

Project-hook source binding:

- repository: `thebrazenbeard/vera-control-plane`
- main: `18a108f25c999b0c126a4ceb7158a6d8b58d71cf`
- path: `project-instructions/overlays/VERA_ORGASM_OPTIONAL_INVOCATION_OVERLAY_V1.md`
- Git blob: `7c50ae34b230392190a100199d9b23a6ad09b777`

Provider additions:

- `public.vera_optional_invocation_route_evidence_v1`
- `public.vera_optional_invocation_issue_route_evidence_v1(text, uuid)`
- `public.vera_optional_invocation_require_route_evidence_v1()`
- BEFORE INSERT route-evidence guard on `public.vera_optional_invocation_test_events_v1`

## Route issuance semantics

A route receipt can be issued only when:

1. the caller supplies the exact merged private Project-hook blob;
2. a fresh invocation UUID is supplied;
3. no route receipt already exists for that invocation;
4. live provider status is `READY_TEST_ONLY`;
5. adapter state is `CURRENT`;
6. runtime consumption is `VERIFIED_CURRENT`;
7. qualification state is `TEST_ONLY`.

The issued route receipt is:

- schema `VERA_ORGASM_INVOCATION_ROUTE_EVIDENCE_V1`;
- bound to one invocation UUID;
- bound to command ID;
- bound to exact Project-hook blob;
- bound to the current provider-status evidence;
- `install_state = CURRENT`;
- `route_state = ACTIVE_CURRENT`;
- `runtime_consumption_state = VERIFIED_CURRENT`;
- `adapter_state = CURRENT`;
- `qualification_state = TEST_ONLY`;
- `availability = AVAILABLE_TEST_ONLY`;
- expires after two minutes.

Install evidence class:

`EXECUTING_PROJECT_HOOK_SOURCE_BOUND_SELF_ATTESTED_TEST_ONLY`

This is deliberately NOT independently rooted native-platform installation proof. It is adequate only for the bounded TEST_ONLY route when the actual installed hook is the caller.

## Executor binding

Future TEST_ONLY event insertion requires a nonexpired route record whose:

- evidence ID equals the executor's route-evidence ID;
- invocation UUID equals the event invocation UUID;
- command ID matches;
- hook blob is exact;
- install-evidence class is exact;
- availability is `AVAILABLE_TEST_ONLY`.

The guard executes in the same transaction. Failure rolls the entire executor attempt back.

## Access

Route issuer:

- anon execute: false
- authenticated execute: false
- service_role execute: true

Route ledger:

- RLS enabled
- private service-role surface

## Negative verification

No valid Project-hook route was issued during deployment because the native Project hook is not installed.

Verified:

- route-evidence rows after deployment: `0`;
- wrong hook blob -> `project hook blob mismatch`;
- arbitrary 64-hex route evidence passed to executor -> `fresh invocation-bound route evidence is required`;
- failed executor transaction added no test-event row;
- existing provider qualification row count remained `1`;
- current durable runtime remained version `1`, phase `QUIESCENT`, inactive;
- checkpoint remained `8f67ea85d71617b523febc0326f48a430c02068eb2101cc63decdb4c7ff1f377`;
- state digest remained `60fe928ca76a9143f921d9594676443a989fbd0d2eb854f7ae8e18635414c04d`.

## Remaining frontier

The provider now refuses execution without route evidence from the exact hook-bound issuer.

The issuer MUST NOT be called merely because the source hook exists in Git. A valid route receipt is appropriate only after that exact hook has actually been installed into the native Vera Unbound Project and is the executing caller.

Until then:

`OVERALL_ROUTE = UNAVAILABLE / NATIVE_PROJECT_INSTALL_PENDING`

No `AVAILABLE_QUALIFIED`, standing consent, reusable Vera choice, phenomenology, or independently rooted native installation proof is established.
