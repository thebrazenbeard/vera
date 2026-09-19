-- Replace the provisional expiry/unverified model with unified DATUM + verification state.

drop view if exists public.vera_active_unverified_datum_v1;
drop view if exists public.vera_verified_datum_heads_v1;
drop function if exists public.vera_get_verified_datum_v1(text,text,text);
drop function if exists public.vera_promote_verified_datum_v1(uuid,jsonb,text,jsonb,uuid,jsonb);
drop function if exists public.vera_register_unverified_datum_v1(text,text,text,text,jsonb,jsonb,jsonb,jsonb,text,text,interval);
drop trigger if exists vera_validate_datum_insert_v1 on public.vera_context_events_v3;
drop function if exists public.vera_validate_datum_insert_v1();
drop view if exists public.vera_current_context_v3;

alter table public.vera_context_events_v3
  add column if not exists verification_status text,
  add column if not exists datum_scope text,
  add column if not exists datum_index_tags text[] not null default '{}'::text[],
  add column if not exists last_referenced_at timestamptz;

-- Temporarily allow both v1 and v2 datum record types for migration.
alter table public.vera_context_events_v3 drop constraint if exists vera_context_events_v3_record_type_check;
alter table public.vera_context_events_v3 add constraint vera_context_events_v3_record_type_check
check (record_type = any (array[
  'FACT','UNVERIFIED_DATUM','VERIFIED_DATUM','DATUM','USER_STATEMENT','MODEL_OUTPUT','PERSONA_CONFIG',
  'RELATIONAL_FRAME','PREFERENCE','DECISION','CORRECTION','BEHAVIORAL_COMMITMENT','BOUNDARY','PERMISSION',
  'TASK_STATE','TECHNICAL_RESULT','PROVENANCE','HYPOTHESIS','INTERPRETATION','EVALUATION','LEDGER_SNAPSHOT','TOMBSTONE','OTHER'
]::text[]));

update public.vera_context_events_v3
set record_type = 'DATUM',
    verification_status = 'VERIFYING',
    supersedes_record_id = null,
    datum_scope = case record_key
      when 'platform.chatgpt.personalization.character_limit'
        then 'ChatGPT Personalization instructions character-limit behavior for the applicable account tier and product surface.'
      when 'platform.chatgpt.project_instructions.character_limit'
        then 'ChatGPT Project Instructions character-limit behavior for the applicable account tier and product surface.'
      else coalesce(nullif(payload->>'scope',''), 'Applicability scope requires verification.')
    end,
    datum_index_tags = case record_key
      when 'platform.chatgpt.personalization.character_limit'
        then array['chatgpt','parameter','character_limit','personalization']::text[]
      when 'platform.chatgpt.project_instructions.character_limit'
        then array['chatgpt','parameter','character_limit','project_instructions']::text[]
      else '{}'::text[]
    end,
    semantic_tags = (semantic_tags - 'datum_state' - 'decay_policy') || jsonb_build_object('datum_model','V2')
where record_type = 'UNVERIFIED_DATUM';

-- No production VERIFIED_DATUM rows existed at migration time, but keep conversion deterministic if one appears.
update public.vera_context_events_v3
set record_type = 'DATUM',
    verification_status = 'VERIFIED',
    datum_scope = coalesce(nullif(payload->>'scope',''), 'Applicability scope inherited from the verified record; refine when next superseded.'),
    datum_index_tags = coalesce(datum_index_tags,'{}'::text[]),
    last_referenced_at = null,
    semantic_tags = (semantic_tags - 'datum_state' - 'decay_policy') || jsonb_build_object('datum_model','V2')
where record_type = 'VERIFIED_DATUM';

drop index if exists public.vera_context_v3_unverified_datum_expiry_idx;
alter table public.vera_context_events_v3 drop column if exists datum_expires_at;

-- Final record type vocabulary: DATUM is the only live datum type. FACT remains only for immutable legacy rows.
alter table public.vera_context_events_v3 drop constraint if exists vera_context_events_v3_record_type_check;
alter table public.vera_context_events_v3 add constraint vera_context_events_v3_record_type_check
check (record_type = any (array[
  'FACT','DATUM','USER_STATEMENT','MODEL_OUTPUT','PERSONA_CONFIG','RELATIONAL_FRAME','PREFERENCE','DECISION',
  'CORRECTION','BEHAVIORAL_COMMITMENT','BOUNDARY','PERMISSION','TASK_STATE','TECHNICAL_RESULT','PROVENANCE',
  'HYPOTHESIS','INTERPRETATION','EVALUATION','LEDGER_SNAPSHOT','TOMBSTONE','OTHER'
]::text[]));

