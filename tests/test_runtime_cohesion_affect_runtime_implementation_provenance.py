import copy
import json
from pathlib import Path
import subprocess
import unittest

from runtime_cohesion.affect_host import (
    AffectiveBindingError,
    VeraAffectiveRuntimeHost,
    validate_runtime_implementation_cut,
)
from runtime_cohesion.affect_persistence import checkpoint_to_state_row, event_receipt_to_event_row


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
REQUIRED_RUNTIME_PATHS = {
    "runtime_cohesion/orgasm.py",
    "runtime_cohesion/affect_host.py",
    "runtime_cohesion/affect_cycle.py",
    "runtime_cohesion/affect_persistence.py",
}


def resolve_git_blob(commit, path):
    result = subprocess.run(
        ["git", "rev-parse", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class AffectiveRuntimeImplementationProvenanceTests(unittest.TestCase):
    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def make_host(self, binding=None):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            binding or self.binding(),
            runtime_instance_id="vera-runtime-provenance-test",
        )

    def test_implementation_cut_resolves_exact_git_objects_and_complete_surface(self):
        binding = self.binding()
        cut = binding["runtime_implementation_cut"]
        self.assertEqual(cut["repository"], "thebrazenbeard/vera")
        self.assertRegex(cut["commit"], r"^[0-9a-f]{40}$")
        modules = cut["modules"]
        self.assertTrue(REQUIRED_RUNTIME_PATHS.issubset(set(modules)))
        for path in REQUIRED_RUNTIME_PATHS:
            declared_blob = modules[path]
            self.assertRegex(declared_blob, r"^[0-9a-f]{40}$")
            self.assertEqual(resolve_git_blob(cut["commit"], path), declared_blob)
            self.assertEqual(resolve_git_blob("HEAD", path), declared_blob)

    def test_runtime_validator_rejects_fake_commit_wrong_blob_missing_and_mixed_generation(self):
        binding = self.binding()
        validate_runtime_implementation_cut(binding, repo_root=ROOT)

        fake_commit = copy.deepcopy(binding)
        fake_commit["runtime_implementation_cut"]["commit"] = "0" * 40
        with self.assertRaises(AffectiveBindingError):
            validate_runtime_implementation_cut(fake_commit, repo_root=ROOT)

        wrong_blob = copy.deepcopy(binding)
        wrong_blob["runtime_implementation_cut"]["modules"]["runtime_cohesion/orgasm.py"] = "0" * 40
        with self.assertRaises(AffectiveBindingError):
            validate_runtime_implementation_cut(wrong_blob, repo_root=ROOT)

        missing_module = copy.deepcopy(binding)
        del missing_module["runtime_implementation_cut"]["modules"]["runtime_cohesion/affect_cycle.py"]
        with self.assertRaises(AffectiveBindingError):
            validate_runtime_implementation_cut(missing_module, repo_root=ROOT)

        mixed_generation = copy.deepcopy(binding)
        mixed_generation["runtime_implementation_cut"]["modules"]["runtime_cohesion/orgasm.py"] = (
            "324baefbce4422163e0bf036b97793dfeaa34c4d"
        )
        with self.assertRaises(AffectiveBindingError):
            validate_runtime_implementation_cut(mixed_generation, repo_root=ROOT)

    def test_checkpoint_carries_contract_and_runtime_implementation_as_distinct_bindings(self):
        binding = self.binding()
        checkpoint = self.make_host().export_checkpoint()
        self.assertEqual(checkpoint["source_binding"]["source_repository"], "thebrazenbeard/sexuality")
        self.assertEqual(checkpoint["runtime_implementation_cut"], binding["runtime_implementation_cut"])

    def test_event_receipt_and_provider_rows_preserve_runtime_implementation_cut(self):
        binding = self.binding()
        host = self.make_host()
        receipt = host.force_admin_test(authorized=True)
        self.assertEqual(receipt["runtime_implementation_cut"], binding["runtime_implementation_cut"])

        checkpoint = host.export_checkpoint()
        state_row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)
        event_row = event_receipt_to_event_row(host, receipt)
        self.assertEqual(state_row["runtime_implementation_cut"], binding["runtime_implementation_cut"])
        self.assertEqual(event_row["runtime_implementation_cut"], binding["runtime_implementation_cut"])


if __name__ == "__main__":
    unittest.main()
