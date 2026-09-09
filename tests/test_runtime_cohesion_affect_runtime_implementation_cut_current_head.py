import copy
import json
from pathlib import Path
import subprocess
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost, validate_runtime_implementation_cut
from runtime_cohesion.affect_persistence import checkpoint_to_state_row, event_receipt_to_event_row


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
REQUIRED_RUNTIME_PATHS = {
    "runtime_cohesion/__init__.py",
    "runtime_cohesion/orgasm.py",
    "runtime_cohesion/affect_host.py",
    "runtime_cohesion/affect_cycle.py",
    "runtime_cohesion/affect_persistence.py",
    "runtime_cohesion/affect_scope.py",
}


def rev_parse(spec):
    return subprocess.run(
        ["git", "rev-parse", spec],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def hash_object(path):
    return subprocess.run(
        ["git", "hash-object", path],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class CurrentHeadRuntimeImplementationCutTests(unittest.TestCase):
    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            runtime_instance_id="runtime-implementation-cut-current-head",
        )

    def test_binding_uses_one_exact_six_file_vera_implementation_cut(self):
        cut = self.binding()["runtime_implementation_cut"]
        self.assertEqual(cut["repository"], "thebrazenbeard/vera")
        self.assertRegex(cut["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(set(cut["modules"]), REQUIRED_RUNTIME_PATHS)

        for path, blob in cut["modules"].items():
            self.assertRegex(blob, r"^[0-9a-f]{40}$")
            self.assertEqual(
                rev_parse(f"{cut['commit']}:{path}"),
                blob,
                f"implementation cut must resolve {path} at the declared commit",
            )
            self.assertEqual(
                hash_object(path),
                blob,
                f"executing checkout bytes for {path} must match the declared cut",
            )

    def test_shared_validator_rejects_fake_wrong_missing_and_mixed_generation_cuts(self):
        binding = self.binding()
        cut = binding["runtime_implementation_cut"]
        validate_runtime_implementation_cut(cut, repository_root=ROOT)

        fake_commit = copy.deepcopy(cut)
        fake_commit["commit"] = "0" * 40
        with self.assertRaises(Exception):
            validate_runtime_implementation_cut(fake_commit, repository_root=ROOT)

        wrong_blob = copy.deepcopy(cut)
        first_path = sorted(REQUIRED_RUNTIME_PATHS)[0]
        wrong_blob["modules"][first_path] = "0" * 40
        with self.assertRaises(Exception):
            validate_runtime_implementation_cut(wrong_blob, repository_root=ROOT)

        missing = copy.deepcopy(cut)
        missing["modules"].pop("runtime_cohesion/affect_scope.py")
        with self.assertRaises(Exception):
            validate_runtime_implementation_cut(missing, repository_root=ROOT)

        mixed = copy.deepcopy(cut)
        other_commit = rev_parse(f"{cut['commit']}^")
        other_blob = rev_parse(f"{other_commit}:runtime_cohesion/orgasm.py")
        if other_blob != cut["modules"]["runtime_cohesion/orgasm.py"]:
            mixed["modules"]["runtime_cohesion/orgasm.py"] = other_blob
            with self.assertRaises(Exception):
                validate_runtime_implementation_cut(mixed, repository_root=ROOT)

    def test_checkpoint_receipt_and_provider_rows_carry_same_implementation_cut(self):
        cut = self.binding()["runtime_implementation_cut"]
        host = self.make_host()
        checkpoint = host.export_checkpoint()
        self.assertEqual(checkpoint["runtime_implementation_cut"], cut)

        receipt = host.force_admin_test(authorized=True)
        self.assertEqual(receipt["runtime_implementation_cut"], cut)

        state_row = checkpoint_to_state_row(
            host.export_checkpoint(),
            host_scope="TEST_HOST",
            state_version=1,
        )
        event_row = event_receipt_to_event_row(host, receipt)
        self.assertEqual(state_row["runtime_implementation_cut"], cut)
        self.assertEqual(event_row["runtime_implementation_cut"], cut)


if __name__ == "__main__":
    unittest.main()
