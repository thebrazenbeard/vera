import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_scope import (
    bind_affective_host_scope,
    require_affective_host_cycle_eligible,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class ScopeCurrentnessSeparationTests(unittest.TestCase):
    def test_scope_binding_does_not_promote_checkpoint_replay_to_provider_current(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        source = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="scope-currentness-separation-test",
        )
        checkpoint = source.export_checkpoint()
        replay = VeraAffectiveRuntimeHost.restore_checkpoint(
            contract_text,
            binding,
            checkpoint,
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )

        # Scope is an identity/binding dimension. It is not evidence that the
        # replay host came from a validated CURRENT provider row/generation.
        bind_affective_host_scope(replay, "TEST_HOST")

        with self.assertRaisesRegex(ValueError, r"(?i)(provider|current|replay|attest)"):
            require_affective_host_cycle_eligible(replay)


if __name__ == "__main__":
    unittest.main()