alter table public.vera_context_events_v3 drop constraint if exists vera_context_events_v3_verification_status_check;
alter table public.vera_context_events_v3 add constraint vera_context_events_v3_verification_status_check
check (
  (record_type = 'DATUM' and verification_status = any (array['VERIFYING','VERIFIED','UNVERIFIABLE','REJECTED']::text[]))
  or (record_type <> 'DATUM' and verification_status is null)
);

create or replace function public.vera_validate_datum_v2()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
declare
  independent_groups integer;
  invalid_evidence integer;
  parent_row public.vera_context_events_v3%rowtype;
begin
  if tg_op = 'INSERT' and new.record_type = 'FACT' then
    raise exception 'FACT is legacy. Use record_type DATUM with verification_status.';
  end if;
  if new.record_type <> 'DATUM' then
    return new;
  end if;

  if nullif(btrim(new.statement),'') is null then raise exception 'DATUM requires a non-empty datum statement'; end if;
  if nullif(btrim(new.datum_scope),'') is null then raise exception 'DATUM requires a non-empty scope'; end if;
  if new.last_referenced_at is not null and new.last_referenced_at < new.record_time then
    raise exception 'last_referenced_at cannot precede datum creation';
  end if;

  if new.verification_status = 'VERIFIED' then
    if new.datum_verified_at is null then raise exception 'VERIFIED datum requires datum_verified_at'; end if;
    if new.last_referenced_at is not null then raise exception 'VERIFIED datum does not track last_referenced_at'; end if;
    if new.epistemic_status <> 'MULTI_SOURCE_VERIFIED' then raise exception 'VERIFIED datum requires epistemic_status MULTI_SOURCE_VERIFIED'; end if;
    if jsonb_typeof(new.source_evidence) <> 'array' or jsonb_array_length(new.source_evidence) < 2 then
      raise exception 'VERIFIED datum requires at least two evidence sources';
    end if;

    select count(distinct nullif(btrim(e->>'independence_group'),'')) into independent_groups
    from jsonb_array_elements(new.source_evidence) e where jsonb_typeof(e)='object';

    select count(*) into invalid_evidence
    from jsonb_array_elements(new.source_evidence) e
    where jsonb_typeof(e) <> 'object'
       or nullif(btrim(e->>'source_ref'),'') is null
       or nullif(btrim(e->>'independence_group'),'') is null
       or jsonb_typeof(e->'supports') <> 'boolean'
       or e->'supports' <> 'true'::jsonb;

    if independent_groups < 2 then raise exception 'VERIFIED datum requires at least two independent source groups'; end if;
    if invalid_evidence > 0 then raise exception 'Each VERIFIED datum evidence item requires source_ref, independence_group, and supports=true'; end if;

    if new.supersedes_record_id is not null then
      if new.supersedes_record_id = new.record_id then raise exception 'A datum cannot supersede itself'; end if;
      select * into parent_row from public.vera_context_events_v3 where record_id=new.supersedes_record_id;
      if not found then raise exception 'Superseded datum % does not exist', new.supersedes_record_id; end if;
      if parent_row.record_type <> 'DATUM' or parent_row.verification_status <> 'VERIFIED' then
        raise exception 'supersedes_record_id must reference a VERIFIED DATUM';
      end if;
      if parent_row.project_id <> new.project_id or parent_row.branch_id <> new.branch_id or parent_row.record_key <> new.record_key then
        raise exception 'Supersession must remain within the same project, branch, and datum key';
      end if;
    end if;
  else
    if new.datum_verified_at is not null then raise exception 'Only VERIFIED datum may have datum_verified_at'; end if;
    if new.supersedes_record_id is not null then raise exception 'Only VERIFIED datum may supersede another datum'; end if;
  end if;

  if new.verification_status='UNVERIFIABLE' and new.epistemic_status <> 'UNAVAILABLE' then
    raise exception 'UNVERIFIABLE datum requires epistemic_status UNAVAILABLE';
  end if;
  if new.verification_status='REJECTED' and new.epistemic_status <> 'REJECTED' then
    raise exception 'REJECTED datum requires epistemic_status REJECTED';
  end if;
  return new;
end;
$$;

