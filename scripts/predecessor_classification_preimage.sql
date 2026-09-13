-- Deterministic predecessor application-object classification preimage.
-- Provider: klmbpaigzeguvnpccqzz
-- Canonical order: schema_name, object_class, identity
-- Canonical line: schema|object_class|identity|disposition
-- Digest: SHA-256(UTF8(string_agg(line, LF))) with no trailing LF.
WITH rels AS (
  SELECT n.nspname AS schema_name, 'relation'::text AS object_class,
         c.relname AS root_name, c.relname || ':' || c.relkind::text AS identity
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname IN ('public','radar','build_team_2','bug_ops','redworm','semantic_atlas')
    AND c.relkind IN ('r','p','v','m','S','f')
), funcs AS (
  SELECT n.nspname, 'function'::text, p.proname,
         p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')'
  FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname IN ('public','radar','build_team_2','bug_ops','redworm','semantic_atlas')
), trigs AS (
  SELECT n.nspname, 'trigger'::text, c.relname, c.relname || '.' || t.tgname
  FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE NOT t.tgisinternal
    AND n.nspname IN ('public','radar','build_team_2','bug_ops','redworm','semantic_atlas')
), objs AS (
  SELECT * FROM rels UNION ALL SELECT * FROM funcs UNION ALL SELECT * FROM trigs
), classified AS (
  SELECT *, CASE
    WHEN schema_name IN ('build_team_2','bug_ops','redworm') THEN 'ARCHIVE'
    WHEN schema_name = 'radar' THEN 'REFERENCE_ONLY'
    WHEN schema_name = 'semantic_atlas' AND
         (root_name LIKE 'semantic_capture_%' OR root_name IN
          ('capture_semantic_event_v1','record_semantic_capture_outcome_v2',
           'reject_capture_history_mutation_v1')) THEN 'REFERENCE_ONLY'
    WHEN schema_name = 'semantic_atlas' THEN 'REBUILD_FROM_SOURCE'
    WHEN schema_name = 'public' AND
         (root_name LIKE 'brigit_%' OR root_name LIKE 'assign_brigit_%' OR
          root_name LIKE 'block_brigit_%') THEN 'REFERENCE_ONLY'
    WHEN schema_name = 'public' AND root_name LIKE 'bt2_%' THEN 'ARCHIVE'
    WHEN schema_name = 'public' AND root_name = 'radar_project_bus_message_v1'
      THEN 'REFERENCE_ONLY'
    WHEN schema_name = 'public' AND root_name = 'rls_auto_enable' THEN 'RETIRE'
    WHEN schema_name = 'public' AND
         (root_name LIKE '%portable_bootstrap%' OR root_name = 'vera_bootstrap_sha256_text')
      THEN 'ARCHIVE'
    WHEN schema_name = 'public' AND
         (root_name LIKE 'vera_coordination%' OR root_name IN
          ('assign_vera_coordination_record_time','block_vera_coordination_mutation'))
      THEN 'REFERENCE_ONLY'
    WHEN schema_name = 'public' AND object_class = 'relation' AND
         (root_name IN ('vera_save_state_events','vera_save_state_supersession_edges',
          'vera_context_events_v3','vera_affective_runtime_state_v1',
          'vera_affective_runtime_events_v1') OR root_name LIKE 'vera_memory_epoch_%')
      THEN 'MIGRATE'
    WHEN schema_name = 'public' AND
         (root_name LIKE 'vera_%' OR root_name LIKE '_vera_%' OR
          root_name LIKE 'assign_vera_%' OR root_name LIKE 'block_vera_%')
      THEN 'REBUILD_FROM_SOURCE'
    ELSE 'UNKNOWN'
  END AS disposition
  FROM objs
), canon AS (
  SELECT schema_name, object_class, identity, disposition,
         schema_name || '|' || object_class || '|' || identity || '|' || disposition AS line
  FROM classified
  ORDER BY schema_name, object_class, identity
), aggregate AS (
  SELECT count(*) AS object_count,
         count(*) FILTER (WHERE disposition = 'UNKNOWN') AS unknown_count,
         string_agg(line, E'\n' ORDER BY schema_name, object_class, identity) AS preimage
  FROM canon
)
SELECT object_count, unknown_count,
       encode(extensions.digest(convert_to(preimage, 'UTF8'), 'sha256'), 'hex') AS sha256,
       preimage
FROM aggregate;
