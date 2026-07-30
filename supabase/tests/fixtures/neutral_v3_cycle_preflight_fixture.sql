-- TEST-ONLY malformed fixture for proving migration refusal.
-- Contains both a two-node cycle and a longer three-node cycle.

begin;

create table public.vera_context_events_v3 (
  record_id uuid primary key,
  project_id text not null,
  branch_id text not null,
  record_key text not null,
  supersedes_record_id uuid
);

insert into public.vera_context_events_v3 (
  record_id, project_id, branch_id, record_key, supersedes_record_id
) values
  (
    '21000000-0000-0000-0000-000000000001',
    'vera-memory-cycle-preflight',
    'branch-a',
    'memory.cycle.two-node',
    '21000000-0000-0000-0000-000000000002'
  ),
  (
    '21000000-0000-0000-0000-000000000002',
    'vera-memory-cycle-preflight',
    'branch-a',
    'memory.cycle.two-node',
    '21000000-0000-0000-0000-000000000001'
  ),
  (
    '22000000-0000-0000-0000-000000000001',
    'vera-memory-cycle-preflight',
    'branch-a',
    'memory.cycle.longer',
    '22000000-0000-0000-0000-000000000003'
  ),
  (
    '22000000-0000-0000-0000-000000000002',
    'vera-memory-cycle-preflight',
    'branch-a',
    'memory.cycle.longer',
    '22000000-0000-0000-0000-000000000001'
  ),
  (
    '22000000-0000-0000-0000-000000000003',
    'vera-memory-cycle-preflight',
    'branch-a',
    'memory.cycle.longer',
    '22000000-0000-0000-0000-000000000002'
  );

commit;
