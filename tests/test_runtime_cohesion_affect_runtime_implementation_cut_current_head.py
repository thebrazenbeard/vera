from collections.abc import Mapping
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost, validate_runtime_implementation_cut
from runtime_cohesion.affect_persistence import checkpoint_to_state_row, event_receipt_to_event_row


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
REQUIRED_RUNTIME_PATHS = {
    "runtime_cohesion/__init__.py",
    "runtime_cohesion/adapters.py",
    "runtime_cohesion/evidence.py",
    "runtime_cohesion/orgasm.py",
    "runtime_cohesion/affect_authority.py",
    "runtime_cohesion/affect_bound_runtime.py",
    "runtime_cohesion/affect_receipt.py",
    "runtime_cohesion/affect_host.py",
    "runtime_cohesion/affect_cycle.py",
    "runtime_cohesion/affect_persistence.py",
    "runtime_cohesion/affect_provider_runtime.py",
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


class ExactAuthorityVerifier:
    verifier_id = "runtime-implementation-cut-authority"

    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, Mapping):
            return None
        if subject.get("state") != "ALLOW":
            return None
        if subject.get("referent") != expected_referent:
            return None
        if subject.get("proposition_or_effect_class") != expected_effect_class:
            return None
        if subject.get("currentness") != "CURRENT" or subject.get("expiry_or_supersession") is not None:
            return None
        canonical = json.dumps(dict(subject), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "runtime-implementation-cut-authority-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class CurrentHeadRuntimeImplementationCutTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(ExactAuthorityVerifier())

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def authorization_subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-runtime-implementation-cut-test",
            "observed_at": "2026-09-10T20:30:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            runtime_instance_id="runtime-implementation-cut-current-head",
        )

    def test_binding_uses_one_exact_affective_execution_implementation_cut(self):
        cut = self.binding()["runtime_implementation_cut"]
        self.assertEqual(cut["schema"], "VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1")
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

    def test_shared_validator_rejects_fake_wrong_missing_extra_and_mixed_generation_cuts(self):
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

        extra = copy.deepcopy(cut)
        extra["modules"]["runtime_cohesion/runtime.py"] = rev_parse(
            f"{cut['commit']}:runtime_cohesion/runtime.py"
        )
        with self.assertRaises(Exception):
            validate_runtime_implementation_cut(extra, repository_root=ROOT)

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

        receipt = host.force_admin_test(
            authorization_subject=self.authorization_subject(),
        )
        self.assertEqual(receipt["runtime_implementation_cut"], cut)

        state_row = checkpoint_to_state_row(
            host.export_checkpoint(),
            host_scope="TEST_HOST",
            state_version=1,
        )
        event_row = event_receipt_to_event_row(host, receipt)
        self.assertEqual(state_row["runtime_implementation_cut"], cut)
        self.assertEqual(event_row["runtime_implementation_cut"], cut)

    def test_restore_rejects_checkpoint_or_provider_row_bound_to_a_different_implementation_cut(self):
        host = self.make_host()
        checkpoint = host.export_checkpoint()
        forged_checkpoint = copy.deepcopy(checkpoint)
        forged_checkpoint["runtime_implementation_cut"]["commit"] = "0" * 40
        forged_checkpoint.pop("checkpoint_sha256", None)

        with self.assertRaises(Exception):
            VeraAffectiveRuntimeHost.restore_checkpoint(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                self.binding(),
                forged_checkpoint,
                expected_checkpoint_sha256="0" * 64,
            )

        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=1,
        )
        forged_row = copy.deepcopy(row)
        forged_row["runtime_implementation_cut"]["commit"] = "0" * 40
        self.assertNotEqual(forged_row["runtime_implementation_cut"], self.binding()["runtime_implementation_cut"])


if __name__ == "__main__":
    unittest.main()
