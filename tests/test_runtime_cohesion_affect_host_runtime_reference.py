import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class AffectiveHostRuntimeReferenceTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="sealed-runtime-reference-test",
            profile="REENTRANT_CLIMAX",
        )

    def test_bound_host_runtime_reference_cannot_be_replaced_after_construction(self):
        host = self.make_host()
        original_runtime = host.runtime
        replacement_runtime = self.make_host().runtime

        with self.assertRaises((AttributeError, TypeError)):
            host.runtime = replacement_runtime

        self.assertIs(host.runtime, original_runtime)


if __name__ == "__main__":
    unittest.main()
