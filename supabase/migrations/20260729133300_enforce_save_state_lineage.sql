-- Promoted from the reviewed temporal pilot draft at commit
-- 8ae8256378a158e74b51bb5baed59d2eb87f8f42.
-- Depends on 20260729133200_add_event_time_precision.sql.
-- Do not apply to production until the separately governed production gate is authorized.

begin;

-- One record may have at most one direct successor. This prevents forks.
create unique index if not exists vera_save_state_events_one_successor_idx
  on public.vera_save_state_events (supersedes_record_id)
  where supersedes_record_id is not null;

alter table public.vera_save_state_events
  add constraint vera_save_state_events_no_self_supersession
  check (supersedes_record_id is null or supersedes_record_id <> record_id);

create or replace function public.enforce_vera_save_state_lineage()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
declare
  current_head_id uuid;
  current_head_count integer;
  parent_project_id text;
  parent_branch_id text;
  parent_record_key text;
begin
  -- A caller cannot forge when Supabase persisted this row.
  new.record_time := clock_timestamp();

  -- Serialize writes for one logical state key without locking unrelated keys.
  perform pg_advisory_xact_lock(
    hashtextextended(
      new.project_id || E'\x1f' || new.branch_id || E'\x1f' || new.record_key,
      0
    )
  );

  select
    count(*),
    (array_agg(e.record_id order by e.record_id))[1]
    into current_head_count, current_head_id
  from public.vera_save_state_events e
  where e.project_id = new.project_id
    and e.branch_id = new.branch_id
    and e.record_key = new.record_key
    and not exists (
      select 1
      from public.vera_save_state_events child
      where child.supersedes_record_id = e.record_id
    );

  if new.supersedes_record_id is not null then
    select project_id, branch_id, record_key
      into parent_project_id, parent_branch_id, parent_record_key
    from public.vera_save_state_events
    where record_id = new.supersedes_record_id;

    if not found then
      raise exception 'superseded record % does not exist', new.supersedes_record_id;
    end if;

    if parent_project_id <> new.project_id
       or parent_branch_id <> new.branch_id
       or parent_record_key <> new.record_key then
      raise exception 'supersession must remain within the same project, branch, and record_key';
    end if;
  end if;

  if current_head_count = 0 then
    if new.supersedes_record_id is not null then
      raise exception 'initial record for a state key must not supersede another record';
    end if;
  elsif current_head_count = 1 then
    if new.supersedes_record_id is distinct from current_head_id then
      raise exception 'new record must supersede the unique current head %', current_head_id;
    end if;
  else
    raise exception 'state key has % current heads; resolve lineage conflict before appending', current_head_count;
  end if;

  return new;
end;
$$;

revoke all on function public.enforce_vera_save_state_lineage() from public, anon, authenticated;
grant execute on function public.enforce_vera_save_state_lineage() to service_role;

drop trigger if exists vera_save_state_events_enforce_lineage
  on public.vera_save_state_events;

create trigger vera_save_state_events_enforce_lineage
before insert on public.vera_save_state_events
for each row execute function public.enforce_vera_save_state_lineage();

-- Expose every unsuperseded head so conflicts remain visible rather than hidden.
create or replace view public.vera_save_state_heads
with (security_invoker = true)
as
select e.*
from public.vera_save_state_events e
where not exists (
  select 1
  from public.vera_save_state_events child
  where child.supersedes_record_id = e.record_id
);

-- event_time_precision changes the view shape, so recreate deliberately.
drop view public.vera_current_save_state;

-- Return only unambiguous heads. A fork becomes absent here and visible in
-- vera_save_state_lineage_conflicts instead of being resolved by timestamp.
create view public.vera_current_save_state
with (security_invoker = true)
as
with heads as (
  select h.*,
         count(*) over (
           partition by h.project_id, h.branch_id, h.record_key
         ) as head_count
  from public.vera_save_state_heads h
)
select
  record_id,
  project_id,
  branch_id,
  record_key,
  record_kind,
  statement,
  lifecycle_status,
  epistemic_status,
  authorship,
  privacy_scope,
  event_time,
  event_time_precision,
  state_time,
  record_time,
  supersedes_record_id,
  payload,
  source_evidence,
  semantic_tags,
  notes
from heads
where head_count = 1;

create or replace view public.vera_save_state_lineage_conflicts
with (security_invoker = true)
as
select
  project_id,
  branch_id,
  record_key,
  count(*) as head_count,
  array_agg(record_id order by record_time, record_id) as head_record_ids
from public.vera_save_state_heads
group by project_id, branch_id, record_key
having count(*) > 1;

revoke all privileges on table public.vera_current_save_state from public, anon, authenticated;
revoke all privileges on table public.vera_save_state_heads from public, anon, authenticated;
revoke all privileges on table public.vera_save_state_lineage_conflicts from public, anon, authenticated;

revoke all privileges on table public.vera_current_save_state from service_role;
revoke all privileges on table public.vera_save_state_heads from service_role;
revoke all privileges on table public.vera_save_state_lineage_conflicts from service_role;

grant select on table public.vera_current_save_state to service_role;
grant select on table public.vera_save_state_heads to service_role;
grant select on table public.vera_save_state_lineage_conflicts to service_role;

comment on column public.vera_save_state_events.record_time is
  'Database-assigned time Supabase persisted the row. Caller-supplied values are overwritten by the insert trigger.';
comment on view public.vera_current_save_state is
  'One unambiguous unsuperseded head per project, branch, and record key. Timestamp recency does not create authority.';
comment on view public.vera_save_state_lineage_conflicts is
  'Diagnostic view for state keys with multiple lineage heads. Conflicts are not resolved by recency.';

commit;
