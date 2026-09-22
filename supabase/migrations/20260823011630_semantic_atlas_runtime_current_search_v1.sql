create or replace function semantic_atlas.search_current_runtime_objects_v1(
  p_authority_scope text,
  p_git_repository_locator text,
  p_git_ref text,
  p_git_readback_sha text,
  p_readback_at timestamptz,
  p_readback_source text,
  p_query text,
  p_limit integer default 20
) returns table(
  snapshot_id uuid,
  object_id text,
  object_type text,
  source_path text,
  payload_sha256 text,
  payload jsonb,
  rank real
)
language plpgsql
security definer
set search_path=pg_catalog,semantic_atlas
as $$
declare
  v_query tsquery;
  v_limit integer;
begin
  if p_query is null or length(btrim(p_query))=0 then
    raise exception 'runtime search query required';
  end if;
  v_limit:=least(greatest(coalesce(p_limit,20),1),100);
  v_query:=websearch_to_tsquery('simple',p_query);

  return query
  with current_rows as (
    select * from semantic_atlas.read_current_runtime_objects_v1(
      p_authority_scope,
      p_git_repository_locator,
      p_git_ref,
      p_git_readback_sha,
      p_readback_at,
      p_readback_source
    )
  ), scored as (
    select r.*,
           ts_rank_cd(to_tsvector('simple',coalesce(r.payload::text,'')),v_query)::real as fts_rank
    from current_rows r
    where to_tsvector('simple',coalesce(r.payload::text,'')) @@ v_query
  )
  select s.snapshot_id,s.object_id,s.object_type,s.source_path,s.payload_sha256,s.payload,s.fts_rank
  from scored s
  order by s.fts_rank desc,convert_to(s.object_id,'UTF8')
  limit v_limit;
end;
$$;

revoke all on function semantic_atlas.search_current_runtime_objects_v1(text,text,text,text,timestamptz,text,text,integer) from public,anon,authenticated;
grant execute on function semantic_atlas.search_current_runtime_objects_v1(text,text,text,text,timestamptz,text,text,integer) to service_role;