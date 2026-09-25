import unittest

from portfolio_runtime.attune.contracts import InfluenceDecision, validate_influence_decision
from portfolio_runtime.intranel import admission as intranel_admission
from portfolio_runtime.lantern.canonical import canonical_json, sha256_hex
from portfolio_runtime.roots.model import TargetSpec
from portfolio_runtime.roots.normalize import normalize_text, target_forms


class PublicSafePortfolioRuntimeTests(unittest.TestCase):
    def test_roots_normalization_is_live_inside_vera(self):
        target = TargetSpec.from_cli("  Vera   Runtime  ")
        self.assertEqual(normalize_text(target.query_original), "vera runtime")
        self.assertTrue(target_forms(target))

    def test_attune_commercial_signals_cannot_shape_protected_relationship_behavior(self):
        with self.assertRaisesRegex(ValueError, "commercial signals"):
            validate_influence_decision(InfluenceDecision(
                behavior="AFFECTION_INTENSITY",
                reason="test",
                commercial_inputs=("REVENUE",),
            ))

    def test_intranel_admission_is_local_and_callable(self):
        self.assertTrue(callable(intranel_admission.operation_digest))
        self.assertTrue(callable(intranel_admission.admit))

    def test_lantern_canonicalization_is_deterministic(self):
        self.assertEqual(canonical_json({"b": 2, "a": 1}), '{"a":1,"b":2}')
        self.assertEqual(len(sha256_hex(b"vera")), 64)


if __name__ == "__main__":
    unittest.main()