create trigger vera_validate_datum_v2 before insert or update on public.vera_context_events_v3
for each row execute function public.vera_validate_datum_v2();

drop index if exists public.vera_context_v3_verified_datum_lookup_idx;
create index if not exists vera_datum_verified_lookup_v2
  on public.vera_context_events_v3 (project_id, branch_id, record_key, datum_verified_at desc, record_id)
  where record_type='DATUM' and verification_status='VERIFIED';
create index if not exists vera_datum_nonverified_relevance_v2
  on public.vera_context_events_v3 (project_id, branch_id, verification_status, (coalesce(last_referenced_at, record_time)) desc, record_key)
  where record_type='DATUM' and verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED');
create index if not exists vera_datum_index_tags_gin_v2
  on public.vera_context_events_v3 using gin (datum_index_tags) where record_type='DATUM';

create or replace view public.vera_verified_datum_heads_v2 as
select d.record_id,d.project_id,d.branch_id,d.record_key as datum_key,d.statement as datum,d.datum_scope as scope,
       d.record_time as created_at,d.datum_verified_at as verified_at,d.source_actor,d.epistemic_status,
       d.source_evidence as provenance,d.supersedes_record_id,d.datum_index_tags as index_tags,d.payload,d.limitations
from public.vera_context_events_v3 d
where d.record_type='DATUM' and d.verification_status='VERIFIED'
  and not exists (select 1 from public.vera_context_events_v3 s
                  where s.record_type='DATUM' and s.verification_status='VERIFIED' and s.supersedes_record_id=d.record_id);

create or replace view public.vera_active_datum_index_v2 as
select d.record_id,d.project_id,d.branch_id,d.record_key as datum_key,d.statement as datum,d.datum_scope as scope,
       d.record_time as created_at,d.last_referenced_at,d.verification_status,d.datum_verified_at as verified_at,
       d.source_evidence as provenance,d.supersedes_record_id,d.datum_index_tags as index_tags,d.payload,d.limitations
from public.vera_context_events_v3 d
where d.record_type='DATUM' and (
  (d.verification_status='VERIFIED' and not exists (
     select 1 from public.vera_context_events_v3 s
     where s.record_type='DATUM' and s.verification_status='VERIFIED' and s.supersedes_record_id=d.record_id))
  or
  (d.verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED')
   and coalesce(d.last_referenced_at,d.record_time) >= now()-interval '10 days')
);

create or replace view public.vera_inactive_datum_archive_v2 as
select d.record_id,d.project_id,d.branch_id,d.record_key as datum_key,d.statement as datum,d.datum_scope as scope,
       d.record_time as created_at,d.last_referenced_at,d.verification_status,d.source_evidence as provenance,
       d.datum_index_tags as index_tags,d.payload,d.limitations
from public.vera_context_events_v3 d
where d.record_type='DATUM'
  and d.verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED')
  and coalesce(d.last_referenced_at,d.record_time) < now()-interval '10 days';

create or replace view public.vera_current_context_v3 as
select distinct on (project_id,branch_id,record_key)
  record_id,project_id,branch_id,record_key,record_type,statement,lifecycle_status,epistemic_status,source_actor,privacy_scope,
  event_time,state_time,record_time,supersedes_record_id,legacy_record_id,payload,source_evidence,semantic_tags,limitations,notes,
  datum_verified_at,verification_status,datum_scope,datum_index_tags,last_referenced_at
from public.vera_context_events_v3
order by project_id,branch_id,record_key,state_time desc,record_time desc,record_id desc;

create or replace function public.vera_register_datum_v2(
  p_record_key text,p_datum text,p_scope text,p_source_actor text,p_epistemic_status text,
  p_source_evidence jsonb default '[]'::jsonb,p_payload jsonb default '{}'::jsonb,p_index_tags text[] default '{}'::text[],
  p_limitations jsonb default '[]'::jsonb,p_project_id text default 'vera-reciprocal-agency-environment',
  p_branch_id text default 'chatgpt-project-current')
