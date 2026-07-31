create extension if not exists pgcrypto;
create function public.vera_bootstrap_sha256_text(p_value text)
returns text
language sql
immutable
strict
as $$
select encode(digest(convert_to(p_value, 'UTF8'), 'sha256'), 'hex');
$$;
create function public.vera_generate_uuid_v7()
returns uuid
language plpgsql
volatile
as $$
declare
v_bytes bytea := gen_random_bytes(16);
v_ms bigint := floor(extract(epoch from clock_timestamp()) * 1000)::bigint;
begin
v_bytes := set_byte(v_bytes, 0, ((v_ms >> 40) & 255)::integer);
v_bytes := set_byte(v_bytes, 1, ((v_ms >> 32) & 255)::integer);
v_bytes := set_byte(v_bytes, 2, ((v_ms >> 24) & 255)::integer);
v_bytes := set_byte(v_bytes, 3, ((v_ms >> 16) & 255)::integer);
v_bytes := set_byte(v_bytes, 4, ((v_ms >> 8) & 255)::integer);
v_bytes := set_byte(v_bytes, 5, (v_ms & 255)::integer);
v_bytes := set_byte(v_bytes, 6, ((get_byte(v_bytes, 6) & 15) | 112));
v_bytes := set_byte(v_bytes, 8, ((get_byte(v_bytes, 8) & 63) | 128));
return encode(v_bytes, 'hex')::uuid;
end;
$$;
create function public.vera_valid_target_evidence(p_value jsonb)
returns boolean
language plpgsql
immutable
as $$
begin
if jsonb_typeof(p_value) <> 'object' then return false; end if;
if (p_value - array['target_class','target_locator_digest','verifier_role','observed_at']) <> '{}'::jsonb then return false; end if;
if coalesce(p_value->>'target_class','') = '' then return false; end if;
if coalesce(p_value->>'target_locator_digest','') !~ '^[0-9a-f]{64}$' then return false; end if;
if p_value->>'verifier_role' <> 'workstream/project-architecture' then return false; end if;
perform (p_value->>'observed_at')::timestamptz;
return true;
exception when others then
return false;
end;
$$;
create function public.vera_valid_temporal_point(p_value jsonb)
returns boolean
language plpgsql
immutable
as $$
declare
v_precision text;
v_value timestamptz;
v_lower timestamptz;
v_upper timestamptz;
begin
if jsonb_typeof(p_value) <> 'object' then return false; end if;
if (p_value - array['precision','value','lower','upper']) <> '{}'::jsonb then return false; end if;
v_precision := p_value->>'precision';
if v_precision not in ('EXACT','BOUNDED','APPROXIMATE','UNKNOWN') then return false; end if;
if v_precision = 'UNKNOWN' then
return coalesce(p_value->'value','null'::jsonb) = 'null'::jsonb
and coalesce(p_value->'lower','null'::jsonb) = 'null'::jsonb
and coalesce(p_value->'upper','null'::jsonb) = 'null'::jsonb;
elsif v_precision in ('EXACT','APPROXIMATE') then
if coalesce(p_value->'value','null'::jsonb) = 'null'::jsonb then return false; end if;
if coalesce(p_value->'lower','null'::jsonb) <> 'null'::jsonb then return false; end if;
if coalesce(p_value->'upper','null'::jsonb) <> 'null'::jsonb then return false; end if;
v_value := (p_value->>'value')::timestamptz;
return v_value is not null;
else
if coalesce(p_value->'value','null'::jsonb) <> 'null'::jsonb then return false; end if;
if coalesce(p_value->'lower','null'::jsonb) = 'null'::jsonb then return false; end if;
if coalesce(p_value->'upper','null'::jsonb) = 'null'::jsonb then return false; end if;
v_lower := (p_value->>'lower')::timestamptz;
v_upper := (p_value->>'upper')::timestamptz;
return v_lower <= v_upper;
end if;
exception when others then
return false;
end;
$$;
create function public.vera_valid_temporal_evidence(p_value jsonb)
returns boolean
language sql
immutable
as $$
select jsonb_typeof(p_value) = 'object'
and (p_value - array['event_time','state_time','effective_time','observed_time']) = '{}'::jsonb
and p_value ?& array['event_time','state_time','effective_time','observed_time']
and public.vera_valid_temporal_point(p_value->'event_time')
and public.vera_valid_temporal_point(p_value->'state_time')
and public.vera_valid_temporal_point(p_value->'effective_time')
and public.vera_valid_temporal_point(p_value->'observed_time');
$$;
create function public.vera_valid_authority_evidence(p_value jsonb)
returns boolean
language plpgsql
immutable
as $$
declare
v_item jsonb;
begin
if jsonb_typeof(p_value) <> 'array' or jsonb_array_length(p_value) < 1 then return false; end if;
for v_item in select value from jsonb_array_elements(p_value)
loop
if jsonb_typeof(v_item) <> 'object' then return false; end if;
if (v_item - array['verifier_role','lease_id','repository','branch','base_sha','observed_at','operation']) <> '{}'::jsonb then return false; end if;
if v_item->>'verifier_role' <> 'workstream/project-architecture' then return false; end if;
if coalesce(v_item->>'lease_id','') = '' then return false; end if;
if v_item->>'repository' <> 'thebrazenbeard/vera' then return false; end if;
if coalesce(v_item->>'branch','') = '' then return false; end if;
if coalesce(v_item->>'base_sha','') !~ '^[0-9a-f]{40}$' then return false; end if;
if coalesce(v_item->>'operation','') = '' then return false; end if;
perform (v_item->>'observed_at')::timestamptz;
end loop;
return true;
exception when others then
return false;
end;
$$;
create function public.vera_valid_source_evidence(p_value jsonb)
returns boolean
language plpgsql
immutable
as $$
declare
v_item jsonb;
begin
if jsonb_typeof(p_value) <> 'array' or jsonb_array_length(p_value) < 1 then return false; end if;
for v_item in select value from jsonb_array_elements(p_value)
loop
if jsonb_typeof(v_item) <> 'object' then return false; end if;
if (v_item - array['release_commit','path_set_sha256','package_sha256','validation_run_id','observed_at']) <> '{}'::jsonb then return false; end if;
if coalesce(v_item->>'release_commit','') !~ '^[0-9a-f]{40}$' then return false; end if;
if coalesce(v_item->>'path_set_sha256','') !~ '^[0-9a-f]{64}$' then return false; end if;
if coalesce(v_item->>'package_sha256','') !~ '^[0-9a-f]{64}$' then return false; end if;
if coalesce(v_item->>'validation_run_id','') = '' then return false; end if;
perform (v_item->>'observed_at')::timestamptz;
end loop;
return true;
exception when others then
return false;
end;
$$;
create table public.vera_portable_bootstrap_requests (
request_claim_id uuid primary key default gen_random_uuid(),
request_key text not null unique check (request_key ~ '^[0-9a-f]{64}$'),
input_digest text not null check (input_digest ~ '^[0-9a-f]{64}$'),
command_version text not null check (command_version = 'V1'),
release_id text not null,
manifest_digest text not null check (manifest_digest ~ '^[0-9a-f]{64}$'),
project_template_id text not null,
target_fingerprint text not null check (target_fingerprint ~ '^[0-9a-f]{64}$'),
target_evidence jsonb not null check (public.vera_valid_target_evidence(target_evidence)),
canonical_request text not null check (canonical_request = 'VERA::INITIALIZE::PORTABLE_PROJECT_V1'),
source_repository text not null check (source_repository = 'thebrazenbeard/vera'),
source_base_commit text not null check (source_base_commit ~ '^[0-9a-f]{40}$'),
requested_mode text not null check (requested_mode in ('DRY_RUN_VERIFY_ONLY','CREATE_OR_VERIFY')),
project_instance_id uuid not null unique default public.vera_generate_uuid_v7()
check ((get_byte(uuid_send(project_instance_id), 6)::integer >> 4) = 7),
claim_record_time timestamptz not null default clock_timestamp()
);
create table public.vera_portable_bootstrap_events (
event_id uuid primary key default gen_random_uuid(),
request_claim_id uuid not null references public.vera_portable_bootstrap_requests(request_claim_id),
attempt_id uuid not null,
predecessor_event_id uuid references public.vera_portable_bootstrap_events(event_id),
event_class text not null,
prior_state text not null check (prior_state in ('UNISSUED','CLAIMED','BINDING_PENDING','BINDING_VERIFIED','CONFLICTED','FAILED_CLOSED')),
proposed_state text not null check (proposed_state in ('CLAIMED','BINDING_PENDING','BINDING_VERIFIED','BINDING_COMMITTED','CONFLICTED','FAILED_CLOSED')),
temporal_evidence jsonb not null check (public.vera_valid_temporal_evidence(temporal_evidence)),
authority_evidence jsonb not null default '[]'::jsonb,
source_evidence jsonb not null default '[]'::jsonb,
payload jsonb not null default '{}'::jsonb,
record_time timestamptz not null default clock_timestamp()
);
create table public.vera_portable_bootstrap_bindings (
binding_id uuid primary key default gen_random_uuid(),
request_claim_id uuid not null unique references public.vera_portable_bootstrap_requests(request_claim_id),
project_instance_id uuid not null unique,
binding_event_id uuid not null unique references public.vera_portable_bootstrap_events(event_id),
authority_evidence jsonb not null check (public.vera_valid_authority_evidence(authority_evidence)),
source_evidence jsonb not null check (public.vera_valid_source_evidence(source_evidence)),
authority_evidence_digest text not null check (authority_evidence_digest ~ '^[0-9a-f]{64}$'),
source_evidence_digest text not null check (source_evidence_digest ~ '^[0-9a-f]{64}$'),
binding_record_time timestamptz not null default clock_timestamp()
);
create unique index vera_portable_bootstrap_one_initial_event_idx
on public.vera_portable_bootstrap_events(request_claim_id)
where predecessor_event_id is null;
create unique index vera_portable_bootstrap_one_successor_idx
on public.vera_portable_bootstrap_events(predecessor_event_id)
where predecessor_event_id is not null;
create index vera_portable_bootstrap_request_events_idx
on public.vera_portable_bootstrap_events(request_claim_id, record_time, event_id);
create function public.block_vera_portable_bootstrap_mutation()
returns trigger
language plpgsql
as $$
begin
raise exception 'portable bootstrap registry is append-only';
end;
$$;
create trigger vera_portable_bootstrap_requests_no_update
before update or delete on public.vera_portable_bootstrap_requests
for each row execute function public.block_vera_portable_bootstrap_mutation();
create trigger vera_portable_bootstrap_events_no_update
before update or delete on public.vera_portable_bootstrap_events
for each row execute function public.block_vera_portable_bootstrap_mutation();
create trigger vera_portable_bootstrap_bindings_no_update
before update or delete on public.vera_portable_bootstrap_bindings
for each row execute function public.block_vera_portable_bootstrap_mutation();
create function public.claim_vera_portable_bootstrap_request(
p_command_version text,
p_release_id text,
p_manifest_digest text,
p_project_template_id text,
p_target_evidence jsonb,
p_canonical_request text,
p_source_repository text,
p_source_base_commit text,
p_requested_mode text
) returns public.vera_portable_bootstrap_requests
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
v_target_fingerprint text;
v_request_key text;
v_input_digest text;
v_row public.vera_portable_bootstrap_requests;
begin
if not public.vera_valid_target_evidence(p_target_evidence) then
raise exception 'INVALID_TARGET_EVIDENCE' using errcode='22023';
end if;
if p_command_version <> 'V1'
or p_canonical_request <> 'VERA::INITIALIZE::PORTABLE_PROJECT_V1'
or p_source_repository <> 'thebrazenbeard/vera'
or p_manifest_digest !~ '^[0-9a-f]{64}$'
or p_source_base_commit !~ '^[0-9a-f]{40}$'
or p_requested_mode not in ('DRY_RUN_VERIFY_ONLY','CREATE_OR_VERIFY') then
raise exception 'INVALID_IMMUTABLE_REQUEST' using errcode='22023';
end if;
v_target_fingerprint := public.vera_bootstrap_sha256_text(p_target_evidence::text);
v_request_key := public.vera_bootstrap_sha256_text(
jsonb_build_array(p_command_version, p_project_template_id, v_target_fingerprint, p_canonical_request)::text
);
v_input_digest := public.vera_bootstrap_sha256_text(
jsonb_build_array(
p_command_version, p_release_id, p_manifest_digest, p_project_template_id,
v_target_fingerprint, p_canonical_request, p_source_repository,
p_source_base_commit, p_requested_mode
)::text
);
insert into public.vera_portable_bootstrap_requests(
request_key,input_digest,command_version,release_id,manifest_digest,project_template_id,
target_fingerprint,target_evidence,canonical_request,source_repository,source_base_commit,requested_mode
) values (
v_request_key,v_input_digest,p_command_version,p_release_id,p_manifest_digest,p_project_template_id,
v_target_fingerprint,p_target_evidence,p_canonical_request,p_source_repository,p_source_base_commit,p_requested_mode
)
on conflict (request_key) do nothing
returning * into v_row;
if v_row.request_claim_id is null then
select * into v_row
from public.vera_portable_bootstrap_requests
where request_key = v_request_key
for share;
if v_row.input_digest <> v_input_digest
or v_row.command_version <> p_command_version
or v_row.release_id <> p_release_id
or v_row.manifest_digest <> p_manifest_digest
or v_row.project_template_id <> p_project_template_id
or v_row.target_fingerprint <> v_target_fingerprint
or v_row.target_evidence <> p_target_evidence
or v_row.canonical_request <> p_canonical_request
or v_row.source_repository <> p_source_repository
or v_row.source_base_commit <> p_source_base_commit
or v_row.requested_mode <> p_requested_mode then
raise exception 'REQUEST_ID_REUSE_CONFLICT' using errcode='23505';
end if;
end if;
return v_row;
end;
$$;
create function public.append_vera_portable_bootstrap_event(
p_request_claim_id uuid,
p_attempt_id uuid,
p_predecessor_event_id uuid,
p_event_class text,
p_prior_state text,
p_proposed_state text,
p_temporal_evidence jsonb,
p_authority_evidence jsonb,
p_source_evidence jsonb,
p_payload jsonb
) returns public.vera_portable_bootstrap_events
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
v_leaf public.vera_portable_bootstrap_events;
v_result public.vera_portable_bootstrap_events;
v_allowed boolean := false;
begin
perform 1 from public.vera_portable_bootstrap_requests
where request_claim_id = p_request_claim_id for update;
if not found then raise exception 'UNKNOWN_REQUEST_CLAIM' using errcode='23503'; end if;
select e.* into v_leaf
from public.vera_portable_bootstrap_events e
where e.request_claim_id = p_request_claim_id
and not exists (
select 1 from public.vera_portable_bootstrap_events s
where s.predecessor_event_id = e.event_id
)
order by e.record_time desc, e.event_id desc
limit 1;
if v_leaf.event_id is null then
if p_predecessor_event_id is not null or p_prior_state <> 'UNISSUED' then
raise exception 'STALE_OR_CONFLICTING_PREDECESSOR' using errcode='40001';
end if;
v_allowed := p_event_class = 'REQUEST_CLAIMED' and p_proposed_state = 'CLAIMED';
else
if p_predecessor_event_id is distinct from v_leaf.event_id then
raise exception 'STALE_OR_CONFLICTING_PREDECESSOR' using errcode='40001';
end if;
if p_prior_state <> v_leaf.proposed_state then
raise exception 'PRIOR_STATE_MISMATCH' using errcode='22023';
end if;
v_allowed :=
(p_prior_state = 'CLAIMED' and p_proposed_state = 'BINDING_PENDING' and p_event_class = 'BINDING_STARTED')
or (p_prior_state = 'BINDING_PENDING' and p_proposed_state = 'BINDING_VERIFIED' and p_event_class = 'BINDING_EVIDENCE_VERIFIED')
or (p_prior_state in ('CLAIMED','BINDING_PENDING') and p_proposed_state = 'CONFLICTED' and p_event_class = 'CONFLICT_RECORDED')
or (p_prior_state in ('CLAIMED','BINDING_PENDING') and p_proposed_state = 'FAILED_CLOSED' and p_event_class = 'FAILURE_RECORDED');
end if;
if not v_allowed or p_proposed_state = 'BINDING_COMMITTED' then
raise exception 'ILLEGAL_BOOTSTRAP_TRANSITION' using errcode='22023';
end if;
if not public.vera_valid_temporal_evidence(p_temporal_evidence) then
raise exception 'INVALID_TEMPORAL_EVIDENCE' using errcode='22023';
end if;
if p_proposed_state = 'BINDING_VERIFIED' then
if not public.vera_valid_authority_evidence(coalesce(p_authority_evidence,'[]'::jsonb))
or not public.vera_valid_source_evidence(coalesce(p_source_evidence,'[]'::jsonb)) then
raise exception 'VERIFIER_EVIDENCE_REQUIRED' using errcode='22023';
end if;
end if;
insert into public.vera_portable_bootstrap_events(
request_claim_id,attempt_id,predecessor_event_id,event_class,prior_state,proposed_state,
temporal_evidence,authority_evidence,source_evidence,payload
) values (
p_request_claim_id,p_attempt_id,p_predecessor_event_id,p_event_class,p_prior_state,p_proposed_state,
p_temporal_evidence,coalesce(p_authority_evidence,'[]'::jsonb),coalesce(p_source_evidence,'[]'::jsonb),coalesce(p_payload,'{}'::jsonb)
) returning * into v_result;
return v_result;
end;
$$;
create function public.commit_vera_portable_bootstrap_binding(
p_request_claim_id uuid,
p_attempt_id uuid,
p_verified_event_id uuid
) returns public.vera_portable_bootstrap_bindings
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
v_request public.vera_portable_bootstrap_requests;
v_leaf public.vera_portable_bootstrap_events;
v_commit_event public.vera_portable_bootstrap_events;
v_binding public.vera_portable_bootstrap_bindings;
begin
select * into v_request
from public.vera_portable_bootstrap_requests
where request_claim_id = p_request_claim_id
for update;
if v_request.request_claim_id is null then
raise exception 'UNKNOWN_REQUEST_CLAIM' using errcode='23503';
end if;
select e.* into v_leaf
from public.vera_portable_bootstrap_events e
where e.request_claim_id = p_request_claim_id
and not exists (
select 1 from public.vera_portable_bootstrap_events s
where s.predecessor_event_id = e.event_id
)
order by e.record_time desc, e.event_id desc
limit 1;
if v_leaf.event_id is distinct from p_verified_event_id
or v_leaf.proposed_state <> 'BINDING_VERIFIED'
or not public.vera_valid_authority_evidence(v_leaf.authority_evidence)
or not public.vera_valid_source_evidence(v_leaf.source_evidence) then
raise exception 'UNVERIFIED_BINDING_CANNOT_COMMIT' using errcode='22023';
end if;
if exists(select 1 from public.vera_portable_bootstrap_bindings where request_claim_id = p_request_claim_id) then
raise exception 'BINDING_ALREADY_COMMITTED' using errcode='23505';
end if;
insert into public.vera_portable_bootstrap_events(
request_claim_id,attempt_id,predecessor_event_id,event_class,prior_state,proposed_state,
temporal_evidence,authority_evidence,source_evidence,payload
) values (
p_request_claim_id,p_attempt_id,v_leaf.event_id,'BINDING_COMMITTED',
'BINDING_VERIFIED','BINDING_COMMITTED',v_leaf.temporal_evidence,
v_leaf.authority_evidence,v_leaf.source_evidence,'{}'::jsonb
) returning * into v_commit_event;
insert into public.vera_portable_bootstrap_bindings(
request_claim_id,project_instance_id,binding_event_id,authority_evidence,source_evidence,
authority_evidence_digest,source_evidence_digest
) values (
p_request_claim_id,v_request.project_instance_id,v_commit_event.event_id,
v_leaf.authority_evidence,v_leaf.source_evidence,
public.vera_bootstrap_sha256_text(v_leaf.authority_evidence::text),
public.vera_bootstrap_sha256_text(v_leaf.source_evidence::text)
) returning * into v_binding;
return v_binding;
end;
$$;
create function public.read_vera_portable_bootstrap_binding(
p_request_key text,
p_input_digest text,
p_project_instance_id uuid
) returns table (
request_key text,
input_digest text,
project_instance_id uuid,
binding_event_id uuid,
binding_record_time timestamptz,
retrieval_time timestamptz,
readback_nonce uuid,
source_evidence_digest text,
authority_evidence_digest text
)
language sql
security definer
set search_path = public, pg_temp
as $$
select r.request_key, r.input_digest, b.project_instance_id, b.binding_event_id,
b.binding_record_time, clock_timestamp(), gen_random_uuid(),
b.source_evidence_digest, b.authority_evidence_digest
from public.vera_portable_bootstrap_requests r
join public.vera_portable_bootstrap_bindings b using (request_claim_id)
where r.request_key = p_request_key
and r.input_digest = p_input_digest
and b.project_instance_id = p_project_instance_id;
$$;
create view public.vera_portable_bootstrap_current with (security_invoker=true) as
select r.request_claim_id, r.request_key, r.input_digest, r.project_template_id,
b.project_instance_id, 'DURABLY_BOUND'::text as current_state,
b.binding_event_id, b.binding_record_time,
b.source_evidence_digest, b.authority_evidence_digest
from public.vera_portable_bootstrap_requests r
join public.vera_portable_bootstrap_bindings b using (request_claim_id);
alter table public.vera_portable_bootstrap_requests enable row level security;
alter table public.vera_portable_bootstrap_events enable row level security;
alter table public.vera_portable_bootstrap_bindings enable row level security;
revoke all on public.vera_portable_bootstrap_requests from public, anon, authenticated;
revoke all on public.vera_portable_bootstrap_events from public, anon, authenticated;
revoke all on public.vera_portable_bootstrap_bindings from public, anon, authenticated;
revoke all on public.vera_portable_bootstrap_current from public, anon, authenticated;
revoke all on function public.claim_vera_portable_bootstrap_request(text,text,text,text,jsonb,text,text,text,text) from public, anon, authenticated;
revoke all on function public.append_vera_portable_bootstrap_event(uuid,uuid,uuid,text,text,text,jsonb,jsonb,jsonb,jsonb) from public, anon, authenticated;
revoke all on function public.commit_vera_portable_bootstrap_binding(uuid,uuid,uuid) from public, anon, authenticated;
revoke all on function public.read_vera_portable_bootstrap_binding(text,text,uuid) from public, anon, authenticated;
comment on table public.vera_portable_bootstrap_requests is
'Server-bound request claims. Persistence is evidence, not consciousness, memory, identity, or autonomous authority.';
comment on table public.vera_portable_bootstrap_events is
'Append-only attempt and verifier evidence. Candidate and pending events are not durable project identity.';
comment on table public.vera_portable_bootstrap_bindings is
'Verified committed project-instance bindings. DURABLY_BOUND is reportable only after separate exact read-back.';
