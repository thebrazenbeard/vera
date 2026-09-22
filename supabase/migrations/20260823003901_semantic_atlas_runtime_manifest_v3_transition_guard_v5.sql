-- Semantic Atlas runtime V5: contract-version correction plus snapshot transition/identity guards.

alter table semantic_atlas.runtime_snapshots
  alter column manifest_contract set default 'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V3';

alter table semantic_atlas.runtime_snapshots
  drop constraint if exists runtime_snapshots_manifest_contract_check;

alter table semantic_atlas.runtime_snapshots
  add constraint runtime_snapshots_manifest_contract_check
  check (manifest_contract='SEMANTIC_ATLAS_RUNTIME_MANIFEST_V3');

create or replace function semantic_atlas.reject_runtime_direct_mutation_v3()
returns trigger
language plpgsql
security definer
set search_path to 'pg_catalog','semantic_atlas'
as $function$
begin
  if current_setting('semantic_atlas.runtime_mutation', true) is distinct from 'on' then
    raise exception 'direct Semantic Atlas runtime mutation is forbidden; use guarded runtime RPCs';
  end if;

  if tg_op='DELETE' then
    raise exception 'runtime snapshots are append-only history and cannot be deleted';
  end if;

  if tg_op='INSERT' then
    if new.state<>'LOADING' or new.validation_state<>'UNVERIFIED' then
      raise exception 'new runtime snapshot attempts must begin LOADING/UNVERIFIED';
    end if;
    if new.sealed_at is not null or new.activated_at is not null
       or new.activation_git_readback_sha is not null
       or new.activation_git_readback_at is not null
       or new.activation_git_readback_source is not null
    then
      raise exception 'new runtime snapshot attempt cannot begin sealed, activated, or externally confirmed';
    end if;
    return new;
  end if;

  if new.snapshot_id is distinct from old.snapshot_id
     or new.authority_scope is distinct from old.authority_scope
     or new.git_commit_sha is distinct from old.git_commit_sha
     or new.git_ref is distinct from old.git_ref
     or new.git_readback_sha is distinct from old.git_readback_sha
     or new.source_branch is distinct from old.source_branch
     or new.materialization_version is distinct from old.materialization_version
     or new.manifest_sha256 is distinct from old.manifest_sha256
     or new.pathset_sha256 is distinct from old.pathset_sha256
     or new.snapshot_sha256 is distinct from old.snapshot_sha256
     or new.expected_object_count is distinct from old.expected_object_count
     or new.manifest_contract is distinct from old.manifest_contract
     or new.attempt_no is distinct from old.attempt_no
     or new.loaded_at is distinct from old.loaded_at
     or new.loader is distinct from old.loader
  then
    raise exception 'runtime snapshot operation/evidence identity is immutable within an attempt';
  end if;

  if new.notes is distinct from old.notes and new.state<>'FAILED' then
    raise exception 'runtime snapshot notes may change only while marking an attempt FAILED';
  end if;

  if old.state='LOADING' then
    if new.state='SEALED' then
      if old.validation_state<>'UNVERIFIED' or new.validation_state<>'VERIFIED'
         or new.sealed_at is null or new.validated_at is null or new.activated_at is not null
         or new.activation_git_readback_sha is not null
         or new.activation_git_readback_at is not null
         or new.activation_git_readback_source is not null
      then raise exception 'illegal LOADING to SEALED transition'; end if;
      return new;
    elsif new.state='FAILED' then
      if new.validation_state<>'FAILED' then raise exception 'FAILED attempt requires FAILED validation state'; end if;
      if new.object_counts is distinct from old.object_counts
         or new.validated_at is distinct from old.validated_at
         or new.sealed_at is distinct from old.sealed_at
         or new.activated_at is distinct from old.activated_at
         or new.activation_git_readback_sha is distinct from old.activation_git_readback_sha
         or new.activation_git_readback_at is distinct from old.activation_git_readback_at
         or new.activation_git_readback_source is distinct from old.activation_git_readback_source
      then raise exception 'LOADING to FAILED may not rewrite verification/readback state'; end if;
      return new;
    else
      raise exception 'illegal runtime snapshot transition from LOADING to %',new.state;
    end if;
  elsif old.state='SEALED' then
    if new.state='SEALED' then
      if new.validation_state<>'VERIFIED'
         or new.object_counts is distinct from old.object_counts
         or new.validated_at is distinct from old.validated_at
         or new.sealed_at is distinct from old.sealed_at
         or new.activated_at is distinct from old.activated_at
      then raise exception 'SEALED snapshot may only update external Git readback fields'; end if;
      return new;
    elsif new.state='ACTIVE' then
      if new.validation_state<>'VERIFIED' or new.activated_at is null
         or new.object_counts is distinct from old.object_counts
         or new.validated_at is distinct from old.validated_at
         or new.sealed_at is distinct from old.sealed_at
         or new.activation_git_readback_sha is distinct from old.activation_git_readback_sha
         or new.activation_git_readback_at is distinct from old.activation_git_readback_at
         or new.activation_git_readback_source is distinct from old.activation_git_readback_source
      then raise exception 'illegal SEALED to ACTIVE transition'; end if;
      return new;
    elsif new.state='FAILED' then
      if new.validation_state<>'FAILED'
         or new.object_counts is distinct from old.object_counts
         or new.validated_at is distinct from old.validated_at
         or new.sealed_at is distinct from old.sealed_at
         or new.activated_at is distinct from old.activated_at
         or new.activation_git_readback_sha is distinct from old.activation_git_readback_sha
         or new.activation_git_readback_at is distinct from old.activation_git_readback_at
         or new.activation_git_readback_source is distinct from old.activation_git_readback_source
      then raise exception 'SEALED to FAILED may not rewrite sealed/readback state'; end if;
      return new;
    else
      raise exception 'illegal runtime snapshot transition from SEALED to %',new.state;
    end if;
  elsif old.state='ACTIVE' then
    if new.state<>'SUPERSEDED' or new.validation_state<>'VERIFIED'
       or new.object_counts is distinct from old.object_counts
       or new.validated_at is distinct from old.validated_at
       or new.sealed_at is distinct from old.sealed_at
       or new.activated_at is distinct from old.activated_at
       or new.activation_git_readback_sha is distinct from old.activation_git_readback_sha
       or new.activation_git_readback_at is distinct from old.activation_git_readback_at
       or new.activation_git_readback_source is distinct from old.activation_git_readback_source
       or new.notes is distinct from old.notes
    then raise exception 'ACTIVE snapshot may only transition immutably to SUPERSEDED'; end if;
    return new;
  else
    raise exception 'runtime snapshot state % is terminal and immutable',old.state;
  end if;
