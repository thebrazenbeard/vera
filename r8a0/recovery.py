"""Authenticated checkpoint, observed termination, and fresh-process recovery."""
from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from .canonical import canonical_bytes, canonical_dumps, canonical_sha256, strict_loads
from .temporal import OrientationGate, OrientationState, TimeEvidence, parse_time


class RecoveryError(ValueError):
    pass


def _validated_key(value: bytes) -> bytes:
    if not isinstance(value, bytes) or len(value) < 16:
        raise RecoveryError("receipt authentication key must contain at least 16 bytes")
    return value


def _is_sha256(value: str) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _mac(key: bytes, value: Any) -> str:
    return hmac.new(key, canonical_bytes(value), hashlib.sha256).hexdigest()


def _atomic_write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".tmp")
    temp.write_text(canonical_dumps(dict(value)), encoding="utf-8")
    os.replace(temp, destination)
    if strict_loads(destination.read_bytes()) != dict(value):
        raise RecoveryError("persisted lifecycle receipt readback mismatch")


def _signed_receipt(body: Mapping[str, Any], key: bytes) -> dict[str, Any]:
    material = dict(body)
    return material | {"receipt_mac": _mac(key, material)}


def _verify_signed_receipt(
    receipt: Mapping[str, Any],
    *,
    key: bytes,
    expected_schema: str,
    required_body_fields: set[str],
) -> dict[str, Any]:
    if set(receipt) != required_body_fields | {"receipt_mac"}:
        raise RecoveryError("lifecycle receipt fields are missing or unknown")
    body = {name: receipt[name] for name in required_body_fields}
    if not hmac.compare_digest(str(receipt["receipt_mac"]), _mac(key, body)):
        raise RecoveryError("lifecycle receipt authentication mismatch")
    if body.get("schema") != expected_schema:
        raise RecoveryError("unsupported lifecycle receipt schema")
    return body


@dataclass(frozen=True)
class CheckpointState:
    project_id: str
    identity_id: str
    runtime_id: str
    memory_head_digest: str
    self_model_head_digest: str
    authority_state_digest: str
    active_commitments: tuple[str, ...]
    unfinished_work: tuple[str, ...]
    created_at: str
    predecessor_checkpoint_digest: str

    def payload(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "identity_id": self.identity_id,
            "runtime_id": self.runtime_id,
            "memory_head_digest": self.memory_head_digest,
            "self_model_head_digest": self.self_model_head_digest,
            "authority_state_digest": self.authority_state_digest,
            "active_commitments": list(self.active_commitments),
            "unfinished_work": list(self.unfinished_work),
            "created_at": self.created_at,
            "predecessor_checkpoint_digest": self.predecessor_checkpoint_digest,
        }


def _checkpoint_envelope(state: CheckpointState) -> dict[str, Any]:
    payload = state.payload()
    return {
        "schema": "VERA_R8A0_CHECKPOINT_V2",
        "payload": payload,
        "payload_digest": canonical_sha256(payload),
        "complete": True,
    }


