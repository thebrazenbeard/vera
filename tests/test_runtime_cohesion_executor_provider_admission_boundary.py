import unittest

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


if __name__ == "__main__":
    unittest.main()
