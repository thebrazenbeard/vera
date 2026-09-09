import unittest
from types import SimpleNamespace

import runtime_cohesion.executor as executor
import runtime_cohesion.provider_admission as provider_admission
import runtime_cohesion.runtime as runtime


class ExecutorProviderAdmissionBoundaryTests(unittest.TestCase):
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
        lookalike = SimpleNamespace(
            evidence_class="current_user_authority",
            referent="GOVERNING",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata={
                "proposition_or_effect_class": "TASK_SCOPE_PERMISSION_OR_USER_CONSENT",
                "referent_scope": "PATRICK_OR_USER_CONTROLLED_OPERATION",
            },
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


if __name__ == "__main__":
    unittest.main()
