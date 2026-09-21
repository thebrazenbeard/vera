create table if not exists public.vera_save_state_supersession_edges (
  edge_id uuid primary key default gen_random_uuid(),
  child_record_id uuid not null references public.vera_save_state_events(record_id),
  parent_record_id uuid not null references public.vera_save_state_events(record_id),
  reason text not null,
  source_evidence jsonb not null default '[]'::jsonb,
  record_time timestamptz not null default clock_timestamp(),
  constraint vera_save_state_supersession_edges_distinct check (child_record_id <> parent_record_id),
  constraint vera_save_state_supersession_edges_unique unique (child_record_id, parent_record_id),
  constraint vera_save_state_supersession_edges_source_array check (jsonb_typeof(source_evidence) = 'array')
);

comment on table public.vera_save_state_supersession_edges is
'Append-only supplemental supersession edges for reconciling vera_save_state_events branches that cannot be merged through the single supersedes_record_id column. Edges do not alter source records and do not grant semantic authority by themselves.';

create or replace function public.vera_validate_save_state_supersession_edge()
returns trigger
language plpgsql
set search_path to 'pg_catalog','public'
as $$
declare
  c_project text;
  c_branch text;
  c_key text;
  c_state timestamptz;
  p_project text;
  p_branch text;
  p_key text;
  p_state timestamptz;
  would_cycle boolean;
begin
  select project_id, branch_id, record_key, state_time
    into c_project, c_branch, c_key, c_state
    from public.vera_save_state_events
   where record_id = new.child_record_id;

  select project_id, branch_id, record_key, state_time
    into p_project, p_branch, p_key, p_state
    from public.vera_save_state_events
   where record_id = new.parent_record_id;

  if c_project is null or p_project is null then
    raise exception 'supplemental supersession edge references missing save-state record';
  end if;

  if c_project is distinct from p_project
     or c_branch is distinct from p_branch
     or c_key is distinct from p_key then
    raise exception 'supplemental supersession edge must stay within one project/branch/record_key';
  end if;

  if c_state < p_state then
    raise exception 'supplemental supersession child cannot predate parent state_time';
  end if;

  with recursive all_edges as (
    select record_id as child_record_id, supersedes_record_id as parent_record_id
      from public.vera_save_state_events
     where supersedes_record_id is not null
    union
    select child_record_id, parent_record_id
      from public.vera_save_state_supersession_edges
  ), descendants(node) as (
    select e.child_record_id
      from all_edges e
     where e.parent_record_id = new.child_record_id
    union
    select e.child_record_id
      from all_edges e
      join descendants d on e.parent_record_id = d.node
  )
  select exists(select 1 from descendants where node = new.parent_record_id)
    into would_cycle;

  if would_cycle then
    raise exception 'supplemental supersession edge would create a cycle';
  end if;

  return new;
end;
$$;

drop trigger if exists vera_save_state_supersession_edges_validate on public.vera_save_state_supersession_edges;
create trigger vera_save_state_supersession_edges_validate
before insert on public.vera_save_state_supersession_edges
for each row execute function public.vera_validate_save_state_supersession_edge();

create or replace function public.block_vera_supersession_edge_mutation()
returns trigger
language plpgsql
set search_path to 'pg_catalog','public'
as $$
begin
  raise exception 'vera_save_state_supersession_edges is append-only; write a successor edge instead';
end;
$$;

drop trigger if exists vera_save_state_supersession_edges_no_update on public.vera_save_state_supersession_edges;
create trigger vera_save_state_supersession_edges_no_update
before update on public.vera_save_state_supersession_edges
for each row execute function public.block_vera_supersession_edge_mutation();

drop trigger if exists vera_save_state_supersession_edges_no_delete on public.vera_save_state_supersession_edges;
create trigger vera_save_state_supersession_edges_no_delete
before delete on public.vera_save_state_supersession_edges
for each row execute function public.block_vera_supersession_edge_mutation();

alter table public.vera_save_state_supersession_edges enable row level security;

create or replace view public.vera_save_state_heads as
with all_edges as (
  select record_id as child_record_id, supersedes_record_id as parent_record_id
    from public.vera_save_state_events
   where supersedes_record_id is not null
  union
  select child_record_id, parent_record_id
    from public.vera_save_state_supersession_edges
)
select e.*
  from public.vera_save_state_events e
 where not exists (
   select 1
     from all_edges x
    where x.parent_record_id = e.record_id
 );

create or replace view public.vera_save_state_head_status as
select project_id,
       branch_id,
       record_key,
       count(*)::bigint as head_count,
       array_agg(record_id order by state_time desc, record_time desc, record_id desc) as head_record_ids
  from public.vera_save_state_heads
 group by project_id, branch_id, record_key;

create or replace view public.vera_current_save_state as
select h.record_id,
       h.project_id,
       h.branch_id,
       h.record_key,
       h.record_kind,
       h.statement,
       h.lifecycle_status,
       h.epistemic_status,
       h.authorship,
       h.privacy_scope,
       h.event_time,
       h.state_time,
       h.record_time,
       h.supersedes_record_id,
       h.payload,
       h.source_evidence,
       h.semantic_tags,
       h.notes
  from public.vera_save_state_heads h
  join public.vera_save_state_head_status s
    on s.project_id = h.project_id
   and s.branch_id = h.branch_id
   and s.record_key = h.record_key
   and s.head_count = 1;

comment on view public.vera_current_save_state is
'Fail-closed current save-state projection. Returns a record only when the supersession graph resolves to exactly one head within project_id + branch_id + record_key. Uses native and supplemental supersession edges; chronology alone never chooses among competing heads.';