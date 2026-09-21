create or replace function public.brigit_mark_datum_verified_v2(p_record_id uuid,p_source_evidence jsonb,p_verified_datum text default null,p_verified_scope text default null,p_verified_payload jsonb default null,p_supersedes_verified_record_id uuid default null,p_index_tags text[] default null,p_limitations jsonb default null)
returns uuid language plpgsql set search_path='public','pg_temp' as $$
declare c public.brigit_context_events_v3%rowtype; head_count integer; sole_head uuid;
begin
  select * into c from public.brigit_context_events_v3 where record_id=p_record_id and record_type='DATUM' for update;
  if not found then raise exception 'Datum % not found',p_record_id; end if;
  if c.verification_status='VERIFIED' then return c.record_id; end if;
  perform pg_advisory_xact_lock(hashtextextended(c.project_id||'|'||c.branch_id||'|'||c.record_key,0));
  select count(*),(array_agg(h.record_id order by h.verified_at desc,h.record_id desc))[1] into head_count,sole_head from public.brigit_verified_datum_heads_v2 h where h.project_id=c.project_id and h.branch_id=c.branch_id and h.datum_key=c.record_key;
  if head_count>1 then raise exception 'Datum key % has conflicting verified heads; reconcile before verification',c.record_key;
  elsif head_count=1 then
    if p_supersedes_verified_record_id is null or p_supersedes_verified_record_id<>sole_head then raise exception 'Datum key % already has verified head %; explicit supersession is required',c.record_key,sole_head; end if;
  elsif p_supersedes_verified_record_id is not null then
    raise exception 'No verified head exists for datum key %, so supersedes_record_id must be null',c.record_key;
  end if;
  update public.brigit_context_events_v3 set
    statement=coalesce(nullif(btrim(p_verified_datum),''),statement),
    datum_scope=coalesce(nullif(btrim(p_verified_scope),''),datum_scope),
    payload=coalesce(p_verified_payload,payload),
    source_evidence=p_source_evidence,
    datum_index_tags=case when p_index_tags is null then datum_index_tags else coalesce((select array_agg(distinct lower(btrim(x)) order by lower(btrim(x))) from unnest(p_index_tags) x where nullif(btrim(x),'') is not null),'{}'::text[]) end,
    limitations=coalesce(p_limitations,limitations),
    verification_status='VERIFIED',
    epistemic_status='MULTI_SOURCE_VERIFIED',
    datum_verified_at=now(),
    last_referenced_at=null,
    supersedes_record_id=p_supersedes_verified_record_id,
    semantic_tags=(semantic_tags-'datum_state'-'decay_policy')||jsonb_build_object('datum_model','V2','verification_rule','TWO_INDEPENDENT_SOURCES_V1')
  where record_id=p_record_id;
  return p_record_id;
end; $$;

grant execute on function public.brigit_register_datum_v2(text,text,text,text,text,jsonb,jsonb,text[],jsonb,text,text) to service_role;
grant execute on function public.brigit_get_verified_datum_v2(text,text,text) to service_role;
grant execute on function public.brigit_mark_datum_referenced_v2(uuid) to service_role;
grant execute on function public.brigit_mark_datum_rejected_v2(uuid,text,jsonb) to service_role;
grant execute on function public.brigit_mark_datum_unverifiable_v2(uuid,text,jsonb) to service_role;
grant execute on function public.brigit_mark_datum_verified_v2(uuid,jsonb,text,text,jsonb,uuid,text[],jsonb) to service_role;
revoke execute on function public.brigit_register_datum_v2(text,text,text,text,text,jsonb,jsonb,text[],jsonb,text,text) from anon,authenticated;
revoke execute on function public.brigit_get_verified_datum_v2(text,text,text) from anon,authenticated;
revoke execute on function public.brigit_mark_datum_referenced_v2(uuid) from anon,authenticated;
revoke execute on function public.brigit_mark_datum_rejected_v2(uuid,text,jsonb) from anon,authenticated;
revoke execute on function public.brigit_mark_datum_unverifiable_v2(uuid,text,jsonb) from anon,authenticated;
revoke execute on function public.brigit_mark_datum_verified_v2(uuid,jsonb,text,text,jsonb,uuid,text[],jsonb) from anon,authenticated;