-- TEST-ONLY fixture mirroring the neutral V3 production shape observed on
-- 2026-07-30 before the bounded Memory hardening migration.
--
-- No production rows, credentials, or private conversation content are used.

begin;

create table public.vera_context_events_v3 (
  record_id uuid primary key default gen_random_uuid(),
  project_id text not null default 'vera-reciprocal-agency-environment',
  branch_id text not null,
  record_key text not null,
  record_type text not null check (record_type in (
    'FACT','USER_STATEMENT','MODEL_OUTPUT','PERSONA_CONFIG','RELATIONAL_FRAME',
    'PREFERENCE','DECISION','CORRECTION','BEHAVIORAL_COMMITMENT','BOUNDARY',
    'PERMISSION','TASK_STATE','TECHNICAL_RESULT','PROVENANCE','HYPOTHESIS',
    'INTERPRETATION','EVALUATION','LEDGER_SNAPSHOT','TOMBSTONE','OTHER'
  )),
  statement text not null,
  lifecycle_status text not null,
  epistemic_status text not null check (epistemic_status in (
    'DIRECT_USER_STATEMENT','OBSERVED_TOOL_RESULT','DOCUMENTED_SOURCE',
    'MODEL_GENERATED_CLAIM','SUPPORTED_INFERENCE','HYPOTHESIS','DISPUTED',
    'REJECTED','UNAVAILABLE'
  )),
  source_actor text not null check (source_actor in (
    'USER','CHATGPT_MODEL','TOOL','SYSTEM','EXTERNAL','UNRESOLVED'
  )),
  privacy_scope text not null default 'PROJECT',
  event_time timestamptz,
  state_time timestamptz not null default now(),
  record_time timestamptz not null default now(),
  supersedes_record_id uuid references public.vera_context_events_v3(record_id),
  legacy_record_id uuid,
  payload jsonb not null default '{}'::jsonb,
  source_evidence jsonb not null default '[]'::jsonb,
  semantic_tags jsonb not null default '{}'::jsonb,
  limitations jsonb not null default '[]'::jsonb,
  notes text,
  constraint vera_context_events_v3_payload_object_chk
    check (jsonb_typeof(payload) = 'object'),
  constraint vera_context_events_v3_source_evidence_array_chk
    check (jsonb_typeof(source_evidence) = 'array'),
  constraint vera_context_events_v3_semantic_tags_object_chk
    check (jsonb_typeof(semantic_tags) = 'object'),
  constraint vera_context_events_v3_limitations_array_chk
    check (jsonb_typeof(limitations) = 'array')
);

create index vera_context_events_v3_record_key_idx
  on public.vera_context_events_v3(record_key, state_time desc, record_time desc);
create index vera_context_events_v3_scope_key_idx
  on public.vera_context_events_v3(
    project_id, branch_id, record_key, state_time desc, record_time desc, record_id desc
  );
create index vera_context_events_v3_supersedes_record_id_idx
  on public.vera_context_events_v3(supersedes_record_id)
  where supersedes_record_id is not null;
create unique index vera_context_events_v3_legacy_record_id_uidx
  on public.vera_context_events_v3(legacy_record_id)
  where legacy_record_id is not null;
create index vera_context_events_v3_semantic_tags_gin
  on public.vera_context_events_v3 using gin (semantic_tags);

create view public.vera_current_context_v3
with (security_invoker = true)
as
select distinct on (project_id, branch_id, record_key)
  *
from public.vera_context_events_v3
order by project_id, branch_id, record_key, state_time desc, record_time desc, record_id desc;

alter table public.vera_context_events_v3 enable row level security;

create policy vera_context_events_v3_no_anon_access
  on public.vera_context_events_v3
  for all
  to anon
  using (false)
  with check (false);

create policy vera_context_events_v3_no_authenticated_access
  on public.vera_context_events_v3
  for all
  to authenticated
  using (false)
  with check (false);

revoke all privileges on table public.vera_context_events_v3 from anon, authenticated;
revoke all privileges on table public.vera_current_context_v3 from anon, authenticated;
grant select, insert, update, delete on table public.vera_context_events_v3 to service_role;
grant select on table public.vera_current_context_v3 to service_role;

-- Representative pre-existing lineage. The successor deliberately carries an
-- older state_time than its root so later tests can prove lineage beats recency.
insert into public.vera_context_events_v3 (
  record_id, project_id, branch_id, record_key, record_type, statement,
  lifecycle_status, epistemic_status, source_actor, privacy_scope,
  event_time, state_time, record_time, supersedes_record_id,
  payload, source_evidence, semantic_tags, limitations, notes
) values
(
  '10000000-0000-0000-0000-000000000001',
  'vera-memory-fixture',
  'branch-a',
  'memory.fixture.chain',
  'DECISION',
  'Fixture root.',
  'CURRENT',
  'DOCUMENTED_SOURCE',
  'SYSTEM',
  'PROJECT',
  '2026-07-30 20:00:00+00',
  '2026-07-30 20:10:00+00',
  '2026-07-30 20:10:01+00',
  null,
  '{"fixture":"root","preserve":true}'::jsonb,
  '[{"surface":"TEST_FIXTURE","claim":"root"}]'::jsonb,
  '{"domain":["memory","lineage"],"status":["historical"]}'::jsonb,
  '["Synthetic test-only evidence."]'::jsonb,
  'Representative root.'
),
(
  '10000000-0000-0000-0000-000000000002',
  'vera-memory-fixture',
  'branch-a',
  'memory.fixture.chain',
  'CORRECTION',
  'Fixture successor.',
  'CURRENT',
  'DOCUMENTED_SOURCE',
  'SYSTEM',
  'PROJECT',
  '2026-07-30 20:01:00+00',
  '2026-07-30 19:00:00+00',
  '2026-07-30 20:11:01+00',
  '10000000-0000-0000-0000-000000000001',
  '{"fixture":"successor","preserve":true}'::jsonb,
  '[{"surface":"TEST_FIXTURE","claim":"successor"}]'::jsonb,
  '{"domain":["memory","lineage"],"status":["current"]}'::jsonb,
  '["Synthetic test-only evidence."]'::jsonb,
  'Representative successor with older state_time.'
),
(
  '10000000-0000-0000-0000-000000000003',
  'vera-memory-fixture',
  'branch-b',
  'memory.fixture.chain',
  'DECISION',
  'Independent branch fixture.',
  'CURRENT',
  'DOCUMENTED_SOURCE',
  'SYSTEM',
  'PROJECT',
  '2026-07-30 20:02:00+00',
  '2026-07-30 20:02:00+00',
  '2026-07-30 20:02:01+00',
  null,
  '{"fixture":"independent","preserve":true}'::jsonb,
  '[{"surface":"TEST_FIXTURE","claim":"independent"}]'::jsonb,
  '{"domain":["memory","branch_separation"],"status":["current"]}'::jsonb,
  '["Synthetic test-only evidence."]'::jsonb,
  'Independent branch root.'
);

commit;
