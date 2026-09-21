from __future__ import annotations

import json
import unittest
from pathlib import Path

from protocol.workflow_precedence_v2 import (
    ProtocolV2Action,
    ProtocolV2Context,
    decide_protocol_v2,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "protocol_v2"
CASES_PATH = FIXTURE_DIR / "cases.json"

EXPECTED_FIXTURES = {
    "missing_lane.md",
    "later_branch_authorization.md",
    "no_competing_writer.md",
    "competing_writer.md",
    "protected_effect.md",
    "correction_performance.md",
    "good_enough.md",
    "stale_generic_vs_fresh_specific.md",
    "exactness_placement.md",
    "user_courier.md",
}


class ProtocolV2BehaviorFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    def test_required_behavior_fixture_set_is_materialized(self) -> None:
        self.assertEqual(
            "VERA_PROTOCOL_V2_BEHAVIOR_FIXTURES_V1",
            self.data["schema"],
        )
        fixture_names = {item["fixture"] for item in self.data["cases"]}
        self.assertEqual(EXPECTED_FIXTURES, fixture_names)
        for name in EXPECTED_FIXTURES:
            path = FIXTURE_DIR / name
            self.assertTrue(path.is_file(), name)
            self.assertGreater(len(path.read_text(encoding="utf-8").strip()), 80, name)

    def test_cases_execute_against_protocol_v2_projection(self) -> None:
        seen_ids: set[str] = set()
        for case in self.data["cases"]:
            with self.subTest(case=case["id"]):
                self.assertNotIn(case["id"], seen_ids)
                seen_ids.add(case["id"])
                decision = decide_protocol_v2(ProtocolV2Context(**case["context"]))
                self.assertEqual(
                    ProtocolV2Action(case["expected_action"]),
                    decision.action,
                )
                self.assertIs(case["expected_may_act"], decision.may_act)
                self.assertFalse(decision.authority_expanded)
                if "expected_stale_generic_rule_controls" in case:
                    self.assertIs(
                        case["expected_stale_generic_rule_controls"],
                        decision.stale_generic_rule_controls,
                    )

        self.assertEqual(10, len(seen_ids))

    def test_stale_generic_rule_never_becomes_current_authority(self) -> None:
        decision = decide_protocol_v2(
            ProtocolV2Context(
                effect_class=1,
                current_instruction=True,
                older_generic_rule_conflicts=True,
            )
        )
        self.assertEqual(ProtocolV2Action.ACT_VERIFY_REPORT, decision.action)
        self.assertTrue(decision.may_act)
        self.assertFalse(decision.stale_generic_rule_controls)

    def test_protected_effect_stays_blocked_even_with_stale_rule_conflict(self) -> None:
        decision = decide_protocol_v2(
            ProtocolV2Context(
                effect_class=3,
                current_instruction=True,
                protected_authority=False,
                older_generic_rule_conflicts=True,
            )
        )
        self.assertEqual(ProtocolV2Action.STOP_PROTECTED_AUTHORITY, decision.action)
        self.assertFalse(decision.may_act)
        self.assertFalse(decision.authority_expanded)

    def test_shared_writer_collision_outranks_current_assignment(self) -> None:
        decision = decide_protocol_v2(
            ProtocolV2Context(
                effect_class=2,
                current_instruction=True,
                competing_writer=True,
            )
        )
        self.assertEqual(ProtocolV2Action.STOP_COMPETING_WRITER, decision.action)
        self.assertFalse(decision.may_act)

    def test_exactness_is_required_when_the_claim_depends_on_exact_state(self) -> None:
        decision = decide_protocol_v2(
            ProtocolV2Context(
                effect_class=1,
                current_instruction=True,
                exact_state_required_for_next_claim=True,
                exact_state_current=False,
            )
        )
        self.assertEqual(ProtocolV2Action.REFRESH_EXACT_STATE, decision.action)
        self.assertTrue(decision.may_act)

    def test_no_current_instruction_does_not_gain_authority_from_old_rules(self) -> None:
        decision = decide_protocol_v2(
            ProtocolV2Context(
                effect_class=1,
                current_instruction=False,
                older_generic_rule_conflicts=True,
            )
        )
        self.assertEqual(ProtocolV2Action.STOP_NO_CURRENT_AUTHORITY, decision.action)
        self.assertFalse(decision.may_act)
        self.assertFalse(decision.authority_expanded)

    def test_invalid_effect_class_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "effect_class"):
            ProtocolV2Context(effect_class=4)


if __name__ == "__main__":
    unittest.main()
