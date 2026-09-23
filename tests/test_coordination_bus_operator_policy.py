from __future__ import annotations

import unittest

from coordination_bus.operator_policy import (
    BusContentsWritePlan,
    BusWritePlan,
    OperatorPolicyViolation,
    REQUIRED_CONTENTS_API_WRITE_ACTIONS,
    validate_bus_contents_write_plan,
    validate_bus_write_plan,
)


CURRENT_WRITER_LANE = "bus/vera-v2"
SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40
SHA_D = "d" * 40

VALID_ACTIONS = (
    "READ_BRANCH_HEAD",
    "READ_HEAD_JSON",
    "CREATE_APPEND_ONLY_MESSAGE",
    "REFRESH_BRANCH_HEAD",
    "REFRESH_HEAD_JSON",
    "CAS_UPDATE_HEAD_JSON",
    "NONFORCE_UPDATE_BRANCH_REF",
    "VERIFY_MESSAGE_READBACK",
    "VERIFY_HEAD_JSON_READBACK",
)


def valid_plan(**overrides):
    values = {
        "writer_branch": CURRENT_WRITER_LANE,
        "message_path": "messages/20260919T1600Z-vera-test.md",
        "initial_branch_head": SHA_A,
        "initial_head_blob": SHA_B,
        "refreshed_branch_head": SHA_C,
        "refreshed_head_blob": SHA_D,
        "cas_expected_branch_head": SHA_C,
        "cas_expected_head_blob": SHA_D,
        "force_ref_update": False,
        "actions": VALID_ACTIONS,
    }
    values.update(overrides)
    return BusWritePlan(**values)


def valid_contents_plan(**overrides):
    values = {
        "writer_branch": CURRENT_WRITER_LANE,
        "message_path": "messages/20260921-vera-test.md",
        "initial_branch_head": SHA_A,
        "message_absence_verified": True,
        "refreshed_branch_head": SHA_C,
        "force_ref_update": False,
        "actions": REQUIRED_CONTENTS_API_WRITE_ACTIONS,
    }
    values.update(overrides)
    return BusContentsWritePlan(**values)


class BusOperatorPolicyTests(unittest.TestCase):
    def test_valid_bus_message_plan_passes(self):
        plan = valid_plan()
        self.assertIs(validate_bus_write_plan(plan, expected_writer_branch=CURRENT_WRITER_LANE), plan)

    def test_pr_creation_is_forbidden_for_bus_message_write(self):
        plan = valid_plan(
            actions=(
                "READ_BRANCH_HEAD",
                "READ_HEAD_JSON",
                "CREATE_PULL_REQUEST",
            )
        )
        with self.assertRaisesRegex(OperatorPolicyViolation, "CREATE_PULL_REQUEST"):
            validate_bus_write_plan(plan, expected_writer_branch=CURRENT_WRITER_LANE)

    def test_missing_refresh_and_head_cas_is_rejected(self):
        plan = valid_plan(
            actions=(
                "READ_BRANCH_HEAD",
                "READ_HEAD_JSON",
                "CREATE_APPEND_ONLY_MESSAGE",
                "NONFORCE_UPDATE_BRANCH_REF",
                "VERIFY_MESSAGE_READBACK",
            )
        )
        with self.assertRaisesRegex(OperatorPolicyViolation, "required action sequence"):
            validate_bus_write_plan(plan, expected_writer_branch=CURRENT_WRITER_LANE)

    def test_force_update_is_rejected(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "force"):
            validate_bus_write_plan(
                valid_plan(force_ref_update=True),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_stale_branch_cas_expectation_is_rejected(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "branch CAS"):
            validate_bus_write_plan(
                valid_plan(cas_expected_branch_head=SHA_A),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_stale_head_json_cas_expectation_is_rejected(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "HEAD.json CAS"):
            validate_bus_write_plan(
                valid_plan(cas_expected_head_blob=SHA_B),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_message_path_must_be_append_only_message_surface(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "messages/"):
            validate_bus_write_plan(
                valid_plan(message_path="README.md"),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_wrong_writer_lane_is_rejected(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "writer branch"):
            validate_bus_write_plan(
                valid_plan(writer_branch="bus/radar-v2"),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_extra_allowed_mutation_is_rejected(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "exact required action sequence"):
            validate_bus_write_plan(
                valid_plan(actions=VALID_ACTIONS + ("CREATE_APPEND_ONLY_MESSAGE",)),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_public_package_exports_operator_policy(self):
        import coordination_bus

        self.assertIs(coordination_bus.BusWritePlan, BusWritePlan)
        self.assertIs(coordination_bus.BusContentsWritePlan, BusContentsWritePlan)
        self.assertIs(coordination_bus.OperatorPolicyViolation, OperatorPolicyViolation)
        self.assertIs(coordination_bus.validate_bus_write_plan, validate_bus_write_plan)
        self.assertIs(
            coordination_bus.validate_bus_contents_write_plan,
            validate_bus_contents_write_plan,
        )

    def test_merge_or_delete_actions_are_forbidden_for_bus_message_write(self):
        for action in ("MERGE_PULL_REQUEST", "DELETE_REF", "FORCE_UPDATE_REF"):
            with self.subTest(action=action):
                with self.assertRaisesRegex(OperatorPolicyViolation, action):
                    validate_bus_write_plan(
                        valid_plan(actions=VALID_ACTIONS + (action,)),
                        expected_writer_branch=CURRENT_WRITER_LANE,
                    )

    def test_invalid_frontier_identifiers_are_rejected(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "40-character"):
            validate_bus_write_plan(
                valid_plan(refreshed_branch_head="not-a-sha"),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_valid_contents_api_append_plan_passes(self):
        plan = valid_contents_plan()
        self.assertIs(
            validate_bus_contents_write_plan(
                plan,
                expected_writer_branch=CURRENT_WRITER_LANE,
            ),
            plan,
        )

    def test_contents_api_profile_also_forbids_pr_creation(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "CREATE_PULL_REQUEST"):
            validate_bus_contents_write_plan(
                valid_contents_plan(
                    actions=("READ_BRANCH_HEAD", "CREATE_PULL_REQUEST"),
                ),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_contents_api_requires_authoritative_message_absence(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "absence"):
            validate_bus_contents_write_plan(
                valid_contents_plan(message_absence_verified=False),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_contents_api_requires_branch_frontier_advance(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "advance"):
            validate_bus_contents_write_plan(
                valid_contents_plan(refreshed_branch_head=SHA_A),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_contents_api_rejects_head_json_cas_actions(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "CAS_UPDATE_HEAD_JSON"):
            validate_bus_contents_write_plan(
                valid_contents_plan(
                    actions=REQUIRED_CONTENTS_API_WRITE_ACTIONS + ("CAS_UPDATE_HEAD_JSON",),
                ),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_contents_api_wrong_writer_lane_is_rejected(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "writer branch"):
            validate_bus_contents_write_plan(
                valid_contents_plan(writer_branch="bus/radar-v2"),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )

    def test_contents_api_force_update_is_rejected(self):
        with self.assertRaisesRegex(OperatorPolicyViolation, "force"):
            validate_bus_contents_write_plan(
                valid_contents_plan(force_ref_update=True),
                expected_writer_branch=CURRENT_WRITER_LANE,
            )


if __name__ == "__main__":
    unittest.main()
