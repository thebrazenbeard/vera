drop view if exists semantic_atlas.pending_semantic_captures;
drop view if exists semantic_atlas.capture_current_state;

alter table semantic_atlas.semantic_capture_events
  add column capture_sequence bigint generated always as identity;
alter table semantic_atlas.semantic_capture_events
  add constraint semantic_capture_events_capture_sequence_key unique (capture_sequence);

alter table semantic_atlas.semantic_capture_outcomes
  add column outcome_sequence bigint generated always as identity;
alter table semantic_atlas.semantic_capture_outcomes
  add constraint semantic_capture_outcomes_outcome_sequence_key unique (outcome_sequence);

alter table semantic_atlas.semantic_capture_outcomes
  drop constraint semantic_capture_outcomes_event_id_fkey;
alter table semantic_atlas.semantic_capture_outcomes
  add constraint semantic_capture_outcomes_event_id_fkey
  foreign key (event_id) references semantic_atlas.semantic_capture_events(event_id) on delete restrict;

alter table semantic_atlas.semantic_capture_outcomes
  add constraint semantic_capture_git_confirmation_binding_ck
  check (
    action <> 'GIT_WRITE_CONFIRMED'
    or (
      semantic_decider is not null
      and git_commit_sha is not null
      and jsonb_typeof(git_object_refs) = 'array'
      and jsonb_array_length(git_object_refs) > 0
    )
  );

create or replace function semantic_atlas.reject_capture_history_mutation_v1()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas
as $$
begin
  raise exception 'Semantic Atlas capture history is append-only';
end;
$$;

create trigger semantic_capture_events_append_only
before update or delete on semantic_atlas.semantic_capture_events
for each row execute function semantic_atlas.reject_capture_history_mutation_v1();

create trigger semantic_capture_outcomes_append_only
before update or delete on semantic_atlas.semantic_capture_outcomes
for each row execute function semantic_atlas.reject_capture_history_mutation_v1();

create or replace function semantic_atlas.capture_semantic_event_v1(
  p_idempotency_key text,
  p_source_surface text,
  p_source_locator jsonb,
  p_source_actor text,
  p_trigger_class text,
  p_salience text,
  p_semantic_key text,
  p_candidate_kind text,
  p_representation text,
  p_representation_fidelity text,
  p_privacy_scope text,
  p_evidence_ceiling text,
  p_notes text default null
) returns uuid
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas
as $$
declare
  v_event_id uuid;
  v_policy semantic_atlas.capture_policy%rowtype;
  v_existing semantic_atlas.semantic_capture_events%rowtype;
  v_locator jsonb := coalesce(p_source_locator, '{}'::jsonb);
begin
  select * into v_policy
  from semantic_atlas.capture_policy
  where policy_key = 'default' and enabled = true;

  if not found or not v_policy.auto_candidate_write then
    raise exception 'semantic capture policy disabled';
  end if;

  if p_salience not in ('MEDIUM','HIGH') then
    raise exception 'semantic capture requires MEDIUM or HIGH salience';
  end if;

  if v_policy.minimum_auto_salience = 'HIGH' and p_salience <> 'HIGH' then
    raise exception 'semantic capture below active minimum salience';
  end if;

  if not (p_trigger_class = any(v_policy.trigger_classes)) then
    raise exception 'trigger class not permitted by active capture policy';
  end if;

  select * into v_existing
  from semantic_atlas.semantic_capture_events
  where idempotency_key = p_idempotency_key;

  if found then
    if v_existing.source_surface is not distinct from p_source_surface
       and v_existing.source_locator is not distinct from v_locator
       and v_existing.source_actor is not distinct from p_source_actor
       and v_existing.detector is not distinct from 'CEE_CONTEXTUAL_V1'
       and v_existing.trigger_class is not distinct from p_trigger_class
       and v_existing.salience is not distinct from p_salience
       and v_existing.semantic_key is not distinct from p_semantic_key
       and v_existing.candidate_kind is not distinct from p_candidate_kind
       and v_existing.representation is not distinct from p_representation
       and v_existing.representation_fidelity is not distinct from p_representation_fidelity
       and v_existing.privacy_scope is not distinct from p_privacy_scope
       and v_existing.evidence_ceiling is not distinct from p_evidence_ceiling
       and v_existing.notes is not distinct from p_notes
    then
      return v_existing.event_id;
    end if;
    raise exception 'idempotency key collision with changed immutable semantic capture payload';
  end if;

  insert into semantic_atlas.semantic_capture_events (
    idempotency_key, source_surface, source_locator, source_actor,
    trigger_class, salience, semantic_key, candidate_kind,
    representation, representation_fidelity, privacy_scope,
    evidence_ceiling, notes
  ) values (
    p_idempotency_key, p_source_surface, v_locator, p_source_actor,
    p_trigger_class, p_salience, p_semantic_key, p_candidate_kind,
    p_representation, p_representation_fidelity, p_privacy_scope,
    p_evidence_ceiling, p_notes
  ) returning event_id into v_event_id;

  return v_event_id;
end;
$$;

create view semantic_atlas.capture_current_state as
select e.*,
       o.action as latest_action,
       o.semantic_decider,
       o.decision_payload,
       o.git_commit_sha,
       o.git_object_refs,
       o.record_time as outcome_time,
       o.outcome_sequence
from semantic_atlas.semantic_capture_events e
left join lateral (
  select x.* from semantic_atlas.semantic_capture_outcomes x
  where x.event_id = e.event_id
  order by x.outcome_sequence desc
  limit 1
) o on true;

create view semantic_atlas.pending_semantic_captures as
select * from semantic_atlas.capture_current_state
where latest_action is null or latest_action in ('HOLD','ADJUDICATE_PENDING_GIT')
order by case salience when 'HIGH' then 0 else 1 end, capture_sequence;

