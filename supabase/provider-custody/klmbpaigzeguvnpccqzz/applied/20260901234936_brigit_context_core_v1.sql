create table public.brigit_context_events_v3 (
  record_id uuid primary key default gen_random_uuid(),
  project_id text not null default 'brigit-reciprocal-agency-environment',
  branch_id text not null,
  record_key text not null,
  record_type text not null check (record_type in ('FACT','DATUM','USER_STATEMENT','MODEL_OUTPUT','PERSONA_CONFIG','RELATIONAL_FRAME','PREFERENCE','DECISION','CORRECTION','BEHAVIORAL_COMMITMENT','BOUNDARY','PERMISSION','TASK_STATE','TECHNICAL_RESULT','PROVENANCE','HYPOTHESIS','INTERPRETATION','EVALUATION','LEDGER_SNAPSHOT','TOMBSTONE','OTHER')),
  statement text not null,
  lifecycle_status text not null,
  epistemic_status text not null check (epistemic_status in ('DIRECT_USER_STATEMENT','OBSERVED_TOOL_RESULT','DOCUMENTED_SOURCE','MULTI_SOURCE_VERIFIED','MODEL_GENERATED_CLAIM','SUPPORTED_INFERENCE','HYPOTHESIS','DISPUTED','REJECTED','UNAVAILABLE')),
  source_actor text not null check (source_actor in ('USER','CHATGPT_MODEL','TOOL','SYSTEM','EXTERNAL','UNRESOLVED')),
  privacy_scope text not null default 'PROJECT',
  event_time timestamptz null,
  state_time timestamptz not null default now(),
  record_time timestamptz not null default now(),
  supersedes_record_id uuid null references public.brigit_context_events_v3(record_id),
  legacy_record_id uuid null,
  payload jsonb not null default '{}'::jsonb check (jsonb_typeof(payload)='object'),
  source_evidence jsonb not null default '[]'::jsonb check (jsonb_typeof(source_evidence)='array'),
  semantic_tags jsonb not null default '{}'::jsonb check (jsonb_typeof(semantic_tags)='object'),
  limitations jsonb not null default '[]'::jsonb check (jsonb_typeof(limitations)='array'),
  notes text null,
  datum_verified_at timestamptz null,
  verification_status text null,
  datum_scope text null,
  datum_index_tags text[] not null default '{}'::text[],
  last_referenced_at timestamptz null
);
comment on table public.brigit_context_events_v3 is 'Neutral Brigit context records. Model-generated claims are not self-authenticating internal-state evidence.';
comment on column public.brigit_context_events_v3.datum_verified_at is 'Time at which a verified datum completed the configured verification rule.';
comment on column public.brigit_context_events_v3.verification_status is 'Datum verification process/outcome only: VERIFYING, VERIFIED, UNVERIFIABLE, or REJECTED. Not a currentness or activity flag.';
comment on column public.brigit_context_events_v3.datum_scope is 'Human-readable applicability scope of a datum.';
comment on column public.brigit_context_events_v3.datum_index_tags is 'Retrieval tags only; tags do not grant epistemic authority.';
comment on column public.brigit_context_events_v3.last_referenced_at is 'Meaningful-reference timestamp for nonverified datum relevance. VERIFIED datum must keep this NULL.';
create unique index brigit_context_events_v3_legacy_record_id_uidx on public.brigit_context_events_v3(legacy_record_id) where legacy_record_id is not null;
create index brigit_context_events_v3_record_key_idx on public.brigit_context_events_v3(record_key,state_time desc,record_time desc);
create index brigit_context_events_v3_scope_key_idx on public.brigit_context_events_v3(project_id,branch_id,record_key,state_time desc,record_time desc,record_id desc);
create index brigit_context_events_v3_semantic_tags_gin on public.brigit_context_events_v3 using gin(semantic_tags);
create index brigit_context_events_v3_supersedes_record_id_idx on public.brigit_context_events_v3(supersedes_record_id) where supersedes_record_id is not null;
create index brigit_datum_index_tags_gin_v2 on public.brigit_context_events_v3 using gin(datum_index_tags) where record_type='DATUM';
create index brigit_datum_nonverified_relevance_v2 on public.brigit_context_events_v3(project_id,branch_id,verification_status,coalesce(last_referenced_at,record_time) desc,record_key) where record_type='DATUM' and verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED');
create index brigit_datum_verified_lookup_v2 on public.brigit_context_events_v3(project_id,branch_id,record_key,datum_verified_at desc,record_id) where record_type='DATUM' and verification_status='VERIFIED';

