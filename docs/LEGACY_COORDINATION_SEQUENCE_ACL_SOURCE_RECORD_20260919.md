# Legacy Coordination Sequence ACL Source Record — 2026-09-19

Issue: `thebrazenbeard/vera#54`

Status: **FRESH_PROVIDER_READBACK / SOURCE_REPAIR_CANDIDATE / NOT_APPLIED**

Target provider:
- Supabase project: `klmbpaigzeguvnpccqzz` (`Vera`)
- sequence: `public.vera_coordination_events_event_sequence_seq`

Fresh read-only provider inspection on 2026-09-19 confirmed the sequence exists.
Observed sequence ACL:
`{postgres=rwU/postgres,anon=rwU/postgres,authenticated=rwU/postgres,service_role=rwU/postgres}`

Fresh `has_sequence_privilege` checks show:
- `anon`: USAGE=true, SELECT=true, UPDATE=true
- `authenticated`: USAGE=true, SELECT=true, UPDATE=true
- `service_role`: USAGE=true, SELECT=true, UPDATE=true
- `postgres`: USAGE=true, SELECT=true, UPDATE=true

No `nextval()` or `setval()` call was made; provider state was not mutated.
The backing table was also re-read:
- `public.vera_coordination_events` has RLS enabled;
- `anon` and `authenticated` have no SELECT/INSERT/UPDATE/DELETE;
- `service_role` retains SELECT/INSERT only;
- `postgres` retains owner privileges.

Therefore the current defect remains specifically the unnecessary client sequence authority, not direct client row access.

The source migration revokes sequence privileges only from `PUBLIC`, `anon`, and `authenticated`. It deliberately preserves `service_role` and `postgres`.
## Claim and authority ceiling

This record plus source tests establish a current provider precondition and a bounded migration candidate only.

The migration has **not** been applied to production. No production/provider mutation is authorized merely by this source record, issue text, branch, test pass, or pull request.

Closure requires:
1. separately authorized migration application;
2. exact provider migration receipt/readback;
3. read-only post-migration validation proving client sequence privileges are false while required service-role access remains intact.
