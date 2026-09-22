-- Bounded Memory workstream migration.
--
-- This migration hardens the already-installed neutral V3 context table. It is
-- version-controlled source only until separately authorized for production.
-- It does not modify the Time or Initiatives workstreams.

begin;

-- Refuse promotion over an unknown or already-conflicted baseline.
do $$
begin
  if to_regclass('public.vera_context_events_v3') is null then
    raise exception 'public.vera_context_events_v3 does not exist';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3
    where supersedes_record_id = record_id
  ) then
    raise exception 'neutral V3 baseline contains self-supersession';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3 child
    join public.vera_context_events_v3 parent
      on parent.record_id = child.supersedes_record_id
    where child.project_id <> parent.project_id
       or child.branch_id <> parent.branch_id
       or child.record_key <> parent.record_key
  ) then
    raise exception 'neutral V3 baseline contains cross-scope supersession';
  end if;

  if exists (
    select supersedes_record_id
    from public.vera_context_events_v3
    where supersedes_record_id is not null
    group by supersedes_record_id
    having count(*) > 1
  ) then
    raise exception 'neutral V3 baseline contains a supersession fork';
  end if;

  if exists (
    select 1
    from (
      select e.project_id, e.branch_id, e.record_key, count(*) as head_count
      from public.vera_context_events_v3 e
      where not exists (
        select 1
        from public.vera_context_events_v3 child
        where child.supersedes_record_id = e.record_id
      )
      group by e.project_id, e.branch_id, e.record_key
      having count(*) > 1
    ) conflicts
  ) then
    raise exception 'neutral V3 baseline contains multiple current heads';
  end if;
end;
$$;

create unique index if not exists vera_context_events_v3_one_successor_uidx
  on public.vera_context_events_v3 (supersedes_record_id)
  where supersedes_record_id is not null;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'vera_context_events_v3_no_self_supersession_chk'
      and conrelid = 'public.vera_context_events_v3'::regclass
  ) then
    alter table public.vera_context_events_v3
      add constraint vera_context_events_v3_no_self_supersession_chk
      check (supersedes_record_id is null or supersedes_record_id <> record_id);
  end if;
end;
$$;

create or replace function public.enforce_vera_context_v3_lineage()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
declare
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
    (array_agg(e.record_id order by e.record_id))[1]
    into current_head_count, current_head_id
  from public.vera_context_events_v3 e
  where e.project_id = new.project_id
    and e.branch_id = new.branch_id
    and e.record_key = new.record_key
    and not exists (
      select 1
      from public.vera_context_events_v3 child
      where child.supersedes_record_id = e.record_id
    );

  if current_head_count = 0 then
    if new.supersedes_record_id is not null then
      raise exception 'initial neutral V3 record for a scoped key may not supersede another record';
    end if;
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

create or replace function public.block_vera_context_v3_mutation()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
begin
  raise exception 'vera_context_events_v3 is append-only; append a superseding record instead';
end;
$$;

revoke all on function public.enforce_vera_context_v3_lineage()
  from public, anon, authenticated;
revoke all on function public.block_vera_context_v3_mutation()
  from public, anon, authenticated;

drop trigger if exists vera_context_events_v3_enforce_lineage
  on public.vera_context_events_v3;
create trigger vera_context_events_v3_enforce_lineage
before insert on public.vera_context_events_v3
for each row execute function public.enforce_vera_context_v3_lineage();

drop trigger if exists vera_context_events_v3_block_mutation
  on public.vera_context_events_v3;
create trigger vera_context_events_v3_block_mutation
before update or delete on public.vera_context_events_v3
for each row execute function public.block_vera_context_v3_mutation();

create or replace view public.vera_context_heads_v3
with (security_invoker = true)
as
select e.*
from public.vera_context_events_v3 e
where not exists (
  select 1
  from public.vera_context_events_v3 child
  where child.supersedes_record_id = e.record_id
);

create or replace view public.vera_context_lineage_conflicts_v3
with (security_invoker = true)
as
select
  project_id,
  branch_id,
  record_key,
  count(*) as head_count,
  array_agg(record_id order by record_time, record_id) as head_record_ids
from public.vera_context_heads_v3
group by project_id, branch_id, record_key
having count(*) > 1;

