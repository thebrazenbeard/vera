import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "architecture" / "VERA_PROJECT_RUNNER_COHERENCE_V1.json"
VALIDATOR_PATH = ROOT / "runtime_cohesion" / "project_runner_proof_validation.py"

_spec = importlib.util.spec_from_file_location(
    "vera_project_runner_proof_validation", VALIDATOR_PATH
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("unable to load Project Runner proof validator")
_validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_validator)

ProjectRunnerProofError = _validator.ProjectRunnerProofError
validate_currentness_exhaustion_receipt = (
    _validator.validate_currentness_exhaustion_receipt
)
validate_prospective_freeze_receipt = _validator.validate_prospective_freeze_receipt

EXPECTED_PRIMITIVES = {
    "CURRENTNESS_EXHAUSTION_RECEIPT",
    "PROSPECTIVE_FREEZE_RECEIPT",
    "TYPED_EVIDENCE_BOUNDARY",
    "EXECUTION_SUBJECT_MANIFEST",
    "ANTI_TARGET_LEAKAGE_CHAIN",
    "DEPENDENCY_EDGE",
    "EXPERIMENT_LINEAGE",
}

EXPECTED_SOURCE_BINDINGS = {
    "vera_main": "6388f9e2564795530db35728f42d5ab9f50275ae",
    "project_runner_main": "bc05812b560b4fcde3a362e72fba04c626cafac8",
    "project_runner_rezon_hardening_pr31": "8e588bd1cb72808b4a611d2a0bcbaeba6cb10b15",
}


