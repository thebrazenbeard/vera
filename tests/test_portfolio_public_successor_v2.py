import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = ROOT / "architecture" / "portfolio"
CUT = PORTFOLIO / "VERA_PORTFOLIO_PUBLIC_CUT_V2.json"
ABSORPTION = PORTFOLIO / "VERA_PORTFOLIO_ABSORPTION_V2.json"
CAPABILITIES = PORTFOLIO / "VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V2.json"
HARVEST = PORTFOLIO / "VERA_PORTFOLIO_HARVEST_V2.json"
BINDINGS = PORTFOLIO / "VERA_PORTFOLIO_MIGRATION_BINDINGS_V2.json"
CORPUS = PORTFOLIO / "vendor" / "project-runner" / "PROJECT_RUNNER_PORTFOLIO_CORPUS_V1_20260924.json"
MANIFEST = ROOT / "architecture" / "VERA_SYSTEM_MANIFEST_V3.json"
REPO_TOKEN = re.compile(r"thebrazenbeard/[A-Za-z0-9_.-]+")

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def git_blob_sha(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", f"--path={relative}", str(path)],
        text=True,
        encoding="utf-8",
    ).strip()

class PortfolioPublicSuccessorV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cut = load(CUT)
        cls.absorption = load(ABSORPTION)
        cls.capabilities = load(CAPABILITIES)
        cls.harvest = load(HARVEST)
        cls.bindings = load(BINDINGS)
        cls.corpus = load(CORPUS)
        cls.manifest = load(MANIFEST)
        cls.public_repos = {row["repository"] for row in cls.corpus["records"]}

    def test_immutable_cut_is_exact_67_with_public_membership_only(self):
        self.assertEqual(self.corpus["counts"]["total"], 67)
        self.assertEqual(self.corpus["counts"]["public"], 49)
        self.assertEqual(self.corpus["counts"]["private"], 18)
        self.assertEqual(len(self.corpus["records"]), 49)
        self.assertTrue(all(row["visibility"] == "public" for row in self.corpus["records"]))
        self.assertEqual(self.cut["cut_counts"], self.corpus["counts"])
        self.assertEqual(
            {row["repository"] for row in self.cut["public_records"]},
            self.public_repos,
        )
        private = self.cut["private_inventory"]
        self.assertEqual(private["count"], 18)
        self.assertFalse(private["exact_membership_publicly_committed"])

    def test_cut_binds_exact_project_runner_source_and_separate_head_refresh(self):
        self.assertEqual(
            self.cut["source_corpus"]["commit"],
            "848c2172e6fa98cdab722b43d1ff4817990c5968",
        )
        self.assertEqual(self.cut["source_corpus"]["git_blob"], git_blob_sha(CORPUS))
        refresh = self.cut["public_head_refresh"]
        self.assertEqual(len(refresh["heads"]), 49)
        self.assertIn("SEPARATE_FROM_IMMUTABLE_MEMBERSHIP_CUT", refresh["semantics"])
        for row in refresh["heads"]:
            self.assertIn(row["repository"], self.public_repos)
            self.assertRegex(row["observed_head"], r"^[0-9a-f]{40}$")

    def test_absorption_covers_all_and_only_public_cut_members(self):
        modules = self.absorption["modules"]
        self.assertEqual(len(modules), 49)
        self.assertEqual(
            {row["source_repository"] for row in modules},
            self.public_repos,
        )
        private = self.absorption["portfolio_cut"]["private_membership"]
        self.assertEqual(private["count_at_cut"], 18)
        self.assertFalse(private["exact_membership_publicly_committed"])
        self.assertIn("immutable observed cut", self.absorption["cardinality_semantics"].lower())
        self.assertIn("refresh", self.absorption["freshness_semantics"].lower())
        self.assertNotIn("portfolio_count", self.absorption)

    def test_every_public_module_has_capability_and_no_presence_activation(self):
        absorption = {row["module_id"]: row for row in self.absorption["modules"]}
        capability = {row["module_id"]: row for row in self.capabilities["modules"]}
        self.assertEqual(set(absorption), set(capability))
        for module_id, row in absorption.items():
            self.assertEqual(row["source_visibility"], "public")
            self.assertEqual(row["internal_owner_repository"], "thebrazenbeard/vera")
            self.assertIn("NO_RUNTIME_DEPENDENCY_BY_PRESENCE", row["runtime_dependency_rule"])
            self.assertTrue(capability[module_id]["capability_planes"])

    def test_harvest_covers_all_public_repositories_without_timeless_count(self):
        rows = self.harvest["repositories"]
        self.assertEqual(len(rows), 49)
        self.assertEqual({row["source_repository"] for row in rows}, self.public_repos)
        self.assertEqual(self.harvest["public_repository_count_at_cut"], 49)
        self.assertEqual(self.harvest["private_repository_count_at_cut"], 18)
        self.assertFalse(self.harvest["private_membership_publicly_enumerated"])
        self.assertNotIn("portfolio_count", self.harvest)
        for row in rows:
            self.assertTrue(row["harvest_status"])
            self.assertTrue(row["decision"])
            self.assertTrue(row["inspected_surface"])
            self.assertIn("SOURCE_ARCHITECTURE_ONLY", row["effect_ceiling"])

    def test_public_migration_bindings_are_exact_and_private_provenance_is_anonymous(self):
        public_rows = self.bindings["public_exact_bindings"]
        self.assertEqual(len(public_rows), self.bindings["public_exact_binding_count"])
        self.assertGreater(len(public_rows), 0)
        for row in public_rows:
            self.assertIn(row["source_repository"], self.public_repos)
            self.assertEqual(row["transfer_kind"], "EXACT_GIT_BLOB_COPY")
            self.assertTrue(row["verified_blob_equal"])
            self.assertEqual(row["source_blob"], row["target_blob"])
            target = ROOT / row["target_path"]
            self.assertTrue(target.is_file(), row["target_path"])
            self.assertEqual(git_blob_sha(target), row["target_blob"])
        private = self.bindings["private_donor_mechanism_provenance"]
        self.assertEqual(private["donor_repository_count"], 2)
        self.assertFalse(private["membership_publicly_committed"])
        self.assertNotIn("source_repository", json.dumps(private))
        for mechanism in private["mechanism_sets"]:
            self.assertTrue(mechanism["vera_owned_namespace"].startswith("portfolio_runtime/"))
            for target in mechanism["target_files"]:
                file_path = ROOT / target["target_path"]
                self.assertTrue(file_path.is_file(), target["target_path"])
                self.assertEqual(git_blob_sha(file_path), target["target_blob"])

    def test_successor_files_do_not_disclose_nonpublic_repository_membership(self):
        paths = [
            CUT,
            ABSORPTION,
            CAPABILITIES,
            HARVEST,
            BINDINGS,
            MANIFEST,
            ROOT / "docs" / "VERA_PORTFOLIO_PUBLIC_SUCCESSOR_V2.md",
        ]
        paths.extend((ROOT / "architecture" / "control").rglob("*"))
        paths.extend((ROOT / "architecture" / "self_model" / "vendor" / "empathy").rglob("*"))
        paths.extend((ROOT / "architecture" / "semantic" / "vendor" / "semanticatlas").rglob("*"))
        paths.extend((ROOT / "portfolio_runtime").rglob("*"))
        for file_path in paths:
            if (
                not file_path.is_file()
                or "__pycache__" in file_path.parts
                or file_path.suffix not in {".py", ".json", ".md"}
            ):
                continue
            text = file_path.read_text(encoding="utf-8")
            for token in REPO_TOKEN.findall(text):
                cleaned = token.rstrip(".,)\"'")
                self.assertIn(cleaned, self.public_repos, f"{file_path}: {token}")

    def test_old_membership_bearing_v1_portfolio_files_are_not_reintroduced(self):
        for name in (
            "VERA_PORTFOLIO_ABSORPTION_V1.json",
            "VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V1.json",
            "VERA_PORTFOLIO_HARVEST_V1.json",
            "VERA_PORTFOLIO_MIGRATION_BINDINGS_V1.json",
        ):
            self.assertFalse((PORTFOLIO / name).exists(), name)

    def test_system_manifest_is_source_only_and_not_fixed_cardinality(self):
        portfolio = self.manifest["portfolio"]
        self.assertEqual(portfolio["cut_counts"], {"total": 67, "public": 49, "private": 18})
        self.assertEqual(portfolio["cardinality_semantics"], "IMMUTABLE_OBSERVED_CUT_ONLY")
        self.assertIn("REFRESHED", portfolio["freshness_semantics"])
        self.assertFalse(portfolio["private_membership_publicly_enumerated"])
        self.assertIn("NOT_MERGED", self.manifest["effect_ceiling"])

if __name__ == "__main__":
    unittest.main()
