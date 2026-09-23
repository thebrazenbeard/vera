from decimal import Decimal
import unittest

from portfolio_runtime.attune.contracts import InfluenceDecision, validate_influence_decision
from portfolio_runtime.intranel import admission as intranel_admission
from portfolio_runtime.lantern.canonical import canonical_json, sha256_hex
from portfolio_runtime.roots.model import TargetSpec
from portfolio_runtime.roots.normalize import normalize_text, target_forms
from portfolio_runtime.skeletonkey.replay import build_derivation_manifest, assert_replay_match
from portfolio_runtime.skeletonkey.sequence import SequenceFlag, SequenceSample, assess_sequence
from portfolio_runtime.skeletonkey.timing import (
    EventOrder,
    SyncStatus,
    TimingQuality,
    definite_order,
    map_event,
)
from portfolio_runtime.vera_works.contracts import load_states


class AbsorbedPortfolioRuntimeTests(unittest.TestCase):
    def test_roots_normalization_is_live_inside_vera(self):
        target = TargetSpec.from_cli("  Vera   Runtime  ")
        self.assertEqual(normalize_text(target.query_original), "vera runtime")
        self.assertTrue(target_forms(target))

    def test_skeletonkey_replay_is_deterministic(self):
        kwargs = dict(
            parent_content_ids=("sha256:" + "a" * 64,),
            procedure_id="vera-test",
            procedure_version="1",
            parameters={"x": 1},
            output=b"same",
        )
        first = build_derivation_manifest(**kwargs)
        second = build_derivation_manifest(**kwargs)
        assert_replay_match(first, second)
        self.assertEqual(first.output_content_id, sha256_hex(b"same").join(("", "")))

    def test_skeletonkey_sequence_marks_gaps_without_reordering_history(self):
        result = assess_sequence([SequenceSample(1), SequenceSample(3), SequenceSample(2)])
        self.assertEqual(result.raw_arrival_order, (1, 3, 2))
        self.assertIn(SequenceFlag.GAP, result.flags)
        self.assertIn(SequenceFlag.REORDERED, result.flags)

    def test_skeletonkey_timing_fails_closed_on_overlap(self):
        quality = TimingQuality(
            status=SyncStatus.SYNCHRONIZED,
            offset_bound=Decimal("0.1"),
            jitter_bound=Decimal("0"),
            capture_path_uncertainty_bound=Decimal("0"),
            resolution=Decimal("0"),
            drift_bound_per_second=Decimal("0"),
        )
        a = map_event(estimated_time=Decimal("1.0"), quality=quality, elapsed_since_last_sync=Decimal("0"))
        b = map_event(estimated_time=Decimal("1.1"), quality=quality, elapsed_since_last_sync=Decimal("0"))
        self.assertEqual(definite_order(a, b), EventOrder.ORDER_UNRESOLVED)

    def test_attune_commercial_signals_cannot_shape_protected_relationship_behavior(self):
        with self.assertRaisesRegex(ValueError, "commercial signals"):
            validate_influence_decision(
                InfluenceDecision(
                    behavior="AFFECTION_INTENSITY",
                    reason="test",
                    commercial_inputs=("REVENUE",),
                )
            )

    def test_intranel_admission_module_is_importable_under_vera_ownership(self):
        self.assertTrue(callable(intranel_admission.operation_digest))
        self.assertTrue(callable(intranel_admission.admit_message))

    def test_lantern_canonical_records_are_deterministic(self):
        self.assertEqual(canonical_json({"b": 2, "a": 1}), '{"a":1,"b":2}')
        self.assertEqual(len(sha256_hex(b"vera")), 64)

    def test_vera_works_state_contract_is_local(self):
        states = load_states()
        self.assertIn("assignment", states["states"])
        self.assertIn("hold", states["states"])


if __name__ == "__main__":
    unittest.main()
