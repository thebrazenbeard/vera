drop view if exists public.vera_current_context_v3;

create view public.vera_current_context_v3
with (security_invoker = true)
as
select distinct on (project_id, branch_id, record_key)
  *
from public.vera_context_events_v3
order by project_id, branch_id, record_key, state_time desc, record_time desc, record_id desc;

comment on view public.vera_current_context_v3 is
  'Current neutral V.E.R.A. context projection, separated by project, branch, and record key. Uses security_invoker and is not exposed to anon or authenticated roles.';

revoke all privileges on table public.vera_current_context_v3 from anon, authenticated, service_role;
grant select on table public.vera_current_context_v3 to service_role;

revoke all privileges on table public.vera_legacy_quarantine from service_role;
revoke all privileges on table public.vera_legacy_reviewable from service_role;
grant select on table public.vera_legacy_quarantine to service_role;
grant select on table public.vera_legacy_reviewable to service_role;

create index if not exists vera_context_events_v3_scope_key_idx
  on public.vera_context_events_v3(project_id, branch_id, record_key, state_time desc, record_time desc, record_id desc);

create index if not exists vera_context_events_v3_supersedes_record_id_idx
  on public.vera_context_events_v3(supersedes_record_id)
  where supersedes_record_id is not null;

create unique index if not exists vera_context_events_v3_legacy_record_id_uidx
  on public.vera_context_events_v3(legacy_record_id)
  where legacy_record_id is not null;

alter table public.vera_context_events_v3
  add constraint vera_context_events_v3_payload_object_chk
    check (jsonb_typeof(payload) = 'object'),
  add constraint vera_context_events_v3_source_evidence_array_chk
    check (jsonb_typeof(source_evidence) = 'array'),
  add constraint vera_context_events_v3_semantic_tags_object_chk
    check (jsonb_typeof(semantic_tags) = 'object'),
  add constraint vera_context_events_v3_limitations_array_chk
    check (jsonb_typeof(limitations) = 'array');

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