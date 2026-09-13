from __future__ import annotations

import hashlib
import subprocess
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "providers" / "vera_control_plane" / "migrations" / "20260912183000_initialize_runtime_planes.sql"
MIGRATION = ROOT / "providers" / "vera_control_plane" / "migrations" / "20260912193000_create_predecessor_import_staging.sql"
CLIENT_ROLES = ("anon", "authenticated", "service_role")


def docker(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["docker", *args], input=input_text, text=True, capture_output=True, check=False)


def psql(container: str, sql: str, *, ok: bool = True) -> subprocess.CompletedProcess[str]:
    result = docker("exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-At",
                    "-U", "postgres", "-d", "postgres", input_text=sql)
    if ok and result.returncode != 0:
        raise AssertionError(f"psql failed:\n{result.stdout}\n{result.stderr}")
    return result


def scalar(container: str, sql: str) -> str:
    return psql(container, sql).stdout.strip()


@pytest.fixture(scope="module")
def db() -> str:
    container = f"vera-import-test-{uuid.uuid4().hex[:8]}"
    started = docker("run", "--rm", "-d", "--name", container,
                     "-e", "POSTGRES_PASSWORD=postgres", "postgres:17-alpine")
    assert started.returncode == 0, started.stderr
    try:
        consecutive = 0
        for _ in range(80):
            probe = docker("exec", container, "psql", "-At", "-U", "postgres", "-d", "postgres", "-c", "select 1")
            if probe.returncode == 0 and probe.stdout.strip() == "1":
                consecutive += 1
                if consecutive >= 2:
                    break
            else:
                consecutive = 0
            time.sleep(0.25)
        else:
            raise AssertionError("PostgreSQL never stabilized")
        psql(container, ";\n".join(f"CREATE ROLE {r} NOLOGIN" for r in CLIENT_ROLES) + ";")
        psql(container, "CREATE SCHEMA extensions; CREATE EXTENSION pgcrypto WITH SCHEMA extensions;")
        psql(container, BOOTSTRAP.read_text(encoding="utf-8"))
        psql(container, MIGRATION.read_text(encoding="utf-8"))
        yield container
    finally:
        docker("rm", "-f", container)


def test_locked_tables_exist(db: str) -> None:
    rows = scalar(db, """
      select n.nspname||'.'||c.relname||':'||c.relrowsecurity
      from pg_class c join pg_namespace n on n.oid=c.relnamespace
      where (n.nspname,c.relname) in (
        ('vera_evidence','predecessor_source_cuts_v1'),
        ('vera_evidence','predecessor_import_rows_v1'),
        ('vera_receipts','predecessor_import_receipts_v1')) order by 1;
    """).splitlines()
    assert rows == [
        "vera_evidence.predecessor_import_rows_v1:true",
        "vera_evidence.predecessor_source_cuts_v1:true",
        "vera_receipts.predecessor_import_receipts_v1:true",
    ]


def test_client_roles_have_no_raw_access(db: str) -> None:
    for schema, table in (
        ("vera_evidence", "predecessor_source_cuts_v1"),
        ("vera_evidence", "predecessor_import_rows_v1"),
        ("vera_receipts", "predecessor_import_receipts_v1"),
    ):
        for role in CLIENT_ROLES:
            assert scalar(db, f"select has_schema_privilege('{role}','{schema}','USAGE');") == "f"
            assert scalar(db, f"select has_table_privilege('{role}','{schema}.{table}','SELECT,INSERT,UPDATE,DELETE');") == "f"


def test_migration_operator_cannot_fabricate_receipts(db: str) -> None:
    assert scalar(db, "select has_table_privilege('vera_migration_operator','vera_receipts.predecessor_import_receipts_v1','INSERT');") == "f"
    denied = psql(db, """
      set role vera_migration_operator;
      insert into vera_receipts.predecessor_import_receipts_v1(
        operation_id, source_provider, source_schema, source_table,
        source_row_count, source_snapshot_sha256, target_row_count,
        target_snapshot_sha256, status, verifier_generation, canonicalization
      ) values ('fake','klmbpaigzeguvnpccqzz','public','vera_save_state_events',1,
        repeat('a',64),1,repeat('a',64),'VERIFIED_EXACT','fake','fake');
    """, ok=False)
    assert denied.returncode != 0


def test_unknown_source_cut_and_raw_insert_are_rejected(db: str) -> None:
    assert scalar(db, "select has_table_privilege('vera_migration_operator','vera_evidence.predecessor_import_rows_v1','INSERT');") == "f"
    denied = psql(db, """
      set role vera_migration_operator;
      select vera_evidence.stage_predecessor_import_row_v1(
        'unknown','klmbpaigzeguvnpccqzz','public','nope',1,'{"id":1}',
        '{"id": 1}','{"id": 1}','TECHNICAL');
    """, ok=False)
    assert denied.returncode != 0


