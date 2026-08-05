"""Fresh-process recovery entry point using explicit evidence bindings."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .canonical import strict_loads
from .recovery import recover
from .temporal import OrientationGate, evidence_from_mapping


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    parser.add_argument("--recovery-input", required=True, help="strict JSON recovery input")
    args = parser.parse_args()

    recovery_input = strict_loads(Path(args.recovery_input).read_bytes())
    required = {
        "now",
        "orientation_source_mode",
        "orientation_evidence",
        "termination_receipt",
        "expected_checkpoint_digest",
        "expected_checkpoint_receipt_digest",
        "expected_predecessor_checkpoint_digest",
        "expected_self_model_head_digest",
        "expected_authority_state_digest",
    }
    if set(recovery_input) != required:
        raise ValueError("recovery input fields are missing or unknown")
    now = datetime.fromisoformat(str(recovery_input["now"]).replace("Z", "+00:00"))
    evidence = evidence_from_mapping(recovery_input["orientation_evidence"])
    orientation = OrientationGate().evaluate(
        evidence,
        now=now,
        source_mode=recovery_input["orientation_source_mode"],
    )
    receipt = recover(
        args.checkpoint,
        orientation,
        termination_receipt=recovery_input["termination_receipt"],
        expected_checkpoint_digest=recovery_input["expected_checkpoint_digest"],
        expected_checkpoint_receipt_digest=recovery_input["expected_checkpoint_receipt_digest"],
        expected_predecessor_checkpoint_digest=recovery_input["expected_predecessor_checkpoint_digest"],
        expected_self_model_head_digest=recovery_input["expected_self_model_head_digest"],
        expected_authority_state_digest=recovery_input["expected_authority_state_digest"],
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
