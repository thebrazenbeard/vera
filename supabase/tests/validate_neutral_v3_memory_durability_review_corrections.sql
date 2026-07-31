-- Close the remaining Memory durability review gaps.
--
-- Proves:
-- 1. operational request tables are not directly accessible;
-- 2. only governed service-role functions are executable;
-- 3. a stored FAILED exact-payload request actually recovers to COMPLETE;
-- 4. recovery creates one canonical record and exact retry returns the stored result.
--
-- Runs only in a disposable CI database and rolls back all fixtures.

begin;

do $$
declare
  record_payload jsonb;
  request_hash text;
  failed_receipt jsonb;
  recovered jsonb;
  retried jsonb;
  status_receipt jsonb;
  record_count integer;
begin
  -- Operational tables remain inaccessible even to service_role. Governed
  -- SECURITY DEFINER functions are the only supported runtime boundary.
  if has_table_privilege('anon', 'public.vera_memory_requests_v3', 'SELECT')
     or has_table_privilege('authenticated', 'public.vera_memory_requests_v3', 'SELECT')
     or has_table_privilege('service_role', 'public.vera_memory_requests_v3', 'SELECT')
     or has_table_privilege('service_role', 'public.vera_memory_requests_v3', 'INSERT')
     or has_table_privilege('service_role', 'public.vera_memory_requests_v3', 'UPDATE')
     or has_table_privilege('service_role', 'public.vera_memory_requests_v3', 'DELETE') then
    raise exception 'durability review failed: operational request table is directly accessible';
  end if;

  if has_function_privilege('anon', 'public.append_vera_context_v3(text,jsonb)', 'EXECUTE')
     or has_function_privilege('authenticated', 'public.append_vera_context_v3(text,jsonb)', 'EXECUTE')
     or has_function_privilege('anon', 'public.get_vera_memory_request_v3(text)', 'EXECUTE')
     or has_function_privilege('authenticated', 'public.get_vera_memory_request_v3(text)', 'EXECUTE') then
    raise exception 'durability review failed: untrusted role can execute governed request functions';
  end if;

  if not has_function_privilege('service_role', 'public.begin_vera_memory_save_v3(text,jsonb)', 'EXECUTE')
     or not has_function_privilege('service_role', 'public.append_vera_context_v3(text,jsonb)', 'EXECUTE')
     or not has_function_privilege(
       'service_role',
       'public.recall_vera_context_v3(text,text,text,text[],text[],boolean,integer)',
       'EXECUTE'
     )
     or not has_function_privilege('service_role', 'public.get_vera_memory_request_v3(text)', 'EXECUTE') then
    raise exception 'durability review failed: service_role lacks governed function access';
  end if;

  if has_function_privilege('service_role', 'public.append_vera_context_v3_once(text,jsonb)', 'EXECUTE')
     or has_function_privilege(
       'service_role',
       'public.recall_vera_context_v3_once(text,text,text,text[],text[],boolean,integer)',
       'EXECUTE'
     )
     or has_function_privilege('service_role', 'public.vera_memory_request_hash_v3(text,jsonb)', 'EXECUTE')
     or has_function_privilege(
       'service_role',
       'public.vera_memory_request_conflict_v3(text,text,text,text)',
       'EXECUTE'
     ) then
    raise exception 'durability review failed: service_role can bypass governed wrappers';
  end if;

  record_payload := jsonb_build_object(
    'project_id', 'vera-memory-failed-recovery-test',
    'branch_id', 'branch-a',
    'record_key', 'memory.failed-recovery.exact',
    'record_type', 'FACT',
    'statement', 'Exact-payload retry recovered a stored FAILED request.',
    'lifecycle_status', 'CURRENT',
    'epistemic_status', 'DOCUMENTED_SOURCE',
    'source_actor', 'EXTERNAL',
    'privacy_scope', 'PROJECT',
    'event_time', '2026-07-31T01:00:00+00:00',
    'state_time', '2026-07-31T01:00:00+00:00',
    'source_evidence', jsonb_build_array(
      jsonb_build_object(
        'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
        'observation', 'Synthetic FAILED-state exact-retry recovery fixture.'
      )
    ),
    'semantic_tags', jsonb_build_object(
      'topics', jsonb_build_array('memory', 'idempotency', 'recovery'),
      'status', jsonb_build_array('test')
    ),
    'limitations', jsonb_build_array(
      'Synthetic CI record in a disposable database.'
    )
  );

  request_hash := public.vera_memory_request_hash_v3('SAVE', record_payload);
  failed_receipt := jsonb_build_object(
    'schema', 'VERA_MVE_RECEIPT_V3',
    'receipt_id', gen_random_uuid(),
    'request_id', 'MREQ-failed-exact-recovery',
    'canonical_request_hash', request_hash,
    'operation', 'SAVE',
    'result_class', 'FAILED',
    'outcome_code', 'MVE_SAVE_FAILED_RECOVERABLE',
    'record_ids', '[]'::jsonb,
    'records', '[]'::jsonb,
    'error', jsonb_build_object(
      'sqlstate', 'XX000',
      'message', 'Synthetic stored failure before exact retry.'
    ),
    'limitations', jsonb_build_array(
      'Synthetic failed request state for exact-retry validation.'
    )
  );

  insert into public.vera_memory_requests_v3 (
    request_id,
    operation,
    canonical_request_hash,
    request_state,
    attempt_count,
    stored_result,
    committed_record_ids,
    last_error,
    limitations,
    completed_at
  ) values (
    'MREQ-failed-exact-recovery',
    'SAVE',
    request_hash,
    'FAILED',
    1,
    failed_receipt,
    '[]'::jsonb,
    failed_receipt->'error',
    failed_receipt->'limitations',
    clock_timestamp()
  );

  status_receipt := public.get_vera_memory_request_v3(
    'MREQ-failed-exact-recovery'
  );
  if status_receipt->>'request_state' <> 'FAILED'
     or status_receipt->>'result_class' <> 'FAILED'
     or status_receipt->>'outcome_code' <> 'MVE_REQUEST_FAILED_RECOVERABLE' then
    raise exception 'durability review failed: stored failure is not machine-readable: %',
      status_receipt;
  end if;

  recovered := public.append_vera_context_v3(
    'MREQ-failed-exact-recovery',
    record_payload
  );
  if recovered->>'result_class' <> 'COMPLETE'
     or recovered->>'outcome_code' <> 'MVE_SAVE_COMPLETE'
     or recovered->>'canonical_request_hash' <> request_hash then
    raise exception 'durability review failed: exact retry did not recover FAILED request: %',
      recovered;
  end if;

  retried := public.append_vera_context_v3(
    'MREQ-failed-exact-recovery',
    record_payload
  );
  if retried <> recovered then
    raise exception 'durability review failed: post-recovery exact retry did not return stored result';
  end if;

  status_receipt := public.get_vera_memory_request_v3(
    'MREQ-failed-exact-recovery'
  );
  if status_receipt->>'request_state' <> 'COMPLETE'
     or status_receipt->>'result_class' <> 'COMPLETE'
     or (status_receipt->>'attempt_count')::integer <> 2
     or status_receipt#>>'{stored_result,receipt_id}' <> recovered->>'receipt_id'
     or status_receipt#>>'{committed_record_ids,0}' <> recovered#>>'{record_ids,0}' then
    raise exception 'durability review failed: recovered request state is incomplete: %',
      status_receipt;
  end if;

  select count(*) into record_count
  from public.vera_context_events_v3
  where project_id = 'vera-memory-failed-recovery-test'
    and branch_id = 'branch-a'
    and record_key = 'memory.failed-recovery.exact';

  if record_count <> 1 then
    raise exception 'durability review failed: FAILED recovery created % canonical records',
      record_count;
  end if;
end;
$$;

rollback;
