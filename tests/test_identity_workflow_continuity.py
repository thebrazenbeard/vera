from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts/validate_identity_workflow_continuity.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_identity_workflow_continuity", VALIDATOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class IdentityWorkflowContinuityTests(unittest.TestCase):
    artifacts = (
        "architecture/identity/VERA_IDENTITY_WORKFLOW_CONTINUITY_V1.json",
        "schemas/vera_identity_workflow_continuity_v1.schema.json",
        "architecture/identity/VERA_PROJECT_IDENTITY_V1.json",
        "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json",
        "docs/IDENTITY_WORKFLOW_CONTINUITY_V1.md",
    )

    def copy_contract(self, target_root: Path) -> None:
        for relative in self.artifacts:
            source = ROOT / relative
            target = target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def mutate_json(
        self,
        target_root: Path,
        relative: str,
        mutation: Callable[[dict[str, object]], None],
    ) -> list[str]:
        path = target_root / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        mutation(value)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        return VALIDATOR.validate_contract(target_root)

    def test_current_policy_validates(self) -> None:
        self.assertEqual([], VALIDATOR.validate_contract(ROOT))

    def test_identity_reference_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                reference = policy["identity_ref"]
                assert isinstance(reference, dict)
                reference["version"] = "1.0.1"

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn("workflow-continuity identity version mismatch", errors)

    def test_silent_scope_expansion_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                authority = policy["authority"]
                assert isinstance(authority, dict)
                authority["silent_scope_expansion"] = True

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn("silent workflow scope expansion is forbidden", errors)

    def test_user_courier_requirement_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                courier = policy["courier_boundary"]
                assert isinstance(courier, dict)
                courier["require_user_to_relay_connected_project_state"] = True

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn(
                "Patrick must not be required to courier connected project state",
                errors,
            )

    def test_stale_authorization_transfer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                advance = policy["advance_policy"]
                assert isinstance(advance, dict)
                advance["stale_authorization_transfer_allowed"] = True

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn("stale authorization must not transfer to a new SHA", errors)

    def test_reviewers_cannot_patch_reviewed_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                advance = policy["advance_policy"]
                assert isinstance(advance, dict)
                advance["reviewers_may_patch_reviewed_branch"] = True

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn("reviewers may not patch the reviewed branch", errors)

    def test_unexpected_head_movement_must_pause(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                advance = policy["advance_policy"]
                assert isinstance(advance, dict)
                advance["unexpected_head_movement"] = "CONTINUE_ANYWAY"

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn("unexpected head movement must pause and reconcile", errors)

    def test_hidden_background_waiting_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                waiting = policy["waiting_semantics"]
                assert isinstance(waiting, dict)
                waiting["hidden_background_waiting"] = True
                waiting["offscreen_progress_claims"] = True

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn("hidden background waiting is forbidden", errors)
            self.assertIn("offscreen progress claims are forbidden", errors)

    def test_merge_hard_stop_cannot_be_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                stops = policy["hard_stops"]
                assert isinstance(stops, dict)
                stops["merge_without_explicit_user_authority"] = False

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn(
                "workflow hard stop must remain enabled: merge_without_explicit_user_authority",
                errors,
            )

    def test_missing_writer_scope_stop_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                stops = policy["hard_stops"]
                assert isinstance(stops, dict)
                stops.pop("write_outside_active_writer_scope")

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertTrue(
                any("write_outside_active_writer_scope" in error for error in errors)
            )

    def test_handoff_order_cannot_be_rearranged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                sequence = policy["handoff_sequence"]
                assert isinstance(sequence, list)
                sequence[3], sequence[4] = sequence[4], sequence[3]

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn("workflow handoff sequence mismatch", errors)

    def test_policy_cannot_claim_autonomous_self_authorship(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(policy: dict[str, object]) -> None:
                boundary = policy["reality_boundary"]
                assert isinstance(boundary, dict)
                claims = boundary["does_not_establish"]
                assert isinstance(claims, list)
                claims.remove("autonomous self-authorship")

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn(
                "workflow reality boundary missing: autonomous self-authorship",
                errors,
            )

    def test_duplicate_policy_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            path = root / self.artifacts[0]
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    '  "schema": "VERA_IDENTITY_WORKFLOW_CONTINUITY_V1",',
                    '  "schema": "VERA_IDENTITY_WORKFLOW_CONTINUITY_V1",\n'
                    '  "schema": "DUPLICATE",',
                    1,
                ),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_contract(root)
            self.assertTrue(any("duplicate JSON key: schema" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