alter table semantic_atlas.runtime_objects alter column source_path set not null;
alter table semantic_atlas.runtime_objects alter column payload_sha256 set not null;

alter table semantic_atlas.runtime_snapshots
  add column pathset_sha256 text null check (pathset_sha256 is null or pathset_sha256 ~ '^[0-9a-f]{64}$'),
  add column snapshot_sha256 text null check (snapshot_sha256 is null or snapshot_sha256 ~ '^[0-9a-f]{64}$'),
  add column expected_object_count integer null check (expected_object_count is null or expected_object_count >= 0),
  add column validation_state text not null default 'UNVERIFIED' check (validation_state in ('UNVERIFIED','VERIFIED','FAILED')),
  add column validated_at timestamptz null;

alter table semantic_atlas.runtime_snapshots
  add constraint semantic_atlas_active_snapshot_verified_ck
  check (
    state <> 'ACTIVE'
    or (
      validation_state = 'VERIFIED'
      and validated_at is not null
      and manifest_sha256 is not null
      and pathset_sha256 is not null
      and snapshot_sha256 is not null
      and expected_object_count is not null
    )
  );

create or replace function semantic_atlas.activate_runtime_snapshot_v1(p_snapshot_id uuid)
returns void
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas, extensions
as $$
declare
  v_snapshot semantic_atlas.runtime_snapshots%rowtype;
  v_count integer;
  v_counts jsonb;
  v_pathset_sha text;
  v_snapshot_sha text;
begin
  select * into v_snapshot
  from semantic_atlas.runtime_snapshots
  where snapshot_id = p_snapshot_id
  for update;

  if not found then
    raise exception 'runtime snapshot not found';
  end if;
  if v_snapshot.state <> 'LOADING' then
    raise exception 'runtime snapshot must be LOADING before activation';
  end if;
  if v_snapshot.manifest_sha256 is null
     or v_snapshot.pathset_sha256 is null
     or v_snapshot.snapshot_sha256 is null
     or v_snapshot.expected_object_count is null then
    raise exception 'runtime snapshot missing manifest/pathset/snapshot digest or expected object count';
  end if;

  select count(*)::integer into v_count
  from semantic_atlas.runtime_objects
  where snapshot_id = p_snapshot_id;

  if v_count <> v_snapshot.expected_object_count then
    raise exception 'runtime object count mismatch: expected %, observed %', v_snapshot.expected_object_count, v_count;
  end if;

  select coalesce(jsonb_object_agg(object_type, type_count), '{}'::jsonb)
  into v_counts
  from (
    select object_type, count(*)::integer as type_count
    from semantic_atlas.runtime_objects
    where snapshot_id = p_snapshot_id
    group by object_type
  ) q;

  select encode(extensions.digest(coalesce(string_agg(distinct source_path, E'\n' order by source_path), ''), 'sha256'), 'hex')
  into v_pathset_sha
  from semantic_atlas.runtime_objects
  where snapshot_id = p_snapshot_id;

  select encode(extensions.digest(coalesce(string_agg(
    source_path || E'\t' || object_id || E'\t' || object_type || E'\t' || payload_sha256,
    E'\n' order by source_path, object_id
  ), ''), 'sha256'), 'hex')
  into v_snapshot_sha
  from semantic_atlas.runtime_objects
  where snapshot_id = p_snapshot_id;

  if v_pathset_sha <> v_snapshot.pathset_sha256 then
    raise exception 'runtime pathset digest mismatch';
  end if;
  if v_snapshot_sha <> v_snapshot.snapshot_sha256 then
    raise exception 'runtime materialization digest mismatch';
  end if;

  update semantic_atlas.runtime_snapshots
  set state = 'SUPERSEDED'
  where authority_scope = v_snapshot.authority_scope
    and state = 'ACTIVE'
    and snapshot_id <> p_snapshot_id;

  update semantic_atlas.runtime_snapshots
  set state = 'ACTIVE',
      validation_state = 'VERIFIED',
      validated_at = clock_timestamp(),
      object_counts = v_counts
  where snapshot_id = p_snapshot_id;
end;
$$;

create or replace function semantic_atlas.mark_runtime_snapshot_failed_v1(p_snapshot_id uuid, p_notes text)
returns void
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas
as $$
begin
  update semantic_atlas.runtime_snapshots
  set state = 'FAILED', validation_state = 'FAILED', notes = concat_ws(E'\n', notes, p_notes)
  where snapshot_id = p_snapshot_id and state = 'LOADING';
  if not found then
    raise exception 'only a LOADING runtime snapshot may be marked FAILED';
  end if;
end;
$$;

revoke update, delete on semantic_atlas.semantic_capture_events from service_role;
revoke update, delete on semantic_atlas.semantic_capture_outcomes from service_role;
revoke update, delete on semantic_atlas.runtime_snapshots from service_role;
revoke update, delete on semantic_atlas.runtime_objects from service_role;
revoke update, delete on semantic_atlas.capture_policy from service_role;

grant select, insert on semantic_atlas.semantic_capture_events to service_role;
grant select, insert on semantic_atlas.semantic_capture_outcomes to service_role;
grant select, insert on semantic_atlas.runtime_snapshots to service_role;
grant select, insert on semantic_atlas.runtime_objects to service_role;
grant select on semantic_atlas.capture_policy to service_role;
grant execute on function semantic_atlas.capture_semantic_event_v1(text,text,jsonb,text,text,text,text,text,text,text,text,text,text) to service_role;
grant execute on function semantic_atlas.activate_runtime_snapshot_v1(uuid) to service_role;
grant execute on function semantic_atlas.mark_runtime_snapshot_failed_v1(uuid,text) to service_role;