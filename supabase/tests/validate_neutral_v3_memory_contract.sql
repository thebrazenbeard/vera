-- Run after the neutral V3 live-schema fixture and bounded Memory migration.
-- Synthetic mutations are rolled back.

begin;

do $$
declare
  root_id uuid;
  successor_id uuid;
  receipt jsonb;
  blocked boolean;
  forged_time timestamptz := '1900-01-01 00:00:00+00';
begin
  if to_regclass('public.vera_context_heads_v3') is null
     or to_regclass('public.vera_context_lineage_conflicts_v3') is null then
    raise exception 'validation failed: lineage views are missing';
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgrelid = 'public.vera_context_events_v3'::regclass
      and tgname = 'vera_context_events_v3_enforce_lineage'
      and not tgisinternal
  ) then
    raise exception 'validation failed: lineage trigger is missing';
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgrelid = 'public.vera_context_events_v3'::regclass
      and tgname = 'vera_context_events_v3_block_mutation'
      and not tgisinternal
  ) then
    raise exception 'validation failed: append-only mutation trigger is missing';
  end if;

  if not exists (
    select 1 from pg_indexes
    where schemaname = 'public'
      and indexname = 'vera_context_events_v3_one_successor_uidx'
  ) then
    raise exception 'validation failed: one-successor index is missing';
  end if;

  if not exists (
    select 1 from public.vera_current_context_v3
    where record_id = '10000000-0000-0000-0000-000000000002'
      and project_id = 'vera-memory-fixture'
      and branch_id = 'branch-a'
      and record_key = 'memory.fixture.chain'
      and statement = 'Fixture successor.'
      and payload = '{"fixture":"successor","preserve":true}'::jsonb
  ) then
    raise exception 'validation failed: explicit fixture successor is not current';
  end if;

  if exists (
    select 1 from public.vera_current_context_v3
    where record_id = '10000000-0000-0000-0000-000000000001'
  ) then
    raise exception 'validation failed: superseded fixture root remains current';
  end if;

  if not exists (
    select 1 from public.vera_current_context_v3
    where record_id = '10000000-0000-0000-0000-000000000003'
      and branch_id = 'branch-b'
  ) then
    raise exception 'validation failed: independent branch fixture is missing';
  end if;

  if exists (select 1 from public.vera_context_lineage_conflicts_v3) then
    raise exception 'validation failed: valid fixture lineage reports a conflict';
  end if;

  receipt := public.append_vera_context_v3(
    'MREQ-contract-root',
    jsonb_build_object(
      'project_id', 'vera-memory-contract-test',
      'branch_id', 'branch-a',
      'record_key', 'memory.contract.lineage',
      'record_type', 'DECISION',
      'statement', 'Contract test root.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'DIRECT_USER_STATEMENT',
      'source_actor', 'USER',
      'privacy_scope', 'PROJECT',
      'event_time', '2026-07-30T21:00:00+00:00',
      'state_time', '2026-07-30T21:00:00+00:00',
      'payload', jsonb_build_object('test', true),
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'claim', 'root')
      ),
      'semantic_tags', jsonb_build_object(
        'domain', jsonb_build_array('memory'),
        'status', jsonb_build_array('current')
      ),
      'limitations', jsonb_build_array('Synthetic test-only record.'),
      'notes', 'Caller attempts to forge record_time are not accepted by the API.'
    )
  );

  if receipt->>'operation' <> 'SAVE'
     or receipt#>>'{write,external_persistence}' <> 'CONFIRMED_BY_DATABASE'
     or jsonb_array_length(receipt->'record_ids') <> 1 then
    raise exception 'validation failed: save receipt is incomplete';
  end if;

  root_id := (receipt#>>'{record_ids,0}')::uuid;

  select record_time into forged_time
  from public.vera_context_events_v3
  where record_id = root_id;

  if forged_time = '1900-01-01 00:00:00+00'::timestamptz then
    raise exception 'validation failed: caller forged database record_time';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-second-root',
      jsonb_build_object(
        'project_id', 'vera-memory-contract-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.contract.lineage',
        'record_type', 'DECISION',
        'statement', 'Invalid second root.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'DIRECT_USER_STATEMENT',
        'source_actor', 'USER',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('domain', jsonb_build_array('memory'))
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'validation failed: second root was accepted';
  end if;

  receipt := public.append_vera_context_v3(
    'MREQ-contract-successor',
    jsonb_build_object(
      'project_id', 'vera-memory-contract-test',
      'branch_id', 'branch-a',
      'record_key', 'memory.contract.lineage',
      'record_type', 'CORRECTION',
      'statement', 'Contract test successor.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'DIRECT_USER_STATEMENT',
      'source_actor', 'USER',
      'privacy_scope', 'PROJECT',
      'event_time', '2026-07-30T21:01:00+00:00',
      'state_time', '2000-01-01T00:00:00+00:00',
      'supersedes_record_id', root_id,
      'payload', jsonb_build_object('test', true, 'revision', 2),
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'claim', 'successor')
      ),
      'semantic_tags', jsonb_build_object(
        'domain', jsonb_build_array('memory'),
        'status', jsonb_build_array('current', 'corrected')
      ),
      'limitations', jsonb_build_array('Synthetic test-only record.')
    )
  );
  successor_id := (receipt#>>'{record_ids,0}')::uuid;

  if not exists (
    select 1 from public.vera_current_context_v3
    where record_id = successor_id
      and statement = 'Contract test successor.'
      and state_time = '2000-01-01 00:00:00+00'::timestamptz
  ) then
    raise exception 'validation failed: lineage successor did not beat newer root state_time';
  end if;

  if exists (
    select 1 from public.vera_current_context_v3
    where record_id = root_id
  ) then
    raise exception 'validation failed: contract root remains current after correction';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-fork',
      jsonb_build_object(
        'project_id', 'vera-memory-contract-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.contract.lineage',
        'record_type', 'CORRECTION',
        'statement', 'Invalid fork from stale root.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'DIRECT_USER_STATEMENT',
        'source_actor', 'USER',
        'privacy_scope', 'PROJECT',
        'supersedes_record_id', root_id,
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('domain', jsonb_build_array('memory'))
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'validation failed: stale-parent fork was accepted';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-cross-branch',
      jsonb_build_object(
        'project_id', 'vera-memory-contract-test',
        'branch_id', 'branch-b',
        'record_key', 'memory.contract.lineage',
        'record_type', 'CORRECTION',
        'statement', 'Invalid cross-branch successor.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'DIRECT_USER_STATEMENT',
        'source_actor', 'USER',
        'privacy_scope', 'PROJECT',
        'supersedes_record_id', successor_id,
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('domain', jsonb_build_array('memory'))
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'validation failed: cross-branch supersession was accepted';
  end if;

  blocked := false;
  begin
    update public.vera_context_events_v3
    set notes = 'forbidden update'
    where record_id = root_id;
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'validation failed: update was not blocked';
  end if;

  blocked := false;
  begin
    delete from public.vera_context_events_v3
    where record_id = root_id;
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'validation failed: delete was not blocked';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-unknown-field',
      jsonb_build_object(
        'project_id', 'vera-memory-contract-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.contract.unknown',
        'record_type', 'DECISION',
        'statement', 'Unknown field must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'DIRECT_USER_STATEMENT',
        'source_actor', 'USER',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('domain', jsonb_build_array('memory')),
        'invented_authority', true
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'validation failed: unknown save field was accepted';
  end if;
end;
$$;

-- Access-surface checks are outside the procedural block for readable failures.
do $$
begin
  if has_table_privilege('service_role', 'public.vera_context_events_v3', 'INSERT')
     or has_table_privilege('service_role', 'public.vera_context_events_v3', 'UPDATE')
     or has_table_privilege('service_role', 'public.vera_context_events_v3', 'DELETE')
     or has_table_privilege('service_role', 'public.vera_context_events_v3', 'TRUNCATE') then
    raise exception 'validation failed: service_role retains direct mutation privileges';
  end if;

  if not has_table_privilege('service_role', 'public.vera_context_events_v3', 'SELECT')
     or not has_table_privilege('service_role', 'public.vera_current_context_v3', 'SELECT')
     or not has_table_privilege('service_role', 'public.vera_context_heads_v3', 'SELECT')
     or not has_table_privilege('service_role', 'public.vera_context_lineage_conflicts_v3', 'SELECT') then
    raise exception 'validation failed: service_role lacks required diagnostic reads';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.append_vera_context_v3(text,jsonb)',
    'EXECUTE'
  ) or not has_function_privilege(
    'service_role',
    'public.recall_vera_context_v3(text,text,text,text[],text[],boolean,integer)',
    'EXECUTE'
  ) then
    raise exception 'validation failed: service_role lacks memory RPC execution';
  end if;

  if has_table_privilege('anon', 'public.vera_context_events_v3', 'SELECT')
     or has_table_privilege('authenticated', 'public.vera_context_events_v3', 'SELECT')
     or has_function_privilege('anon', 'public.append_vera_context_v3(text,jsonb)', 'EXECUTE')
     or has_function_privilege('authenticated', 'public.recall_vera_context_v3(text,text,text,text[],text[],boolean,integer)', 'EXECUTE') then
    raise exception 'validation failed: client roles can access governed memory';
  end if;
end;
$$;

rollback;
