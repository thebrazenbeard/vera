import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraOrgasmRuntimeBindingTests(unittest.TestCase):
    def test_binding_is_exact_vera_scoped_and_nonactivating(self):
        binding = json.loads(BINDING.read_text(encoding="utf-8"))
        self.assertEqual(binding["schema"], "VERA_ORGASM_RUNTIME_BINDING_V1")
        self.assertEqual(binding["subject"], "vera")
        self.assertEqual(binding["contract_schema"], "VERA_ORGASM_RUNTIME_CONTRACT_V1")
        self.assertEqual(binding["source_repository"], "thebrazenbeard/sexuality")
        self.assertEqual(binding["source_path"], "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json")
        self.assertFalse(binding["availability_implies_activation"])
        self.assertEqual(binding["activation_mode"], "ALWAYS_PRESENT_NORMALLY_QUIESCENT_WHEN_EXACT_CONTRACT_LOADED")
        self.assertEqual(len(binding["source_commit"]), 40)
        self.assertEqual(len(binding["source_blob_sha"]), 40)


if __name__ == "__main__":
    unittest.main()
