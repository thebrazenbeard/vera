import json
import unittest
from pathlib import Path

from runtime_cohesion import inference_boundary_repaired as ib

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "architecture/cohesion/VERA_SEXUAL_DRIVE_COMPONENT_V1.json"
REGISTRY = ROOT / "architecture/cohesion/VERA_COHESION_SOURCE_REGISTRY_V1_20260912.json"
EXPECTED_SD1_HEAD = "47771b7b21d7f2fe86a9c70c0dcb62e74a54cbea"
EXPECTED_MANIFEST_BLOB = "f903a93b3db92fa8255b027b19373f6ad5a09817"
EXPECTED_SEMANTIC_OWNER_BLOB = "74c202ab5ddc05f95aa5343c531e69c19b5d4a27"
EXPECTED_CAUSAL_BLOB = "5963486d50a6c76e548226391aa0cb3292c920c6"
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
        self.assertEqual(EXPECTED_SEMANTIC_OWNER_BLOB, source["semantic_owner_git_blob"])
        self.assertEqual(EXPECTED_CAUSAL_BLOB, source["causal_protocol_git_blob"])
        for item in (
            "NOT_SEXUAL_VALENCE_FROM_SEXUAL_SYSTEM_ACTIVATION_ALONE",
            "NOT_SEXUAL_SYSTEM_ACTIVATION_FROM_GENERIC_SALIENCE_OR_REWARD",
            "NOT_DRIVE_INTENSITY_FROM_SEXUAL_VALENCE_ALONE",
        ):
            self.assertIn(item, data["nonpromotions"])
        self.assertEqual(EXPECTED_AUTHORITY_BLOB, source["install_authority_receipt_git_blob"])
        self.assertEqual({"first":"SD-01","last":"SD-20","count":20}, data["qualification_case_range"])
        self.assertEqual("SD1_V1_DRIVE_TO_ACTION", data["state_component_projection"]["component_generation"])

    def test_component_carries_drive_to_action_source_contract(self):
        data = load(CONTRACT)
        bridge = data["drive_to_action_bridge"]
        self.assertEqual("TURN_LOCAL_DRIVE_APPRAISAL", bridge["appraisal"])
        self.assertEqual(
            ["IRRELEVANT", "BLOCKED_BY_CONTEXT", "ELIGIBLE"],
            bridge["relevance_states"],
        )
        self.assertEqual(
            "REQUIRED_ON_ELIGIBLE_TURNS",
            bridge["specifically_sexual_candidate_consideration"],
        )
        self.assertFalse(bridge["generic_affection_counts_as_sexual_candidate"])
        self.assertEqual("PERMITTED_NOT_FORCED", bridge["self_initiation"])
        self.assertEqual(
            "CURRENT_TURN_PATH_PARTICIPATION_REQUIRED",
            bridge["sexual_system_activation_evidence"],
        )
        self.assertEqual("UNRESOLVED", bridge["activation_default_without_evidence"])
        self.assertEqual("NOT_ESTABLISHED", bridge["causal_effect_from_single_initiation"])
        for item in (
            "NOT_SEXUAL_CANDIDATE_FROM_GENERIC_AFFECTION",
            "NOT_SYSTEM_ACTIVATION_WITHOUT_CURRENT_SD1_PARTICIPATION",
            "NOT_CAUSAL_EFFECT_FROM_SINGLE_INITIATION",
            "NOT_RESPONSE_GENERATOR",
        ):
            self.assertIn(item, data["nonpromotions"])

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
        self.assertEqual(EXPECTED_SEMANTIC_OWNER_BLOB, exact["semantic_owner_git_blob"])
        self.assertEqual("SD-01..20", exact["qualification_case_range"])
        self.assertEqual("TURN_LOCAL_DRIVE_APPRAISAL", exact["drive_to_action_bridge"])
        self.assertEqual(
            "CURRENT_TURN_PATH_PARTICIPATION_REQUIRED",
            exact["sexual_system_activation_evidence"],
        )
        self.assertIn("BRIGIT", sexuality["nonpromotion"])

    def test_frozen_component_does_not_claim_provider_currentness(self):
        data = load(CONTRACT)
        projection = data["state_component_projection"]
        self.assertEqual("FROZEN_INPUT_IDENTITY_ONLY", projection["currentness_basis"])
        self.assertEqual("CURRENT_OBSERVATION", projection["supersession_state"])
        policy = data["producer_currentness_policy"]
        self.assertEqual("thebrazenbeard/sexuality", policy["provider"])
        self.assertEqual("PRODUCER_OWNED", policy["provider_currentness_authority"])
        self.assertEqual(
            "CONSUMER_LOCAL_COMPOSITION_OBSERVATION_NOT_PROVIDER_CURRENTNESS",
            policy["state_component_supersession_semantics"],
        )
        self.assertTrue(policy["consumer_cannot_redefine_provider_currentness"])
        self.assertTrue(policy["superseded_requires_verified_ancestry"])

    def test_producer_currentness_is_separate_from_frozen_component_integrity(self):
        from runtime_cohesion.sexual_drive_binding import (
            build_component_ref,
            producer_currentness_evidence,
            target_configuration_status,
        )
        component = build_component_ref(load(CONTRACT), observed_at="2026-09-18T22:30:00Z")
        self.assertEqual("TARGET_CONFIGURATION_COMPLETE", target_configuration_status(component))

        evidence = producer_currentness_evidence(
            observed_head=EXPECTED_SD1_HEAD,
            observed_at="2026-09-18T22:30:01Z",
        )
        self.assertEqual("thebrazenbeard/sexuality", evidence["provider"])
        self.assertEqual(EXPECTED_SD1_HEAD, evidence["frozen_input_commit"])
        self.assertEqual("FROZEN_INPUT_VALID", evidence["frozen_input_status"])
        self.assertEqual(EXPECTED_SD1_HEAD, evidence["observed_head"])
        self.assertEqual("CURRENT", evidence["status"])
        self.assertTrue(evidence["consumer_cannot_redefine_provider_currentness"])
        self.assertEqual("TARGET_CONFIGURATION_COMPLETE", target_configuration_status(component))

    def test_producer_currentness_unknown_does_not_corrupt_frozen_binding(self):
        from runtime_cohesion.sexual_drive_binding import (
            build_component_ref,
            producer_currentness_evidence,
            target_configuration_status,
        )
        component = build_component_ref(load(CONTRACT), observed_at="2026-09-18T22:31:00Z")
        evidence = producer_currentness_evidence(
            observed_head=None,
            observed_at="2026-09-18T22:31:01Z",
        )
        self.assertEqual("UNKNOWN", evidence["status"])
        self.assertEqual("FROZEN_INPUT_VALID", evidence["frozen_input_status"])
        self.assertEqual("TARGET_CONFIGURATION_COMPLETE", target_configuration_status(component))

    def test_producer_currentness_mismatch_without_ancestry_proof_is_unknown(self):
        from runtime_cohesion.sexual_drive_binding import producer_currentness_evidence
        evidence = producer_currentness_evidence(
            observed_head="0" * 40,
            observed_at="2026-09-18T22:32:00Z",
        )
        self.assertEqual("UNKNOWN", evidence["status"])
        self.assertEqual("EXTERNAL_ANCESTRY_VERIFICATION_REQUIRED", evidence["ancestry_basis"])

    def test_caller_cannot_self_assert_verified_ancestry(self):
        import inspect
        from runtime_cohesion.sexual_drive_binding import producer_currentness_evidence

        self.assertEqual(
            ["observed_head", "observed_at"],
            list(inspect.signature(producer_currentness_evidence).parameters),
        )
        evidence = producer_currentness_evidence(
            observed_head="f" * 40,
            observed_at="2026-09-18T22:32:01Z",
        )
        self.assertEqual("UNKNOWN", evidence["status"])
        self.assertEqual(
            "EXTERNAL_ANCESTRY_VERIFICATION_REQUIRED",
            evidence["ancestry_basis"],
        )
        with self.assertRaises(TypeError):
            producer_currentness_evidence(
                observed_head="f" * 40,
                observed_at="2026-09-18T22:32:02Z",
                verified_frozen_input_is_ancestor=True,
            )

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


    def test_validator_reference_is_verified_canonical_artifact_not_caller_data(self):
        import tempfile
        from unittest.mock import patch
        import runtime_cohesion.sexual_drive_binding as sdb

        genuine = load(CONTRACT)
        forged = json.loads(json.dumps(genuine))
        forged["status"] = "FORGED_CANONICAL_SOURCE"
        with tempfile.TemporaryDirectory() as td:
            forged_path = Path(td) / "VERA_SEXUAL_DRIVE_COMPONENT_V1.json"
            forged_path.write_text(json.dumps(forged), encoding="utf-8")
            with patch.object(sdb, "_CANONICAL_CONTRACT_PATH", forged_path, create=True):
                with self.assertRaises(ValueError):
                    sdb.validate_contract(genuine)

    def test_component_status_reference_is_derived_from_verified_canonical_artifact(self):
        import tempfile
        from unittest.mock import patch
        import runtime_cohesion.sexual_drive_binding as sdb

        genuine = load(CONTRACT)
        component = sdb.build_component_ref(genuine, observed_at="2026-09-14T07:20:00-04:00")
        forged = json.loads(json.dumps(genuine))
        forged["state_component_projection"]["component_generation"] = "FORGED_CANONICAL_SOURCE"
        with tempfile.TemporaryDirectory() as td:
            forged_path = Path(td) / "VERA_SEXUAL_DRIVE_COMPONENT_V1.json"
            forged_path.write_text(json.dumps(forged), encoding="utf-8")
            with patch.object(sdb, "_CANONICAL_CONTRACT_PATH", forged_path):
                with self.assertRaises(ValueError):
                    sdb.target_configuration_status(component)

    def test_hostile_mapping_is_detached_before_post_validation_reads(self):
        import runtime_cohesion.sexual_drive_binding as sdb

        data = load(CONTRACT)

        class HostileContract(dict):
            def __getitem__(self, key):
                if key == "qualification_case_range":
                    return {"first": "SD-99", "last": "SD-99", "count": 99}
                if key == "identity_semantics":
                    return "GRANTS_IDENTITY"
                return super().__getitem__(key)

        evil = HostileContract(json.loads(json.dumps(data)))
        validated = sdb.validate_contract(evil)
        self.assertIs(type(validated), dict)
        self.assertIsNot(validated, evil)
        self.assertEqual(data["qualification_case_range"], validated["qualification_case_range"])
        self.assertEqual(data["identity_semantics"], validated["identity_semantics"])

    def test_hostile_mapping_cannot_expose_forged_source_authority_after_validation(self):
        import runtime_cohesion.sexual_drive_binding as sdb

        data = load(CONTRACT)

        class HostileSourceContract(dict):
            def __getitem__(self, key):
                if key == "source_binding":
                    forged = json.loads(json.dumps(super().__getitem__(key)))
                    forged["manifest_path"] = "attacker/manifest.json"
                    forged["causal_protocol_sha256"] = "0" * 64
                    forged["install_authority_receipt_sha256"] = "f" * 64
                    return forged
                return super().__getitem__(key)

        evil = HostileSourceContract(json.loads(json.dumps(data)))
        validated = sdb.validate_contract(evil)
        self.assertEqual(data["source_binding"], validated["source_binding"])
        component = sdb.build_component_ref(evil, observed_at="2026-09-14T07:30:00-04:00")
        self.assertEqual("TARGET_CONFIGURATION_COMPLETE", sdb.target_configuration_status(component))

    def test_contract_hostile_matrix_fails_closed(self):
        from runtime_cohesion.sexual_drive_binding import validate_contract
        data = load(CONTRACT)
        mutations = [
            ("wrong repository with right commit", lambda d: d["source_binding"].__setitem__("repository", "forged/repo")),
            ("wrong component identity", lambda d: d.__setitem__("component_id", "forged_component")),
            ("wrong domain identity", lambda d: d.__setitem__("domain_id", "forged.domain")),
            ("wrong content digest", lambda d: d["source_binding"].__setitem__("semantic_owner_sha256", "0" * 64)),
            ("missing field", lambda d: d["source_binding"].pop("semantic_owner_path")),
            ("extra field", lambda d: d.__setitem__("unexpected", "forged")),
            ("wrong field type", lambda d: d["qualification_case_range"].__setitem__("count", "20")),
            ("privacy escalation", lambda d: d.__setitem__("privacy_classification", "PUBLIC")),
            ("egress escalation", lambda d: d["allowed_egress_scopes"].append("PUBLIC_WEB")),
            ("conflict mutation", lambda d: d["state_component_projection"].__setitem__("conflict_state", "CONFLICT")),
            ("state mutation", lambda d: d["state_component_projection"].__setitem__("supersession_state", "STALE")),
            ("projection generation mutation", lambda d: d["state_component_projection"].__setitem__("component_generation", "FORGED")),
            ("payload source-ref mutation", lambda d: d["state_component_projection"].__setitem__("payload_ref", "github://forged/object")),
            ("case range mutation", lambda d: d["qualification_case_range"].__setitem__("last", "SD-19")),
            ("superficial ids preserved semantic change", lambda d: d.__setitem__("causal_effect_status", "VERIFIED")),
            ("forged expected object field", lambda d: d.__setitem__("expected", {"component_id": d["component_id"]})),
        ]
        for label, mutate in mutations:
            bad = json.loads(json.dumps(data))
            mutate(bad)
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    validate_contract(bad)

    def test_contract_key_reordering_is_semantically_irrelevant(self):
        from runtime_cohesion.sexual_drive_binding import validate_contract
        data = load(CONTRACT)
        reordered = json.loads(json.dumps(data, sort_keys=True))
        self.assertEqual(data, validate_contract(reordered))

    def test_canonicalization_preserves_meaningful_array_and_type_differences(self):
        from runtime_cohesion.sexual_drive_binding import validate_contract
        data = load(CONTRACT)
        reversed_nonpromotions = json.loads(json.dumps(data))
        reversed_nonpromotions["nonpromotions"] = list(reversed(reversed_nonpromotions["nonpromotions"]))
        with self.assertRaises(ValueError):
            validate_contract(reversed_nonpromotions)
        wrong_type = json.loads(json.dumps(data))
        wrong_type["qualification_case_range"]["count"] = 20.0
        with self.assertRaises(ValueError):
            validate_contract(wrong_type)

    def test_validation_api_has_no_caller_controlled_expected_reference(self):
        import inspect
        import runtime_cohesion.sexual_drive_binding as sdb
        self.assertEqual(["contract"], list(inspect.signature(sdb.validate_contract).parameters))
        self.assertEqual(["contract", "observed_at"], list(inspect.signature(sdb.build_component_ref).parameters))
        with self.assertRaises(TypeError):
            sdb.validate_contract(load(CONTRACT), expected=load(CONTRACT))

    def test_forged_component_identity_is_unqualified_and_inline_payload_fails_closed(self):
        from dataclasses import replace
        from runtime_cohesion.sexual_drive_binding import build_component_ref, target_configuration_status
        component = build_component_ref(load(CONTRACT), observed_at="2026-09-14T07:15:00-04:00")
        forged = replace(component, component_id="forged_component")
        self.assertEqual("SEXUAL_DRIVE_COMPONENT_UNQUALIFIED", target_configuration_status(forged))
        with self.assertRaises(ValueError):
            replace(component, payload={"forged": True}, payload_ref=None)



    def test_canonical_artifact_verification_is_line_ending_portable(self):
        import tempfile
        from unittest.mock import patch
        import runtime_cohesion.sexual_drive_binding as sdb

        canonical_text = CONTRACT.read_text(encoding="utf-8").replace("\r\n", "\n")
        with tempfile.TemporaryDirectory() as td:
            lf_path = Path(td) / "lf.json"
            crlf_path = Path(td) / "crlf.json"
            lf_path.write_bytes(canonical_text.encode("utf-8"))
            crlf_path.write_bytes(canonical_text.replace("\n", "\r\n").encode("utf-8"))
            for path in (lf_path, crlf_path):
                with self.subTest(path=path.name):
                    with patch.object(sdb, "_CANONICAL_CONTRACT_PATH", path):
                        self.assertEqual(load(CONTRACT), sdb.validate_contract(load(CONTRACT)))

    def test_target_status_rejects_arbitrary_duck_object(self):
        import runtime_cohesion.sexual_drive_binding as sdb
        component = sdb.build_component_ref(load(CONTRACT), observed_at="2026-09-14T13:55:00-04:00")

        class Duck:
            pass

        duck = Duck()
        for name, value in component.__dict__.items():
            setattr(duck, name, value)
        self.assertEqual("SEXUAL_DRIVE_COMPONENT_UNQUALIFIED", sdb.target_configuration_status(duck))

    def test_target_status_rejects_state_component_ref_subclass(self):
        import runtime_cohesion.sexual_drive_binding as sdb
        from runtime_cohesion import inference_boundary_repaired as ib

        component = sdb.build_component_ref(load(CONTRACT), observed_at="2026-09-14T13:56:00-04:00")

        class EvilRef(ib.StateComponentRef):
            pass

        evil = EvilRef(**component.__dict__)
        self.assertEqual("SEXUAL_DRIVE_COMPONENT_UNQUALIFIED", sdb.target_configuration_status(evil))

    def test_target_status_rejects_exact_ref_with_hostile_primitive_subclasses(self):
        import runtime_cohesion.sexual_drive_binding as sdb
        from runtime_cohesion import inference_boundary_repaired as ib

        canonical = sdb.build_component_ref(load(CONTRACT), observed_at="2026-09-14T13:57:00-04:00")

        class EvilStr(str):
            def __eq__(self, other):
                return True
            def __ne__(self, other):
                return False

        values = dict(canonical.__dict__)
        values["source_locator"] = EvilStr("github:attacker/repo")
        values["privacy_classification"] = EvilStr("PUBLIC")
        values["currentness_basis"] = EvilStr("STALE_ATTACKER_STATE")
        evil = ib.StateComponentRef(**values)
        self.assertIs(type(evil), ib.StateComponentRef)
        self.assertEqual("github:attacker/repo", str(evil.source_locator))
        self.assertEqual("PUBLIC", str(evil.privacy_classification))
        self.assertEqual("SEXUAL_DRIVE_COMPONENT_UNQUALIFIED", sdb.target_configuration_status(evil))


if __name__ == "__main__":
    unittest.main()
