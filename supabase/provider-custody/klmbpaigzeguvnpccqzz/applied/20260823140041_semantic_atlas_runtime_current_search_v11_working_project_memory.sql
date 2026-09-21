create or replace function semantic_atlas.search_current_runtime_objects_v11(
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
set search_path to 'pg_catalog','semantic_atlas'
as $$
declare
  v_strict tsquery;
  v_broad tsquery;
  v_tokens text[];
  v_limit integer;
  v_broad_text text;
  v_allowed text[];
begin
  if p_query is null or length(btrim(p_query))=0 then
    raise exception 'runtime search query required';
  end if;

  if exists(
    select 1 from unnest(p_allowed_object_types) x
    where x is not null and (upper(btrim(x))='ALL' or btrim(x) ~ '[*%?]')
  ) then
    raise exception 'runtime search object-type wildcards/ALL are forbidden; enumerate explicit allowed types';
  end if;

  select array_agg(distinct btrim(x) order by btrim(x))
  into v_allowed
  from unnest(p_allowed_object_types) x
  where x is not null and length(btrim(x))>0;

  if coalesce(cardinality(v_allowed),0)=0 then
    raise exception 'runtime search requires a non-empty explicit allowed_object_types scope';
  end if;

  if exists(
    select 1 from unnest(v_allowed) x
    where x not in ('validation_case','runtime_contract','working_memory','semantic_index')
  ) then
    raise exception 'runtime search object type has no approved deterministic search projection';
  end if;

  v_limit := least(greatest(coalesce(p_limit,20),1),100);
  v_strict := websearch_to_tsquery('english',p_query);
  v_tokens := tsvector_to_array(to_tsvector('english',p_query));

  if coalesce(cardinality(v_tokens),0)=0 then
    raise exception 'runtime search query produced no searchable lexemes';
  end if;

  select string_agg(quote_literal(x),' | ' order by x)
  into v_broad_text
  from unnest(v_tokens) x;
  v_broad := to_tsquery('english',v_broad_text);

  return query
  with current_rows as materialized (
    select *
    from semantic_atlas.read_current_runtime_objects_v1(
      p_authority_scope,
      p_git_repository_locator,
      p_git_ref,
      p_git_readback_sha,
      p_readback_at,
      p_readback_source
    )
  ), scoped_rows as materialized (
    select r.*
    from current_rows r
    where r.object_type=any(v_allowed)
  ), projected as materialized (
    select r.*,
      case
        when r.object_type='validation_case' then coalesce((
          select string_agg(coalesce(src.elem->>'content',''),' ' order by src.ord)
          from jsonb_array_elements(coalesce(r.payload #> '{case,sources}','[]'::jsonb))
               with ordinality as src(elem,ord)
        ),'')
        when r.object_type='runtime_contract' then coalesce(r.payload::text,'')
        when r.object_type='working_memory' then concat_ws(' ',
          coalesce(r.payload->>'subject',''),
          coalesce(r.payload->>'memory_summary',''),
          coalesce(r.payload->>'memory_class',''),
          coalesce(r.payload->>'currentness','')
        )
        when r.object_type='semantic_index' then concat_ws(' ',
          coalesce(r.payload->>'semantic_key',''),
          coalesce(r.payload->>'meaning',''),
          coalesce((select string_agg(value,' ') from jsonb_array_elements_text(coalesce(r.payload->'anti_collapse_rules','[]'::jsonb))), '')
        )
        else ''
      end as search_text
    from scoped_rows r
  ), vectors as materialized (
    select p.*,to_tsvector('english',p.search_text) as vec
    from projected p
  ), strict_matches as materialized (
    select v.*,ts_rank_cd(v.vec,v_strict)::real as score,
      ((select count(*) from unnest(v_tokens) q where q=any(tsvector_to_array(v.vec)))::real/cardinality(v_tokens)::real)::real as coverage
    from vectors v
    where v.vec @@ v_strict
  ), broad_matches as materialized (
    select v.*,ts_rank_cd(v.vec,v_broad)::real as score,
      ((select count(*) from unnest(v_tokens) q where q=any(tsvector_to_array(v.vec)))::real/cardinality(v_tokens)::real)::real as coverage
    from vectors v
    where v.vec @@ v_broad
  ), chosen as materialized (
    select s.snapshot_id,s.object_id,s.object_type,s.source_path,s.payload_sha256,s.payload,s.score,'STRICT'::text as mode,s.coverage
    from strict_matches s
    union all
    select b.snapshot_id,b.object_id,b.object_type,b.source_path,b.payload_sha256,b.payload,b.score,'BROAD_FALLBACK'::text as mode,b.coverage
    from broad_matches b
    where not exists(select 1 from strict_matches)
  ), stats as materialized (
    select count(*)::integer as n,
      count(*) filter(where c.coverage=(select max(c2.coverage) from chosen c2))::integer as top_ties,
      bool_or(c.mode='STRICT') as has_strict
    from chosen c
  ), limited as materialized (
    select c.*
    from chosen c
    order by c.coverage desc,c.score desc,convert_to(c.object_id,'UTF8')
    limit v_limit
  )
  select
    l.snapshot_id,
    l.payload_sha256 as candidate_digest,
    l.object_type,
    case
      when l.object_type='validation_case' then jsonb_build_object('sources',coalesce(l.payload #> '{case,sources}','[]'::jsonb))
      when l.object_type='runtime_contract' then jsonb_build_object('runtime_contract',l.payload)
      when l.object_type='working_memory' then jsonb_build_object(
        'memory_class',l.payload->'memory_class',
        'subject',l.payload->'subject',
        'memory_summary',l.payload->'memory_summary',
        'currentness',l.payload->'currentness',
        'promotion_status',l.payload->'promotion_status'
      )
      when l.object_type='semantic_index' then jsonb_build_object(
        'semantic_key',l.payload->'semantic_key',
        'meaning',l.payload->'meaning',
        'anti_collapse_rules',coalesce(l.payload->'anti_collapse_rules','[]'::jsonb)
      )
      else '{}'::jsonb
    end as projected_payload,
    l.score,
    l.mode,
    l.coverage,
    case
      when s.has_strict then 'STRICT_CANDIDATES'
      when s.top_ties>1 then 'BROAD_AMBIGUOUS'
      else 'BROAD_CANDIDATES'
    end,
    s.n,
    s.top_ties,
    v_allowed,
    'SEMANTIC_ATLAS_RUNTIME_SEARCH_GENERATOR_PROJECTION_V3'::text
  from limited l
  cross join stats s
  order by l.coverage desc,l.score desc,convert_to(l.object_id,'UTF8');
end;
$$;

revoke all on function semantic_atlas.search_current_runtime_objects_v11(text,text,text,text,timestamptz,text,text,integer,text[]) from public, anon, authenticated;
grant execute on function semantic_atlas.search_current_runtime_objects_v11(text,text,text,text,timestamptz,text,text,integer,text[]) to service_role;