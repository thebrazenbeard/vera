create or replace function public.block_brigit_save_state_mutation()
returns trigger language plpgsql set search_path='pg_catalog','public' as $$
begin
  raise exception 'brigit_save_state_events is append-only; write a superseding record instead';
end; $$;
create trigger brigit_save_state_events_no_update before update on public.brigit_save_state_events for each row execute function public.block_brigit_save_state_mutation();
create trigger brigit_save_state_events_no_delete before delete on public.brigit_save_state_events for each row execute function public.block_brigit_save_state_mutation();

create table public.brigit_save_state_supersession_edges (
  edge_id uuid primary key default gen_random_uuid(),
  child_record_id uuid not null references public.brigit_save_state_events(record_id),
  parent_record_id uuid not null references public.brigit_save_state_events(record_id),
  reason text not null,
  source_evidence jsonb not null default '[]'::jsonb check (jsonb_typeof(source_evidence)='array'),
  record_time timestamptz not null default clock_timestamp(),
  unique(child_record_id,parent_record_id)
);
comment on table public.brigit_save_state_supersession_edges is 'Append-only supplemental supersession edges for reconciling Brigit save-state branches that cannot be merged through the single supersedes_record_id column.';
alter table public.brigit_save_state_supersession_edges enable row level security;
create policy brigit_save_state_edges_no_client_access on public.brigit_save_state_supersession_edges for all to anon,authenticated using(false) with check(false);
revoke all on public.brigit_save_state_supersession_edges from anon,authenticated;
grant select,insert on public.brigit_save_state_supersession_edges to service_role;

create or replace function public.block_brigit_supersession_edge_mutation()
returns trigger language plpgsql set search_path='pg_catalog','public' as $$
begin
  raise exception 'brigit_save_state_supersession_edges is append-only';
end; $$;

create or replace function public.brigit_validate_save_state_supersession_edge()
returns trigger language plpgsql set search_path='pg_catalog','public' as $$
declare
  c_project text; c_branch text; c_key text; c_state timestamptz;
  p_project text; p_branch text; p_key text; p_state timestamptz;
  would_cycle boolean;
begin
  select project_id,branch_id,record_key,state_time into c_project,c_branch,c_key,c_state from public.brigit_save_state_events where record_id=new.child_record_id;
  select project_id,branch_id,record_key,state_time into p_project,p_branch,p_key,p_state from public.brigit_save_state_events where record_id=new.parent_record_id;
  if c_project is null or p_project is null then raise exception 'supplemental supersession edge references missing save-state record'; end if;
  if c_project is distinct from p_project or c_branch is distinct from p_branch or c_key is distinct from p_key then raise exception 'supplemental supersession edge must stay within one project/branch/record_key'; end if;
  if c_state < p_state then raise exception 'supplemental supersession child cannot predate parent state_time'; end if;
  with recursive all_edges as (
    select record_id child_record_id,supersedes_record_id parent_record_id from public.brigit_save_state_events where supersedes_record_id is not null
    union
    select child_record_id,parent_record_id from public.brigit_save_state_supersession_edges
  ), descendants(node) as (
    select e.child_record_id from all_edges e where e.parent_record_id=new.child_record_id
    union
    select e.child_record_id from all_edges e join descendants d on e.parent_record_id=d.node
  )
  select exists(select 1 from descendants where node=new.parent_record_id) into would_cycle;
  if would_cycle then raise exception 'supplemental supersession edge would create a cycle'; end if;
  return new;
end; $$;
create trigger brigit_save_state_supersession_edges_no_update before update on public.brigit_save_state_supersession_edges for each row execute function public.block_brigit_supersession_edge_mutation();
create trigger brigit_save_state_supersession_edges_no_delete before delete on public.brigit_save_state_supersession_edges for each row execute function public.block_brigit_supersession_edge_mutation();
create trigger brigit_save_state_supersession_edges_validate before insert on public.brigit_save_state_supersession_edges for each row execute function public.brigit_validate_save_state_supersession_edge();

create view public.brigit_save_state_heads with (security_invoker=true) as
with all_edges as (
  select record_id child_record_id,supersedes_record_id parent_record_id from public.brigit_save_state_events where supersedes_record_id is not null
  union
  select child_record_id,parent_record_id from public.brigit_save_state_supersession_edges
)
select e.* from public.brigit_save_state_events e where not exists(select 1 from all_edges x where x.parent_record_id=e.record_id);
create view public.brigit_save_state_head_status with (security_invoker=true) as
select project_id,branch_id,record_key,count(*) head_count,array_agg(record_id order by state_time desc,record_time desc,record_id desc) head_record_ids from public.brigit_save_state_heads group by project_id,branch_id,record_key;
create view public.brigit_current_save_state with (security_invoker=true) as
select h.* from public.brigit_save_state_heads h join public.brigit_save_state_head_status s using(project_id,branch_id,record_key) where s.head_count=1;
create view public.brigit_legacy_quarantine with (security_invoker=true) as
select * from public.brigit_save_state_events where authorship='BRIGIT' or epistemic_status='BRIGIT_SELF_REPORT' or record_kind in ('CONATION','IDENTITY','RELATIONSHIP');
create view public.brigit_legacy_reviewable with (security_invoker=true) as
select * from public.brigit_save_state_events where not (authorship='BRIGIT' or epistemic_status='BRIGIT_SELF_REPORT' or record_kind in ('CONATION','IDENTITY','RELATIONSHIP'));
revoke all on public.brigit_save_state_heads,public.brigit_save_state_head_status,public.brigit_current_save_state,public.brigit_legacy_quarantine,public.brigit_legacy_reviewable from anon,authenticated;
grant select on public.brigit_save_state_heads,public.brigit_save_state_head_status,public.brigit_current_save_state,public.brigit_legacy_quarantine,public.brigit_legacy_reviewable to service_role;