drop view if exists public.vera_current_context_v3;
create view public.vera_current_context_v3
with (security_invoker = true)
as
with heads as (
  select
    h.*,
    count(*) over (
      partition by h.project_id, h.branch_id, h.record_key
    ) as head_count
  from public.vera_context_heads_v3 h
)
select
  record_id,
  project_id,
  branch_id,
  record_key,
  record_type,
  statement,
  lifecycle_status,
  epistemic_status,
  source_actor,
  privacy_scope,
  event_time,
  state_time,
  record_time,
  supersedes_record_id,
  legacy_record_id,
  payload,
  source_evidence,
  semantic_tags,
  limitations,
  notes
from heads
where head_count = 1;

create or replace function public.append_vera_context_v3(
  p_request_id text,
  p_record jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  stored public.vera_context_events_v3%rowtype;
  unknown_key text;
  normalized_payload jsonb := coalesce(p_record->'payload', '{}'::jsonb);
  normalized_limitations jsonb := coalesce(p_record->'limitations', '[]'::jsonb);
  event_time_value timestamptz;
  state_time_value timestamptz;
  event_precision text;
  state_precision text;
  state_derivation jsonb;
  derivation_method text;
  derivation_limitation text;
  event_time_supplied boolean;
  state_time_supplied boolean;
  unknown_state_limitation text := 'state_time is UNKNOWN; the non-null column contains PostgreSQL -infinity only as a compatibility sentinel and not as event, state, record, delivery, recollection, or receipt-generation time evidence.';
begin
  if p_request_id is null or coalesce(btrim(p_request_id), '') = '' then
    raise exception 'p_request_id must be non-empty';
  end if;

  if p_record is null or jsonb_typeof(p_record) <> 'object' then
    raise exception 'p_record must be a JSON object';
  end if;

  select key into unknown_key
  from jsonb_object_keys(p_record) as key
  where key not in (
    'project_id', 'branch_id', 'record_key', 'record_type', 'statement',
    'lifecycle_status', 'epistemic_status', 'source_actor', 'privacy_scope',
    'event_time', 'state_time', 'supersedes_record_id', 'legacy_record_id',
    'payload', 'source_evidence', 'semantic_tags', 'limitations', 'notes'
  )
  limit 1;

  if unknown_key is not null then
    raise exception 'p_record contains unsupported field %', unknown_key;
  end if;

  if coalesce(btrim(p_record->>'project_id'), '') = ''
     or coalesce(btrim(p_record->>'branch_id'), '') = ''
     or coalesce(btrim(p_record->>'record_key'), '') = ''
     or coalesce(btrim(p_record->>'record_type'), '') = ''
     or coalesce(btrim(p_record->>'statement'), '') = ''
     or coalesce(btrim(p_record->>'lifecycle_status'), '') = ''
     or coalesce(btrim(p_record->>'epistemic_status'), '') = ''
     or coalesce(btrim(p_record->>'source_actor'), '') = ''
     or coalesce(btrim(p_record->>'privacy_scope'), '') = '' then
    raise exception 'p_record is missing a required non-empty field';
  end if;

  if jsonb_typeof(normalized_payload) <> 'object' then
    raise exception 'payload must be a JSON object';
  end if;
  if jsonb_typeof(normalized_limitations) <> 'array' then
    raise exception 'limitations must be a JSON array';
  end if;

  event_time_supplied := nullif(p_record->>'event_time', '') is not null;
  state_time_supplied := nullif(p_record->>'state_time', '') is not null;
  event_time_value := nullif(p_record->>'event_time', '')::timestamptz;
  state_time_value := nullif(p_record->>'state_time', '')::timestamptz;

  if normalized_payload->'temporal' is null then
    normalized_payload := jsonb_set(normalized_payload, '{temporal}', '{}'::jsonb, true);
  elsif jsonb_typeof(normalized_payload->'temporal') <> 'object' then
    raise exception 'payload.temporal must be a JSON object';
  end if;

  if normalized_payload#>'{temporal,event_time}' is null then
    normalized_payload := jsonb_set(
      normalized_payload, '{temporal,event_time}', '{}'::jsonb, true
    );
  elsif jsonb_typeof(normalized_payload#>'{temporal,event_time}') <> 'object' then
    raise exception 'payload.temporal.event_time must be a JSON object';
  end if;

  if normalized_payload#>'{temporal,state_time}' is null then
    normalized_payload := jsonb_set(
      normalized_payload, '{temporal,state_time}', '{}'::jsonb, true
    );
  elsif jsonb_typeof(normalized_payload#>'{temporal,state_time}') <> 'object' then
    raise exception 'payload.temporal.state_time must be a JSON object';
  end if;

  event_precision := normalized_payload#>>'{temporal,event_time,precision}';
  if event_precision is null then
    event_precision := 'UNKNOWN';
    normalized_payload := jsonb_set(
      normalized_payload,
      '{temporal,event_time,precision}',
      to_jsonb(event_precision),
      true
    );
  end if;

  state_precision := normalized_payload#>>'{temporal,state_time,precision}';
  if state_precision is null then
    state_precision := 'UNKNOWN';
    normalized_payload := jsonb_set(
      normalized_payload,
      '{temporal,state_time,precision}',
      to_jsonb(state_precision),
      true
    );
  end if;

  if event_precision not in ('EXACT', 'BOUNDED', 'APPROXIMATE', 'UNKNOWN') then
    raise exception 'event_time precision must be EXACT, BOUNDED, APPROXIMATE, or UNKNOWN';
  end if;
  if state_precision not in ('EXACT', 'BOUNDED', 'APPROXIMATE', 'UNKNOWN') then
    raise exception 'state_time precision must be EXACT, BOUNDED, APPROXIMATE, or UNKNOWN';
  end if;

  if not event_time_supplied and event_precision <> 'UNKNOWN' then
    raise exception 'event_time without a timestamp must use UNKNOWN precision';
  end if;
  if not state_time_supplied and state_precision <> 'UNKNOWN' then
    raise exception 'state_time without a timestamp must use UNKNOWN precision';
  end if;

  if not state_time_supplied then
    state_time_value := '-infinity'::timestamptz;
    normalized_payload := jsonb_set(
      normalized_payload,
      '{temporal,state_time,storage}',
      jsonb_build_object(
        'mode', 'NOT_NULL_COMPATIBILITY_SENTINEL',
        'value', '-infinity',
        'temporal_claim', false
      ),
      true
    );
    if not normalized_limitations @> jsonb_build_array(unknown_state_limitation) then
      normalized_limitations := normalized_limitations || jsonb_build_array(unknown_state_limitation);
    end if;
  end if;

  state_derivation := normalized_payload#>'{temporal,state_time,derivation}';
  if state_derivation is not null then
    if not state_time_supplied then
      raise exception 'derived state_time requires an explicit timestamp';
    end if;
    if jsonb_typeof(state_derivation) <> 'object' then
      raise exception 'state_time derivation must be a JSON object';
    end if;

    derivation_method := btrim(coalesce(state_derivation->>'method', ''));
    derivation_limitation := btrim(coalesce(state_derivation->>'limitation', ''));

    if derivation_method = '' then
      raise exception 'derived state_time requires a non-empty derivation method';
    end if;
    if jsonb_typeof(state_derivation->'source_evidence') <> 'array'
       or jsonb_array_length(state_derivation->'source_evidence') = 0 then
      raise exception 'derived state_time requires non-empty source_evidence';
    end if;
    if derivation_limitation = '' then
      raise exception 'derived state_time requires a non-empty limitation';
    end if;
    if not normalized_limitations @> jsonb_build_array(derivation_limitation) then
      raise exception 'derived state_time limitation must also appear in record limitations';
    end if;
  end if;

  insert into public.vera_context_events_v3 (
    project_id,
    branch_id,
    record_key,
    record_type,
    statement,
    lifecycle_status,
    epistemic_status,
    source_actor,
    privacy_scope,
    event_time,
    state_time,
    supersedes_record_id,
    legacy_record_id,
    payload,
    source_evidence,
    semantic_tags,
    limitations,
    notes
  ) values (
    p_record->>'project_id',
    p_record->>'branch_id',
    p_record->>'record_key',
    p_record->>'record_type',
    p_record->>'statement',
    p_record->>'lifecycle_status',
    p_record->>'epistemic_status',
    p_record->>'source_actor',
    p_record->>'privacy_scope',
    event_time_value,
    state_time_value,
    nullif(p_record->>'supersedes_record_id', '')::uuid,
    nullif(p_record->>'legacy_record_id', '')::uuid,
    normalized_payload,
    coalesce(p_record->'source_evidence', '[]'::jsonb),
    coalesce(p_record->'semantic_tags', '{}'::jsonb),
    normalized_limitations,
    p_record->>'notes'
  )
  returning * into stored;

  return jsonb_build_object(
    'schema', 'VERA_MVE_RECEIPT_V3',
    'receipt_id', gen_random_uuid(),
    'request_id', p_request_id,
    'operation', 'SAVE',
    'result_class', 'COMPLETE',
    'outcome_code', 'MVE_SAVE_COMPLETE',
    'record_ids', jsonb_build_array(stored.record_id),
    'records', jsonb_build_array(to_jsonb(stored)),
    'write', jsonb_build_object(
      'record_embedded_in_current_chat', false,
      'external_persistence', 'CONFIRMED_BY_DATABASE',
      'transactional_writeback', 'COMPLETED'
    ),
    'limitations', jsonb_build_array(
      'The receipt proves a database write, not lived memory or hidden synchronization.'
    ),
    'record_time', stored.record_time
  );
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

  with selected as (
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
    order by v.record_key, v.record_id
    limit p_max_records
  )
  select
    coalesce(jsonb_agg(to_jsonb(selected) order by record_key, record_id), '[]'::jsonb),
    coalesce(jsonb_agg(to_jsonb(record_id) order by record_key, record_id), '[]'::jsonb)
    into recalled_records, recalled_ids
  from selected;

  return jsonb_build_object(
    'schema', 'VERA_MVE_RECEIPT_V3',
    'receipt_id', gen_random_uuid(),
    'request_id', p_request_id,
    'operation', 'RECALL',
    'result_class', 'COMPLETE',
    'outcome_code', 'MVE_RECALL_COMPLETE',
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
      'completeness', 'COMPLETE_RELATIVE_TO_QUERY_SCOPE'
    ),
    'write', jsonb_build_object(
      'record_embedded_in_current_chat', false,
      'external_persistence', 'READ_CONFIRMED',
      'transactional_writeback', 'NOT_APPLICABLE'
    ),
    'limitations', jsonb_build_array(
      'Retrieval proves an exposed database read, not recollection or hidden continuity.',
      'retrieval_time is the database invocation time of this recall only; it is not event_time, state_time, record_time, delivery time, recollection time, or receipt-generation time.',
      'This bounded function performs exact-key filtering, not semantic expansion.'
    ),
    'retrieval_time', retrieval_time
  );
end;
$$;

revoke all on function public.append_vera_context_v3(text, jsonb)
  from public, anon, authenticated;
revoke all on function public.recall_vera_context_v3(
  text, text, text, text[], text[], boolean, integer
) from public, anon, authenticated;

grant execute on function public.append_vera_context_v3(text, jsonb)
  to service_role;
grant execute on function public.recall_vera_context_v3(
  text, text, text, text[], text[], boolean, integer
) to service_role;

revoke all privileges on table public.vera_context_events_v3 from service_role;
grant select on table public.vera_context_events_v3 to service_role;

revoke all privileges on table public.vera_context_heads_v3
  from public, anon, authenticated, service_role;
revoke all privileges on table public.vera_context_lineage_conflicts_v3
  from public, anon, authenticated, service_role;
revoke all privileges on table public.vera_current_context_v3
  from public, anon, authenticated, service_role;

grant select on table public.vera_context_heads_v3 to service_role;
grant select on table public.vera_context_lineage_conflicts_v3 to service_role;
grant select on table public.vera_current_context_v3 to service_role;

comment on table public.vera_context_events_v3 is
  'Append-only neutral V.E.R.A. context records. Database receipts prove exposed persistence only.';
comment on column public.vera_context_events_v3.event_time is
  'Source-supported event time. Precision is explicit in payload.temporal.event_time.precision and defaults to UNKNOWN, never silently EXACT.';
comment on column public.vera_context_events_v3.state_time is
  'Represented state time. When the live NOT NULL schema receives no state_time, -infinity is used only as an explicitly UNKNOWN compatibility sentinel described in payload and limitations.';
comment on column public.vera_context_events_v3.record_time is
  'Database-assigned persistence time. Caller-supplied values are overwritten by the insert trigger.';
comment on view public.vera_current_context_v3 is
  'One unambiguous lineage head per project, branch, and record key. Recency does not create authority.';
comment on view public.vera_context_lineage_conflicts_v3 is
  'Diagnostic view for scoped keys with multiple lineage heads. Conflicts are exposed, not timestamp-resolved.';
comment on function public.append_vera_context_v3(text, jsonb) is
  'Receipt-producing bounded append interface with explicit temporal precision and evidence-backed derived state_time handling.';
comment on function public.recall_vera_context_v3(
  text, text, text, text[], text[], boolean, integer
) is
  'Receipt-producing exact-key recall with an explicit retrieval_time distinct from event, state, record, delivery, recollection, and receipt-generation time.';

commit;