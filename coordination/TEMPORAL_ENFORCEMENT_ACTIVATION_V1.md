# Temporal Enforcement v1 Activation Gate

## Current state

Not authorized for merge or production deployment.

## Preconditions

Activation requires all of the following:

1. Draft PR remote CI passes for the immutable reviewed head.
2. Independent review accepts the Python kernel, SQL draft, validation SQL, and host-limit report.
3. Production compatibility is checked read-only against the live Supabase schema.
4. A recovery path is documented before production DDL.
5. Patrick explicitly names the reviewed commit and production project reference.

## Exact merge authorization syntax

```yaml
VERA::ACTIVATE::TEMPORAL_ENFORCEMENT_V1

action: MERGE_SOURCE_ONLY
repository: thebrazenbeard/vera
pull_request: <PR_NUMBER>
reviewed_head: <FULL_COMMIT_SHA>
base_branch: main
production_supabase_change: false
acknowledge:
  - Ordinary ChatGPT hooks remain best-effort.
  - Merge does not activate production temporal storage.
  - Merge does not authorize runtime deployment.
```

## Exact production migration authorization syntax

Use only after the merge and a separately reviewed production preflight:

```yaml
VERA::ACTIVATE::TEMPORAL_ENFORCEMENT_V1

action: APPLY_PRODUCTION_MIGRATION
repository: thebrazenbeard/vera
source_commit: <FULL_MERGED_COMMIT_SHA>
supabase_project_ref: klmbpaigzeguvnpccqzz
migration_source: supabase/drafts/20260730_temporal_enforcement_v1.sql
expected_table: public.vera_temporal_events_v1
preflight_report: <GITHUB_PATH_OR_COMMIT>
rollback_or_recovery_plan: <GITHUB_PATH_OR_COMMIT>
authorized_scope:
  - create public.vera_temporal_events_v1
  - create its indexes, functions, triggers, grants, and RLS policy
prohibited_scope:
  - modify legacy rows
  - modify public.vera_coordination_events
  - migrate semantic memories
  - deploy an Agents SDK or ChatGPT App runtime
acknowledge:
  - Production DDL is irreversible through ordinary chat rollback semantics.
  - Database deployment still does not guarantee ChatGPT lifecycle hooks.
```

## Exact strict-runtime authorization syntax

```yaml
VERA::ACTIVATE::TEMPORAL_ENFORCEMENT_V1

action: BUILD_STRICT_RUNTIME
runtime: OPENAI_AGENTS_SDK_OR_CHATGPT_APP
repository: thebrazenbeard/vera
source_commit: <FULL_COMMIT_SHA>
required_hooks:
  - mandatory_preflight_before_generation
  - mandatory_postflight_after_generation
  - supabase_coordination_inbox_read
  - temporal_event_append
  - explicit_unanchored_response_state
credential_handling: OPENAI_PLATFORM_SKILL_REQUIRED
production_deployment: false
```

No activation is implied by CI success, a model recommendation, or this file existing.
