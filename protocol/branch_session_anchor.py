"""Reference implementation for Vera's bounded branch/session-anchor contract.

This module is deliberately storage-neutral. It validates anchor records,
resolves honest stable or ephemeral scopes, models append-only predecessor and
idempotency rules, and computes elapsed results without inventing provider
identities, timestamps, durable recognition, waiting, or hidden activity.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any, Mapping
from uuid import UUID, uuid4

EVIDENCE_PRECISIONS = {"EXACT", "BOUNDED", "APPROXIMATE", "UNKNOWN"}
ELAPSED_STATUSES = {"EXACT", "BOUNDED", "APPROXIMATE", "UNAVAILABLE", "CONFLICTED"}
IDENTITY_STATUSES = {"EXPOSED", "UNAVAILABLE"}
SCOPE_MODES = {"STABLE", "EPHEMERAL"}
ANCHOR_KINDS = {"ENTRY", "MATERIAL_EXIT"}
MATERIAL_EXIT_REASONS = {
    "BRANCH_HANDOFF",
    "VERIFIED_CHECKPOINT",
    "TASK_STATE_TRANSITION",
    "CONTEXT_SWITCH",
    "SESSION_CLOSE",
}
IDENTITY_SOURCE_BY_STATUS = {
    "EXPOSED": "PROVIDER_EXPOSED_ID",
    "UNAVAILABLE": "PROVIDER_ID_UNAVAILABLE",
}
EVENT_TIME_SOURCE_PRECISIONS = {
    "PROVIDER_EXPOSED_TIMESTAMP": {"EXACT", "BOUNDED", "APPROXIMATE", "UNKNOWN"},
    "TOOL_EXPOSED_TIMESTAMP": {"EXACT", "BOUNDED", "APPROXIMATE", "UNKNOWN"},
    "USER_REPORTED_TIMESTAMP": {"BOUNDED", "APPROXIMATE", "UNKNOWN"},
    "EVENT_TIME_UNAVAILABLE": {"UNKNOWN"},
}
CHECKPOINT_VERIFICATION_SOURCE = "CHECKPOINT_OWNER_VERIFIED"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

ANCHOR_CONTENT_EXCLUDED_FIELDS = {"content_hash", "idempotency_key", "record_time"}
ANCHOR_ALLOWED_FIELDS = {
    "schema", "anchor_id", "project_id", "conversation_identity",
    "branch_identity", "scope_mode", "scope_id", "scope_instance_id",
    "session_id", "checkpoint_id", "anchor_kind", "entry_reason",
    "exit_reason", "exit_details", "prior_anchor_id",
    "predecessor_checkpoint_evidence", "event_time", "source",
    "content_hash", "idempotency_key", "payload", "record_time",
}
RESERVED_CLAIM_FIELDS = {
    "waiting", "hidden_activity", "continuous_activity", "private_duration",
    "uninterrupted_continuity", "invented_identity", "identity_claim",
    "durable_recognition", "resumed_identity", "continuous_experience",
}
PAYLOAD_ALLOWED_FIELDS = {"labels", "references", "details"}
PAYLOAD_DETAIL_FIELDS = {"handoff_target", "task_state", "note"}
PAYLOAD_REFERENCE_FIELDS = {"kind", "value"}
PAYLOAD_REFERENCE_KINDS = {"ISSUE", "PULL_REQUEST", "CHECKPOINT", "DOCUMENT"}
IDENTITY_FIELDS = {"status", "value", "source"}
EVENT_TIME_FIELDS = {"observed_at", "precision", "lower_bound", "upper_bound", "source"}
CHECKPOINT_EVIDENCE_FIELDS = {
    "status", "source", "checkpoint_id", "predecessor_anchor_id",
    "project_id", "scope_id",
}


class AnchorValidationError(ValueError):
    """Raised when an anchor violates the bounded protocol."""


class IdempotencyConflict(RuntimeError):
    """Raised when claimed or stored append identity conflicts with content."""


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


def _require_exact_fields(value: Mapping[str, Any], allowed: set[str], field: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise AnchorValidationError(f"{field} contains unsupported fields: {sorted(unknown)}")


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _reject_reserved_claim_fields(value: Any, field: str = "anchor") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _normalized_key(key) in RESERVED_CLAIM_FIELDS:
                raise AnchorValidationError(
                    f"{field} may not encode reserved continuity or identity claim field {key!r}"
                )
            _reject_reserved_claim_fields(nested, f"{field}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_reserved_claim_fields(nested, f"{field}[{index}]")


def _identity(value: Mapping[str, Any], field: str) -> tuple[str, str | None, str]:
    if not isinstance(value, Mapping):
        raise AnchorValidationError(f"{field} must be an object")
    _require_exact_fields(value, IDENTITY_FIELDS, field)
    status = value.get("status")
    identifier = value.get("value")
    source = value.get("source")
    if status not in IDENTITY_STATUSES:
        raise AnchorValidationError(f"{field}.status must be EXPOSED or UNAVAILABLE")
    expected_source = IDENTITY_SOURCE_BY_STATUS[status]
    if source != expected_source:
        raise AnchorValidationError(
            f"{field}.source must be {expected_source} when status is {status}"
        )
    if status == "EXPOSED":
        if not isinstance(identifier, str) or not identifier.strip():
            raise AnchorValidationError(f"{field}.value is required when EXPOSED")
        return status, identifier, source
    if identifier is not None:
        raise AnchorValidationError(f"{field}.value must be null when UNAVAILABLE")
    return status, None, source


def stable_scope_id(project_id: str, conversation_id: str, branch_id: str) -> str:
    """Derive a stable opaque scope key from provider-exposed identities."""
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
) -> dict[str, Any]:
    """Resolve a stable scope or internally generate a fresh ephemeral scope.

    The public resolver exposes no caller-supplied UUID value or generator.
    Tests may patch the module-private ``uuid4`` dependency, but production
    callers cannot select an ephemeral identity through the resolver API.
    """
    conversation_status, conversation_id, _ = _identity(
        conversation, "conversation_identity"
    )
    branch_status, branch_id, _ = _identity(branch, "branch_identity")
    if conversation_status == branch_status == "EXPOSED":
        return {
            "mode": "STABLE",
            "scope_id": stable_scope_id(project_id, conversation_id or "", branch_id or ""),
            "durable_recognition": True,
        }
    return {
        "mode": "EPHEMERAL",
        "scope_id": _uuid(uuid4(), "generated_ephemeral_scope_id"),
        "durable_recognition": False,
    }


def validate_temporal_evidence(value: Mapping[str, Any], field: str = "event_time") -> None:
    if not isinstance(value, Mapping):
        raise AnchorValidationError(f"{field} must be an object")
    _require_exact_fields(value, EVENT_TIME_FIELDS, field)
    precision = value.get("precision")
    observed_at = value.get("observed_at")
    lower = value.get("lower_bound")
    upper = value.get("upper_bound")
    source = value.get("source")
    if precision not in EVIDENCE_PRECISIONS:
        raise AnchorValidationError(
            f"{field}.precision must be EXACT, BOUNDED, APPROXIMATE, or UNKNOWN"
        )
    compatible_precisions = EVENT_TIME_SOURCE_PRECISIONS.get(source)
    if compatible_precisions is None:
        raise AnchorValidationError(f"{field}.source is not an approved evidence classification")
    if precision not in compatible_precisions:
        raise AnchorValidationError(
            f"{field}.source {source} is incompatible with precision {precision}"
        )
    if source == "EVENT_TIME_UNAVAILABLE":
        if observed_at is not None or lower is not None or upper is not None:
            raise AnchorValidationError(
                f"{field} unavailable source requires null observed_at and bounds"
            )
        return
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


def _validate_payload(payload: Any) -> None:
    if not isinstance(payload, Mapping):
        raise AnchorValidationError("payload must be an object")
    _require_exact_fields(payload, PAYLOAD_ALLOWED_FIELDS, "payload")
    labels = payload.get("labels", [])
    if not isinstance(labels, list) or any(
        not isinstance(item, str) or not item.strip() for item in labels
    ):
        raise AnchorValidationError("payload.labels must be a list of non-empty strings")
    references = payload.get("references", [])
    if not isinstance(references, list):
        raise AnchorValidationError("payload.references must be a list")
    for index, reference in enumerate(references):
        if not isinstance(reference, Mapping):
            raise AnchorValidationError(f"payload.references[{index}] must be an object")
        _require_exact_fields(
            reference, PAYLOAD_REFERENCE_FIELDS, f"payload.references[{index}]"
        )
        if reference.get("kind") not in PAYLOAD_REFERENCE_KINDS:
            raise AnchorValidationError(f"payload.references[{index}].kind is not allowlisted")
        if not isinstance(reference.get("value"), str) or not reference["value"].strip():
            raise AnchorValidationError(
                f"payload.references[{index}].value must be a non-empty string"
            )
    details = payload.get("details", {})
    if not isinstance(details, Mapping):
        raise AnchorValidationError("payload.details must be an object")
    _require_exact_fields(details, PAYLOAD_DETAIL_FIELDS, "payload.details")
    for key, value in details.items():
        if not isinstance(value, str) or not value.strip():
            raise AnchorValidationError(f"payload.details.{key} must be a non-empty string")


def _checkpoint_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise AnchorValidationError(f"{field} must be a non-empty string")
    if value != value.strip() or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise AnchorValidationError(
            f"{field} must not contain surrounding whitespace or control characters"
        )
    return value


def _checkpoint_identity_collisions(anchor: Mapping[str, Any]) -> dict[str, Any]:
    conversation = anchor.get("conversation_identity")
    branch = anchor.get("branch_identity")
    conversation_id = conversation.get("value") if isinstance(conversation, Mapping) else None
    branch_id = branch.get("value") if isinstance(branch, Mapping) else None
    return {
        "session_id": anchor.get("session_id"),
        "anchor_id": anchor.get("anchor_id"),
        "scope_instance_id": anchor.get("scope_instance_id"),
        "conversation_identity": conversation_id,
        "branch_identity": branch_id,
        "scope_id": anchor.get("scope_id"),
        "prior_anchor_id": anchor.get("prior_anchor_id"),
    }


def _validate_distinct_checkpoint_id(value: Any, anchor: Mapping[str, Any], field: str) -> str:
    checkpoint_id = _checkpoint_id(value, field)
    for identity_name, identity_value in _checkpoint_identity_collisions(anchor).items():
        if identity_value is not None and checkpoint_id == identity_value:
            raise AnchorValidationError(
                f"{field} must remain distinct from {identity_name}"
            )
    return checkpoint_id


def _validate_checkpoint_evidence(value: Any, anchor: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise AnchorValidationError("predecessor_checkpoint_evidence must be an object")
    _require_exact_fields(
        value, CHECKPOINT_EVIDENCE_FIELDS, "predecessor_checkpoint_evidence"
    )
    if value.get("status") != "VERIFIED":
        raise AnchorValidationError("predecessor checkpoint evidence must be VERIFIED")
    if value.get("source") != CHECKPOINT_VERIFICATION_SOURCE:
        raise AnchorValidationError(
            f"predecessor checkpoint source must be {CHECKPOINT_VERIFICATION_SOURCE}"
        )
    _validate_distinct_checkpoint_id(
        value.get("checkpoint_id"), anchor, "predecessor_checkpoint_evidence.checkpoint_id"
    )
    _uuid(
        value.get("predecessor_anchor_id"),
        "predecessor_checkpoint_evidence.predecessor_anchor_id",
    )
    if value.get("predecessor_anchor_id") != anchor.get("prior_anchor_id"):
        raise AnchorValidationError("checkpoint evidence predecessor does not match prior_anchor_id")
    if value.get("project_id") != anchor.get("project_id"):
        raise AnchorValidationError("checkpoint evidence project does not match anchor")
    if value.get("scope_id") != anchor.get("scope_id"):
        raise AnchorValidationError("checkpoint evidence scope does not match anchor")


def canonical_anchor_content(anchor: Mapping[str, Any]) -> dict[str, Any]:
    """Return logical content covered by content_hash.

    Only the self-referential hash, append-request idempotency key, and a later
    database-assigned record_time are excluded.
    """
    return {
        key: deepcopy(value)
        for key, value in anchor.items()
        if key not in ANCHOR_CONTENT_EXCLUDED_FIELDS
    }


def canonical_anchor_bytes(anchor: Mapping[str, Any]) -> bytes:
    try:
        serialized = json.dumps(
            canonical_anchor_content(anchor),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AnchorValidationError("anchor logical content must be canonical JSON") from exc
    return serialized.encode("utf-8")


def compute_content_hash(anchor: Mapping[str, Any]) -> str:
    return sha256(canonical_anchor_bytes(anchor)).hexdigest()


def validate_anchor(anchor: Mapping[str, Any], *, verify_content_hash: bool = True) -> None:
    """Validate one append-only anchor record."""
    if not isinstance(anchor, Mapping):
        raise AnchorValidationError("anchor must be an object")
    _require_exact_fields(anchor, ANCHOR_ALLOWED_FIELDS, "anchor")
    _reject_reserved_claim_fields(anchor)
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
    conversation_status, conversation_id, _ = _identity(
        anchor.get("conversation_identity", {}), "conversation_identity"
    )
    branch_status, branch_id, _ = _identity(
        anchor.get("branch_identity", {}), "branch_identity"
    )
    mode = anchor.get("scope_mode")
    if mode not in SCOPE_MODES:
        raise AnchorValidationError("scope_mode must be STABLE or EPHEMERAL")
    scope_id = anchor.get("scope_id")
    if not isinstance(scope_id, str) or not scope_id:
        raise AnchorValidationError("scope_id is required")
    if mode == "STABLE":
        if conversation_status != "EXPOSED" or branch_status != "EXPOSED":
            raise AnchorValidationError(
                "STABLE scope requires provider-exposed conversation and branch identities"
            )
        expected = stable_scope_id(anchor["project_id"], conversation_id or "", branch_id or "")
        if scope_id != expected:
            raise AnchorValidationError("scope_id does not match provider-exposed identities")
    else:
        _uuid(scope_id, "scope_id")
        if conversation_status == branch_status == "EXPOSED":
            raise AnchorValidationError(
                "EPHEMERAL scope is not allowed when both identities are provider-exposed"
            )

    checkpoint_id = anchor.get("checkpoint_id")
    if checkpoint_id is not None:
        _validate_distinct_checkpoint_id(checkpoint_id, anchor, "checkpoint_id")

    prior_anchor_id = anchor.get("prior_anchor_id")
    checkpoint_evidence = anchor.get("predecessor_checkpoint_evidence")
    exit_reason = anchor.get("exit_reason")
    exit_details = anchor.get("exit_details")
    if kind == "ENTRY":
        if exit_reason is not None or exit_details is not None:
            raise AnchorValidationError("ENTRY anchors may not carry exit_reason or exit_details")
        if mode == "EPHEMERAL" and prior_anchor_id is not None:
            raise AnchorValidationError("EPHEMERAL entry may not invent durable recognition")
        if prior_anchor_id is not None:
            _uuid(prior_anchor_id, "prior_anchor_id")
        if checkpoint_evidence is not None:
            if mode != "STABLE" or prior_anchor_id is None:
                raise AnchorValidationError(
                    "checkpoint predecessor evidence requires a stable ENTRY with prior_anchor_id"
                )
            _validate_checkpoint_evidence(checkpoint_evidence, anchor)
    else:
        _uuid(prior_anchor_id, "prior_anchor_id")
        if exit_reason not in MATERIAL_EXIT_REASONS:
            raise AnchorValidationError(
                "MATERIAL_EXIT exit_reason must be a canonical material reason"
            )
        if exit_details is not None and (
            not isinstance(exit_details, str) or not exit_details.strip()
        ):
            raise AnchorValidationError("exit_details must be a non-empty string or null")
        if checkpoint_evidence is not None:
            raise AnchorValidationError(
                "MATERIAL_EXIT may not substitute checkpoint evidence for an existing predecessor"
            )

    validate_temporal_evidence(anchor.get("event_time", {}))
    if not HEX64.fullmatch(anchor["content_hash"]):
        raise AnchorValidationError("content_hash must be lowercase SHA-256 hex")
    if not HEX64.fullmatch(anchor["idempotency_key"]):
        raise AnchorValidationError("idempotency_key must be lowercase SHA-256 hex")
    _validate_payload(anchor.get("payload", {}))
    if "record_time" in anchor and anchor["record_time"] is not None:
        _parse_timestamp(anchor["record_time"], "record_time")
    if verify_content_hash and anchor["content_hash"] != compute_content_hash(anchor):
        raise AnchorValidationError(
            "content_hash does not match canonical logical anchor content"
        )


def _endpoint_interval(endpoint: Mapping[str, Any]) -> tuple[datetime, datetime, datetime, str]:
    validate_temporal_evidence(endpoint, "endpoint")
    precision = endpoint["precision"]
    if endpoint["source"] == "EVENT_TIME_UNAVAILABLE":
        raise AnchorValidationError("endpoint time is unavailable")
    observed = _parse_timestamp(endpoint["observed_at"], "endpoint.observed_at")
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
        if "unavailable" in str(exc).lower():
            return {"status": "UNAVAILABLE", "reason": "UNKNOWN_PRECISION"}
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


@dataclass(frozen=True)
class AppendResult:
    outcome: str
    anchor_id: str


class AppendOnlyAnchorSet:
    """In-memory reference for append-only, idempotent predecessor behavior."""

    def __init__(self) -> None:
        self._by_idempotency_key: dict[str, tuple[str, str]] = {}
        self._by_anchor_id: dict[str, dict[str, Any]] = {}

    def _validate_predecessor(self, anchor: Mapping[str, Any]) -> None:
        prior_anchor_id = anchor.get("prior_anchor_id")
        if anchor["anchor_kind"] == "ENTRY":
            if prior_anchor_id is None:
                return
            existing = self._by_anchor_id.get(prior_anchor_id)
            if existing is not None:
                if (
                    anchor["scope_mode"] != "STABLE"
                    or existing["scope_mode"] != "STABLE"
                    or existing["project_id"] != anchor["project_id"]
                    or existing["scope_id"] != anchor["scope_id"]
                ):
                    raise AnchorValidationError(
                        "stable ENTRY predecessor must exist in the same project and stable scope"
                    )
                return
            evidence = anchor.get("predecessor_checkpoint_evidence")
            if evidence is None:
                raise AnchorValidationError(
                    "stable ENTRY predecessor must exist or carry separately verified checkpoint evidence"
                )
            _validate_checkpoint_evidence(evidence, anchor)
            return

        existing = self._by_anchor_id.get(prior_anchor_id)
        if existing is None:
            raise AnchorValidationError("MATERIAL_EXIT predecessor does not exist")
        compared_fields = ("project_id", "scope_id", "scope_instance_id", "session_id")
        mismatched = [field for field in compared_fields if existing[field] != anchor[field]]
        if mismatched:
            raise AnchorValidationError(
                "MATERIAL_EXIT predecessor mismatch for " + ", ".join(mismatched)
            )

    def append(self, anchor: Mapping[str, Any]) -> AppendResult:
        validate_anchor(anchor, verify_content_hash=False)
        canonical_hash = compute_content_hash(anchor)
        if anchor["content_hash"] != canonical_hash:
            raise IdempotencyConflict(
                "CONFLICTED: claimed content_hash does not match canonical logical content"
            )
        key = anchor["idempotency_key"]
        anchor_id = anchor["anchor_id"]
        current = self._by_idempotency_key.get(key)
        if current is not None:
            stored_hash, stored_anchor_id = current
            if stored_hash != canonical_hash or stored_anchor_id != anchor_id:
                raise IdempotencyConflict(
                    "CONFLICTED: idempotency key reused for different canonical content"
                )
            return AppendResult("EXISTING", stored_anchor_id)

        existing_id = self._by_anchor_id.get(anchor_id)
        if existing_id is not None:
            if compute_content_hash(existing_id) != canonical_hash:
                raise IdempotencyConflict(
                    "CONFLICTED: anchor_id reused for different canonical content"
                )
            # An alternate request key for byte-identical logical content is
            # explicitly accepted and permanently bound to the existing anchor.
            self._by_idempotency_key[key] = (canonical_hash, anchor_id)
            return AppendResult("EXISTING", anchor_id)

        self._validate_predecessor(anchor)
        stored = deepcopy(dict(anchor))
        self._by_anchor_id[anchor_id] = stored
        self._by_idempotency_key[key] = (canonical_hash, anchor_id)
        return AppendResult("APPENDED", anchor_id)
