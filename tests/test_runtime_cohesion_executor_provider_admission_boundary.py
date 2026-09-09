import unittest
from types import SimpleNamespace

import runtime_cohesion.executor as executor
import runtime_cohesion.provider_admission as provider_admission
import runtime_cohesion.runtime as runtime
from runtime_cohesion.evidence import ProviderEvidenceEnvelope


class ExecutorProviderAdmissionBoundaryTests(unittest.TestCase):
    @staticmethod
    def governing_material():
        index = {
            "domains": [
                {
                    "id": "GOVERNING",
                    "authority_resolver_ref": (
                        "VERA_RUNTIME_CONTRACT_V1#authority_resolvers.current_user_instruction"
                    ),
                }
            ]
        }
        contract = {
            "authority_resolvers": {
                "current_user_instruction": {
                    "accepted_evidence_classes": ["current_user_authority"]
                }
            },
            "resolver_dispatch": [
                {
                    "id": "dispatch:user-task-authority",
                    "domain_scope": "GOVERNING",
                    "proposition_or_effect_class": "TASK_SCOPE_PERMISSION_OR_USER_CONSENT",
                    "referent_scope": "PATRICK_OR_USER_CONTROLLED_OPERATION",
                    "resolver_ref": "current_user_instruction",
                    "precedence": 100,
                    "conflict_disposition": "FAIL_CLOSED",
                }
            ],
            "resolver_dispatch_decisive_evidence": {
                "dispatch:user-task-authority": {
                    "all_of": ["current_user_authority"],
                    "any_of": [],
                }
            },
        }
        metadata = {
            "proposition_or_effect_class": "TASK_SCOPE_PERMISSION_OR_USER_CONSENT",
            "referent_scope": "PATRICK_OR_USER_CONTROLLED_OPERATION",
        }
        return index, contract, metadata

    def test_executor_uses_provider_strict_admission_symbol(self):
        self.assertIs(
            executor.evaluate_proposition_admission,
            provider_admission.evaluate_provider_proposition_admission,
            "governing executor must not import the lightweight-capable abstract evaluator",
        )

    def test_runtime_module_keeps_abstract_policy_evaluator_explicitly_named(self):
        self.assertTrue(hasattr(runtime, "evaluate_abstract_proposition_admission"))
        self.assertIsNot(
            runtime.evaluate_proposition_admission,
            runtime.evaluate_abstract_proposition_admission,
            "direct runtime provider admission and abstract policy evaluation must be distinct symbols",
        )

    def test_governing_resolution_rejects_duck_typed_provider_lookalike(self):
        index, contract, metadata = self.governing_material()
        lookalike = SimpleNamespace(
            evidence_class="current_user_authority",
            referent="GOVERNING",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata=metadata,
        )

        with self.assertRaises(
            TypeError,
            msg=(
                "the real governing-resolution path must enforce ProviderEvidenceEnvelope "
                "type, not merely accept a duck-typed object that carries the same fields"
            ),
        ):
            executor._derive_governing_resolution(
                "GOVERNING",
                index,
                contract,
                [lookalike],
            )

    def test_governing_resolution_accepts_real_current_bound_envelope(self):
        index, contract, metadata = self.governing_material()
        envelope = ProviderEvidenceEnvelope(
            provider="test-provider",
            locator="test://governing/current-user-authority",
            revision="rev-1",
            observed_at="2026-09-09T22:50:00+00:00",
            evidence_class="current_user_authority",
            referent="GOVERNING",
            scope="TASK_SCOPE_PERMISSION_OR_USER_CONSENT",
            privacy_class="TEST",
            currentness_basis="explicit test current observation",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata=metadata,
        )

        decision = executor._derive_governing_resolution(
            "GOVERNING",
            index,
            contract,
            [envelope],
        )

        self.assertEqual(decision.status, "SATISFIED")
        self.assertEqual(decision.admission_status, "ADMITTED")
        self.assertEqual(decision.current_observation_count, 1)


if __name__ == "__main__":
    unittest.main()
