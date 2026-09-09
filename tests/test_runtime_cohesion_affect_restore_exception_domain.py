import copy
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost, _checkpoint_sha256
from runtime_cohesion.affect_persistence import (
    PersistenceRecordError,
    checkpoint_to_state_row,
    restore_host_from_state_row,
)
from runtime_cohesion.orgasm import ContractError


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveRestoreExceptionDomainTests(unittest.TestCase):
    def bound_material(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="restore-exception-domain-test",
        )
        return contract_text, binding, host

    def semantically_invalid_integrity_consistent_row(self):
        contract_text, binding, host = self.bound_material()
        checkpoint = host.export_checkpoint()
        forged = copy.deepcopy(checkpoint)

        # Keep outer integrity self-consistent so the failure necessarily comes
        # from the inner orgasm-state semantic validator rather than hash checks.
        forged["runtime_state"]["state"]["phase"] = "NOT_A_REAL_PHASE"
        forged["checkpoint_sha256"] = _checkpoint_sha256(forged)
        row = checkpoint_to_state_row(
            forged,
            host_scope="TEST_HOST",
            state_version=1,
        )
        self.assertEqual(row["checkpoint_sha256"], forged["checkpoint_sha256"])
        return contract_text, binding, row

    def test_row_restore_normalizes_inner_semantic_contract_error(self):
        contract_text, binding, row = self.semantically_invalid_integrity_consistent_row()

        try:
            restore_host_from_state_row(
                contract_text,
                binding,
                row,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=row["checkpoint_sha256"],
            )
        except PersistenceRecordError as exc:
            self.assertIsInstance(
                exc.__cause__,
                ContractError,
                "public persistence restore should preserve the lower semantic ContractError as its chained cause",
            )
            self.assertRegex(str(exc), r"(?i)(state|phase|semantic|contract|restore)")
            return
        except ContractError as exc:
            self.fail(
                "public restore leaked lower ContractError instead of normalizing it to PersistenceRecordError: "
                + str(exc)
            )

        self.fail("semantically invalid provider row was unexpectedly accepted")


if __name__ == "__main__":
    unittest.main()
