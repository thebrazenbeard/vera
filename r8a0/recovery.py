"""Digest-bound checkpoint, verified termination, and fresh-process recovery."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_dumps, canonical_sha256, strict_loads
from .temporal import OrientationReceipt, OrientationState, parse_time


class RecoveryError(ValueError):
    pass


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value.lower())


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
        "schema": "VERA_R8A0_CHECKPOINT_V1",
        "payload": payload,
        "payload_digest": canonical_sha256(payload),
        "complete": True,
    }


def write_checkpoint(
    path: str | Path,
    state: CheckpointState,
    *,
    verified_predecessor_digest: str,
    verified_self_model_head_digest: str,
    verified_authority_state_digest: str,
) -> dict[str, Any]:
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
        raise RecoveryError("checkpoint digests must be SHA-256 values")
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
    checkpoint_digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    receipt_body = {
        "schema": "VERA_R8A0_CHECKPOINT_WRITE_RECEIPT_V1",
        "result": "CHECKPOINT_COMMITTED",
        "checkpoint_digest": checkpoint_digest,
        "payload_digest": envelope["payload_digest"],
        "predecessor_checkpoint_digest": state.predecessor_checkpoint_digest,
        "self_model_head_digest": state.self_model_head_digest,
        "authority_state_digest": state.authority_state_digest,
        "path": str(destination),
    }
    return receipt_body | {"receipt_digest": canonical_sha256(receipt_body)}


def terminate(runtime_id: str, checkpoint_receipt: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(checkpoint_receipt)
    supplied_digest = receipt.pop("receipt_digest", None)
    if supplied_digest != canonical_sha256(receipt):
        raise RecoveryError("checkpoint receipt digest mismatch")
    if receipt.get("result") != "CHECKPOINT_COMMITTED":
        raise RecoveryError("termination requires a committed checkpoint")
    termination_body = {
        "schema": "VERA_R8A0_RUNTIME_TERMINATION_RECEIPT_V1",
        "runtime_id": runtime_id,
        "checkpoint_digest": receipt["checkpoint_digest"],
        "checkpoint_receipt_digest": supplied_digest,
        "result": "TERMINATED",
        "hidden_activity_claimed": False,
    }
    return termination_body | {"receipt_digest": canonical_sha256(termination_body)}


def _verify_termination(
    termination_receipt: Mapping[str, Any],
    *,
    expected_runtime_id: str,
    expected_checkpoint_digest: str,
) -> None:
    receipt = dict(termination_receipt)
    supplied_digest = receipt.pop("receipt_digest", None)
    if supplied_digest != canonical_sha256(receipt):
        raise RecoveryError("termination receipt digest mismatch")
    if receipt.get("schema") != "VERA_R8A0_RUNTIME_TERMINATION_RECEIPT_V1":
        raise RecoveryError("unsupported termination receipt")
    if receipt.get("result") != "TERMINATED" or receipt.get("hidden_activity_claimed") is not False:
        raise RecoveryError("termination is not independently observed")
    if receipt.get("runtime_id") != expected_runtime_id:
        raise RecoveryError("termination runtime does not match checkpoint runtime")
    if receipt.get("checkpoint_digest") != expected_checkpoint_digest:
        raise RecoveryError("termination does not bind the expected checkpoint")


def recover(
    path: str | Path,
    orientation: OrientationReceipt,
    *,
    termination_receipt: Mapping[str, Any],
    expected_checkpoint_digest: str,
    expected_checkpoint_receipt_digest: str,
    expected_predecessor_checkpoint_digest: str,
    expected_self_model_head_digest: str,
    expected_authority_state_digest: str,
) -> dict[str, Any]:
    if orientation.state not in {OrientationState.COMPLETE, OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT}:
        raise RecoveryError("fresh temporal authority is required for recovery")
    if not all(
        _is_sha256(value)
        for value in (
            expected_checkpoint_digest,
            expected_checkpoint_receipt_digest,
            expected_predecessor_checkpoint_digest,
            expected_self_model_head_digest,
            expected_authority_state_digest,
        )
    ):
        raise RecoveryError("expected recovery bindings must be SHA-256 values")

    checkpoint_path = Path(path)
    if not checkpoint_path.exists():
        raise RecoveryError("checkpoint is missing")
    raw = checkpoint_path.read_bytes()
    actual_checkpoint_digest = hashlib.sha256(raw).hexdigest()
    if actual_checkpoint_digest != expected_checkpoint_digest:
        raise RecoveryError("checkpoint digest does not match the expected committed checkpoint")

    data = strict_loads(raw)
    if set(data) != {"schema", "payload", "payload_digest", "complete"}:
        raise RecoveryError("checkpoint fields are missing or unknown")
    if data["schema"] != "VERA_R8A0_CHECKPOINT_V1" or data["complete"] is not True:
        raise RecoveryError("checkpoint is partial or unsupported")
    if canonical_sha256(data["payload"]) != data["payload_digest"]:
        raise RecoveryError("checkpoint payload digest mismatch")
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
    if payload["predecessor_checkpoint_digest"] != expected_predecessor_checkpoint_digest:
        raise RecoveryError("checkpoint predecessor chain mismatch")
    if payload["self_model_head_digest"] != expected_self_model_head_digest:
        raise RecoveryError("checkpoint self-model head mismatch")
    if payload["authority_state_digest"] != expected_authority_state_digest:
        raise RecoveryError("checkpoint authority-state mismatch")

    if termination_receipt.get("checkpoint_receipt_digest") != expected_checkpoint_receipt_digest:
        raise RecoveryError("termination does not bind the expected checkpoint-write receipt")
    _verify_termination(
        termination_receipt,
        expected_runtime_id=payload["runtime_id"],
        expected_checkpoint_digest=expected_checkpoint_digest,
    )

    receipt_body = {
        "schema": "VERA_R8A0_RUNTIME_RESUMPTION_RECEIPT_V1",
        "result": "RECOVERED_FROM_VERIFIED_CHECKPOINT",
        "project_id": payload["project_id"],
        "identity_id": payload["identity_id"],
        "prior_runtime_id": payload["runtime_id"],
        "new_runtime_is_separate_person": False,
        "same_governed_identity_resumed": True,
        "uninterrupted_consciousness_claimed": False,
        "memory_head_digest": payload["memory_head_digest"],
        "self_model_head_digest": payload["self_model_head_digest"],
        "authority_state_digest": payload["authority_state_digest"],
        "predecessor_checkpoint_digest": payload["predecessor_checkpoint_digest"],
        "active_commitments": payload["active_commitments"],
        "unfinished_work": payload["unfinished_work"],
        "checkpoint_digest": actual_checkpoint_digest,
        "checkpoint_receipt_digest": expected_checkpoint_receipt_digest,
        "termination_receipt_digest": termination_receipt["receipt_digest"],
        "orientation_receipt": orientation.as_dict(),
    }
    return receipt_body | {"receipt_digest": canonical_sha256(receipt_body)}