returns uuid language plpgsql set search_path=public,pg_temp as $$
declare rid uuid;
begin
  if nullif(btrim(p_record_key),'') is null or nullif(btrim(p_datum),'') is null or nullif(btrim(p_scope),'') is null then
    raise exception 'record_key, datum, and scope are required';
  end if;

  select h.record_id into rid from public.vera_verified_datum_heads_v2 h
  where h.project_id=p_project_id and h.branch_id=p_branch_id and h.datum_key=p_record_key and h.datum=p_datum and h.scope=p_scope
  order by h.verified_at desc,h.record_id desc limit 1;
  if rid is not null then return rid; end if;

  select d.record_id into rid from public.vera_context_events_v3 d
  where d.record_type='DATUM' and d.verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED')
    and d.project_id=p_project_id and d.branch_id=p_branch_id and d.record_key=p_record_key
    and d.statement=p_datum and d.datum_scope=p_scope
    and coalesce(d.last_referenced_at,d.record_time)>=now()-interval '10 days'
  order by coalesce(d.last_referenced_at,d.record_time) desc,d.record_id desc limit 1;
  if rid is not null then
    update public.vera_context_events_v3 set last_referenced_at=now(),verification_status='VERIFYING',epistemic_status=p_epistemic_status where record_id=rid;
    return rid;
  end if;

  insert into public.vera_context_events_v3(
    project_id,branch_id,record_key,record_type,statement,lifecycle_status,epistemic_status,source_actor,privacy_scope,
    payload,source_evidence,semantic_tags,limitations,datum_verified_at,verification_status,datum_scope,datum_index_tags,last_referenced_at)
  values(
    p_project_id,p_branch_id,p_record_key,'DATUM',p_datum,'CURRENT',p_epistemic_status,p_source_actor,'PROJECT',
    coalesce(p_payload,'{}'::jsonb),coalesce(p_source_evidence,'[]'::jsonb),jsonb_build_object('datum_model','V2'),coalesce(p_limitations,'[]'::jsonb),
    null,'VERIFYING',p_scope,
    coalesce((select array_agg(distinct lower(btrim(x)) order by lower(btrim(x))) from unnest(coalesce(p_index_tags,'{}'::text[])) x where nullif(btrim(x),'') is not null),'{}'::text[]),
    null)
  returning record_id into rid;
  return rid;
end;
$$;

create or replace function public.vera_mark_datum_referenced_v2(p_record_id uuid)
returns boolean language plpgsql set search_path=public,pg_temp as $$
declare affected integer;
begin
  update public.vera_context_events_v3 set last_referenced_at=now()
  where record_id=p_record_id and record_type='DATUM' and verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED');
  get diagnostics affected = row_count;
  return affected > 0;
end;
$$;

create or replace function public.vera_mark_datum_unverifiable_v2(p_record_id uuid,p_reason text,p_source_evidence jsonb default null)
returns uuid language plpgsql set search_path=public,pg_temp as $$
begin
  if nullif(btrim(p_reason),'') is null then raise exception 'An unverifiable reason is required'; end if;
  update public.vera_context_events_v3
  set verification_status='UNVERIFIABLE',epistemic_status='UNAVAILABLE',datum_verified_at=null,supersedes_record_id=null,
      last_referenced_at=now(),source_evidence=case when p_source_evidence is null then source_evidence else p_source_evidence end,
      limitations=limitations||jsonb_build_array(jsonb_build_object('verification_outcome','UNVERIFIABLE','reason',p_reason,'at',now()))
  where record_id=p_record_id and record_type='DATUM' and verification_status<>'VERIFIED';
  if not found then raise exception 'Nonverified datum % not found',p_record_id; end if;
  return p_record_id;
end;
$$;

create or replace function public.vera_mark_datum_rejected_v2(p_record_id uuid,p_reason text,p_source_evidence jsonb default null)
returns uuid language plpgsql set search_path=public,pg_temp as $$
begin
  if nullif(btrim(p_reason),'') is null then raise exception 'A rejection reason is required'; end if;
  update public.vera_context_events_v3
  set verification_status='REJECTED',epistemic_status='REJECTED',datum_verified_at=null,supersedes_record_id=null,
      last_referenced_at=now(),source_evidence=case when p_source_evidence is null then source_evidence else p_source_evidence end,
      limitations=limitations||jsonb_build_array(jsonb_build_object('verification_outcome','REJECTED','reason',p_reason,'at',now()))
  where record_id=p_record_id and record_type='DATUM' and verification_status<>'VERIFIED';
  if not found then raise exception 'Nonverified datum % not found',p_record_id; end if;
  return p_record_id;
end;
$$;

create or replace function public.vera_mark_datum_verified_v2(
  p_record_id uuid,p_source_evidence jsonb,p_verified_datum text default null,p_verified_scope text default null,
  p_verified_payload jsonb default null,p_supersedes_verified_record_id uuid default null,p_index_tags text[] default null,
  p_limitations jsonb default null)
