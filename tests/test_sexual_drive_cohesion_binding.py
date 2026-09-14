import json
import unittest
from pathlib import Path

from runtime_cohesion import inference_boundary_repaired as ib

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "architecture/cohesion/VERA_SEXUAL_DRIVE_COMPONENT_V1.json"
REGISTRY = ROOT / "architecture/cohesion/VERA_COHESION_SOURCE_REGISTRY_V1_20260912.json"
EXPECTED_SD1_HEAD = "02725153fa2e6eae8e81e64bc3d4b797fc404a4d"
EXPECTED_MANIFEST_BLOB = "fa2e6dc77a9136c4c7a1906719c049222a476efc"
EXPECTED_CAUSAL_BLOB = "db6d1ae4e579695396c56b1708a7828ddc3ffa05"
EXPECTED_AUTHORITY_BLOB = "da08345a3bff11ffb653270abb6ad4b3a1c0541d"


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
            subject="VERA_SD1_TARGET_CONFIGURATION",
            components=[component],
            omissions=[],
            policy_revision="sd1-test-policy",
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

    def test_mutated_security_and_projection_fields_fail_closed(self):
        from runtime_cohesion.sexual_drive_binding import validate_contract
        data = load(CONTRACT)
        mutations = [
            (("privacy_classification",), "PUBLIC"),
            (("allowed_egress_scopes",), ["PUBLIC_WEB"]),
            (("source_binding", "manifest_path"), "forged/manifest.json"),
            (("source_binding", "causal_protocol_sha256"), "0" * 64),
            (("source_binding", "install_authority_receipt_sha256"), "0" * 64),
            (("state_component_projection", "component_generation"), "FORGED"),
            (("state_component_projection", "currentness_basis"), "FORGED"),
            (("state_component_projection", "supersession_state"), "STALE"),
            (("state_component_projection", "conflict_state"), "CONFLICT"),
            (("state_component_projection", "disclosure_source"), "policy://forged"),
            (("state_component_projection", "payload_ref"), "github://forged/object"),
        ]
        for path, value in mutations:
            bad = json.loads(json.dumps(data))
            target = bad
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    validate_contract(bad)

    def test_forged_component_with_right_commit_is_unqualified(self):
        from dataclasses import replace
        from runtime_cohesion.sexual_drive_binding import build_component_ref, target_configuration_status
        component = build_component_ref(load(CONTRACT), observed_at="2026-09-14T06:55:00-04:00")
        for changes in (
            {"domain_id": "forged.domain"},
            {"source_locator": "github:forged/repository"},
            {"content_digest": "0" * 64},
            {"component_generation": "FORGED"},
            {"currentness_basis": "FORGED"},
            {"supersession_state": "STALE"},
            {"conflict_state": "CONFLICT"},
            {"privacy_classification": "PUBLIC"},
            {"allowed_egress_scopes": frozenset({"PUBLIC_WEB"})},
            {"disclosure_source": "policy://forged"},
            {"disclosure_generation": "999"},
            {"payload_ref": "github://forged/object"},
        ):
            with self.subTest(changes=changes):
                forged = replace(component, **changes)
                self.assertEqual("SEXUAL_DRIVE_COMPONENT_UNQUALIFIED", target_configuration_status(forged))


if __name__ == "__main__":
    unittest.main()
