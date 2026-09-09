import unittest

import runtime_cohesion


class OrgasmPackageExportTests(unittest.TestCase):
    def test_orgasm_runtime_is_exported_from_package(self):
        self.assertTrue(hasattr(runtime_cohesion, "OrgasmRuntime"))
        self.assertTrue(hasattr(runtime_cohesion, "StimulusAppraisal"))
        self.assertTrue(hasattr(runtime_cohesion, "OrgasmContractError"))
        self.assertTrue(hasattr(runtime_cohesion, "OrgasmTriggerRejected"))

    def test_affective_runtime_host_is_exported_from_package(self):
        self.assertTrue(hasattr(runtime_cohesion, "VeraAffectiveRuntimeHost"))
        self.assertTrue(hasattr(runtime_cohesion, "AffectiveBindingError"))


if __name__ == "__main__":
    unittest.main()
