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


if __name__ == "__main__":
    unittest.main()
