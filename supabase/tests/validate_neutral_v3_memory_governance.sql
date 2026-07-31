-- Run after both bounded Memory migrations. All synthetic writes roll back.

begin;

do $$
declare
  blocked boolean;
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.vera_context_events_v3'::regclass
      and conname in (
        'vera_context_events_v3_source_evidence_nonempty_chk',
        'vera_context_events_v3_semantic_tags_nonempty_chk',
        'vera_context_events_v3_model_actor_classification_chk',
        'vera_context_events_v3_model_output_epistemic_chk'
      )
    group by conrelid
    having count(*) = 4
  ) then
    raise exception 'governance validation failed: one or more constraints are missing';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-governance-empty-evidence',
      jsonb_build_object(
        'project_id', 'vera-memory-governance-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.governance.empty_evidence',
        'record_type', 'DECISION',
        'statement', 'Missing evidence must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'DIRECT_USER_STATEMENT',
        'source_actor', 'USER',
        'privacy_scope', 'PROJECT',
        'source_evidence', '[]'::jsonb,
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory'))
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'governance validation failed: empty source evidence was accepted';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-governance-empty-tags',
      jsonb_build_object(
        'project_id', 'vera-memory-governance-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.governance.empty_tags',
        'record_type', 'DECISION',
        'statement', 'Missing semantic tags must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'DIRECT_USER_STATEMENT',
        'source_actor', 'USER',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', '{}'::jsonb
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'governance validation failed: empty semantic tags were accepted';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-governance-model-promotion',
      jsonb_build_object(
        'project_id', 'vera-memory-governance-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.governance.model_promotion',
        'record_type', 'FACT',
        'statement', 'Model output must not become a fact.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'DOCUMENTED_SOURCE',
        'source_actor', 'CHATGPT_MODEL',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory'))
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'governance validation failed: ChatGPT model output was promoted';
  end if;

  blocked := false;
  begin
    perform public.append_vera_context_v3(
      'MREQ-governance-model-output-status',
      jsonb_build_object(
        'project_id', 'vera-memory-governance-test',
        'branch_id', 'branch-a',
        'record_key', 'memory.governance.model_output_status',
        'record_type', 'MODEL_OUTPUT',
        'statement', 'Model output with wrong epistemic status must fail.',
        'lifecycle_status', 'CURRENT',
        'epistemic_status', 'SUPPORTED_INFERENCE',
        'source_actor', 'EXTERNAL',
        'privacy_scope', 'PROJECT',
        'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
        'semantic_tags', jsonb_build_object('topics', jsonb_build_array('memory'))
      )
    );
  exception when others then
    blocked := true;
  end;
  if not blocked then
    raise exception 'governance validation failed: MODEL_OUTPUT used a promoted status';
  end if;

  perform public.append_vera_context_v3(
    'MREQ-governance-valid-model-output',
    jsonb_build_object(
      'project_id', 'vera-memory-governance-test',
      'branch_id', 'branch-a',
      'record_key', 'memory.governance.valid_model_output',
      'record_type', 'MODEL_OUTPUT',
      'statement', 'Valid audit-only model output.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'MODEL_GENERATED_CLAIM',
      'source_actor', 'CHATGPT_MODEL',
      'privacy_scope', 'TECHNICAL',
      'source_evidence', jsonb_build_array(jsonb_build_object('surface', 'CI')),
      'semantic_tags', jsonb_build_object(
        'topics', jsonb_build_array('memory', 'model_output'),
        'status', jsonb_build_array('audit_only')
      ),
      'limitations', jsonb_build_array('Not introspective evidence.')
    )
  );
end;
$$;

rollback;
