from __future__ import annotations

import subprocess
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "providers" / "vera_control_plane" / "migrations"
BOOTSTRAP = MIGRATIONS_DIR / "20260912183000_initialize_runtime_planes.sql"
BASE_MIGRATION = MIGRATIONS_DIR / "20260912193000_create_predecessor_import_staging.sql"


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
    container = f"vera-import-seal-test-{uuid.uuid4().hex[:8]}"
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
        psql(container, ";\n".join(f"CREATE ROLE {r} NOLOGIN" for r in ("anon", "authenticated", "service_role")) + ";")
        psql(container, "CREATE SCHEMA extensions; CREATE EXTENSION pgcrypto WITH SCHEMA extensions;")
        psql(container, BOOTSTRAP.read_text(encoding="utf-8"))
        psql(container, BASE_MIGRATION.read_text(encoding="utf-8"))
        for migration in sorted(MIGRATIONS_DIR.glob("*predecessor_import_seal*.sql")):
            psql(container, migration.read_text(encoding="utf-8"))
        yield container
    finally:
        docker("rm", "-f", container)


def test_verified_operation_rejects_late_staging(db: str) -> None:
    payload = '{"privacy_scope": "TECHNICAL", "record_id": "00000000-0000-0000-0000-000000000201", "statement": "x"}'
    digest = scalar(db, f"select encode(extensions.digest(convert_to(jsonb_build_array('{payload}'::jsonb)::text,'UTF8'),'sha256'),'hex');")
    psql(db, f"""
      insert into vera_evidence.predecessor_source_cuts_v1(
        source_provider,source_schema,source_table,source_row_count,source_snapshot_sha256,canonicalization,captured_at)
      values ('synthetic-seal','public','vera_save_state_events',1,'{digest}','test-jsonb-array',clock_timestamp());
      set role vera_migration_operator;
      with p as (select '{payload}'::jsonb as j)
      select vera_evidence.stage_predecessor_import_row_v1(
        'op-seal','synthetic-seal','public','vera_save_state_events',1,
        jsonb_build_object('record_id',j->'record_id'),j::text,j,'TECHNICAL') from p;
      select vera_receipts.verify_predecessor_import_v1('op-seal','synthetic-seal','public','vera_save_state_events');
      reset role;
    """)

    late = psql(db, """
      set role vera_migration_operator;
      with p as (select jsonb_build_object(
        'privacy_scope','TECHNICAL',
        'record_id','00000000-0000-0000-0000-000000000202',
        'statement','late') as j)
      select vera_evidence.stage_predecessor_import_row_v1(
        'op-seal','synthetic-seal','public','vera_save_state_events',2,
        jsonb_build_object('record_id',j->'record_id'),j::text,j,'TECHNICAL') from p;
    """, ok=False)
    assert late.returncode != 0
    assert "sealed" in late.stderr.lower()
    assert scalar(db, "select count(*) from vera_evidence.predecessor_import_rows_v1 where operation_id='op-seal';") == "1"
    assert scalar(db, "select status from vera_receipts.predecessor_import_receipts_v1 where operation_id='op-seal';") == "VERIFIED_EXACT"