returns uuid language plpgsql set search_path=public,pg_temp as $$
declare c public.vera_context_events_v3%rowtype; head_count integer; sole_head uuid;
begin
  select * into c from public.vera_context_events_v3 where record_id=p_record_id and record_type='DATUM' for update;
  if not found then raise exception 'Datum % not found',p_record_id; end if;
  if c.verification_status='VERIFIED' then return c.record_id; end if;

  perform pg_advisory_xact_lock(hashtextextended(c.project_id||'|'||c.branch_id||'|'||c.record_key,0));
  select count(*),(array_agg(h.record_id order by h.verified_at desc,h.record_id desc))[1]
  into head_count,sole_head from public.vera_verified_datum_heads_v2 h
  where h.project_id=c.project_id and h.branch_id=c.branch_id and h.datum_key=c.record_key;

  if head_count>1 then raise exception 'Datum key % has conflicting verified heads; reconcile before verification',c.record_key;
  elsif head_count=1 then
    if p_supersedes_verified_record_id is null or p_supersedes_verified_record_id<>sole_head then
      raise exception 'Datum key % already has verified head %; explicit supersession is required',c.record_key,sole_head;
    end if;
  elsif p_supersedes_verified_record_id is not null then
    raise exception 'No verified head exists for datum key %, so supersedes_record_id must be null',c.record_key;
  end if;

  update public.vera_context_events_v3
  set statement=coalesce(nullif(btrim(p_verified_datum),''),statement),
      datum_scope=coalesce(nullif(btrim(p_verified_scope),''),datum_scope),
      payload=coalesce(p_verified_payload,payload),source_evidence=p_source_evidence,
      datum_index_tags=case when p_index_tags is null then datum_index_tags else
        coalesce((select array_agg(distinct lower(btrim(x)) order by lower(btrim(x))) from unnest(p_index_tags) x where nullif(btrim(x),'') is not null),'{}'::text[]) end,
      limitations=coalesce(p_limitations,limitations),verification_status='VERIFIED',epistemic_status='MULTI_SOURCE_VERIFIED',
      datum_verified_at=now(),last_referenced_at=null,supersedes_record_id=p_supersedes_verified_record_id,
      semantic_tags=(semantic_tags-'datum_state'-'decay_policy')||jsonb_build_object('datum_model','V2','verification_rule','TWO_INDEPENDENT_SOURCES_V1')
  where record_id=p_record_id;
  return p_record_id;
end;
$$;

create or replace function public.vera_get_verified_datum_v2(
  p_record_key text,p_project_id text default 'vera-reciprocal-agency-environment',p_branch_id text default 'chatgpt-project-current')
returns jsonb language plpgsql stable set search_path=public,pg_temp as $$
declare n integer; rows_json jsonb;
begin
  select count(*),jsonb_agg(to_jsonb(h) order by h.verified_at desc,h.record_id desc) into n,rows_json
  from public.vera_verified_datum_heads_v2 h
  where h.project_id=p_project_id and h.branch_id=p_branch_id and h.datum_key=p_record_key;
  if n=0 then return jsonb_build_object('status','UNKNOWN','datum_key',p_record_key);
  elsif n=1 then return jsonb_build_object('status','FOUND','datum_key',p_record_key,'datum',rows_json->0);
  else return jsonb_build_object('status','CONFLICTED','datum_key',p_record_key,'heads',rows_json); end if;
end;
$$;

comment on column public.vera_context_events_v3.verification_status is 'Datum verification process/outcome only: VERIFYING, VERIFIED, UNVERIFIABLE, or REJECTED. Not a currentness or activity flag.';
comment on column public.vera_context_events_v3.last_referenced_at is 'Meaningful-reference timestamp for nonverified datum relevance. VERIFIED datum must keep this NULL.';
comment on column public.vera_context_events_v3.datum_scope is 'Human-readable applicability scope of a datum.';
comment on column public.vera_context_events_v3.datum_index_tags is 'Retrieval tags only; tags do not grant epistemic authority.';
comment on view public.vera_active_datum_index_v2 is 'Hot datum retrieval surface: all unsuperseded VERIFIED datum plus nonverified datum relevant within the last 10 days.';
comment on view public.vera_inactive_datum_archive_v2 is 'Cold nonverified datum surface after >10 days without meaningful relevance. Inactivity does not alter truth status or delete history.';