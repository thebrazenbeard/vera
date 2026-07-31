-- Durable request identity, exact retry, and stored receipt recovery for Memory v3.
--
-- Source-only migration. It does not authorize production application or writes.
-- Canonical memory remains append-only. The operational request ledger is mutable
-- only through SECURITY DEFINER functions and is not canonical memory.

begin;

create table if not exists public.vera_memory_requests_v3 (
  request_id text primary key,
  operation text not null,
  canonical_request_hash text not null,
  request_state text not null,
  attempt_count integer not null default 1,
  stored_result jsonb,
  committed_record_ids jsonb not null default '[]'::jsonb,
  last_error jsonb,
  limitations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default clock_timestamp(),
  updated_at timestamptz not null default clock_timestamp(),
  completed_at timestamptz,
  constraint vera_memory_requests_v3_request_id_nonblank_chk
    check (btrim(request_id) <> ''),
  constraint vera_memory_requests_v3_operation_chk
    check (operation in ('SAVE', 'RECALL')),
  constraint vera_memory_requests_v3_hash_chk
    check (canonical_request_hash ~ '^[0-9a-f]{64}$'),
  constraint vera_memory_requests_v3_state_chk
    check (request_state in ('IN_PROGRESS', 'COMPLETE', 'FAILED')),
  constraint vera_memory_requests_v3_attempt_count_chk
    check (attempt_count > 0),
  constraint vera_memory_requests_v3_record_ids_shape_chk
    check (jsonb_typeof(committed_record_ids) = 'array'),
  constraint vera_memory_requests_v3_limitations_shape_chk
    check (jsonb_typeof(limitations) = 'array'),
  constraint vera_memory_requests_v3_complete_shape_chk
    check (
      (request_state = 'COMPLETE' and stored_result is not null and completed_at is not null)
      or (request_state = 'IN_PROGRESS' and stored_result is null and completed_at is null)
      or (request_state = 'FAILED' and stored_result is not null and completed_at is not null)
    )
);

alter table public.vera_memory_requests_v3 enable row level security;

comment on table public.vera_memory_requests_v3 is
  'Operational request-idempotency ledger. It stores request hashes and receipts, not canonical memory or model recollection.';
comment on column public.vera_memory_requests_v3.canonical_request_hash is
  'SHA-256 of the canonical JSONB operation subject. It binds request identity to exact payload semantics.';
comment on column public.vera_memory_requests_v3.request_state is
  'IN_PROGRESS is an explicit recoverable preclaim; COMPLETE and FAILED retain the stored result receipt.';

create or replace function public.vera_memory_request_hash_v3(
  p_operation text,
  p_payload jsonb
)
returns text
language sql
immutable
strict
set search_path = pg_catalog, public
as $$
  select encode(
    digest(
      convert_to(
        jsonb_build_object(
          'operation', upper(btrim(p_operation)),
          'payload', p_payload
        )::text,
        'UTF8'
      ),
      'sha256'
    ),
    'hex'
  );
$$;

create or replace function public.vera_memory_request_conflict_v3(
  p_request_id text,
  p_operation text,
  p_request_hash text,
  p_stored_hash text
)
returns jsonb
language sql
volatile
set search_path = pg_catalog, public
as $$
  select jsonb_build_object(
    'schema', 'VERA_MVE_RECEIPT_V3',
    'receipt_id', gen_random_uuid(),
    'request_id', p_request_id,
    'canonical_request_hash', p_request_hash,
    'stored_request_hash', p_stored_hash,
    'operation', upper(p_operation),
    'result_class', 'CONFLICT',
    'outcome_code', 'MVE_REQUEST_ID_PAYLOAD_CONFLICT',
    'record_ids', '[]'::jsonb,
    'records', '[]'::jsonb,
    'write', jsonb_build_object(
      'record_embedded_in_current_chat', false,
      'external_persistence', 'NOT_PERFORMED',
      'transactional_writeback', 'NOT_APPLICABLE'
    ),
    'limitations', jsonb_build_array(
      'The request ID was already bound to a different canonical operation payload.',
      'No canonical memory mutation was performed by this conflicting invocation.'
    ),
    'record_time', clock_timestamp()
  );
$$;