end;
$function$;

create or replace function semantic_atlas.runtime_manifest_stream_v3(
  p_authority_scope text,p_git_commit_sha text,p_git_ref text,p_source_branch text,
  p_materialization_version text,p_object_count integer,p_object_stream text
)
returns text
language sql
immutable
strict
set search_path to 'pg_catalog','semantic_atlas'
as $function$
  select 'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V3'
    || semantic_atlas.frame_utf8_v1(p_authority_scope)
    || semantic_atlas.frame_utf8_v1(p_git_commit_sha)
    || semantic_atlas.frame_utf8_v1(p_git_ref)
    || semantic_atlas.frame_utf8_v1(p_source_branch)
    || semantic_atlas.frame_utf8_v1(p_materialization_version)
    || semantic_atlas.frame_utf8_v1(p_object_count::text)
    || semantic_atlas.frame_utf8_v1(p_object_stream)
$function$;

create or replace function semantic_atlas.start_runtime_snapshot_v5(
  p_git_commit_sha text,p_git_ref text,p_git_readback_sha text,p_source_branch text,p_authority_scope text,
  p_materialization_version text,p_manifest_sha256 text,p_pathset_sha256 text,p_snapshot_sha256 text,
  p_expected_object_count integer,p_loader text default 'semantic-atlas-sync',p_notes text default null
)
returns uuid
language plpgsql
security definer
set search_path to 'pg_catalog','semantic_atlas'
as $function$
declare
  v_existing semantic_atlas.runtime_snapshots%rowtype;
  v_attempt_no integer := 1;
  v_snapshot_id uuid;
