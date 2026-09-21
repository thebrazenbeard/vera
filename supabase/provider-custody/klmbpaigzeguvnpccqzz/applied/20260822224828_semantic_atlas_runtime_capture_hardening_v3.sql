begin;

alter table semantic_atlas.semantic_capture_outcomes
  add column if not exists git_authority_scope text,
  add column if not exists git_ref text,
  add column if not exists git_readback_sha text;

alter table semantic_atlas.semantic_capture_outcomes
  drop constraint if exists semantic_capture_outcomes_git_scope_check,
  drop constraint if exists semantic_capture_outcomes_git_confirmation_binding_ck;

alter table semantic_atlas.semantic_capture_outcomes
  add constraint semantic_capture_outcomes_git_scope_check
    check (git_authority_scope is null or git_authority_scope in ('CANONICAL_LEDGER','RESEARCH_STAGING')),
  add constraint semantic_capture_outcomes_git_confirmation_binding_ck
    check (
      action <> 'GIT_WRITE_CONFIRMED'
      or (
        git_commit_sha is not null
        and git_commit_sha ~ '^[0-9a-f]{40}$'
        and git_authority_scope in ('CANONICAL_LEDGER','RESEARCH_STAGING')
        and git_ref is not null and length(git_ref) > 0
        and git_readback_sha = git_commit_sha
        and jsonb_typeof(git_object_refs) = 'array'
        and jsonb_array_length(git_object_refs) > 0
      )
    ) not valid;

alter table semantic_atlas.runtime_snapshots
  add column if not exists git_ref text,
  add column if not exists git_readback_sha text,
  add column if not exists manifest_contract text not null default 'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V1';

update semantic_atlas.runtime_snapshots
set git_ref = coalesce(git_ref, source_branch),
    git_readback_sha = coalesce(git_readback_sha, git_commit_sha)
where git_ref is null or git_readback_sha is null;

alter table semantic_atlas.runtime_snapshots
  alter column git_ref set not null,
  alter column git_readback_sha set not null;

alter table semantic_atlas.runtime_snapshots
  drop constraint if exists runtime_snapshots_git_commit_sha_key,
  drop constraint if exists runtime_snapshots_git_readback_sha_check,
  drop constraint if exists runtime_snapshots_manifest_contract_check;

alter table semantic_atlas.runtime_snapshots
  add constraint runtime_snapshots_git_readback_sha_check
    check (git_readback_sha ~ '^[0-9a-f]{40}$' and git_readback_sha = git_commit_sha),
  add constraint runtime_snapshots_manifest_contract_check
    check (manifest_contract = 'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V1');

create unique index if not exists semantic_atlas_runtime_snapshot_operation_uq
  on semantic_atlas.runtime_snapshots(authority_scope, git_commit_sha, materialization_version);

alter table semantic_atlas.runtime_objects
  add column if not exists canonical_payload text;

update semantic_atlas.runtime_objects
set canonical_payload = payload::text
where canonical_payload is null;

alter table semantic_atlas.runtime_objects
  alter column canonical_payload set not null;

create or replace function semantic_atlas.reject_runtime_direct_mutation_v3()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas
as $$
begin
  if current_setting('semantic_atlas.runtime_mutation', true) is distinct from 'on' then
    raise exception 'direct Semantic Atlas runtime mutation is forbidden; use guarded runtime RPCs';
  end if;
  if tg_op = 'DELETE' then return old; end if;
  return new;
end;
$$;

create or replace function semantic_atlas.validate_runtime_object_payload_v3()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas, extensions
as $$
declare
  v_payload jsonb;
  v_sha text;
begin
  if current_setting('semantic_atlas.runtime_mutation', true) is distinct from 'on' then
    raise exception 'direct Semantic Atlas runtime object mutation is forbidden; use guarded runtime RPCs';
  end if;
  begin
    v_payload := new.canonical_payload::jsonb;
  exception when others then
    raise exception 'canonical_payload is not valid JSON';
  end;
  v_sha := encode(extensions.digest(convert_to(new.canonical_payload, 'UTF8'), 'sha256'), 'hex');
  if new.payload is distinct from v_payload then
    raise exception 'runtime object payload does not match canonical_payload JSON';
  end if;
  if new.payload_sha256 is distinct from v_sha then
    raise exception 'runtime object payload_sha256 does not match canonical_payload bytes';
  end if;
  return new;