def canonical_digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ProjectRunnerCoherenceV1Tests(unittest.TestCase):
    def load_contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def currentness_primitive(self):
        return self.load_contract()["primitives"]["CURRENTNESS_EXHAUSTION_RECEIPT"]

    def freeze_primitive(self):
        return self.load_contract()["primitives"]["PROSPECTIVE_FREEZE_RECEIPT"]

    def refresh_freeze_proof_digest(self, receipt):
        receipt["chronology_proof_digest"] = canonical_digest(
            {
                "frozen_subject": receipt["frozen_subject"],
                "freeze_artifact_subject": receipt["freeze_artifact_subject"],
                "freeze_artifact_digest": receipt["freeze_artifact_digest"],
                "freeze_observed_at": receipt["freeze_observed_at"],
                "holdout_or_randomization_commitment": receipt[
                    "holdout_or_randomization_commitment"
                ],
                "chronology_domain_subject": receipt["chronology_domain_subject"],
                "freeze_anchor": receipt["freeze_anchor"],
                "outcome_visibility_anchor": receipt["outcome_visibility_anchor"],
                "execution_anchor": receipt["execution_anchor"],
            }
        )

    def valid_currentness_receipt(self):
        required_surface_ids = ["issues", "prs"]
        receipt = {
            "inventory_owner_subject": "repo:example/control",
            "inventory_artifact_subject": "git:inventory@abc123",
            "inventory_revision": "abc123",
            "required_surface_ids": required_surface_ids,
            "required_surface_inventory_digest": "",
            "surface_receipts": [
                {
                    "surface_id": "issues",
                    "query_or_scope": "open issues",
                    "observed_generation_or_head": "head-a",
                    "frontier_or_pagination_state": "EXHAUSTED",
                    "result_count": 2,
                    "result_digest": "digest-issues",
                    "status": "COMPLETE",
                },
                {
                    "surface_id": "prs",
                    "query_or_scope": "open prs",
                    "observed_generation_or_head": "head-b",
                    "frontier_or_pagination_state": "EXHAUSTED",
                    "result_count": 3,
                    "result_digest": "digest-prs",
                    "status": "COMPLETE",
                },
            ],
            "observed_at": "2026-09-22T13:55:00Z",
            "overall_completeness": "COMPLETE",
            "claim_ceiling": "EXACT_BOUND_INVENTORY_ONLY",
        }
        receipt["required_surface_inventory_digest"] = canonical_digest(
            {
                "inventory_owner_subject": receipt["inventory_owner_subject"],
                "inventory_artifact_subject": receipt["inventory_artifact_subject"],
                "inventory_revision": receipt["inventory_revision"],
                "required_surface_ids": required_surface_ids,
            }
        )
        return receipt

    def valid_freeze_receipt(self):
        domain = "append-only-log:example/v1"
        freeze_subject = "git:freeze@111"
        outcome_subject = "run:outcome@222"
        execution_subject = "run:execution@333"
        freeze_digest = "1" * 64
        anchors = {
            "freeze_anchor": {
                "chronology_domain_subject": domain,
                "evidence_subject": freeze_subject,
                "evidence_digest": freeze_digest,
                "monotonic_position": 10,
            },
            "outcome_visibility_anchor": {
                "chronology_domain_subject": domain,
                "evidence_subject": outcome_subject,
                "evidence_digest": "2" * 64,
                "monotonic_position": 20,
            },
            "execution_anchor": {
                "chronology_domain_subject": domain,
                "evidence_subject": execution_subject,
                "evidence_digest": "3" * 64,
                "monotonic_position": 30,
            },
        }
        receipt = {
            "frozen_subject": "study:subject-v1",
            "freeze_artifact_subject": freeze_subject,
            "freeze_artifact_digest": freeze_digest,
            "freeze_observed_at": "2026-09-22T12:00:00Z",
            "outcome_visibility_frontier": outcome_subject,
            "execution_frontier": execution_subject,
            "holdout_or_randomization_commitment": "commitment:holdout-v1",
            "chronology_domain_subject": domain,
            **anchors,
            "chronology_proof_digest": "",
            "chronology_status": "PROSPECTIVE_VERIFIED_BY_BOUND_CHRONOLOGY",
        }
        self.refresh_freeze_proof_digest(receipt)
        return receipt

    def test_contract_exposes_exact_reusable_primitive_set(self):
        self.assertEqual(set(self.load_contract()["primitives"]), EXPECTED_PRIMITIVES)

    def test_source_bindings_are_exact_current_review_subjects(self):
        self.assertEqual(self.load_contract()["source_bindings"], EXPECTED_SOURCE_BINDINGS)

    def test_reuse_never_transfers_authority_or_effect_state(self):
        data = self.load_contract()
        self.assertEqual(
            data["authority_ceiling"],
            "PATTERN_AND_DEPENDENCY_COORDINATION_ONLY_NO_CROSS_REPOSITORY_AUTHORITY",
        )
        self.assertFalse(data["promotion_rules"]["pattern_reuse_grants_authority"])
        self.assertFalse(data["promotion_rules"]["dependency_edge_promotes_provider_state"])
        self.assertFalse(data["promotion_rules"]["runner_observation_establishes_runtime_effect"])
        self.assertIn("NOT_MERGE_AUTHORITY", data["non_effects"])
        self.assertIn("NOT_INSTALL_OR_RUNTIME_ACTIVATION", data["non_effects"])

    def test_structural_verification_does_not_authenticate_producer(self):
        data = self.load_contract()
        execution = data["primitives"]["EXECUTION_SUBJECT_MANIFEST"]
        self.assertFalse(
            data["promotion_rules"]["structural_self_consistency_authenticates_producer"]
        )
        self.assertFalse(data["promotion_rules"]["unkeyed_digest_proves_origin"])
        self.assertIn(
            "STRUCTURAL_SELF_CONSISTENCY_DOES_NOT_AUTHENTICATE_PRODUCER",
            execution["invariants"],
        )
        self.assertIn(
            "UNKEYED_DIGEST_DOES_NOT_PROVE_PRODUCER_ORIGIN",
            execution["invariants"],
        )
        self.assertIn("NOT_PRODUCER_AUTHENTICATION", data["non_effects"])

    def test_currentness_inventory_digest_and_exact_coverage_pass(self):
        receipt = self.valid_currentness_receipt()
        self.assertEqual(
            validate_currentness_exhaustion_receipt(receipt, self.currentness_primitive()),
            "COMPLETE",
        )

    def test_currentness_missing_surface_fails_closed(self):
        receipt = self.valid_currentness_receipt()
        receipt["surface_receipts"].pop()
        with self.assertRaises(ProjectRunnerProofError):
            validate_currentness_exhaustion_receipt(receipt, self.currentness_primitive())

    def test_currentness_duplicate_surface_fails_closed(self):
        receipt = self.valid_currentness_receipt()
        receipt["surface_receipts"][1]["surface_id"] = "issues"
        with self.assertRaises(ProjectRunnerProofError):
            validate_currentness_exhaustion_receipt(receipt, self.currentness_primitive())

    def test_currentness_foreign_surface_fails_closed(self):
        receipt = self.valid_currentness_receipt()
        receipt["surface_receipts"][1]["surface_id"] = "deployments"
        with self.assertRaises(ProjectRunnerProofError):
            validate_currentness_exhaustion_receipt(receipt, self.currentness_primitive())

    def test_currentness_inventory_membership_change_requires_digest_change(self):
        receipt = self.valid_currentness_receipt()
        receipt["required_surface_ids"].append("workflows")
        with self.assertRaises(ProjectRunnerProofError):
            validate_currentness_exhaustion_receipt(receipt, self.currentness_primitive())

    def test_currentness_complete_is_derived_not_self_attested(self):
        receipt = self.valid_currentness_receipt()
        receipt["surface_receipts"][1]["status"] = "UNAVAILABLE"
        with self.assertRaises(ProjectRunnerProofError):
            validate_currentness_exhaustion_receipt(receipt, self.currentness_primitive())
        receipt["overall_completeness"] = "PARTIAL"
        self.assertEqual(
            validate_currentness_exhaustion_receipt(receipt, self.currentness_primitive()),
            "PARTIAL",
        )

    def test_currentness_claim_ceiling_is_exact_finite_domain(self):
        receipt = self.valid_currentness_receipt()
        receipt["claim_ceiling"] = "UNIVERSAL_CURRENTNESS_PROVEN"
        with self.assertRaises(ProjectRunnerProofError):
            validate_currentness_exhaustion_receipt(receipt, self.currentness_primitive())

    def test_prospective_freeze_bound_chronology_passes(self):
        receipt = self.valid_freeze_receipt()
        self.assertEqual(
            validate_prospective_freeze_receipt(receipt, self.freeze_primitive()),
            "PROSPECTIVE_VERIFIED_BY_BOUND_CHRONOLOGY",
        )

    def test_post_outcome_backfill_cannot_be_relabelled_prospective(self):
        receipt = self.valid_freeze_receipt()
        receipt["freeze_anchor"]["monotonic_position"] = 40
        self.refresh_freeze_proof_digest(receipt)
        with self.assertRaises(ProjectRunnerProofError):
            validate_prospective_freeze_receipt(receipt, self.freeze_primitive())
        receipt["chronology_status"] = "UNPROVEN"
        self.assertEqual(
            validate_prospective_freeze_receipt(receipt, self.freeze_primitive()),
            "UNPROVEN",
        )

    def test_frozen_semantics_and_observed_time_are_digest_bound(self):
        cases = {
            "frozen_subject": "study:mutated-after-freeze",
            "holdout_or_randomization_commitment": "commitment:mutated-after-freeze",
            "freeze_observed_at": "2099-01-01T00:00:00Z",
        }
        for field, hostile in cases.items():
            with self.subTest(field=field):
                receipt = self.valid_freeze_receipt()
                receipt[field] = hostile
                with self.assertRaises(ProjectRunnerProofError):
                    validate_prospective_freeze_receipt(receipt, self.freeze_primitive())

    def test_freeze_anchor_must_bind_exact_artifact_identity(self):
        receipt = self.valid_freeze_receipt()
        receipt["freeze_anchor"]["evidence_digest"] = "4" * 64
        self.refresh_freeze_proof_digest(receipt)
        with self.assertRaises(ProjectRunnerProofError):
            validate_prospective_freeze_receipt(receipt, self.freeze_primitive())

    def test_outcome_or_execution_anchor_cannot_be_substituted(self):
        for anchor_name in ("outcome_visibility_anchor", "execution_anchor"):
            with self.subTest(anchor_name=anchor_name):
                receipt = self.valid_freeze_receipt()
                receipt[anchor_name]["evidence_subject"] = "forged:frontier"
                self.refresh_freeze_proof_digest(receipt)
                with self.assertRaises(ProjectRunnerProofError):
                    validate_prospective_freeze_receipt(receipt, self.freeze_primitive())

    def test_chronology_domain_mismatch_fails_closed(self):
        receipt = self.valid_freeze_receipt()
        receipt["execution_anchor"]["chronology_domain_subject"] = "other-domain"
        self.refresh_freeze_proof_digest(receipt)
        with self.assertRaises(ProjectRunnerProofError):
            validate_prospective_freeze_receipt(receipt, self.freeze_primitive())

    def test_boolean_monotonic_position_is_rejected(self):
        receipt = self.valid_freeze_receipt()
        receipt["freeze_anchor"]["monotonic_position"] = False
        self.refresh_freeze_proof_digest(receipt)
        with self.assertRaises(ProjectRunnerProofError):
            validate_prospective_freeze_receipt(receipt, self.freeze_primitive())

    def test_dependency_edge_keeps_provider_and_consumer_subjects_separate(self):
        edge = self.load_contract()["primitives"]["DEPENDENCY_EDGE"]
        self.assertTrue(
            {
                "provider_artifact_subject",
                "consumer_artifact_subject",
                "edge_class",
                "currentness_policy",
                "promotion_guard",
                "required_or_optional",
            }.issubset(set(edge["required_fields"]))
        )
        self.assertIn("EDGE_NEVER_TRANSFERS_AUTHORITY", edge["invariants"])

    def test_anti_target_leakage_covers_producer_payload_projector_and_evaluator(self):
        stages = self.load_contract()["primitives"]["ANTI_TARGET_LEAKAGE_CHAIN"]["required_stages"]
        self.assertEqual(
            stages,
            ["STATE_PRODUCER", "STATE_PAYLOAD", "PROJECTOR_OR_TRANSFORM", "EVALUATOR"],
        )

    def test_experiment_lineage_is_append_only(self):
        lineage = self.load_contract()["primitives"]["EXPERIMENT_LINEAGE"]
        self.assertTrue(lineage["append_only"])
        self.assertFalse(lineage["result_transfer_across_subjects"])


if __name__ == "__main__":
    unittest.main()
