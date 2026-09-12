from __future__ import annotations

import subprocess
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "providers" / "vera_control_plane" / "migrations" / "20260912183000_initialize_runtime_planes.sql"
SCHEMAS = ("vera_evidence", "vera_state", "vera_receipts", "vera_sync")
CAPABILITY_ROLES = (
    "vera_runtime_evidence_reader",
    "vera_runtime_state_proposer",
    "vera_cohesion_admitter",
    "vera_effect_executor",
    "vera_control_verifier",
    "vera_migration_operator",
)
SCHEMA_OWNER_ROLE = "vera_runtime_schema_owner"
INTERNAL_ROLES = CAPABILITY_ROLES + (SCHEMA_OWNER_ROLE,)
CLIENT_ROLES = ("anon", "authenticated", "service_role")


def docker(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def psql(container: str, sql: str) -> str:
    result = docker(
        "exec", "-i", container,
        "psql", "-v", "ON_ERROR_STOP=1", "-At", "-U", "postgres", "-d", "postgres",
        input_text=sql,
    )
    if result.returncode != 0:
        raise AssertionError(f"psql failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return result.stdout.strip()


@pytest.fixture(scope="module")
def migrated_postgres() -> str:
    assert MIGRATION.exists(), f"missing Control Plane provider migration: {MIGRATION}"
    container = f"vera-cp-test-{uuid.uuid4().hex[:8]}"
    started = docker(
        "run", "--rm", "-d", "--name", container,
        "-e", "POSTGRES_PASSWORD=postgres",
        "postgres:17-alpine",
    )
    assert started.returncode == 0, started.stderr
    try:
        consecutive_ready = 0
        for _ in range(80):
            ready = docker(
                "exec", container,
                "psql", "-At", "-U", "postgres", "-d", "postgres", "-c", "SELECT 1",
            )
            if ready.returncode == 0 and ready.stdout.strip() == "1":
                consecutive_ready += 1
                if consecutive_ready >= 2:
                    break
            else:
                consecutive_ready = 0
            time.sleep(0.25)
        else:
            raise AssertionError("disposable PostgreSQL did not become stably queryable")

        psql(container, ";\n".join(f"CREATE ROLE {role} NOLOGIN" for role in CLIENT_ROLES) + ";")
        psql(container, MIGRATION.read_text(encoding="utf-8"))
        yield container
    finally:
        docker("rm", "-f", container)


def test_runtime_plane_schemas_exist(migrated_postgres: str) -> None:
    found = set(psql(
        migrated_postgres,
        "SELECT nspname FROM pg_namespace WHERE nspname LIKE 'vera_%' ORDER BY nspname;",
    ).splitlines())
    assert set(SCHEMAS).issubset(found)
    assert "vera_control" not in found


def test_capability_roles_exist_without_login(migrated_postgres: str) -> None:
    rows = psql(
        migrated_postgres,
        "SELECT rolname || ':' || CASE WHEN rolcanlogin THEN 't' ELSE 'f' END FROM pg_roles "
        "WHERE rolname LIKE 'vera_%' ORDER BY rolname;",
    ).splitlines()
    observed = dict(row.split(":", 1) for row in rows)
    for role in INTERNAL_ROLES:
        assert observed.get(role) == "f"


def test_client_roles_have_no_raw_schema_usage(migrated_postgres: str) -> None:
    for schema in SCHEMAS:
        for role in CLIENT_ROLES:
            value = psql(
                migrated_postgres,
                f"SELECT has_schema_privilege('{role}', '{schema}', 'USAGE');",
            )
            assert value == "f", f"{role} unexpectedly has USAGE on {schema}"


def test_capability_roles_are_not_privileged_db_admins(migrated_postgres: str) -> None:
    rows = psql(
        migrated_postgres,
        "SELECT rolname || ':' || CASE WHEN rolsuper THEN 't' ELSE 'f' END || ':' || CASE WHEN rolcreatedb THEN 't' ELSE 'f' END || ':' || CASE WHEN rolcreaterole THEN 't' ELSE 'f' END || ':' || CASE WHEN rolbypassrls THEN 't' ELSE 'f' END "
        "FROM pg_roles WHERE rolname LIKE 'vera_%' ORDER BY rolname;",
    ).splitlines()
    observed = {parts[0]: parts[1:] for parts in (row.split(":") for row in rows)}
    for role in INTERNAL_ROLES:
        assert observed.get(role) == ["f", "f", "f", "f"]


def test_future_functions_do_not_default_to_public_execute(migrated_postgres: str) -> None:
    for schema in SCHEMAS:
        psql(
            migrated_postgres,
            f"SET ROLE {SCHEMA_OWNER_ROLE}; CREATE FUNCTION {schema}.__priv_probe() RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$; RESET ROLE;",
        )
        try:
            value = psql(
                migrated_postgres,
                f"SELECT has_function_privilege('public', '{schema}.__priv_probe()', 'EXECUTE');",
            )
            assert value == "f", f"PUBLIC unexpectedly has EXECUTE on new function in {schema}"
        finally:
            psql(migrated_postgres, f"SET ROLE {SCHEMA_OWNER_ROLE}; DROP FUNCTION {schema}.__priv_probe(); RESET ROLE;")


def test_future_tables_do_not_default_to_client_access(migrated_postgres: str) -> None:
    for schema in SCHEMAS:
        psql(migrated_postgres, f"SET ROLE {SCHEMA_OWNER_ROLE}; CREATE TABLE {schema}.__priv_probe(id bigint generated always as identity primary key); RESET ROLE;")
        try:
            for role in CLIENT_ROLES:
                value = psql(
                    migrated_postgres,
                    f"SELECT has_table_privilege('{role}', '{schema}.__priv_probe', 'SELECT,INSERT,UPDATE,DELETE');",
                )
                assert value == "f", f"{role} unexpectedly has DML access to new table in {schema}"
        finally:
            psql(migrated_postgres, f"SET ROLE {SCHEMA_OWNER_ROLE}; DROP TABLE {schema}.__priv_probe; RESET ROLE;")