end;
$$;

drop trigger if exists semantic_atlas_runtime_snapshot_guard_v3 on semantic_atlas.runtime_snapshots;
create trigger semantic_atlas_runtime_snapshot_guard_v3
before insert or update or delete on semantic_atlas.runtime_snapshots
for each row execute function semantic_atlas.reject_runtime_direct_mutation_v3();

drop trigger if exists semantic_atlas_runtime_object_guard_v3 on semantic_atlas.runtime_objects;
create trigger semantic_atlas_runtime_object_guard_v3
before insert or update or delete on semantic_atlas.runtime_objects
for each row execute function semantic_atlas.validate_runtime_object_payload_v3();

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
)
returns uuid
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
  select * into v_policy from semantic_atlas.capture_policy where policy_key='default' and enabled=true;
  if not found or not v_policy.auto_candidate_write then raise exception 'semantic capture policy disabled'; end if;
  if p_salience not in ('MEDIUM','HIGH') then raise exception 'semantic capture requires MEDIUM or HIGH salience'; end if;
  if v_policy.minimum_auto_salience='HIGH' and p_salience<>'HIGH' then raise exception 'semantic capture below active minimum salience'; end if;
  if not (p_trigger_class=any(v_policy.trigger_classes)) then raise exception 'trigger class not permitted by active capture policy'; end if;

  insert into semantic_atlas.semantic_capture_events(
    idempotency_key,source_surface,source_locator,source_actor,trigger_class,salience,
    semantic_key,candidate_kind,representation,representation_fidelity,privacy_scope,evidence_ceiling,notes
  ) values (
    p_idempotency_key,p_source_surface,v_locator,p_source_actor,p_trigger_class,p_salience,
    p_semantic_key,p_candidate_kind,p_representation,p_representation_fidelity,p_privacy_scope,p_evidence_ceiling,p_notes
  ) on conflict(idempotency_key) do nothing returning event_id into v_event_id;
  if v_event_id is not null then return v_event_id; end if;

  select * into v_existing from semantic_atlas.semantic_capture_events where idempotency_key=p_idempotency_key;
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
  then return v_existing.event_id; end if;
  raise exception 'idempotency key collision with changed immutable semantic capture payload';
end;
$$;

create or replace function semantic_atlas.record_semantic_capture_outcome_v2(
  p_event_id uuid,
  p_action text,
  p_semantic_decider text,
  p_decision_payload jsonb default '{}'::jsonb,
  p_git_commit_sha text default null,
  p_git_object_refs jsonb default '[]'::jsonb,
  p_git_authority_scope text default null,
  p_git_ref text default null,
  p_git_readback_sha text default null,
  p_notes text default null
)
returns uuid
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas
as $$
declare v_outcome_id uuid;
begin
  if not exists(select 1 from semantic_atlas.semantic_capture_events where event_id=p_event_id) then raise exception 'semantic capture event not found'; end if;
  if p_action='GIT_WRITE_CONFIRMED' then
    if p_git_commit_sha is null or p_git_commit_sha !~ '^[0-9a-f]{40}$'
       or p_git_authority_scope not in ('CANONICAL_LEDGER','RESEARCH_STAGING')
       or p_git_ref is null or length(p_git_ref)=0
       or p_git_readback_sha is distinct from p_git_commit_sha
       or jsonb_typeof(coalesce(p_git_object_refs,'[]'::jsonb))<>'array'
       or jsonb_array_length(coalesce(p_git_object_refs,'[]'::jsonb))=0
    then raise exception 'GIT_WRITE_CONFIRMED requires exact commit, scope, ref, matching readback SHA, and object refs'; end if;
  end if;
  insert into semantic_atlas.semantic_capture_outcomes(
    event_id,action,semantic_decider,decision_payload,git_commit_sha,git_object_refs,
    git_authority_scope,git_ref,git_readback_sha,notes
  ) values (
    p_event_id,p_action,p_semantic_decider,coalesce(p_decision_payload,'{}'::jsonb),p_git_commit_sha,
    coalesce(p_git_object_refs,'[]'::jsonb),p_git_authority_scope,p_git_ref,p_git_readback_sha,p_notes
  ) returning outcome_id into v_outcome_id;
  return v_outcome_id;
