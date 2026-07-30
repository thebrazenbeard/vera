-- Run after both bounded Memory migrations. All synthetic writes roll back.

begin;

do $$
declare
  receipt jsonb;
  record_id uuid;
  blocked boolean;
  derived_limitation text := 'Derived state_time is approximate and depends on the cited sequence evidence.';
  unknown_state_limitation text := 'state_time is UNKNOWN; the non-null column contains PostgreSQL -infinity only as a compatibility sentinel and not as event, state, record, delivery, recollection, or receipt-generation time evidence.';
begin
  -- Missing event_time remains NULL. Missing state_time is explicitly UNKNOWN
  -- through the payload, limitation, and non-temporal -infinity sentinel.
  receipt := public.append_vera_context_v3(
    'MREQ-temporal-unknown',
    jsonb_build_object(
      'project_id', 'vera-memory-temporal-test',
      'branch_id', 'branch-a',
      'record_key', 'memory.temporal.unknown',
      'record_type', 'TECHNICAL_RESULT',
      'statement', 'No source-supported event or state time was supplied.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'OBSERVED_TOOL_RESULT',
      'source_actor', 'TOOL',
      'privacy_scope', 'PROJECT',
      'payload', jsonb_build_object('test', true),
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'observation', 'timestamps omitted')
      ),
      'semantic_tags', jsonb_build_object(
        'topics', jsonb_build_array('memory', 'temporal-uncertainty')
      ),
      'limitations', jsonb_build_array('Synthetic test-only record.')
    )
  );

  record_id := (receipt#>>'{record_ids,0}')::uuid;
  if receipt#>>'{records,0,event_time}' is not null
     or receipt#>>'{records,0,payload,temporal,event_time,precision}' <> 'UNKNOWN'
     or receipt#>>'{records,0,payload,temporal,state_time,precision}' <> 'UNKNOWN'
     or receipt#>>'{records,0,payload,temporal,state_time,storage,mode}' <> 'NOT_NULL_COMPATIBILITY_SENTINEL'
     or receipt#>>'{records,0,payload,temporal,state_time,storage,value}' <> '-infinity'
     or receipt#>>'{records,0,payload,temporal,state_time,storage,temporal_claim}' <> 'false'
     or not (receipt#>'{records,0,limitations}') @> jsonb_build_array(unknown_state_limitation) then
    raise exception 'temporal validation failed: omitted times were not preserved as NULL/explicit UNKNOWN: %', receipt;
  end if;

  if not exists (
    select 1
    from public.vera_context_events_v3
    where public.vera_context_events_v3.record_id = record_id
      and event_time is null
      and state_time = '-infinity'::timestamptz
      and payload#>>'{temporal,state_time,storage,temporal_claim}' = 'false'
      and limitations @> jsonb_build_array(unknown_state_limitation)
  ) then
    raise exception 'temporal validation failed: database did not preserve explicit UNKNOWN state_time representation';
  end if;

  -- Caller-provided timestamps without precision remain UNKNOWN, never silently EXACT.
  receipt := public.append_vera_context_v3(
    'MREQ-temporal-unclassified-timestamps',
    jsonb_build_object(
      'project_id', 'vera-memory-temporal-test',
      'branch_id', 'branch-a',
      'record_key', 'memory.temporal.unclassified',
      'record_type', 'TECHNICAL_RESULT',
      'statement', 'Timestamps were supplied without source precision.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'OBSERVED_TOOL_RESULT',
      'source_actor', 'TOOL',
      'privacy_scope', 'PROJECT',
      'event_time', '2026-07-30T22:00:00+00:00',
      'state_time', '2026-07-30T22:01:00+00:00',
      'payload', jsonb_build_object('test', true),
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'observation', 'precision omitted')
      ),
      'semantic_tags', jsonb_build_object(
        'topics', jsonb_build_array('memory', 'temporal-uncertainty')
      ),
      'limitations', jsonb_build_array('Synthetic test-only record.')
    )
  );

  if receipt#>>'{records,0,payload,temporal,event_time,precision}' <> 'UNKNOWN'
     or receipt#>>'{records,0,payload,temporal,state_time,precision}' <> 'UNKNOWN'
     or receipt#>'{records,0,payload,temporal,state_time,storage}' is not null then
    raise exception 'temporal validation failed: supplied timestamps were silently promoted or given a sentinel: %', receipt;
  end if;

  -- Explicit supported precision is preserved.
  receipt := public.append_vera_context_v3(
    'MREQ-temporal-explicit-precision',
    jsonb_build_object(
      'project_id', 'vera-memory-temporal-test',
      'branch_id', 'branch-a',
      'record_key', 'memory.temporal.explicit',
      'record_type', 'TECHNICAL_RESULT',
      'statement', 'Temporal precision was explicitly supplied.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'OBSERVED_TOOL_RESULT',
      'source_actor', 'TOOL',
      'privacy_scope', 'PROJECT',
      'event_time', '2026-07-30T22:02:00+00:00',
      'state_time', '2026-07-30T22:02:30+00:00',
      'payload', jsonb_build_object(
        'temporal', jsonb_build_object(
          'event_time', jsonb_build_object('precision', 'EXACT'),
          'state_time', jsonb_build_object('precision', 'BOUNDED')
        )
      ),
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'observation', 'explicit precision')
      ),
      'semantic_tags', jsonb_build_object(
        'topics', jsonb_build_array('memory', 'temporal-precision')
      ),
      'limitations', jsonb_build_array('Synthetic test-only record.')
    )
  );

  if receipt#>>'{records,0,payload,temporal,event_time,precision}' <> 'EXACT'
     or receipt#>>'{records,0,payload,temporal,state_time,precision}' <> 'BOUNDED' then
    raise exception 'temporal validation failed: explicit precision was not preserved: %', receipt;
  end if;

  -- Non-UNKNOWN precision cannot be attached to an omitted time.
  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-temporal-missing-state-exact',
      jsonb_build_object(
        'project_id', 'vera-memory-temporal-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.temporal.invalid-missing-state',
        'record_type', 'TECHNICAL_RESULT',
        'statement', 'An omitted state time cannot be exact.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'OBSERVED_TOOL_RESULT',
        'source_actor', 'TOOL',
        'privacy_scope', 'PROJECT',
        'payload', jsonb_build_object(
          'temporal', jsonb_build_object(
            'state_time', jsonb_build_object('precision', 'EXACT')
          )
        ),
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory')),
        'limitations', jsonb_build_array('Synthetic test-only record.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'temporal validation failed: omitted state_time accepted EXACT precision';
  end if;

  -- Unsupported precision values are rejected.
  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-temporal-invalid-precision',
      jsonb_build_object(
        'project_id', 'vera-memory-temporal-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.temporal.invalid-precision',
        'record_type', 'TECHNICAL_RESULT',
        'statement', 'Unsupported precision must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'OBSERVED_TOOL_RESULT',
        'source_actor', 'TOOL',
        'privacy_scope', 'PROJECT',
        'event_time', '2026-07-30T22:03:00+00:00',
        'payload', jsonb_build_object(
          'temporal', jsonb_build_object(
            'event_time', jsonb_build_object('precision', 'MAGICAL')
          )
        ),
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory')),
        'limitations', jsonb_build_array('Synthetic test-only record.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'temporal validation failed: unsupported precision was accepted';
  end if;

  -- A derived state_time without evidence and a recorded limitation is rejected.
  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-temporal-derived-unsubstantiated',
      jsonb_build_object(
        'project_id', 'vera-memory-temporal-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.temporal.derived-invalid',
        'record_type', 'TECHNICAL_RESULT',
        'statement', 'Unsubstantiated derived state time must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'SUPPORTED_INFERENCE',
        'source_actor', 'TOOL',
        'privacy_scope', 'PROJECT',
        'state_time', '2026-07-30T22:04:00+00:00',
        'payload', jsonb_build_object(
          'temporal', jsonb_build_object(
            'state_time', jsonb_build_object(
              'precision', 'APPROXIMATE',
              'derivation', jsonb_build_object('method', 'sequence interpolation')
            )
          )
        ),
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory')),
        'limitations', jsonb_build_array('Synthetic test-only record.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'temporal validation failed: unsupported derived state_time was accepted';
  end if;

  -- An explicit evidence-backed derived state_time with a matching limitation is accepted.
  receipt := public.append_vera_context_v3(
    'MREQ-temporal-derived-valid',
    jsonb_build_object(
      'project_id', 'vera-memory-temporal-test',
      'branch_id', 'branch-a',
      'record_key', 'memory.temporal.derived-valid',
      'record_type', 'INTERPRETATION',
      'statement', 'Derived state time is explicitly represented as an approximation.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'SUPPORTED_INFERENCE',
      'source_actor', 'TOOL',
      'privacy_scope', 'PROJECT',
      'state_time', '2026-07-30T22:05:00+00:00',
      'payload', jsonb_build_object(
        'temporal', jsonb_build_object(
          'state_time', jsonb_build_object(
            'precision', 'APPROXIMATE',
            'derivation', jsonb_build_object(
              'method', 'sequence interpolation',
              'source_evidence', jsonb_build_array(
                jsonb_build_object('event_sequence', 29),
                jsonb_build_object('event_sequence', 31)
              ),
              'limitation', derived_limitation
            )
          )
        )
      ),
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'observation', 'derived state evidence')
      ),
      'semantic_tags', jsonb_build_object(
        'topics', jsonb_build_array('memory', 'temporal-derivation')
      ),
      'limitations', jsonb_build_array(
        'Synthetic test-only record.',
        derived_limitation
      )
    )
  );

  if receipt#>>'{records,0,state_time}' is null
     or receipt#>>'{records,0,payload,temporal,state_time,precision}' <> 'APPROXIMATE'
     or receipt#>>'{records,0,payload,temporal,state_time,derivation,method}' <> 'sequence interpolation'
     or not (receipt#>'{records,0,limitations}') @> jsonb_build_array(derived_limitation) then
    raise exception 'temporal validation failed: valid derived state_time was not preserved: %', receipt;
  end if;

  -- Recall reports invocation time only under retrieval_time.
  receipt := public.recall_vera_context_v3(
    'MREQ-temporal-recall',
    'vera-memory-temporal-test',
    'branch-a',
    array['memory.temporal.unknown']::text[],
    array['PROJECT']::text[],
    false,
    8
  );

  if receipt->>'retrieval_time' is null
     or receipt ? 'timestamp'
     or receipt ? 'event_time'
     or receipt ? 'state_time'
     or receipt ? 'record_time' then
    raise exception 'temporal validation failed: recall invocation time is ambiguous: %', receipt;
  end if;
end;
$$;

rollback;