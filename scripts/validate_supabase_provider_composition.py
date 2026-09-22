from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPABASE = ROOT / "supabase"
MIGRATIONS = SUPABASE / "migrations"
CUSTODY = SUPABASE / "provider-custody" / "klmbpaigzeguvnpccqzz"
INVENTORY = CUSTODY / "VERA_FULL_PROVIDER_LEDGER_CUSTODY_V3.json"
COMPOSITION = SUPABASE / "composition" / "VERA_PROVIDER_COMPOSITION_V1.json"
PENDING = SUPABASE / "composition" / "PENDING_MIGRATIONS_V1.json"


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
        "status": "PASS",
        "provider_migrations": len(expected),
        "pending_migrations": len(declared_pending),
        "last_provider_version": last,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