-- Preserve the validated implementation as an internal one-attempt primitive.
do $$
begin
  if to_regprocedure('public.append_vera_context_v3_once(text,jsonb)') is null then
    if to_regprocedure('public.append_vera_context_v3(text,jsonb)') is null then
      raise exception 'append_vera_context_v3(text,jsonb) is missing';
    end if;
    alter function public.append_vera_context_v3(text, jsonb)
      rename to append_vera_context_v3_once;
  end if;

  if to_regprocedure(
    'public.recall_vera_context_v3_once(text,text,text,text[],text[],boolean,integer)'
  ) is null then
    if to_regprocedure(
      'public.recall_vera_context_v3(text,text,text,text[],text[],boolean,integer)'
    ) is null then
      raise exception 'recall_vera_context_v3 bounded function is missing';
    end if;
    alter function public.recall_vera_context_v3(
      text, text, text, text[], text[], boolean, integer
    ) rename to recall_vera_context_v3_once;
  end if;
end;
$$;

revoke all on function public.append_vera_context_v3_once(text, jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.recall_vera_context_v3_once(
  text, text, text, text[], text[], boolean, integer
) from public, anon, authenticated, service_role;

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
      'result_class', 'COMPLETE',
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
    'result_class', 'COMPLETE',
    'outcome_code', 'MVE_REQUEST_STARTED',
    'may_execute', true,
    'limitations', jsonb_build_array(
      'The request preclaim is operational state and proves no canonical mutation.',
      'Call append_vera_context_v3 with the exact same request ID and payload to complete or recover the request.'
    )
  );
end;
$$;

create or replace function public.append_vera_context_v3(
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
  result jsonb;
  preclaimed boolean := false;
  failure_result jsonb;
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
      return existing.stored_result;
    end if;

    preclaimed := true;
    update public.vera_memory_requests_v3
    set request_state = 'IN_PROGRESS',
        attempt_count = attempt_count + 1,
        stored_result = null,
        last_error = null,
        completed_at = null,
        updated_at = clock_timestamp()
    where request_id = p_request_id;
  else
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
        'The request and canonical mutation commit atomically in this invocation.',
        'A rolled-back invocation leaves no committed canonical mutation or success receipt.'
      )
    );
  end if;

  begin
    result := public.append_vera_context_v3_once(p_request_id, p_record);
    result := result || jsonb_build_object(
      'canonical_request_hash', request_hash,
      'idempotency', jsonb_build_object(
        'request_state', 'COMPLETE',
        'exact_retry_returns_stored_result', true,
        'changed_payload_reuse', 'CONFLICT'
      )
    );

    update public.vera_memory_requests_v3
    set request_state = 'COMPLETE',
        stored_result = result,
        committed_record_ids = coalesce(result->'record_ids', '[]'::jsonb),
        last_error = null,
        completed_at = clock_timestamp(),
        updated_at = clock_timestamp()
    where request_id = p_request_id;

    return result;
  exception when others then
    if not preclaimed then
      raise;
    end if;

    failure_result := jsonb_build_object(
      'schema', 'VERA_MVE_RECEIPT_V3',
      'receipt_id', gen_random_uuid(),
      'request_id', p_request_id,
      'canonical_request_hash', request_hash,
      'operation', 'SAVE',
      'result_class', 'FAILED',
      'outcome_code', 'MVE_SAVE_FAILED_RECOVERABLE',
      'record_ids', '[]'::jsonb,
      'records', '[]'::jsonb,
      'error', jsonb_build_object(
        'sqlstate', sqlstate,
        'message', sqlerrm
      ),
      'write', jsonb_build_object(
        'external_persistence', 'NOT_CONFIRMED',
        'transactional_writeback', 'ROLLED_BACK'
      ),
      'limitations', jsonb_build_array(
        'The canonical append subtransaction was rolled back.',
        'The preclaimed request remains recoverable only with the exact same canonical payload.'
      ),
      'record_time', clock_timestamp()
    );

    update public.vera_memory_requests_v3
    set request_state = 'FAILED',
        stored_result = failure_result,
        committed_record_ids = '[]'::jsonb,
        last_error = failure_result->'error',
        completed_at = clock_timestamp(),
        updated_at = clock_timestamp()
    where request_id = p_request_id;

    return failure_result;
  end;
end;
$$;

