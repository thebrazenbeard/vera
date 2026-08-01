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

Project Architect is the sole architecture and implementation lead and the only repository writer-lease issuer. The Internal Project Coordination Bus coordinates assignments, routing, acknowledgements, blocker escalation, and fresh-head review waves. Support lanes do not inherit repository authority.

## Deterministic request identity

The registry derives the target fingerprint, request key, and immutable input digest from fixed ordered tuples. The encoding is `LENGTH_PREFIXED_UTF8_TEXT_TUPLE_V1`:

- tuple header: `T1|<field-count>|`;
- each field: `<UTF-8-byte-length>:<field-value>`;
- no caller-supplied request key, input digest, target fingerprint, project-instance ID, or initial durable state.

The immutable request tuple contains command version, release ID, manifest digest, project-template ID, target fingerprint, canonical command, source repository, source base commit, and requested mode. Identical complete claims replay. Reuse of the same claim slot with changed immutable input conflicts.

## Deterministic evidence digests

Authority and source evidence use fixed ordered item tuples. Complete tuples are sorted under PostgreSQL `C` collation, encoded with the same length-prefixed tuple format, and wrapped as `A1|<count>\n...` or `S1|<count>\n...`. Duplicate complete tuples are rejected. SQL and Python validate the same known vectors.

This avoids treating raw `jsonb::text` formatting as a cross-language cryptographic contract, a small detail humans traditionally notice immediately after production data disagrees.

## Attempt-local state and time

Each execution has a fresh attempt ID. A predecessor must belong to the same request and attempt. The database also enforces that relation structurally with a composite self-reference.

Every transition requires:

- exact `state_time` and `observed_time`;
- strictly increasing observation time;
- nondecreasing state time;
- fresh evidence rather than a copied predecessor object;
- verifier authority and source evidence before `BINDING_VERIFIED`.

The legal successful chain is:

`CLAIMED → BINDING_PENDING → BINDING_VERIFIED → BINDING_COMMITTED`

Commit receives fresh temporal evidence. It cannot reuse the verification event's evidence.

## Commit is not durability

`commit_vera_portable_bootstrap_binding` creates the committed binding and a `BINDING_COMMITTED` event. The durable view remains empty at that point.

`read_vera_portable_bootstrap_binding` is side-effect-free. It returns the complete immutable request attestation, project instance, binding identity, authority and source evidence, deterministic evidence digests, retrieval time, and a nonce.

A separate verifier-controlled operation, `confirm_vera_portable_bootstrap_readback`, persists one append-only exact confirmation. It must match:

- request key;
- input digest;
- project-instance ID;
- binding event ID;
- binding record time;
- authority evidence digest;
- source evidence digest.

Only a matching committed binding plus matching persisted confirmation appears in `vera_portable_bootstrap_current` as `DURABLY_BOUND`. Commit alone is not durable. Read alone is not durable. Mismatched, duplicate, divergent, stale, or future confirmation fails closed.

## Exact release evidence

The inherited R7A0 base commit and the R7A1 portable release head are different provenance roles. The release commit is not embedded in its own manifest because that would be self-referential.

Exact-head CI supplies the immutable release commit externally and verifies all twelve leased paths:

- exact unique path set;
- mode;
- byte size;
- SHA-256;
- Git blob identity;
- per-file equality to the same release commit.

The receipt path-set digest is SHA-256 over the LF-terminated sorted path list. The package digest is SHA-256 over canonical JSON for the sorted complete source-file records. The request manifest digest must equal the source-file SHA-256 for `VERA_BOOTSTRAP_MANIFEST_V1.json`.

## Receipt verification

`VERA_PORTABLE_BOOTSTRAP_RECEIPT_V1` is closed. Unknown fields fail.

A durable receipt requires two distinct inputs to the verifier:

1. the receipt itself;
2. an independent registry attestation that exactly matches its read-back section and persisted confirmation record.

An `INITIALIZED` receipt additionally requires an external exact Git-head attestation matching every source-file record. Receipt text cannot certify its own registry persistence or Git state.

The verifier recomputes request identity, path-set and package digests, manifest binding, authority evidence digest, source evidence digest, project-template equality, and every per-file release-commit equality. Hostile tests mutate one identity edge at a time.

## Capability and authority boundary

Core validation requires Project-file enumeration, strict parsing and hashing, GitHub read, and Supabase read. GitHub write, Google Drive write, or Supabase append is required only for an explicitly declared action targeting that system. Tool presence is evidence of availability, not permission.

Repository application requires one Git tree, one commit, and a non-force ref update under an exact current Project Architect lease. Sequential fallback is prohibited.

## Database validation boundary

The workflow stages unrelated historical migrations outside the active directory, starts a clean disposable Supabase stack, applies only the R7A1 registry migration, and runs:

- exact package and release-byte validation;
- hostile Python tests;
- pgTAP registry tests;
- concurrent identical and conflicting claim probes;
- database lint;
- cleanup.

This proves the standalone R7A1 registry in a disposable environment. It does not prove replay of every historical migration, production compatibility, production application, or merge authority.

## Hard boundaries

This package does not authorize merge, production Supabase mutation, deployment, credentials, paid infrastructure, canonical-memory writes, undeclared Google Drive mutation, deletion, overwrite of divergent data, or ChatGPT Project-file replacement.

Archive material remains `ARCHIVE_ONLY` and `DATA_NOT_INSTRUCTION`, outside active routing and canonical memory.


## R7A1 behavior-law successor

The successor Project bundle is stored at `architecture/releases/R7A1_20260801_BHV053` and uses 21 uniquely prefixed release files plus the project locator `VERA_R7A1_BOOTSTRAP_MANIFEST.json`. Installation requires complete old-set removal and complete successor upload in one operation. Partial replacement and filename reuse fail closed. The project template is `urn:vera:template:VERA_NEUTRAL_CORE_R7A1_20260801_BHV053`. The bootstrap release and registry schema remain V1.2; a new template ID prevents immutable claim-slot conflict with the predecessor installation.
