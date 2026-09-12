-- Predecessor-provider import staging for Vera Control Plane migration.
-- Source semantics remain in thebrazenbeard/vera; imported rows are evidence, not admitted/current state.

CREATE TABLE vera_evidence.predecessor_import_rows_v1 (
    import_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id text NOT NULL CHECK (operation_id <> ''),
    source_provider text NOT NULL CHECK (source_provider <> ''),
    source_schema text NOT NULL CHECK (source_schema <> ''),
    source_table text NOT NULL CHECK (source_table <> ''),
    source_pk jsonb NOT NULL CHECK (jsonb_typeof(source_pk) = 'object'),
    source_row_sha256 text NOT NULL CHECK (source_row_sha256 ~ '^[0-9a-f]{64}$'),
    source_snapshot_sha256 text NOT NULL CHECK (source_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    source_payload jsonb NOT NULL,
    privacy_class text NOT NULL CHECK (privacy_class <> ''),
    target_adapter text,
    imported_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    limitations jsonb NOT NULL DEFAULT '["PREDECESSOR_EVIDENCE_ONLY","NOT_ADMITTED_CURRENT_STATE"]'::jsonb,
    CHECK (jsonb_typeof(limitations) = 'array')
);

CREATE UNIQUE INDEX predecessor_import_rows_v1_source_identity_uq
    ON vera_evidence.predecessor_import_rows_v1 (
        source_provider, source_schema, source_table, (source_pk::text)
    );

CREATE TABLE vera_receipts.predecessor_import_receipts_v1 (
    receipt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id text NOT NULL CHECK (operation_id <> ''),
    source_provider text NOT NULL CHECK (source_provider <> ''),
    source_schema text NOT NULL CHECK (source_schema <> ''),
    source_table text NOT NULL CHECK (source_table <> ''),
    source_row_count bigint NOT NULL CHECK (source_row_count >= 0),
    source_snapshot_sha256 text NOT NULL CHECK (source_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    target_row_count bigint CHECK (target_row_count IS NULL OR target_row_count >= 0),
    target_snapshot_sha256 text CHECK (target_snapshot_sha256 IS NULL OR target_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    status text NOT NULL CHECK (status IN ('STAGED','VERIFIED_EXACT','MISMATCH','AMBIGUOUS','ERROR')),
    verifier text NOT NULL DEFAULT 'vera_migration_operator',
    observed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    limitations jsonb NOT NULL DEFAULT '["MIGRATION_RECEIPT_ONLY","NOT_CURRENTNESS_OR_ADMISSION"]'::jsonb,
    CHECK (jsonb_typeof(limitations) = 'array'),
    CHECK (status <> 'VERIFIED_EXACT' OR (
        target_row_count = source_row_count
        AND target_snapshot_sha256 = source_snapshot_sha256
    ))
);

CREATE UNIQUE INDEX predecessor_import_receipts_v1_operation_uq
    ON vera_receipts.predecessor_import_receipts_v1 (
        operation_id, source_provider, source_schema, source_table
    );

DROP INDEX vera_evidence.predecessor_import_rows_v1_source_identity_uq;
CREATE UNIQUE INDEX predecessor_import_rows_v1_source_identity_uq
    ON vera_evidence.predecessor_import_rows_v1 (
        source_provider, source_schema, source_table,
        (source_pk::text), source_row_sha256
    );

CREATE FUNCTION vera_evidence.reject_predecessor_import_mutation_v1()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    RAISE EXCEPTION 'predecessor import rows are append-only';
END
$$;

CREATE TRIGGER predecessor_import_rows_v1_immutable
BEFORE UPDATE OR DELETE ON vera_evidence.predecessor_import_rows_v1
FOR EACH ROW EXECUTE FUNCTION vera_evidence.reject_predecessor_import_mutation_v1();

CREATE FUNCTION vera_receipts.reject_predecessor_import_receipt_mutation_v1()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    RAISE EXCEPTION 'predecessor import receipts are append-only';
END
$$;

CREATE TRIGGER predecessor_import_receipts_v1_immutable
BEFORE UPDATE OR DELETE ON vera_receipts.predecessor_import_receipts_v1
FOR EACH ROW EXECUTE FUNCTION vera_receipts.reject_predecessor_import_receipt_mutation_v1();

ALTER TABLE vera_evidence.predecessor_import_rows_v1 OWNER TO vera_runtime_schema_owner;
ALTER TABLE vera_receipts.predecessor_import_receipts_v1 OWNER TO vera_runtime_schema_owner;
ALTER FUNCTION vera_evidence.reject_predecessor_import_mutation_v1() OWNER TO vera_runtime_schema_owner;
ALTER FUNCTION vera_receipts.reject_predecessor_import_receipt_mutation_v1() OWNER TO vera_runtime_schema_owner;

ALTER TABLE vera_evidence.predecessor_import_rows_v1 ENABLE ROW LEVEL SECURITY;
ALTER TABLE vera_evidence.predecessor_import_rows_v1 FORCE ROW LEVEL SECURITY;
ALTER TABLE vera_receipts.predecessor_import_receipts_v1 ENABLE ROW LEVEL SECURITY;
ALTER TABLE vera_receipts.predecessor_import_receipts_v1 FORCE ROW LEVEL SECURITY;

REVOKE ALL ON vera_evidence.predecessor_import_rows_v1 FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON vera_receipts.predecessor_import_receipts_v1 FROM PUBLIC, anon, authenticated, service_role;
REVOKE EXECUTE ON FUNCTION vera_evidence.reject_predecessor_import_mutation_v1() FROM PUBLIC, anon, authenticated, service_role;
REVOKE EXECUTE ON FUNCTION vera_receipts.reject_predecessor_import_receipt_mutation_v1() FROM PUBLIC, anon, authenticated, service_role;

GRANT USAGE ON SCHEMA vera_evidence, vera_receipts TO vera_migration_operator;
GRANT SELECT, INSERT ON vera_evidence.predecessor_import_rows_v1 TO vera_migration_operator;
GRANT SELECT, INSERT ON vera_receipts.predecessor_import_receipts_v1 TO vera_migration_operator;

CREATE POLICY predecessor_import_rows_v1_migration_read
ON vera_evidence.predecessor_import_rows_v1
FOR SELECT TO vera_migration_operator
USING (true);

CREATE POLICY predecessor_import_rows_v1_migration_insert
ON vera_evidence.predecessor_import_rows_v1
FOR INSERT TO vera_migration_operator
WITH CHECK (true);

CREATE POLICY predecessor_import_receipts_v1_migration_read
ON vera_receipts.predecessor_import_receipts_v1
FOR SELECT TO vera_migration_operator
USING (true);

CREATE POLICY predecessor_import_receipts_v1_migration_insert
ON vera_receipts.predecessor_import_receipts_v1
FOR INSERT TO vera_migration_operator
WITH CHECK (true);

COMMENT ON TABLE vera_evidence.predecessor_import_rows_v1 IS
'Append-only predecessor-provider evidence staging. Presence is not admission, currentness, identity endorsement, consent, or control authority.';

COMMENT ON TABLE vera_receipts.predecessor_import_receipts_v1 IS
'Append-only migration/readback receipts. A receipt binds observed transfer facts only and cannot self-establish provider currentness or behavioral qualification.';
