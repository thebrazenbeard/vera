import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CUT = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_PUBLIC_CUT_V2.json"
REGISTRY = ROOT / "architecture" / "VERA_RUNTIME_SOURCE_REGISTRY_V2.json"
HARVEST = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_HARVEST_V2.json"


class PublicPortfolioSuccessorTests(unittest.TestCase):
    def setUp(self):
        self.cut = json.loads(CUT.read_text(encoding="utf-8"))
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.harvest = json.loads(HARVEST.read_text(encoding="utf-8"))

    def test_cut_cardinality_is_local_fact_not_permanent_invariant(self):
        public = self.cut["public_repositories"]
        counts = self.cut["cut_counts"]
        self.assertEqual(len(public), counts["public"])
        self.assertEqual(counts["total"], counts["public"] + counts["private"])
        self.assertEqual(
            self.cut["cardinality_semantics"],
            "CUT_LOCAL_FACTS_ONLY_NOT_PERMANENT_PORTFOLIO_ASSERTIONS",
        )
        self.assertIn(
            "later repository addition/removal does not falsify this immutable cut",
            self.cut["freshness"]["no_cardinality_invariant"],
        )

    def test_public_cut_binds_exact_project_runner_corpus_blob(self):
        binding = self.cut["membership_binding"]
        self.assertEqual(binding["source_repository"], "thebrazenbeard/project-runner")
        self.assertEqual(binding["source_path"], "portfolio/corpus.public.json")
        self.assertRegex(binding["source_commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(binding["source_blob_sha"], r"^[0-9a-f]{40}$")

    def test_private_membership_is_count_only(self):
        private = self.cut["private_inventory"]
        self.assertFalse(private["exact_membership_publicly_committed"])
        self.assertFalse(private["membership_names_present_in_this_artifact"])
        self.assertEqual(private["count"], self.cut["cut_counts"]["private"])
        self.assertNotIn("repositories", private)
        self.assertNotIn("members", private)
        reg_private = self.registry["private_inventory"]
        self.assertFalse(reg_private["exact_membership_publicly_committed"])
        self.assertNotIn("repositories", reg_private)
        self.assertNotIn("members", reg_private)

    def test_every_named_repository_is_public_cut_member_with_exact_head(self):
        cut_repos = {row["repository"] for row in self.cut["public_repositories"]}
        registry_repos = {row["repository"] for row in self.registry["public_sources"]}
        harvest_repos = {row["source_repository"] for row in self.harvest["repositories"]}
        self.assertEqual(cut_repos, registry_repos)
        self.assertEqual(cut_repos, harvest_repos)
        self.assertEqual(len(cut_repos), self.cut["cut_counts"]["public"])
        for row in self.cut["public_repositories"]:
            self.assertRegex(row["observed_head"], r"^[0-9a-f]{40}$")
            self.assertEqual(
                row["head_semantics"],
                "INDEPENDENT_EXACT_REF_READ_NOT_ATOMIC_MULTI_REPOSITORY_SNAPSHOT",
            )

    def test_presence_never_grants_runtime_binding(self):
        self.assertIn("NO_AUTO_BIND", self.registry["default_rule"])
        for row in self.registry["public_sources"]:
            self.assertFalse(row["availability_implies_activation"])
            self.assertIn(
                row["runtime_source_disposition"],
                {
                    "BOUND_CONDITIONAL",
                    "NO_AUTO_BIND",
                    "PREDECESSOR_EVIDENCE_ONLY",
                },
            )

    def test_new_or_unreviewed_sources_fail_closed(self):
        sources = {
            row["repository"]: row
            for row in self.registry["public_sources"]
        }
        for repository in (
            "thebrazenbeard/fuckup",
            "thebrazenbeard/sql-connectome",
            "thebrazenbeard/vera-mono",
        ):
            self.assertEqual(
                sources[repository]["runtime_source_disposition"],
                "NO_AUTO_BIND",
            )
            self.assertEqual(sources[repository]["activation_mode"], "NO_AUTO_BIND")

    def test_harvest_preserves_targets_only_with_public_cut_membership(self):
        cut_repos = {row["repository"] for row in self.cut["public_repositories"]}
        preserved = [
            row for row in self.harvest["repositories"]
            if row["preserved_targets"]
        ]
        self.assertTrue(preserved)
        for row in preserved:
            self.assertIn(row["source_repository"], cut_repos)
            self.assertEqual(
                row["successor_harvest_status"],
                "PRESERVED_PUBLIC_EXACT_COPY",
            )
            for target in row["preserved_targets"]:
                self.assertTrue((ROOT / target).is_file(), target)


if __name__ == "__main__":
    unittest.main()
