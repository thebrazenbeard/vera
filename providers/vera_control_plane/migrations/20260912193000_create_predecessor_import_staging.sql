-- Locked predecessor import staging and terminal readback receipts.
-- Imported rows remain predecessor evidence; persistence is not admission/currentness.

CREATE TABLE vera_evidence.predecessor_source_cuts_v1 (
    source_provider text NOT NULL,
    source_schema text NOT NULL,
    source_table text NOT NULL,
    source_row_count bigint NOT NULL CHECK (source_row_count >= 0),
    source_snapshot_sha256 text NOT NULL CHECK (source_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    canonicalization text NOT NULL,
    captured_at timestamptz NOT NULL,
    limitations jsonb NOT NULL DEFAULT '["SOURCE_READBACK_ONLY","NOT_ADMISSION_OR_CURRENTNESS"]'::jsonb,
    PRIMARY KEY (source_provider, source_schema, source_table),
    UNIQUE (source_provider, source_schema, source_table, source_snapshot_sha256)
);

INSERT INTO vera_evidence.predecessor_source_cuts_v1
(source_provider, source_schema, source_table, source_row_count, source_snapshot_sha256, canonicalization, captured_at)
VALUES
('klmbpaigzeguvnpccqzz','public','vera_affective_runtime_events_v1',2,'7e05dbcd91818aa095e86507b56051d3af2dc5b7d10f15044be5ea9162395f35','sha256(jsonb_agg(to_jsonb(row) order by declared_pk)::text)','2026-09-13T03:23:54.997914Z'),
('klmbpaigzeguvnpccqzz','public','vera_affective_runtime_state_v1',1,'db18a7a3ba39f1ea00527af2c5217190cc13ebb62b14e3cc3dce7ac2af4b9bbd','sha256(jsonb_agg(to_jsonb(row) order by declared_pk)::text)','2026-09-13T03:23:54.997914Z'),
('klmbpaigzeguvnpccqzz','public','vera_context_events_v3',76,'0f9ffce7ab249079ed7f5eb4c5388885485d89d89c65b35e0871054676f2e349','sha256(jsonb_agg(to_jsonb(row) order by declared_pk)::text)','2026-09-13T03:23:54.997914Z'),('klmbpaigzeguvnpccqzz','public','vera_memory_epoch_archive_receipts_v1',1,'adf3bbdc1f6b808668e3bca2b69c85cf76dec59d75bf18f25e6712229af7ab96','sha256(jsonb_agg(to_jsonb(row) order by declared_pk)::text)','2026-09-13T03:23:54.997914Z'),
('klmbpaigzeguvnpccqzz','public','vera_memory_epoch_events_v1',7,'64ca800a4ac5d41b80b1770b3c0306161bae6d71782e68fd5b185283c2c2bfd9','sha256(jsonb_agg(to_jsonb(row) order by declared_pk)::text)','2026-09-13T03:23:54.997914Z'),
('klmbpaigzeguvnpccqzz','public','vera_memory_epoch_provider_receipts_v1',2,'24dd45dc6379db182f5780b6c0d372e6fe17d8035d9d73ff21730d86ddfa5e6f','sha256(jsonb_agg(to_jsonb(row) order by declared_pk)::text)','2026-09-13T03:23:54.997914Z'),
('klmbpaigzeguvnpccqzz','public','vera_memory_epoch_subjects_v1',1,'07f7f56de22e430b71a44d86909966f05f34406fbdb1c6a5fcaf7ed3bcba865c','sha256(jsonb_agg(to_jsonb(row) order by declared_pk)::text)','2026-09-13T03:23:54.997914Z'),
('klmbpaigzeguvnpccqzz','public','vera_save_state_events',203,'ae34f51c5536b302387d516a2591caee130eb462e08e83239542adef74adc4b1','sha256(jsonb_agg(to_jsonb(row) order by declared_pk)::text)','2026-09-13T03:23:54.997914Z'),
('klmbpaigzeguvnpccqzz','public','vera_save_state_supersession_edges',1,'3cc8033c63896c74d29bb8c016c04ff02355976328630ef699892122a7c01368','sha256(jsonb_agg(to_jsonb(row) order by declared_pk)::text)','2026-09-13T03:23:54.997914Z');

CREATE TABLE vera_evidence.predecessor_import_rows_v1 (
    import_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id text NOT NULL CHECK (operation_id <> ''),
    source_provider text NOT NULL,
    source_schema text NOT NULL,
    source_table text NOT NULL,
    source_ordinal bigint NOT NULL CHECK (source_ordinal > 0),
    source_pk jsonb NOT NULL CHECK (jsonb_typeof(source_pk) = 'object'),
    source_row_sha256 text NOT NULL CHECK (source_row_sha256 ~ '^[0-9a-f]{64}$'),
    source_snapshot_sha256 text NOT NULL CHECK (source_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    source_row_jsonb_text text NOT NULL,
    source_payload jsonb NOT NULL,
    privacy_class text NOT NULL CHECK (privacy_class <> ''),    imported_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    limitations jsonb NOT NULL DEFAULT '["PREDECESSOR_EVIDENCE_ONLY","NOT_ADMITTED_CURRENT_STATE"]'::jsonb,
    FOREIGN KEY (source_provider, source_schema, source_table, source_snapshot_sha256)
      REFERENCES vera_evidence.predecessor_source_cuts_v1
      (source_provider, source_schema, source_table, source_snapshot_sha256),
    UNIQUE (operation_id, source_provider, source_schema, source_table, source_ordinal),
    UNIQUE (operation_id, source_provider, source_schema, source_table, source_pk)
);

CREATE TABLE vera_receipts.predecessor_import_receipts_v1 (
    receipt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id text NOT NULL,
    source_provider text NOT NULL,
    source_schema text NOT NULL,
    source_table text NOT NULL,
    source_row_count bigint NOT NULL CHECK (source_row_count >= 0),
    source_snapshot_sha256 text NOT NULL CHECK (source_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    target_row_count bigint NOT NULL CHECK (target_row_count >= 0),
    target_snapshot_sha256 text NOT NULL CHECK (target_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    status text NOT NULL CHECK (status IN ('VERIFIED_EXACT','MISMATCH','ERROR')),
    verifier_generation text NOT NULL,
    canonicalization text NOT NULL,
    observed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    limitations jsonb NOT NULL DEFAULT '["MIGRATION_RECEIPT_ONLY","NOT_CURRENTNESS_OR_ADMISSION"]'::jsonb,
    UNIQUE (operation_id, source_provider, source_schema, source_table)
);
CREATE FUNCTION vera_receipts.verify_predecessor_import_v1(
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
    v_digest text;
    v_status text;
    v_receipt uuid;
BEGIN
    SELECT * INTO STRICT cut
      FROM vera_evidence.predecessor_source_cuts_v1
     WHERE source_provider=p_source_provider AND source_schema=p_source_schema AND source_table=p_source_table;

    SELECT count(*),
           encode(extensions.digest(convert_to(coalesce(jsonb_agg(source_payload ORDER BY source_ordinal)::text,'[]'),'UTF8'),'sha256'),'hex')
      INTO v_count, v_digest
      FROM vera_evidence.predecessor_import_rows_v1
     WHERE operation_id=p_operation_id AND source_provider=p_source_provider
       AND source_schema=p_source_schema AND source_table=p_source_table
       AND source_snapshot_sha256=cut.source_snapshot_sha256;

    v_status := CASE WHEN v_count=cut.source_row_count AND v_digest=cut.source_snapshot_sha256
                     THEN 'VERIFIED_EXACT' ELSE 'MISMATCH' END;    INSERT INTO vera_receipts.predecessor_import_receipts_v1(
        operation_id, source_provider, source_schema, source_table,
        source_row_count, source_snapshot_sha256,
        target_row_count, target_snapshot_sha256,
        status, verifier_generation, canonicalization
    ) VALUES (
        p_operation_id, p_source_provider, p_source_schema, p_source_table,
        cut.source_row_count, cut.source_snapshot_sha256,
        v_count, v_digest,
        v_status, 'vera_receipts.verify_predecessor_import_v1@v1', cut.canonicalization
    ) ON CONFLICT (operation_id, source_provider, source_schema, source_table)
      DO NOTHING
      RETURNING receipt_id INTO v_receipt;

    IF v_receipt IS NULL THEN
        SELECT receipt_id INTO v_receipt
          FROM vera_receipts.predecessor_import_receipts_v1
         WHERE operation_id=p_operation_id AND source_provider=p_source_provider
           AND source_schema=p_source_schema AND source_table=p_source_table;
    END IF;
    RETURN v_receipt;
END
$$;

CREATE FUNCTION vera_evidence.reject_predecessor_import_mutation_v1()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
    RAISE EXCEPTION 'predecessor import rows are append-only';
END
$$;

CREATE FUNCTION vera_receipts.reject_predecessor_import_receipt_mutation_v1()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
    RAISE EXCEPTION 'predecessor import receipts are append-only';
END
$$;
CREATE TRIGGER predecessor_import_rows_v1_immutable
BEFORE UPDATE OR DELETE ON vera_evidence.predecessor_import_rows_v1
FOR EACH ROW EXECUTE FUNCTION vera_evidence.reject_predecessor_import_mutation_v1();

CREATE TRIGGER predecessor_import_receipts_v1_immutable
BEFORE UPDATE OR DELETE ON vera_receipts.predecessor_import_receipts_v1
FOR EACH ROW EXECUTE FUNCTION vera_receipts.reject_predecessor_import_receipt_mutation_v1();

ALTER TABLE vera_evidence.predecessor_source_cuts_v1 OWNER TO vera_runtime_schema_owner;
ALTER TABLE vera_evidence.predecessor_import_rows_v1 OWNER TO vera_runtime_schema_owner;
ALTER TABLE vera_receipts.predecessor_import_receipts_v1 OWNER TO vera_runtime_schema_owner;
ALTER FUNCTION vera_evidence.reject_predecessor_import_mutation_v1() OWNER TO vera_runtime_schema_owner;
ALTER FUNCTION vera_receipts.reject_predecessor_import_receipt_mutation_v1() OWNER TO vera_runtime_schema_owner;
ALTER FUNCTION vera_receipts.verify_predecessor_import_v1(text,text,text,text) OWNER TO vera_runtime_schema_owner;

ALTER TABLE vera_evidence.predecessor_source_cuts_v1 ENABLE ROW LEVEL SECURITY;
ALTER TABLE vera_evidence.predecessor_source_cuts_v1 FORCE ROW LEVEL SECURITY;
ALTER TABLE vera_evidence.predecessor_import_rows_v1 ENABLE ROW LEVEL SECURITY;
ALTER TABLE vera_evidence.predecessor_import_rows_v1 FORCE ROW LEVEL SECURITY;
ALTER TABLE vera_receipts.predecessor_import_receipts_v1 ENABLE ROW LEVEL SECURITY;
ALTER TABLE vera_receipts.predecessor_import_receipts_v1 FORCE ROW LEVEL SECURITY;

REVOKE ALL ON vera_evidence.predecessor_source_cuts_v1 FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON vera_evidence.predecessor_import_rows_v1 FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON vera_receipts.predecessor_import_receipts_v1 FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION vera_receipts.verify_predecessor_import_v1(text,text,text,text) FROM PUBLIC, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA vera_evidence, vera_receipts TO vera_migration_operator;
GRANT SELECT ON vera_evidence.predecessor_source_cuts_v1 TO vera_migration_operator;
GRANT SELECT, INSERT ON vera_evidence.predecessor_import_rows_v1 TO vera_migration_operator;
GRANT SELECT ON vera_receipts.predecessor_import_receipts_v1 TO vera_migration_operator;
GRANT EXECUTE ON FUNCTION vera_receipts.verify_predecessor_import_v1(text,text,text,text) TO vera_migration_operator;

CREATE POLICY predecessor_source_cuts_v1_migration_read
ON vera_evidence.predecessor_source_cuts_v1
FOR SELECT TO vera_migration_operator USING (true);

CREATE POLICY predecessor_import_rows_v1_migration_read
ON vera_evidence.predecessor_import_rows_v1
FOR SELECT TO vera_migration_operator USING (true);

CREATE POLICY predecessor_import_rows_v1_migration_insert
ON vera_evidence.predecessor_import_rows_v1
FOR INSERT TO vera_migration_operator
WITH CHECK (true);

CREATE POLICY predecessor_import_receipts_v1_migration_read
ON vera_receipts.predecessor_import_receipts_v1
FOR SELECT TO vera_migration_operator USING (true);

COMMENT ON TABLE vera_evidence.predecessor_source_cuts_v1 IS
'Frozen predecessor source cuts used only to verify staged migration evidence.';
COMMENT ON TABLE vera_evidence.predecessor_import_rows_v1 IS
'Append-only predecessor evidence staging; persistence is not admission/currentness.';
COMMENT ON TABLE vera_receipts.predecessor_import_receipts_v1 IS
'Terminal database-derived migration readback receipts; no caller-written VERIFIED_EXACT.';

CREATE POLICY predecessor_source_cuts_v1_owner_read
ON vera_evidence.predecessor_source_cuts_v1
FOR SELECT TO vera_runtime_schema_owner USING (true);

CREATE POLICY predecessor_import_rows_v1_owner_read
ON vera_evidence.predecessor_import_rows_v1
FOR SELECT TO vera_runtime_schema_owner USING (true);

CREATE POLICY predecessor_import_receipts_v1_owner_read
ON vera_receipts.predecessor_import_receipts_v1
FOR SELECT TO vera_runtime_schema_owner USING (true);

CREATE POLICY predecessor_import_receipts_v1_owner_insert
ON vera_receipts.predecessor_import_receipts_v1
FOR INSERT TO vera_runtime_schema_owner WITH CHECK (true);

GRANT USAGE ON SCHEMA extensions TO vera_runtime_schema_owner;
GRANT EXECUTE ON FUNCTION extensions.digest(bytea,text) TO vera_runtime_schema_owner;
