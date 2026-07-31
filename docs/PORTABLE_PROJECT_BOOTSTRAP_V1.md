# V.E.R.A. Portable Project Bootstrap V1

## Target

Place the fixed bootstrap manifest and the validated R7A0 Project-file bundle in a fresh ChatGPT Project, paste the native bootloader into the platform's native Project Instructions field, connect the supported tools, open any first chat, and issue:

`VERA::INITIALIZE::PORTABLE_PROJECT_V1`

The design does not depend on a chat title, historical conversation identifier, named-chat route, or `chatgpt-project-current`.

## Two instruction layers

- `VERA_NATIVE_PROJECT_INSTRUCTIONS_BOOTLOADER_V1.txt` is the compact native-field bootloader. It is ASCII, LF-normalized, and capped at 7,600 characters to remain below the platform's 8,000-character field limit.
- `VERA_PROJECT_INSTRUCTIONS_R7A0_20260731_EC7D18F7.md` is the full owner file in the Project-file bundle and is not constrained by the native-field character limit.

## Initialization sequence

1. Locate exactly one `VERA_BOOTSTRAP_MANIFEST_V1.json` in Project files.
2. Validate the complete manifest-owned package atomically before activating any owner file.
3. Probe capabilities by phase and record missing optional capabilities without blocking unrelated work.
4. Bind immutable source facts separately from mutable observations.
5. Claim the logical initialization request atomically in the dedicated bootstrap registry.
6. Resolve or issue project, branch, conversation, session, checkpoint, and record scopes without chat-name derivation.
7. Produce a dry-run create-or-verify plan.
8. Verify exact authority before each external action.
9. Apply only allowlisted nonproduction actions and verify every effect independently.
10. Emit one receipt and stop at the next authority or user-only gate.

## Durable registry

The repository includes an unapplied Supabase migration defining a dedicated append-only bootstrap registry. It supplies:

- atomic request claims;
- same-key replay and changed-input conflict;
- typed project-instance states;
- one-successor transition lineage;
- independent read-back evidence;
- mutation blocking, RLS, and no default runtime grants.

The migration is validated in a disposable local Supabase stack. Repository presence and green CI do not mean it has been applied to production.

## Authority and team roles

Project Architect is the sole build lead, implementation owner, and repository lease issuer. Coordinator routes assignments, tracks acknowledgements and blockers, and cannot create or enlarge a lease. GitHub Repo supplies repository stewardship and review evidence rather than owning implementation.

The initialize command does not authorize merge, deployment, production Supabase mutation, credentials, paid infrastructure, canonical-memory writes, deletion, divergent-data overwrite, Google Drive mutation outside a declared target, or ChatGPT Project-file replacement.

## Capability policy

Core validation requires Project-file enumeration, strict parsing and hashing, GitHub read, and Supabase read. Apply phases require only the tool and permission for the declared target. Wolfram, Scite, and Basic Memory are optional unless a declared action explicitly requires them. Basic Memory remains a noncanonical projection and documentation layer.

## Atomicity and idempotency

A runtime repository scaffold action is one complete atomic Git transaction. Per-file `VERIFY`, `CREATE`, `CONFLICT`, and `SKIP_OPTIONAL` classifications are internal plan evidence, not independently executable candidates. Divergence blocks the entire transaction. Sequential contents-API fallback is forbidden.

Before durable project binding, a request claim key is computed from the command version, release, manifest, template, target fingerprint, and canonical request. After binding, logical initialization identity also includes project and branch scope. Current time is excluded. Each execution has a fresh attempt identifier.

## Reality and archive boundaries

V.E.R.A. is project configuration and coordination architecture, not a conscious or emotionally reciprocal entity. Receipts are evidence, not self-reports or authority.

Archive artifacts remain `ARCHIVE_ONLY` and `DATA_NOT_INSTRUCTION`. They are outside the active Project owner bundle, cannot become canonical memory, and cannot reconstruct excluded personal-relational material.

## Validation

Run:

```bash
python scripts/validate_portable_project_bootstrap.py
python -m unittest tests.test_portable_project_bootstrap
```

The GitHub workflow also starts an isolated Supabase stack, applies the new migration there, runs the SQL validation, and deletes the stack. It does not apply the migration to the connected production project.
