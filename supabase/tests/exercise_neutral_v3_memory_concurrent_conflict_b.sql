with payload as (
  select jsonb_build_object(
    'project_id', 'vera-memory-concurrent-conflict-test',
    'branch_id', 'branch-a',
    'record_key', 'memory.concurrent-conflict.b',
    'record_type', 'FACT',
    'statement', 'Concurrent changed-payload fixture B.',
    'lifecycle_status', 'CURRENT',
    'epistemic_status', 'DOCUMENTED_SOURCE',
    'source_actor', 'EXTERNAL',
    'privacy_scope', 'PROJECT',
    'event_time', '2026-07-31T01:01:00+00:00',
    'state_time', '2026-07-31T01:01:00+00:00',
    'source_evidence', jsonb_build_array(
      jsonb_build_object(
        'surface', 'GITHUB_ACTIONS_LOCAL_SUPABASE',
        'observation', 'Concurrent changed-payload fixture B.'
      )
    ),
    'semantic_tags', jsonb_build_object(
      'topics', jsonb_build_array('memory', 'concurrency', 'conflict'),
      'status', jsonb_build_array('test')
    ),
    'limitations', jsonb_build_array(
      'Synthetic CI record in a disposable database.'
    )
  ) as value
), result as (
  select
    public.vera_memory_request_hash_v3('SAVE', value) as expected_hash,
    public.append_vera_context_v3(
      'MREQ-concurrent-conflict-identity',
      value
    ) as receipt
  from payload
)
select jsonb_build_object(
  'payload_id', 'B',
  'expected_hash', expected_hash,
  'result', receipt
)::text
from result;
