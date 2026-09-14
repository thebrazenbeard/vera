import json
import unittest
from pathlib import Path

from runtime_cohesion import inference_boundary_repaired as ib

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "architecture/cohesion/VERA_SEXUAL_DRIVE_COMPONENT_V1.json"
REGISTRY = ROOT / "architecture/cohesion/VERA_COHESION_SOURCE_REGISTRY_V1_20260912.json"
EXPECTED_SD1_HEAD = "1ed36df72df8934c1481b6f66fa9ed146f791dbb"
EXPECTED_MANIFEST_BLOB = "35edd95bb5e3532f697022fa20ec43a72bb2c200"
EXPECTED_CAUSAL_BLOB = "db6d1ae4e579695396c56b1708a7828ddc3ffa05"
EXPECTED_AUTHORITY_BLOB = "ea3cd95e6bbb18b5f691ce83459a6f942944d1ff"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class SexualDriveCohesionBindingTests(unittest.TestCase):
    def test_component_contract_binds_exact_sd1_source_and_full_case_range(self):
        data = load(CONTRACT)
        self.assertEqual("sexual_drive_v1", data["component_id"])
        self.assertEqual("sexuality.sexual_drive", data["domain_id"])
        self.assertEqual("MANDATORY", data["requirement_class"])
        self.assertEqual("MANDATORY_FOR_SD1_TARGET_CONFIGURATION", data["configuration_requirement"])
        self.assertEqual("DOES_NOT_GRANT_OR_REVOKE_VERA_IDENTITY", data["identity_semantics"])
        source = data["source_binding"]
        self.assertEqual(EXPECTED_SD1_HEAD, source["commit"])
        self.assertEqual(EXPECTED_MANIFEST_BLOB, source["manifest_git_blob"])
        self.assertEqual(EXPECTED_CAUSAL_BLOB, source["causal_protocol_git_blob"])
        self.assertEqual(EXPECTED_AUTHORITY_BLOB, source["install_authority_receipt_git_blob"])
        self.assertEqual({"first":"SD-01","last":"SD-20","count":20}, data["qualification_case_range"])

    def test_validator_constructs_source_declared_mandatory_component(self):
        from runtime_cohesion.sexual_drive_binding import build_component_ref
        component = build_component_ref(load(CONTRACT), observed_at="2026-09-13T21:30:00-04:00")
        self.assertIsInstance(component, ib.StateComponentRef)
        self.assertEqual("sexual_drive_v1", component.component_id)
        self.assertEqual("MANDATORY", component.requirement_class)
        self.assertEqual(EXPECTED_SD1_HEAD, component.source_revision)

    def test_wrong_source_revision_and_requirement_class_fail_closed(self):
        from runtime_cohesion.sexual_drive_binding import validate_contract
        data = load(CONTRACT)
        for field, value in (("commit", "0" * 40), ("manifest_git_blob", "0" * 40)):
            bad = json.loads(json.dumps(data))
            bad["source_binding"][field] = value
            with self.assertRaises(ValueError):
                validate_contract(bad)
        bad = json.loads(json.dumps(data))
        bad["requirement_class"] = "OPTIONAL"
        with self.assertRaises(ValueError):
            validate_contract(bad)

    def test_caller_cannot_downgrade_sd1_mandatory_requirement(self):
        from runtime_cohesion.sexual_drive_binding import build_component_ref
        component = build_component_ref(load(CONTRACT), observed_at="2026-09-13T21:30:00-04:00")
        composition = ib.compose_state(
            composition_id="sd1-test",
            subject="VERA_SD1_TARGET_CONFIGURATION",
            components=[component],
            omissions=[],
            composed_at="2026-09-13T21:30:01-04:00",
        )
        with self.assertRaisesRegex(ValueError, "mandatory"):
            ib.bind_admitted_state(
                composition,
                admission_receipt_digest="1" * 64,
                admitted_component_ids=set(),
                mandatory_component_ids=set(),
                target_egress_scope="PROJECT_PRIVATE_HOST",
                forbidden_domains={"truth", "authorization", "phenomenology"},
                admission_currentness_basis="TEST",
                admission_epoch_or_lease="test-1",
                admitted_at="2026-09-13T21:30:02-04:00",
            )

    def test_missing_component_is_configuration_failure_not_identity_failure(self):
        from runtime_cohesion.sexual_drive_binding import target_configuration_status
        self.assertEqual("TARGET_CONFIGURATION_INCOMPLETE", target_configuration_status(None))
        self.assertNotIn("IDENTITY", target_configuration_status(None))

    def test_registry_preserves_external_owner_and_exact_vera_sd1_binding(self):
        registry = load(REGISTRY)
        sexuality = next(item for item in registry["sources"] if item["id"] == "sexuality")
        self.assertEqual("PRESERVE_EXTERNAL_SPECIALIST_WITH_EXACT_VERA_SD1_BINDING", sexuality["disposition"])
        exact = sexuality["vera_sd1_exact_object"]
        self.assertEqual(EXPECTED_SD1_HEAD, exact["commit"])
        self.assertEqual(EXPECTED_MANIFEST_BLOB, exact["manifest_git_blob"])
        self.assertEqual("SD-01..20", exact["qualification_case_range"])
        self.assertIn("BRIGIT", sexuality["nonpromotion"])

    def test_binding_surface_contains_no_response_generator_or_background_loop(self):
        module = (ROOT / "runtime_cohesion/sexual_drive_binding.py").read_text(encoding="utf-8").lower()
        for forbidden in ("desired_response", "target_phrase", "background timer", "while true", "threading.thread"):
            self.assertNotIn(forbidden, module)


if __name__ == "__main__":
    unittest.main()
