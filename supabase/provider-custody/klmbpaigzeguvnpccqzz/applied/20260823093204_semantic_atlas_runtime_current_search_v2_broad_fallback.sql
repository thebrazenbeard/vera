create or replace function semantic_atlas.search_current_runtime_objects_v2(
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
  query_coverage real
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
begin
  if p_query is null or length(btrim(p_query))=0 then
    raise exception 'runtime search query required';
  end if;
  v_limit:=least(greatest(coalesce(p_limit,20),1),100);
  v_strict:=websearch_to_tsquery('simple',p_query);
  v_tokens:=tsvector_to_array(to_tsvector('simple',p_query));
  if coalesce(cardinality(v_tokens),0)=0 then
    raise exception 'runtime search query produced no searchable lexemes';
  end if;

  select string_agg(quote_literal(x),' | ' order by x)
  into v_broad_text
  from unnest(v_tokens) x;
  v_broad:=to_tsquery('simple',v_broad_text);

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
  ), vectors as (
    select r.*,to_tsvector('simple',coalesce(r.payload::text,'')) as vec
    from current_rows r
  ), strict_matches as (
    select v.*,
      ts_rank_cd(v.vec,v_strict)::real as score,
      ((select count(*) from unnest(v_tokens) q where q=any(tsvector_to_array(v.vec)))::real / cardinality(v_tokens)::real)::real as coverage
    from vectors v
    where v.vec @@ v_strict
  ), broad_matches as (
    select v.*,
      ts_rank_cd(v.vec,v_broad)::real as score,
      ((select count(*) from unnest(v_tokens) q where q=any(tsvector_to_array(v.vec)))::real / cardinality(v_tokens)::real)::real as coverage
    from vectors v
    where v.vec @@ v_broad
  ), chosen as (
    select s.snapshot_id,s.object_id,s.object_type,s.source_path,s.payload_sha256,s.payload,s.score,'STRICT'::text as mode,s.coverage
    from strict_matches s
    union all
    select b.snapshot_id,b.object_id,b.object_type,b.source_path,b.payload_sha256,b.payload,b.score,'BROAD_FALLBACK'::text as mode,b.coverage
    from broad_matches b
    where not exists(select 1 from strict_matches)
  )
  select c.snapshot_id,c.object_id,c.object_type,c.source_path,c.payload_sha256,c.payload,c.score,c.mode,c.coverage
  from chosen c
  order by c.coverage desc,c.score desc,convert_to(c.object_id,'UTF8')
  limit v_limit;
end;
$$;

revoke all on function semantic_atlas.search_current_runtime_objects_v2(text,text,text,text,timestamptz,text,text,integer) from public, anon, authenticated;
grant execute on function semantic_atlas.search_current_runtime_objects_v2(text,text,text,text,timestamptz,text,text,integer) to service_role;