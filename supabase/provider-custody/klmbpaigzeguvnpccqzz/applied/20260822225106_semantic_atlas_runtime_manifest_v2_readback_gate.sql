begin;

alter table semantic_atlas.runtime_snapshots
  add column if not exists activation_git_readback_sha text,
  add column if not exists activation_git_readback_at timestamptz,
  add column if not exists activation_git_readback_source text;

alter table semantic_atlas.runtime_snapshots
  alter column manifest_contract set default 'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V2';

alter table semantic_atlas.runtime_snapshots
  drop constraint if exists runtime_snapshots_manifest_contract_check,
  drop constraint if exists semantic_atlas_active_snapshot_git_readback_ck;

alter table semantic_atlas.runtime_snapshots
  add constraint runtime_snapshots_manifest_contract_check
    check (manifest_contract = 'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V2'),
  add constraint semantic_atlas_active_snapshot_git_readback_ck
    check (
      state <> 'ACTIVE'
      or (
        activation_git_readback_sha = git_commit_sha
        and activation_git_readback_at is not null
        and activation_git_readback_source is not null
        and length(activation_git_readback_source) > 0
      )
    );

create or replace function semantic_atlas.frame_utf8_v1(p_value text)
returns text
language sql
immutable
strict
set search_path = pg_catalog
as $$
  select octet_length(convert_to(p_value,'UTF8'))::text || ':' || p_value
$$;

create or replace function semantic_atlas.confirm_runtime_git_readback_v1(
  p_snapshot_id uuid,
  p_git_ref text,
  p_git_readback_sha text,
  p_readback_at timestamptz,
  p_readback_source text
)
returns void
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas
as $$
declare
  v_snapshot semantic_atlas.runtime_snapshots%rowtype;
  v_now timestamptz := clock_timestamp();
begin
  select * into v_snapshot
  from semantic_atlas.runtime_snapshots
  where snapshot_id=p_snapshot_id
  for update;
  if not found then raise exception 'runtime snapshot not found'; end if;
  if v_snapshot.state <> 'LOADING' or v_snapshot.validation_state <> 'UNVERIFIED' then
    raise exception 'Git activation readback requires LOADING/UNVERIFIED snapshot';
  end if;
  if p_git_ref is distinct from v_snapshot.git_ref then
    raise exception 'Git activation readback ref mismatch';
  end if;
  if p_git_readback_sha is distinct from v_snapshot.git_commit_sha then
    raise exception 'Git activation readback SHA mismatch';
  end if;
  if p_readback_at is null or p_readback_at < v_now - interval '5 minutes' or p_readback_at > v_now + interval '1 minute' then
    raise exception 'Git activation readback is stale or implausibly future-dated';
  end if;
  if p_readback_source is null or length(p_readback_source)=0 then
    raise exception 'Git activation readback source required';
  end if;
  perform set_config('semantic_atlas.runtime_mutation','on',true);
  update semantic_atlas.runtime_snapshots
  set activation_git_readback_sha=p_git_readback_sha,
      activation_git_readback_at=p_readback_at,
      activation_git_readback_source=p_readback_source
  where snapshot_id=p_snapshot_id;
end;
$$;