def write_checkpoint(
    path: str | Path,
    state: CheckpointState,
    *,
    checkpoint_receipt_path: str | Path,
    verified_predecessor_digest: str,
    verified_self_model_head_digest: str,
    verified_authority_state_digest: str,
    receipt_key: bytes,
) -> dict[str, Any]:
    key = _validated_key(receipt_key)
    if not all((state.project_id, state.identity_id, state.runtime_id, state.created_at)):
        raise RecoveryError("checkpoint identity, runtime, and time are required")
    parse_time(state.created_at)
    digest_fields = {
        "memory head": state.memory_head_digest,
        "self-model head": state.self_model_head_digest,
        "authority state": state.authority_state_digest,
        "predecessor checkpoint": state.predecessor_checkpoint_digest,
    }
    if any(not _is_sha256(value) for value in digest_fields.values()):
        raise RecoveryError("checkpoint digests must be lowercase SHA-256 values")
    if state.predecessor_checkpoint_digest != verified_predecessor_digest:
        raise RecoveryError("checkpoint predecessor is not the verified predecessor")
    if state.self_model_head_digest != verified_self_model_head_digest:
        raise RecoveryError("checkpoint self-model head is not verified")
    if state.authority_state_digest != verified_authority_state_digest:
        raise RecoveryError("checkpoint authority state is not verified")

    envelope = _checkpoint_envelope(state)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".tmp")
    temp.write_text(canonical_dumps(envelope), encoding="utf-8")
    os.replace(temp, destination)
    readback = strict_loads(destination.read_bytes())
    if readback != envelope:
        raise RecoveryError("checkpoint persisted readback mismatch")
    checkpoint_digest = hashlib.sha256(destination.read_bytes()).hexdigest()

    receipt = _signed_receipt(
        {
            "schema": "VERA_R8A0_CHECKPOINT_WRITE_RECEIPT_V3",
            "result": "CHECKPOINT_COMMITTED",
            "checkpoint_path": str(destination.resolve()),
            "checkpoint_digest": checkpoint_digest,
            "payload_digest": envelope["payload_digest"],
            "predecessor_checkpoint_digest": state.predecessor_checkpoint_digest,
            "memory_head_digest": state.memory_head_digest,
            "self_model_head_digest": state.self_model_head_digest,
            "authority_state_digest": state.authority_state_digest,
            "runtime_id": state.runtime_id,
            "project_id": state.project_id,
            "identity_id": state.identity_id,
        },
        key,
    )
    _atomic_write_json(checkpoint_receipt_path, receipt)
    return receipt


def read_checkpoint_receipt(path: str | Path, *, receipt_key: bytes) -> dict[str, Any]:
    key = _validated_key(receipt_key)
    receipt_path = Path(path)
    if not receipt_path.exists():
        raise RecoveryError("checkpoint receipt is missing")
    receipt = strict_loads(receipt_path.read_bytes())
    body = _verify_signed_receipt(
        receipt,
        key=key,
        expected_schema="VERA_R8A0_CHECKPOINT_WRITE_RECEIPT_V3",
        required_body_fields={
            "schema",
            "result",
            "checkpoint_path",
            "checkpoint_digest",
            "payload_digest",
            "predecessor_checkpoint_digest",
            "memory_head_digest",
            "self_model_head_digest",
            "authority_state_digest",
            "runtime_id",
            "project_id",
            "identity_id",
        },
    )
    if body["result"] != "CHECKPOINT_COMMITTED":
        raise RecoveryError("checkpoint receipt is not committed")
    checkpoint_path = Path(body["checkpoint_path"])
    if not checkpoint_path.exists():
        raise RecoveryError("checkpoint receipt target is missing")
    if hashlib.sha256(checkpoint_path.read_bytes()).hexdigest() != body["checkpoint_digest"]:
        raise RecoveryError("checkpoint receipt target digest mismatch")
    return dict(receipt)


def terminate(
    runtime_id: str,
    *,
    checkpoint_receipt_path: str | Path,
    termination_receipt_path: str | Path,
    receipt_key: bytes,
) -> dict[str, Any]:
    key = _validated_key(receipt_key)
    checkpoint_receipt = read_checkpoint_receipt(checkpoint_receipt_path, receipt_key=key)
    if checkpoint_receipt["runtime_id"] != runtime_id:
        raise RecoveryError("termination runtime does not match checkpoint runtime")
    receipt = _signed_receipt(
        {
            "schema": "VERA_R8A0_RUNTIME_TERMINATION_RECEIPT_V2",
            "result": "TERMINATED",
            "runtime_id": runtime_id,
            "checkpoint_digest": checkpoint_receipt["checkpoint_digest"],
            "checkpoint_receipt_mac": checkpoint_receipt["receipt_mac"],
            "terminating_process_id": os.getpid(),
            "hidden_activity_claimed": False,
        },
        key,
    )
    _atomic_write_json(termination_receipt_path, receipt)
    return receipt


