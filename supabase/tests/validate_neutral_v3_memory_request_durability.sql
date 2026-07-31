-- Adversarial validation for durable SAVE request identity and exact receipt
-- recovery. The concurrent exercise is committed by separate psql processes
-- before this file runs. All additional hostile writes in this file roll back.

begin;

DO $$
declare
  concurrent_record jsonb := $record$
  {
    "project_id": "vera-memory-durability",
    "branch_id": "branch-a",
    "record_key": "memory.durability.concurrent",
    "record_type": "TECHNICAL_RESULT",
    "statement": "Concurrent idempotent save committed once.",
    "lifecycle_status": "CURRENT",
    "epistemic_status": "OBSERVED_TOOL_RESULT",
    "source_actor": "TOOL",
    "privacy_scope": "PROJECT",
    "payload": {
      "contract": "memory-request-durability-v1",
      "case": "concurrent-exact-retry"
    },
    "source_evidence": [
      {
        "surface": "GITHUB_ACTIONS_LOCAL_SUPABASE",
        "tool_result_id": "MREQ-durable-concurrent-save"
      }
    ],
    "semantic_tags": {
      "topics": ["memory", "idempotency", "concurrency"],
      "status": ["test"]
    },
    "limitations": [
      "Synthetic CI record in a disposable database."
    ]
  }
  $record$::jsonb;
  journal_row public.vera_memory_request_receipts_v3%rowtype;
  recovered_receipt jsonb;
  record_count integer;
  journal_count integer;
  conflict_seen boolean := false;
begin
  select count(*) into record_count
  from public.vera_context_events_v3
  where project_id = 'vera-memory-durability'
    and branch_id = 'branch-a'
    and record_key = 'memory.durability.concurrent';

  select count(*) into journal_count
  from public.vera_memory_request_receipts_v3
  where request_id = 'MREQ-durable-concurrent-save';

  if record_count <> 1 or journal_count <> 1 then
    raise exception 'concurrent idempotency failed: records %, journal rows %',
      record_count, journal_count;
  end if;

  select * into strict journal_row
  from public.vera_memory_request_receipts_v3
  where request_id = 'MREQ-durable-concurrent-save';

  if journal_row.request_hash
       <> public.vera_memory_save_request_hash_v3(concurrent_record)
     or journal_row.operation <> 'SAVE'
     or journal_row.receipt->>'receipt_id' <> journal_row.receipt_id::text
     or journal_row.receipt#>>'{record_ids,0}' <> journal_row.record_id::text then
    raise exception 'request journal binding is incomplete: %', to_jsonb(journal_row);
  end if;

  recovered_receipt := public.append_vera_context_v3(
    'MREQ-durable-concurrent-save',
    concurrent_record
  );

  if recovered_receipt is distinct from journal_row.receipt then
    raise exception 'exact retry did not recover the exact stored receipt';
  end if;

  begin
    perform public.append_vera_context_v3(
      'MREQ-durable-concurrent-save',
      jsonb_set(
        concurrent_record,
        '{statement}',
        to_jsonb('Changed payload must not reuse the request ID.'::text)
      )
    );
  exception
    when sqlstate '22023' then
      if position('MVE_REQUEST_ID_REUSE_CONFLICT' in sqlerrm) > 0 then
        conflict_seen := true;
      else
        raise;
      end if;
  end;

  if not conflict_seen then
    raise exception 'changed-payload request-ID reuse was not rejected';
  end if;

  select count(*) into record_count
  from public.vera_context_events_v3
  where project_id = 'vera-memory-durability'
    and branch_id = 'branch-a'
    and record_key = 'memory.durability.concurrent';

  select count(*) into journal_count
  from public.vera_memory_request_receipts_v3
  where request_id = 'MREQ-durable-concurrent-save';

  if record_count <> 1 or journal_count <> 1 then
    raise exception 'reuse conflict mutated durable state: records %, journal rows %',
      record_count, journal_count;
  end if;
end;
$$;

DO $$
begin
  if not has_function_privilege(
       'service_role',
       'public.append_vera_context_v3(text,jsonb)',
       'EXECUTE'
     ) then
    raise exception 'service_role lacks governed durable append execute';
  end if;

  if has_function_privilege(
       'service_role',
       'public.append_vera_context_v3_once(text,jsonb)',
       'EXECUTE'
     ) then
    raise exception 'service_role can bypass durable request journaling';
  end if;

  if has_table_privilege(
       'service_role',
       'public.vera_memory_request_receipts_v3',
       'SELECT'
     )
     or has_table_privilege(
       'service_role',
       'public.vera_memory_request_receipts_v3',
       'INSERT'
     )
     or has_table_privilege(
       'service_role',
       'public.vera_memory_request_receipts_v3',
       'UPDATE'
     )
     or has_table_privilege(
       'service_role',
       'public.vera_memory_request_receipts_v3',
       'DELETE'
     ) then
    raise exception 'service_role has direct request-journal table privileges';
  end if;
end;
$$;

DO $$
declare
  update_blocked boolean := false;
  delete_blocked boolean := false;
