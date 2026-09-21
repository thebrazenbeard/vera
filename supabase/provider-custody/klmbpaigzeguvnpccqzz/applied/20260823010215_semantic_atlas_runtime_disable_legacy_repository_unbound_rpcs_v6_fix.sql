create or replace function semantic_atlas.confirm_runtime_git_readback_v3(
  p_snapshot_id uuid,
  p_git_ref text,
  p_git_readback_sha text,
  p_readback_at timestamptz,
  p_readback_source text
) returns void
language plpgsql security definer
set search_path=pg_catalog,semantic_atlas
as $$
declare
  v_snapshot semantic_atlas.runtime_snapshots%rowtype;
  v_now timestamptz;
begin
  select * into v_snapshot from semantic_atlas.runtime_snapshots where snapshot_id=p_snapshot_id for update;
  if not found then raise exception 'runtime snapshot not found'; end if;
  if v_snapshot.manifest_contract='SEMANTIC_ATLAS_RUNTIME_MANIFEST_V4' then
    raise exception 'legacy repository-unbound Git readback is disabled for Manifest V4; use confirm_runtime_git_readback_v4';
  end if;
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
$$;

revoke execute on function semantic_atlas.start_runtime_snapshot_v2(text,text,text,text,text,text,text,text,text,integer,text,text) from service_role;
revoke execute on function semantic_atlas.start_runtime_snapshot_v3(text,text,text,text,text,text,text,text,text,integer,text,text) from service_role;
revoke execute on function semantic_atlas.start_runtime_snapshot_v4(text,text,text,text,text,text,text,text,text,integer,text,text) from service_role;
revoke execute on function semantic_atlas.start_runtime_snapshot_v5(text,text,text,text,text,text,text,text,text,integer,text,text) from service_role;
revoke execute on function semantic_atlas.seal_runtime_snapshot_v1(uuid) from service_role;
revoke execute on function semantic_atlas.seal_runtime_snapshot_v2(uuid) from service_role;
revoke execute on function semantic_atlas.confirm_runtime_git_readback_v1(uuid,text,text,timestamptz,text) from service_role;
revoke execute on function semantic_atlas.confirm_runtime_git_readback_v2(uuid,text,text,timestamptz,text) from service_role;
revoke execute on function semantic_atlas.confirm_runtime_git_readback_v3(uuid,text,text,timestamptz,text) from service_role;
revoke execute on function semantic_atlas.activate_runtime_snapshot_v1(uuid) from service_role;
revoke execute on function semantic_atlas.activate_runtime_snapshot_v2(uuid) from service_role;
revoke execute on function semantic_atlas.activate_runtime_snapshot_v3(uuid) from service_role;
revoke execute on function semantic_atlas.activate_runtime_snapshot_v4(uuid) from service_role;
revoke execute on function semantic_atlas.activate_runtime_snapshot_v5(uuid) from service_role;

revoke all on function semantic_atlas.start_runtime_snapshot_v2(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.start_runtime_snapshot_v3(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.start_runtime_snapshot_v4(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.start_runtime_snapshot_v5(text,text,text,text,text,text,text,text,text,integer,text,text) from public,anon,authenticated;
revoke all on function semantic_atlas.seal_runtime_snapshot_v1(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.seal_runtime_snapshot_v2(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.confirm_runtime_git_readback_v1(uuid,text,text,timestamptz,text) from public,anon,authenticated;
revoke all on function semantic_atlas.confirm_runtime_git_readback_v2(uuid,text,text,timestamptz,text) from public,anon,authenticated;
revoke all on function semantic_atlas.confirm_runtime_git_readback_v3(uuid,text,text,timestamptz,text) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v1(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v2(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v3(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v4(uuid) from public,anon,authenticated;
revoke all on function semantic_atlas.activate_runtime_snapshot_v5(uuid) from public,anon,authenticated;