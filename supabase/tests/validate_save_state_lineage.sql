-- Run only after both temporal draft migrations are applied in an isolated database.
-- All synthetic rows are rolled back.

begin;

do $$
declare
  root_id uuid;
  successor_id uuid;
  other_branch_id uuid;
  self_id uuid;
  stored_record_time timestamptz;
  blocked boolean;
begin
  -- Initial head. The forged record_time must be overwritten by Supabase.
  insert into public.vera_save_state_events (
    project_id,
    branch_id,
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
    record_time,
    payload,
    source_evidence,
    semantic_tags,
    notes
  ) values (
    'vera-temporal-test',
    'branch-a',
    'technical.lineage_validation',
    'TECHNICAL',
    'Synthetic lineage root.',
    'CURRENT',
    'OBSERVED_TOOL_RESULT',
    'SYSTEM_OBSERVATION',
    'TECHNICAL',
    clock_timestamp(),
    'EXACT',
    '2099-01-01 00:00:00+00',
    '1900-01-01 00:00:00+00',
    '{}'::jsonb,
    '[]'::jsonb,
    '{}'::jsonb,
    'Rolled back by validation.'
  )
  returning record_id, record_time into root_id, stored_record_time;

  if stored_record_time = '1900-01-01 00:00:00+00'::timestamptz then
    raise exception 'validation failed: caller forged record_time';
  end if;

  if not exists (
    select 1 from public.vera_current_save_state
    where project_id = 'vera-temporal-test'
      and branch_id = 'branch-a'
      and record_key = 'technical.lineage_validation'
      and record_id = root_id
  ) then
    raise exception 'validation failed: initial root is not current';
  end if;

  -- A second root for the same scoped key must fail.
  blocked := false;
  begin
    insert into public.vera_save_state_events (
      project_id, branch_id, record_key, record_kind, statement,
      lifecycle_status, epistemic_status, authorship, privacy_scope,
      event_time, event_time_precision, state_time
    ) values (
      'vera-temporal-test', 'branch-a', 'technical.lineage_validation',
      'TECHNICAL', 'Invalid second root.', 'CURRENT',
      'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
      clock_timestamp(), 'EXACT', clock_timestamp()
    );
  exception when others then
    blocked := true;
  end;

  if not blocked then
    raise exception 'validation failed: second root was accepted';
  end if;

  -- Caller-supplied self-supersession must fail.
  self_id := gen_random_uuid();
  blocked := false;
  begin
    insert into public.vera_save_state_events (
      record_id, project_id, branch_id, record_key, record_kind, statement,
      lifecycle_status, epistemic_status, authorship, privacy_scope,
      event_time, event_time_precision, state_time, supersedes_record_id
    ) values (
      self_id, 'vera-temporal-test', 'branch-self', 'technical.self_supersession',
      'TECHNICAL', 'Invalid self-supersession.', 'CURRENT',
      'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
      clock_timestamp(), 'EXACT', clock_timestamp(), self_id
    );
  exception when others then
    blocked := true;
  end;

  if not blocked then
    raise exception 'validation failed: self-supersession was accepted';
  end if;

  -- Cross-key supersession must fail.
  blocked := false;
  begin
    insert into public.vera_save_state_events (
      project_id, branch_id, record_key, record_kind, statement,
      lifecycle_status, epistemic_status, authorship, privacy_scope,
      event_time, event_time_precision, state_time, supersedes_record_id
    ) values (
      'vera-temporal-test', 'branch-a', 'technical.different_key',
      'TECHNICAL', 'Invalid cross-key successor.', 'CURRENT',
      'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
      clock_timestamp(), 'EXACT', clock_timestamp(), root_id
    );
  exception when others then
    blocked := true;
  end;

  if not blocked then
    raise exception 'validation failed: cross-key supersession was accepted';
  end if;

  -- Cross-branch supersession must fail.
  blocked := false;
  begin
    insert into public.vera_save_state_events (
      project_id, branch_id, record_key, record_kind, statement,
      lifecycle_status, epistemic_status, authorship, privacy_scope,
      event_time, event_time_precision, state_time, supersedes_record_id
    ) values (
      'vera-temporal-test', 'branch-b', 'technical.lineage_validation',
      'TECHNICAL', 'Invalid cross-branch successor.', 'CURRENT',
      'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
      clock_timestamp(), 'EXACT', clock_timestamp(), root_id
    );
  exception when others then
    blocked := true;
  end;

  if not blocked then
    raise exception 'validation failed: cross-branch supersession was accepted';
  end if;

  -- Cross-project supersession must fail.
  blocked := false;
  begin
    insert into public.vera_save_state_events (
      project_id, branch_id, record_key, record_kind, statement,
      lifecycle_status, epistemic_status, authorship, privacy_scope,
      event_time, event_time_precision, state_time, supersedes_record_id
    ) values (
      'vera-other-project', 'branch-a', 'technical.lineage_validation',
      'TECHNICAL', 'Invalid cross-project successor.', 'CURRENT',
      'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
      clock_timestamp(), 'EXACT', clock_timestamp(), root_id
    );
  exception when others then
    blocked := true;
  end;

  if not blocked then
    raise exception 'validation failed: cross-project supersession was accepted';
  end if;

  -- A valid successor becomes current even with an older state_time.
  insert into public.vera_save_state_events (
    project_id,
    branch_id,
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
    supersedes_record_id,
    payload,
    source_evidence,
    semantic_tags
  ) values (
    'vera-temporal-test',
    'branch-a',
    'technical.lineage_validation',
    'TECHNICAL',
    'Synthetic valid successor.',
    'CURRENT',
    'OBSERVED_TOOL_RESULT',
    'SYSTEM_OBSERVATION',
    'TECHNICAL',
    clock_timestamp(),
    'EXACT',
    '2000-01-01 00:00:00+00',
    root_id,
    '{}'::jsonb,
    '[]'::jsonb,
    '{}'::jsonb
  )
  returning record_id into successor_id;

  if not exists (
    select 1 from public.vera_current_save_state
    where project_id = 'vera-temporal-test'
      and branch_id = 'branch-a'
      and record_key = 'technical.lineage_validation'
      and record_id = successor_id
  ) then
    raise exception 'validation failed: explicit successor is not current';
  end if;

  if exists (
    select 1 from public.vera_current_save_state
    where record_id = root_id
  ) then
    raise exception 'validation failed: superseded root remains current';
  end if;

  -- Forking from the old root must fail.
  blocked := false;
  begin
    insert into public.vera_save_state_events (
      project_id, branch_id, record_key, record_kind, statement,
      lifecycle_status, epistemic_status, authorship, privacy_scope,
      event_time, event_time_precision, state_time, supersedes_record_id
    ) values (
      'vera-temporal-test', 'branch-a', 'technical.lineage_validation',
      'TECHNICAL', 'Invalid fork.', 'CURRENT',
      'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
      clock_timestamp(), 'EXACT', clock_timestamp(), root_id
    );
  exception when others then
    blocked := true;
  end;

  if not blocked then
    raise exception 'validation failed: fork was accepted';
  end if;

  -- The same key may have an independent head in another branch.
  insert into public.vera_save_state_events (
    project_id, branch_id, record_key, record_kind, statement,
    lifecycle_status, epistemic_status, authorship, privacy_scope,
    event_time, event_time_precision, state_time
  ) values (
    'vera-temporal-test', 'branch-b', 'technical.lineage_validation',
    'TECHNICAL', 'Independent branch root.', 'CURRENT',
    'OBSERVED_TOOL_RESULT', 'SYSTEM_OBSERVATION', 'TECHNICAL',
    clock_timestamp(), 'APPROXIMATE', clock_timestamp()
  )
  returning record_id into other_branch_id;

  if (
    select count(*)
    from public.vera_current_save_state
    where project_id = 'vera-temporal-test'
      and record_key = 'technical.lineage_validation'
  ) <> 2 then
    raise exception 'validation failed: branch-scoped heads were collapsed';
  end if;

  if exists (
    select 1
    from public.vera_save_state_lineage_conflicts
    where project_id = 'vera-temporal-test'
  ) then
    raise exception 'validation failed: valid synthetic lineage reported as conflict';
  end if;
