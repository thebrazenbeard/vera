import json
from dataclasses import fields
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class VeraOrgasmAppraisalContractFidelityTests(unittest.TestCase):
    def test_executable_appraisal_represents_every_contract_declared_appraisal_field(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        declared = set(contract["state_families"]["stimulus_appraisal"])
        executable = {field.name for field in fields(StimulusAppraisal)}

        self.assertTrue(
            declared.issubset(executable),
            f"executable StimulusAppraisal is missing contract-declared fields: {sorted(declared - executable)}",
        )

    def test_declared_ambiguity_and_boundary_relevance_accept_exact_endpoints(self):
        low_high = StimulusAppraisal(ambiguity=0.0, boundary_relevance=1.0)
        high_low = StimulusAppraisal(ambiguity=1.0, boundary_relevance=0.0)

        self.assertEqual(low_high.ambiguity, 0.0)
        self.assertEqual(low_high.boundary_relevance, 1.0)
        self.assertEqual(high_low.ambiguity, 1.0)
        self.assertEqual(high_low.boundary_relevance, 0.0)

    def test_declared_ambiguity_and_boundary_relevance_reject_out_of_range_and_non_numeric_values(self):
        invalid_values = (-0.001, 1.001, True, False, "0.5", None)
        for field_name in ("ambiguity", "boundary_relevance"):
            for value in invalid_values:
                with self.subTest(field=field_name, value=value):
                    with self.assertRaises((TypeError, ValueError)):
                        StimulusAppraisal(**{field_name: value})


if __name__ == "__main__":
    unittest.main()
