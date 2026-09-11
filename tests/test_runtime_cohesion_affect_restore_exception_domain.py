import copy
import hashlib
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


def canonical_digest(value):
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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

    def valid_checkpoint_and_row(self):
        contract_text, binding, host = self.bound_material()
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=1,
        )
        return contract_text, binding, checkpoint, row

    def forged_row_bypassing_checkpoint_to_state_row(self):
        contract_text, binding, checkpoint, valid_row = self.valid_checkpoint_and_row()
        row = copy.deepcopy(valid_row)

        # Start from a row that already crossed the public checkpoint->row
        # boundary successfully, then forge only the durable representation.
        # This keeps the restore-domain test independent from the separate rule
        # that checkpoint_to_state_row itself must reject impossible state.
        row["state"]["phase"] = "NOT_A_REAL_PHASE"
        row["state_digest"] = canonical_digest(row["state"])

        # Reproduce the exact checkpoint shape restore_host_from_state_row will
        # reconstruct from this durable row so outer integrity remains coherent
        # and the failure reaches the lower semantic runtime validator.
        forged_checkpoint = copy.deepcopy(checkpoint)
        forged_checkpoint["runtime_state"]["state"] = copy.deepcopy(row["state"])
        forged_checkpoint["checkpoint_sha256"] = _checkpoint_sha256(forged_checkpoint)
        row["checkpoint_sha256"] = forged_checkpoint["checkpoint_sha256"]

        self.assertEqual(row["state_digest"], canonical_digest(row["state"]))
        return contract_text, binding, row

    def test_checkpoint_to_state_row_rejects_impossible_runtime_phase(self):
        _, _, checkpoint, _ = self.valid_checkpoint_and_row()
        forged = copy.deepcopy(checkpoint)
        forged["runtime_state"]["state"]["phase"] = "NOT_A_REAL_PHASE"
        forged["checkpoint_sha256"] = _checkpoint_sha256(forged)

        with self.assertRaisesRegex(
            PersistenceRecordError,
            r"(?i)(state|phase|semantic|contract)",
        ):
            checkpoint_to_state_row(
                forged,
                host_scope="TEST_HOST",
                state_version=1,
            )

    def test_row_restore_normalizes_inner_semantic_contract_error(self):
        contract_text, binding, row = self.forged_row_bypassing_checkpoint_to_state_row()

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
