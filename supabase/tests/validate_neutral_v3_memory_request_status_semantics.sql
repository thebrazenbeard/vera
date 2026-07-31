-- Validate that operational request state is not conflated with completion.
-- Runs only in the disposable CI database and rolls back all fixtures.

begin;

do $$
declare
  record_payload jsonb;
  failed_payload jsonb;
  started jsonb;
  repeated jsonb;
  status_receipt jsonb;
  completed jsonb;
  failed_hash text;
begin
  record_payload := jsonb_build_object(
    'project_id', 'vera-memory-status-semantics-test',
    'branch_id', 'branch-a',
    'record_key', 'memory.status.in-progress',
    'record_type', 'FACT',
    'statement', 'Request status semantics test.',
    'lifecycle_status', 'CURRENT',
    'epistemic_status', 'DOCUMENTED_SOURCE',
    'source_actor', 'EXTERNAL',
    'privacy_scope', 'PROJECT',
    'event_time', '2026-07-31T00:40:00+00:00',
    'state_time', '2026-07-31T00:40:00+00:00',
    'source_evidence', jsonb_build_array(
      jsonb_build_object(
        'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
        'observation', 'Synthetic request-status fixture.'
      )
    ),
    'semantic_tags', jsonb_build_object(
      'topics', jsonb_build_array('memory', 'request-status'),
      'status', jsonb_build_array('test')
    ),
    'limitations', jsonb_build_array(
      'Synthetic CI record in a disposable database.'
    )
  );

  started := public.begin_vera_memory_save_v3(
    'MREQ-status-in-progress',
    record_payload
  );

  if started->>'request_state' <> 'IN_PROGRESS'
     or started->>'result_class' <> 'PARTIAL'
     or started->>'outcome_code' <> 'MVE_REQUEST_STARTED'
     or coalesce((started->>'may_execute')::boolean, false) is not true then
    raise exception 'request status validation failed: new preclaim is ambiguous: %',
      started;
  end if;

  repeated := public.begin_vera_memory_save_v3(
    'MREQ-status-in-progress',
    record_payload
  );

  if repeated->>'request_state' <> 'IN_PROGRESS'
     or repeated->>'result_class' <> 'PARTIAL'
     or repeated->>'outcome_code' <> 'MVE_REQUEST_IN_PROGRESS_RECOVERABLE' then
    raise exception 'request status validation failed: repeated preclaim is ambiguous: %',
      repeated;
  end if;

  status_receipt := public.get_vera_memory_request_v3(
    'MREQ-status-in-progress'
  );

  if status_receipt->>'request_state' <> 'IN_PROGRESS'
     or status_receipt->>'result_class' <> 'PARTIAL'
     or status_receipt->>'outcome_code' <> 'MVE_REQUEST_IN_PROGRESS_RECOVERABLE'
     or status_receipt->'stored_result' is not null then
    raise exception 'request status validation failed: IN_PROGRESS retrieval claims completion: %',
      status_receipt;
  end if;

  completed := public.append_vera_context_v3(
    'MREQ-status-in-progress',
    record_payload
  );

  if completed->>'result_class' <> 'COMPLETE' then
    raise exception 'request status validation failed: append did not complete: %',
      completed;
  end if;

  status_receipt := public.get_vera_memory_request_v3(
    'MREQ-status-in-progress'
  );

  if status_receipt->>'request_state' <> 'COMPLETE'
     or status_receipt->>'result_class' <> 'COMPLETE'
     or status_receipt->>'outcome_code' <> 'MVE_REQUEST_COMPLETE'
     or status_receipt#>>'{stored_result,receipt_id}' <> completed->>'receipt_id' then
    raise exception 'request status validation failed: completed request is not bound to stored result: %',
      status_receipt;
  end if;

  failed_payload := jsonb_set(
    record_payload,
    '{record_key}',
    to_jsonb('memory.status.failed'::text)
  );
  failed_hash := public.vera_memory_request_hash_v3('SAVE', failed_payload);

  insert into public.vera_memory_requests_v3 (
    request_id,
    operation,
    canonical_request_hash,
    request_state,
    stored_result,
    committed_record_ids,
    last_error,
    limitations,
    completed_at
  ) values (
    'MREQ-status-failed',
    'SAVE',
    failed_hash,
    'FAILED',
    jsonb_build_object(
      'schema', 'VERA_MVE_RECEIPT_V3',
      'request_id', 'MREQ-status-failed',
      'operation', 'SAVE',
      'result_class', 'FAILED',
      'outcome_code', 'MVE_SAVE_FAILED_RECOVERABLE',
      'record_ids', '[]'::jsonb
    ),
    '[]'::jsonb,
    jsonb_build_object(
      'sqlstate', 'XX000',
      'message', 'Synthetic recoverable failure.'
    ),
    jsonb_build_array(
      'Synthetic failed request state for status validation.'
    ),
    clock_timestamp()
  );

  repeated := public.begin_vera_memory_save_v3(
    'MREQ-status-failed',
    failed_payload
  );

  if repeated->>'request_state' <> 'FAILED'
     or repeated->>'result_class' <> 'FAILED'
     or repeated->>'outcome_code' <> 'MVE_REQUEST_FAILED_RECOVERABLE'
     or coalesce((repeated->>'may_execute')::boolean, false) is not true then
    raise exception 'request status validation failed: recoverable failure claims completion: %',
      repeated;
  end if;

  status_receipt := public.get_vera_memory_request_v3(
    'MREQ-status-failed'
  );

  if status_receipt->>'request_state' <> 'FAILED'
     or status_receipt->>'result_class' <> 'FAILED'
     or status_receipt->>'outcome_code' <> 'MVE_REQUEST_FAILED_RECOVERABLE' then
    raise exception 'request status validation failed: FAILED retrieval is ambiguous: %',
      status_receipt;
  end if;
end;
$$;

rollback;
