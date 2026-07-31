-- Validate durable request identity, exact retry, conflict, rollback, and recovery.
-- Runs against the disposable local Supabase stack only.

begin;

do $$
declare
  record_payload jsonb;
  first_receipt jsonb;
  retry_receipt jsonb;
  conflict_receipt jsonb;
  recall_first jsonb;
  recall_retry jsonb;
  status_receipt jsonb;
  saved_record_id uuid;
  saved_receipt_id text;
  request_hash text;
  count_records integer;
begin
  if to_regclass('public.vera_memory_requests_v3') is null then
    raise exception 'idempotency validation failed: request ledger missing';
  end if;

  record_payload := jsonb_build_object(
    'project_id', 'vera-memory-idempotency-test',
    'branch_id', 'branch-a',
    'record_key', 'memory.idempotency.exact-retry',
    'record_type', 'DECISION',
    'statement', 'Durable idempotency test record.',
    'lifecycle_status', 'CURRENT',
    'epistemic_status', 'DIRECT_USER_STATEMENT',
    'source_actor', 'USER',
    'privacy_scope', 'PROJECT',
    'event_time', '2026-07-31T00:30:00+00:00',
    'state_time', '2026-07-31T00:30:00+00:00',
    'payload', jsonb_build_object(
      'test', 'memory-request-idempotency',
      'version', 1
    ),
    'source_evidence', jsonb_build_array(
      jsonb_build_object(
        'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
        'observation', 'Synthetic durable request test record.'
      )
    ),
    'semantic_tags', jsonb_build_object(
      'topics', jsonb_build_array('memory', 'idempotency'),
      'status', jsonb_build_array('current')
    ),
    'limitations', jsonb_build_array(
      'Synthetic CI record in a disposable database.'
    )
  );

  first_receipt := public.append_vera_context_v3(
    'MREQ-idempotency-exact',
    record_payload
  );
  retry_receipt := public.append_vera_context_v3(
    'MREQ-idempotency-exact',
    record_payload
  );

  if first_receipt <> retry_receipt then
    raise exception 'idempotency validation failed: exact retry did not return stored result';
  end if;

  if first_receipt->>'result_class' <> 'COMPLETE'
     or first_receipt->>'outcome_code' <> 'MVE_SAVE_COMPLETE'
     or coalesce(first_receipt->>'canonical_request_hash', '') !~ '^[0-9a-f]{64}$' then
    raise exception 'idempotency validation failed: first receipt lacks durable identity: %',
      first_receipt;
  end if;

  saved_record_id := (first_receipt#>>'{record_ids,0}')::uuid;
  saved_receipt_id := first_receipt->>'receipt_id';
  request_hash := first_receipt->>'canonical_request_hash';

  select count(*) into count_records
  from public.vera_context_events_v3
  where project_id = 'vera-memory-idempotency-test'
    and branch_id = 'branch-a'
    and record_key = 'memory.idempotency.exact-retry';

  if count_records <> 1 then
    raise exception 'idempotency validation failed: exact retry created % records',
      count_records;
  end if;

  conflict_receipt := public.append_vera_context_v3(
    'MREQ-idempotency-exact',
    jsonb_set(
      record_payload,
      '{statement}',
      to_jsonb('Changed payload must conflict.'::text)
    )
  );

  if conflict_receipt->>'result_class' <> 'CONFLICT'
     or conflict_receipt->>'outcome_code' <> 'MVE_REQUEST_ID_PAYLOAD_CONFLICT'
     or conflict_receipt->>'stored_request_hash' <> request_hash then
    raise exception 'idempotency validation failed: changed-payload reuse was not named conflict: %',
      conflict_receipt;
  end if;

  select count(*) into count_records
  from public.vera_context_events_v3
  where project_id = 'vera-memory-idempotency-test'
    and branch_id = 'branch-a'
    and record_key = 'memory.idempotency.exact-retry';

  if count_records <> 1 then
    raise exception 'idempotency validation failed: conflict mutated canonical memory';
  end if;

  -- A SAVE-bound request ID cannot be reused by RECALL even when the query is valid.
  conflict_receipt := public.recall_vera_context_v3(
    'MREQ-idempotency-exact',
    'vera-memory-idempotency-test',
    'branch-a',
    array['memory.idempotency.exact-retry']::text[],
    array['PROJECT']::text[],
    false,
    8
  );
  if conflict_receipt->>'result_class' <> 'CONFLICT'
     or conflict_receipt->>'outcome_code' <> 'MVE_REQUEST_ID_PAYLOAD_CONFLICT'
     or conflict_receipt->>'operation' <> 'RECALL' then
    raise exception 'idempotency validation failed: SAVE-versus-RECALL request-ID reuse was not rejected: %',
      conflict_receipt;
  end if;

  status_receipt := public.get_vera_memory_request_v3('MREQ-idempotency-exact');
  if status_receipt->>'request_state' <> 'COMPLETE'
     or status_receipt#>>'{stored_result,receipt_id}' <> saved_receipt_id
     or status_receipt#>>'{committed_record_ids,0}' <> saved_record_id::text then
    raise exception 'idempotency validation failed: stored request recovery is incomplete: %',
      status_receipt;
  end if;

  recall_first := public.recall_vera_context_v3(
    'MREQ-idempotency-recall',
    'vera-memory-idempotency-test',
    'branch-a',
    array['memory.idempotency.exact-retry']::text[],
    array['PROJECT']::text[],
    false,
    8
  );
  recall_retry := public.recall_vera_context_v3(
    'MREQ-idempotency-recall',
    'vera-memory-idempotency-test',
    'branch-a',
    array['memory.idempotency.exact-retry']::text[],
    array['PROJECT']::text[],
    false,
    8
  );

  if recall_first <> recall_retry
     or recall_first->>'result_class' not in ('COMPLETE', 'PARTIAL')
     or recall_first->>'canonical_request_hash' is null then
    raise exception 'idempotency validation failed: recall retry did not recover stored result';
  end if;

  conflict_receipt := public.recall_vera_context_v3(
    'MREQ-idempotency-recall',
    'vera-memory-idempotency-test',
    'branch-a',
    null,
    array['PROJECT']::text[],
    false,
    8
  );

  if conflict_receipt->>'result_class' <> 'CONFLICT'
     or conflict_receipt->>'outcome_code' <> 'MVE_REQUEST_ID_PAYLOAD_CONFLICT' then
    raise exception 'idempotency validation failed: recall payload reuse did not conflict';
  end if;
end;
$$;

commit;

-- A separately committed preclaim is explicit recoverable state before SAVE.
begin;
select public.begin_vera_memory_save_v3(
  'MREQ-idempotency-interrupted',
  jsonb_build_object(
    'project_id', 'vera-memory-idempotency-test',
    'branch_id', 'branch-a',
    'record_key', 'memory.idempotency.interrupted',
    'record_type', 'FACT',
    'statement', 'Recovered after a committed request preclaim.',
    'lifecycle_status', 'CURRENT',
    'epistemic_status', 'DOCUMENTED_SOURCE',
    'source_actor', 'EXTERNAL',
    'privacy_scope', 'PROJECT',
    'event_time', '2026-07-31T00:31:00+00:00',
    'state_time', '2026-07-31T00:31:00+00:00',
    'source_evidence', jsonb_build_array(
      jsonb_build_object(
        'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
        'observation', 'Synthetic interrupted-attempt recovery fixture.'
      )
    ),
    'semantic_tags', jsonb_build_object(
      'topics', jsonb_build_array('memory', 'recovery'),
      'status', jsonb_build_array('current')
    ),
    'limitations', jsonb_build_array(
      'Synthetic CI record in a disposable database.'
    )
  )
);
commit;

-- Simulate an interrupted atomic invocation: both request row and canonical row roll back.
begin;
select public.append_vera_context_v3(
  'MREQ-idempotency-rolled-back',
  jsonb_build_object(
    'project_id', 'vera-memory-idempotency-test',
    'branch_id', 'branch-a',
    'record_key', 'memory.idempotency.rolled-back',
    'record_type', 'FACT',
    'statement', 'This invocation is deliberately rolled back.',
    'lifecycle_status', 'CURRENT',
    'epistemic_status', 'DOCUMENTED_SOURCE',
    'source_actor', 'EXTERNAL',
    'privacy_scope', 'PROJECT',
    'source_evidence', jsonb_build_array(
      jsonb_build_object(
        'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
        'observation', 'Rollback fixture.'
      )
    ),
    'semantic_tags', jsonb_build_object(
      'topics', jsonb_build_array('memory', 'rollback'),
      'status', jsonb_build_array('current')
    )
  )
);
rollback;

do $$
declare
  status_receipt jsonb;
begin
  status_receipt := public.get_vera_memory_request_v3(
    'MREQ-idempotency-rolled-back'
  );
  if status_receipt->>'request_state' <> 'NOT_FOUND'
     or status_receipt->>'outcome_code' <> 'MVE_REQUEST_NOT_FOUND' then
    raise exception 'idempotency validation failed: rolled-back request reported ambiguous success';
  end if;

  status_receipt := public.get_vera_memory_request_v3(
    'MREQ-idempotency-interrupted'
  );
  if status_receipt->>'request_state' <> 'IN_PROGRESS'
     or status_receipt->>'result_class' <> 'PARTIAL'
     or status_receipt->>'stored_result' is not null then
    raise exception 'idempotency validation failed: preclaim is not explicit recoverable partial state';
  end if;
end;
$$;