def test_database_staging_enforces_project_internal_floor(db: str) -> None:
    denied = psql(db, """
      set role vera_migration_operator;
      with p as (
        select jsonb_build_object(
          'event_id', '00000000-0000-0000-0000-000000000099'
        ) as j
      )
      select vera_evidence.stage_predecessor_import_row_v1(
        'op-privacy-floor',
        'klmbpaigzeguvnpccqzz',
        'public',
        'vera_affective_runtime_events_v1',
        1,
        jsonb_build_object('event_id', j->'event_id'),
        j::text,
        j,
        'PUBLIC'
      ) from p;
    """, ok=False)
    assert denied.returncode != 0
    assert "privacy class violates source policy" in denied.stderr


def test_database_verifier_rejects_noncontiguous_ordinals(db: str) -> None:
    psql(db, """
      with p as (
        select jsonb_build_array(
          jsonb_build_object('record_id', '00000000-0000-0000-0000-000000000101'),
          jsonb_build_object('record_id', '00000000-0000-0000-0000-000000000102')
        )::text as text_value
      )
      insert into vera_evidence.predecessor_source_cuts_v1(
        source_provider, source_schema, source_table, source_row_count,
        source_snapshot_sha256, canonicalization, captured_at
      )
      select
        'synthetic-ordinal-test', 'public', 'vera_save_state_events', 2,
        encode(extensions.digest(convert_to(text_value, 'UTF8'), 'sha256'), 'hex'),
        'test-jsonb-array', clock_timestamp()
      from p;
    """)
    psql(db, """
      set role vera_migration_operator;
      with first_row as (
        select jsonb_build_object(
          'record_id', '00000000-0000-0000-0000-000000000101'
        ) as j
      )
      select vera_evidence.stage_predecessor_import_row_v1(
        'op-ordinal-gap',
        'synthetic-ordinal-test',
        'public',
        'vera_save_state_events',
        10,
        jsonb_build_object('record_id', j->'record_id'),
        j::text,
        j,
        'TECHNICAL'
      ) from first_row;
      with second_row as (
        select jsonb_build_object(
          'record_id', '00000000-0000-0000-0000-000000000102'
        ) as j
      )
      select vera_evidence.stage_predecessor_import_row_v1(
        'op-ordinal-gap',
        'synthetic-ordinal-test',
        'public',
        'vera_save_state_events',
        20,
        jsonb_build_object('record_id', j->'record_id'),
        j::text,
        j,
        'TECHNICAL'
      ) from second_row;
      select vera_receipts.verify_predecessor_import_v1(
        'op-ordinal-gap',
        'synthetic-ordinal-test',
        'public',
        'vera_save_state_events'
      );
      reset role;
    """)
    assert scalar(
        db,
        "select status from vera_receipts.predecessor_import_receipts_v1 "
        "where operation_id='op-ordinal-gap';",
    ) == "MISMATCH"


def test_database_verifier_derives_exact_receipt(db: str) -> None:
    payload = '{"privacy_scope": "TECHNICAL", "record_id": "00000000-0000-0000-0000-000000000001", "statement": "x"}'
    digest = scalar(db, f"select encode(extensions.digest(convert_to(jsonb_build_array('{payload}'::jsonb)::text,'UTF8'),'sha256'),'hex');")
    psql(db, f"""
      insert into vera_evidence.predecessor_source_cuts_v1(
        source_provider,source_schema,source_table,source_row_count,source_snapshot_sha256,canonicalization,captured_at)
      values ('synthetic','public','vera_save_state_events',1,'{digest}','test-jsonb-array',clock_timestamp());
      set role vera_migration_operator;
      with p as (select '{payload}'::jsonb as j)
      select vera_evidence.stage_predecessor_import_row_v1(
        'op-exact','synthetic','public','vera_save_state_events',1,
        jsonb_build_object('record_id',j->'record_id'),j::text,j,'TECHNICAL') from p;
      select vera_receipts.verify_predecessor_import_v1('op-exact','synthetic','public','vera_save_state_events');
      reset role;
    """)
    assert scalar(db, "select status from vera_receipts.predecessor_import_receipts_v1 where operation_id='op-exact';") == "VERIFIED_EXACT"


def test_database_verifier_is_idempotent(db: str) -> None:
    first = scalar(db, "select vera_receipts.verify_predecessor_import_v1('op-exact','synthetic','public','vera_save_state_events');")
    second = scalar(db, "select vera_receipts.verify_predecessor_import_v1('op-exact','synthetic','public','vera_save_state_events');")
    assert first == second
    assert scalar(db, "select count(*) from vera_receipts.predecessor_import_receipts_v1 where operation_id='op-exact';") == "1"
