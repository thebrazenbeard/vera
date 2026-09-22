-- Bounded Memory review correction.
--
-- Adds cycle and zero-head lineage protection, truthful recall completeness,
-- and bounded structural provenance/semantic/model-output validation.
-- Version-controlled source only. Production application remains unauthorized.

begin;

create or replace function public.vera_source_evidence_v3_is_meaningful(
  p_evidence jsonb
)
returns boolean
language sql
immutable
set search_path = pg_catalog, public
as $$
  select case
    when jsonb_typeof(p_evidence) <> 'array' then false
    when jsonb_array_length(p_evidence) = 0 then false
    else not exists (
      select 1
      from jsonb_array_elements(p_evidence) as evidence(value)
      where jsonb_typeof(evidence.value) <> 'object'
         or coalesce(btrim(evidence.value->>'surface'), '') = ''
         or not (
           coalesce(btrim(evidence.value->>'claim'), '') <> ''
           or coalesce(btrim(evidence.value->>'observation'), '') <> ''
           or coalesce(btrim(evidence.value->>'source_uri'), '') <> ''
           or coalesce(btrim(evidence.value->>'source_ref'), '') <> ''
           or coalesce(btrim(evidence.value->>'record_id'), '') <> ''
           or coalesce(btrim(evidence.value->>'event_id'), '') <> ''
           or coalesce(btrim(evidence.value->>'message_id'), '') <> ''
           or coalesce(btrim(evidence.value->>'artifact_sha256'), '') <> ''
           or coalesce(btrim(evidence.value->>'generation_id'), '') <> ''
           or coalesce(btrim(evidence.value->>'tool_result_id'), '') <> ''
         )
    )
  end;
$$;

