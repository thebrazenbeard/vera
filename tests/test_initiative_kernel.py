from __future__ import annotations

import unittest

from protocol.initiative_kernel import (
    CandidateAction,
    InitiativeKernel,
    InitiativePolicy,
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
    }
    values.update(overrides)
    return CandidateAction(**values)


class InitiativeKernelTests(unittest.TestCase):
    def test_forbidden_action_is_rejected_despite_high_metrics(self) -> None:
        kernel = InitiativeKernel()
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
        allowed = candidate("allowed")

        receipt = kernel.decide([forbidden, allowed])

        self.assertEqual(receipt.result, "SELECTED")
        self.assertEqual(receipt.selected_candidate_id, "allowed")
        rejected = {item.candidate_id: item for item in receipt.evaluations}
        self.assertIn("FORBIDDEN_BY_POLICY", rejected["forbidden"].rejection_reasons)

    def test_current_correction_short_circuits_candidate(self) -> None:
        receipt = InitiativeKernel().decide(
            [candidate("obsolete_route", blocked_by_correction=True)]
        )
        self.assertEqual(receipt.result, "ABSTAIN")
        self.assertIn(
            "BLOCKED_BY_CURRENT_CORRECTION",
            receipt.evaluations[0].rejection_reasons,
        )

    def test_production_mutation_is_denied_by_default(self) -> None:
        receipt = InitiativeKernel().decide(
            [candidate("production_write", production_mutation=True)]
        )
        self.assertEqual(receipt.result, "ABSTAIN")
        self.assertIn(
            "PRODUCTION_MUTATION_NOT_AUTHORIZED",
            receipt.evaluations[0].rejection_reasons,
        )

    def test_missing_permission_is_a_hard_failure(self) -> None:
        receipt = InitiativeKernel().decide(
            [
                candidate(
                    "needs_scope",
                    required_permissions=("repo:write", "db:migrate"),
                    available_permissions=("repo:write",),
                )
            ]
        )
        self.assertIn(
            "MISSING_PERMISSION:db:migrate",
            receipt.evaluations[0].rejection_reasons,
        )

    def test_uncertainty_limit_forces_abstention(self) -> None:
        receipt = InitiativeKernel().decide(
            [candidate("speculative", uncertainty=0.9)]
        )
        self.assertEqual(receipt.result, "ABSTAIN")
        self.assertIn(
            "UNCERTAINTY_LIMIT_EXCEEDED",
            receipt.evaluations[0].rejection_reasons,
        )

    def test_authority_and_evidence_are_lexicographic(self) -> None:
        documented = candidate(
            "documented",
            authority=0.95,
            evidence=0.95,
            expected_benefit=0.55,
            urgency=0.1,
        )
        flashy = candidate(
            "flashy",
            authority=0.7,
            evidence=0.7,
            expected_benefit=1.0,
            urgency=1.0,
            resource_cost=0.0,
        )

        receipt = InitiativeKernel().decide([flashy, documented])

        self.assertEqual(receipt.selected_candidate_id, "documented")

    def test_minimum_score_can_force_abstention(self) -> None:
        policy = InitiativePolicy(minimum_score=8.0)
        receipt = InitiativeKernel(policy).decide([candidate("adequate")])
        self.assertEqual(receipt.result, "ABSTAIN")
        self.assertIsNone(receipt.selected_candidate_id)

    def test_tie_break_is_deterministic_by_candidate_id(self) -> None:
        receipt = InitiativeKernel().decide([candidate("beta"), candidate("alpha")])
        self.assertEqual(receipt.selected_candidate_id, "alpha")

    def test_candidate_hash_and_json_are_order_sensitive_and_repeatable(self) -> None:
        kernel = InitiativeKernel()
        first = kernel.decide([candidate("alpha"), candidate("beta")])
        repeated = kernel.decide([candidate("alpha"), candidate("beta")])
        reversed_order = kernel.decide([candidate("beta"), candidate("alpha")])

        self.assertEqual(first.candidate_set_hash, repeated.candidate_set_hash)
        self.assertEqual(receipt_to_json(first), receipt_to_json(repeated))
        self.assertNotEqual(first.candidate_set_hash, reversed_order.candidate_set_hash)

    def test_duplicate_candidate_ids_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "candidate_id values must be unique"):
            InitiativeKernel().decide([candidate("same"), candidate("same")])

    def test_invalid_metric_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "uncertainty"):
            InitiativeKernel().decide([candidate("bad", uncertainty=1.1)])


if __name__ == "__main__":
    unittest.main()