create or replace function public.recall_vera_context_v3(
  p_request_id text,
  p_project_id text,
  p_branch_id text,
  p_record_keys text[] default null,
  p_privacy_scopes text[] default array['PROJECT']::text[],
  p_include_model_generated boolean default false,
  p_max_records integer default 8
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  request_payload jsonb;
  request_hash text;
  existing public.vera_memory_requests_v3%rowtype;
  result jsonb;
begin
  if p_request_id is null or coalesce(btrim(p_request_id), '') = '' then
    raise exception 'p_request_id must be non-empty';
  end if;

  request_payload := jsonb_build_object(
    'project_id', p_project_id,
    'branch_id', p_branch_id,
    'record_keys', to_jsonb(p_record_keys),
    'privacy_scopes', to_jsonb(p_privacy_scopes),
    'include_model_generated', p_include_model_generated,
    'max_records', p_max_records
  );
  request_hash := public.vera_memory_request_hash_v3('RECALL', request_payload);

  perform pg_advisory_xact_lock(
    hashtextextended('vera-memory-request-v3:' || p_request_id, 0)
  );

  select * into existing
  from public.vera_memory_requests_v3
  where request_id = p_request_id
  for update;

  if found then
    if existing.operation <> 'RECALL'
       or existing.canonical_request_hash <> request_hash then
      return public.vera_memory_request_conflict_v3(
        p_request_id,
        'RECALL',
        request_hash,
        existing.canonical_request_hash
      );
    end if;
    if existing.request_state = 'COMPLETE' then
      return existing.stored_result;
    end if;
  else
    insert into public.vera_memory_requests_v3 (
      request_id,
      operation,
      canonical_request_hash,
      request_state,
      limitations
    ) values (
      p_request_id,
      'RECALL',
      request_hash,
      'IN_PROGRESS',
      jsonb_build_array(
        'The stored recall receipt is idempotent for this exact query payload.',
        'A repeated request ID does not refresh retrieval_time or silently widen query scope.'
      )
    );
  end if;

  result := public.recall_vera_context_v3_once(
    p_request_id,
    p_project_id,
    p_branch_id,
    p_record_keys,
    p_privacy_scopes,
    p_include_model_generated,
    p_max_records
  );
  result := result || jsonb_build_object(
    'canonical_request_hash', request_hash,
    'idempotency', jsonb_build_object(
      'request_state', 'COMPLETE',
      'exact_retry_returns_stored_result', true,
      'changed_payload_reuse', 'CONFLICT'
    )
  );

  update public.vera_memory_requests_v3
  set request_state = 'COMPLETE',
      stored_result = result,
      committed_record_ids = '[]'::jsonb,
      last_error = null,
      completed_at = clock_timestamp(),
      updated_at = clock_timestamp()
  where request_id = p_request_id;

  return result;
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
    'result_class', case
      when stored.request_state = 'FAILED' then 'FAILED'
      else 'COMPLETE'
    end,
    'outcome_code', 'MVE_REQUEST_STATUS_RETRIEVED',
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

revoke all privileges on table public.vera_memory_requests_v3
  from public, anon, authenticated, service_role;
revoke all on function public.vera_memory_request_hash_v3(text, jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.vera_memory_request_conflict_v3(text, text, text, text)
  from public, anon, authenticated, service_role;
revoke all on function public.begin_vera_memory_save_v3(text, jsonb)
  from public, anon, authenticated;
revoke all on function public.append_vera_context_v3(text, jsonb)
  from public, anon, authenticated;
revoke all on function public.recall_vera_context_v3(
  text, text, text, text[], text[], boolean, integer
) from public, anon, authenticated;
revoke all on function public.get_vera_memory_request_v3(text)
  from public, anon, authenticated;

grant execute on function public.begin_vera_memory_save_v3(text, jsonb)
  to service_role;
grant execute on function public.append_vera_context_v3(text, jsonb)
  to service_role;
grant execute on function public.recall_vera_context_v3(
  text, text, text, text[], text[], boolean, integer
) to service_role;
grant execute on function public.get_vera_memory_request_v3(text)
  to service_role;

comment on function public.begin_vera_memory_save_v3(text, jsonb) is
  'Commits an explicit recoverable SAVE request preclaim when invoked in its own transaction. It performs no canonical memory mutation.';
comment on function public.append_vera_context_v3(text, jsonb) is
  'Idempotent governed SAVE. Exact retries return the stored receipt; changed-payload request-ID reuse returns a named conflict.';
comment on function public.recall_vera_context_v3(
  text, text, text, text[], text[], boolean, integer
) is
  'Idempotent exact-key RECALL. Exact retries return the stored result without refreshing retrieval_time.';
comment on function public.get_vera_memory_request_v3(text) is
  'Retrieves durable operational request state and its stored result receipt in a later database invocation.';

commit;
