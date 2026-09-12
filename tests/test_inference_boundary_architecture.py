from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "architecture/VERA_COHESION_INFERENCE_BOUNDARY_V1.json"
HOOK = ROOT / "architecture/VERA_RUNTIME_COHESION_INFERENCE_HOOK_V1.json"
PACKAGE_INIT = ROOT / "runtime_cohesion/__init__.py"


class InferenceBoundaryArchitectureTests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_contract_and_hook_exist_and_parse(self):
        self.assertTrue(CONTRACT.is_file())
        self.assertTrue(HOOK.is_file())
        self.assertIsInstance(self.load(CONTRACT), dict)
        self.assertIsInstance(self.load(HOOK), dict)

    def test_contract_is_source_only_and_binds_exact_r31_provenance(self):
        contract = self.load(CONTRACT)
        self.assertEqual(contract["status"], "SOURCE_ONLY_NOT_INSTALLED")
        reviewed = contract["reviewed_design_input"]
        self.assertEqual(reviewed["repository"], "thebrazenbeard/wip")
        self.assertEqual(reviewed["pull_request"], 1)
        self.assertEqual(reviewed["head"], "941b7bc45d97138bed5d220c0ba591db87100a58")
        self.assertEqual(reviewed["contract_schema"], "1.4")
        self.assertEqual(reviewed["contract_blob"], "56a428ff12c665c7cd735f16c46daa92a538cc5a")
        self.assertEqual(reviewed["architecture_blob"], "d5470af547efe1487e8cd0f11925ccdc816a564b")

    def test_lifecycle_preserves_distinct_validation_admission_and_effect_stages(self):
        contract = self.load(CONTRACT)
        self.assertEqual(contract["lifecycle"], [
            "CAPTURE", "VALIDATE_COMPONENTS", "COMPOSE", "ADMIT", "CAPABILITY_BIND",
            "PROJECT", "PRECALL_REVALIDATE_GATE", "INVOCATION_RESERVE", "INJECT",
            "GENERATE", "VERIFY_OBSERVE", "RECEIPT",
        ])

    def test_ownership_is_split_and_source_cannot_self_install(self):
        contract = self.load(CONTRACT)
        owners = contract["ownership"]
        self.assertEqual(owners["provider_neutral_contract"], "thebrazenbeard/vera/runtime_cohesion")
        self.assertEqual(owners["concrete_injection_and_frontier"], "EXACT_INFERENCE_HOST")
        self.assertEqual(owners["install_current_route_qualification"], "thebrazenbeard/vera-control-plane")
        self.assertNotEqual(owners["provider_neutral_contract"], owners["install_current_route_qualification"])

    def test_nonpromotion_edges_and_claim_ceiling_are_explicit(self):
        contract = self.load(CONTRACT)
        edges = {(e["source"], e["forbidden_promotion"]) for e in contract["nonpromotion_edges"]}
        required = {
            ("PROJECTION_SUCCESS", "ADMISSION_OR_AUTHORITY"),
            ("REQUEST_CONSTRUCTED", "PROVIDER_CONSUMPTION"),
            ("RESPONSE_BOUND", "BEHAVIORAL_QUALIFICATION"),
            ("SOURCE_IMPLEMENTED", "INSTALL_OR_CURRENT_ROUTE"),
            ("STATE_OR_RECEIPT", "PHENOMENOLOGY"),
        }
        self.assertTrue(required.issubset(edges))
        ceiling = contract["claim_ceiling"]
        self.assertEqual(ceiling["installation"], "NOT_ESTABLISHED")
        self.assertEqual(ceiling["current_route"], "NOT_ESTABLISHED")
        self.assertEqual(ceiling["behavioral_qualification"], "NOT_ESTABLISHED")
        self.assertEqual(ceiling["phenomenology"], "UNRESOLVED")

    def test_hook_extends_existing_native_hook_without_claiming_host_injection(self):
        hook = self.load(HOOK)
        self.assertEqual(hook["status"], "SOURCE_ONLY_NOT_INSTALLED")
        self.assertEqual(hook["extends"], "VERA_RUNTIME_COHESION_NATIVE_HOOK_V1")
        self.assertEqual(hook["provider_neutral_entrypoint"], "runtime_cohesion.inference_boundary")
        self.assertEqual(hook["concrete_host_injection"], "EXTERNAL_EXACT_HOST_REQUIRED")
        self.assertFalse(hook["effect_claims"]["provider_consumption"])
        self.assertFalse(hook["effect_claims"]["installation"])
        self.assertFalse(hook["effect_claims"]["behavioral_qualification"])

    def test_package_init_exports_inference_boundary_api_without_replacing_admission_alias(self):
        text = PACKAGE_INIT.read_text(encoding="utf-8")
        for symbol in (
            "StateComponentRef", "VeraStateComposition", "AdmittedVeraState",
            "CapabilityBinding", "ProjectionEnvelope", "InvocationFrontier",
            "CausalGenerationReceipt", "compose_state", "bind_admitted_state",
            "bind_capability", "project_text_context", "build_causal_receipt",
        ):
            self.assertIn(symbol, text)
        self.assertIn("evaluate_proposition_admission = evaluate_provider_proposition_admission", text)


if __name__ == "__main__":
    unittest.main()