end;
$$;

create or replace function semantic_atlas.start_runtime_snapshot_v2(
  p_git_commit_sha text,
  p_git_ref text,
  p_git_readback_sha text,
  p_source_branch text,
  p_authority_scope text,
  p_materialization_version text,
  p_manifest_sha256 text,
  p_pathset_sha256 text,
  p_snapshot_sha256 text,
  p_expected_object_count integer,
  p_loader text default 'semantic-atlas-sync',
  p_notes text default null
)
returns uuid
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas
as $$
declare
  v_snapshot_id uuid;
  v_existing semantic_atlas.runtime_snapshots%rowtype;
begin
  if p_git_commit_sha !~ '^[0-9a-f]{40}$' or p_git_readback_sha is distinct from p_git_commit_sha then raise exception 'snapshot requires exact Git commit readback'; end if;
  if p_git_ref is null or length(p_git_ref)=0 or p_source_branch is null or length(p_source_branch)=0 then raise exception 'snapshot requires Git ref and source branch'; end if;
  if p_authority_scope not in ('CANONICAL_LEDGER','RESEARCH_STAGING') then raise exception 'invalid authority scope'; end if;
  if p_manifest_sha256 !~ '^[0-9a-f]{64}$' or p_pathset_sha256 !~ '^[0-9a-f]{64}$' or p_snapshot_sha256 !~ '^[0-9a-f]{64}$' then raise exception 'snapshot requires exact manifest/pathset/materialization digests'; end if;
  if p_expected_object_count is null or p_expected_object_count<0 then raise exception 'snapshot requires nonnegative expected object count'; end if;

  perform set_config('semantic_atlas.runtime_mutation','on',true);
  insert into semantic_atlas.runtime_snapshots(
    git_commit_sha,git_ref,git_readback_sha,source_branch,authority_scope,materialization_version,
    manifest_sha256,pathset_sha256,snapshot_sha256,expected_object_count,state,validation_state,loader,notes,manifest_contract
  ) values (
    p_git_commit_sha,p_git_ref,p_git_readback_sha,p_source_branch,p_authority_scope,p_materialization_version,
    p_manifest_sha256,p_pathset_sha256,p_snapshot_sha256,p_expected_object_count,'LOADING','UNVERIFIED',p_loader,p_notes,'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V1'
  ) on conflict(authority_scope,git_commit_sha,materialization_version) do nothing returning snapshot_id into v_snapshot_id;
  if v_snapshot_id is not null then return v_snapshot_id; end if;

  select * into v_existing from semantic_atlas.runtime_snapshots
  where authority_scope=p_authority_scope and git_commit_sha=p_git_commit_sha and materialization_version=p_materialization_version;
  if v_existing.git_ref is not distinct from p_git_ref
     and v_existing.git_readback_sha is not distinct from p_git_readback_sha
     and v_existing.source_branch is not distinct from p_source_branch
     and v_existing.manifest_sha256 is not distinct from p_manifest_sha256
     and v_existing.pathset_sha256 is not distinct from p_pathset_sha256
     and v_existing.snapshot_sha256 is not distinct from p_snapshot_sha256
     and v_existing.expected_object_count is not distinct from p_expected_object_count
  then return v_existing.snapshot_id; end if;
  raise exception 'snapshot replay identity collision with changed materialization evidence';
end;
$$;

create or replace function semantic_atlas.append_runtime_object_v2(
  p_snapshot_id uuid,p_object_id text,p_object_type text,p_source_path text,p_canonical_payload text
)
returns text
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas, extensions
as $$
declare
  v_snapshot semantic_atlas.runtime_snapshots%rowtype;
  v_payload jsonb;
  v_sha text;
  v_existing semantic_atlas.runtime_objects%rowtype;
