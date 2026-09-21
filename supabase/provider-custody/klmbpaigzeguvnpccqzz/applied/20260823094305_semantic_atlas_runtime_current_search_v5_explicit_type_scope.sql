create or replace function semantic_atlas.search_current_runtime_objects_v5(
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
  payload jsonb,
  rank real,
  match_mode text,
  query_coverage real,
  retrieval_state text,
  candidate_count integer,
  top_coverage_tie_count integer,
  allowed_object_types text[]
)
language plpgsql
stable
security definer
set search_path = pg_catalog, semantic_atlas
as $$
declare
  v_strict tsquery;
  v_broad tsquery;
  v_tokens text[];
  v_limit integer;
  v_broad_text text;
  v_allowed text[];
begin
  if p_query is null or length(btrim(p_query))=0 then raise exception 'runtime search query required'; end if;
  select array_agg(distinct btrim(x) order by btrim(x)) into v_allowed
  from unnest(p_allowed_object_types) x
  where x is not null and length(btrim(x))>0;
  if coalesce(cardinality(v_allowed),0)=0 then raise exception 'runtime search requires a non-empty explicit allowed_object_types scope'; end if;
  v_limit:=least(greatest(coalesce(p_limit,20),1),100);
  v_strict:=websearch_to_tsquery('simple',p_query);
  v_tokens:=tsvector_to_array(to_tsvector('simple',p_query));
  if coalesce(cardinality(v_tokens),0)=0 then raise exception 'runtime search query produced no searchable lexemes'; end if;
  select string_agg(quote_literal(x),' | ' order by x) into v_broad_text from unnest(v_tokens) x;
  v_broad:=to_tsquery('simple',v_broad_text);

  return query
  with current_rows as materialized (
    select * from semantic_atlas.read_current_runtime_objects_v1(p_authority_scope,p_git_repository_locator,p_git_ref,p_git_readback_sha,p_readback_at,p_readback_source)
  ), scoped_rows as materialized (
    select r.* from current_rows r where r.object_type=any(v_allowed)
  ), vectors as materialized (
    select r.*,to_tsvector('simple',coalesce(r.payload::text,'')) as vec from scoped_rows r
  ), strict_matches as materialized (
    select v.*,ts_rank_cd(v.vec,v_strict)::real as score,
      ((select count(*) from unnest(v_tokens) q where q=any(tsvector_to_array(v.vec)))::real/cardinality(v_tokens)::real)::real as coverage
    from vectors v where v.vec @@ v_strict
  ), broad_matches as materialized (
    select v.*,ts_rank_cd(v.vec,v_broad)::real as score,
      ((select count(*) from unnest(v_tokens) q where q=any(tsvector_to_array(v.vec)))::real/cardinality(v_tokens)::real)::real as coverage
    from vectors v where v.vec @@ v_broad
  ), chosen as materialized (
    select s.snapshot_id,s.object_id,s.object_type,s.source_path,s.payload_sha256,s.payload,s.score,'STRICT'::text as mode,s.coverage from strict_matches s
    union all
    select b.snapshot_id,b.object_id,b.object_type,b.source_path,b.payload_sha256,b.payload,b.score,'BROAD_FALLBACK'::text as mode,b.coverage from broad_matches b where not exists(select 1 from strict_matches)
  ), limited as materialized (
    select c.* from chosen c order by c.coverage desc,c.score desc,convert_to(c.object_id,'UTF8') limit v_limit
  ), stats as (
    select count(*)::integer as n,
      count(*) filter(where l.coverage=(select max(l2.coverage) from limited l2))::integer as top_ties,
      bool_or(l.mode='STRICT') as has_strict
    from limited l
  )
  select l.snapshot_id,l.object_id,l.object_type,l.source_path,l.payload_sha256,l.payload,l.score,l.mode,l.coverage,
    case when s.has_strict then 'STRICT_CANDIDATES' when s.top_ties>1 then 'BROAD_AMBIGUOUS' else 'BROAD_CANDIDATES' end,
    s.n,s.top_ties,v_allowed
  from limited l cross join stats s
  order by l.coverage desc,l.score desc,convert_to(l.object_id,'UTF8');
end;
$$;

revoke all on function semantic_atlas.search_current_runtime_objects_v5(text,text,text,text,timestamptz,text,text,integer,text[]) from public, anon, authenticated;
grant execute on function semantic_atlas.search_current_runtime_objects_v5(text,text,text,text,timestamptz,text,text,integer,text[]) to service_role;

revoke execute on function semantic_atlas.search_current_runtime_objects_v1(text,text,text,text,timestamptz,text,text,integer) from service_role;
revoke execute on function semantic_atlas.search_current_runtime_objects_v2(text,text,text,text,timestamptz,text,text,integer) from service_role;
revoke execute on function semantic_atlas.search_current_runtime_objects_v3(text,text,text,text,timestamptz,text,text,integer) from service_role;
revoke execute on function semantic_atlas.search_current_runtime_objects_v4(text,text,text,text,timestamptz,text,text,integer,text) from service_role;