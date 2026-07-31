create extension if not exists pgcrypto;

create table public.vera_portable_bootstrap_requests (
  request_claim_id uuid primary key default gen_random_uuid(),
  request_key text not null unique check (request_key ~ '^[0-9a-f]{64}$'),
  input_digest text not null check (input_digest ~ '^[0-9a-f]{64}$'),
  command_version text not null,
  release_id text not null,
  manifest_digest text not null check (manifest_digest ~ '^[0-9a-f]{64}$'),
  project_template_id text not null,
  target_fingerprint text not null check (target_fingerprint ~ '^[0-9a-f]{64}$'),
  canonical_request text not null,
  project_instance_id uuid not null check ((get_byte(uuid_send(project_instance_id), 6)::integer >> 4) = 7),
  initial_state text not null check (initial_state in ('CANDIDATE_UNPERSISTED','BINDING_PENDING','DURABLY_BOUND','CONFLICTED','UNKNOWN')),
  record_time timestamptz not null default clock_timestamp()
);

create table public.vera_portable_bootstrap_events (
  event_id uuid primary key default gen_random_uuid(),
  request_claim_id uuid not null references public.vera_portable_bootstrap_requests(request_claim_id),
  attempt_id uuid not null,
  predecessor_event_id uuid references public.vera_portable_bootstrap_events(event_id),
  event_class text not null,
  prior_state text not null check (prior_state in ('CANDIDATE_UNPERSISTED','BINDING_PENDING','DURABLY_BOUND','CONFLICTED','UNKNOWN')),
  proposed_state text not null check (proposed_state in ('CANDIDATE_UNPERSISTED','BINDING_PENDING','DURABLY_BOUND','CONFLICTED','UNKNOWN')),
  event_time timestamptz,
  state_time timestamptz,
  effective_time timestamptz,
  observed_time timestamptz,
  record_time timestamptz not null default clock_timestamp(),
  temporal_precision text not null check (temporal_precision in ('EXACT','BOUNDED','APPROXIMATE','UNKNOWN')),
  authority_evidence jsonb not null default '[]'::jsonb,
  source_evidence jsonb not null default '[]'::jsonb,
  payload jsonb not null default '{}'::jsonb,
  check ((temporal_precision = 'UNKNOWN' and state_time is null and effective_time is null) or temporal_precision <> 'UNKNOWN')
);

create unique index vera_portable_bootstrap_one_successor_idx
  on public.vera_portable_bootstrap_events(predecessor_event_id)
  where predecessor_event_id is not null;
create index vera_portable_bootstrap_request_events_idx
  on public.vera_portable_bootstrap_events(request_claim_id, record_time desc);

create function public.block_vera_portable_bootstrap_mutation()
returns trigger language plpgsql as $$
begin
  raise exception 'portable bootstrap registry is append-only';
end;
$$;
create trigger vera_portable_bootstrap_requests_no_update before update or delete on public.vera_portable_bootstrap_requests
for each row execute function public.block_vera_portable_bootstrap_mutation();
create trigger vera_portable_bootstrap_events_no_update before update or delete on public.vera_portable_bootstrap_events
for each row execute function public.block_vera_portable_bootstrap_mutation();

create function public.claim_vera_portable_bootstrap_request(
  p_request_key text, p_input_digest text, p_command_version text, p_release_id text,
  p_manifest_digest text, p_project_template_id text, p_target_fingerprint text,
  p_canonical_request text, p_project_instance_id uuid, p_initial_state text
) returns public.vera_portable_bootstrap_requests
language plpgsql security definer set search_path = public, pg_temp as $$
declare current_row public.vera_portable_bootstrap_requests;
begin
  insert into public.vera_portable_bootstrap_requests(
    request_key,input_digest,command_version,release_id,manifest_digest,project_template_id,
    target_fingerprint,canonical_request,project_instance_id,initial_state)
  values (p_request_key,p_input_digest,p_command_version,p_release_id,p_manifest_digest,
    p_project_template_id,p_target_fingerprint,p_canonical_request,p_project_instance_id,p_initial_state)
  on conflict (request_key) do nothing returning * into current_row;
  if current_row.request_claim_id is null then
    select * into current_row from public.vera_portable_bootstrap_requests where request_key=p_request_key for share;
    if current_row.input_digest <> p_input_digest then
      raise exception 'REQUEST_ID_REUSE_CONFLICT' using errcode='23505';
    end if;
  end if;
  return current_row;
