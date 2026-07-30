-- Adversarial validation for independent-review corrections.
-- All synthetic writes roll back.

begin;

do $$
declare
  receipt jsonb;
  blocked boolean;
begin
  if to_regclass('public.vera_context_lineage_anomalies_v3') is null then
    raise exception 'review correction validation failed: lineage anomaly view is missing';
  end if;

  if exists (select 1 from public.vera_context_lineage_anomalies_v3) then
    raise exception 'review correction validation failed: valid baseline reports a lineage anomaly';
  end if;

  -- Force-inject two malformed cyclic components into the disposable database.
  alter table public.vera_context_events_v3 disable trigger all;

  insert into public.vera_context_events_v3 (
    record_id, project_id, branch_id, record_key, record_type, statement,
    lifecycle_status, epistemic_status, source_actor, privacy_scope,
    event_time, state_time, record_time, supersedes_record_id,
    payload, source_evidence, semantic_tags, limitations, notes
  ) values
  (
    '31000000-0000-0000-0000-000000000001',
    'vera-memory-review-test', 'branch-cycle', 'memory.cycle.two-node',
    'TECHNICAL_RESULT', 'Two-node cycle A.', 'CURRENT',
    'OBSERVED_TOOL_RESULT', 'TOOL', 'PROJECT', null, now(), now(),
    '31000000-0000-0000-0000-000000000002', '{}'::jsonb,
    '[{"surface":"CI","observation":"forced two-node cycle A"}]'::jsonb,
    '{"topics":["memory","cycle"]}'::jsonb,
    '["Synthetic corruption fixture."]'::jsonb, null
  ),
  (
    '31000000-0000-0000-0000-000000000002',
    'vera-memory-review-test', 'branch-cycle', 'memory.cycle.two-node',
    'TECHNICAL_RESULT', 'Two-node cycle B.', 'CURRENT',
    'OBSERVED_TOOL_RESULT', 'TOOL', 'PROJECT', null, now(), now(),
    '31000000-0000-0000-0000-000000000001', '{}'::jsonb,
    '[{"surface":"CI","observation":"forced two-node cycle B"}]'::jsonb,
    '{"topics":["memory","cycle"]}'::jsonb,
    '["Synthetic corruption fixture."]'::jsonb, null
  ),
  (
    '32000000-0000-0000-0000-000000000001',
    'vera-memory-review-test', 'branch-cycle', 'memory.cycle.longer',
    'TECHNICAL_RESULT', 'Longer cycle A.', 'CURRENT',
    'OBSERVED_TOOL_RESULT', 'TOOL', 'PROJECT', null, now(), now(),
    '32000000-0000-0000-0000-000000000003', '{}'::jsonb,
    '[{"surface":"CI","observation":"forced longer cycle A"}]'::jsonb,
    '{"topics":["memory","cycle"]}'::jsonb,
    '["Synthetic corruption fixture."]'::jsonb, null
  ),
  (
    '32000000-0000-0000-0000-000000000002',
    'vera-memory-review-test', 'branch-cycle', 'memory.cycle.longer',
    'TECHNICAL_RESULT', 'Longer cycle B.', 'CURRENT',
    'OBSERVED_TOOL_RESULT', 'TOOL', 'PROJECT', null, now(), now(),
    '32000000-0000-0000-0000-000000000001', '{}'::jsonb,
    '[{"surface":"CI","observation":"forced longer cycle B"}]'::jsonb,
    '{"topics":["memory","cycle"]}'::jsonb,
    '["Synthetic corruption fixture."]'::jsonb, null
  ),
  (
    '32000000-0000-0000-0000-000000000003',
    'vera-memory-review-test', 'branch-cycle', 'memory.cycle.longer',
    'TECHNICAL_RESULT', 'Longer cycle C.', 'CURRENT',
    'OBSERVED_TOOL_RESULT', 'TOOL', 'PROJECT', null, now(), now(),
    '32000000-0000-0000-0000-000000000002', '{}'::jsonb,
    '[{"surface":"CI","observation":"forced longer cycle C"}]'::jsonb,
    '{"topics":["memory","cycle"]}'::jsonb,
    '["Synthetic corruption fixture."]'::jsonb, null
  );

  alter table public.vera_context_events_v3 enable trigger all;

  if not exists (
    select 1
    from public.vera_context_lineage_anomalies_v3
    where project_id = 'vera-memory-review-test'
      and branch_id = 'branch-cycle'
      and record_key = 'memory.cycle.two-node'
      and has_cycle
      and head_count = 0
      and anomaly_types @> array['CYCLE', 'ZERO_HEAD']::text[]
      and cardinality(cycle_record_ids) = 2
  ) then
    raise exception 'review correction validation failed: two-node cycle was not diagnosed';
  end if;

  if not exists (
    select 1
    from public.vera_context_lineage_anomalies_v3
    where project_id = 'vera-memory-review-test'
      and branch_id = 'branch-cycle'
      and record_key = 'memory.cycle.longer'
      and has_cycle
      and head_count = 0
      and anomaly_types @> array['CYCLE', 'ZERO_HEAD']::text[]
      and cardinality(cycle_record_ids) = 3
  ) then
    raise exception 'review correction validation failed: longer cycle was not diagnosed';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-cycle-zero-head-append',
      jsonb_build_object(
        'project_id', 'vera-memory-review-test',
        'branch_id', 'branch-cycle',
        'record_key', 'memory.cycle.two-node',
        'record_type', 'TECHNICAL_RESULT',
        'statement', 'Append into a zero-head component must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'OBSERVED_TOOL_RESULT',
        'source_actor', 'TOOL',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(
          jsonb_build_object('surface', 'CI', 'observation', 'zero-head append attempt')
        ),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory', 'cycle')),
        'limitations', jsonb_build_array('Synthetic test-only record.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'review correction validation failed: append into zero-head lineage was accepted';
  end if;

  -- Structurally meaningless evidence is rejected.
  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-evidence-null',
      jsonb_build_object(
        'project_id', 'vera-memory-review-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.evidence.null',
        'record_type', 'TECHNICAL_RESULT',
        'statement', 'Null evidence entry must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'OBSERVED_TOOL_RESULT',
        'source_actor', 'TOOL',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(null),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory')),
        'limitations', jsonb_build_array('Synthetic test-only record.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'review correction validation failed: null evidence entry was accepted';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-evidence-empty-object',
      jsonb_build_object(
        'project_id', 'vera-memory-review-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.evidence.empty-object',
        'record_type', 'TECHNICAL_RESULT',
        'statement', 'Empty evidence object must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'OBSERVED_TOOL_RESULT',
        'source_actor', 'TOOL',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(jsonb_build_object()),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory')),
        'limitations', jsonb_build_array('Synthetic test-only record.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'review correction validation failed: empty evidence object was accepted';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-evidence-surface-only',
      jsonb_build_object(
        'project_id', 'vera-memory-review-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.evidence.surface-only',
        'record_type', 'TECHNICAL_RESULT',
        'statement', 'Surface-only evidence must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'OBSERVED_TOOL_RESULT',
        'source_actor', 'TOOL',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory')),
        'limitations', jsonb_build_array('Synthetic test-only record.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'review correction validation failed: unattributable surface-only evidence was accepted';
  end if;

  -- Semantic tag containers without usable values are rejected.
  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-semantic-values',
      jsonb_build_object(
        'project_id', 'vera-memory-review-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.semantic.empty-values',
        'record_type', 'TECHNICAL_RESULT',
        'statement', 'Empty semantic values must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'OBSERVED_TOOL_RESULT',
        'source_actor', 'TOOL',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(
          jsonb_build_object('surface', 'CI', 'observation', 'empty semantic values')
        ),
        'semantic_tags', jsonb_build_object(
          'topics', jsonb_build_array(),
          'status', ''
        ),
        'limitations', jsonb_build_array('Synthetic test-only record.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'review correction validation failed: semantic tags without usable values were accepted';
  end if;

  -- Model output must retain runtime/source context, generation evidence, and limitation.
  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-model-context',
      jsonb_build_object(
        'project_id', 'vera-memory-review-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.model.missing-context',
        'record_type', 'MODEL_OUTPUT',
        'statement', 'Model output missing runtime context must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'MODEL_GENERATED_CLAIM',
        'source_actor', 'CHATGPT_MODEL',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(
          jsonb_build_object('surface', 'CI', 'generation_id', 'generation-missing-context')
        ),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory', 'model-output')),
        'limitations', jsonb_build_array('Generated language is not introspective evidence.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'review correction validation failed: model output without runtime/source context was accepted';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-model-generation-evidence',
      jsonb_build_object(
        'project_id', 'vera-memory-review-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.model.missing-generation',
        'record_type', 'MODEL_OUTPUT',
        'statement', 'Model output missing generation evidence must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'MODEL_GENERATED_CLAIM',
        'source_actor', 'CHATGPT_MODEL',
        'privacy_scope', 'PROJECT',
        'payload', jsonb_build_object(
          'model_context', jsonb_build_object(
            'runtime', 'CHATGPT',
            'source_surface', 'CI_TEST'
          )
        ),
        'source_evidence', jsonb_build_array(
          jsonb_build_object('surface', 'CI', 'claim', 'generated output')
        ),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory', 'model-output')),
        'limitations', jsonb_build_array('Generated language is not introspective evidence.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'review correction validation failed: model output without generation evidence was accepted';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-invalid-model-limitation',
      jsonb_build_object(
        'project_id', 'vera-memory-review-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.model.missing-limitation',
        'record_type', 'MODEL_OUTPUT',
        'statement', 'Model output missing limitation must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'MODEL_GENERATED_CLAIM',
        'source_actor', 'CHATGPT_MODEL',
        'privacy_scope', 'PROJECT',
        'payload', jsonb_build_object(
          'model_context', jsonb_build_object(
            'runtime', 'CHATGPT',
            'source_surface', 'CI_TEST'
          )
        ),
        'source_evidence', jsonb_build_array(
          jsonb_build_object('surface', 'CI', 'generation_id', 'generation-missing-limitation')
        ),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory', 'model-output')),
        'limitations', jsonb_build_array('Synthetic test-only record.')
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'review correction validation failed: model output without non-introspective limitation was accepted';
  end if;

  receipt := public.append_vera_context_v3(
    'MREQ-valid-model-structure',
    jsonb_build_object(
      'project_id', 'vera-memory-review-test',
      'branch_id', 'branch-a',
      'record_key', 'memory.model.valid',
      'record_type', 'MODEL_OUTPUT',
      'statement', 'Valid bounded model output.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'MODEL_GENERATED_CLAIM',
      'source_actor', 'CHATGPT_MODEL',
      'privacy_scope', 'PROJECT',
      'payload', jsonb_build_object(
        'model_context', jsonb_build_object(
          'runtime', 'CHATGPT',
          'source_surface', 'CI_TEST'
        )
      ),
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'generation_id', 'generation-valid-1')
      ),
      'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory', 'model-output')),
      'limitations', jsonb_build_array('Generated language is not introspective evidence.')
    )
  );

  if receipt#>>'{records,0,record_type}' <> 'MODEL_OUTPUT'
     or receipt#>>'{records,0,epistemic_status}' <> 'MODEL_GENERATED_CLAIM'
     or receipt#>>'{records,0,source_actor}' <> 'CHATGPT_MODEL'
     or receipt#>>'{records,0,payload,model_context,runtime}' <> 'CHATGPT' then
    raise exception 'review correction validation failed: valid model output structure was not preserved: %', receipt;
  end if;

  -- More eligible records than p_max_records must produce a truthful partial receipt.
  perform public.append_vera_context_v3(
    'MREQ-page-1',
    jsonb_build_object(
      'project_id', 'vera-memory-pagination-test', 'branch_id', 'branch-a',
      'record_key', 'memory.page.1', 'record_type', 'FACT',
      'statement', 'Page record 1.', 'lifecycle_status', 'CURRENT',
      'epistemic_status', 'DOCUMENTED_SOURCE', 'source_actor', 'SYSTEM',
      'privacy_scope', 'PROJECT',
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'observation', 'page record 1')
      ),
      'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory', 'pagination')),
      'limitations', jsonb_build_array('Synthetic test-only record.')
    )
  );
  perform public.append_vera_context_v3(
    'MREQ-page-2',
    jsonb_build_object(
      'project_id', 'vera-memory-pagination-test', 'branch_id', 'branch-a',
      'record_key', 'memory.page.2', 'record_type', 'FACT',
      'statement', 'Page record 2.', 'lifecycle_status', 'CURRENT',
      'epistemic_status', 'DOCUMENTED_SOURCE', 'source_actor', 'SYSTEM',
      'privacy_scope', 'PROJECT',
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'observation', 'page record 2')
      ),
      'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory', 'pagination')),
      'limitations', jsonb_build_array('Synthetic test-only record.')
    )
  );
  perform public.append_vera_context_v3(
    'MREQ-page-3',
    jsonb_build_object(
      'project_id', 'vera-memory-pagination-test', 'branch_id', 'branch-a',
      'record_key', 'memory.page.3', 'record_type', 'FACT',
      'statement', 'Page record 3.', 'lifecycle_status', 'CURRENT',
      'epistemic_status', 'DOCUMENTED_SOURCE', 'source_actor', 'SYSTEM',
      'privacy_scope', 'PROJECT',
      'source_evidence', jsonb_build_array(
        jsonb_build_object('surface', 'CI', 'observation', 'page record 3')
      ),
      'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory', 'pagination')),
      'limitations', jsonb_build_array('Synthetic test-only record.')
    )
  );

  receipt := public.recall_vera_context_v3(
    'MREQ-page-recall-partial',
    'vera-memory-pagination-test',
    'branch-a',
    null,
    array['PROJECT']::text[],
    false,
    2
  );

  if receipt->>'result_class' <> 'PARTIAL'
     or receipt->>'outcome_code' <> 'MVE_RECALL_PARTIAL_TRUNCATED'
     or receipt#>>'{retrieval,completeness}' <> 'PARTIAL_TRUNCATED'
     or receipt#>>'{retrieval,total_matches}' <> '3'
     or receipt#>>'{retrieval,returned_matches}' <> '2'
     or receipt#>>'{retrieval,has_more}' <> 'true'
     or jsonb_array_length(receipt->'records') <> 2 then
    raise exception 'review correction validation failed: truncated recall was reported inaccurately: %', receipt;
  end if;

  receipt := public.recall_vera_context_v3(
    'MREQ-page-recall-complete',
    'vera-memory-pagination-test',
    'branch-a',
    null,
    array['PROJECT']::text[],
    false,
    3
  );

  if receipt->>'result_class' <> 'COMPLETE'
     or receipt->>'outcome_code' <> 'MVE_RECALL_COMPLETE'
     or receipt#>>'{retrieval,completeness}' <> 'COMPLETE_RELATIVE_TO_QUERY_SCOPE'
     or receipt#>>'{retrieval,total_matches}' <> '3'
     or receipt#>>'{retrieval,returned_matches}' <> '3'
     or receipt#>>'{retrieval,has_more}' <> 'false' then
    raise exception 'review correction validation failed: complete recall was reported inaccurately: %', receipt;
  end if;
end;
$$;

rollback;
