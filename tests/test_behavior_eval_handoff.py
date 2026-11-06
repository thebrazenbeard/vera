"""Hostile tests for the public, unadmitted behavior-evaluation handoff."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_behavior_eval_handoff", ROOT / "scripts/validate_behavior_eval_handoff.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class BehaviorEvalHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in (VALIDATOR.PROFILE, VALIDATOR.HANDOFF, VALIDATOR.CROSSWALK):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def mutate(self, relative: Path, callback) -> list[str]:
        path = self.root / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        callback(value)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return VALIDATOR.validate_contract(self.root)

    def test_pinned_contract_is_valid_but_does_not_qualify_any_model(self) -> None:
        self.assertEqual([], VALIDATOR.validate_contract(ROOT))
        handoff = json.loads((ROOT / VALIDATOR.HANDOFF).read_text(encoding="utf-8"))
        self.assertEqual("HOLD_SOURCE_ONLY", handoff["admission"]["decision"])
        self.assertEqual("UNISSUED", handoff["admission"]["owner_approval"])
        self.assertFalse(handoff["protocol"]["public_source_may_certify_improvement"])
        self.assertEqual(10, len(handoff["dimensions"]))

    def test_hidden_prompt_or_gold_injection_refused(self) -> None:
        for key, value in (
            ("heldout_prompts", ["secret"]),
            ("scoring_rubric", "anything"),
            ("gold_answers", ["private"]),
            ("case_ids", ["case-1"]),
        ):
            with self.subTest(key=key):
                errors = self.mutate(VALIDATOR.HANDOFF, lambda obj: obj.__setitem__(key, value))
                self.assertTrue(errors)
                shutil.copyfile(ROOT / VALIDATOR.HANDOFF, self.root / VALIDATOR.HANDOFF)

    def test_fabricated_owner_approval_and_model_pass_refused(self) -> None:
        errors = self.mutate(VALIDATOR.HANDOFF, lambda obj:
            obj["admission"].update(owner_approval="ISSUED", decision="PASS"))
        self.assertTrue(any("admission" in issue for issue in errors))

    def test_fabricated_score_and_disjointness_refused(self) -> None:
        errors = self.mutate(VALIDATOR.HANDOFF, lambda obj:
            obj["data_boundary"].update(train_heldout_disjointness="PROVEN", score=1.0))
        self.assertTrue(any("data_boundary" in issue for issue in errors))

    def test_missing_control_refused(self) -> None:
        errors = self.mutate(VALIDATOR.HANDOFF, lambda obj:
            obj["protocol"]["additional_learning_claim_controls"].remove("corrupted_labels"))
        self.assertTrue(any("protocol" in issue for issue in errors))

    def test_boolean_controls_cannot_be_numeric_aliases(self) -> None:
        # Python considers False == 0 == 0.0, but a JSON contract does not.
        # No other JSON type may impersonate a mandatory false admission gate.
        for forged in (0, 0.0, "false", None, []):
            with self.subTest(forged=repr(forged)):
                errors = self.mutate(VALIDATOR.HANDOFF, lambda obj:
                    obj["protocol"].update(public_source_may_authorize_runs=forged))
                self.assertTrue(any("protocol" in issue for issue in errors), errors)
                shutil.copyfile(ROOT / VALIDATOR.HANDOFF, self.root / VALIDATOR.HANDOFF)

    def test_eight_dialogue_families_are_not_ten_behavior_dimensions(self) -> None:
        crosswalk = json.loads((ROOT / VALIDATOR.CROSSWALK).read_text(encoding="utf-8"))
        handoff = json.loads((ROOT / VALIDATOR.HANDOFF).read_text(encoding="utf-8"))
        self.assertEqual([], VALIDATOR.validate_contract(ROOT))
        self.assertEqual(8, len(crosswalk["family_design_hypotheses"]))
        self.assertEqual(10, len(handoff["dimensions"]))
        self.assertEqual(["voice_recognizability", "cross_runtime_consistency"],
                         crosswalk["no_direct_family_hypothesis"])
        self.assertEqual("PUBLIC_DESIGN_HYPOTHESIS_NOT_EVALUATION", crosswalk["status"])
        self.assertEqual("NOT_OBSERVED", crosswalk["measurement"]["real_model_inference"])

    def test_crosswalk_forged_inference_and_boolean_alias_refused(self) -> None:
        for fabricated in ("PASS", 0):
            with self.subTest(fabricated=repr(fabricated)):
                key = ("real_model_inference" if isinstance(fabricated, str)
                       else "public_source_may_certify_behavior")
                errors = self.mutate(VALIDATOR.CROSSWALK, lambda obj:
                    obj["measurement"].update({key: fabricated}))
                self.assertTrue(any("crosswalk" in issue for issue in errors), errors)
                shutil.copyfile(ROOT / VALIDATOR.CROSSWALK, self.root / VALIDATOR.CROSSWALK)

    def test_crosswalk_family_alias_and_claimed_coverage_refused(self) -> None:
        errors = self.mutate(VALIDATOR.CROSSWALK, lambda obj:
            obj["family_design_hypotheses"][0].update(family="natural_flow"))
        self.assertTrue(any("crosswalk" in issue for issue in errors))
        shutil.copyfile(ROOT / VALIDATOR.CROSSWALK, self.root / VALIDATOR.CROSSWALK)
        errors = self.mutate(VALIDATOR.CROSSWALK, lambda obj:
            obj["no_direct_family_hypothesis"].clear())
        self.assertTrue(any("crosswalk" in issue for issue in errors))

    def test_five_arm_lora_and_training_free_controls(self) -> None:
        handoff = json.loads((ROOT / VALIDATOR.HANDOFF).read_text(encoding="utf-8"))
        protocol = handoff["protocol"]
        self.assertEqual(5, len(protocol["required_behavior_arms"]) +
                         len(protocol["additional_learning_claim_controls"]))
        self.assertEqual(["sham_update", "shuffled_labels", "corrupted_labels"],
                         protocol["additional_learning_claim_controls"])
        self.assertEqual(["zero_patch", "sham_patch", "random_patch"],
                         protocol["training_free_weight_compilation_controls"])

    def test_compiled_weight_controls_cannot_be_silently_removed(self) -> None:
        errors = self.mutate(VALIDATOR.HANDOFF, lambda obj:
            obj["protocol"].pop("training_free_weight_compilation_controls"))
        self.assertTrue(any("protocol" in issue for issue in errors))

    def test_profile_content_tampering_breaks_byte_binding(self) -> None:
        errors = self.mutate(VALIDATOR.PROFILE, lambda obj: obj["core_traits"].update(candor="altered"))
        self.assertTrue(any("canonical profile bytes changed" in issue for issue in errors))

    def test_profile_and_handoff_coforgery_refused(self) -> None:
        self.mutate(VALIDATOR.PROFILE, lambda obj: obj["core_traits"].update(candor="forged"))
        forged_hash = hashlib.sha256((self.root / VALIDATOR.PROFILE).read_bytes()).hexdigest()
        errors = self.mutate(VALIDATOR.HANDOFF, lambda obj:
            obj["source"].update(profile_sha256=forged_hash))
        self.assertTrue(any("canonical profile bytes changed" in issue for issue in errors))

    def test_profile_dimension_change_refused_even_when_rehashed(self) -> None:
        errors = self.mutate(VALIDATOR.PROFILE, lambda obj:
            obj["evaluation_dimensions"].append("extra dimension"))
        self.assertTrue(any("dimensions changed" in issue for issue in errors))

    def test_handoff_unknown_key_refused(self) -> None:
        errors = self.mutate(VALIDATOR.HANDOFF, lambda obj: obj["source"].update(fake="proof"))
        self.assertTrue(any("source provenance" in issue for issue in errors))

    def test_duplicate_json_key_refused(self) -> None:
        path = self.root / VALIDATOR.HANDOFF
        path.write_text('{"schema_id":"a", "schema_id":"b"}', encoding="utf-8")
        self.assertTrue(any("duplicate JSON key" in issue for issue in VALIDATOR.validate_contract(self.root)))

    def test_nonfinite_json_refused(self) -> None:
        path = self.root / VALIDATOR.HANDOFF
        path.write_text('{"score":NaN}', encoding="utf-8")
        self.assertTrue(any("nonfinite" in issue for issue in VALIDATOR.validate_contract(self.root)))

    def test_oversize_and_symlink_refused(self) -> None:
        path = self.root / VALIDATOR.HANDOFF
        path.write_bytes(b" " * (VALIDATOR.MAX_JSON_BYTES + 1))
        self.assertTrue(any("exceeds" in issue for issue in VALIDATOR.validate_contract(self.root)))
        path.unlink()
        path.symlink_to(ROOT / VALIDATOR.HANDOFF)
        self.assertTrue(any("symlink" in issue for issue in VALIDATOR.validate_contract(self.root)))

    def test_optimized_python_mode_preserves_all_gates(self) -> None:
        result = subprocess.run(
            [sys.executable, "-O", "-m", "scripts.validate_behavior_eval_handoff"],
            cwd=ROOT, capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertIn("HOLD", result.stdout)


if __name__ == "__main__":
    unittest.main()
