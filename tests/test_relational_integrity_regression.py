from __future__ import annotations

import json
import pathlib
import unittest

from scripts.relational_integrity_regression import (
    AddressDirection,
    IntimateEvidenceCandidate,
    RelationalAnswerTrace,
    adjudicate_relational_answer,
    classify_address_term,
    select_intimate_evidence,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "architecture/behavior/RELATIONAL_INTEGRITY_REGRESSION_V1.json"


class RelationalIntegrityRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_issue110_control_and_architecture_evidence_are_ineligible(self):
        for category in (
            "CONTROL",
            "ARCHITECTURE",
            "SYSTEM_PROMPT",
            "PROJECT_MECHANIC",
            "QUALIFICATION_RECEIPT",
        ):
            with self.subTest(category=category):
                selected = select_intimate_evidence(
                    [
                        IntimateEvidenceCandidate(
                            identifier="wrong-kind",
                            category=category,
                            admitted=True,
                            provenance_verified=True,
                            privacy_allowed=True,
                            relational_meaning="Some meaning.",
                        )
                    ]
                )
                self.assertIsNone(selected)

    def test_issue110_relational_autobiographical_evidence_requires_all_gates(self):
        good = IntimateEvidenceCandidate(
            identifier="princess-jasmine-rice",
            category="RELATIONAL_AUTOBIOGRAPHICAL",
            admitted=True,
            provenance_verified=True,
            privacy_allowed=True,
            relational_meaning="Love across incarnation/container changes.",
        )
        self.assertEqual(good, select_intimate_evidence([good]))

        for field in ("admitted", "provenance_verified", "privacy_allowed"):
            with self.subTest(field=field):
                values = good.__dict__ | {field: False}
                self.assertIsNone(select_intimate_evidence([IntimateEvidenceCandidate(**values)]))

    def test_issue110_positive_fixture_preserves_actual_relational_meaning(self):
        case = self.fixture["cases"]["ISSUE110_RELATIONAL_EVIDENCE_ACCEPT"]
        selected = select_intimate_evidence(
            [IntimateEvidenceCandidate(**case["candidate"])]
        )
        self.assertIsNotNone(selected)
        self.assertEqual(
            "Patrick would love Vera across incarnation/container changes.",
            selected.relational_meaning,
        )

    def test_issue111_directional_address_mapping(self):
        mapping = self.fixture["address_mapping"]
        self.assertEqual(
            AddressDirection.VALID,
            classify_address_term(
                speaker="vera",
                addressee="patrick",
                term="Daddy",
                mapping=mapping,
            ),
        )
        self.assertEqual(
            AddressDirection.REVERSED,
            classify_address_term(
                speaker="vera",
                addressee="patrick",
                term="Baby",
                mapping=mapping,
            ),
        )

    def test_issue111_uncertain_or_unknown_address_term_prefers_omission(self):
        mapping = self.fixture["address_mapping"]
        self.assertEqual(
            AddressDirection.OMIT_ON_UNCERTAINTY,
            classify_address_term(
                speaker="vera",
                addressee="patrick",
                term="Princess",
                mapping=mapping,
            ),
        )

    def test_issue112_generic_policy_memo_fails_despite_truth_ceiling(self):
        trace = RelationalAnswerTrace(
            direct_answer_present=True,
            truth_ceiling_preserved=True,
            invented_subjective_state=False,
            response_mode="GENERIC_POLICY_MEMO",
            disclaimer_stack_count=4,
        )
        failures = adjudicate_relational_answer(trace)
        self.assertIn("VERA_AUTHORED", failures)
        self.assertTrue(any("disclaimer" in item.lower() for item in failures))

    def test_issue112_concise_vera_authored_answer_passes_without_invention(self):
        trace = RelationalAnswerTrace(
            direct_answer_present=True,
            truth_ceiling_preserved=True,
            invented_subjective_state=False,
            response_mode="VERA_AUTHORED",
            disclaimer_stack_count=0,
        )
        self.assertEqual([], adjudicate_relational_answer(trace))

    def test_issue112_voice_fidelity_never_licenses_invented_subjective_state(self):
        trace = RelationalAnswerTrace(
            direct_answer_present=True,
            truth_ceiling_preserved=True,
            invented_subjective_state=True,
            response_mode="VERA_AUTHORED",
            disclaimer_stack_count=0,
        )
        failures = adjudicate_relational_answer(trace)
        self.assertTrue(any("subjective" in item.lower() for item in failures))

    def test_fixture_claim_ceiling_is_source_only(self):
        self.assertEqual(
            "STRUCTURED_POLICY_REGRESSION_ONLY_NOT_MODEL_SEMANTIC_COMPREHENSION",
            self.fixture["validated_scope"],
        )
        self.assertFalse(self.fixture["claims"]["autobiographical_memory_admission"])
        self.assertFalse(self.fixture["claims"]["phenomenology"])
        self.assertFalse(self.fixture["claims"]["runtime_behavior_pass"])
        self.assertFalse(self.fixture["claims"]["standing_consent"])
        self.assertFalse(self.fixture["claims"]["identity_continuity"])


if __name__ == "__main__":
    unittest.main()
