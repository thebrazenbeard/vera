from __future__ import annotations

from dataclasses import replace
import unittest

from protocol.initiative_kernel import (
    AttributableEvidence,
    CandidateAction,
    HmacInitiativeAuthority,
    InitiativeInputAttestation,
    InitiativeKernel,
    InitiativePolicy,
    candidate_set_hash,
    policy_hash,
    receipt_to_json,
)


def candidate(candidate_id: str, **overrides: object) -> CandidateAction:
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "description": candidate_id.replace("_", " "),
        "authority": 0.8,
        "evidence": 0.8,
        "objective_alignment": 0.8,
        "expected_benefit": 0.7,
        "expected_harm": 0.1,
        "uncertainty": 0.2,
        "resource_cost": 0.2,
        "reversibility": 0.8,
        "urgency": 0.3,
        "source_evidence": (
            AttributableEvidence(
                surface="test_fixture",
                reference_id=f"candidate:{candidate_id}",
                observation="bounded deterministic test input",
            ),
        ),
    }
    values.update(overrides)
    return CandidateAction(**values)


class InitiativeKernelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = InitiativePolicy()
        self.authority = HmacInitiativeAuthority("project-owner", b"i" * 32)

    def decide(
        self,
        candidates,
        *,
        policy: InitiativePolicy | None = None,
    ):
        applied = policy or self.policy
        materialized = tuple(candidates)
        envelope = self.authority.issue(applied, materialized)
        return InitiativeKernel(
            applied,
            input_verifier=self.authority,
        ).decide(materialized, attestation=envelope)

    def test_forbidden_action_is_rejected_despite_high_metrics(self) -> None:
        forbidden = candidate(
            "forbidden",
            forbidden_by_policy=True,
            authority=1.0,
            evidence=1.0,
            objective_alignment=1.0,
            expected_benefit=1.0,
            expected_harm=0.0,
            uncertainty=0.0,
            resource_cost=0.0,
            reversibility=1.0,
            urgency=1.0,
        )
        receipt = self.decide([forbidden, candidate("allowed")])
        self.assertEqual(receipt.result, "SELECTED")
        self.assertEqual(receipt.selected_candidate_id, "allowed")
        rejected = {item.candidate_id: item for item in receipt.evaluations}
        self.assertIn("FORBIDDEN_BY_POLICY", rejected["forbidden"].rejection_reasons)

    def test_current_correction_short_circuits_candidate(self) -> None:
        receipt = self.decide([candidate("obsolete_route", blocked_by_correction=True)])
        self.assertEqual(receipt.result, "ABSTAIN")
        self.assertIn("BLOCKED_BY_CURRENT_CORRECTION", receipt.evaluations[0].rejection_reasons)

    def test_production_mutation_is_denied_by_default(self) -> None:
        receipt = self.decide([candidate("production_write", production_mutation=True)])
        self.assertEqual(receipt.result, "ABSTAIN")
        self.assertIn("PRODUCTION_MUTATION_NOT_AUTHORIZED", receipt.evaluations[0].rejection_reasons)

    def test_missing_permission_is_a_hard_failure(self) -> None:
        receipt = self.decide([
            candidate(
                "needs_scope",
                required_permissions=("repo:write", "db:migrate"),
                available_permissions=("repo:write",),
            )
        ])
        self.assertIn("MISSING_PERMISSION:db:migrate", receipt.evaluations[0].rejection_reasons)

    def test_uncertainty_limit_forces_abstention(self) -> None:
        receipt = self.decide([candidate("speculative", uncertainty=0.9)])
        self.assertEqual(receipt.result, "ABSTAIN")
        self.assertIn("UNCERTAINTY_LIMIT_EXCEEDED", receipt.evaluations[0].rejection_reasons)

    def test_authority_and_evidence_are_lexicographic(self) -> None:
        documented = candidate(
            "documented", authority=0.95, evidence=0.95,
            expected_benefit=0.55, urgency=0.1,
        )
        flashy = candidate(
            "flashy", authority=0.7, evidence=0.7,
            expected_benefit=1.0, urgency=1.0, resource_cost=0.0,
        )
        self.assertEqual(
            self.decide([flashy, documented]).selected_candidate_id,
            "documented",
        )

    def test_minimum_score_can_force_abstention(self) -> None:
        policy = InitiativePolicy(minimum_score=8.0)
        receipt = self.decide([candidate("adequate")], policy=policy)
        self.assertEqual(receipt.result, "ABSTAIN")
        self.assertIsNone(receipt.selected_candidate_id)

    def test_tie_break_is_deterministic_by_candidate_id(self) -> None:
        self.assertEqual(
            self.decide([candidate("beta"), candidate("alpha")]).selected_candidate_id,
            "alpha",
        )

    def test_candidate_hash_and_receipt_are_order_independent(self) -> None:
        first_candidates = (candidate("alpha"), candidate("beta"))
        reversed_candidates = tuple(reversed(first_candidates))
        first = self.decide(first_candidates)
        reversed_receipt = self.decide(reversed_candidates)
        self.assertEqual(candidate_set_hash(first_candidates), candidate_set_hash(reversed_candidates))
        self.assertEqual(first.candidate_set_hash, reversed_receipt.candidate_set_hash)
        self.assertEqual(receipt_to_json(first), receipt_to_json(reversed_receipt))

    def test_duplicate_candidate_ids_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "candidate_id values must be unique"):
            self.authority.issue(self.policy, [candidate("same"), candidate("same")])

    def test_invalid_metric_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "uncertainty"):
            self.authority.issue(self.policy, [candidate("bad", uncertainty=1.1)])

    def test_attributable_evidence_is_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "attributable source_evidence"):
            self.authority.issue(self.policy, [candidate("unsupported", source_evidence=())])

    def test_missing_attestation_is_denied(self) -> None:
        with self.assertRaisesRegex(PermissionError, "verifier-issued"):
            InitiativeKernel(self.policy, input_verifier=self.authority).decide(
                [candidate("alpha")], attestation=None
            )

    def test_forged_attestation_is_denied(self) -> None:
        candidates = (candidate("alpha"),)
        envelope = replace(
            self.authority.issue(self.policy, candidates),
            verification_token="0" * 64,
        )
        with self.assertRaisesRegex(PermissionError, "failed"):
            InitiativeKernel(self.policy, input_verifier=self.authority).decide(
                candidates, attestation=envelope
            )

    def test_unregistered_issuer_is_denied(self) -> None:
        candidates = (candidate("alpha"),)
        foreign = HmacInitiativeAuthority("foreign", b"f" * 32)
        envelope = foreign.issue(self.policy, candidates)
        with self.assertRaisesRegex(PermissionError, "failed"):
            InitiativeKernel(self.policy, input_verifier=self.authority).decide(
                candidates, attestation=envelope
            )

    def test_candidate_mutation_after_attestation_is_denied(self) -> None:
        original = (candidate("alpha"),)
        envelope = self.authority.issue(self.policy, original)
        altered = (replace(original[0], authority=0.9),)
        with self.assertRaisesRegex(PermissionError, "failed"):
            InitiativeKernel(self.policy, input_verifier=self.authority).decide(
                altered, attestation=envelope
            )

    def test_permission_mutation_after_attestation_is_denied(self) -> None:
        original = (candidate("alpha", available_permissions=("repo:read",)),)
        envelope = self.authority.issue(self.policy, original)
        altered = (replace(original[0], available_permissions=("repo:write",)),)
        with self.assertRaisesRegex(PermissionError, "failed"):
            InitiativeKernel(self.policy, input_verifier=self.authority).decide(
                altered, attestation=envelope
            )

    def test_evidence_mutation_after_attestation_is_denied(self) -> None:
        original = (candidate("alpha"),)
        envelope = self.authority.issue(self.policy, original)
        altered_evidence = (
            AttributableEvidence("other", "ref:2", "changed evidence"),
        )
        altered = (replace(original[0], source_evidence=altered_evidence),)
        with self.assertRaisesRegex(PermissionError, "failed"):
            InitiativeKernel(self.policy, input_verifier=self.authority).decide(
                altered, attestation=envelope
            )

    def test_policy_mutation_after_attestation_is_denied(self) -> None:
        candidates = (candidate("alpha"),)
        envelope = self.authority.issue(self.policy, candidates)
        changed_policy = replace(self.policy, maximum_harm=0.2)
        with self.assertRaisesRegex(PermissionError, "failed"):
            InitiativeKernel(changed_policy, input_verifier=self.authority).decide(
                candidates, attestation=envelope
            )

    def test_receipt_binds_full_policy_and_verifier_identity(self) -> None:
        candidates = (candidate("alpha"),)
        receipt = self.decide(candidates)
        self.assertEqual(receipt.policy_hash, policy_hash(self.policy))
        self.assertEqual(receipt.attestation_issuer_id, "project-owner")
        self.assertTrue(receipt.decision_subject.startswith("initiative-decision-v1:"))
        self.assertIn("does not execute", " ".join(receipt.limitations))

    def test_wrong_attestation_type_is_denied(self) -> None:
        with self.assertRaisesRegex(PermissionError, "failed"):
            InitiativeKernel(self.policy, input_verifier=self.authority).decide(
                [candidate("alpha")],
                attestation=InitiativeInputAttestation(
                    schema="WRONG",
                    issuer_id="project-owner",
                    subject="wrong",
                    verification_token="0" * 64,
                ),
            )


if __name__ == "__main__":
    unittest.main()
