import json
from pathlib import Path
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
            self.assertEqual(str(path.relative_to(ROOT)), bindings[key]["path"])
            self.assertEqual(blob, bindings[key]["blob"])


if __name__ == "__main__":
    unittest.main()
