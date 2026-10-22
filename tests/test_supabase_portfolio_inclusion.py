"""Inclusion gates keep optional portfolio services from becoming implicit Vera runtime requirements."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_supabase_portfolio_inclusion import reconcile  # noqa: E402

CONTRACT = json.loads(
    (ROOT / "supabase/composition/PORTFOLIO_INCLUSION_V1.json").read_text(encoding="utf-8")
)


def deployed_inventory():
    expected = [
        name
        for item in CONTRACT["components"]
        for name in item.get("observed_objects", [])
    ]
    return {
        "tables": [name for name in expected if not name.startswith("edge:")],
        "edge_functions": [name.removeprefix("edge:") for name in expected if name.startswith("edge:")],
    }


def test_deployed_contract_is_satisfied_by_bound_observations_only():
    result = reconcile(CONTRACT, deployed_inventory())
    assert result["status"] == "MATCH"
    assert result["checked_components"] == len(CONTRACT["components"])
    assert result["runtime_consumption_verified"] is False
    assert result["permission_to_deploy"] is False


def test_missing_expected_provider_table_detected():
    inventory = deployed_inventory()
    inventory["tables"].remove("public.vera_save_state_events")
    result = reconcile(CONTRACT, inventory)
    assert result["status"] == "DRIFT"
    assert {"component": "vera-state-history", "object": "public.vera_save_state_events",
            "reason": "DEPLOYED_OBJECT_MISSING"} in result["findings"]


def test_design_only_ark_mirror_is_not_a_mandatory_missing_table():
    result = reconcile(CONTRACT, deployed_inventory())
    assert not any("vera_ark" in entry["object"] for entry in result["findings"])


def test_unadmitted_candidate_appearance_is_not_promoted():
    inventory = deployed_inventory()
    inventory["tables"].append("public.vera_ark_operational_events")
    result = reconcile(CONTRACT, inventory)
    assert result["status"] == "DRIFT"
    assert {"component": "vera-ark-mirror", "object": "public.vera_ark_operational_events",
            "reason": "CANDIDATE_APPEARED_WITHOUT_ADMISSION"} in result["findings"]


def test_unrelated_observed_table_does_not_mint_an_admission():
    inventory = deployed_inventory()
    inventory["tables"].append("public.unrelated_table")
    result = reconcile(CONTRACT, inventory)
    assert result["status"] == "MATCH"
    assert "public.unrelated_table" in result["unknown_observed_objects"]


def test_duplicate_object_or_invalid_role_is_rejected():
    altered = json.loads(json.dumps(CONTRACT))
    altered["components"][1]["observed_objects"] = ["public.vera_save_state_events"]
    with pytest.raises(ValueError, match="multiple components"):
        reconcile(altered, deployed_inventory())
    altered = json.loads(json.dumps(CONTRACT))
    altered["components"][-1]["candidate_objects"] = ["public.some_table"]
    with pytest.raises(ValueError, match="local component"):
        reconcile(altered, deployed_inventory())


def test_forged_inventory_types_are_rejected():
    inventory = deployed_inventory()
    inventory["tables"] = "public.vera_save_state_events"
    with pytest.raises(ValueError, match="array"):
        reconcile(CONTRACT, inventory)
