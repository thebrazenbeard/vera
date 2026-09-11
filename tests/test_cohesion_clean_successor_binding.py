from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_cohesion_clean_successor import load_json_strict, validate_clean_successor


ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "architecture/cohesion/VERA_COHESION_CLEAN_SUCCESSOR_V1.json"
OWNERSHIP_PATH = ROOT / "architecture/cohesion/VERA_COHESION_OWNERSHIP_CONTRACT_V0.json"
BINDING_PATH = ROOT / "architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json"


class CohesionCleanSuccessorBindingTests(unittest.TestCase):
    def record(self) -> dict:
        return load_json_strict(RECORD_PATH)

    def test_current_clean_successor_validates(self):
        validate_clean_successor(
            self.record(),
            ownership_path=OWNERSHIP_PATH,
            binding_path=BINDING_PATH,
            repository_root=ROOT,
        )

    def test_donor_cannot_become_clean_source_commit(self):
        record = self.record()
        mutated = deepcopy(record)
        mutated["clean_source_commit"] = mutated["donor"]["head"]
        with self.assertRaisesRegex(ValueError, "flattened clean source"):
            validate_clean_successor(mutated, ownership_path=OWNERSHIP_PATH, binding_path=BINDING_PATH, repository_root=ROOT)

    def test_source_cannot_claim_install_or_qualification(self):
        record = self.record()
        for key in ("installation", "current_route", "behavioral_qualification", "provider_currentness"):
            mutated = deepcopy(record)
            mutated["claim_ceiling"][key] = "ESTABLISHED"
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "claim ceiling"):
                    validate_clean_successor(mutated, ownership_path=OWNERSHIP_PATH, binding_path=BINDING_PATH, repository_root=ROOT)

    def test_phenomenology_must_remain_unresolved(self):
        record = self.record()
        mutated = deepcopy(record)
        mutated["claim_ceiling"]["phenomenology"] = "ESTABLISHED"
        with self.assertRaisesRegex(ValueError, "phenomenology"):
            validate_clean_successor(mutated, ownership_path=OWNERSHIP_PATH, binding_path=BINDING_PATH, repository_root=ROOT)

    def test_frozen_sexuality_object_is_exact(self):
        record = self.record()
        mutated = deepcopy(record)
        mutated["frozen_sexuality_object"]["blob"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "frozen sexuality"):
            validate_clean_successor(mutated, ownership_path=OWNERSHIP_PATH, binding_path=BINDING_PATH, repository_root=ROOT)


if __name__ == "__main__":
    unittest.main()
