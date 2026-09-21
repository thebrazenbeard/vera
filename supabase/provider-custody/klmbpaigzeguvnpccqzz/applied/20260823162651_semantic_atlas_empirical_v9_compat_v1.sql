create or replace function semantic_atlas.search_current_runtime_objects_empirical_v9_compat_v1(
  p_authority_scope text,
  p_git_repository_locator text,
  p_git_ref text,
  p_git_readback_sha text,
  p_readback_at timestamptz,
  p_readback_source text,
  p_query text,
  p_limit integer,
  p_allowed_object_types text[]
)
returns table(
  snapshot_id uuid,
  candidate_digest text,
  object_type text,
  projected_payload jsonb,
  rank real,
  match_mode text,
  query_coverage real,
  retrieval_state text,
  candidate_count integer,
  top_coverage_tie_count integer,
  allowed_object_types text[],
  projection_version text
)
language plpgsql
stable
security definer
set search_path = pg_catalog, semantic_atlas
as $$
begin
  if p_allowed_object_types is distinct from array['validation_case']::text[] then
    raise exception 'empirical V9 compatibility route requires allowed_object_types exactly [validation_case]';
  end if;

  if p_limit is distinct from 5 then
    raise exception 'empirical V9 compatibility route requires result limit exactly 5';
  end if;

  return query
  select
    r.snapshot_id,
    r.payload_sha256 as candidate_digest,
    r.object_type,
    jsonb_build_object(
      'sources', coalesce(r.payload #> '{case,sources}', '[]'::jsonb)
    ) as projected_payload,
    r.rank,
    r.match_mode,
    r.query_coverage,
    r.retrieval_state,
    r.candidate_count,
    r.top_coverage_tie_count,
    array['validation_case']::text[] as allowed_object_types,
    'SEMANTIC_ATLAS_EMPIRICAL_V9_COMPAT_PROJECTION_V1'::text as projection_version
  from semantic_atlas.search_current_runtime_objects_v7(
    p_authority_scope,
    p_git_repository_locator,
    p_git_ref,
    p_git_readback_sha,
    p_readback_at,
    p_readback_source,
    p_query,
    5,
    array['validation_case']::text[]
  ) r
  order by r.query_coverage desc, r.rank desc, convert_to(r.object_id, 'UTF8');
end;
$$;

revoke all on function semantic_atlas.search_current_runtime_objects_empirical_v9_compat_v1(text,text,text,text,timestamptz,text,text,integer,text[]) from public;
revoke all on function semantic_atlas.search_current_runtime_objects_empirical_v9_compat_v1(text,text,text,text,timestamptz,text,text,integer,text[]) from anon;
revoke all on function semantic_atlas.search_current_runtime_objects_empirical_v9_compat_v1(text,text,text,text,timestamptz,text,text,integer,text[]) from authenticated;
grant execute on function semantic_atlas.search_current_runtime_objects_empirical_v9_compat_v1(text,text,text,text,timestamptz,text,text,integer,text[]) to service_role;
