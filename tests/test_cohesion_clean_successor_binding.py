from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

from scripts.validate_cohesion_clean_successor import (
    R2_CLEAN_SOURCE_COMMIT,
    R2_CLEAN_SOURCE_TREE,
    RUNTIME_IMPLEMENTATION_CUT,
    load_json_strict,
    validate_clean_successor,
)


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

    def test_current_record_binds_exact_r2_clean_source(self):
        record = self.record()
        self.assertEqual(R2_CLEAN_SOURCE_COMMIT, record["clean_source_commit"])
        self.assertEqual(R2_CLEAN_SOURCE_TREE, record["clean_source_tree"])
        self.assertEqual(
            RUNTIME_IMPLEMENTATION_CUT,
            record["runtime_binding"]["runtime_implementation_cut_commit"],
        )
        self.assertNotEqual(
            record["clean_source_commit"],
            record["runtime_binding"]["runtime_implementation_cut_commit"],
        )
        self.assertTrue(
            record["runtime_binding"]["bound_module_byte_equivalence_required"]
        )

    def test_r1_cannot_regress_into_current_clean_source(self):
        record = self.record()
        mutated = deepcopy(record)
        mutated["clean_source_commit"] = mutated["r1_predecessor"]["clean_source_commit"]
        with self.assertRaisesRegex(ValueError, "exact R2 source tuple"):
            validate_clean_successor(
                mutated,
                ownership_path=OWNERSHIP_PATH,
                binding_path=BINDING_PATH,
                repository_root=ROOT,
            )

    def test_donor_cannot_become_clean_source_commit(self):
        record = self.record()
        mutated = deepcopy(record)
        mutated["clean_source_commit"] = mutated["donor"]["head"]
        with self.assertRaisesRegex(ValueError, "exact R2 source tuple"):
            validate_clean_successor(
                mutated,
                ownership_path=OWNERSHIP_PATH,
                binding_path=BINDING_PATH,
                repository_root=ROOT,
            )

    def test_declared_runtime_cut_must_match_provider_bound_runtime_cut(self):
        record = self.record()
        mutated = deepcopy(record)
        mutated["runtime_binding"]["runtime_implementation_cut_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "runtime implementation cut mismatch"):
            validate_clean_successor(
                mutated,
                ownership_path=OWNERSHIP_PATH,
                binding_path=BINDING_PATH,
                repository_root=ROOT,
            )

    def test_binding_file_cut_mismatch_fails_closed(self):
        record = self.record()
        binding = load_json_strict(BINDING_PATH)
        binding["runtime_implementation_cut"]["commit"] = "0" * 40
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binding.json"
            path.write_text(json.dumps(binding), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError,
                "runtime binding file does not match declared implementation cut",
            ):
                validate_clean_successor(
                    record,
                    ownership_path=OWNERSHIP_PATH,
                    binding_path=path,
                    repository_root=ROOT,
                )

    def test_r3_successor_must_bind_r2_predecessor(self):
        record = self.record()
        mutated = deepcopy(record)
        mutated["downstream_successor"]["predecessor_clean_r2_source"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "R3 downstream-successor binding mismatch"):
            validate_clean_successor(
                mutated,
                ownership_path=OWNERSHIP_PATH,
                binding_path=BINDING_PATH,
                repository_root=ROOT,
            )

    def test_source_cannot_claim_install_or_qualification(self):
        record = self.record()
        for key in ("installation", "current_route", "behavioral_qualification", "provider_currentness"):
            mutated = deepcopy(record)
            mutated["claim_ceiling"][key] = "ESTABLISHED"
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "claim ceiling"):
                    validate_clean_successor(
                        mutated,
                        ownership_path=OWNERSHIP_PATH,
                        binding_path=BINDING_PATH,
                        repository_root=ROOT,
                    )

    def test_phenomenology_must_remain_unresolved(self):
        record = self.record()
        mutated = deepcopy(record)
        mutated["claim_ceiling"]["phenomenology"] = "ESTABLISHED"
        with self.assertRaisesRegex(ValueError, "phenomenology"):
            validate_clean_successor(
                mutated,
                ownership_path=OWNERSHIP_PATH,
                binding_path=BINDING_PATH,
                repository_root=ROOT,
            )

    def test_frozen_sexuality_object_is_exact(self):
        record = self.record()
        mutated = deepcopy(record)
        mutated["frozen_sexuality_object"]["blob"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "frozen sexuality"):
            validate_clean_successor(
                mutated,
                ownership_path=OWNERSHIP_PATH,
                binding_path=BINDING_PATH,
                repository_root=ROOT,
            )


if __name__ == "__main__":
    unittest.main()
