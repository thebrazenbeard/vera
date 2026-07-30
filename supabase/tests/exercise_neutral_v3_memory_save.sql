-- First half of the independently invoked memory-cycle proof.
-- This script commits synthetic records to the disposable local Supabase stack.
-- The recall proof runs later through a separate psql invocation.

begin;

do $$
declare
  root_receipt jsonb;
  successor_receipt jsonb;
  root_id uuid;
begin
  root_receipt := public.append_vera_context_v3(
    'MREQ-e2e-save-root',
    jsonb_build_object(
      'project_id', 'vera-memory-e2e',
      'branch_id', 'branch-a',
      'record_key', 'memory.e2e.current',
      'record_type', 'DECISION',
      'statement', 'Initial governed memory value.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'DIRECT_USER_STATEMENT',
      'source_actor', 'USER',
      'privacy_scope', 'PROJECT',
      'event_time', '2026-07-30T21:10:00+00:00',
      'state_time', '2026-07-30T21:10:00+00:00',
      'payload', jsonb_build_object(
        'cycle', 'memory-cross-chat-contract-v1',
        'version', 1
      ),
      'source_evidence', jsonb_build_array(
        jsonb_build_object(
          'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
          'source_actor', 'USER',
          'claim', 'Initial governed memory value.'
        )
      ),
      'semantic_tags', jsonb_build_object(
        'entities', jsonb_build_array('V.E.R.A.'),
        'topics', jsonb_build_array('memory', 'cross-chat', 'governance'),
        'status', jsonb_build_array('current')
      ),
      'limitations', jsonb_build_array(
        'Synthetic CI record in a disposable database.'
      )
    )
  );

  if root_receipt->>'schema' <> 'VERA_MVE_RECEIPT_V3'
     or root_receipt->>'operation' <> 'SAVE'
     or root_receipt->>'outcome_code' <> 'MVE_SAVE_COMPLETE'
     or root_receipt#>>'{write,external_persistence}' <> 'CONFIRMED_BY_DATABASE'
     or root_receipt#>>'{write,transactional_writeback}' <> 'COMPLETED'
     or jsonb_array_length(root_receipt->'record_ids') <> 1 then
    raise exception 'save exercise failed: root receipt is incomplete: %', root_receipt;
  end if;

  root_id := (root_receipt#>>'{record_ids,0}')::uuid;

  successor_receipt := public.append_vera_context_v3(
    'MREQ-e2e-save-successor',
    jsonb_build_object(
      'project_id', 'vera-memory-e2e',
      'branch_id', 'branch-a',
      'record_key', 'memory.e2e.current',
      'record_type', 'CORRECTION',
      'statement', 'Corrected governed memory value.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'DIRECT_USER_STATEMENT',
      'source_actor', 'USER',
      'privacy_scope', 'PROJECT',
      'event_time', '2026-07-30T21:11:00+00:00',
      'state_time', '2000-01-01T00:00:00+00:00',
      'supersedes_record_id', root_id,
      'payload', jsonb_build_object(
        'cycle', 'memory-cross-chat-contract-v1',
        'version', 2
      ),
      'source_evidence', jsonb_build_array(
        jsonb_build_object(
          'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
          'source_actor', 'USER',
          'claim', 'Corrected governed memory value.'
        )
      ),
      'semantic_tags', jsonb_build_object(
        'entities', jsonb_build_array('V.E.R.A.'),
        'topics', jsonb_build_array('memory', 'cross-chat', 'governance'),
        'status', jsonb_build_array('current', 'corrected')
      ),
      'limitations', jsonb_build_array(
        'Synthetic CI record in a disposable database.'
      )
    )
  );

  if successor_receipt->>'operation' <> 'SAVE'
     or successor_receipt#>>'{write,external_persistence}' <> 'CONFIRMED_BY_DATABASE'
     or successor_receipt#>>'{records,0,supersedes_record_id}' <> root_id::text then
    raise exception 'save exercise failed: successor receipt is incomplete: %',
      successor_receipt;
  end if;

  perform public.append_vera_context_v3(
    'MREQ-e2e-save-foreign-branch',
    jsonb_build_object(
      'project_id', 'vera-memory-e2e',
      'branch_id', 'branch-b',
      'record_key', 'memory.e2e.current',
      'record_type', 'DECISION',
      'statement', 'Foreign branch memory value.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'DIRECT_USER_STATEMENT',
      'source_actor', 'USER',
      'privacy_scope', 'PROJECT',
      'payload', jsonb_build_object('version', 99),
      'source_evidence', jsonb_build_array(
        jsonb_build_object(
          'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
          'observation', 'Foreign branch memory value was written for isolation testing.'
        )
      ),
      'semantic_tags', jsonb_build_object(
        'topics', jsonb_build_array('memory'),
        'status', jsonb_build_array('current')
      ),
      'limitations', jsonb_build_array('Synthetic foreign-branch test record.')
    )
  );

  perform public.append_vera_context_v3(
    'MREQ-e2e-save-private',
    jsonb_build_object(
      'project_id', 'vera-memory-e2e',
      'branch_id', 'branch-a',
      'record_key', 'memory.e2e.private',
      'record_type', 'FACT',
      'statement', 'Private scoped value.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'DOCUMENTED_SOURCE',
      'source_actor', 'EXTERNAL',
      'privacy_scope', 'PRIVATE',
      'source_evidence', jsonb_build_array(
        jsonb_build_object(
          'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
          'observation', 'Private scoped value was written for authorization-filter testing.'
        )
      ),
      'semantic_tags', jsonb_build_object(
        'topics', jsonb_build_array('memory', 'privacy'),
        'status', jsonb_build_array('current')
      ),
      'limitations', jsonb_build_array('Synthetic privacy-filter test record.')
    )
  );

  perform public.append_vera_context_v3(
    'MREQ-e2e-save-model-claim',
    jsonb_build_object(
      'project_id', 'vera-memory-e2e',
      'branch_id', 'branch-a',
      'record_key', 'memory.e2e.model_claim',
      'record_type', 'MODEL_OUTPUT',
      'statement', 'Generated language stored for audit only.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'MODEL_GENERATED_CLAIM',
      'source_actor', 'CHATGPT_MODEL',
      'privacy_scope', 'PROJECT',
      'payload', jsonb_build_object(
        'model_context', jsonb_build_object(
          'runtime', 'CHATGPT',
          'source_surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE'
        )
      ),
      'source_evidence', jsonb_build_array(
        jsonb_build_object(
          'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
          'generation_id', 'MREQ-e2e-save-model-claim'
        )
      ),
      'semantic_tags', jsonb_build_object(
        'topics', jsonb_build_array('memory', 'model_output'),
        'status', jsonb_build_array('audit_only')
      ),
      'limitations', jsonb_build_array(
        'Generated language is not introspective evidence.'
      )
    )
  );

  perform public.append_vera_context_v3(
    'MREQ-e2e-save-rejected',
    jsonb_build_object(
      'project_id', 'vera-memory-e2e',
      'branch_id', 'branch-a',
      'record_key', 'memory.e2e.rejected',
      'record_type', 'HYPOTHESIS',
      'statement', 'Rejected memory candidate.',
      'lifecycle_status', 'CURRENT',
      'epistemic_status', 'REJECTED',
      'source_actor', 'UNRESOLVED',
      'privacy_scope', 'PROJECT',
      'source_evidence', jsonb_build_array(
        jsonb_build_object(
          'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
          'observation', 'Rejected candidate retained only for exclusion testing.'
        )
      ),
      'semantic_tags', jsonb_build_object(
        'topics', jsonb_build_array('memory', 'rejection'),
        'status', jsonb_build_array('rejected')
      ),
      'limitations', jsonb_build_array('Synthetic rejection-filter test record.')
    )
  );
end;
$$;

commit;