begin
  select * into v_snapshot from semantic_atlas.runtime_snapshots where snapshot_id=p_snapshot_id for update;
  if not found then raise exception 'runtime snapshot not found'; end if;
  if v_snapshot.state<>'LOADING' or v_snapshot.validation_state<>'UNVERIFIED' then raise exception 'runtime object append requires LOADING/UNVERIFIED snapshot'; end if;
  if p_object_id is null or length(p_object_id)=0 or p_object_type is null or length(p_object_type)=0 or p_source_path is null or length(p_source_path)=0 then raise exception 'runtime object identity/type/source path required'; end if;
  begin v_payload:=p_canonical_payload::jsonb; exception when others then raise exception 'canonical runtime payload is not valid JSON'; end;
  v_sha:=encode(extensions.digest(convert_to(p_canonical_payload,'UTF8'),'sha256'),'hex');
  perform set_config('semantic_atlas.runtime_mutation','on',true);
  insert into semantic_atlas.runtime_objects(snapshot_id,object_id,object_type,source_path,payload_sha256,payload,canonical_payload)
  values(p_snapshot_id,p_object_id,p_object_type,p_source_path,v_sha,v_payload,p_canonical_payload)
  on conflict(snapshot_id,object_id) do nothing;
  select * into v_existing from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id and object_id=p_object_id;
  if v_existing.object_type is not distinct from p_object_type
     and v_existing.source_path is not distinct from p_source_path
     and v_existing.canonical_payload is not distinct from p_canonical_payload
     and v_existing.payload_sha256 is not distinct from v_sha
  then return v_sha; end if;
  raise exception 'runtime object replay collision with changed immutable payload';
end;
$$;

create or replace function semantic_atlas.activate_runtime_snapshot_v2(p_snapshot_id uuid)
returns void
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas, extensions
as $$
declare
  v_snapshot semantic_atlas.runtime_snapshots%rowtype;
  v_count integer;
  v_counts jsonb;
  v_pathset_text text;
  v_object_lines text;
  v_manifest_text text;
  v_pathset_sha text;
  v_snapshot_sha text;
  v_manifest_sha text;
begin
  select * into v_snapshot from semantic_atlas.runtime_snapshots where snapshot_id=p_snapshot_id for update;
  if not found then raise exception 'runtime snapshot not found'; end if;
  if v_snapshot.state<>'LOADING' or v_snapshot.validation_state<>'UNVERIFIED' then raise exception 'runtime snapshot must be LOADING/UNVERIFIED before activation'; end if;
  if v_snapshot.git_readback_sha is distinct from v_snapshot.git_commit_sha then raise exception 'runtime snapshot Git readback no longer matches commit'; end if;
  if exists(select 1 from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id and (payload_sha256<>encode(extensions.digest(convert_to(canonical_payload,'UTF8'),'sha256'),'hex') or payload<>canonical_payload::jsonb)) then raise exception 'runtime object canonical payload verification failed'; end if;
  select count(*)::integer into v_count from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id;
  if v_count<>v_snapshot.expected_object_count then raise exception 'runtime object count mismatch: expected %, observed %',v_snapshot.expected_object_count,v_count; end if;
  select coalesce(jsonb_object_agg(object_type,type_count),'{}'::jsonb) into v_counts from (select object_type,count(*)::integer type_count from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id group by object_type) q;
  select coalesce(string_agg(distinct source_path,E'\n' order by source_path),'') into v_pathset_text from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id;
  select coalesce(string_agg(source_path||E'\t'||object_id||E'\t'||object_type||E'\t'||payload_sha256,E'\n' order by source_path,object_id),'') into v_object_lines from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id;
  v_pathset_sha:=encode(extensions.digest(convert_to(v_pathset_text,'UTF8'),'sha256'),'hex');
  v_snapshot_sha:=encode(extensions.digest(convert_to(v_object_lines,'UTF8'),'sha256'),'hex');
  v_manifest_text:='SEMANTIC_ATLAS_RUNTIME_MANIFEST_V1'||E'\n'
    ||'authority_scope='||v_snapshot.authority_scope||E'\n'
    ||'git_commit_sha='||v_snapshot.git_commit_sha||E'\n'
    ||'git_ref='||v_snapshot.git_ref||E'\n'
    ||'source_branch='||v_snapshot.source_branch||E'\n'
    ||'materialization_version='||v_snapshot.materialization_version||E'\n'
    ||'object_count='||v_count::text||E'\n'
    ||'objects:'||E'\n'||v_object_lines;
  v_manifest_sha:=encode(extensions.digest(convert_to(v_manifest_text,'UTF8'),'sha256'),'hex');
  if v_pathset_sha<>v_snapshot.pathset_sha256 then raise exception 'runtime pathset digest mismatch'; end if;
  if v_snapshot_sha<>v_snapshot.snapshot_sha256 then raise exception 'runtime materialization digest mismatch'; end if;
  if v_manifest_sha<>v_snapshot.manifest_sha256 then raise exception 'runtime reconstructed manifest digest mismatch'; end if;
  perform set_config('semantic_atlas.runtime_mutation','on',true);
  update semantic_atlas.runtime_snapshots set state='SUPERSEDED' where authority_scope=v_snapshot.authority_scope and state='ACTIVE' and snapshot_id<>p_snapshot_id;
  update semantic_atlas.runtime_snapshots set state='ACTIVE',validation_state='VERIFIED',validated_at=clock_timestamp(),object_counts=v_counts where snapshot_id=p_snapshot_id;
