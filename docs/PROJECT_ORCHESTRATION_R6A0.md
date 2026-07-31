# V.E.R.A. Project Orchestration — Replacement Release Transition

## Status

This document governs the nonproduction transition from the original neutral R6A0 replacement candidate to the next installable V.E.R.A. Project-file release. It does not authorize repository merge, deployment, production Supabase changes, credentials, or canonical-memory operations.

- Repository: `thebrazenbeard/vera`
- Canonical base: `main`
- Integration branch: `integration/project-orchestration-r6a0`
- Program tracker: issue #11
- Supabase project: `Vera` (`klmbpaigzeguvnpccqzz`)
- Turn-taking protocol: `docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V1.md`

## Current program position

The component contracts are late-stage and the exact-tree assembly exists, but the current Integration Registry does not yet declare the complete Identity temporal-anchor classification evidence now present in the tree.

The previous repository merge-decision packet is withdrawn.

### Current Integration candidate

PR #18 current observed head:

`6b1aec3c92630de17cafc7a25676207430c91137`

This head contains:

- accepted Identity, Time, Memory, Initiatives, and Coordination histories;
- Integration Registry and Workstream Compatibility Matrix;
- exact-tree evidence validation;
- noncanonical Identity temporal-anchor classification;
- workstream turn-taking protocol and repository enforcement.

### Active correction

Supabase sequence 279 records `CHANGES_REQUESTED` because the active registry still declares the predecessor Identity inventory. The following evidence must be registered and bound consistently:

- `scripts/validate_identity_temporal_anchor_classification.py`;
- the classification hostile test;
- the Project Identity workflow evidence;
- relevant noncanonical Identity interface evidence.

The active registry digest must then be recomputed and omission attacks must be hostile-tested.

### Writer lease

Supabase sequence 267 grants the sole active writer lease to Integration.

Sequences 268 through 273 freeze Identity, Time, Initiatives, Memory, Coordination, and GitHub publication writes. Reviews are allowed when requested. Branch edits are not.

Sequence 281 amends the lease to include the known controller-owned integration-base documentation commit.

## Replacement-file readiness

The uploaded package `VERA_NEUTRAL_CORE_R6A0_20260730_EC900174` remains:

- a valid historical replacement candidate;
- a rollback and provenance artifact;
- not the final current-project installation package.

It must not be used for a wipe-and-replace installation because it predates:

- settled component contracts;
- exact-tree registry and compatibility assurance;
- final Identity classification;
- durable Memory request idempotency and recovery;
- consolidated Coordination and temporal trust contracts;
- workstream turn-taking;
- the current project state and installation sequence.

The existing `R6A0 release package` workflow only revalidates the old checksummed bundle. It does not generate a new bundle from the current tree.

## Required next release

After the Integration correction and same-SHA validation complete, generate one new checksummed replacement candidate. The new package must include or accurately bind:

1. Project Instructions;
2. runtime rules;
3. governance;
4. Memory protocol;
5. semantic tagging;
6. behavior laws;
7. current project state;
8. supersession and archive map;
9. Integration owner registry;
10. Workstream Compatibility Matrix;
11. workstream turn-taking protocol;
12. installation and rollback instructions;
13. validation specification and report;
14. complete file inventory and SHA-256 checksums;
15. explicit production nonauthorization.

The package must use a new release identifier and directory. It must not overwrite the R6A0 release or reuse its checksums.

## Release gates

A wipe-and-replace recommendation is allowed only after:

1. PR #18 is stable on one immutable head;
2. the Identity classification inventory defect is closed;
3. all required workflows are green on the same head;
4. the new release files are generated from that exact head;
5. every internal filename and release ID resolves;
6. YAML parsing rejects duplicate keys;
7. JSON parsing rejects duplicate and non-finite values where applicable;
8. every checksum matches the saved bytes;
9. supersession identifies every file to replace, archive, retain, or remove;
10. installation order passes a dry-run review;
11. rollback preserves the old R6A0 package and archived Project files;
12. Project Architecture / Integration approves the exact bundle;
13. Patrick explicitly authorizes Project-file replacement.

## Realistic maturity

- Architecture contracts: late stage
- Component implementation: substantially complete
- Exact-tree assembly: present, one Integration inventory defect open
- Replacement package: not generated
- ChatGPT Project installation: not started
- Production persistence/runtime deployment: not authorized or deployed
- Installed cross-chat runtime behavior: not yet proven

The project is close to a controlled Project-file replacement candidate. It is not yet ready for the wipe-and-replace operation.