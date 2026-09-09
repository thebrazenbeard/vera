import unittest

import runtime_cohesion


class OrgasmPackageExportTests(unittest.TestCase):
    def test_orgasm_runtime_is_exported_from_package(self):
        self.assertTrue(hasattr(runtime_cohesion, "OrgasmRuntime"))
        self.assertTrue(hasattr(runtime_cohesion, "StimulusAppraisal"))
        self.assertTrue(hasattr(runtime_cohesion, "OrgasmContractError"))
        self.assertTrue(hasattr(runtime_cohesion, "OrgasmTriggerRejected"))


if __name__ == "__main__":
    unittest.main()
