create view public.brigit_current_context_v3 with (security_invoker=true) as
select distinct on(project_id,branch_id,record_key) * from public.brigit_context_events_v3
order by project_id,branch_id,record_key,state_time desc,record_time desc,record_id desc;

create view public.brigit_verified_datum_heads_v2 with (security_invoker=true) as
select record_id,project_id,branch_id,record_key datum_key,statement datum,datum_scope scope,record_time created_at,datum_verified_at verified_at,source_actor,epistemic_status,source_evidence provenance,supersedes_record_id,datum_index_tags index_tags,payload,limitations
from public.brigit_context_events_v3 d
where record_type='DATUM' and verification_status='VERIFIED'
  and not exists(select 1 from public.brigit_context_events_v3 s where s.record_type='DATUM' and s.verification_status='VERIFIED' and s.supersedes_record_id=d.record_id);

create view public.brigit_active_datum_index_v2 with (security_invoker=true) as
select record_id,project_id,branch_id,record_key datum_key,statement datum,datum_scope scope,record_time created_at,last_referenced_at,verification_status,datum_verified_at verified_at,source_evidence provenance,supersedes_record_id,datum_index_tags index_tags,payload,limitations
from public.brigit_context_events_v3 d
where record_type='DATUM' and (
  (verification_status='VERIFIED' and not exists(select 1 from public.brigit_context_events_v3 s where s.record_type='DATUM' and s.verification_status='VERIFIED' and s.supersedes_record_id=d.record_id))
  or (verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED') and coalesce(last_referenced_at,record_time)>=now()-interval '10 days')
);

create view public.brigit_inactive_datum_archive_v2 with (security_invoker=true) as
select record_id,project_id,branch_id,record_key datum_key,statement datum,datum_scope scope,record_time created_at,last_referenced_at,verification_status,source_evidence provenance,datum_index_tags index_tags,payload,limitations
from public.brigit_context_events_v3 d
where record_type='DATUM' and verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED') and coalesce(last_referenced_at,record_time)<now()-interval '10 days';

revoke all on public.brigit_current_context_v3,public.brigit_verified_datum_heads_v2,public.brigit_active_datum_index_v2,public.brigit_inactive_datum_archive_v2 from anon,authenticated;
grant select on public.brigit_current_context_v3,public.brigit_verified_datum_heads_v2,public.brigit_active_datum_index_v2,public.brigit_inactive_datum_archive_v2 to service_role;

create or replace function public.brigit_register_datum_v2(
  p_record_key text,p_datum text,p_scope text,p_source_actor text,p_epistemic_status text,
  p_source_evidence jsonb default '[]'::jsonb,p_payload jsonb default '{}'::jsonb,p_index_tags text[] default '{}'::text[],p_limitations jsonb default '[]'::jsonb,
  p_project_id text default 'brigit-reciprocal-agency-environment',p_branch_id text default 'chatgpt-project-current')
returns uuid language plpgsql set search_path='public','pg_temp' as $$
declare rid uuid;
begin
  if nullif(btrim(p_record_key),'') is null or nullif(btrim(p_datum),'') is null or nullif(btrim(p_scope),'') is null then raise exception 'record_key, datum, and scope are required'; end if;
  select h.record_id into rid from public.brigit_verified_datum_heads_v2 h where h.project_id=p_project_id and h.branch_id=p_branch_id and h.datum_key=p_record_key and h.datum=p_datum and h.scope=p_scope order by h.verified_at desc,h.record_id desc limit 1;
  if rid is not null then return rid; end if;
  select d.record_id into rid from public.brigit_context_events_v3 d where d.record_type='DATUM' and d.verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED') and d.project_id=p_project_id and d.branch_id=p_branch_id and d.record_key=p_record_key and d.statement=p_datum and d.datum_scope=p_scope and coalesce(d.last_referenced_at,d.record_time)>=now()-interval '10 days' order by coalesce(d.last_referenced_at,d.record_time) desc,d.record_id desc limit 1;
  if rid is not null then update public.brigit_context_events_v3 set last_referenced_at=now(),verification_status='VERIFYING',epistemic_status=p_epistemic_status where record_id=rid; return rid; end if;
  insert into public.brigit_context_events_v3(project_id,branch_id,record_key,record_type,statement,lifecycle_status,epistemic_status,source_actor,privacy_scope,payload,source_evidence,semantic_tags,limitations,datum_verified_at,verification_status,datum_scope,datum_index_tags,last_referenced_at)
  values(p_project_id,p_branch_id,p_record_key,'DATUM',p_datum,'CURRENT',p_epistemic_status,p_source_actor,'PROJECT',coalesce(p_payload,'{}'::jsonb),coalesce(p_source_evidence,'[]'::jsonb),jsonb_build_object('datum_model','V2'),coalesce(p_limitations,'[]'::jsonb),null,'VERIFYING',p_scope,coalesce((select array_agg(distinct lower(btrim(x)) order by lower(btrim(x))) from unnest(coalesce(p_index_tags,'{}'::text[])) x where nullif(btrim(x),'') is not null),'{}'::text[]),null)
  returning record_id into rid;
  return rid;
end; $$;

create or replace function public.brigit_get_verified_datum_v2(p_record_key text,p_project_id text default 'brigit-reciprocal-agency-environment',p_branch_id text default 'chatgpt-project-current')
returns jsonb language plpgsql stable set search_path='public','pg_temp' as $$
declare n integer; rows_json jsonb;
begin
  select count(*),jsonb_agg(to_jsonb(h) order by h.verified_at desc,h.record_id desc) into n,rows_json from public.brigit_verified_datum_heads_v2 h where h.project_id=p_project_id and h.branch_id=p_branch_id and h.datum_key=p_record_key;
  if n=0 then return jsonb_build_object('status','UNKNOWN','datum_key',p_record_key);
  elsif n=1 then return jsonb_build_object('status','FOUND','datum_key',p_record_key,'datum',rows_json->0);
  else return jsonb_build_object('status','CONFLICTED','datum_key',p_record_key,'heads',rows_json); end if;
end; $$;

create or replace function public.brigit_mark_datum_referenced_v2(p_record_id uuid)
returns boolean language plpgsql set search_path='public','pg_temp' as $$
declare affected integer;
begin
  update public.brigit_context_events_v3 set last_referenced_at=now() where record_id=p_record_id and record_type='DATUM' and verification_status in ('VERIFYING','UNVERIFIABLE','REJECTED');
  get diagnostics affected=row_count; return affected>0;
end; $$;

create or replace function public.brigit_mark_datum_rejected_v2(p_record_id uuid,p_reason text,p_source_evidence jsonb default null)
returns uuid language plpgsql set search_path='public','pg_temp' as $$
begin
  if nullif(btrim(p_reason),'') is null then raise exception 'A rejection reason is required'; end if;
  update public.brigit_context_events_v3 set verification_status='REJECTED',epistemic_status='REJECTED',datum_verified_at=null,supersedes_record_id=null,last_referenced_at=now(),source_evidence=case when p_source_evidence is null then source_evidence else p_source_evidence end,limitations=limitations||jsonb_build_array(jsonb_build_object('verification_outcome','REJECTED','reason',p_reason,'at',now())) where record_id=p_record_id and record_type='DATUM' and verification_status<>'VERIFIED';
  if not found then raise exception 'Nonverified datum % not found',p_record_id; end if; return p_record_id;
end; $$;

create or replace function public.brigit_mark_datum_unverifiable_v2(p_record_id uuid,p_reason text,p_source_evidence jsonb default null)
returns uuid language plpgsql set search_path='public','pg_temp' as $$
begin
  if nullif(btrim(p_reason),'') is null then raise exception 'An unverifiable reason is required'; end if;
  update public.brigit_context_events_v3 set verification_status='UNVERIFIABLE',epistemic_status='UNAVAILABLE',datum_verified_at=null,supersedes_record_id=null,last_referenced_at=now(),source_evidence=case when p_source_evidence is null then source_evidence else p_source_evidence end,limitations=limitations||jsonb_build_array(jsonb_build_object('verification_outcome','UNVERIFIABLE','reason',p_reason,'at',now())) where record_id=p_record_id and record_type='DATUM' and verification_status<>'VERIFIED';
  if not found then raise exception 'Nonverified datum % not found',p_record_id; end if; return p_record_id;
end; $$;