from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_vera_runtime_cohesion_v1 import (
    load_json_strict,
    validate_cohesion,
    validate_cohesion_index,
    validate_consolidated_pair,
    validate_evidence_contract,
    validate_introspection,
    validate_manifest,
    validate_routing,
    validate_runtime_contract,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "architecture"


def manifest() -> dict:
    return load_json_strict(ARCHITECTURE / "VERA_SYSTEM_MANIFEST_V1.json")


def routing() -> dict:
    return load_json_strict(ARCHITECTURE / "VERA_RUNTIME_ROUTING_CONTRACT_V1.json")


def introspection() -> dict:
    return load_json_strict(ARCHITECTURE / "VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json")


def evidence_contract() -> dict:
    return load_json_strict(ARCHITECTURE / "VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json")


def cohesion_index() -> dict:
    return load_json_strict(ARCHITECTURE / "VERA_COHESION_INDEX_V1.json")


def runtime_contract() -> dict:
    return load_json_strict(ARCHITECTURE / "VERA_RUNTIME_CONTRACT_V1.json")


class VeraRuntimeCohesionV1Tests(unittest.TestCase):
    def test_current_source_passes(self):
        validate_cohesion(ROOT)

    def test_manifest_rejects_inventory_count_drift(self):
        document = manifest()
        document["inventory_count"] = 14
        with self.assertRaisesRegex(ValueError, "inventory_count"):
            validate_manifest(document)

    def test_manifest_rejects_duplicate_system_id(self):
        document = manifest()
        document["systems"][1]["system_id"] = document["systems"][0]["system_id"]
        with self.assertRaisesRegex(ValueError, "system_id contains duplicates"):
            validate_manifest(document)

    def test_manifest_rejects_bus_conflict_erasure(self):
        document = manifest()
        bus = next(
            system
            for system in document["systems"]
            if system["system_id"] == "chat-communication-bus"
        )
        bus["lifecycle"]["BOUND"] = "YES"
        with self.assertRaisesRegex(ValueError, "Bus BOUND"):
            validate_manifest(document)

    def test_routing_rejects_live_precedence_reversal(self):
        document = routing()
        document["decision_algorithm"][0] = "Retrieve durable state first."
        with self.assertRaisesRegex(ValueError, "live correction/scope precedence"):
            validate_routing(document)

    def test_routing_rejects_current_task_primary_drift(self):
        document = routing()
        current = next(
            route
            for route in document["domain_routes"]
            if route["domain"] == "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT"
        )
        current["primary"] = "SUPABASE"
        with self.assertRaisesRegex(ValueError, "LIVE_CONVERSATION"):
            validate_routing(document)

    def test_introspection_rejects_proposition_class_collapse(self):
        document = introspection()
        document["proposition_classes"].remove("PHENOMENOLOGY_CLAIM")
        with self.assertRaisesRegex(ValueError, "proposition classes drift"):
            validate_introspection(document)

    def test_introspection_rejects_false_phenomenology_resolution(self):
        document = introspection()
        document["current_status"]["phenomenology"] = "PROVEN"
        with self.assertRaisesRegex(ValueError, "UNRESOLVED"):
            validate_introspection(document)

    def test_introspection_rejects_false_install_claim(self):
        document = introspection()
        document["current_status"]["native_introspection_layer"] = "INSTALLED"
        with self.assertRaisesRegex(ValueError, "must not claim native introspection installation"):
            validate_introspection(document)

    def test_introspection_rejects_missing_negative_control(self):
        document = introspection()
        document["adversarial_probe_families"] = [
            probe
            for probe in document["adversarial_probe_families"]
            if probe["probe"] != "NEGATIVE_CONTROL_FALSE_AUTOBIOGRAPHY"
        ]
        with self.assertRaisesRegex(ValueError, "probe family drift"):
            validate_introspection(document)

    def test_evidence_contract_rejects_monotonic_lifecycle_semantics(self):
        document = evidence_contract()
        document["lifecycle_evidence"]["semantics"] = "MONOTONIC_LADDER"
        with self.assertRaisesRegex(ValueError, "orthogonal"):
            validate_evidence_contract(document)

    def test_evidence_contract_rejects_live_authority_class_collapse(self):
        document = evidence_contract()
        document["live_context_types"] = document["live_context_types"][:2]
        with self.assertRaisesRegex(ValueError, "live context type"):
            validate_evidence_contract(document)

    def test_evidence_contract_rejects_missing_durable_operational_state(self):
        document = evidence_contract()
        del document["durable_state_classes"]["DURABLE_OPERATIONAL_STATE"]
        with self.assertRaisesRegex(ValueError, "DURABLE_OPERATIONAL_STATE"):
            validate_evidence_contract(document)

    def test_evidence_contract_rejects_blind_contamination_erasure(self):
        document = evidence_contract()
        document["provenance"]["blind_review_state"] = "BLIND"
        with self.assertRaisesRegex(ValueError, "blind review"):
            validate_evidence_contract(document)

    def test_successor_index_rejects_runtime_availability_claim(self):
        document = cohesion_index()
        document["route_declarations"][0]["declaration_state"] = "AVAILABLE"
        with self.assertRaisesRegex(ValueError, "DECLARED"):
            validate_cohesion_index(document)

    def test_successor_index_rejects_symbolic_proof_decoration(self):
        document = cohesion_index()
        document["systems"][0]["proof_unit_refs"] = ["R10:DECORATIVE"]
        with self.assertRaisesRegex(ValueError, "proof_unit_refs"):
            validate_cohesion_index(document)

    def test_successor_pair_rejects_missing_evidence_class_target(self):
        index = cohesion_index()
        contract = runtime_contract()
        del contract["evidence_classes"]["general_mechanism_research"]
        with self.assertRaisesRegex(ValueError, "evidence class"):
            validate_consolidated_pair(index, contract)

    def test_successor_pair_rejects_missing_failure_signature(self):
        index = cohesion_index()
        contract = runtime_contract()
        del contract["failure_signatures"]["brigit_to_vera_transfer"]
        with self.assertRaisesRegex(ValueError, "failure signature"):
            validate_consolidated_pair(index, contract)

    def test_runtime_contract_rejects_unbounded_or_zero_retrieval_budget(self):
        document = runtime_contract()
        document["active_context_policy"]["uncertainty_probe_budget"]["max_total_new_domains"] = 0
        with self.assertRaisesRegex(ValueError, "budget"):
            validate_runtime_contract(document)

    def test_runtime_contract_rejects_false_phenomenology_resolution(self):
        document = runtime_contract()
        document["phenomenology"]["status"] = "PROVEN"
        with self.assertRaisesRegex(ValueError, "UNRESOLVED"):
            validate_runtime_contract(document)

    def test_mutation_does_not_leak_between_fixture_loads(self):
        first = introspection()
        second = deepcopy(first)
        second["current_status"]["phenomenology"] = "PROVEN"
        self.assertEqual(first["current_status"]["phenomenology"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
