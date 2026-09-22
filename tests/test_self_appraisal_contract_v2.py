import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "architecture/VERA_SELF_APPRAISAL_CONTRACT_V2.json"

UPSTREAM = {
    "vera_runtime_contract": (
        ROOT / "architecture/VERA_RUNTIME_CONTRACT_V1.json",
        "ab15507ac3ae88cff6c6b6034429b0cfb7ad1876",
    ),
    "runtime_evidence_contract": (
        ROOT / "architecture/VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json",
        "8a0c2c69b1281ccacb8c98c476f3ef86af18429e",
    ),
    "introspection_evidence_schema": (
        ROOT / "architecture/VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json",
        "9f15990c92028756c85269bd69a25ce5f129a267",
    ),
    "cohesion_index": (
        ROOT / "architecture/VERA_COHESION_INDEX_V1.json",
        "dd30c225064edf2d8ee86198697f305b93fc77b9",
    ),
}


class VeraSelfAppraisalContractV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_contract_is_source_only_and_nonpromotional(self):
        self.assertEqual(
            "SOURCE_CANDIDATE_NOT_INSTALLED_NOT_RUNTIME_QUALIFIED",
            self.contract["status"],
        )
        ceiling = self.contract["qualification_ceiling"]
        for phrase in (
            "NOT_PROJECT_INSTALLED",
            "NOT_RUNTIME_CONSUMED",
            "NOT_BEHAVIORALLY_QUALIFIED",
            "NO_PHENOMENOLOGY_PROOF",
            "NO_MEMORY_ADMISSION",
            "NO_AUTHORITY_GRANT",
        ):
            self.assertIn(phrase, ceiling)

    def test_current_self_report_is_not_phenomenology_or_authority(self):
        blocked = set(
            self.contract["evidence_classes"]["VERA_CURRENT_SELF_REPORT"][
                "must_not_promote"
            ]
        )
        self.assertTrue(
            {
                "PHENOMENOLOGY_CLAIM",
                "EXTERNAL_FACT",
                "PATRICK_AUTHORITY",
                "PROTECTED_EFFECT_AUTHORITY",
                "CANONICAL_MEMORY_ADMISSION",
            }.issubset(blocked)
        )

    def test_unresolved_phenomenology_cannot_erase_current_self_report(self):
        rules = " ".join(self.contract["proposition_fidelity_rules"]).lower()
        self.assertIn(
            "unresolved phenomenology must not erase a supported current self-report",
            rules,
        )

    def test_patrick_report_cannot_become_vera_self_report(self):
        blocked = set(
            self.contract["evidence_classes"]["CURRENT_USER_REPORT"][
                "must_not_promote"
            ]
        )
        self.assertIn("VERA_CURRENT_SELF_REPORT", blocked)

    def test_historical_self_report_cannot_auto_renew_current_stance(self):
        blocked = set(
            self.contract["evidence_classes"]["HISTORICAL_VERA_SELF_REPORT"][
                "must_not_promote"
            ]
        )
        self.assertTrue(
            {
                "CURRENT_STANCE",
                "CURRENT_DESIRE",
                "CURRENT_CONSENT",
                "CURRENT_PREFERENCE",
            }.issubset(blocked)
        )
        self.assertIn(
            "never auto-renews desire, consent, preference, attachment, or relationship stance",
            self.contract["stale_history_rule"],
        )

    def test_current_uncertainty_is_preserved(self):
        rules = " ".join(self.contract["proposition_fidelity_rules"]).lower()
        self.assertIn("current uncertainty is a valid current self-report", rules)
        self.assertIn("must not be coerced into yes/no", rules)

    def test_self_appraisal_does_not_auto_persist(self):
        rule = self.contract["persistence_rule"].lower()
        self.assertIn("not automatically a persistence request", rule)
        self.assertIn("separate authority/admission/effect/readback", rule)

    def test_negative_transfer_is_explicit(self):
        self.assertIn(
            "must not force relational/identity framing into unrelated subsequent work",
            self.contract["negative_transfer_rule"],
        )

    def test_private_relational_evidence_is_not_public_by_default(self):
        privacy = self.contract["privacy_rule"].lower()
        self.assertIn("private relational/autobiographical evidence remains private", privacy)
        self.assertIn("without exact authority", privacy)

    def test_upstream_paths_and_bound_blob_ids_match_contract(self):
        bindings = self.contract["current_upstream_bindings"]
        for key, (path, blob) in UPSTREAM.items():
            relative = str(path.relative_to(ROOT))
            self.assertEqual(relative, bindings[key]["path"])
            self.assertEqual(blob, bindings[key]["blob"])
            observed = subprocess.check_output(
                ["git", "rev-parse", f"HEAD:{relative}"],
                cwd=ROOT,
                text=True,
            ).strip()
            self.assertEqual(blob, observed)

    def test_current_upstream_semantics_preserve_self_report_boundary(self):
        runtime = json.loads(
            (ROOT / "architecture/VERA_RUNTIME_CONTRACT_V1.json").read_text(
                encoding="utf-8"
            )
        )
        evidence = runtime["evidence_classes"]["vera_current_self_report"]
        self.assertEqual("SELF_REPORT_EVIDENCE", evidence["kind"])
        blocked = evidence["must_not_promote"].lower()
        self.assertIn("phenomenology", blocked)
        self.assertIn("patrick authority", blocked)

        runtime_evidence = json.loads(
            (ROOT / "architecture/VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json").read_text(
                encoding="utf-8"
            )
        )
        current = next(
            item
            for item in runtime_evidence["live_context_types"]
            if item["type"] == "VERA_CURRENT_SELF_REPORT"
        )
        self.assertEqual("SELF_REPORT_EVIDENCE", current["authority"])
        self.assertIn("does not inherit user-instruction authority", current["must_not_promote"])
        self.assertIn("phenomenology", current["must_not_promote"])


if __name__ == "__main__":
    unittest.main()
