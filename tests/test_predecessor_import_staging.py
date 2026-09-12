from __future__ import annotations

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
    result = docker("exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-At", "-U", "postgres", "-d", "postgres", input_text=sql)
    if ok and result.returncode != 0:
        raise AssertionError(f"psql failed:\n{result.stdout}\n{result.stderr}")
    return result
@pytest.fixture(scope="module")
def db() -> str:
    assert BOOTSTRAP.exists()
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    container = f"vera-import-test-{uuid.uuid4().hex[:8]}"
    started = docker("run", "--rm", "-d", "--name", container, "-e", "POSTGRES_PASSWORD=postgres", "postgres:17-alpine")
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
        psql(container, BOOTSTRAP.read_text(encoding="utf-8"))
        psql(container, MIGRATION.read_text(encoding="utf-8"))
        yield container
    finally:
        docker("rm", "-f", container)
def scalar(container: str, sql: str) -> str:
    return psql(container, sql).stdout.strip()


def test_import_tables_exist_and_are_rls_locked(db: str) -> None:
    rows = scalar(db, "select n.nspname||'.'||c.relname||':'||c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where (n.nspname,c.relname) in (('vera_evidence','predecessor_import_rows_v1'),('vera_receipts','predecessor_import_receipts_v1')) order by 1;").splitlines()
    assert rows == [
        "vera_evidence.predecessor_import_rows_v1:true",
        "vera_receipts.predecessor_import_receipts_v1:true",
    ]


def test_client_roles_have_no_raw_access(db: str) -> None:
    for schema, table in (("vera_evidence", "predecessor_import_rows_v1"), ("vera_receipts", "predecessor_import_receipts_v1")):
        for role in CLIENT_ROLES:
            assert scalar(db, f"select has_schema_privilege('{role}','{schema}','USAGE');") == "f"
            assert scalar(db, f"select has_table_privilege('{role}','{schema}.{table}','SELECT,INSERT,UPDATE,DELETE');") == "f"


def test_migration_operator_can_only_append_and_read(db: str) -> None:
    assert scalar(db, "select has_table_privilege('vera_migration_operator','vera_evidence.predecessor_import_rows_v1','SELECT,INSERT');") == "t"
    assert scalar(db, "select has_table_privilege('vera_migration_operator','vera_evidence.predecessor_import_rows_v1','UPDATE,DELETE');") == "f"
    assert scalar(db, "select has_table_privilege('vera_migration_operator','vera_receipts.predecessor_import_receipts_v1','SELECT,INSERT');") == "t"
    assert scalar(db, "select has_table_privilege('vera_migration_operator','vera_receipts.predecessor_import_receipts_v1','UPDATE,DELETE');") == "f"
def test_migration_operator_can_insert_but_cannot_mutate_import_row(db: str) -> None:
    sql = """
    set role vera_migration_operator;
    insert into vera_evidence.predecessor_import_rows_v1(
      operation_id, source_provider, source_schema, source_table, source_pk,
      source_row_sha256, source_snapshot_sha256, source_payload, privacy_class
    ) values (
      'op-test', 'klmbpaigzeguvnpccqzz', 'public', 'vera_save_state_events',
      '{"record_id":"00000000-0000-0000-0000-000000000001"}'::jsonb,
      repeat('a',64), repeat('b',64), '{"statement":"x"}'::jsonb, 'TECHNICAL'
    );
    reset role;
    """
    psql(db, sql)
    assert scalar(db, "select count(*) from vera_evidence.predecessor_import_rows_v1 where operation_id='op-test';") == "1"
    denied = psql(db, "set role vera_migration_operator; update vera_evidence.predecessor_import_rows_v1 set privacy_class='PROJECT' where operation_id='op-test';", ok=False)
    assert denied.returncode != 0


def test_import_receipt_status_is_bounded(db: str) -> None:
    bad = psql(db, """
      set role vera_migration_operator;
      insert into vera_receipts.predecessor_import_receipts_v1(
        operation_id, source_provider, source_schema, source_table,
        source_row_count, source_snapshot_sha256, target_row_count,
        target_snapshot_sha256, status
      ) values ('bad','klmbpaigzeguvnpccqzz','public','vera_save_state_events',1,repeat('a',64),1,repeat('a',64),'SUCCESS');
    """, ok=False)
    assert bad.returncode != 0
