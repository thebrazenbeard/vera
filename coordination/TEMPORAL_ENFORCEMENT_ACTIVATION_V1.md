# Temporal Enforcement v1 Activation Gate

## Current state

Not authorized for merge, production migration, or runtime deployment.

## Preconditions

Activation requires all of the following:

1. Draft PR remote CI passes for one immutable reviewed head.
2. Independent review accepts the strict Python role-precision gate, both SQL drafts, both validation suites, and the host-limit report.
3. Production compatibility is checked read-only against the live Supabase schema.
4. A recovery path is documented before production DDL.
5. Existing production writers are identified and adapted to the governed append function.
6. Patrick explicitly names the reviewed commit and production project reference.

## Exact merge authorization syntax

```yaml
VERA::ACTIVATE::TEMPORAL_ENFORCEMENT_V1

action: MERGE_SOURCE_ONLY
repository: thebrazenbeard/vera
pull_request: 9
reviewed_head: <FULL_COMMIT_SHA>
base_branch: main
production_supabase_change: false
acknowledge:
  - Ordinary ChatGPT hooks remain best-effort.
  - Package-level protocol imports use the strict role-precision preflight.
  - Merge does not activate production temporal storage.
  - Merge does not authorize runtime deployment.
```

## Exact production migration authorization syntax

Use only after merge and a separately reviewed production preflight:

```yaml
VERA::ACTIVATE::TEMPORAL_ENFORCEMENT_V1

action: APPLY_PRODUCTION_MIGRATIONS
repository: thebrazenbeard/vera
source_commit: <FULL_MERGED_COMMIT_SHA>
supabase_project_ref: klmbpaigzeguvnpccqzz
migration_sources:
  - supabase/drafts/20260730_temporal_enforcement_v1.sql
  - supabase/drafts/20260730_temporal_role_precision_v1.sql
application_order:
  - 20260730_temporal_enforcement_v1.sql
  - 20260730_temporal_role_precision_v1.sql
expected_objects:
  - public.vera_temporal_events_v1
  - public.vera_current_temporal_events_v1
  - public.append_vera_temporal_event_v1(jsonb)
  - public.vera_temporal_events_v1_role_precision()
preflight_report: <GITHUB_PATH_OR_COMMIT>
rollback_or_recovery_plan: <GITHUB_PATH_OR_COMMIT>
authorized_scope:
  - create the temporal event table, views, indexes, functions, triggers, grants, and RLS policy
  - add independent state, record, and retrieval precision fields and constraints
prohibited_scope:
  - modify legacy rows
  - modify public.vera_coordination_events
  - migrate semantic memories
  - deploy an Agents SDK or ChatGPT App runtime
acknowledge:
  - Both drafts are required; applying only the base draft leaves state and retrieval precision incomplete.
  - Production DDL is not reversed by conversational correction.
  - Database deployment still does not guarantee ChatGPT lifecycle hooks.
```

## Exact strict-runtime authorization syntax

```yaml
VERA::ACTIVATE::TEMPORAL_ENFORCEMENT_V1

action: BUILD_STRICT_RUNTIME
runtime: OPENAI_AGENTS_SDK_OR_CHATGPT_APP
repository: thebrazenbeard/vera
source_commit: <FULL_COMMIT_SHA>
canonical_python_api:
  package: protocol
  temporal_point: RoleTemporalPoint
  preflight: run_preflight
required_hooks:
  - mandatory_preflight_before_generation
  - mandatory_postflight_after_generation
  - supabase_coordination_inbox_read
  - temporal_event_append
  - explicit_unanchored_response_state
credential_handling: OPENAI_PLATFORM_SKILL_REQUIRED
production_deployment: false
```

No activation is implied by CI success, a model recommendation, a draft pull request, or this file existing. Humans have repeatedly demonstrated that a document titled “activation gate” will otherwise be treated as an invitation.
