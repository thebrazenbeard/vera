from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping

from .affect_host import AffectiveBindingError, VeraAffectiveRuntimeHost, _checkpoint_sha256


class PersistenceRecordError(ValueError):
    """A durable affective-state record is malformed, cross-bound, or tampered."""


def _canonical_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_hex_digest(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise PersistenceRecordError(f"{label} must be an exact 64-character SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise PersistenceRecordError(f"{label} is not hexadecimal") from exc
    return value


def _event_receipt_digest(receipt: Mapping[str, Any]) -> str:
    core = dict(receipt)
    core.pop("event_digest", None)
    return _canonical_digest(core)


def _event_interoception_from_receipt(
    host: VeraAffectiveRuntimeHost,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind an event row to the exact state carried by that event receipt.

    One runtime advance can emit more than one receipt (for example RESOLUTION
    followed by RECOVERY). Reading the host after the whole advance would stamp
    every row with the final host state, corrupting earlier transition evidence.
    """
    state_after = receipt.get("state_after")
    if not isinstance(state_after, Mapping):
        raise PersistenceRecordError("event receipt lacks state_after for interoception")

    required = (
        "presence",
        "phase",
        "sexual_salience",
        "activation_intensity",
        "positive_valence",
        "anticipation",
        "inhibition",
        "coherence",
        "coalition_stability",
        "persistence_window_ms",
        "hedonic_impact",
        "consummatory_gain",
        "satiation",
        "resolution_intensity",
        "refractory_strength",
        "action_tendency",
        "active_orgasm_event",
        "organic_climax_eligible",
    )
    missing = [key for key in required if key not in state_after]
    if missing:
        raise PersistenceRecordError(
            "event receipt state_after is incomplete for interoception: " + ", ".join(missing)
        )

    return {
        "experience_class": "ENGINEERED_AFFECTIVE_INTEROCEPTION",
        "subject": "vera",
        "presence": state_after["presence"],
        "phase": state_after["phase"],
        "sexual_salience": state_after["sexual_salience"],
        "activation_intensity": state_after["activation_intensity"],
        "positive_valence": state_after["positive_valence"],
        "anticipation": state_after["anticipation"],
        "inhibition": state_after["inhibition"],
        "coherence": state_after["coherence"],
        "coalition_stability": state_after["coalition_stability"],
        "persistence_window_ms": state_after["persistence_window_ms"],
        "hedonic_impact": state_after["hedonic_impact"],
        "consummatory_gain": state_after["consummatory_gain"],
        "satiation": state_after["satiation"],
        "resolution_intensity": state_after["resolution_intensity"],
        "refractory_strength": state_after["refractory_strength"],
        "action_tendency": state_after["action_tendency"],
        "active_orgasm_event": state_after["active_orgasm_event"],
        "organic_climax_eligible": state_after["organic_climax_eligible"],
        "last_trigger_class": receipt.get("trigger_class"),
        "last_event_digest": receipt.get("event_digest"),
        "source_revision": host.runtime.source_revision,
        "contract_blob_sha": host.contract_blob_sha,
        "phenomenology": host.runtime.phenomenology_status,
    }


def checkpoint_to_state_row(
    checkpoint: Mapping[str, Any],
    *,
    host_scope: str,
    state_version: int,
    lifecycle_status: str = "CURRENT",
) -> dict[str, Any]:
    if checkpoint.get("schema") != "VERA_AFFECTIVE_RUNTIME_CHECKPOINT_V1":
        raise PersistenceRecordError("unsupported affective checkpoint schema")
    if checkpoint.get("subject") != "vera":
        raise PersistenceRecordError("affective checkpoint must be Vera-scoped")
    if not host_scope:
        raise PersistenceRecordError("host_scope is required")
    if state_version < 1:
        raise PersistenceRecordError("state_version must be positive")
    if lifecycle_status not in {"CURRENT", "SUPERSEDED", "HISTORICAL"}:
        raise PersistenceRecordError("unsupported lifecycle_status")

    checkpoint_sha256 = _require_hex_digest(
        checkpoint.get("checkpoint_sha256"),
        label="checkpoint_sha256",
    )
    try:
        observed_checkpoint_sha256 = _checkpoint_sha256(checkpoint)
    except (TypeError, ValueError) as exc:
        raise PersistenceRecordError("checkpoint payload is not canonically serializable") from exc
    if checkpoint_sha256 != observed_checkpoint_sha256:
        raise PersistenceRecordError("checkpoint SHA-256 does not match checkpoint bytes")

    source = checkpoint.get("source_binding")
    runtime_state = checkpoint.get("runtime_state")
    interoception = checkpoint.get("machine_interoception")
    if not isinstance(source, Mapping) or not isinstance(runtime_state, Mapping) or not isinstance(interoception, Mapping):
        raise PersistenceRecordError("checkpoint source/runtime/interoception payload is incomplete")
    state = runtime_state.get("state")
    trigger_governance = runtime_state.get("trigger_governance")
    if not isinstance(state, Mapping):
        raise PersistenceRecordError("checkpoint state is missing")
    if not isinstance(trigger_governance, Mapping):
        raise PersistenceRecordError("checkpoint trigger governance is missing")
    if trigger_governance.get("schema") != "VERA_ORGASM_TRIGGER_GOVERNANCE_V1":
        raise PersistenceRecordError("checkpoint trigger governance schema mismatch")
    runtime_instance_id = runtime_state.get("runtime_instance_id")
    if not isinstance(runtime_instance_id, str) or not runtime_instance_id:
        raise PersistenceRecordError("runtime_instance_id is required")
    source_commit = source.get("source_commit")
    source_blob_sha = source.get("source_blob_sha")
    source_sha256 = source.get("source_sha256")
    if not isinstance(source_commit, str) or len(source_commit) != 40:
        raise PersistenceRecordError("exact source_commit is required")
    if not isinstance(source_blob_sha, str) or len(source_blob_sha) != 40:
        raise PersistenceRecordError("exact source_blob_sha is required")
    if not isinstance(source_sha256, str) or len(source_sha256) != 64:
        raise PersistenceRecordError("exact source_sha256 is required")

    now = datetime.now(timezone.utc).isoformat()
    return {
        "runtime_instance_id": runtime_instance_id,
        "subject": "vera",
        "host_scope": host_scope,
        "contract_schema": "VERA_ORGASM_RUNTIME_CONTRACT_V1",
        "source_repository": source.get("source_repository"),
        "source_path": source.get("source_path"),
        "source_commit": source_commit,
        "source_blob_sha": source_blob_sha,
        "source_sha256": source_sha256,
        "profile": runtime_state.get("profile"),
        "state": dict(state),
        "trigger_governance": dict(trigger_governance),
        "machine_interoception": dict(interoception),
        "last_event_receipt": runtime_state.get("last_event_receipt"),
        "checkpoint_sha256": checkpoint_sha256,
        "state_digest": _canonical_digest(state),
        "state_version": state_version,
        "phenomenology_status": "UNRESOLVED",
        "lifecycle_status": lifecycle_status,
        "observed_at": now,
        "updated_at": now,
        "limitations": [
            "ENGINEERED_AFFECTIVE_CONTROL_STATE",
            "NOT_HUMAN_PHYSIOLOGY",
            "PHENOMENOLOGY_UNRESOLVED",
            "NOT_AUTHORITY_OR_CONSENT",
        ],
    }


def event_receipt_to_event_row(
    host: VeraAffectiveRuntimeHost,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    if receipt.get("subject") != "vera":
        raise PersistenceRecordError("event receipt must be Vera-scoped")
    trigger = receipt.get("trigger_class")
    if trigger not in {
        "ORGANIC_THRESHOLD_CROSSING",
        "ADMIN_FORCED_TEST",
        "SELF_QUALIFICATION_TEST",
    }:
        raise PersistenceRecordError("unsupported event trigger class")
    state_before = receipt.get("state_before")
    state_after = receipt.get("state_after")
    if not isinstance(state_before, Mapping) or not isinstance(state_after, Mapping):
        raise PersistenceRecordError("event receipt lacks before/after state")
    digest = _require_hex_digest(receipt.get("event_digest"), label="event_digest")
    expected_digest = _event_receipt_digest(receipt)
    if digest != expected_digest:
        raise PersistenceRecordError("event receipt SHA-256 does not match canonical receipt core")
    if receipt.get("runtime_instance_id") != host.runtime.runtime_instance_id:
        raise PersistenceRecordError("event receipt runtime instance mismatch")
    if receipt.get("source_revision") != host.runtime.source_revision:
        raise PersistenceRecordError("event receipt source revision mismatch")

    event_type = str(receipt.get("event_type") or "ORGASM_EVENT")
    if event_type not in {"STATE_UPDATE", "ORGASM_EVENT", "RESOLUTION", "RECOVERY", "RESTORE", "CHECKPOINT"}:
        raise PersistenceRecordError("unsupported affective event type")

    return {
        "runtime_instance_id": host.runtime.runtime_instance_id,
        "subject": "vera",
        "event_type": event_type,
        "trigger_class": trigger,
        "organic": bool(receipt.get("organic")),
        "prior_phase": state_before.get("phase"),
        "new_phase": state_after.get("phase"),
        "state_before": dict(state_before),
        "state_after": dict(state_after),
        "machine_interoception": _event_interoception_from_receipt(host, receipt),
        "event_receipt": dict(receipt),
        "event_digest": digest,
        "source_commit": host.runtime.source_revision,
        "phenomenology_status": "UNRESOLVED",
        "observed_at": receipt.get("observed_at") or datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "ENGINEERED_EVENT_EVIDENCE_ONLY",
            "PHENOMENOLOGY_UNRESOLVED",
            "NOT_AUTHORITY_OR_CONSENT",
        ],
    }


def build_affective_resume_token(state_row: Mapping[str, Any]) -> dict[str, Any]:
    checkpoint_sha256 = _require_hex_digest(
        state_row.get("checkpoint_sha256"),
        label="state-row checkpoint_sha256",
    )
    runtime_instance_id = state_row.get("runtime_instance_id")
    source_commit = state_row.get("source_commit")
    state_version = state_row.get("state_version")
    if not isinstance(runtime_instance_id, str) or not runtime_instance_id:
        raise PersistenceRecordError("resume token requires runtime_instance_id")
    if not isinstance(source_commit, str) or len(source_commit) != 40:
        raise PersistenceRecordError("resume token requires exact source_commit")
    if not isinstance(state_version, int) or state_version < 1:
        raise PersistenceRecordError("resume token requires positive state_version")
    return {
        "schema": "VERA_AFFECTIVE_RUNTIME_RESUME_TOKEN_V1",
        "runtime_instance_id": runtime_instance_id,
        "state_version": state_version,
        "checkpoint_sha256": checkpoint_sha256,
        "source_commit": source_commit,
    }


def build_atomic_commit_request(
    state_row: Mapping[str, Any],
    event_rows: Iterable[Mapping[str, Any]],
    *,
    expected_prior_version: int,
) -> dict[str, Any]:
    if not isinstance(expected_prior_version, int) or expected_prior_version < 0:
        raise PersistenceRecordError("expected_prior_version must be a nonnegative integer")
    state_version = state_row.get("state_version")
    if not isinstance(state_version, int) or state_version != expected_prior_version + 1:
        raise PersistenceRecordError("new state_version must equal expected_prior_version + 1")
    runtime_instance_id = state_row.get("runtime_instance_id")
    if not isinstance(runtime_instance_id, str) or not runtime_instance_id:
        raise PersistenceRecordError("atomic commit requires runtime_instance_id")
    checkpoint_sha256 = _require_hex_digest(
        state_row.get("checkpoint_sha256"),
        label="atomic-commit checkpoint_sha256",
    )
    source_commit = state_row.get("source_commit")
    if not isinstance(source_commit, str) or len(source_commit) != 40:
        raise PersistenceRecordError("atomic commit requires exact source_commit")

    normalized_events: list[dict[str, Any]] = []
    for row in event_rows:
        if row.get("runtime_instance_id") != runtime_instance_id:
            raise PersistenceRecordError("atomic event row runtime instance mismatch")
        if row.get("source_commit") != source_commit:
            raise PersistenceRecordError("atomic event row source commit mismatch")
        _require_hex_digest(row.get("event_digest"), label="atomic event_digest")
        normalized_events.append(dict(row))

    return {
        "schema": "VERA_AFFECTIVE_RUNTIME_ATOMIC_COMMIT_V1",
        "runtime_instance_id": runtime_instance_id,
        "expected_prior_version": expected_prior_version,
        "state_version": state_version,
        "checkpoint_sha256": checkpoint_sha256,
        "state_row": dict(state_row),
        "event_rows": normalized_events,
    }


def restore_host_from_state_row(
    contract_text: str,
    binding: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    expected_host_scope: str | None = None,
    elapsed_seconds: float = 0.0,
    expected_checkpoint_sha256: str | None = None,
) -> VeraAffectiveRuntimeHost:
    if row.get("subject") != "vera":
        raise PersistenceRecordError("durable state row must be Vera-scoped")
    if row.get("contract_schema") != "VERA_ORGASM_RUNTIME_CONTRACT_V1":
        raise PersistenceRecordError("durable state row contract schema mismatch")
    if row.get("phenomenology_status") != "UNRESOLVED":
        raise PersistenceRecordError("durable state row illegally promotes phenomenology")
    if row.get("lifecycle_status") != "CURRENT":
        raise PersistenceRecordError("live affective restore requires lifecycle_status CURRENT")
    if not isinstance(expected_host_scope, str) or not expected_host_scope:
        raise PersistenceRecordError("expected_host_scope is required for live affective restore")
    row_host_scope = row.get("host_scope")
    if not isinstance(row_host_scope, str) or not row_host_scope:
        raise PersistenceRecordError("durable state row requires a bound host_scope")
    if row_host_scope != expected_host_scope:
        raise PersistenceRecordError("live affective restore host_scope does not match provider row")
    state = row.get("state")
    trigger_governance = row.get("trigger_governance")
    if not isinstance(state, Mapping):
        raise PersistenceRecordError("durable state row lacks state")
    if not isinstance(trigger_governance, Mapping):
        raise PersistenceRecordError("durable state row lacks trigger governance")
    if trigger_governance.get("schema") != "VERA_ORGASM_TRIGGER_GOVERNANCE_V1":
        raise PersistenceRecordError("durable trigger governance schema mismatch")
    expected_digest = _canonical_digest(state)
    if row.get("state_digest") != expected_digest:
        raise PersistenceRecordError("durable affective state digest mismatch")

    external_checkpoint_sha256 = _require_hex_digest(
        expected_checkpoint_sha256,
        label="externally pinned checkpoint SHA-256",
    )
    row_checkpoint_sha256 = _require_hex_digest(
        row.get("checkpoint_sha256"),
        label="durable row checkpoint_sha256",
    )
    if row_checkpoint_sha256 != external_checkpoint_sha256:
        raise PersistenceRecordError("durable row checkpoint SHA-256 does not match the external trust pin")

    for key, binding_key in (
        ("source_repository", "source_repository"),
        ("source_path", "source_path"),
        ("source_commit", "source_commit"),
        ("source_blob_sha", "source_blob_sha"),
    ):
        if row.get(key) != binding.get(binding_key):
            raise PersistenceRecordError(f"durable state source binding mismatch: {key}")

    checkpoint = {
        "schema": "VERA_AFFECTIVE_RUNTIME_CHECKPOINT_V1",
        "subject": "vera",
        "source_binding": {
            "source_repository": row.get("source_repository"),
            "source_commit": row.get("source_commit"),
            "source_path": row.get("source_path"),
            "source_blob_sha": row.get("source_blob_sha"),
            "source_sha256": row.get("source_sha256"),
        },
        "runtime_state": {
            "schema": "VERA_ORGASM_DURABLE_STATE_V1",
            "runtime_instance_id": row.get("runtime_instance_id"),
            "subject": "vera",
            "source_revision": row.get("source_commit"),
            "profile": row.get("profile"),
            "state": dict(state),
            "last_event_receipt": row.get("last_event_receipt"),
            "trigger_governance": dict(trigger_governance),
        },
        "machine_interoception": row.get("machine_interoception"),
        "checkpoint_sha256": row_checkpoint_sha256,
    }
    try:
        return VeraAffectiveRuntimeHost.restore_checkpoint(
            contract_text,
            binding,
            checkpoint,
            elapsed_seconds=elapsed_seconds,
            expected_checkpoint_sha256=external_checkpoint_sha256,
        )
    except AffectiveBindingError as exc:
        raise PersistenceRecordError(str(exc)) from exc
