-- Run only after applying the promoted temporal migrations in an isolated test database.
-- The transaction is rolled back so synthetic records are never retained.

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
    where event_time_precision not in ('EXACT', 'BOUNDED', 'APPROXIMATE', 'UNKNOWN')
  ) then
    raise exception 'validation failed: invalid event_time_precision';
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'vera_save_state_events_event_time_precision_check'
  ) then
    raise exception 'validation failed: precision constraint missing';
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'vera_save_state_events_event_time_bounds_check'
  ) then
    raise exception 'validation failed: bounds constraint missing';
  end if;

  if not exists (
    select 1 from information_schema.columns
    where table_schema = 'public'
      and table_name = 'vera_save_state_events'
      and column_name = 'event_time_lower_bound'
      and data_type = 'timestamp with time zone'
  ) or not exists (
    select 1 from information_schema.columns
    where table_schema = 'public'
      and table_name = 'vera_save_state_events'
      and column_name = 'event_time_upper_bound'
      and data_type = 'timestamp with time zone'
  ) then
    raise exception 'validation failed: bounded evidence columns missing';
  end if;
end;
$$;

-- Valid EXACT record used for append-only checks.
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

-- Valid BOUNDED evidence requires inclusive lower and upper bounds.
insert into public.vera_save_state_events (
  record_key, record_kind, statement, lifecycle_status, epistemic_status,
  authorship, privacy_scope, event_time, event_time_precision,
  event_time_lower_bound, event_time_upper_bound, state_time
) values (
  'technical.synthetic_bounded_temporal_validation',
  'TECHNICAL',
  'Synthetic bounded temporal validation record.',
  'CURRENT',
  'OBSERVED_TOOL_RESULT',
  'SYSTEM_OBSERVATION',
  'TECHNICAL',
  '2026-07-29 14:00:00+00',
  'BOUNDED',
  '2026-07-29 13:55:00+00',
  '2026-07-29 14:05:00+00',
  '2026-07-29 14:00:00+00'
);

do $$
declare
  blocked boolean;
begin
  -- BOUNDED without both bounds must fail.
  blocked := false;
  begin
    insert into public.vera_save_state_events (
      record_key, record_kind, statement, lifecycle_status, epistemic_status,
      authorship, privacy_scope, event_time, event_time_precision,
      event_time_lower_bound, state_time
    ) values (
      'technical.invalid_bounded_missing_upper', 'TECHNICAL',
      'Invalid bounded record without upper bound.', 'CURRENT',
      'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
      clock_timestamp(), 'BOUNDED', clock_timestamp(), clock_timestamp()
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'validation failed: BOUNDED record without both bounds was accepted';
  end if;

  -- Inverted bounds must fail.
  blocked := false;
  begin
    insert into public.vera_save_state_events (
      record_key, record_kind, statement, lifecycle_status, epistemic_status,
      authorship, privacy_scope, event_time, event_time_precision,
      event_time_lower_bound, event_time_upper_bound, state_time
    ) values (
      'technical.invalid_bounded_inverted', 'TECHNICAL',
      'Invalid bounded record with inverted bounds.', 'CURRENT',
      'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
      '2026-07-29 14:00:00+00', 'BOUNDED',
      '2026-07-29 14:05:00+00', '2026-07-29 13:55:00+00',
      '2026-07-29 14:00:00+00'
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'validation failed: inverted bounded interval was accepted';
  end if;

  -- Non-BOUNDED precision may not carry bounds.
  blocked := false;
  begin
    insert into public.vera_save_state_events (
      record_key, record_kind, statement, lifecycle_status, epistemic_status,
      authorship, privacy_scope, event_time, event_time_precision,
      event_time_lower_bound, event_time_upper_bound, state_time
    ) values (
      'technical.invalid_exact_with_bounds', 'TECHNICAL',
      'Invalid exact record with range fields.', 'CURRENT',
      'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
      '2026-07-29 14:00:00+00', 'EXACT',
      '2026-07-29 13:55:00+00', '2026-07-29 14:05:00+00',
      '2026-07-29 14:00:00+00'
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'validation failed: non-BOUNDED record with bounds was accepted';
  end if;
end;
$$;

-- Append-only enforcement checks.
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
