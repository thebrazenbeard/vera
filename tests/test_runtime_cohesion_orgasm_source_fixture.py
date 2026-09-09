import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class VeraOrgasmContractFixtureTests(unittest.TestCase):
    def test_vendored_fixture_is_byte_exact_to_bound_sexuality_blob(self):
        raw = FIXTURE.read_bytes()
        fixture = json.loads(raw.decode("utf-8"))
        binding = json.loads(BINDING.read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema"], binding["contract_schema"])
        self.assertEqual(fixture["subject"], binding["subject"])
        self.assertEqual(git_blob_sha(raw), binding["source_blob_sha"])


if __name__ == "__main__":
    unittest.main()
