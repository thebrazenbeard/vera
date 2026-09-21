create or replace function semantic_atlas.search_current_runtime_objects_v8(
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
  object_id text,
  object_type text,
  source_path text,
  payload_sha256 text,
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
language sql
stable
security definer
set search_path = pg_catalog, semantic_atlas
as $$
  select
    r.snapshot_id,
    r.object_id,
    r.object_type,
    r.source_path,
    r.payload_sha256,
    case
      when r.object_type = 'validation_case' then
        jsonb_build_object(
          'sources', coalesce(r.payload #> '{case,sources}', '[]'::jsonb)
        )
      when r.object_type = 'runtime_contract' then
        jsonb_build_object('runtime_contract', r.payload)
      else '{}'::jsonb
    end as projected_payload,
    r.rank,
    r.match_mode,
    r.query_coverage,
    r.retrieval_state,
    r.candidate_count,
    r.top_coverage_tie_count,
    r.allowed_object_types,
    'SEMANTIC_ATLAS_RUNTIME_SEARCH_RESULT_PROJECTION_V1'::text as projection_version
  from semantic_atlas.search_current_runtime_objects_v7(
    p_authority_scope,
    p_git_repository_locator,
    p_git_ref,
    p_git_readback_sha,
    p_readback_at,
    p_readback_source,
    p_query,
    p_limit,
    p_allowed_object_types
  ) r
  order by r.query_coverage desc, r.rank desc, convert_to(r.object_id,'UTF8');
$$;

revoke all on function semantic_atlas.search_current_runtime_objects_v8(text,text,text,text,timestamptz,text,text,integer,text[]) from public;
revoke all on function semantic_atlas.search_current_runtime_objects_v8(text,text,text,text,timestamptz,text,text,integer,text[]) from anon;
revoke all on function semantic_atlas.search_current_runtime_objects_v8(text,text,text,text,timestamptz,text,text,integer,text[]) from authenticated;
grant execute on function semantic_atlas.search_current_runtime_objects_v8(text,text,text,text,timestamptz,text,text,integer,text[]) to postgres, service_role;
revoke execute on function semantic_atlas.search_current_runtime_objects_v7(text,text,text,text,timestamptz,text,text,integer,text[]) from service_role;