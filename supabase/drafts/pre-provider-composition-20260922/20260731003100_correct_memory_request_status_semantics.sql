-- Correct Memory request-status semantics without changing canonical memory.
--
-- IN_PROGRESS is a recoverable partial operation state, not successful
-- completion. FAILED remains failed even when an exact retry may resume it.
-- Only a stored COMPLETE operation reports result_class COMPLETE.

begin;

create or replace function public.begin_vera_memory_save_v3(
  p_request_id text,
  p_record jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  request_hash text;
  existing public.vera_memory_requests_v3%rowtype;
begin
  if p_request_id is null or coalesce(btrim(p_request_id), '') = '' then
    raise exception 'p_request_id must be non-empty';
  end if;
  if p_record is null or jsonb_typeof(p_record) <> 'object' then
    raise exception 'p_record must be a JSON object';
  end if;

  request_hash := public.vera_memory_request_hash_v3('SAVE', p_record);
  perform pg_advisory_xact_lock(
    hashtextextended('vera-memory-request-v3:' || p_request_id, 0)
  );

  select * into existing
  from public.vera_memory_requests_v3
  where request_id = p_request_id
  for update;

  if found then
    if existing.operation <> 'SAVE'
       or existing.canonical_request_hash <> request_hash then
      return public.vera_memory_request_conflict_v3(
        p_request_id,
        'SAVE',
        request_hash,
        existing.canonical_request_hash
      );
    end if;

    if existing.request_state = 'COMPLETE' then
      return jsonb_build_object(
        'schema', 'VERA_MVE_REQUEST_STATUS_V3',
        'request_id', p_request_id,
        'canonical_request_hash', request_hash,
        'operation', 'SAVE',
        'request_state', 'COMPLETE',
        'result_class', 'COMPLETE',
        'outcome_code', 'MVE_REQUEST_ALREADY_COMPLETE',
        'may_execute', false,
        'stored_result', existing.stored_result,
        'limitations', existing.limitations
      );
    end if;

    return jsonb_build_object(
      'schema', 'VERA_MVE_REQUEST_STATUS_V3',
      'request_id', p_request_id,
      'canonical_request_hash', request_hash,
      'operation', 'SAVE',
      'request_state', existing.request_state,
      'result_class', case
        when existing.request_state = 'FAILED' then 'FAILED'
        else 'PARTIAL'
      end,
      'outcome_code', case
        when existing.request_state = 'FAILED'
          then 'MVE_REQUEST_FAILED_RECOVERABLE'
        else 'MVE_REQUEST_IN_PROGRESS_RECOVERABLE'
      end,
      'may_execute', true,
      'stored_result', existing.stored_result,
      'limitations', existing.limitations
    );
  end if;

  insert into public.vera_memory_requests_v3 (
    request_id,
    operation,
    canonical_request_hash,
    request_state,
    limitations
  ) values (
    p_request_id,
    'SAVE',
    request_hash,
    'IN_PROGRESS',
    jsonb_build_array(
      'This row is operational request state, not canonical memory.',
      'A committed IN_PROGRESS row is explicitly recoverable by an exact retry.'
    )
  );

  return jsonb_build_object(
    'schema', 'VERA_MVE_REQUEST_STATUS_V3',
    'request_id', p_request_id,
    'canonical_request_hash', request_hash,
    'operation', 'SAVE',
    'request_state', 'IN_PROGRESS',
    'result_class', 'PARTIAL',
    'outcome_code', 'MVE_REQUEST_STARTED',
    'may_execute', true,
    'limitations', jsonb_build_array(
      'The request preclaim is operational state and proves no canonical mutation.',
      'Call append_vera_context_v3 with the exact same request ID and payload to complete or recover the request.'
    )
  );
end;
$$;

create or replace function public.get_vera_memory_request_v3(
  p_request_id text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  stored public.vera_memory_requests_v3%rowtype;
begin
  if p_request_id is null or coalesce(btrim(p_request_id), '') = '' then
    raise exception 'p_request_id must be non-empty';
  end if;

  select * into stored
  from public.vera_memory_requests_v3
  where request_id = p_request_id;

  if not found then
    return jsonb_build_object(
      'schema', 'VERA_MVE_REQUEST_STATUS_V3',
      'request_id', p_request_id,
      'result_class', 'NOT_FOUND',
      'outcome_code', 'MVE_REQUEST_NOT_FOUND',
      'request_state', 'NOT_FOUND',
      'stored_result', null,
      'limitations', jsonb_build_array(
        'No committed request state exists for this request ID.',
        'An interrupted atomic invocation may have rolled back both request state and canonical mutation; absence is not evidence of success.'
      )
    );
  end if;

  return jsonb_build_object(
    'schema', 'VERA_MVE_REQUEST_STATUS_V3',
    'request_id', stored.request_id,
    'operation', stored.operation,
    'canonical_request_hash', stored.canonical_request_hash,
    'request_state', stored.request_state,
    'result_class', case stored.request_state
      when 'COMPLETE' then 'COMPLETE'
      when 'FAILED' then 'FAILED'
      else 'PARTIAL'
    end,
    'outcome_code', case stored.request_state
      when 'COMPLETE' then 'MVE_REQUEST_COMPLETE'
      when 'FAILED' then 'MVE_REQUEST_FAILED_RECOVERABLE'
      else 'MVE_REQUEST_IN_PROGRESS_RECOVERABLE'
    end,
    'attempt_count', stored.attempt_count,
    'committed_record_ids', stored.committed_record_ids,
    'stored_result', stored.stored_result,
    'last_error', stored.last_error,
    'created_at', stored.created_at,
    'updated_at', stored.updated_at,
    'completed_at', stored.completed_at,
    'limitations', stored.limitations
  );
end;
$$;

revoke all on function public.begin_vera_memory_save_v3(text, jsonb)
  from public, anon, authenticated;
revoke all on function public.get_vera_memory_request_v3(text)
  from public, anon, authenticated;

grant execute on function public.begin_vera_memory_save_v3(text, jsonb)
  to service_role;
grant execute on function public.get_vera_memory_request_v3(text)
  to service_role;

comment on function public.begin_vera_memory_save_v3(text, jsonb) is
  'Creates or reports recoverable SAVE request state. IN_PROGRESS is PARTIAL, FAILED is FAILED, and only completed canonical work is COMPLETE.';
comment on function public.get_vera_memory_request_v3(text) is
  'Retrieves durable operational request state without conflating request existence with operation completion.';

commit;