begin
  if p_git_commit_sha !~ '^[0-9a-f]{40}$' or p_git_readback_sha is distinct from p_git_commit_sha then raise exception 'snapshot requires exact Git commit readback'; end if;
  if p_git_ref is null or length(p_git_ref)=0 or p_source_branch is null or length(p_source_branch)=0 then raise exception 'snapshot requires Git ref and source branch'; end if;
  if p_authority_scope not in ('CANONICAL_LEDGER','RESEARCH_STAGING') then raise exception 'invalid authority scope'; end if;
  if p_manifest_sha256 !~ '^[0-9a-f]{64}$' or p_pathset_sha256 !~ '^[0-9a-f]{64}$' or p_snapshot_sha256 !~ '^[0-9a-f]{64}$' then raise exception 'snapshot requires exact manifest/pathset/materialization digests'; end if;
  if p_expected_object_count is null or p_expected_object_count<0 then raise exception 'snapshot requires nonnegative expected object count'; end if;

  perform pg_advisory_xact_lock(hashtextextended(p_authority_scope || E'\x1f' || p_git_commit_sha || E'\x1f' || p_materialization_version,0));

  select * into v_existing
  from semantic_atlas.runtime_snapshots
  where authority_scope=p_authority_scope and git_commit_sha=p_git_commit_sha and materialization_version=p_materialization_version
  order by attempt_no desc limit 1 for update;

  if found then
    if v_existing.git_ref is distinct from p_git_ref
       or v_existing.git_readback_sha is distinct from p_git_readback_sha
       or v_existing.source_branch is distinct from p_source_branch
       or v_existing.manifest_sha256 is distinct from p_manifest_sha256
       or v_existing.pathset_sha256 is distinct from p_pathset_sha256
       or v_existing.snapshot_sha256 is distinct from p_snapshot_sha256
       or v_existing.expected_object_count is distinct from p_expected_object_count
       or v_existing.manifest_contract<>'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V3'
    then raise exception 'snapshot logical-operation collision with changed materialization evidence; use a new materialization_version'; end if;
    if v_existing.state<>'FAILED' then return v_existing.snapshot_id; end if;
    v_attempt_no:=v_existing.attempt_no+1;
  end if;

  perform set_config('semantic_atlas.runtime_mutation','on',true);
  insert into semantic_atlas.runtime_snapshots(
    git_commit_sha,git_ref,git_readback_sha,source_branch,authority_scope,materialization_version,
    manifest_sha256,pathset_sha256,snapshot_sha256,expected_object_count,state,validation_state,
    loader,notes,manifest_contract,attempt_no
  ) values (
    p_git_commit_sha,p_git_ref,p_git_readback_sha,p_source_branch,p_authority_scope,p_materialization_version,
    p_manifest_sha256,p_pathset_sha256,p_snapshot_sha256,p_expected_object_count,'LOADING','UNVERIFIED',
    p_loader,p_notes,'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V3',v_attempt_no
  ) returning snapshot_id into v_snapshot_id;
  return v_snapshot_id;
end;
$function$;

create or replace function semantic_atlas.seal_runtime_snapshot_v2(p_snapshot_id uuid)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','semantic_atlas','extensions'
as $function$
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
  v_sealed_at timestamptz;
