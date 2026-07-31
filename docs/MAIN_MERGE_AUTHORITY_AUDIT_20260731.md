# PR #12 Main-Merge Authority Audit

## Observed state

- PR: `#12`
- reviewed integration head: `0f609243f790a9337d8e07db524e2ca0347056c0`
- observed main merge commit: `b20e7309c6ded3c358dce00baa537d2fc1880004`
- merge time: `2026-07-31T12:10:47Z`
- comparison from reviewed head to merge commit: zero changed files

## Provenance finding

The available current conversation explicitly authorized PR #18 into the integration branch and explicitly withheld authority for PR #12 into `main`.

No matching exact-SHA PR #12 authorization was located in:

- the current conversation;
- PR #12 issue comments or review submissions;
- `public.vera_coordination_events` through sequence 345.

The merge commit message says the merge was authorized. That statement is a repository claim, not self-authenticating authority evidence.

## Classification

- repository state: `OBSERVED_MERGED`
- tree integrity: `MATCHES_REVIEWED_INTEGRATION_HEAD`
- merge-authority provenance: `UNVERIFIED_PROVENANCE`
- automatic rollback authorized: `false`
- history rewrite authorized: `false`

## Governing consequence

Preserve the merge as observed history unless Patrick explicitly directs a revert or other remediation. Do not infer production, deployment, canonical-memory, credential, paid-infrastructure, or Project-file authority from this event.
