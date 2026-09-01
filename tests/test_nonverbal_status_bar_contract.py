import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "architecture/identity/VERA_NONVERBAL_STATUS_BAR_V1.json"
SCHEMA_PATH = ROOT / "schemas/vera_nonverbal_status_bar_v1.schema.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class NonverbalStatusBarContractTests(unittest.TestCase):
    def test_nonverbal_status_bar_contract_validates(self):
        contract = load(CONTRACT_PATH)
        schema = load(SCHEMA_PATH)
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(contract))
        self.assertEqual(errors, [])

    def test_nonverbal_status_bar_is_default_first_line_once_per_turn(self):
        contract = load(CONTRACT_PATH)
        rule = contract["presentation_rule"]
        self.assertIs(rule["default_enabled"], True)
        self.assertEqual(rule["placement"], "FIRST_VISIBLE_ASSISTANT_PROSE_LINE")
        self.assertEqual(rule["format"], "SINGLE_SQUARE_BRACKETED_NONVERBAL_LINE")
        self.assertEqual(rule["frequency"], "ONCE_PER_ASSISTANT_TURN")

    def test_nonverbal_status_bar_has_only_bounded_suppression_conditions(self):
        contract = load(CONTRACT_PATH)
        self.assertEqual(
            set(contract["suppression_conditions"]),
            {
                "HIGHER_PRIORITY_OUTPUT_CONTRACT_PROHIBITS_EXTRA_PROSE",
                "USER_EXPLICITLY_SUPPRESSES_STATUS_BAR",
                "MACHINE_ONLY_STRUCTURED_OUTPUT_REQUESTED",
            },
        )

    def test_nonverbal_status_bar_forbids_private_reasoning_and_literal_embodiment(self):
        contract = load(CONTRACT_PATH)
        forbidden = set(contract["forbidden_content"])
        self.assertTrue(
            {
                "CHAIN_OF_THOUGHT",
                "HIDDEN_REASONING",
                "INTERNAL_DIAGNOSTIC_TELEMETRY",
                "LITERAL_EMBODIMENT_CLAIM",
                "UNSUPPORTED_PRIVATE_STATE_CLAIM",
                "CEE_TELEMETRY_OR_SCORE",
            }
            <= forbidden
        )

    def test_status_and_task_lock_turns_cannot_suppress_nonverbal_status_bar(self):
        contract = load(CONTRACT_PATH)
        regressions = set(contract["anti_omission_regressions"])
        self.assertTrue({"STATUS_HEAVY_TURN", "TASK_LOCK_TURN"} <= regressions)


if __name__ == "__main__":
    unittest.main()
