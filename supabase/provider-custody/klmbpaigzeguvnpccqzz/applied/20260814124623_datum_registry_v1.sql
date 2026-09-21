alter table public.vera_context_events_v3
  add column if not exists datum_expires_at timestamptz,
  add column if not exists datum_verified_at timestamptz;

alter table public.vera_context_events_v3
  drop constraint if exists vera_context_events_v3_record_type_check;

alter table public.vera_context_events_v3
  add constraint vera_context_events_v3_record_type_check
  check (record_type = any (array[
    'FACT','UNVERIFIED_DATUM','VERIFIED_DATUM','USER_STATEMENT','MODEL_OUTPUT',
    'PERSONA_CONFIG','RELATIONAL_FRAME','PREFERENCE','DECISION','CORRECTION',
    'BEHAVIORAL_COMMITMENT','BOUNDARY','PERMISSION','TASK_STATE','TECHNICAL_RESULT',
    'PROVENANCE','HYPOTHESIS','INTERPRETATION','EVALUATION','LEDGER_SNAPSHOT',
    'TOMBSTONE','OTHER'
  ]));

alter table public.vera_context_events_v3
  drop constraint if exists vera_context_events_v3_epistemic_status_check;

alter table public.vera_context_events_v3
  add constraint vera_context_events_v3_epistemic_status_check
  check (epistemic_status = any (array[
    'DIRECT_USER_STATEMENT','OBSERVED_TOOL_RESULT','DOCUMENTED_SOURCE',
    'MULTI_SOURCE_VERIFIED','MODEL_GENERATED_CLAIM','SUPPORTED_INFERENCE',
    'HYPOTHESIS','DISPUTED','REJECTED','UNAVAILABLE'
  ]));

create or replace function public.vera_validate_datum_insert_v1()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
declare
  independent_groups integer;
  invalid_evidence integer;
begin
  if new.record_type = 'FACT' then
    raise exception 'FACT is legacy. Use UNVERIFIED_DATUM or VERIFIED_DATUM.';
  end if;

  if new.record_type = 'UNVERIFIED_DATUM' then
    if new.datum_verified_at is not null then
      raise exception 'UNVERIFIED_DATUM cannot have datum_verified_at';
    end if;
    if new.datum_expires_at is null or new.datum_expires_at <= new.record_time then
      raise exception 'UNVERIFIED_DATUM requires a future datum_expires_at';
    end if;
  elsif new.record_type = 'VERIFIED_DATUM' then
    if new.datum_verified_at is null then
      raise exception 'VERIFIED_DATUM requires datum_verified_at';
    end if;
    if new.epistemic_status <> 'MULTI_SOURCE_VERIFIED' then
      raise exception 'VERIFIED_DATUM requires epistemic_status MULTI_SOURCE_VERIFIED';
    end if;
    if jsonb_typeof(new.source_evidence) <> 'array' or jsonb_array_length(new.source_evidence) < 2 then
      raise exception 'VERIFIED_DATUM requires at least two evidence sources';
    end if;

    select count(distinct nullif(btrim(e->>'independence_group'),''))
      into independent_groups
      from jsonb_array_elements(new.source_evidence) e
      where jsonb_typeof(e) = 'object';

    select count(*)
      into invalid_evidence
      from jsonb_array_elements(new.source_evidence) e
      where jsonb_typeof(e) <> 'object'
         or nullif(btrim(e->>'source_ref'),'') is null
         or nullif(btrim(e->>'independence_group'),'') is null
         or jsonb_typeof(e->'supports') <> 'boolean'
         or e->'supports' <> 'true'::jsonb;

    if independent_groups < 2 then
      raise exception 'VERIFIED_DATUM requires at least two independent source groups';
    end if;
    if invalid_evidence > 0 then
      raise exception 'Each VERIFIED_DATUM evidence item requires source_ref, independence_group, and supports=true';
    end if;
  end if;

  return new;
end;
$$;

drop trigger if exists vera_validate_datum_insert_v1 on public.vera_context_events_v3;
create trigger vera_validate_datum_insert_v1
before insert on public.vera_context_events_v3
for each row execute function public.vera_validate_datum_insert_v1();

create index if not exists vera_context_v3_verified_datum_lookup_idx
  on public.vera_context_events_v3
  (project_id, branch_id, record_key, state_time desc, record_time desc, record_id desc)
  where record_type = 'VERIFIED_DATUM' and lifecycle_status = 'CURRENT';

