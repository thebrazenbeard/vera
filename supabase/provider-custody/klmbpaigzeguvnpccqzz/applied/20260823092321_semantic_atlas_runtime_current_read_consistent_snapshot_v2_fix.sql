create or replace function semantic_atlas.read_current_runtime_objects_v1(
  p_authority_scope text,
  p_git_repository_locator text,
  p_git_ref text,
  p_git_readback_sha text,
  p_readback_at timestamptz,
  p_readback_source text
)
returns setof semantic_atlas.active_runtime_objects
language plpgsql
stable
security definer
set search_path = pg_catalog, semantic_atlas
as $$
declare
  v_snapshot semantic_atlas.runtime_snapshots%rowtype;
  v_now timestamptz;
begin
  if p_authority_scope not in ('CANONICAL_LEDGER','RESEARCH_STAGING') then
    raise exception 'invalid runtime authority scope';
  end if;
  if p_git_repository_locator is null or length(p_git_repository_locator)=0
     or p_git_ref is null or length(p_git_ref)=0
     or p_git_readback_sha !~ '^[0-9a-f]{40}$'
  then
    raise exception 'current runtime read requires exact repository/ref/SHA readback';
  end if;
  if p_readback_source is null or length(p_readback_source)=0 then
    raise exception 'current runtime readback source required';
  end if;

  v_now:=statement_timestamp();
  if p_readback_at is null
     or p_readback_at<v_now-interval '60 seconds'
     or p_readback_at>v_now+interval '1 minute'
  then
    raise exception 'current runtime read requires provider readback within 60 seconds';
  end if;

  select * into v_snapshot
  from semantic_atlas.runtime_snapshots
  where authority_scope=p_authority_scope and state='ACTIVE';
  if not found then raise exception 'no active runtime snapshot for scope'; end if;

  if v_snapshot.git_repository_locator is distinct from p_git_repository_locator then
    raise exception 'active runtime repository does not match current provider readback';
  end if;
  if v_snapshot.git_ref is distinct from p_git_ref then
    raise exception 'active runtime ref does not match current provider readback';
  end if;
  if v_snapshot.git_commit_sha is distinct from p_git_readback_sha then
    raise exception 'active runtime snapshot is stale relative to current provider ref';
  end if;
  if p_readback_at<v_snapshot.activated_at then
    raise exception 'current provider readback predates runtime activation';
  end if;

  return query
  select *
  from semantic_atlas.active_runtime_objects
  where snapshot_id=v_snapshot.snapshot_id;
end;
$$;

revoke all on function semantic_atlas.read_current_runtime_objects_v1(text,text,text,text,timestamptz,text) from public, anon, authenticated;
grant execute on function semantic_atlas.read_current_runtime_objects_v1(text,text,text,text,timestamptz,text) to service_role;