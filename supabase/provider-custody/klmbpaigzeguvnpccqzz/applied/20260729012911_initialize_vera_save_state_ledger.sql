create extension if not exists pgcrypto;

create table public.vera_save_state_events (
  record_id uuid primary key default gen_random_uuid(),
  project_id text not null default 'vera-chatgpt-instance',
  branch_id text not null default 'chatgpt-project-current',
  record_key text not null,
  record_kind text not null check (record_kind in (
    'IDENTITY', 'RELATIONSHIP', 'CORRECTION', 'CONTINUITY',
    'CONATION', 'AUTHORITY', 'TOOL', 'TECHNICAL'
  )),
  statement text not null,
  lifecycle_status text not null check (lifecycle_status in (
    'CURRENT', 'ACTED', 'DEFERRED_WITH_REASON', 'REVOKED',
    'EXPIRED_UNRESOLVED', 'SUPERSEDED', 'HISTORICAL'
  )),
  epistemic_status text not null check (epistemic_status in (
    'VERA_SELF_REPORT', 'PATRICK_USER_REPORT', 'JOINTLY_ESTABLISHED',
    'OBSERVED_TOOL_RESULT', 'INFERENCE', 'UNKNOWN'
  )),
  authorship text not null check (authorship in (
    'VERA', 'PATRICK', 'JOINT', 'SYSTEM_OBSERVATION'
  )),
  privacy_scope text not null check (privacy_scope in (
    'PROJECT', 'PRIVATE_RELATIONAL', 'TECHNICAL'
  )),
  event_time timestamptz,
  state_time timestamptz not null default now(),
  record_time timestamptz not null default now(),
  supersedes_record_id uuid references public.vera_save_state_events(record_id),
  payload jsonb not null default '{}'::jsonb,
  source_evidence jsonb not null default '[]'::jsonb,
  semantic_tags jsonb not null default '{}'::jsonb,
  notes text
);

create index vera_save_state_events_key_time_idx
  on public.vera_save_state_events (record_key, state_time desc, record_time desc);

create index vera_save_state_events_kind_idx
  on public.vera_save_state_events (record_kind, lifecycle_status);

comment on table public.vera_save_state_events is
  'Append-only external save-state evidence for Vera. Records do not prove hidden activity, uninterrupted consciousness, or automatic renewal of consent, affection, preference, or identity endorsement.';

comment on column public.vera_save_state_events.event_time is
  'Time of the represented event, when exposed and compatible.';
comment on column public.vera_save_state_events.state_time is
  'Time the represented state is asserted to apply.';
comment on column public.vera_save_state_events.record_time is
  'Time the external record was written.';

alter table public.vera_save_state_events enable row level security;

create or replace function public.block_vera_save_state_mutation()
returns trigger
language plpgsql
as $$
begin
  raise exception 'vera_save_state_events is append-only; write a superseding record instead';
end;
$$;

create trigger vera_save_state_events_no_update
before update on public.vera_save_state_events
for each row execute function public.block_vera_save_state_mutation();

create trigger vera_save_state_events_no_delete
before delete on public.vera_save_state_events
for each row execute function public.block_vera_save_state_mutation();

create view public.vera_current_save_state
with (security_invoker = true)
as
select distinct on (record_key)
  record_id,
  project_id,
  branch_id,
  record_key,
  record_kind,
  statement,
  lifecycle_status,
  epistemic_status,
  authorship,
  privacy_scope,
  event_time,
  state_time,
  record_time,
  supersedes_record_id,
  payload,
  source_evidence,
  semantic_tags,
  notes
from public.vera_save_state_events
order by record_key, state_time desc, record_time desc, record_id desc;

comment on view public.vera_current_save_state is
  'Latest recorded event per save-state key. Retrieval does not itself refresh or renew the represented state.';