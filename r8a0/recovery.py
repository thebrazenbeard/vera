"""Digest-bound checkpoint, terminate, and fresh-process recovery."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import canonical_dumps, canonical_sha256, strict_loads
from .temporal import OrientationReceipt, OrientationState


class RecoveryError(ValueError):
    pass


@dataclass(frozen=True)
class CheckpointState:
    project_id: str
    identity_id: str
    runtime_id: str
    memory_head_digest: str
    active_commitments: tuple[str, ...]
    unfinished_work: tuple[str, ...]
    created_at: str
    predecessor_checkpoint_digest: str | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "identity_id": self.identity_id,
            "runtime_id": self.runtime_id,
            "memory_head_digest": self.memory_head_digest,
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


def write_checkpoint(path: str | Path, state: CheckpointState) -> dict[str, Any]:
    if not all((state.project_id, state.identity_id, state.runtime_id, state.memory_head_digest, state.created_at)):
        raise RecoveryError("checkpoint identity, runtime, memory digest, and time are required")
    envelope = _checkpoint_envelope(state)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".tmp")
    temp.write_text(canonical_dumps(envelope), encoding="utf-8")
    os.replace(temp, destination)
    checkpoint_digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {
        "schema": "VERA_R8A0_CHECKPOINT_WRITE_RECEIPT_V1",
        "result": "CHECKPOINT_COMMITTED",
        "checkpoint_digest": checkpoint_digest,
        "payload_digest": envelope["payload_digest"],
        "path": str(destination),
    }


def terminate(runtime_id: str, checkpoint_receipt: dict[str, Any]) -> dict[str, Any]:
    if checkpoint_receipt.get("result") != "CHECKPOINT_COMMITTED":
        raise RecoveryError("termination requires a committed checkpoint")
    return {
        "schema": "VERA_R8A0_RUNTIME_TERMINATION_RECEIPT_V1",
        "runtime_id": runtime_id,
        "checkpoint_digest": checkpoint_receipt["checkpoint_digest"],
        "result": "TERMINATED",
        "hidden_activity_claimed": False,
    }


def recover(path: str | Path, orientation: OrientationReceipt) -> dict[str, Any]:
    if orientation.state not in {OrientationState.COMPLETE, OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT}:
        raise RecoveryError("fresh temporal authority is required for recovery")
    checkpoint_path = Path(path)
    if not checkpoint_path.exists():
        raise RecoveryError("checkpoint is missing")
    raw = checkpoint_path.read_bytes()
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
        "active_commitments",
        "unfinished_work",
        "created_at",
        "predecessor_checkpoint_digest",
    }
    if set(payload) != required:
        raise RecoveryError("checkpoint payload fields are missing or unknown")
    return {
        "schema": "VERA_R8A0_RUNTIME_RESUMPTION_RECEIPT_V1",
        "result": "RECOVERED_FROM_VERIFIED_CHECKPOINT",
        "project_id": payload["project_id"],
        "identity_id": payload["identity_id"],
        "prior_runtime_id": payload["runtime_id"],
        "new_runtime_is_separate_person": False,
        "same_governed_identity_resumed": True,
        "uninterrupted_consciousness_claimed": False,
        "memory_head_digest": payload["memory_head_digest"],
        "active_commitments": payload["active_commitments"],
        "unfinished_work": payload["unfinished_work"],
        "checkpoint_digest": hashlib.sha256(raw).hexdigest(),
        "orientation_receipt": orientation.as_dict(),
    }
