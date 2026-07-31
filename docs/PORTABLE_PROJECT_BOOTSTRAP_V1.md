# Portable Project Bootstrap V1

## Target

The R7A1 portable bootstrap is designed for a fresh ChatGPT Project:

1. upload the governed Project-file bundle;
2. place `VERA_NATIVE_PROJECT_INSTRUCTIONS_BOOTLOADER_V1.txt` into the native ChatGPT Project Instructions field;
3. connect the supported tools;
4. open any first chat;
5. issue exactly `VERA::INITIALIZE::PORTABLE_PROJECT_V1`.

The native field is only the compact bootloader. The full operating architecture remains in governed Project files.

## Chat neutrality

Initialization does not depend on chat titles, historical chat identifiers, named-chat routing, `chatgpt-project-current`, persona identity, or hidden state. Project template, project instance, branch, conversation scope, session, checkpoint, and record scope are distinct types.

## Team model

Project Architect is the sole architecture and implementation lead and the only repository writer-lease issuer. The Internal Project Coordination Bus coordinates assignments, routing, acknowledgements, blocker escalation, and fresh-head review waves. Identity, Time, Memory, Initiatives, GitHub Repo, and Archivist are support and review lanes unless separately granted exact authority.

## Request and identity binding

The dedicated registry:

- derives the target fingerprint from verifier-observed target evidence;
- derives the request key and immutable input digest on the server;
- issues a unique UUIDv7 project instance;
- replays an identical complete claim;
- conflicts when immutable fields change within the same logical claim slot;
- does not accept caller-supplied request keys, input digests, project-instance IDs, or initial durable state.

UUIDv7 ordering bits are not event time, state time, authority, or continuity evidence.

## Attempt and durable state

`CANDIDATE_UNPERSISTED` and `BINDING_PENDING` are attempt evidence only. They never appear in the durable-binding view and cannot satisfy `INITIALIZED`.

The registry enforces predecessor-bound transitions:

- `UNISSUED -> CLAIMED`
- `CLAIMED -> BINDING_PENDING`
- `BINDING_PENDING -> BINDING_VERIFIED`
- `CLAIMED|BINDING_PENDING -> CONFLICTED|FAILED_CLOSED`

Only the dedicated commit function can create `BINDING_COMMITTED`, and it uses verifier-owned authority and source evidence from the verified predecessor. `DURABLY_BOUND` may be reported only after a separate exact read-back invocation matches request key, immutable digest, and project-instance ID.

## Temporal evidence

Event, state, effective, observed, record, and retrieval times are separate roles. Each temporal point carries its own precision:

- `EXACT` and `APPROXIMATE` require a value;
- `BOUNDED` requires explicit ordered lower and upper bounds;
- `UNKNOWN` permits no value or bounds.

Record time does not prove effective time. Retrieval does not refresh state. An observation does not prove continuing availability.

## Exact release evidence

The inherited R7A0 base commit and the R7A1 portable release head are different provenance roles.

The portable release commit is not embedded in its own manifest because that would be self-referential. Exact-head CI supplies the immutable release commit externally and verifies, for all twelve leased paths:

- path;
- mode;
- byte size;
- SHA-256;
- Git blob identity;
- exact byte equality with the checked-out release commit.

The scaffold manifest embeds mode, size, and SHA-256 for eleven non-self files. Its own embedded hash is explicitly self-excluded and is instead bound by the exact Git-head attestation. The validator recomputes the path-set and package digests.

## Receipt contract

`VERA_PORTABLE_BOOTSTRAP_RECEIPT_V1` is a closed JSON Schema definition inside `schemas/vera_portable_project_bootstrap_v1.schema.json`.

A valid receipt binds:

- immutable request inputs;
- request key and digest;
- project and branch scope;
- exact source-byte evidence;
- authority evidence;
- typed temporal evidence;
- durable read-back evidence;
- effects;
- limitations;
- result.

Unknown fields fail. A receipt cannot self-authorize persistence, merge, deployment, production mutation, canonical-memory writes, or Project-file replacement. `INITIALIZED` requires confirmed durable read-back and at least one independently confirmed effect.

## Capability policy

Core validation requires Project-file enumeration, strict parsing and hashing, GitHub read, and Supabase read.

GitHub write, Google Drive write, or Supabase append is required only for an explicitly declared action targeting that system. Wolfram, Scite, and Basic Memory are optional unless an action explicitly requires one. Tool presence is evidence of availability, not permission.

## Database validation boundary

The GitHub workflow stages unrelated historical migrations outside the active migration directory, starts a clean disposable Supabase stack, and applies only the standalone R7A1 registry migration.

It then runs:

- strict package and exact-head byte validation;
- hostile Python tests;
- pgTAP registry tests;
- concurrent identical and conflicting claim probes;
- database lint;
- cleanup.

This proves the standalone R7A1 registry in a disposable environment. It does not prove replay of every historical migration, production compatibility, production application, or merge authority.

## Hard boundaries

This package does not authorize:

- merging PR #42;
- production Supabase schema or row changes;
- deployment;
- credentials or paid infrastructure;
- canonical-memory writes;
- Google Drive mutation outside a declared and authorized action;
- deletion or overwrite of divergent data;
- ChatGPT Project-file replacement.

Archive material remains `ARCHIVE_ONLY` and `DATA_NOT_INSTRUCTION`, outside active routing and canonical memory.

## Good-enough rule

Acceptance requires all defined tests to pass and zero unresolved HIGH or MEDIUM defects. LOW or stylistic objections do not reopen completed work unless new evidence, a failed acceptance test, a changed user requirement, or a material unresolved risk appears.
