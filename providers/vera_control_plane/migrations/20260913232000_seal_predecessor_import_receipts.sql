-- Seal predecessor staging after a terminal receipt and serialize staging with verification.
-- Persistence remains predecessor evidence only; this migration does not admit/currentize payloads.

CREATE OR REPLACE FUNCTION vera_receipts.verify_predecessor_import_v1(
    p_operation_id text,
    p_source_provider text,
    p_source_schema text,
    p_source_table text
) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    cut vera_evidence.predecessor_source_cuts_v1%ROWTYPE;
    v_count bigint;
    v_min_ordinal bigint;
    v_max_ordinal bigint;
    v_distinct_ordinals bigint;
    v_digest text;
    v_status text;
    v_receipt uuid;
BEGIN
    SELECT * INTO STRICT cut
      FROM vera_evidence.predecessor_source_cuts_v1
     WHERE source_provider=p_source_provider
       AND source_schema=p_source_schema
       AND source_table=p_source_table
     FOR UPDATE;

    SELECT count(*),
           min(source_ordinal),
           max(source_ordinal),
           count(DISTINCT source_ordinal),
           encode(extensions.digest(convert_to(coalesce(jsonb_agg(source_payload ORDER BY source_ordinal)::text,'[]'),'UTF8'),'sha256'),'hex')
      INTO v_count, v_min_ordinal, v_max_ordinal, v_distinct_ordinals, v_digest
      FROM vera_evidence.predecessor_import_rows_v1
     WHERE operation_id=p_operation_id
       AND source_provider=p_source_provider
       AND source_schema=p_source_schema
       AND source_table=p_source_table
       AND source_snapshot_sha256=cut.source_snapshot_sha256;

    v_status := CASE
      WHEN v_count = cut.source_row_count
       AND (
         (cut.source_row_count = 0
          AND v_min_ordinal IS NULL
          AND v_max_ordinal IS NULL
          AND v_distinct_ordinals = 0)
         OR
         (cut.source_row_count > 0
          AND v_min_ordinal = 1
          AND v_max_ordinal = v_count
          AND v_distinct_ordinals = v_count)
       )
       AND v_digest = cut.source_snapshot_sha256
      THEN 'VERIFIED_EXACT' ELSE 'MISMATCH' END;

    INSERT INTO vera_receipts.predecessor_import_receipts_v1(
        operation_id, source_provider, source_schema, source_table,
        source_row_count, source_snapshot_sha256,
        target_row_count, target_snapshot_sha256,
        status, verifier_generation, canonicalization
    ) VALUES (
        p_operation_id, p_source_provider, p_source_schema, p_source_table,
        cut.source_row_count, cut.source_snapshot_sha256,
        v_count, v_digest,
        v_status, 'vera_receipts.verify_predecessor_import_v1@v3-sealed', cut.canonicalization
    ) ON CONFLICT (operation_id, source_provider, source_schema, source_table)
      DO NOTHING
      RETURNING receipt_id INTO v_receipt;

    IF v_receipt IS NULL THEN
        SELECT receipt_id INTO v_receipt
          FROM vera_receipts.predecessor_import_receipts_v1
         WHERE operation_id=p_operation_id
           AND source_provider=p_source_provider
           AND source_schema=p_source_schema
           AND source_table=p_source_table;
    END IF;
    RETURN v_receipt;
END
$$;

CREATE FUNCTION vera_evidence.reject_sealed_predecessor_import_insert_v1()
RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $$
BEGIN
    PERFORM 1
      FROM vera_evidence.predecessor_source_cuts_v1
     WHERE source_provider=NEW.source_provider
       AND source_schema=NEW.source_schema
       AND source_table=NEW.source_table
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'predecessor source cut missing';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM vera_receipts.predecessor_import_receipts_v1
         WHERE operation_id=NEW.operation_id
           AND source_provider=NEW.source_provider
           AND source_schema=NEW.source_schema
           AND source_table=NEW.source_table
    ) THEN
        RAISE EXCEPTION 'predecessor import operation sealed by terminal receipt';
    END IF;

    RETURN NEW;
END
$$;

ALTER FUNCTION vera_evidence.reject_sealed_predecessor_import_insert_v1()
OWNER TO vera_runtime_schema_owner;
REVOKE ALL ON FUNCTION vera_evidence.reject_sealed_predecessor_import_insert_v1()
FROM PUBLIC, anon, authenticated, service_role, vera_migration_operator;

CREATE TRIGGER predecessor_import_rows_v1_seal_before_insert
BEFORE INSERT ON vera_evidence.predecessor_import_rows_v1
FOR EACH ROW EXECUTE FUNCTION vera_evidence.reject_sealed_predecessor_import_insert_v1();
