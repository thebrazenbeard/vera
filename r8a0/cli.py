"""Observed lifecycle entry points for the bounded R8A0 slice."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from .canonical import strict_loads
from .recovery import CheckpointState, recover, terminate, write_checkpoint
from .temporal import evidence_from_mapping


def _receipt_key() -> bytes:
    value = os.environ.get("VERA_R8A0_RECEIPT_KEY_HEX", "")
    if len(value) < 32 or len(value) % 2:
        raise ValueError("VERA_R8A0_RECEIPT_KEY_HEX must contain at least 16 bytes of hexadecimal key material")
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError("VERA_R8A0_RECEIPT_KEY_HEX is not valid hexadecimal") from exc


def _checkpoint_terminate(args: argparse.Namespace) -> int:
    input_data = strict_loads(Path(args.state_input).read_bytes())
    if set(input_data) != {
        "state",
        "verified_predecessor_digest",
        "verified_self_model_head_digest",
        "verified_authority_state_digest",
    }:
        raise ValueError("checkpoint lifecycle input fields are missing or unknown")
    state_data = input_data["state"]
    if set(state_data) != {
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
    }:
        raise ValueError("checkpoint state fields are missing or unknown")
    state = CheckpointState(
        project_id=state_data["project_id"],
        identity_id=state_data["identity_id"],
        runtime_id=state_data["runtime_id"],
        memory_head_digest=state_data["memory_head_digest"],
        self_model_head_digest=state_data["self_model_head_digest"],
        authority_state_digest=state_data["authority_state_digest"],
        active_commitments=tuple(state_data["active_commitments"]),
        unfinished_work=tuple(state_data["unfinished_work"]),
        created_at=state_data["created_at"],
        predecessor_checkpoint_digest=state_data["predecessor_checkpoint_digest"],
    )
    key = _receipt_key()
    checkpoint_receipt = write_checkpoint(
        args.checkpoint,
        state,
        checkpoint_receipt_path=args.checkpoint_receipt,
        verified_predecessor_digest=input_data["verified_predecessor_digest"],
        verified_self_model_head_digest=input_data["verified_self_model_head_digest"],
        verified_authority_state_digest=input_data["verified_authority_state_digest"],
        receipt_key=key,
    )
    termination_receipt = terminate(
        state.runtime_id,
        checkpoint_receipt_path=args.checkpoint_receipt,
        termination_receipt_path=args.termination_receipt,
        receipt_key=key,
    )
    print(
        json.dumps(
            {
                "result": "CHECKPOINT_WRITTEN_AND_RUNTIME_TERMINATED",
                "runtime_id": state.runtime_id,
                "checkpoint_receipt_mac": checkpoint_receipt["receipt_mac"],
                "termination_receipt_mac": termination_receipt["receipt_mac"],
            },
            sort_keys=True,
        )
    )
    return 0


def _recover(args: argparse.Namespace) -> int:
    recovery_input = strict_loads(Path(args.recovery_input).read_bytes())
    required = {
        "now",
        "orientation_source_mode",
        "orientation_evidence",
        "checkpoint_receipt_path",
        "termination_receipt_path",
        "expected_checkpoint_receipt_mac",
        "expected_termination_receipt_mac",
        "expected_predecessor_checkpoint_digest",
        "expected_memory_head_digest",
        "expected_self_model_head_digest",
        "expected_authority_state_digest",
        "successor_runtime_id",
    }
    if set(recovery_input) != required:
        raise ValueError("recovery input fields are missing or unknown")
    now = datetime.fromisoformat(str(recovery_input["now"]).replace("Z", "+00:00"))
    receipt = recover(
        args.checkpoint,
        orientation_evidence=evidence_from_mapping(recovery_input["orientation_evidence"]),
        orientation_now=now,
        orientation_source_mode=recovery_input["orientation_source_mode"],
        checkpoint_receipt_path=recovery_input["checkpoint_receipt_path"],
        termination_receipt_path=recovery_input["termination_receipt_path"],
        expected_checkpoint_receipt_mac=recovery_input["expected_checkpoint_receipt_mac"],
        expected_termination_receipt_mac=recovery_input["expected_termination_receipt_mac"],
        expected_predecessor_checkpoint_digest=recovery_input["expected_predecessor_checkpoint_digest"],
        expected_memory_head_digest=recovery_input["expected_memory_head_digest"],
        expected_self_model_head_digest=recovery_input["expected_self_model_head_digest"],
        expected_authority_state_digest=recovery_input["expected_authority_state_digest"],
        successor_runtime_id=recovery_input["successor_runtime_id"],
        receipt_key=_receipt_key(),
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    checkpoint_terminate = subparsers.add_parser("checkpoint-terminate")
    checkpoint_terminate.add_argument("--state-input", required=True)
    checkpoint_terminate.add_argument("--checkpoint", required=True)
    checkpoint_terminate.add_argument("--checkpoint-receipt", required=True)
    checkpoint_terminate.add_argument("--termination-receipt", required=True)
    checkpoint_terminate.set_defaults(handler=_checkpoint_terminate)

    recovery = subparsers.add_parser("recover")
    recovery.add_argument("checkpoint")
    recovery.add_argument("--recovery-input", required=True)
    recovery.set_defaults(handler=_recover)

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
