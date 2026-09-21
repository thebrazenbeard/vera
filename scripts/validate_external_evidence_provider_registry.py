#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "architecture/integration/VERA_EXTERNAL_EVIDENCE_PROVIDER_REGISTRY_V1.json"
SCHEMA = ROOT / "schemas/vera_external_evidence_provider_registry_v1.schema.json"

EXPECTED_PROVIDER_HEAD = "539b5988e0913130427da3d1098d84592d1122cf"
EXPECTED_MERGED_COMMIT = "f073feb409f71a0fdea7baa9053e54bcf8ed89a0"
EXPECTED_BINDINGS = {
    "architecture/DEEP_MEMORY_ARCHITECTURE_BINDING_V1.json": (
        "a951cbfad09e2dcc3685a04e47680df16a6edfc9",
        "architecture/integration/vendor/DEEP_MEMORY_ARCHITECTURE_BINDING_V1.json",
    ),
    "architecture/DEEP_MEMORY_INTEGRATION_CONTRACT_V1.md": (
        "35f9be1c67d5898724ac85256af8cc9e667039f1",
        "architecture/integration/vendor/DEEP_MEMORY_INTEGRATION_CONTRACT_V1.md",
    ),
    "schema/DEEP_MEMORY_EVIDENCE_RESULT_V1.schema.json": (
        "d9c0b09e16557c4871b2095bdf06962a3562ebf0",
        "architecture/integration/vendor/DEEP_MEMORY_EVIDENCE_RESULT_V1.schema.json",
    ),
}
EXPECTED_PRECEDENCE = [
    "platform_and_safety",
    "Patrick_current_task_correction_privacy_permission_scope",
    "fresh_current_control_and_state",
    "current_governed_memory",
    "deep_memory_historical_evidence",
    "inference",
]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def git_blob(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    completed = subprocess.run(
        ["git", "hash-object", f"--path={relative}", str(path)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def validate(root: Path = ROOT) -> None:
    root = root.resolve()
    registry = load(root / REGISTRY.relative_to(ROOT))
    schema = load(root / SCHEMA.relative_to(ROOT))
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(registry),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ValueError(
            "; ".join(f"{list(error.path)}: {error.message}" for error in errors)
        )

    providers = registry["providers"]
    if len(providers) != 1:
        raise ValueError("V1 requires exactly one pinned external evidence provider")
    provider = providers[0]
    if provider["provider_class"] != "EXTERNAL_EVIDENCE_PROVIDER":
        raise ValueError("external evidence provider may not impersonate a workstream owner")
    source = provider["source"]
    if source["reviewed_provider_head"] != EXPECTED_PROVIDER_HEAD:
        raise ValueError("reviewed Deep Memory provider head drift")
    if source["source_merged_commit"] != EXPECTED_MERGED_COMMIT:
        raise ValueError("merged Deep Memory provider commit drift")
    observed = {
        item["path"]: (item["blob"], item["vendored_path"])
        for item in source["bindings"]
    }
    if observed != EXPECTED_BINDINGS:
        raise ValueError("external provider path/blob binding drift")

    for external_path, (expected_blob, vendored_path) in EXPECTED_BINDINGS.items():
        path = root / vendored_path
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing regular vendored provider artifact: {vendored_path}")
        actual = git_blob(path, root)
        if actual != expected_blob:
            raise ValueError(
                f"vendored provider artifact drift for {external_path}: {actual}"
            )

    adapter = root / provider["consumer_adapter_path"]
    contract = root / provider["consumer_contract_path"]
    if not adapter.is_file() or adapter.is_symlink():
        raise ValueError("consumer adapter path is missing or unsafe")
    if not contract.is_file() or contract.is_symlink():
        raise ValueError("consumer contract path is missing or unsafe")

    if provider["operations"] != ["EVIDENCE_SEARCH"]:
        raise ValueError("external provider operation set widened")
    if provider["currentness_precedence"] != EXPECTED_PRECEDENCE:
        raise ValueError("Deep Memory currentness precedence drift")
    if provider["canonical_memory_transfer"]:
        raise ValueError("provider discovery cannot transfer canonical memory")
    if provider["execution_authorized"]:
        raise ValueError("provider discovery cannot authorize execution")
    if provider["runtime_install_authorized"]:
        raise ValueError("provider registry cannot claim runtime installation")
    if provider["newest_wins_conflict_collapse"]:
        raise ValueError("historical evidence cannot use newest-wins conflict collapse")
    if provider["discovery_implies_admission"]:
        raise ValueError("provider discovery cannot imply memory admission")
    if provider["identity_keying"] != "PROVENANCE_ONLY_NOT_RUNTIME_IDENTITY":
        raise ValueError("model/chat/session/branch provenance cannot key Vera identity")

    bridge = provider["admission_bridge"]
    if (
        bridge["operation"] != "HISTORICAL_TO_CURRENT_ADMISSION_REVIEW"
        or bridge["mode"] != "SEPARATE_EXPLICIT_REVIEW_ONLY"
        or not bridge["requires_separate_authority"]
        or not bridge["requires_receipt"]
        or bridge["automatic"]
    ):
        raise ValueError("historical-to-current bridge boundary weakened")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    validate(args.root.resolve())
    print("external evidence provider registry: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
