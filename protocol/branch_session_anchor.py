"""Reference implementation for Vera's bounded branch/session-anchor contract.

This module is deliberately storage-neutral. It validates anchor records and
computes elapsed results without inventing provider identities, timestamps, or
activity between anchors.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any, Mapping
from uuid import UUID

EVIDENCE_PRECISIONS = {"EXACT", "BOUNDED", "APPROXIMATE", "UNKNOWN"}
ELAPSED_STATUSES = {"EXACT", "BOUNDED", "APPROXIMATE", "UNAVAILABLE", "CONFLICTED"}
IDENTITY_STATUSES = {"EXPOSED", "UNAVAILABLE"}
SCOPE_MODES = {"STABLE", "EPHEMERAL"}
ANCHOR_KINDS = {"ENTRY", "MATERIAL_EXIT"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class AnchorValidationError(ValueError):
    """Raised when an anchor violates the bounded protocol."""


class IdempotencyConflict(RuntimeError):
    """Raised when one idempotency key is reused for different content."""


def _uuid(value: Any, field: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise AnchorValidationError(f"{field} must be a UUID") from exc


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise AnchorValidationError(f"{field} must be an ISO-8601 timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AnchorValidationError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AnchorValidationError(f"{field} must include a UTC offset")
    return parsed


def _identity(value: Mapping[str, Any], field: str) -> tuple[str, str | None]:
    status = value.get("status")
    identifier = value.get("value")
    if status not in IDENTITY_STATUSES:
        raise AnchorValidationError(f"{field}.status must be EXPOSED or UNAVAILABLE")
    if status == "EXPOSED":
        if not isinstance(identifier, str) or not identifier.strip():
            raise AnchorValidationError(f"{field}.value is required when EXPOSED")
        return status, identifier
    if identifier is not None:
        raise AnchorValidationError(f"{field}.value must be null when UNAVAILABLE")
    return status, None


def stable_scope_id(project_id: str, conversation_id: str, branch_id: str) -> str:
    """Derive a stable, opaque scope key from exposed provider identities."""
    canonical = json.dumps(
        [project_id, conversation_id, branch_id],
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def resolve_scope(
    project_id: str,
    conversation: Mapping[str, Any],
    branch: Mapping[str, Any],
    ephemeral_scope_id: str,
) -> dict[str, str]:
    """Resolve stable scope only when both provider identities are exposed.

    Any missing provider identity forces an ephemeral scope. The generated
    scope separates the current visible runtime but is not reusable evidence
    of a resumed conversation or branch.
    """
    conversation_status, conversation_id = _identity(conversation, "conversation_identity")
    branch_status, branch_id = _identity(branch, "branch_identity")
    if conversation_status == branch_status == "EXPOSED":
        return {
            "mode": "STABLE",
            "scope_id": stable_scope_id(project_id, conversation_id or "", branch_id or ""),
        }
    return {"mode": "EPHEMERAL", "scope_id": _uuid(ephemeral_scope_id, "ephemeral_scope_id")}


def validate_temporal_evidence(value: Mapping[str, Any], field: str = "event_time") -> None:
    precision = value.get("precision")
    observed_at = value.get("observed_at")
    lower = value.get("lower_bound")
    upper = value.get("upper_bound")
    if precision not in EVIDENCE_PRECISIONS:
        raise AnchorValidationError(
            f"{field}.precision must be EXACT, BOUNDED, APPROXIMATE, or UNKNOWN"
        )
    observed = _parse_timestamp(observed_at, f"{field}.observed_at")
    if precision == "BOUNDED":
        lower_dt = _parse_timestamp(lower, f"{field}.lower_bound")
        upper_dt = _parse_timestamp(upper, f"{field}.upper_bound")
        if lower_dt > upper_dt:
            raise AnchorValidationError(f"{field} bounds are inverted")
        if not lower_dt <= observed <= upper_dt:
            raise AnchorValidationError(f"{field}.observed_at must fall inside its bounds")
    elif lower is not None or upper is not None:
        raise AnchorValidationError(f"{field} bounds are allowed only for BOUNDED evidence")


def validate_anchor(anchor: Mapping[str, Any]) -> None:
    """Validate one append-only anchor record."""
    required_text = ("schema", "project_id", "source", "content_hash", "idempotency_key")
    for field in required_text:
        if not isinstance(anchor.get(field), str) or not anchor[field]:
            raise AnchorValidationError(f"{field} is required")
    if anchor["schema"] != "VERA_BRANCH_SESSION_ANCHOR_V1":
        raise AnchorValidationError("unsupported anchor schema")
    for field in ("anchor_id", "session_id", "scope_instance_id"):
        _uuid(anchor.get(field), field)
    kind = anchor.get("anchor_kind")
    if kind not in ANCHOR_KINDS:
        raise AnchorValidationError("anchor_kind must be ENTRY or MATERIAL_EXIT")
    conversation_status, conversation_id = _identity(
        anchor.get("conversation_identity", {}), "conversation_identity"
    )
    branch_status, branch_id = _identity(anchor.get("branch_identity", {}), "branch_identity")
    mode = anchor.get("scope_mode")
    if mode not in SCOPE_MODES:
        raise AnchorValidationError("scope_mode must be STABLE or EPHEMERAL")
    scope_id = anchor.get("scope_id")
    if not isinstance(scope_id, str) or not scope_id:
        raise AnchorValidationError("scope_id is required")
    if mode == "STABLE":
        if conversation_status != "EXPOSED" or branch_status != "EXPOSED":
            raise AnchorValidationError("STABLE scope requires exposed conversation and branch identities")
        expected = stable_scope_id(anchor["project_id"], conversation_id or "", branch_id or "")
        if scope_id != expected:
            raise AnchorValidationError("scope_id does not match exposed identities")
    else:
        _uuid(scope_id, "scope_id")
        if conversation_status == branch_status == "EXPOSED":
            raise AnchorValidationError("EPHEMERAL scope is not allowed when both identities are exposed")

    checkpoint_id = anchor.get("checkpoint_id")
    if checkpoint_id is not None:
        if not isinstance(checkpoint_id, str) or not checkpoint_id:
            raise AnchorValidationError("checkpoint_id must be a non-empty string or null")
        if checkpoint_id in {
            anchor.get("session_id"),
            conversation_id,
            branch_id,
            anchor.get("scope_id"),
        }:
            raise AnchorValidationError("checkpoint identity must remain distinct")

    prior_anchor_id = anchor.get("prior_anchor_id")
    exit_reason = anchor.get("exit_reason")
    if kind == "ENTRY":
        if exit_reason is not None:
            raise AnchorValidationError("ENTRY anchors may not carry exit_reason")
        if mode == "EPHEMERAL" and prior_anchor_id is not None:
            raise AnchorValidationError("EPHEMERAL entry may not invent a prior anchor")
    else:
        _uuid(prior_anchor_id, "prior_anchor_id")
        if not isinstance(exit_reason, str) or not exit_reason.strip():
            raise AnchorValidationError("MATERIAL_EXIT requires exit_reason")

    validate_temporal_evidence(anchor.get("event_time", {}))
    if not HEX64.fullmatch(anchor["content_hash"]):
        raise AnchorValidationError("content_hash must be lowercase SHA-256 hex")
    if not HEX64.fullmatch(anchor["idempotency_key"]):
        raise AnchorValidationError("idempotency_key must be lowercase SHA-256 hex")
    prohibited = {"waiting", "hidden_activity", "continuous_activity", "private_duration"}
    if prohibited.intersection(anchor.keys()):
        raise AnchorValidationError("anchor may not encode hidden activity or waiting")


def _endpoint_interval(endpoint: Mapping[str, Any]) -> tuple[datetime, datetime, datetime, str]:
    validate_temporal_evidence(endpoint, "endpoint")
    observed = _parse_timestamp(endpoint["observed_at"], "endpoint.observed_at")
    precision = endpoint["precision"]
    if precision == "BOUNDED":
        return (
            _parse_timestamp(endpoint["lower_bound"], "endpoint.lower_bound"),
            observed,
            _parse_timestamp(endpoint["upper_bound"], "endpoint.upper_bound"),
            precision,
        )
    return observed, observed, observed, precision


def calculate_elapsed(
    start: Mapping[str, Any] | None,
    end: Mapping[str, Any] | None,
    *,
    start_scope_id: str | None,
    end_scope_id: str | None,
) -> dict[str, Any]:
    """Calculate elapsed time from compatible exposed endpoints only."""
    if start is None or end is None:
        return {"status": "UNAVAILABLE", "reason": "MISSING_ENDPOINT"}
    if not start_scope_id or not end_scope_id:
        return {"status": "UNAVAILABLE", "reason": "MISSING_SCOPE"}
    if start_scope_id != end_scope_id:
        return {"status": "CONFLICTED", "reason": "SCOPE_MISMATCH"}
    try:
        start_low, start_best, start_high, start_precision = _endpoint_interval(start)
        end_low, end_best, end_high, end_precision = _endpoint_interval(end)
    except AnchorValidationError as exc:
        return {"status": "CONFLICTED", "reason": str(exc)}
    if "UNKNOWN" in {start_precision, end_precision}:
        return {"status": "UNAVAILABLE", "reason": "UNKNOWN_PRECISION"}
    minimum = (end_low - start_high).total_seconds()
    maximum = (end_high - start_low).total_seconds()
    representative = (end_best - start_best).total_seconds()
    if maximum < 0:
        return {"status": "CONFLICTED", "reason": "END_PRECEDES_START"}
    if start_precision == end_precision == "EXACT":
        return {"status": "EXACT", "seconds": representative}
    if "BOUNDED" in {start_precision, end_precision}:
        return {
            "status": "BOUNDED",
            "range": {"lower_seconds": minimum, "upper_seconds": maximum},
            "representative_seconds": representative,
        }
    return {"status": "APPROXIMATE", "seconds": representative}


@dataclass
class AppendResult:
    outcome: str
    anchor_id: str


class AppendOnlyAnchorSet:
    """In-memory reference for append-only, idempotent behavior."""

    def __init__(self) -> None:
        self._by_idempotency_key: dict[str, tuple[str, str]] = {}

    def append(self, anchor: Mapping[str, Any]) -> AppendResult:
        validate_anchor(anchor)
        key = anchor["idempotency_key"]
        current = self._by_idempotency_key.get(key)
        if current is None:
            self._by_idempotency_key[key] = (anchor["content_hash"], anchor["anchor_id"])
            return AppendResult("APPENDED", anchor["anchor_id"])
        content_hash, anchor_id = current
        if content_hash != anchor["content_hash"]:
            raise IdempotencyConflict("idempotency key reused for different content")
        return AppendResult("EXISTING", anchor_id)