create index if not exists vera_context_v3_unverified_datum_expiry_idx
  on public.vera_context_events_v3
  (datum_expires_at, project_id, branch_id, record_key)
  where record_type = 'UNVERIFIED_DATUM' and lifecycle_status = 'CURRENT';

create or replace view public.vera_active_unverified_datum_v1 as
select u.*
from public.vera_context_events_v3 u
where u.record_type = 'UNVERIFIED_DATUM'
  and u.lifecycle_status = 'CURRENT'
  and u.datum_expires_at > now()
  and not exists (
    select 1
    from public.vera_context_events_v3 v
    where v.record_type = 'VERIFIED_DATUM'
      and (
        v.supersedes_record_id = u.record_id
        or v.payload->>'candidate_record_id' = u.record_id::text
      )
  );

create or replace view public.vera_verified_datum_heads_v1 as
select v.*
from public.vera_context_events_v3 v
where v.record_type = 'VERIFIED_DATUM'
  and v.lifecycle_status = 'CURRENT'
  and not exists (
    select 1
    from public.vera_context_events_v3 s
    where s.record_type = 'VERIFIED_DATUM'
      and s.supersedes_record_id = v.record_id
  );

create or replace function public.vera_get_verified_datum_v1(
  p_record_key text,
  p_project_id text default 'vera-reciprocal-agency-environment',
  p_branch_id text default 'chatgpt-project-current'
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = public, pg_temp
as $$
declare
  n integer;
  one_row jsonb;
  all_rows jsonb;
begin
  select count(*), jsonb_agg(to_jsonb(h) order by h.state_time desc, h.record_time desc, h.record_id desc)
    into n, all_rows
    from public.vera_verified_datum_heads_v1 h
    where h.project_id = p_project_id
      and h.branch_id = p_branch_id
      and h.record_key = p_record_key;

  if n = 0 then
    return jsonb_build_object('status','UNKNOWN','record_key',p_record_key);
  elsif n = 1 then
    one_row := all_rows->0;
    return jsonb_build_object('status','CURRENT','record_key',p_record_key,'datum',one_row);
  else
    return jsonb_build_object('status','CONFLICTED','record_key',p_record_key,'heads',all_rows);
  end if;
end;
$$;

create or replace function public.vera_register_unverified_datum_v1(
  p_record_key text,
  p_statement text,
  p_source_actor text,
  p_epistemic_status text,
  p_source_evidence jsonb default '[]'::jsonb,
  p_payload jsonb default '{}'::jsonb,
  p_semantic_tags jsonb default '{}'::jsonb,
  p_limitations jsonb default '[]'::jsonb,
  p_project_id text default 'vera-reciprocal-agency-environment',
  p_branch_id text default 'chatgpt-project-current',
  p_decay_after interval default interval '30 days'
)
returns uuid
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
declare
  rid uuid;
begin
  if nullif(btrim(p_record_key),'') is null or nullif(btrim(p_statement),'') is null then
    raise exception 'record_key and statement are required';
  end if;
  if p_decay_after is null or p_decay_after <= interval '0 seconds' then
    raise exception 'p_decay_after must be positive';
  end if;

  insert into public.vera_context_events_v3 (
    project_id, branch_id, record_key, record_type, statement,
    lifecycle_status, epistemic_status, source_actor, privacy_scope,
    payload, source_evidence, semantic_tags, limitations,
    datum_expires_at, datum_verified_at
  ) values (
    p_project_id, p_branch_id, p_record_key, 'UNVERIFIED_DATUM', p_statement,
    'CURRENT', p_epistemic_status, p_source_actor, 'PROJECT',
    coalesce(p_payload,'{}'::jsonb), coalesce(p_source_evidence,'[]'::jsonb),
    coalesce(p_semantic_tags,'{}'::jsonb) || jsonb_build_object(
      'datum_state','UNVERIFIED',
      'decay_policy','TIMEBOXED_NONDESTRUCTIVE_V1'
    ),
    coalesce(p_limitations,'[]'::jsonb),
    now() + p_decay_after, null
  )
  returning record_id into rid;

  return rid;
end;
$$;

create or replace function public.vera_promote_verified_datum_v1(
  p_unverified_record_id uuid,
  p_source_evidence jsonb,
  p_verified_statement text default null,
  p_verified_payload jsonb default null,
  p_supersedes_verified_record_id uuid default null,
  p_limitations jsonb default null
)
returns uuid
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
declare
  c public.vera_context_events_v3%rowtype;
  rid uuid;
  head_count integer;
  sole_head uuid;
  existing_promoted uuid;
begin
  select * into c
  from public.vera_context_events_v3
  where record_id = p_unverified_record_id
    and record_type = 'UNVERIFIED_DATUM';

  if not found then
    raise exception 'Unverified datum % not found', p_unverified_record_id;
  end if;

  if c.datum_expires_at <= now() then
    raise exception 'Unverified datum % has decayed; register a fresh candidate before verification', p_unverified_record_id;
  end if;

  select v.record_id into existing_promoted
  from public.vera_context_events_v3 v
  where v.record_type = 'VERIFIED_DATUM'
    and (v.supersedes_record_id = c.record_id or v.payload->>'candidate_record_id' = c.record_id::text)
  order by v.record_time desc
  limit 1;

  if existing_promoted is not null then
    return existing_promoted;
  end if;

  select count(*), min(h.record_id)
    into head_count, sole_head
    from public.vera_verified_datum_heads_v1 h
    where h.project_id = c.project_id
      and h.branch_id = c.branch_id
      and h.record_key = c.record_key;

  if head_count > 1 then
    raise exception 'Verified datum key % is already conflicted; reconcile existing heads before promotion', c.record_key;
  elsif head_count = 1 then
    if p_supersedes_verified_record_id is null or p_supersedes_verified_record_id <> sole_head then
      raise exception 'Verified datum key % already has a current head; explicit supersession of % is required', c.record_key, sole_head;
    end if;
  elsif p_supersedes_verified_record_id is not null then
    raise exception 'No current verified head exists for key %, so p_supersedes_verified_record_id must be null', c.record_key;
  end if;

  insert into public.vera_context_events_v3 (
    project_id, branch_id, record_key, record_type, statement,
    lifecycle_status, epistemic_status, source_actor, privacy_scope,
    state_time, supersedes_record_id, payload, source_evidence,
    semantic_tags, limitations, datum_expires_at, datum_verified_at
  ) values (
    c.project_id, c.branch_id, c.record_key, 'VERIFIED_DATUM',
    coalesce(nullif(btrim(p_verified_statement),''), c.statement),
    'CURRENT', 'MULTI_SOURCE_VERIFIED', 'SYSTEM', c.privacy_scope,
    now(), coalesce(p_supersedes_verified_record_id, c.record_id),
    coalesce(p_verified_payload, c.payload) || jsonb_build_object('candidate_record_id', c.record_id::text),
    p_source_evidence,
    c.semantic_tags || jsonb_build_object(
      'datum_state','VERIFIED',
      'verification_rule','TWO_INDEPENDENT_SOURCES_V1'
    ),
    coalesce(p_limitations, c.limitations),
    null, now()
  )
  returning record_id into rid;

  return rid;
end;
$$;

comment on column public.vera_context_events_v3.datum_expires_at is
  'Decay boundary for UNVERIFIED_DATUM. Expired rows remain audit history but leave the active verification queue.';
comment on column public.vera_context_events_v3.datum_verified_at is
  'Time at which a VERIFIED_DATUM completed the configured verification rule.';
comment on function public.vera_get_verified_datum_v1(text,text,text) is
  'Fast governed lookup of current verified datum heads by semantic record_key and scope. Returns CURRENT, CONFLICTED, or UNKNOWN.';

insert into public.vera_context_events_v3 (
  project_id, branch_id, record_key, record_type, statement,
  lifecycle_status, epistemic_status, source_actor, privacy_scope,
  event_time, state_time, supersedes_record_id, payload,
  source_evidence, semantic_tags, limitations, notes,
  datum_expires_at, datum_verified_at
)
select
  f.project_id, f.branch_id, f.record_key, 'UNVERIFIED_DATUM', f.statement,
  'CURRENT', f.epistemic_status, f.source_actor, f.privacy_scope,
  f.event_time, now(), f.record_id,
  f.payload || jsonb_build_object('legacy_fact_record_id', f.record_id::text),
  f.source_evidence,
  f.semantic_tags || jsonb_build_object(
    'datum_state','UNVERIFIED',
    'legacy_fact_reclassified',true,
    'decay_policy','TIMEBOXED_NONDESTRUCTIVE_V1'
  ),
  f.limitations,
  'Successor created by datum_registry_v1; legacy FACT row retained as historical provenance.',
  now() + interval '30 days', null
from public.vera_context_events_v3 f
where f.record_type = 'FACT'
  and not exists (
    select 1 from public.vera_context_events_v3 d
    where d.supersedes_record_id = f.record_id
      and d.record_type in ('UNVERIFIED_DATUM','VERIFIED_DATUM')
  );