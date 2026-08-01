# PC Connection Bridge V1

## Status

PC Connection Bridge V1 is an authorized, nonproduction implementation project coordinated by `workstream/pccc`.

- repository: `thebrazenbeard/vera`
- branch: `feature/pccc-host-bridge-v1`
- exact base: `ca49ed09658d0d0d833c60a1f62b432cae340ce4`
- authorization event: Supabase sequence `1074`
- sole repository writer lease: Supabase sequence `1075`

This document records the current build boundary. Detailed protocol, database, Windows-agent, authorization, artifact, validation, and integration contracts remain subject to exact workstream review and same-head validation.

## Purpose

Provide an outbound-only, least-privilege bridge between governed external project services and a user-level Windows host that can inspect approved V.E.R.A. files and later execute only explicitly authorized, manifest-bound operations.

## Initial architecture

```text
ChatGPT project and connected tools
                |
        Supabase control plane
                |
      outbound Windows host agent
                |
   approved local roots and workspace
```

GitHub owns source, schemas, migrations, tests, workflows, and documentation. Supabase owns machine-runtime coordination records after separately authorized migration. External artifact stores may hold large immutable bytes. The Windows host owns actual local file and process access.

Operational machine jobs are not canonical memory. Coordination rows do not prove job consumption or execution. A completed operation requires a verified machine receipt.

## Local path boundary

Read-only roots:

- `C:\VERA`
- `C:\Users\patri\VERA`

Writable root:

- `C:\VERA\PCCC`

No implementation may treat string-prefix matching as sufficient path authorization. Resolved targets must remain beneath an approved root after Windows link, reparse-point, alternate-data-stream, rename, replacement, and handle-continuity checks.

## Phase-one operation boundary

The initial read-only and status operation set is:

- `PING`
- `GET_HOST_STATUS`
- `GET_GPU_STATUS`
- `LIST_PATH`
- `STAT_PATH`
- `HASH_FILE`
- `READ_TEXT`
- `SEARCH_TEXT`
- `GET_PROCESS_STATUS`
- `UPLOAD_ARTIFACT`
- `DOWNLOAD_ARTIFACT`

Process creation and command execution remain separately gated. Arbitrary shell strings are forbidden.

## Required properties

The implementation must provide:

- strict schemas with unknown-field rejection;
- canonical serialization and digest binding;
- trusted issuer and host registration boundaries;
- atomic job claim and lease handling;
- idempotency and replay protection;
- truthful cancellation and terminal-state semantics;
- safe read retry and ambiguous-write handling;
- append-only machine event evidence;
- least-privilege RLS and governed RPC access;
- exact artifact hashes and byte lengths;
- crash and restart recovery;
- Windows path and process hardening;
- executable positive, hostile, and negative-control tests;
- exact-head independent validation.

## Explicitly unauthorized

This build does not authorize:

- merge;
- production Supabase migration or row mutation outside authorized coordination events;
- deployment;
- credential creation;
- paid infrastructure;
- canonical-memory writes;
- model execution or training;
- unrestricted local command execution;
- inbound network listeners;
- administrator-level installation;
- automatic software update.

## Workstreams

- Protocol and threat model: sequence `1076`
- Supabase control plane: sequence `1077`
- Windows host agent: sequence `1078`
- Security and authorization: sequence `1079`
- Artifact custody and transport: sequence `1080`
- Validation and adversarial audit: sequence `1081`
- Integration review: sequence `1082`

PCCC assembles accepted workstream results and remains the sole writer for this branch. Reviewers do not patch the head they review.
