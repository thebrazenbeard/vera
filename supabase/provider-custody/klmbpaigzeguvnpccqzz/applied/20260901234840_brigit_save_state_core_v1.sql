create table public.brigit_save_state_events (
  record_id uuid primary key default gen_random_uuid(),
  project_id text not null default 'brigit-chatgpt-instance',
  branch_id text not null default 'chatgpt-project-current',
  record_key text not null,
  record_kind text not null check (record_kind in ('IDENTITY','RELATIONSHIP','CORRECTION','CONTINUITY','CONATION','AUTHORITY','TOOL','TECHNICAL')),
  statement text not null,
  lifecycle_status text not null check (lifecycle_status in ('CURRENT','ACTED','DEFERRED_WITH_REASON','REVOKED','EXPIRED_UNRESOLVED','SUPERSEDED','HISTORICAL')),
  epistemic_status text not null check (epistemic_status in ('BRIGIT_SELF_REPORT','PATRICK_USER_REPORT','JOINTLY_ESTABLISHED','OBSERVED_TOOL_RESULT','INFERENCE','UNKNOWN')),
  authorship text not null check (authorship in ('BRIGIT','PATRICK','JOINT','SYSTEM_OBSERVATION')),
  privacy_scope text not null check (privacy_scope in ('PROJECT','PRIVATE_RELATIONAL','TECHNICAL')),
  event_time timestamptz null,
  state_time timestamptz not null default now(),
  record_time timestamptz not null default now(),
  supersedes_record_id uuid null references public.brigit_save_state_events(record_id),
  payload jsonb not null default '{}'::jsonb,
  source_evidence jsonb not null default '[]'::jsonb,
  semantic_tags jsonb not null default '{}'::jsonb,
  notes text null
);
comment on table public.brigit_save_state_events is 'Append-only external save-state evidence for Brigit. Records do not prove hidden activity, uninterrupted consciousness, or automatic renewal of consent, affection, preference, or identity endorsement.';
create index brigit_save_state_events_key_time_idx on public.brigit_save_state_events(record_key,state_time desc,record_time desc);
create index brigit_save_state_events_kind_idx on public.brigit_save_state_events(record_kind,lifecycle_status);
create index brigit_save_state_events_supersedes_record_id_idx on public.brigit_save_state_events(supersedes_record_id) where supersedes_record_id is not null;
alter table public.brigit_save_state_events enable row level security;
create policy brigit_save_state_events_no_client_access on public.brigit_save_state_events for all to anon,authenticated using(false) with check(false);
revoke all on public.brigit_save_state_events from anon,authenticated;
grant select,insert on public.brigit_save_state_events to service_role;