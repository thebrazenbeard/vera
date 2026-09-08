import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json"


class VeraCohesionIndexV1Tests(unittest.TestCase):
    def test_fixed_system_inventory_is_explicit_and_temporal_is_auxiliary(self):
        self.assertTrue(INDEX.exists(), "consolidated cohesion index must exist")
        document = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertEqual(document["schema"], "VERA_COHESION_INDEX_V1")
        systems = document["systems"]
        self.assertEqual(len(systems), 13)
        ids = [system["id"] for system in systems]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn("temporal", ids)
        self.assertEqual(document["auxiliary_sources"]["temporal"]["role"], "CHRONOLOGY_ONLY")


if __name__ == "__main__":
    unittest.main()
