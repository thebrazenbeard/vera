-- Separate-invocation proof for committed request preclaim and stored receipt recovery.

begin;

do $$
declare
  record_payload jsonb;
  completed_receipt jsonb;
  retry_receipt jsonb;
  status_receipt jsonb;
  record_count integer;
begin
  record_payload := jsonb_build_object(
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
  );

  status_receipt := public.get_vera_memory_request_v3(
    'MREQ-idempotency-interrupted'
  );
  if status_receipt->>'request_state' <> 'IN_PROGRESS' then
    raise exception 'recovery verification failed: committed preclaim was not recoverable';
  end if;

  completed_receipt := public.append_vera_context_v3(
    'MREQ-idempotency-interrupted',
    record_payload
  );
  retry_receipt := public.append_vera_context_v3(
    'MREQ-idempotency-interrupted',
    record_payload
  );

  if completed_receipt->>'result_class' <> 'COMPLETE'
     or completed_receipt <> retry_receipt then
    raise exception 'recovery verification failed: completion or exact retry was not deterministic';
  end if;

  status_receipt := public.get_vera_memory_request_v3(
    'MREQ-idempotency-interrupted'
  );
  if status_receipt->>'request_state' <> 'COMPLETE'
     or status_receipt#>>'{stored_result,receipt_id}' <> completed_receipt->>'receipt_id'
     or status_receipt#>>'{stored_result,canonical_request_hash}'
        <> completed_receipt->>'canonical_request_hash' then
    raise exception 'recovery verification failed: later invocation could not retrieve stored receipt';
  end if;

  select count(*) into record_count
  from public.vera_context_events_v3
  where project_id = 'vera-memory-idempotency-test'
    and branch_id = 'branch-a'
    and record_key = 'memory.idempotency.interrupted';

  if record_count <> 1 then
    raise exception 'recovery verification failed: recovered request created % canonical rows',
      record_count;
  end if;
end;
$$;

commit;