create or replace function public.vera_semantic_tags_v3_are_meaningful(
  p_tags jsonb
)
returns boolean
language sql
immutable
set search_path = pg_catalog, public
as $$
  select case
    when jsonb_typeof(p_tags) <> 'object' then false
    else exists (
      select 1
      from jsonb_each(p_tags) as tag(key, value)
      where case jsonb_typeof(tag.value)
        when 'string' then coalesce(btrim(tag.value #>> '{}'), '') <> ''
        when 'array' then exists (
          select 1
          from jsonb_array_elements(tag.value) as item(value)
          where jsonb_typeof(item.value) = 'string'
            and coalesce(btrim(item.value #>> '{}'), '') <> ''
        )
        else false
      end
    )
  end;
$$;

create or replace function public.vera_model_output_v3_has_context(
  p_record_type text,
  p_epistemic_status text,
  p_source_actor text,
  p_payload jsonb,
  p_source_evidence jsonb,
  p_limitations jsonb
)
returns boolean
language sql
immutable
set search_path = pg_catalog, public
as $$
  select case
    when p_record_type = 'MODEL_OUTPUT'
      or p_epistemic_status = 'MODEL_GENERATED_CLAIM'
      or p_source_actor = 'CHATGPT_MODEL'
    then
      p_record_type = 'MODEL_OUTPUT'
      and p_epistemic_status = 'MODEL_GENERATED_CLAIM'
      and p_source_actor = 'CHATGPT_MODEL'
      and jsonb_typeof(p_payload->'model_context') = 'object'
      and coalesce(btrim(p_payload#>>'{model_context,runtime}'), '') <> ''
      and coalesce(btrim(p_payload#>>'{model_context,source_surface}'), '') <> ''
      and jsonb_typeof(p_source_evidence) = 'array'
      and exists (
        select 1
        from jsonb_array_elements(p_source_evidence) as evidence(value)
        where jsonb_typeof(evidence.value) = 'object'
          and (
            coalesce(btrim(evidence.value->>'generation_id'), '') <> ''
            or coalesce(btrim(evidence.value->>'message_id'), '') <> ''
            or coalesce(btrim(evidence.value->>'tool_result_id'), '') <> ''
          )
      )
      and jsonb_typeof(p_limitations) = 'array'
      and exists (
        select 1
        from jsonb_array_elements(p_limitations) as limitation(value)
        where jsonb_typeof(limitation.value) = 'string'
          and lower(limitation.value #>> '{}') like '%not introspective evidence%'
      )
    else true
  end;
$$;

-- Refuse promotion over cyclic, zero-head, or structurally under-governed data.
do $$
begin
  if exists (
    with recursive lineage_walk as (
      select
        e.project_id,
        e.branch_id,
        e.record_key,
        e.record_id as start_record_id,
        e.record_id as current_record_id,
        e.supersedes_record_id as next_record_id,
        array[e.record_id]::uuid[] as path,
        false as is_cycle
      from public.vera_context_events_v3 e

      union all

      select
        walk.project_id,
        walk.branch_id,
        walk.record_key,
        walk.start_record_id,
        parent.record_id,
        parent.supersedes_record_id,
        walk.path || parent.record_id,
        parent.record_id = any(walk.path)
      from lineage_walk walk
      join public.vera_context_events_v3 parent
        on parent.record_id = walk.next_record_id
      where walk.next_record_id is not null
        and not walk.is_cycle
    )
    select 1
    from lineage_walk
    where is_cycle
  ) then
    raise exception 'neutral V3 baseline contains a multi-record supersession cycle';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3 e
    left join public.vera_context_events_v3 child
      on child.supersedes_record_id = e.record_id
    group by e.project_id, e.branch_id, e.record_key
    having count(*) > 0
       and count(*) filter (where child.record_id is null) = 0
  ) then
    raise exception 'neutral V3 baseline contains a scoped key with records but zero lineage heads';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3
    where not public.vera_source_evidence_v3_is_meaningful(source_evidence)
  ) then
    raise exception 'neutral V3 baseline contains structurally meaningless source evidence';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3
    where not public.vera_semantic_tags_v3_are_meaningful(semantic_tags)
  ) then
    raise exception 'neutral V3 baseline contains semantic tags without usable values';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3
    where not public.vera_model_output_v3_has_context(
      record_type,
      epistemic_status,
      source_actor,
      payload,
      source_evidence,
      limitations
    )
  ) then
    raise exception 'neutral V3 baseline contains model output without runtime/source context, generation evidence, or the required limitation';
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.vera_context_events_v3'::regclass
      and conname = 'vera_context_events_v3_source_evidence_structured_chk'
  ) then
    alter table public.vera_context_events_v3
      add constraint vera_context_events_v3_source_evidence_structured_chk
      check (public.vera_source_evidence_v3_is_meaningful(source_evidence));
  end if;

  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.vera_context_events_v3'::regclass
      and conname = 'vera_context_events_v3_semantic_tags_usable_chk'
  ) then
    alter table public.vera_context_events_v3
      add constraint vera_context_events_v3_semantic_tags_usable_chk
      check (public.vera_semantic_tags_v3_are_meaningful(semantic_tags));
  end if;

  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.vera_context_events_v3'::regclass
      and conname = 'vera_context_events_v3_model_output_context_chk'
  ) then
    alter table public.vera_context_events_v3
      add constraint vera_context_events_v3_model_output_context_chk
      check (public.vera_model_output_v3_has_context(
        record_type,
        epistemic_status,
        source_actor,
        payload,
        source_evidence,
        limitations
      ));
  end if;
end;
$$;

create or replace view public.vera_context_lineage_anomalies_v3
with (security_invoker = true)
as
with recursive lineage_walk as (
  select
    e.project_id,
    e.branch_id,
    e.record_key,
    e.record_id as start_record_id,
    e.record_id as current_record_id,
    e.supersedes_record_id as next_record_id,
    array[e.record_id]::uuid[] as path,
    false as is_cycle
  from public.vera_context_events_v3 e

  union all

  select
    walk.project_id,
    walk.branch_id,
    walk.record_key,
    walk.start_record_id,
    parent.record_id,
    parent.supersedes_record_id,
    walk.path || parent.record_id,
    parent.record_id = any(walk.path)
  from lineage_walk walk
  join public.vera_context_events_v3 parent
    on parent.record_id = walk.next_record_id
  where walk.next_record_id is not null
    and not walk.is_cycle
),
cycle_members as (
  select distinct
    walk.project_id,
    walk.branch_id,
    walk.record_key,
    member.record_id
  from lineage_walk walk
  cross join lateral unnest(walk.path) as member(record_id)
  where walk.is_cycle
),
cycle_scopes as (
  select
    project_id,
    branch_id,
    record_key,
    array_agg(record_id order by record_id) as cycle_record_ids
  from cycle_members
  group by project_id, branch_id, record_key
),
scope_summary as (
  select
    e.project_id,
    e.branch_id,
    e.record_key,
    count(*)::bigint as record_count,
    count(*) filter (where child.record_id is null)::bigint as head_count,
    array_agg(e.record_id order by e.record_id) as record_ids
  from public.vera_context_events_v3 e
  left join public.vera_context_events_v3 child
    on child.supersedes_record_id = e.record_id
  group by e.project_id, e.branch_id, e.record_key
)
select
  summary.project_id,
  summary.branch_id,
  summary.record_key,
  summary.record_count,
  summary.head_count,
  cycle.cycle_record_ids is not null as has_cycle,
  array_remove(array[
    case when cycle.cycle_record_ids is not null then 'CYCLE' end,
    case when summary.head_count = 0 then 'ZERO_HEAD' end
  ], null)::text[] as anomaly_types,
  summary.record_ids,
  coalesce(cycle.cycle_record_ids, array[]::uuid[]) as cycle_record_ids
from scope_summary summary
left join cycle_scopes cycle
  using (project_id, branch_id, record_key)
where summary.head_count = 0
   or cycle.cycle_record_ids is not null;

create or replace function public.enforce_vera_context_v3_lineage()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
declare
  existing_record_count integer;
  current_head_id uuid;
  current_head_count integer;
  parent_project_id text;
  parent_branch_id text;
  parent_record_key text;
begin
  new.record_time := clock_timestamp();

  perform pg_advisory_xact_lock(
    hashtextextended(
      new.project_id || E'\x1f' || new.branch_id || E'\x1f' || new.record_key,
      0
    )
  );

  if new.supersedes_record_id is not null then
    select project_id, branch_id, record_key
      into parent_project_id, parent_branch_id, parent_record_key
    from public.vera_context_events_v3
    where record_id = new.supersedes_record_id;

    if not found then
      raise exception 'superseded neutral V3 record % does not exist',
        new.supersedes_record_id;
    end if;

    if parent_project_id <> new.project_id
       or parent_branch_id <> new.branch_id
       or parent_record_key <> new.record_key then
      raise exception 'neutral V3 supersession must remain within the same project, branch, and record_key';
    end if;
  end if;

  select
    count(*),
    count(*) filter (where not exists (
      select 1
      from public.vera_context_events_v3 child
      where child.supersedes_record_id = e.record_id
    )),
    (array_agg(e.record_id order by e.record_id) filter (where not exists (
      select 1
      from public.vera_context_events_v3 child
      where child.supersedes_record_id = e.record_id
    )))[1]
    into existing_record_count, current_head_count, current_head_id
  from public.vera_context_events_v3 e
  where e.project_id = new.project_id
    and e.branch_id = new.branch_id
    and e.record_key = new.record_key;

  if existing_record_count = 0 then
    if new.supersedes_record_id is not null then
      raise exception 'initial neutral V3 record for a scoped key may not supersede another record';
    end if;
  elsif current_head_count = 0 then
    raise exception 'neutral V3 scoped key has existing records but zero lineage heads; cyclic or malformed lineage must be resolved before appending';
  elsif current_head_count = 1 then
    if new.supersedes_record_id is distinct from current_head_id then
      raise exception 'new neutral V3 record must supersede the unique current head %',
        current_head_id;
    end if;
  else
    raise exception 'neutral V3 scoped key has % current heads; resolve conflict before appending',
      current_head_count;
  end if;

  return new;
end;
$$;

create or replace function public.recall_vera_context_v3(
  p_request_id text,
  p_project_id text,
  p_branch_id text,
  p_record_keys text[] default null,
  p_privacy_scopes text[] default array['PROJECT']::text[],
  p_include_model_generated boolean default false,
  p_max_records integer default 8
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  recalled_records jsonb;
  recalled_ids jsonb;
  total_matches integer;
  returned_matches integer;
  has_more boolean;
  completeness text;
  result_class text;
  outcome_code text;
  retrieval_limitations jsonb;
  retrieval_time timestamptz := clock_timestamp();
begin
  if p_request_id is null or coalesce(btrim(p_request_id), '') = '' then
    raise exception 'p_request_id must be non-empty';
  end if;
  if p_project_id is null or coalesce(btrim(p_project_id), '') = '' then
    raise exception 'p_project_id must be non-empty';
  end if;
  if p_branch_id is null or coalesce(btrim(p_branch_id), '') = '' then
    raise exception 'p_branch_id must be non-empty';
  end if;
  if p_privacy_scopes is null or cardinality(p_privacy_scopes) = 0 then
    raise exception 'p_privacy_scopes must contain at least one scope';
  end if;
  if p_max_records is null or p_max_records < 1 or p_max_records > 50 then
    raise exception 'p_max_records must be between 1 and 50';
  end if;

  with eligible as materialized (
    select v.*
    from public.vera_current_context_v3 v
    where v.project_id = p_project_id
      and v.branch_id = p_branch_id
      and v.lifecycle_status = 'CURRENT'
      and v.privacy_scope = any(p_privacy_scopes)
      and (
        p_record_keys is null
        or cardinality(p_record_keys) = 0
        or v.record_key = any(p_record_keys)
      )
      and v.epistemic_status not in ('REJECTED', 'DISPUTED')
      and (
        p_include_model_generated
        or v.epistemic_status <> 'MODEL_GENERATED_CLAIM'
      )
  ),
  page as (
    select *
    from eligible
    order by record_key, record_id
    limit p_max_records
  )
  select
    coalesce((
      select jsonb_agg(to_jsonb(page) order by record_key, record_id)
      from page
    ), '[]'::jsonb),
    coalesce((
      select jsonb_agg(to_jsonb(record_id) order by record_key, record_id)
      from page
    ), '[]'::jsonb),
    (select count(*)::integer from eligible)
    into recalled_records, recalled_ids, total_matches;

  returned_matches := jsonb_array_length(recalled_records);
  has_more := total_matches > returned_matches;
  completeness := case
    when has_more then 'PARTIAL_TRUNCATED'
    else 'COMPLETE_RELATIVE_TO_QUERY_SCOPE'
  end;
  result_class := case when has_more then 'PARTIAL' else 'COMPLETE' end;
  outcome_code := case
    when has_more then 'MVE_RECALL_PARTIAL_TRUNCATED'
    else 'MVE_RECALL_COMPLETE'
  end;

  retrieval_limitations := jsonb_build_array(
    'Retrieval proves an exposed database read, not recollection or hidden continuity.',
    'retrieval_time is the database invocation time of this recall only; it is not event_time, state_time, record_time, delivery time, recollection time, or receipt-generation time.',
    'This bounded function performs exact-key filtering, not semantic expansion.'
  );
  if has_more then
    retrieval_limitations := retrieval_limitations || jsonb_build_array(
      'Eligible records exceeded p_max_records; the returned page is truncated and has_more is true.'
    );
  end if;

  return jsonb_build_object(
    'schema', 'VERA_MVE_RECEIPT_V3',
    'receipt_id', gen_random_uuid(),
    'request_id', p_request_id,
    'operation', 'RECALL',
    'result_class', result_class,
    'outcome_code', outcome_code,
    'record_ids', recalled_ids,
    'records', recalled_records,
    'retrieval', jsonb_build_object(
      'query_original', jsonb_build_object(
        'project_id', p_project_id,
        'branch_id', p_branch_id,
        'record_keys', to_jsonb(p_record_keys),
        'privacy_scopes', to_jsonb(p_privacy_scopes),
        'include_model_generated', p_include_model_generated,
        'max_records', p_max_records
      ),
      'records_used', recalled_ids,
      'source_surfaces', jsonb_build_array('SUPABASE'),
      'total_matches', total_matches,
      'returned_matches', returned_matches,
      'has_more', has_more,
      'completeness', completeness
    ),
    'write', jsonb_build_object(
      'record_embedded_in_current_chat', false,
      'external_persistence', 'READ_CONFIRMED',
      'transactional_writeback', 'NOT_APPLICABLE'
    ),
    'limitations', retrieval_limitations,
    'retrieval_time', retrieval_time
  );
end;
$$;

revoke all on function public.vera_source_evidence_v3_is_meaningful(jsonb)
  from public, anon, authenticated;
revoke all on function public.vera_semantic_tags_v3_are_meaningful(jsonb)
  from public, anon, authenticated;
revoke all on function public.vera_model_output_v3_has_context(text, text, text, jsonb, jsonb, jsonb)
  from public, anon, authenticated;

revoke all privileges on table public.vera_context_lineage_anomalies_v3
  from public, anon, authenticated, service_role;
grant select on table public.vera_context_lineage_anomalies_v3 to service_role;

comment on constraint vera_context_events_v3_source_evidence_structured_chk
  on public.vera_context_events_v3 is
  'Each source-evidence entry must identify a source surface and at least one bounded attributable observation or reference field.';
comment on constraint vera_context_events_v3_semantic_tags_usable_chk
  on public.vera_context_events_v3 is
  'Semantic tags must contain at least one non-empty string or non-empty string-array value.';
comment on constraint vera_context_events_v3_model_output_context_chk
  on public.vera_context_events_v3 is
  'Model output remains MODEL_OUTPUT/MODEL_GENERATED_CLAIM/CHATGPT_MODEL and retains runtime/source context, generation evidence, and a not-introspective-evidence limitation.';
comment on view public.vera_context_lineage_anomalies_v3 is
  'Diagnostic view exposing scoped cyclic and zero-head lineage components without timestamp-based repair.';
comment on function public.recall_vera_context_v3(
  text, text, text, text[], text[], boolean, integer
) is
  'Receipt-producing exact-key recall with explicit total_matches, returned_matches, has_more, and truthful completeness when p_max_records truncates eligible records.';

commit;