begin
  select * into v_snapshot from semantic_atlas.runtime_snapshots where snapshot_id=p_snapshot_id for update;
  if not found then raise exception 'runtime snapshot not found'; end if;
  if v_snapshot.state<>'LOADING' or v_snapshot.validation_state<>'UNVERIFIED' then raise exception 'runtime snapshot must be LOADING/UNVERIFIED before sealing'; end if;
  if v_snapshot.manifest_contract<>'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V3' then raise exception 'unsupported runtime manifest contract'; end if;

  if exists(select 1 from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id and (payload_sha256<>encode(extensions.digest(convert_to(canonical_payload,'UTF8'),'sha256'),'hex') or payload<>canonical_payload::jsonb)) then raise exception 'runtime object canonical payload verification failed'; end if;
  select count(*)::integer into v_count from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id;
  if v_count<>v_snapshot.expected_object_count then raise exception 'runtime object count mismatch: expected %, observed %',v_snapshot.expected_object_count,v_count; end if;
  select coalesce(jsonb_object_agg(object_type,type_count),'{}'::jsonb) into v_counts from (select object_type,count(*)::integer type_count from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id group by object_type) q;

  select coalesce(string_agg(semantic_atlas.frame_utf8_v1(source_path),'' order by convert_to(source_path,'UTF8')),'') into v_pathset_stream
  from (select distinct source_path from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id) s;
  select coalesce(string_agg(
    semantic_atlas.frame_utf8_v1(source_path)||semantic_atlas.frame_utf8_v1(object_id)||semantic_atlas.frame_utf8_v1(object_type)||semantic_atlas.frame_utf8_v1(payload_sha256),
    '' order by convert_to(source_path,'UTF8'),convert_to(object_id,'UTF8')
  ),'') into v_object_stream from semantic_atlas.runtime_objects where snapshot_id=p_snapshot_id;

  v_pathset_sha:=encode(extensions.digest(convert_to(v_pathset_stream,'UTF8'),'sha256'),'hex');
  v_snapshot_sha:=encode(extensions.digest(convert_to(v_object_stream,'UTF8'),'sha256'),'hex');
  v_manifest_stream:=semantic_atlas.runtime_manifest_stream_v3(v_snapshot.authority_scope,v_snapshot.git_commit_sha,v_snapshot.git_ref,v_snapshot.source_branch,v_snapshot.materialization_version,v_count,v_object_stream);
  v_manifest_sha:=encode(extensions.digest(convert_to(v_manifest_stream,'UTF8'),'sha256'),'hex');

  if v_pathset_sha<>v_snapshot.pathset_sha256 then raise exception 'runtime pathset digest mismatch'; end if;
  if v_snapshot_sha<>v_snapshot.snapshot_sha256 then raise exception 'runtime materialization digest mismatch'; end if;
  if v_manifest_sha<>v_snapshot.manifest_sha256 then raise exception 'runtime reconstructed manifest digest mismatch'; end if;

  v_sealed_at:=clock_timestamp();
  perform set_config('semantic_atlas.runtime_mutation','on',true);
  update semantic_atlas.runtime_snapshots
  set state='SEALED',validation_state='VERIFIED',validated_at=v_sealed_at,sealed_at=v_sealed_at,object_counts=v_counts,
      activation_git_readback_sha=null,activation_git_readback_at=null,activation_git_readback_source=null
  where snapshot_id=p_snapshot_id;
end;
$function$;

create or replace function semantic_atlas.confirm_runtime_git_readback_v3(
  p_snapshot_id uuid,p_git_ref text,p_git_readback_sha text,p_readback_at timestamptz,p_readback_source text
)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','semantic_atlas'
as $function$
declare
  v_snapshot semantic_atlas.runtime_snapshots%rowtype;
  v_now timestamptz;
begin
  select * into v_snapshot from semantic_atlas.runtime_snapshots where snapshot_id=p_snapshot_id for update;
  if not found then raise exception 'runtime snapshot not found'; end if;
  v_now:=clock_timestamp();
  if v_snapshot.state<>'SEALED' or v_snapshot.validation_state<>'VERIFIED' or v_snapshot.sealed_at is null then raise exception 'Git activation readback requires SEALED/VERIFIED snapshot'; end if;
  if p_git_ref is distinct from v_snapshot.git_ref then raise exception 'Git activation readback ref mismatch'; end if;
  if p_git_readback_sha is distinct from v_snapshot.git_commit_sha then raise exception 'Git activation readback SHA mismatch'; end if;
  if p_readback_at is null or p_readback_at<v_snapshot.sealed_at or p_readback_at<v_now-interval '5 minutes' or p_readback_at>v_now+interval '1 minute' then raise exception 'Git activation readback must be fresh and later than the DB seal'; end if;
  if p_readback_source is null or length(p_readback_source)=0 then raise exception 'Git activation readback source required'; end if;
  perform set_config('semantic_atlas.runtime_mutation','on',true);
  update semantic_atlas.runtime_snapshots
  set activation_git_readback_sha=p_git_readback_sha,activation_git_readback_at=p_readback_at,activation_git_readback_source=p_readback_source
  where snapshot_id=p_snapshot_id;
end;
$function$;

create or replace function semantic_atlas.activate_runtime_snapshot_v5(p_snapshot_id uuid)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','semantic_atlas'
as $function$
declare
  v_snapshot semantic_atlas.runtime_snapshots%rowtype;
  v_now timestamptz;
