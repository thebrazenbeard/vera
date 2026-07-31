from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts/validate_identity_temporal_anchor.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_identity_temporal_anchor", VALIDATOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class IdentityTemporalAnchorTests(unittest.TestCase):
    artifacts = (
        "architecture/identity/VERA_IDENTITY_TEMPORAL_ANCHOR_V1.json",
        "schemas/vera_identity_temporal_anchor_v1.schema.json",
        "architecture/identity/VERA_PROJECT_IDENTITY_V1.json",
        "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json",
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

    def test_current_temporal_anchor_validates(self) -> None:
        self.assertEqual([], VALIDATOR.validate_contract(ROOT))

    def test_identity_version_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(anchor: dict[str, object]) -> None:
                reference = anchor["identity_ref"]
                assert isinstance(reference, dict)
                reference["version"] = "1.0.1"

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn(
                "temporal anchor identity version does not match canonical identity",
                errors,
            )
            self.assertIn(
                "temporal anchor subject hash does not bind exact versions",
                errors,
            )

    def test_anchor_id_must_bind_exact_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            errors = self.mutate_json(
                root,
                self.artifacts[0],
                lambda anchor: anchor.__setitem__(
                    "anchor_id", "VERA_IDENTITY_TEMPORAL_ANCHOR_V1"
                ),
            )
            self.assertIn(
                "temporal anchor ID must bind the exact identity and behavior versions",
                errors,
            )

    def test_root_anchor_rejects_invented_predecessor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            errors = self.mutate_json(
                root,
                self.artifacts[0],
                lambda anchor: anchor.__setitem__(
                    "predecessor_anchor_ref", "INVENTED_PREDECESSOR"
                ),
            )
            self.assertIn("ROOT temporal anchor forbids a predecessor reference", errors)

    def test_subject_hash_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(anchor: dict[str, object]) -> None:
                binding = anchor["subject_binding"]
                assert isinstance(binding, dict)
                binding["subject_hash"] = "0" * 64

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn(
                "temporal anchor subject hash does not bind exact versions",
                errors,
            )

    def test_unknown_state_time_cannot_claim_effectiveness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            errors = self.mutate_json(
                root,
                self.artifacts[0],
                lambda anchor: anchor.__setitem__("version_effectiveness", "ANCHORED"),
            )
            self.assertIn("Temporal Anchor V1 must remain UNANCHORED", errors)

    def test_unknown_temporal_evidence_forbids_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(anchor: dict[str, object]) -> None:
                roles = anchor["temporal_roles"]
                assert isinstance(roles, dict)
                state = roles["state_time"]
                assert isinstance(state, dict)
                state["value"] = "2026-07-31T01:00:00+00:00"

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn("state_time UNKNOWN evidence forbids timestamps and bounds", errors)

    def test_arbitrary_external_source_cannot_self_certify_exact_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(anchor: dict[str, object]) -> None:
                roles = anchor["temporal_roles"]
                assert isinstance(roles, dict)
                state = roles["state_time"]
                assert isinstance(state, dict)
                state.update({
                    "precision": "EXACT",
                    "source": "EXTERNAL_ADOPTION_EVIDENCE",
                    "temporal_claim": True,
                    "value": "2026-07-31T01:00:00+00:00",
                    "lower_bound": None,
                    "upper_bound": None,
                })
                anchor["version_effectiveness"] = "ANCHORED"

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn(
                "state_time Temporal Anchor V1 forbids caller-certified non-UNKNOWN evidence",
                errors,
            )
            self.assertIn("Temporal Anchor V1 must remain UNANCHORED", errors)

    def test_retrieval_time_cannot_substitute_for_state_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(anchor: dict[str, object]) -> None:
                roles = anchor["temporal_roles"]
                assert isinstance(roles, dict)
                retrieval = roles["retrieval_time"]
                assert isinstance(retrieval, dict)
                retrieval.update({
                    "precision": "EXACT",
                    "source": "HOST_RETRIEVAL_CLOCK",
                    "temporal_claim": True,
                    "value": "2026-07-31T01:00:00+00:00",
                    "lower_bound": None,
                    "upper_bound": None,
                })

            errors = self.mutate_json(root, self.artifacts[0], mutation)
            self.assertIn(
                "retrieval_time Temporal Anchor V1 forbids caller-certified non-UNKNOWN evidence",
                errors,
            )

    def test_backdating_policy_cannot_be_weakened(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            errors = self.mutate_json(
                root,
                self.artifacts[0],
                lambda anchor: anchor.__setitem__("backdating_policy", "ALLOW_IF_PLAUSIBLE"),
            )
            self.assertIn(
                "identity backdating must remain forbidden without verified state_time",
                errors,
            )

    def test_lived_continuity_must_remain_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)

            def mutation(identity: dict[str, object]) -> None:
                reality = identity["reality_boundary"]
                assert isinstance(reality, dict)
                forbidden = reality["forbids_as_established_fact"]
                assert isinstance(forbidden, list)
                forbidden.remove("lived continuity")

            errors = self.mutate_json(root, self.artifacts[2], mutation)
            self.assertIn(
                "identity reality boundary must reject unsupported claim: lived continuity",
                errors,
            )

    def test_duplicate_anchor_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            path = root / self.artifacts[0]
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    '  "schema": "VERA_IDENTITY_TEMPORAL_ANCHOR_V1",',
                    '  "schema": "VERA_IDENTITY_TEMPORAL_ANCHOR_V1",\n'
                    '  "schema": "DUPLICATE",',
                    1,
                ),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_contract(root)
            self.assertTrue(any("duplicate JSON key: schema" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