create or replace function public.brigit_validate_datum_v2()
returns trigger language plpgsql set search_path='public','pg_temp' as $$
declare independent_groups integer; invalid_evidence integer; parent_row public.brigit_context_events_v3%rowtype;
begin
  if tg_op='INSERT' and new.record_type='FACT' then raise exception 'FACT is legacy. Use record_type DATUM with verification_status.'; end if;
  if new.record_type<>'DATUM' then return new; end if;
  if nullif(btrim(new.statement),'') is null then raise exception 'DATUM requires a non-empty datum statement'; end if;
  if nullif(btrim(new.datum_scope),'') is null then raise exception 'DATUM requires a non-empty scope'; end if;
  if new.last_referenced_at is not null and new.last_referenced_at<new.record_time then raise exception 'last_referenced_at cannot precede datum creation'; end if;
  if new.verification_status not in ('VERIFYING','VERIFIED','UNVERIFIABLE','REJECTED') then raise exception 'DATUM requires verification_status VERIFYING, VERIFIED, UNVERIFIABLE, or REJECTED'; end if;
  if new.verification_status='VERIFIED' then
    if new.datum_verified_at is null then raise exception 'VERIFIED datum requires datum_verified_at'; end if;
    if new.last_referenced_at is not null then raise exception 'VERIFIED datum does not track last_referenced_at'; end if;
    if new.epistemic_status<>'MULTI_SOURCE_VERIFIED' then raise exception 'VERIFIED datum requires epistemic_status MULTI_SOURCE_VERIFIED'; end if;
    if jsonb_typeof(new.source_evidence)<>'array' or jsonb_array_length(new.source_evidence)<2 then raise exception 'VERIFIED datum requires at least two evidence sources'; end if;
    select count(distinct nullif(btrim(e->>'independence_group'),'')) into independent_groups from jsonb_array_elements(new.source_evidence) e where jsonb_typeof(e)='object';
    select count(*) into invalid_evidence from jsonb_array_elements(new.source_evidence) e where jsonb_typeof(e)<>'object' or nullif(btrim(e->>'source_ref'),'') is null or nullif(btrim(e->>'independence_group'),'') is null or jsonb_typeof(e->'supports')<>'boolean' or e->'supports'<>'true'::jsonb;
    if independent_groups<2 then raise exception 'VERIFIED datum requires at least two independent source groups'; end if;
    if invalid_evidence>0 then raise exception 'Each VERIFIED datum evidence item requires source_ref, independence_group, and supports=true'; end if;
    if new.supersedes_record_id is not null then
      if new.supersedes_record_id=new.record_id then raise exception 'A datum cannot supersede itself'; end if;
      select * into parent_row from public.brigit_context_events_v3 where record_id=new.supersedes_record_id;
      if not found then raise exception 'Superseded datum % does not exist',new.supersedes_record_id; end if;
      if parent_row.record_type<>'DATUM' or parent_row.verification_status<>'VERIFIED' then raise exception 'supersedes_record_id must reference a VERIFIED DATUM'; end if;
      if parent_row.project_id<>new.project_id or parent_row.branch_id<>new.branch_id or parent_row.record_key<>new.record_key then raise exception 'Supersession must remain within the same project, branch, and datum key'; end if;
    end if;
  else
    if new.datum_verified_at is not null then raise exception 'Only VERIFIED datum may have datum_verified_at'; end if;
    if new.supersedes_record_id is not null then raise exception 'Only VERIFIED datum may supersede another datum'; end if;
  end if;
  if new.verification_status='UNVERIFIABLE' and new.epistemic_status<>'UNAVAILABLE' then raise exception 'UNVERIFIABLE datum requires epistemic_status UNAVAILABLE'; end if;
  if new.verification_status='REJECTED' and new.epistemic_status<>'REJECTED' then raise exception 'REJECTED datum requires epistemic_status REJECTED'; end if;
  return new;
end; $$;
create trigger brigit_validate_datum_v2 before insert or update on public.brigit_context_events_v3 for each row execute function public.brigit_validate_datum_v2();

alter table public.brigit_context_events_v3 enable row level security;
create policy brigit_context_events_v3_no_client_access on public.brigit_context_events_v3 for all to anon,authenticated using(false) with check(false);
revoke all on public.brigit_context_events_v3 from anon,authenticated;
grant select,insert,update,delete,truncate,references,trigger on public.brigit_context_events_v3 to service_role;