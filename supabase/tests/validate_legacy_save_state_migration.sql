-- Run after the temporal precision and lineage drafts in an isolated database.
-- Verifies representative pre-existing rows survive migration unchanged except
-- for the intended event_time_precision backfill.

do $$
declare
  legacy_count integer;
begin
  select count(*) into legacy_count
  from public.vera_save_state_events
  where project_id = 'vera-legacy-test';

  if legacy_count <> 3 then
    raise exception 'legacy migration validation failed: expected 3 rows, found %', legacy_count;
  end if;

  if exists (
    select 1
    from public.vera_save_state_events
    where project_id = 'vera-legacy-test'
      and event_time_precision <> 'APPROXIMATE'
  ) then
    raise exception 'legacy migration validation failed: legacy precision backfill is not uniformly APPROXIMATE';
  end if;

  if not exists (
    select 1 from public.vera_save_state_events
    where record_id = '10000000-0000-0000-0000-000000000001'
      and statement = 'Legacy root row.'
      and event_time = '2026-07-01 12:00:00+00'::timestamptz
      and state_time = '2026-07-10 12:00:00+00'::timestamptz
      and record_time = '2026-07-01 12:00:01+00'::timestamptz
      and supersedes_record_id is null
      and payload = '{"fixture":"legacy-root","preserve":true}'::jsonb
      and source_evidence = '[{"source":"legacy-fixture","ordinal":1}]'::jsonb
      and semantic_tags = '{"topics":["temporal","legacy"]}'::jsonb
  ) then
    raise exception 'legacy migration validation failed: root row changed unexpectedly';
  end if;

  if not exists (
    select 1 from public.vera_save_state_events
    where record_id = '10000000-0000-0000-0000-000000000002'
      and statement = 'Legacy successor row.'
      and event_time = '2026-07-02 12:00:00+00'::timestamptz
      and state_time = '2026-06-01 12:00:00+00'::timestamptz
      and record_time = '2026-07-02 12:00:01+00'::timestamptz
      and supersedes_record_id = '10000000-0000-0000-0000-000000000001'::uuid
      and payload = '{"fixture":"legacy-successor","preserve":true}'::jsonb
      and source_evidence = '[{"source":"legacy-fixture","ordinal":2}]'::jsonb
      and semantic_tags = '{"topics":["temporal","legacy"]}'::jsonb
  ) then
    raise exception 'legacy migration validation failed: successor row changed unexpectedly';
  end if;

  if not exists (
    select 1 from public.vera_save_state_events
    where record_id = '10000000-0000-0000-0000-000000000003'
      and statement = 'Legacy independent row.'
      and event_time = '2026-07-03 12:00:00+00'::timestamptz
      and state_time = '2026-07-03 12:00:00+00'::timestamptz
      and record_time = '2026-07-03 12:00:01+00'::timestamptz
      and supersedes_record_id is null
      and payload = '{"fixture":"legacy-independent","preserve":true}'::jsonb
      and source_evidence = '[{"source":"legacy-fixture","ordinal":3}]'::jsonb
      and semantic_tags = '{"topics":["temporal","legacy"]}'::jsonb
  ) then
    raise exception 'legacy migration validation failed: independent row changed unexpectedly';
  end if;

  if not exists (
    select 1 from public.vera_current_save_state
    where record_id = '10000000-0000-0000-0000-000000000002'
      and project_id = 'vera-legacy-test'
      and branch_id = 'branch-a'
      and record_key = 'technical.legacy_chain'
  ) then
    raise exception 'legacy migration validation failed: explicit successor is not current';
  end if;

  if exists (
    select 1 from public.vera_current_save_state
    where record_id = '10000000-0000-0000-0000-000000000001'
  ) then
    raise exception 'legacy migration validation failed: superseded root remains current';
  end if;

  if not exists (
    select 1 from public.vera_current_save_state
    where record_id = '10000000-0000-0000-0000-000000000003'
      and project_id = 'vera-legacy-test'
      and branch_id = 'branch-b'
      and record_key = 'technical.legacy_independent'
  ) then
    raise exception 'legacy migration validation failed: independent legacy head is missing';
  end if;

  if exists (
    select 1 from public.vera_save_state_lineage_conflicts
    where project_id = 'vera-legacy-test'
  ) then
    raise exception 'legacy migration validation failed: valid legacy rows reported as a conflict';
  end if;
end;
$$;