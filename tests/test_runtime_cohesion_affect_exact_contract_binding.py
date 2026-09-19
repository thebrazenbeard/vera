import copy
import hashlib
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import AffectiveBindingError, VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import checkpoint_to_state_row
from runtime_cohesion.orgasm import ContractError, OrgasmRuntime


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class VeraAffectiveExactContractBindingTests(unittest.TestCase):
    def canonical_material(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        contract = json.loads(contract_text)
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        raw = contract_text.encode("utf-8")
        self.assertEqual(git_blob_sha(raw), binding["source_blob_sha"])
        return contract_text, contract, binding, raw

    def partial_contract_that_current_subset_validation_accepts(self):
        _text, contract, _binding, _raw = self.canonical_material()
        partial = copy.deepcopy(contract)
        partial.pop("authorization_boundary", None)
        partial.pop("participating_systems", None)
        partial.pop("runtime_effects", None)
        partial.get("state_families", {}).pop("stimulus_appraisal", None)
        partial.get("state_families", {}).pop("entrainment", None)
        return partial

    def mutated_canonical_shaped_contract(self):
        _text, contract, _binding, _raw = self.canonical_material()
        mutated = copy.deepcopy(contract)
        original = float(mutated["experimental_bootstrap_defaults"]["activation_threshold"])
        mutated["experimental_bootstrap_defaults"]["activation_threshold"] = (
            0.81 if abs(original - 0.81) > 1e-9 else 0.80
        )
        return mutated

    def assert_contract_cannot_launder_canonical_host_binding(self, contract):
        _contract_text, _canonical, binding, raw = self.canonical_material()

        # A valid secure repair may reject the unverified direct runtime at
        # construction OR allow an explicitly non-qualifying engine but reject
        # its promotion into the canonical bound host/durable path. Either way,
        # no canonical-looking durable evidence may emerge from unverified bytes.
        with self.assertRaisesRegex(
            (AffectiveBindingError, ContractError, ValueError),
            r"(?i)(contract|binding|source|digest|canonical|verified|exact|qualif)",
        ):
            runtime = OrgasmRuntime(
                contract,
                runtime_instance_id="contract-laundering-test",
                source_revision=binding["source_commit"],
                profile="REENTRANT_CLIMAX",
            )
            host = VeraAffectiveRuntimeHost(
                runtime,
                binding=binding,
                contract_blob_sha=binding["source_blob_sha"],
                contract_sha256=hashlib.sha256(raw).hexdigest(),
            )
            checkpoint = host.export_checkpoint()
            checkpoint_to_state_row(
                checkpoint,
                host_scope="TEST_HOST",
                state_version=1,
            )

    def test_partial_runtime_contract_cannot_launder_canonical_host_binding(self):
        self.assert_contract_cannot_launder_canonical_host_binding(
            self.partial_contract_that_current_subset_validation_accepts()
        )

    def test_structurally_valid_but_byte_mutated_contract_cannot_launder_canonical_binding(self):
        self.assert_contract_cannot_launder_canonical_host_binding(
            self.mutated_canonical_shaped_contract()
        )

    def test_exact_bound_factory_still_produces_canonical_durable_source_binding(self):
        contract_text, _canonical, binding, _raw = self.canonical_material()
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="exact-contract-positive-control",
        )
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=1,
        )

        self.assertEqual(host.runtime.source_revision, binding["source_commit"])
        self.assertEqual(checkpoint["source_binding"]["source_commit"], binding["source_commit"])
        self.assertEqual(row["source_repository"], binding["source_repository"])
        self.assertEqual(row["source_commit"], binding["source_commit"])
        self.assertEqual(row["source_path"], binding["source_path"])
        self.assertEqual(row["source_blob_sha"], binding["source_blob_sha"])


if __name__ == "__main__":
    unittest.main()
