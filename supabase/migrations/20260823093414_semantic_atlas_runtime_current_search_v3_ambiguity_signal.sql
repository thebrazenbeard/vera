create or replace function semantic_atlas.search_current_runtime_objects_v3(
  p_authority_scope text,
  p_git_repository_locator text,
  p_git_ref text,
  p_git_readback_sha text,
  p_readback_at timestamptz,
  p_readback_source text,
  p_query text,
  p_limit integer default 20
)
returns table(
  snapshot_id uuid,
  object_id text,
  object_type text,
  source_path text,
  payload_sha256 text,
  payload jsonb,
  rank real,
  match_mode text,
  query_coverage real,
  retrieval_state text,
  candidate_count integer,
  top_coverage_tie_count integer
)
language sql
stable
security definer
set search_path = pg_catalog, semantic_atlas
as $$
  with candidates as materialized (
    select *
    from semantic_atlas.search_current_runtime_objects_v2(
      p_authority_scope,
      p_git_repository_locator,
      p_git_ref,
      p_git_readback_sha,
      p_readback_at,
      p_readback_source,
      p_query,
      p_limit
    )
  ), stats as (
    select
      count(*)::integer as candidate_count,
      max(query_coverage) as top_coverage,
      count(*) filter (where query_coverage=(select max(query_coverage) from candidates))::integer as top_coverage_tie_count,
      bool_or(match_mode='STRICT') as has_strict
    from candidates
  )
  select
    c.snapshot_id,c.object_id,c.object_type,c.source_path,c.payload_sha256,c.payload,
    c.rank,c.match_mode,c.query_coverage,
    case
      when s.has_strict then 'STRICT_CANDIDATES'
      when s.top_coverage_tie_count>1 then 'BROAD_AMBIGUOUS'
      else 'BROAD_CANDIDATES'
    end as retrieval_state,
    s.candidate_count,
    s.top_coverage_tie_count
  from candidates c cross join stats s
  order by c.query_coverage desc,c.rank desc,convert_to(c.object_id,'UTF8')
$$;

revoke all on function semantic_atlas.search_current_runtime_objects_v3(text,text,text,text,timestamptz,text,text,integer) from public, anon, authenticated;
grant execute on function semantic_atlas.search_current_runtime_objects_v3(text,text,text,text,timestamptz,text,text,integer) to service_role;