begin
  begin
    update public.vera_memory_request_receipts_v3
    set request_hash = repeat('0', 64)
    where request_id = 'MREQ-durable-concurrent-save';
  exception
    when others then
      if position('append-only' in sqlerrm) > 0 then
        update_blocked := true;
      else
        raise;
      end if;
  end;

  begin
    delete from public.vera_memory_request_receipts_v3
    where request_id = 'MREQ-durable-concurrent-save';
  exception
    when others then
      if position('append-only' in sqlerrm) > 0 then
        delete_blocked := true;
      else
        raise;
      end if;
  end;

  if not update_blocked or not delete_blocked then
    raise exception 'request journal is not append-only: update %, delete %',
      update_blocked, delete_blocked;
  end if;
end;
$$;

create or replace function public.test_force_memory_request_journal_failure_v3()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
begin
  if new.request_id = 'MREQ-durable-interrupted-save' then
    raise exception 'TEST_FORCED_REQUEST_JOURNAL_FAILURE';
  end if;
  return new;
end;
$$;

create trigger test_force_memory_request_journal_failure_v3
before insert on public.vera_memory_request_receipts_v3
for each row execute function public.test_force_memory_request_journal_failure_v3();

DO $$
declare
  interrupted_record jsonb := $record$
  {
    "project_id": "vera-memory-durability",
    "branch_id": "branch-a",
    "record_key": "memory.durability.interrupted",
    "record_type": "TECHNICAL_RESULT",
    "statement": "Interrupted save must roll back before retry.",
    "lifecycle_status": "CURRENT",
    "epistemic_status": "OBSERVED_TOOL_RESULT",
    "source_actor": "TOOL",
    "privacy_scope": "PROJECT",
    "payload": {
      "contract": "memory-request-durability-v1",
      "case": "interrupted-before-journal-commit"
    },
    "source_evidence": [
      {
        "surface": "GITHUB_ACTIONS_LOCAL_SUPABASE",
        "tool_result_id": "MREQ-durable-interrupted-save"
      }
    ],
    "semantic_tags": {
      "topics": ["memory", "idempotency", "recovery"],
      "status": ["test"]
    },
    "limitations": [
      "Synthetic CI record in a disposable database."
    ]
  }
  $record$::jsonb;
  failure_seen boolean := false;
  record_count integer;
  journal_count integer;
begin
  begin
    perform public.append_vera_context_v3(
      'MREQ-durable-interrupted-save',
      interrupted_record
    );
  exception
    when others then
      if position('TEST_FORCED_REQUEST_JOURNAL_FAILURE' in sqlerrm) > 0 then
        failure_seen := true;
      else
        raise;
      end if;
  end;

  if not failure_seen then
    raise exception 'forced interrupted request did not fail';
  end if;

  select count(*) into record_count
  from public.vera_context_events_v3
  where project_id = 'vera-memory-durability'
    and branch_id = 'branch-a'
    and record_key = 'memory.durability.interrupted';

  select count(*) into journal_count
  from public.vera_memory_request_receipts_v3
  where request_id = 'MREQ-durable-interrupted-save';

  if record_count <> 0 or journal_count <> 0 then
    raise exception 'interrupted request left partial state: records %, journal rows %',
      record_count, journal_count;
  end if;
end;
$$;

drop trigger test_force_memory_request_journal_failure_v3
  on public.vera_memory_request_receipts_v3;
drop function public.test_force_memory_request_journal_failure_v3();

DO $$
declare
  interrupted_record jsonb := $record$
  {
    "project_id": "vera-memory-durability",
    "branch_id": "branch-a",
    "record_key": "memory.durability.interrupted",
    "record_type": "TECHNICAL_RESULT",
    "statement": "Interrupted save must roll back before retry.",
    "lifecycle_status": "CURRENT",
    "epistemic_status": "OBSERVED_TOOL_RESULT",
    "source_actor": "TOOL",
    "privacy_scope": "PROJECT",
    "payload": {
      "contract": "memory-request-durability-v1",
      "case": "interrupted-before-journal-commit"
    },
    "source_evidence": [
      {
        "surface": "GITHUB_ACTIONS_LOCAL_SUPABASE",
        "tool_result_id": "MREQ-durable-interrupted-save"
      }
    ],
    "semantic_tags": {
      "topics": ["memory", "idempotency", "recovery"],
      "status": ["test"]
    },
    "limitations": [
      "Synthetic CI record in a disposable database."
    ]
  }
  $record$::jsonb;
  first_receipt jsonb;
  retry_receipt jsonb;
  record_count integer;
  journal_count integer;
begin
  first_receipt := public.append_vera_context_v3(
    'MREQ-durable-interrupted-save',
    interrupted_record
  );
  retry_receipt := public.append_vera_context_v3(
    'MREQ-durable-interrupted-save',
    interrupted_record
  );

  if first_receipt is distinct from retry_receipt then
    raise exception 'post-interruption exact retry did not recover stored receipt';
  end if;

  select count(*) into record_count
  from public.vera_context_events_v3
  where project_id = 'vera-memory-durability'
    and branch_id = 'branch-a'
    and record_key = 'memory.durability.interrupted';

  select count(*) into journal_count
  from public.vera_memory_request_receipts_v3
  where request_id = 'MREQ-durable-interrupted-save';

  if record_count <> 1 or journal_count <> 1 then
    raise exception 'post-interruption retry did not commit exactly once: records %, journal rows %',
      record_count, journal_count;
  end if;
end;
$$;

rollback;