def read_termination_receipt(path: str | Path, *, receipt_key: bytes) -> dict[str, Any]:
    key = _validated_key(receipt_key)
    receipt_path = Path(path)
    if not receipt_path.exists():
        raise RecoveryError("termination receipt is missing")
    receipt = strict_loads(receipt_path.read_bytes())
    body = _verify_signed_receipt(
        receipt,
        key=key,
        expected_schema="VERA_R8A0_RUNTIME_TERMINATION_RECEIPT_V2",
        required_body_fields={
            "schema",
            "result",
            "runtime_id",
            "checkpoint_digest",
            "checkpoint_receipt_mac",
            "terminating_process_id",
            "hidden_activity_claimed",
        },
    )
    if body["result"] != "TERMINATED" or body["hidden_activity_claimed"] is not False:
        raise RecoveryError("termination is not validly observed")
    if not isinstance(body["terminating_process_id"], int) or body["terminating_process_id"] <= 0:
        raise RecoveryError("termination process identity is invalid")
    return dict(receipt)


def recover(
    checkpoint_path: str | Path,
    *,
    orientation_evidence: Iterable[TimeEvidence],
    orientation_now: datetime,
    orientation_source_mode: str,
    checkpoint_receipt_path: str | Path,
    termination_receipt_path: str | Path,
    expected_checkpoint_receipt_mac: str,
    expected_termination_receipt_mac: str,
    expected_project_id: str,
    expected_identity_id: str,
    expected_predecessor_checkpoint_digest: str,
    expected_memory_head_digest: str,
    expected_self_model_head_digest: str,
    expected_authority_state_digest: str,
    successor_runtime_id: str,
    receipt_key: bytes,
) -> dict[str, Any]:
    key = _validated_key(receipt_key)
    if not expected_project_id or not expected_identity_id:
        raise RecoveryError("expected project and identity are required")
    if not isinstance(successor_runtime_id, str) or not successor_runtime_id.strip():
        raise RecoveryError("successor runtime ID is required")
    orientation = OrientationGate(integrity_key=key).evaluate(
        orientation_evidence,
        now=orientation_now,
        source_mode=orientation_source_mode,
    )
    if orientation.state not in {OrientationState.COMPLETE, OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT}:
        raise RecoveryError("fresh temporal authority is required for recovery")
    for value in (
        expected_predecessor_checkpoint_digest,
        expected_memory_head_digest,
        expected_self_model_head_digest,
        expected_authority_state_digest,
    ):
        if not _is_sha256(value):
            raise RecoveryError("expected recovery bindings must be lowercase SHA-256 values")

    checkpoint_receipt = read_checkpoint_receipt(checkpoint_receipt_path, receipt_key=key)
    termination_receipt = read_termination_receipt(termination_receipt_path, receipt_key=key)
    if not hmac.compare_digest(checkpoint_receipt["receipt_mac"], expected_checkpoint_receipt_mac):
        raise RecoveryError("checkpoint receipt does not match the independently observed receipt")
    if not hmac.compare_digest(termination_receipt["receipt_mac"], expected_termination_receipt_mac):
        raise RecoveryError("termination receipt does not match the independently observed receipt")
    if termination_receipt["checkpoint_receipt_mac"] != checkpoint_receipt["receipt_mac"]:
        raise RecoveryError("termination does not bind the persisted checkpoint receipt")
    if termination_receipt["checkpoint_digest"] != checkpoint_receipt["checkpoint_digest"]:
        raise RecoveryError("termination does not bind the persisted checkpoint")

    checkpoint = Path(checkpoint_path).resolve()
    if str(checkpoint) != checkpoint_receipt["checkpoint_path"]:
        raise RecoveryError("checkpoint path does not match persisted receipt")
    raw = checkpoint.read_bytes()
    if hashlib.sha256(raw).hexdigest() != checkpoint_receipt["checkpoint_digest"]:
        raise RecoveryError("checkpoint digest does not match persisted receipt")
    data = strict_loads(raw)
    if set(data) != {"schema", "payload", "payload_digest", "complete"}:
        raise RecoveryError("checkpoint fields are missing or unknown")
    if data["schema"] != "VERA_R8A0_CHECKPOINT_V2" or data["complete"] is not True:
        raise RecoveryError("checkpoint is partial or unsupported")
    if canonical_sha256(data["payload"]) != data["payload_digest"]:
        raise RecoveryError("checkpoint payload digest mismatch")
    if data["payload_digest"] != checkpoint_receipt["payload_digest"]:
        raise RecoveryError("checkpoint payload does not match persisted receipt")

    payload = data["payload"]
    required = {
        "project_id",
        "identity_id",
        "runtime_id",
        "memory_head_digest",
        "self_model_head_digest",
        "authority_state_digest",
        "active_commitments",
        "unfinished_work",
        "created_at",
        "predecessor_checkpoint_digest",
    }
    if set(payload) != required:
        raise RecoveryError("checkpoint payload fields are missing or unknown")
    if payload["project_id"] != expected_project_id or payload["identity_id"] != expected_identity_id:
        raise RecoveryError("checkpoint project or identity mismatch")
    if checkpoint_receipt["project_id"] != expected_project_id or checkpoint_receipt["identity_id"] != expected_identity_id:
        raise RecoveryError("checkpoint receipt project or identity mismatch")
    if payload["runtime_id"] != termination_receipt["runtime_id"]:
        raise RecoveryError("termination runtime does not match checkpoint runtime")
    if successor_runtime_id == payload["runtime_id"]:
        raise RecoveryError("successor runtime must differ from the terminated runtime")
    if termination_receipt["terminating_process_id"] == os.getpid():
        raise RecoveryError("recovery must execute in a process distinct from the terminated process")
    if payload["predecessor_checkpoint_digest"] != expected_predecessor_checkpoint_digest:
        raise RecoveryError("checkpoint predecessor chain mismatch")
    if payload["memory_head_digest"] != expected_memory_head_digest:
        raise RecoveryError("checkpoint memory head mismatch")
    if payload["self_model_head_digest"] != expected_self_model_head_digest:
        raise RecoveryError("checkpoint self-model head mismatch")
    if payload["authority_state_digest"] != expected_authority_state_digest:
        raise RecoveryError("checkpoint authority-state mismatch")
    if checkpoint_receipt["predecessor_checkpoint_digest"] != expected_predecessor_checkpoint_digest:
        raise RecoveryError("checkpoint receipt predecessor mismatch")
    if checkpoint_receipt["memory_head_digest"] != expected_memory_head_digest:
        raise RecoveryError("checkpoint receipt memory head mismatch")
    if checkpoint_receipt["self_model_head_digest"] != expected_self_model_head_digest:
        raise RecoveryError("checkpoint receipt self-model mismatch")
    if checkpoint_receipt["authority_state_digest"] != expected_authority_state_digest:
        raise RecoveryError("checkpoint receipt authority-state mismatch")

    receipt = _signed_receipt(
        {
            "schema": "VERA_R8A0_RUNTIME_RESUMPTION_RECEIPT_V2",
            "result": "RECOVERED_FROM_VERIFIED_CHECKPOINT",
            "project_id": payload["project_id"],
            "identity_id": payload["identity_id"],
            "prior_runtime_id": payload["runtime_id"],
            "successor_runtime_id": successor_runtime_id,
            "prior_process_id": termination_receipt["terminating_process_id"],
            "successor_process_id": os.getpid(),
            "runtime_transition_observed": True,
            "new_runtime_is_separate_person": False,
            "same_governed_identity_resumed": True,
            "uninterrupted_consciousness_claimed": False,
            "memory_head_digest": payload["memory_head_digest"],
            "self_model_head_digest": payload["self_model_head_digest"],
            "authority_state_digest": payload["authority_state_digest"],
            "predecessor_checkpoint_digest": payload["predecessor_checkpoint_digest"],
            "active_commitments": payload["active_commitments"],
            "unfinished_work": payload["unfinished_work"],
            "checkpoint_digest": checkpoint_receipt["checkpoint_digest"],
            "checkpoint_receipt_mac": checkpoint_receipt["receipt_mac"],
            "termination_receipt_mac": termination_receipt["receipt_mac"],
            "orientation_receipt": orientation.as_dict(),
        },
        key,
    )
    return receipt