end;
$$;

create or replace function semantic_atlas.activate_runtime_snapshot_v1(p_snapshot_id uuid)
returns void language plpgsql security definer set search_path=pg_catalog,semantic_atlas,extensions as $$begin perform semantic_atlas.activate_runtime_snapshot_v2(p_snapshot_id); end;$$;

create or replace function semantic_atlas.mark_runtime_snapshot_failed_v1(p_snapshot_id uuid,p_notes text)
returns void language plpgsql security definer set search_path=pg_catalog,semantic_atlas as $$
begin
  if exists(select 1 from semantic_atlas.runtime_snapshots where snapshot_id=p_snapshot_id and state='ACTIVE') then raise exception 'cannot mark active runtime snapshot failed'; end if;
  perform set_config('semantic_atlas.runtime_mutation','on',true);
  update semantic_atlas.runtime_snapshots set state='FAILED',validation_state='FAILED',notes=coalesce(p_notes,notes) where snapshot_id=p_snapshot_id and state='LOADING';
  if not found then raise exception 'LOADING runtime snapshot not found'; end if;
end;$$;

revoke insert,update,delete,truncate on semantic_atlas.runtime_snapshots from service_role;
revoke insert,update,delete,truncate on semantic_atlas.runtime_objects from service_role;
revoke insert,update,delete,truncate on semantic_atlas.semantic_capture_events from service_role;
revoke insert,update,delete,truncate on semantic_atlas.semantic_capture_outcomes from service_role;
revoke insert,update,delete on semantic_atlas.active_runtime_objects from service_role;
revoke insert,update,delete on semantic_atlas.canonical_runtime_objects from service_role;
revoke insert,update,delete on semantic_atlas.research_runtime_objects from service_role;

grant usage on schema semantic_atlas to service_role;
grant select on semantic_atlas.runtime_snapshots,semantic_atlas.runtime_objects,semantic_atlas.semantic_capture_events,semantic_atlas.semantic_capture_outcomes,semantic_atlas.capture_policy to service_role;
grant select on semantic_atlas.active_runtime_objects,semantic_atlas.canonical_runtime_objects,semantic_atlas.research_runtime_objects to service_role;
grant execute on function semantic_atlas.capture_semantic_event_v1(text,text,jsonb,text,text,text,text,text,text,text,text,text,text) to service_role;
grant execute on function semantic_atlas.record_semantic_capture_outcome_v2(uuid,text,text,jsonb,text,jsonb,text,text,text,text) to service_role;
grant execute on function semantic_atlas.start_runtime_snapshot_v2(text,text,text,text,text,text,text,text,text,integer,text,text) to service_role;
grant execute on function semantic_atlas.append_runtime_object_v2(uuid,text,text,text,text) to service_role;
grant execute on function semantic_atlas.activate_runtime_snapshot_v2(uuid) to service_role;
grant execute on function semantic_atlas.activate_runtime_snapshot_v1(uuid) to service_role;
grant execute on function semantic_atlas.mark_runtime_snapshot_failed_v1(uuid,text) to service_role;

revoke all on function semantic_atlas.record_semantic_capture_outcome_v2(uuid,text,text,jsonb,text,jsonb,text,text,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.start_runtime_snapshot_v2(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.append_runtime_object_v2(uuid,text,text,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v2(uuid) from public,anon,authenticated;

commit;