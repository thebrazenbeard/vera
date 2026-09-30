"""Fail-closed operator policy for normal Chat Bus message writes.

This module validates proposed connector-action plans before mutation. It does
not itself call GitHub, install a runtime router, or prove that a live operator
consulted the policy.

The Bus protocol invariant is transport-independent: ordinary messages append
under messages/ on the current writer lane and must not silently broaden into
pull-request, merge, deletion, or force-update effects. Transport-specific
validators may add stricter sequencing without redefining that protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


class OperatorPolicyViolation(ValueError):
    """A proposed Bus mutation plan exceeds the bounded message-write effect."""


REQUIRED_BUS_WRITE_ACTIONS = (
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

ALLOWED_BUS_WRITE_ACTIONS = frozenset(REQUIRED_BUS_WRITE_ACTIONS)

REQUIRED_CONTENTS_API_WRITE_ACTIONS = (
    "READ_BRANCH_HEAD",
    "VERIFY_MESSAGE_ABSENT",
    "CREATE_APPEND_ONLY_MESSAGE",
    "REFRESH_BRANCH_HEAD",
    "VERIFY_BRANCH_ADVANCED",
    "VERIFY_MESSAGE_READBACK",
)

ALLOWED_CONTENTS_API_WRITE_ACTIONS = frozenset(REQUIRED_CONTENTS_API_WRITE_ACTIONS)

FORBIDDEN_BUS_WRITE_ACTIONS = frozenset(
    {
        "CREATE_PULL_REQUEST",
        "MERGE_PULL_REQUEST",
        "DELETE_REF",
        "FORCE_UPDATE_REF",
    }
)


@dataclass(frozen=True)
class BusWritePlan:
    """Git-data + HEAD.json CAS profile retained for compatibility."""

    writer_branch: str
    message_path: str
    initial_branch_head: str
    initial_head_blob: str
    refreshed_branch_head: str
    refreshed_head_blob: str
    cas_expected_branch_head: str
    cas_expected_head_blob: str
    force_ref_update: bool
    actions: tuple[str, ...]


@dataclass(frozen=True)
class BusContentsWritePlan:
    """Direct GitHub Contents-API append profile for one normal Bus message."""

    writer_branch: str
    message_path: str
    initial_branch_head: str
    message_absence_verified: bool
    refreshed_branch_head: str
    force_ref_update: bool
    actions: tuple[str, ...]


def _validate_git_oid(value: str, field: str) -> None:
    if type(value) is not str or len(value) != 40:
        raise OperatorPolicyViolation(f"{field} must be a 40-character Git object id")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OperatorPolicyViolation(
            f"{field} must be a 40-character hexadecimal Git object id"
        ) from exc


def _validate_writer_and_path(
    *,
    writer_branch: str,
    message_path: str,
    expected_writer_branch: str,
) -> None:
    if type(expected_writer_branch) is not str or not expected_writer_branch:
        raise OperatorPolicyViolation("expected writer branch must be non-empty")
    if writer_branch != expected_writer_branch:
        raise OperatorPolicyViolation(
            "writer branch does not match the current authorized Bus route"
        )
    if (
        type(message_path) is not str
        or not message_path.startswith("messages/")
        or message_path == "messages/"
        or "\\" in message_path
        or ".." in message_path.split("/")
    ):
        raise OperatorPolicyViolation(
            "Bus message path must be an append-only messages/ path"
        )


def _validate_no_force(force_ref_update: bool) -> None:
    if type(force_ref_update) is not bool:
        raise OperatorPolicyViolation("force_ref_update must be boolean")
    if force_ref_update:
        raise OperatorPolicyViolation(
            "force ref update is forbidden for normal Bus message writes"
        )


def _validate_action_sequence(
    actions: Sequence[str],
    *,
    allowed_actions: frozenset[str],
    required_actions: tuple[str, ...],
    profile_name: str,
) -> None:
    for action in actions:
        if action in FORBIDDEN_BUS_WRITE_ACTIONS:
            raise OperatorPolicyViolation(
                f"{action} is forbidden for BUS_MESSAGE_WRITE intent"
            )
        if action not in allowed_actions:
            raise OperatorPolicyViolation(
                f"{action} is not an allowed {profile_name} action"
            )

    if tuple(actions) != required_actions:
        raise OperatorPolicyViolation(
            f"{profile_name} must use the exact required action sequence"
        )


def validate_bus_write_plan(
    plan: BusWritePlan,
    *,
    expected_writer_branch: str,
) -> BusWritePlan:
    """Validate the legacy Git-data + HEAD.json CAS message-write profile."""

    _validate_writer_and_path(
        writer_branch=plan.writer_branch,
        message_path=plan.message_path,
        expected_writer_branch=expected_writer_branch,
    )

    for field in (
        "initial_branch_head",
        "initial_head_blob",
        "refreshed_branch_head",
        "refreshed_head_blob",
        "cas_expected_branch_head",
        "cas_expected_head_blob",
    ):
        _validate_git_oid(getattr(plan, field), field)

    _validate_no_force(plan.force_ref_update)

    if plan.cas_expected_branch_head != plan.refreshed_branch_head:
        raise OperatorPolicyViolation(
            "branch CAS expectation must equal the refreshed branch frontier"
        )
    if plan.cas_expected_head_blob != plan.refreshed_head_blob:
        raise OperatorPolicyViolation(
            "HEAD.json CAS expectation must equal the refreshed HEAD.json blob"
        )

    if type(plan.actions) is not tuple:
        raise OperatorPolicyViolation("actions must be an immutable tuple")
    _validate_action_sequence(
        plan.actions,
        allowed_actions=ALLOWED_BUS_WRITE_ACTIONS,
        required_actions=REQUIRED_BUS_WRITE_ACTIONS,
        profile_name="GIT_DATA_HEAD_CAS",
    )

    return plan


def validate_bus_contents_write_plan(
    plan: BusContentsWritePlan,
    *,
    expected_writer_branch: str,
) -> BusContentsWritePlan:
    """Validate a direct Contents-API append without promoting HEAD.json.

    This profile is valid only for creation of a previously absent message path.
    It does not authorize overwrite/update semantics for an existing message.
    """

    _validate_writer_and_path(
        writer_branch=plan.writer_branch,
        message_path=plan.message_path,
        expected_writer_branch=expected_writer_branch,
    )
    _validate_git_oid(plan.initial_branch_head, "initial_branch_head")
    _validate_git_oid(plan.refreshed_branch_head, "refreshed_branch_head")
    _validate_no_force(plan.force_ref_update)

    if type(plan.message_absence_verified) is not bool:
        raise OperatorPolicyViolation("message_absence_verified must be boolean")
    if not plan.message_absence_verified:
        raise OperatorPolicyViolation(
            "Contents-API append requires authoritative absence of the message path"
        )
    if plan.refreshed_branch_head == plan.initial_branch_head:
        raise OperatorPolicyViolation(
            "Contents-API append must advance the writer branch frontier"
        )

    if type(plan.actions) is not tuple:
        raise OperatorPolicyViolation("actions must be an immutable tuple")
    _validate_action_sequence(
        plan.actions,
        allowed_actions=ALLOWED_CONTENTS_API_WRITE_ACTIONS,
        required_actions=REQUIRED_CONTENTS_API_WRITE_ACTIONS,
        profile_name="CONTENTS_API_APPEND",
    )

    return plan


__all__ = [
    "ALLOWED_BUS_WRITE_ACTIONS",
    "ALLOWED_CONTENTS_API_WRITE_ACTIONS",
    "BusContentsWritePlan",
    "BusWritePlan",
    "FORBIDDEN_BUS_WRITE_ACTIONS",
    "OperatorPolicyViolation",
    "REQUIRED_BUS_WRITE_ACTIONS",
    "REQUIRED_CONTENTS_API_WRITE_ACTIONS",
    "validate_bus_contents_write_plan",
    "validate_bus_write_plan",
]
