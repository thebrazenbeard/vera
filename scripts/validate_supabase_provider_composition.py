from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPABASE = ROOT / "supabase"
MIGRATIONS = SUPABASE / "migrations"
CUSTODY = SUPABASE / "provider-custody" / "klmbpaigzeguvnpccqzz"
INVENTORY = CUSTODY / "VERA_FULL_PROVIDER_LEDGER_CUSTODY_V4.json"
COMPOSITION = SUPABASE / "composition" / "VERA_PROVIDER_COMPOSITION_V1.json"
PENDING = SUPABASE / "composition" / "PENDING_MIGRATIONS_V1.json"
REPORT_SCHEMA = "VERA_PROVIDER_COMPOSITION_REPORT_V2"


class LiveProviderQualificationRequired(ValueError):
    """A frozen source manifest cannot qualify a current provider."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict[str, object]:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    composition = json.loads(COMPOSITION.read_text(encoding="utf-8"))
    pending = json.loads(PENDING.read_text(encoding="utf-8"))

    expected: dict[str, str] = {}
    for item in inventory["migrations"]:
        name = f'{item["version"]}_{item["name"]}.sql'
        if name in expected:
            raise AssertionError(f"duplicate provider migration identity: {name}")
        digest = item.get("provider_sha256") or item.get("custody_sha256")
        if not digest:
            raise AssertionError(f"migration lacks custody digest: {name}")
        expected[name] = digest

    if len(expected) != composition["baseline"]["provider_migration_count"]:
        raise AssertionError("provider/composition migration-count mismatch")

    declared_pending = {
        item["filename"]: item
        for item in pending["pending"]
    }
    actual = {
        path.name
        for path in MIGRATIONS.glob("*.sql")
        if path.is_file()
    }
    allowed = set(expected) | set(declared_pending)
    if actual != allowed:
        missing = sorted(allowed - actual)
        extra = sorted(actual - allowed)
        raise AssertionError(
            f"migration identity drift: missing={missing} extra={extra}"
        )

    for name, digest in expected.items():
        executable = MIGRATIONS / name
        custody = CUSTODY / "applied" / name
        if not custody.is_file():
            raise AssertionError(f"missing provider custody file: {name}")
        if sha256(custody) != digest:
            raise AssertionError(f"custody digest mismatch: {name}")
        if sha256(executable) != digest:
            raise AssertionError(f"executable migration differs from custody: {name}")
        if executable.read_bytes() != custody.read_bytes():
            raise AssertionError(f"executable/custody byte mismatch: {name}")

    last = inventory["observed_cut"]["last_version"]
    for name, item in declared_pending.items():
        version = name.split("_", 1)[0]
        if len(version) != 14 or not version.isdigit():
            raise AssertionError(f"pending migration has invalid version: {name}")
        if version <= last:
            raise AssertionError(f"pending migration does not advance provider cut: {name}")
        owner = item.get("source_repository")
        source_blob = item.get("source_blob")
        if not owner or not source_blob or len(source_blob) != 40:
            raise AssertionError(f"pending migration lacks exact source binding: {name}")

    return {
        "report_schema": REPORT_SCHEMA,
        "status": "HISTORICAL_BASELINE_ONLY",
        "historical_source_byte_check": "PASS",
        "historical_inventory_observed_date": inventory["observed_cut"]["date"],
        "historical_provider_project_id": inventory["provider"]["project_id"],
        "historical_provider_migrations": len(expected),
        "pending_source_migrations": len(declared_pending),
        "historical_last_provider_version": last,
        "live_provider_queried": False,
        "live_full_ledger_parity": "UNVERIFIED_NOT_QUERIED",
        "live_sql_bytes_attested": False,
        "provider_apply_or_install_authorized": False,
        "legacy_v1_pass_compatible": False,
    }


def require_live_provider_parity(report: dict[str, object]) -> None:
    """Refuse source-report promotion regardless of its local PASS result.

    This validator has no provider connection, so even an altered or
    caller-forged report is not authenticated live readback.
    """
    raise LiveProviderQualificationRequired(
        "source-only Vera provider composition cannot attest current provider ledger or SQL bytes"
    )


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
