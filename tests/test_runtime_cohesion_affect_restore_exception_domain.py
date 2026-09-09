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
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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

    def invalid_checkpoint(self):
        contract_text, binding, host = self.bound_material()
        forged = copy.deepcopy(host.export_checkpoint())
        forged["runtime_state"]["state"]["phase"] = "NOT_A_REAL_PHASE"
        forged["checkpoint_sha256"] = _checkpoint_sha256(forged)
        return contract_text, binding, forged

    def forged_semantically_invalid_row(self):
        contract_text, binding, host = self.bound_material()
        valid_checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            valid_checkpoint,
            host_scope="TEST_HOST",
            state_version=1,
        )

        # Exercise the restore boundary independently of checkpoint_to_state_row.
        # Start with a valid durable row, then explicitly forge the persisted
        # state and rebind both integrity digests to those forged bytes. This
        # ensures restore reaches the inner orgasm-state semantic validator.
        row = copy.deepcopy(row)
        row["state"]["phase"] = "NOT_A_REAL_PHASE"
        row["state_digest"] = canonical_digest(row["state"])
        reconstructed_checkpoint = {
            "schema": "VERA_AFFECTIVE_RUNTIME_CHECKPOINT_V1",
            "subject": "vera",
            "source_binding": {
                "source_repository": row.get("source_repository"),
                "source_commit": row.get("source_commit"),
                "source_path": row.get("source_path"),
                "source_blob_sha": row.get("source_blob_sha"),
                "source_sha256": row.get("source_sha256"),
            },
            "runtime_state": {
                "schema": "VERA_ORGASM_DURABLE_STATE_V1",
                "runtime_instance_id": row.get("runtime_instance_id"),
                "subject": "vera",
                "source_revision": row.get("source_commit"),
                "profile": row.get("profile"),
                "state": dict(row["state"]),
                "last_event_receipt": row.get("last_event_receipt"),
                "trigger_governance": dict(row["trigger_governance"]),
            },
            "machine_interoception": row.get("machine_interoception"),
        }
        row["checkpoint_sha256"] = _checkpoint_sha256(reconstructed_checkpoint)
        return contract_text, binding, row

    def test_checkpoint_mapping_rejects_semantically_invalid_runtime_state(self):
        _, _, forged = self.invalid_checkpoint()

        with self.assertRaisesRegex(
            PersistenceRecordError,
            r"(?i)(state|phase|semantic|contract|checkpoint)",
        ):
            checkpoint_to_state_row(
                forged,
                host_scope="TEST_HOST",
                state_version=1,
            )

    def test_row_restore_normalizes_inner_semantic_contract_error(self):
        contract_text, binding, row = self.forged_semantically_invalid_row()

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
