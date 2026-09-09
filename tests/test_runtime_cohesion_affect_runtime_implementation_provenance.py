import hashlib
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import checkpoint_to_state_row, event_receipt_to_event_row


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
RUNTIME_PATH = ROOT / "runtime_cohesion" / "orgasm.py"


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class AffectiveRuntimeImplementationProvenanceTests(unittest.TestCase):
    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            runtime_instance_id="vera-runtime-provenance-test",
        )

    def test_binding_separately_pins_executable_vera_runtime_source(self):
        binding = self.binding()
        self.assertEqual(binding["source_repository"], "thebrazenbeard/sexuality")
        self.assertEqual(binding["runtime_repository"], "thebrazenbeard/vera")
        self.assertEqual(binding["runtime_module"], "runtime_cohesion/orgasm.py")
        self.assertRegex(binding["runtime_commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(binding["runtime_blob_sha"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            binding["runtime_blob_sha"],
            git_blob_sha(RUNTIME_PATH.read_bytes()),
            "runtime implementation binding must match the exact executing module bytes",
        )

    def test_checkpoint_carries_contract_and_runtime_implementation_as_distinct_bindings(self):
        binding = self.binding()
        checkpoint = self.make_host().export_checkpoint()
        self.assertEqual(checkpoint["source_binding"]["source_repository"], "thebrazenbeard/sexuality")
        implementation = checkpoint["runtime_implementation_binding"]
        self.assertEqual(implementation["repository"], "thebrazenbeard/vera")
        self.assertEqual(implementation["commit"], binding["runtime_commit"])
        self.assertEqual(implementation["path"], binding["runtime_module"])
        self.assertEqual(implementation["blob_sha"], binding["runtime_blob_sha"])

    def test_event_receipt_and_provider_rows_preserve_runtime_implementation_binding(self):
        binding = self.binding()
        host = self.make_host()
        receipt = host.force_admin_test(authorized=True)
        implementation = receipt["runtime_implementation_binding"]
        self.assertEqual(implementation["repository"], "thebrazenbeard/vera")
        self.assertEqual(implementation["commit"], binding["runtime_commit"])
        self.assertEqual(implementation["path"], binding["runtime_module"])
        self.assertEqual(implementation["blob_sha"], binding["runtime_blob_sha"])

        checkpoint = host.export_checkpoint()
        state_row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)
        event_row = event_receipt_to_event_row(host, receipt)
        for row in (state_row, event_row):
            self.assertEqual(row["runtime_repository"], "thebrazenbeard/vera")
            self.assertEqual(row["runtime_commit"], binding["runtime_commit"])
            self.assertEqual(row["runtime_path"], binding["runtime_module"])
            self.assertEqual(row["runtime_blob_sha"], binding["runtime_blob_sha"])


if __name__ == "__main__":
    unittest.main()
