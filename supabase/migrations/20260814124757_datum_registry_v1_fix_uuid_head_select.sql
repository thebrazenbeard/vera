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

  select count(*), (array_agg(h.record_id order by h.state_time desc, h.record_time desc, h.record_id desc))[1]
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