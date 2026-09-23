# Bus/Radar continuation pointer — 2026-09-23 V1

Restore with:

`VERA::RESTORE_AND_RUN::BUS_RADAR_ACTIONS_CONTINUATION_20260923_V1`

Primary durable checkpoint is in `thebrazenbeard/chat-communication-bus`:

- main at save: `0d47644171283e0a46d2e759c67ef4a5bf0b72ff`
- `docs/checkpoints/VERA_BUS_RADAR_ACTIONS_CONTINUATION_20260923_V1.md`
- blob `4b1b3c879ca453c5a2eae39c48a3c6beabcb4076`
- `docs/checkpoints/VERA_BUS_RADAR_ACTIONS_CONTINUATION_20260923_V1.json`
- blob `fc2d6656bdd814bd2f6cb02332b16cdadab44a7e`

At save:
- canonical Bus source custody is repaired;
- deployed `github-bus-ingest` matches canonical Bus main;
- private GitHub Actions still fail before runner allocation;
- central dispatcher has not executed;
- Radar projection tables remain empty/stale;
- replay rejection and idempotent recovery are not reverified.

This pointer is not currentness authority. Fresh-read the primary checkpoint and refresh Bus/Vera/VCP/Supabase state before resuming.
