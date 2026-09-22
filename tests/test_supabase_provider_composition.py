import json
from pathlib import Path

from scripts.validate_supabase_provider_composition import validate


ROOT = Path(__file__).resolve().parents[1]


def test_supabase_provider_composition_is_exact() -> None:
    report = validate()
    assert report["status"] == "PASS"
    assert report["provider_migrations"] == 97
    assert report["pending_migrations"] == 1
    assert report["last_provider_version"] == "20260921202237"


def test_radar_pending_migration_is_bound_to_bus_exact_source() -> None:
    pending = json.loads(
        (ROOT / "supabase/composition/PENDING_MIGRATIONS_V1.json").read_text(
            encoding="utf-8"
        )
    )
    item = pending["pending"][0]
    assert item["filename"] == "20260922171230_radar_oidc_replay_guard_rls_v1.sql"
    assert item["source_repository"] == "thebrazenbeard/chat-communication-bus"
    assert item["source_ref"] == "f9179bd1426bf90c23ab6a4d14d5a8e9b39c66d2"
    assert item["source_blob"] == "054d668486887c05efe359314b51894e7274d0a6"
    assert item["effect_state"] == "SOURCE_COMPOSED_PROVIDER_EFFECT_PENDING"