create or replace function semantic_atlas.start_runtime_snapshot_v3(
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
    p_manifest_sha256,p_pathset_sha256,p_snapshot_sha256,p_expected_object_count,'LOADING','UNVERIFIED',p_loader,p_notes,'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V2'
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
     and v_existing.manifest_contract='SEMANTIC_ATLAS_RUNTIME_MANIFEST_V2'
  then return v_existing.snapshot_id; end if;
  raise exception 'snapshot replay identity collision with changed materialization evidence';
end;
$$;

create or replace function semantic_atlas.start_runtime_snapshot_v2(
  p_git_commit_sha text,p_git_ref text,p_git_readback_sha text,p_source_branch text,p_authority_scope text,
  p_materialization_version text,p_manifest_sha256 text,p_pathset_sha256 text,p_snapshot_sha256 text,
  p_expected_object_count integer,p_loader text default 'semantic-atlas-sync',p_notes text default null
)
returns uuid
language sql
security definer
set search_path = pg_catalog, semantic_atlas
as $$
  select semantic_atlas.start_runtime_snapshot_v3(
    p_git_commit_sha,p_git_ref,p_git_readback_sha,p_source_branch,p_authority_scope,p_materialization_version,
    p_manifest_sha256,p_pathset_sha256,p_snapshot_sha256,p_expected_object_count,p_loader,p_notes
  )
$$;

create or replace function semantic_atlas.activate_runtime_snapshot_v3(p_snapshot_id uuid)
returns void
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas, extensions
as $$
declare
  v_snapshot semantic_atlas.runtime_snapshots%rowtype;
  v_count integer;
  v_counts jsonb;
  v_pathset_stream text;
  v_object_stream text;
  v_manifest_stream text;
  v_pathset_sha text;
  v_snapshot_sha text;
  v_manifest_sha text;
  v_now timestamptz := clock_timestamp();
begin
  select * into v_snapshot from semantic_atlas.runtime_snapshots where snapshot_id=p_snapshot_id for update;
  if not found then raise exception 'runtime snapshot not found'; end if;
  if v_snapshot.state<>'LOADING' or v_snapshot.validation_state<>'UNVERIFIED' then raise exception 'runtime snapshot must be LOADING/UNVERIFIED before activation'; end if;
  if v_snapshot.manifest_contract<>'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V2' then raise exception 'unsupported runtime manifest contract'; end if;
  if v_snapshot.activation_git_readback_sha is distinct from v_snapshot.git_commit_sha
     or v_snapshot.activation_git_readback_at is null
     or v_snapshot.activation_git_readback_at < v_now - interval '5 minutes'
     or v_snapshot.activation_git_readback_at > v_now + interval '1 minute'
     or v_snapshot.activation_git_readback_source is null
     or length(v_snapshot.activation_git_readback_source)=0
  then raise exception 'fresh external Git ref readback required immediately before activation'; end if;
  if exists(select 1 from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id and (payload_sha256<>encode(extensions.digest(convert_to(canonical_payload,'UTF8'),'sha256'),'hex') or payload<>canonical_payload::jsonb)) then raise exception 'runtime object canonical payload verification failed'; end if;
  select count(*)::integer into v_count from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id;
  if v_count<>v_snapshot.expected_object_count then raise exception 'runtime object count mismatch: expected %, observed %',v_snapshot.expected_object_count,v_count; end if;
  select coalesce(jsonb_object_agg(object_type,type_count),'{}'::jsonb) into v_counts from (select object_type,count(*)::integer type_count from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id group by object_type) q;
  select coalesce(string_agg(semantic_atlas.frame_utf8_v1(source_path),'' order by source_path),'') into v_pathset_stream
  from (select distinct source_path from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id) s;
  select coalesce(string_agg(
    semantic_atlas.frame_utf8_v1(source_path)
    ||semantic_atlas.frame_utf8_v1(object_id)
    ||semantic_atlas.frame_utf8_v1(object_type)
    ||semantic_atlas.frame_utf8_v1(payload_sha256),
    '' order by source_path,object_id
  ),'') into v_object_stream
  from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id;
  v_pathset_sha:=encode(extensions.digest(convert_to(v_pathset_stream,'UTF8'),'sha256'),'hex');
  v_snapshot_sha:=encode(extensions.digest(convert_to(v_object_stream,'UTF8'),'sha256'),'hex');
  v_manifest_stream:='SEMANTIC_ATLAS_RUNTIME_MANIFEST_V2'
    ||semantic_atlas.frame_utf8_v1(v_snapshot.authority_scope)
    ||semantic_atlas.frame_utf8_v1(v_snapshot.git_commit_sha)
    ||semantic_atlas.frame_utf8_v1(v_snapshot.git_ref)
    ||semantic_atlas.frame_utf8_v1(v_snapshot.source_branch)
    ||semantic_atlas.frame_utf8_v1(v_snapshot.materialization_version)
    ||semantic_atlas.frame_utf8_v1(v_count::text)
    ||semantic_atlas.frame_utf8_v1(v_object_stream);
  v_manifest_sha:=encode(extensions.digest(convert_to(v_manifest_stream,'UTF8'),'sha256'),'hex');
  if v_pathset_sha<>v_snapshot.pathset_sha256 then raise exception 'runtime pathset digest mismatch'; end if;
  if v_snapshot_sha<>v_snapshot.snapshot_sha256 then raise exception 'runtime materialization digest mismatch'; end if;
  if v_manifest_sha<>v_snapshot.manifest_sha256 then raise exception 'runtime reconstructed manifest digest mismatch'; end if;
  perform set_config('semantic_atlas.runtime_mutation','on',true);
  update semantic_atlas.runtime_snapshots set state='SUPERSEDED' where authority_scope=v_snapshot.authority_scope and state='ACTIVE' and snapshot_id<>p_snapshot_id;
  update semantic_atlas.runtime_snapshots set state='ACTIVE',validation_state='VERIFIED',validated_at=clock_timestamp(),object_counts=v_counts where snapshot_id=p_snapshot_id;
end;
$$;

create or replace function semantic_atlas.activate_runtime_snapshot_v2(p_snapshot_id uuid)
returns void language plpgsql security definer set search_path=pg_catalog,semantic_atlas,extensions as $$begin perform semantic_atlas.activate_runtime_snapshot_v3(p_snapshot_id); end;$$;
create or replace function semantic_atlas.activate_runtime_snapshot_v1(p_snapshot_id uuid)
returns void language plpgsql security definer set search_path=pg_catalog,semantic_atlas,extensions as $$begin perform semantic_atlas.activate_runtime_snapshot_v3(p_snapshot_id); end;$$;

grant execute on function semantic_atlas.frame_utf8_v1(text) to service_role;
grant execute on function semantic_atlas.confirm_runtime_git_readback_v1(uuid,text,text,timestamptz,text) to service_role;
grant execute on function semantic_atlas.start_runtime_snapshot_v3(text,text,text,text,text,text,text,text,text,integer,text,text) to service_role;
grant execute on function semantic_atlas.activate_runtime_snapshot_v3(uuid) to service_role;
revoke all on function semantic_atlas.confirm_runtime_git_readback_v1(uuid,text,text,timestamptz,text) from public,anon,authenticated;
revoke all on function semantic_atlas.start_runtime_snapshot_v3(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v3(uuid) from public,anon,authenticated;

commit;