end;
$$;

create function public.append_vera_portable_bootstrap_event(
  p_request_claim_id uuid, p_attempt_id uuid, p_predecessor_event_id uuid,
  p_event_class text, p_prior_state text, p_proposed_state text,
  p_event_time timestamptz, p_state_time timestamptz, p_effective_time timestamptz,
  p_observed_time timestamptz, p_temporal_precision text,
  p_authority_evidence jsonb, p_source_evidence jsonb, p_payload jsonb
) returns public.vera_portable_bootstrap_events
language plpgsql security definer set search_path = public, pg_temp as $$
declare current_leaf uuid; result public.vera_portable_bootstrap_events;
begin
  perform 1 from public.vera_portable_bootstrap_requests where request_claim_id=p_request_claim_id for update;
  if not found then raise exception 'UNKNOWN_REQUEST_CLAIM' using errcode='23503'; end if;
  select event_id into current_leaf from public.vera_portable_bootstrap_events e
   where e.request_claim_id=p_request_claim_id and not exists(
     select 1 from public.vera_portable_bootstrap_events s where s.predecessor_event_id=e.event_id)
   order by e.record_time desc, e.event_id desc limit 1;
  if current_leaf is distinct from p_predecessor_event_id then
    raise exception 'STALE_OR_CONFLICTING_PREDECESSOR' using errcode='40001';
  end if;
  insert into public.vera_portable_bootstrap_events(
    request_claim_id,attempt_id,predecessor_event_id,event_class,prior_state,proposed_state,
    event_time,state_time,effective_time,observed_time,temporal_precision,
    authority_evidence,source_evidence,payload)
  values (p_request_claim_id,p_attempt_id,p_predecessor_event_id,p_event_class,p_prior_state,p_proposed_state,
    p_event_time,p_state_time,p_effective_time,p_observed_time,p_temporal_precision,
    coalesce(p_authority_evidence,'[]'),coalesce(p_source_evidence,'[]'),coalesce(p_payload,'{}'))
  returning * into result;
  return result;
end;
$$;

create view public.vera_portable_bootstrap_current with (security_invoker=true) as
select distinct on (r.request_claim_id) r.*, e.event_id, e.proposed_state as current_state,
  e.state_time, e.effective_time, e.record_time as event_record_time
from public.vera_portable_bootstrap_requests r
left join public.vera_portable_bootstrap_events e on e.request_claim_id=r.request_claim_id
 and not exists(select 1 from public.vera_portable_bootstrap_events s where s.predecessor_event_id=e.event_id)
order by r.request_claim_id, e.record_time desc nulls last, e.event_id desc;

alter table public.vera_portable_bootstrap_requests enable row level security;
alter table public.vera_portable_bootstrap_events enable row level security;
revoke all on public.vera_portable_bootstrap_requests from public, anon, authenticated;
revoke all on public.vera_portable_bootstrap_events from public, anon, authenticated;
revoke all on function public.claim_vera_portable_bootstrap_request(text,text,text,text,text,text,text,text,uuid,text) from public, anon, authenticated;
revoke all on function public.append_vera_portable_bootstrap_event(uuid,uuid,uuid,text,text,text,timestamptz,timestamptz,timestamptz,timestamptz,text,jsonb,jsonb,jsonb) from public, anon, authenticated;

comment on table public.vera_portable_bootstrap_requests is 'Append-only request claims for the portable bootstrap. Persistence is evidence, not consciousness, identity, memory, or authority.';
comment on table public.vera_portable_bootstrap_events is 'Append-only state-transition evidence. A visible receipt cannot self-certify durable binding or external effects.';
