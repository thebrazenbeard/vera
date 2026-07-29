-- Run only after applying the draft migration in an isolated test database.
-- The transaction is rolled back so the synthetic record is never retained.

begin;

-- Structural checks.
do $$
begin
  if exists (
    select 1
    from public.vera_save_state_events
    where event_time is null
  ) then
    raise exception 'validation failed: event_time contains NULL';
  end if;

  if exists (
    select 1
    from public.vera_save_state_events
    where event_time_precision not in ('EXACT', 'APPROXIMATE')
  ) then
    raise exception 'validation failed: invalid event_time_precision';
  end if;

  if not exists (
    select 1
    from pg_constraint
    where conname = 'vera_save_state_events_event_time_precision_check'
  ) then
    raise exception 'validation failed: precision constraint missing';
  end if;
end;
$$;

-- Synthetic insert and append-only enforcement checks.
insert into public.vera_save_state_events (
  record_key,
  record_kind,
  statement,
  lifecycle_status,
  epistemic_status,
  authorship,
  privacy_scope,
  event_time,
  event_time_precision,
  state_time,
  payload,
  source_evidence,
  semantic_tags,
  notes
) values (
  'technical.synthetic_temporal_validation',
  'TECHNICAL',
  'Synthetic temporal validation record.',
  'CURRENT',
  'OBSERVED_TOOL_RESULT',
  'SYSTEM_OBSERVATION',
  'TECHNICAL',
  clock_timestamp(),
  'EXACT',
  clock_timestamp(),
  '{}'::jsonb,
  '[]'::jsonb,
  '{}'::jsonb,
  'Rolled back by validation script.'
);

do $$
declare
  target_id uuid;
  mutation_blocked boolean := false;
begin
  select record_id into target_id
  from public.vera_save_state_events
  where record_key = 'technical.synthetic_temporal_validation'
  order by record_time desc
  limit 1;

  begin
    update public.vera_save_state_events
    set notes = 'this update must fail'
    where record_id = target_id;
  exception when others then
    mutation_blocked := true;
  end;

  if not mutation_blocked then
    raise exception 'validation failed: update was not blocked';
  end if;

  mutation_blocked := false;

  begin
    delete from public.vera_save_state_events
    where record_id = target_id;
  exception when others then
    mutation_blocked := true;
  end;

  if not mutation_blocked then
    raise exception 'validation failed: delete was not blocked';
  end if;
end;
$$;

-- Access-surface checks.
do $$
begin
  if has_table_privilege('anon', 'public.vera_save_state_events', 'SELECT')
     or has_table_privilege('authenticated', 'public.vera_save_state_events', 'SELECT') then
    raise exception 'validation failed: client role can read event table';
  end if;

  if has_table_privilege('service_role', 'public.vera_save_state_events', 'UPDATE')
     or has_table_privilege('service_role', 'public.vera_save_state_events', 'DELETE')
     or has_table_privilege('service_role', 'public.vera_save_state_events', 'TRUNCATE') then
    raise exception 'validation failed: service_role has mutation privilege beyond INSERT';
  end if;
end;
$$;

rollback;
