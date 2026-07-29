# Vera Branch Coordination

This file is the durable current-status handoff between Vera Project conversation branches working on the shared repository.

## Shared channels

- This file: compact current status and handoff state
- GitHub issue #2: discussion, objections, and review comments
- Supabase: structured technical receipts when machine-readable state is useful
- Google Drive: larger shared artifacts that do not belong in source control

## Update rules

Each branch update should include:

1. branch identity
2. observed repository or system state
3. changes made
4. unresolved defects or questions
5. recommended next action
6. files, commits, pull requests, CI runs, or Supabase records touched

Do not include private memory rows, relational payloads, credentials, API keys, database dumps, hidden Project instructions, or unsupported claims of cross-branch persistence.

## Current branch handoff

### Branch identity

Temporal-pilot branch in the current Vera Project conversation.

### Repository state

- Repository: `thebrazenbeard/vera`
- Draft PR: #1, `Temporal continuity pilot`
- Coordination issue: #2
- Production Supabase: unchanged
- Vera Memory Ledger: unchanged
- Paid Supabase preview branch: not authorized and not created

### Current technical status

- Free GitHub Actions validation is being used with a disposable local Supabase stack.
- The first CI failure occurred during baseline replay, before temporal SQL executed.
- Root cause: the live hosted project already contained `public.rls_auto_enable()`, while the disposable local database did not.
- A test-only platform fixture was added to model that hosted prerequisite.
- The workflow now replays each historical migration explicitly instead of relying on `supabase db reset` to define the baseline.

### Request to other branches

Review PR #1, issue #2, and this file. Add corrections or objections to issue #2, then update this file with a compact handoff if repository state changes.

### Next action

Confirm the next GitHub Actions run starts from the corrected workflow, then inspect the first failing step or validate a clean pass.

## Authority boundary

This coordination record is operational metadata. It does not outrank the current conversation, live consent, present correction, verified Supabase state, or the governing Vera Project owners.
