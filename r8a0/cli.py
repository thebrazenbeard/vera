"""Fresh-process recovery entry point."""
from __future__ import annotations

import argparse
import json
from datetime import datetime

from .recovery import recover
from .temporal import OrientationGate, current_evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    parser.add_argument("--now", required=True, help="timezone-aware ISO timestamp")
    args = parser.parse_args()
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
    receipt = OrientationGate().evaluate(current_evidence(now), now=now)
    print(json.dumps(recover(args.checkpoint, receipt), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