begin
  select * into v_snapshot from semantic_atlas.runtime_snapshots where snapshot_id=p_snapshot_id for update;
  if not found then raise exception 'runtime snapshot not found'; end if;
  v_now:=clock_timestamp();
  if v_snapshot.state<>'SEALED' or v_snapshot.validation_state<>'VERIFIED' or v_snapshot.sealed_at is null then raise exception 'runtime snapshot must be SEALED/VERIFIED before activation'; end if;
  if v_snapshot.manifest_contract<>'SEMANTIC_ATLAS_RUNTIME_MANIFEST_V3' then raise exception 'unsupported runtime manifest contract'; end if;
  if v_snapshot.activation_git_readback_sha is distinct from v_snapshot.git_commit_sha
     or v_snapshot.activation_git_readback_at is null
     or v_snapshot.activation_git_readback_at<v_snapshot.sealed_at
     or v_snapshot.activation_git_readback_at<v_now-interval '5 minutes'
     or v_snapshot.activation_git_readback_at>v_now+interval '1 minute'
     or v_snapshot.activation_git_readback_source is null
     or length(v_snapshot.activation_git_readback_source)=0
  then raise exception 'fresh external Git ref readback required after seal and immediately before activation'; end if;

  perform set_config('semantic_atlas.runtime_mutation','on',true);
  update semantic_atlas.runtime_snapshots set state='SUPERSEDED' where authority_scope=v_snapshot.authority_scope and state='ACTIVE' and snapshot_id<>p_snapshot_id;
  update semantic_atlas.runtime_snapshots set state='ACTIVE',activated_at=v_now where snapshot_id=p_snapshot_id;
end;
$function$;

create or replace function semantic_atlas.start_runtime_snapshot_v4(
  p_git_commit_sha text,p_git_ref text,p_git_readback_sha text,p_source_branch text,p_authority_scope text,
  p_materialization_version text,p_manifest_sha256 text,p_pathset_sha256 text,p_snapshot_sha256 text,
  p_expected_object_count integer,p_loader text default 'semantic-atlas-sync',p_notes text default null
)
returns uuid language sql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ select semantic_atlas.start_runtime_snapshot_v5(p_git_commit_sha,p_git_ref,p_git_readback_sha,p_source_branch,p_authority_scope,p_materialization_version,p_manifest_sha256,p_pathset_sha256,p_snapshot_sha256,p_expected_object_count,p_loader,p_notes) $function$;

create or replace function semantic_atlas.start_runtime_snapshot_v3(
  p_git_commit_sha text,p_git_ref text,p_git_readback_sha text,p_source_branch text,p_authority_scope text,
  p_materialization_version text,p_manifest_sha256 text,p_pathset_sha256 text,p_snapshot_sha256 text,
  p_expected_object_count integer,p_loader text default 'semantic-atlas-sync',p_notes text default null
)
returns uuid language sql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ select semantic_atlas.start_runtime_snapshot_v5(p_git_commit_sha,p_git_ref,p_git_readback_sha,p_source_branch,p_authority_scope,p_materialization_version,p_manifest_sha256,p_pathset_sha256,p_snapshot_sha256,p_expected_object_count,p_loader,p_notes) $function$;

create or replace function semantic_atlas.start_runtime_snapshot_v2(
  p_git_commit_sha text,p_git_ref text,p_git_readback_sha text,p_source_branch text,p_authority_scope text,
  p_materialization_version text,p_manifest_sha256 text,p_pathset_sha256 text,p_snapshot_sha256 text,
  p_expected_object_count integer,p_loader text default 'semantic-atlas-sync',p_notes text default null
)
returns uuid language sql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ select semantic_atlas.start_runtime_snapshot_v5(p_git_commit_sha,p_git_ref,p_git_readback_sha,p_source_branch,p_authority_scope,p_materialization_version,p_manifest_sha256,p_pathset_sha256,p_snapshot_sha256,p_expected_object_count,p_loader,p_notes) $function$;

create or replace function semantic_atlas.seal_runtime_snapshot_v1(p_snapshot_id uuid)
returns void language plpgsql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ begin perform semantic_atlas.seal_runtime_snapshot_v2(p_snapshot_id); end; $function$;

create or replace function semantic_atlas.confirm_runtime_git_readback_v2(
  p_snapshot_id uuid,p_git_ref text,p_git_readback_sha text,p_readback_at timestamptz,p_readback_source text
)
returns void language plpgsql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ begin perform semantic_atlas.confirm_runtime_git_readback_v3(p_snapshot_id,p_git_ref,p_git_readback_sha,p_readback_at,p_readback_source); end; $function$;

