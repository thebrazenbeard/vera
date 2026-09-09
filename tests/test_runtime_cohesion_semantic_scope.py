import unittest

from runtime_cohesion.live_sources import classify_semantic_snapshot


class SemanticSnapshotScopeTests(unittest.TestCase):
    def test_explicit_research_staging_remains_research_staging_only(self):
        decision = classify_semantic_snapshot({
            "authority_scope": "RESEARCH_STAGING",
            "state": "ACTIVE",
            "validation_state": "VERIFIED",
        })
        self.assertEqual(decision["status"], "RESEARCH_STAGING_ONLY")
        self.assertFalse(decision["canonical_runtime_semantics"])

    def test_missing_authority_scope_is_unresolved_not_retyped_as_research_staging(self):
        decision = classify_semantic_snapshot({
            "state": "ACTIVE",
            "validation_state": "VERIFIED",
        })
        self.assertEqual(decision["status"], "UNRESOLVED")
        self.assertFalse(decision["canonical_runtime_semantics"])

    def test_unknown_authority_scope_is_unresolved_not_retyped_as_research_staging(self):
        decision = classify_semantic_snapshot({
            "authority_scope": "UNKNOWN_SCOPE",
            "state": "ACTIVE",
            "validation_state": "VERIFIED",
        })
        self.assertEqual(decision["status"], "UNRESOLVED")
        self.assertFalse(decision["canonical_runtime_semantics"])


if __name__ == "__main__":
    unittest.main()
