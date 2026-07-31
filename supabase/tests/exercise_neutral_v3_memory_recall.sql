-- Second half of the independently invoked memory-cycle proof.
-- This file runs in a separate psql process after the save exercise committed.

begin;

do $$
declare
  receipt jsonb;
  successor_id uuid;
  root_id uuid;
begin
  select record_id into successor_id
  from public.vera_context_events_v3
  where project_id = 'vera-memory-e2e'
    and branch_id = 'branch-a'
    and record_key = 'memory.e2e.current'
    and statement = 'Corrected governed memory value.';

  select record_id into root_id
  from public.vera_context_events_v3
  where project_id = 'vera-memory-e2e'
    and branch_id = 'branch-a'
    and record_key = 'memory.e2e.current'
    and statement = 'Initial governed memory value.';

  if successor_id is null or root_id is null then
    raise exception 'recall exercise failed: prior save invocation is not visible';
  end if;

  receipt := public.recall_vera_context_v3(
    'MREQ-e2e-recall-current',
    'vera-memory-e2e',
    'branch-a',
    array['memory.e2e.current']::text[],
    array['PROJECT']::text[],
    false,
    8
  );

  if receipt->>'schema' <> 'VERA_MVE_RECEIPT_V3'
     or receipt->>'operation' <> 'RECALL'
     or receipt->>'outcome_code' <> 'MVE_RECALL_COMPLETE'
     or receipt#>>'{write,external_persistence}' <> 'READ_CONFIRMED'
     or receipt#>>'{retrieval,completeness}' <> 'COMPLETE_RELATIVE_TO_QUERY_SCOPE'
     or jsonb_array_length(receipt->'record_ids') <> 1
     or receipt#>>'{record_ids,0}' <> successor_id::text
     or receipt#>>'{records,0,statement}' <> 'Corrected governed memory value.'
     or receipt#>>'{records,0,payload,version}' <> '2'
     or receipt#>>'{records,0,source_evidence,0,source_actor}' <> 'USER'
     or receipt#>>'{records,0,semantic_tags,status,1}' <> 'corrected'
     or receipt#>>'{records,0,payload,temporal,event_time,precision}' <> 'UNKNOWN'
     or receipt#>>'{records,0,payload,temporal,state_time,precision}' <> 'UNKNOWN'
     or receipt->>'retrieval_time' is null
     or receipt ? 'timestamp' then
    raise exception 'recall exercise failed: current recall receipt is wrong: %', receipt;
  end if;

  if not exists (
    select 1
    from jsonb_array_elements_text(receipt->'limitations') as limitation(value)
    where value = 'retrieval_time is the database invocation time of this recall only; it is not event_time, state_time, record_time, delivery time, recollection time, or receipt-generation time.'
  ) then
    raise exception 'recall exercise failed: retrieval_time boundary is missing: %', receipt;
  end if;

  if receipt->'record_ids' @> jsonb_build_array(root_id) then
    raise exception 'recall exercise failed: superseded root leaked into recall';
  end if;

  receipt := public.recall_vera_context_v3(
    'MREQ-e2e-recall-branch-b',
    'vera-memory-e2e',
    'branch-b',
    array['memory.e2e.current']::text[],
    array['PROJECT']::text[],
    false,
    8
  );

  if jsonb_array_length(receipt->'records') <> 1
     or receipt#>>'{records,0,statement}' <> 'Foreign branch memory value.'
     or receipt#>>'{records,0,payload,temporal,state_time,precision}' <> 'UNKNOWN'
     or receipt#>>'{records,0,payload,temporal,state_time,storage,mode}' <> 'NOT_NULL_COMPATIBILITY_SENTINEL'
     or receipt#>>'{records,0,payload,temporal,state_time,storage,temporal_claim}' <> 'false' then
    raise exception 'recall exercise failed: branch-b record not isolated or unknown state_time was misrepresented: %', receipt;
  end if;

  receipt := public.recall_vera_context_v3(
    'MREQ-e2e-recall-private-denied',
    'vera-memory-e2e',
    'branch-a',
    array['memory.e2e.private']::text[],
    array['PROJECT']::text[],
    false,
    8
  );

  if jsonb_array_length(receipt->'records') <> 0 then
    raise exception 'recall exercise failed: unauthorized private record leaked: %', receipt;
  end if;

  receipt := public.recall_vera_context_v3(
    'MREQ-e2e-recall-private-allowed',
    'vera-memory-e2e',
    'branch-a',
    array['memory.e2e.private']::text[],
    array['PRIVATE']::text[],
    false,
    8
  );

  if jsonb_array_length(receipt->'records') <> 1
     or receipt#>>'{records,0,statement}' <> 'Private scoped value.' then
    raise exception 'recall exercise failed: explicitly allowed private record missing: %', receipt;
  end if;

  receipt := public.recall_vera_context_v3(
    'MREQ-e2e-recall-model-default',
    'vera-memory-e2e',
    'branch-a',
    array['memory.e2e.model_claim']::text[],
    array['PROJECT']::text[],
    false,
    8
  );

  if jsonb_array_length(receipt->'records') <> 0 then
    raise exception 'recall exercise failed: model-generated claim entered default routing: %', receipt;
  end if;

  receipt := public.recall_vera_context_v3(
    'MREQ-e2e-recall-model-audit',
    'vera-memory-e2e',
    'branch-a',
    array['memory.e2e.model_claim']::text[],
    array['PROJECT']::text[],
    true,
    8
  );

  if jsonb_array_length(receipt->'records') <> 1
     or receipt#>>'{records,0,epistemic_status}' <> 'MODEL_GENERATED_CLAIM'
     or receipt#>>'{records,0,source_actor}' <> 'CHATGPT_MODEL' then
    raise exception 'recall exercise failed: explicit model-output audit recall is wrong: %', receipt;
  end if;

  receipt := public.recall_vera_context_v3(
    'MREQ-e2e-recall-rejected',
    'vera-memory-e2e',
    'branch-a',
    array['memory.e2e.rejected']::text[],
    array['PROJECT']::text[],
    true,
    8
  );

  if jsonb_array_length(receipt->'records') <> 0 then
    raise exception 'recall exercise failed: rejected record entered recall: %', receipt;
  end if;
end;
$$;

rollback;