end;
$$;

-- Structural and access checks.
do $$
begin
  if not exists (
    select 1 from pg_trigger
    where tgname = 'vera_save_state_events_enforce_lineage'
      and not tgisinternal
  ) then
    raise exception 'validation failed: lineage trigger missing';
  end if;

  if not exists (
    select 1 from pg_indexes
    where schemaname = 'public'
      and indexname = 'vera_save_state_events_one_successor_idx'
  ) then
    raise exception 'validation failed: one-successor index missing';
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'vera_save_state_events_no_self_supersession'
  ) then
    raise exception 'validation failed: self-supersession constraint missing';
  end if;

  if has_table_privilege('anon', 'public.vera_save_state_heads', 'SELECT')
     or has_table_privilege('authenticated', 'public.vera_save_state_heads', 'SELECT')
     or has_table_privilege('anon', 'public.vera_save_state_lineage_conflicts', 'SELECT')
     or has_table_privilege('authenticated', 'public.vera_save_state_lineage_conflicts', 'SELECT') then
    raise exception 'validation failed: client role can read lineage views';
  end if;

  if not has_table_privilege('service_role', 'public.vera_current_save_state', 'SELECT')
     or not has_table_privilege('service_role', 'public.vera_save_state_heads', 'SELECT')
     or not has_table_privilege('service_role', 'public.vera_save_state_lineage_conflicts', 'SELECT') then
    raise exception 'validation failed: service_role cannot read required views';
  end if;
end;
$$;

rollback;