create or replace function semantic_atlas.confirm_runtime_git_readback_v1(
  p_snapshot_id uuid,p_git_ref text,p_git_readback_sha text,p_readback_at timestamptz,p_readback_source text
)
returns void language plpgsql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ begin perform semantic_atlas.confirm_runtime_git_readback_v3(p_snapshot_id,p_git_ref,p_git_readback_sha,p_readback_at,p_readback_source); end; $function$;

create or replace function semantic_atlas.activate_runtime_snapshot_v4(p_snapshot_id uuid)
returns void language plpgsql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ begin perform semantic_atlas.activate_runtime_snapshot_v5(p_snapshot_id); end; $function$;
create or replace function semantic_atlas.activate_runtime_snapshot_v3(p_snapshot_id uuid)
returns void language plpgsql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ begin perform semantic_atlas.activate_runtime_snapshot_v5(p_snapshot_id); end; $function$;
create or replace function semantic_atlas.activate_runtime_snapshot_v2(p_snapshot_id uuid)
returns void language plpgsql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ begin perform semantic_atlas.activate_runtime_snapshot_v5(p_snapshot_id); end; $function$;
create or replace function semantic_atlas.activate_runtime_snapshot_v1(p_snapshot_id uuid)
returns void language plpgsql security definer set search_path to 'pg_catalog','semantic_atlas'
as $function$ begin perform semantic_atlas.activate_runtime_snapshot_v5(p_snapshot_id); end; $function$;

revoke all on function semantic_atlas.runtime_manifest_stream_v3(text,text,text,text,text,integer,text) from public,anon,authenticated;
revoke all on function semantic_atlas.start_runtime_snapshot_v5(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.seal_runtime_snapshot_v2(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.confirm_runtime_git_readback_v3(uuid,text,text,timestamptz,text) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v5(uuid) from public,anon,authenticated;
grant execute on function semantic_atlas.runtime_manifest_stream_v3(text,text,text,text,text,integer,text) to service_role;
grant execute on function semantic_atlas.start_runtime_snapshot_v5(text,text,text,text,text,text,text,text,text,integer,text,text) to service_role;
grant execute on function semantic_atlas.seal_runtime_snapshot_v2(uuid) to service_role;
grant execute on function semantic_atlas.confirm_runtime_git_readback_v3(uuid,text,text,timestamptz,text) to service_role;
grant execute on function semantic_atlas.activate_runtime_snapshot_v5(uuid) to service_role;

revoke all on function semantic_atlas.start_runtime_snapshot_v4(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.start_runtime_snapshot_v3(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.start_runtime_snapshot_v2(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.seal_runtime_snapshot_v1(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.confirm_runtime_git_readback_v2(uuid,text,text,timestamptz,text) from public,anon,authenticated;
revoke all on function semantic_atlas.confirm_runtime_git_readback_v1(uuid,text,text,timestamptz,text) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v4(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v3(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v2(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v1(uuid) from public,anon,authenticated;
grant execute on function semantic_atlas.start_runtime_snapshot_v4(text,text,text,text,text,text,text,text,text,integer,text,text) to service_role;
grant execute on function semantic_atlas.start_runtime_snapshot_v3(text,text,text,text,text,text,text,text,text,integer,text,text) to service_role;
grant execute on function semantic_atlas.start_runtime_snapshot_v2(text,text,text,text,text,text,text,text,text,integer,text,text) to service_role;
grant execute on function semantic_atlas.seal_runtime_snapshot_v1(uuid) to service_role;
grant execute on function semantic_atlas.confirm_runtime_git_readback_v2(uuid,text,text,timestamptz,text) to service_role;
grant execute on function semantic_atlas.confirm_runtime_git_readback_v1(uuid,text,text,timestamptz,text) to service_role;
grant execute on function semantic_atlas.activate_runtime_snapshot_v4(uuid) to service_role;
grant execute on function semantic_atlas.activate_runtime_snapshot_v3(uuid) to service_role;
grant execute on function semantic_atlas.activate_runtime_snapshot_v2(uuid) to service_role;
grant execute on function semantic_atlas.activate_runtime_snapshot_v1(uuid) to service_role;