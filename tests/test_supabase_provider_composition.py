import json
from pathlib import Path

from scripts.validate_supabase_provider_composition import validate


ROOT = Path(__file__).resolve().parents[1]


def test_supabase_provider_composition_is_exact() -> None:
    report = validate()
    assert report["status"] == "PASS"
    assert report["provider_migrations"] == 99
    assert report["pending_migrations"] == 0
    assert report["last_provider_version"] == "20260922190100"


def test_datum_acl_migration_is_promoted_from_exact_reviewed_source() -> None:
    inventory = json.loads(
        (
            ROOT
            / "supabase/provider-custody/klmbpaigzeguvnpccqzz/VERA_FULL_PROVIDER_LEDGER_CUSTODY_V4.json"
        ).read_text(encoding="utf-8")
    )
    item = inventory["migrations"][-1]
    assert item["version"] == "20260922190100"
    assert item["source_repository"] == "thebrazenbeard/vera"
    assert item["source_ref"] == "c59d914e4a7cb1c39cfc4d5fd63f07b29b34c05c"
    assert item["source_blob"] == "f603a3ebbbc9553179995601ced867b5d096ef0f"
    assert item["predecessor_pr"] == 189
    assert item["successor_pr"] == 196
    readback = item["provider_effect_readback"]
    assert readback["functions"] == 5
    assert readback["anon_execute_all_false"] is True
    assert readback["authenticated_execute_all_false"] is True
    assert readback["service_role_execute_all_true"] is True


def test_radar_oidc_migration_remains_exact_bus_bound() -> None:
    inventory = json.loads(
        (
            ROOT
            / "supabase/provider-custody/klmbpaigzeguvnpccqzz/VERA_FULL_PROVIDER_LEDGER_CUSTODY_V4.json"
        ).read_text(encoding="utf-8")
    )
    item = inventory["migrations"][-2]
    assert item["version"] == "20260922171230"
    assert item["source_repository"] == "thebrazenbeard/chat-communication-bus"
    assert item["source_blob"] == "054d668486887c05efe359314b51894e7274d0a6"


def test_live_bus_edge_function_has_exact_noncanonical_source_binding() -> None:
    custody = json.loads(
        (
            ROOT
            / "supabase/provider-custody/klmbpaigzeguvnpccqzz/edge-functions/GITHUB_BUS_INGEST_DEPLOYMENT_CUSTODY_V1.json"
        ).read_text(encoding="utf-8")
    )
    binding = custody["exact_source_binding"]
    assert binding["repository"] == "thebrazenbeard/chat-communication-bus"
    assert binding["active_pr"] == 325
    assert binding["source_head"] == "640b44c4b715d870b6d5efcdb64ff447eec64467"
    assert binding["files"]["handler.ts"]["blob"] == "cc7cd56632e21c34ec861797db43b60f83977d9b"
    assert binding["files"]["handler.ts"]["live_byte_match"] is True
    assert custody["canonical_currentness"]["live_matches_bus_main_handler"] is False
    assert custody["canonical_currentness"]["independent_source_mutation_forbidden"] is True
