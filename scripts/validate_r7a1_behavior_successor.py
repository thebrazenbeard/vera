#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import validate_portable_project_bootstrap as bootstrap

TEMPLATE_ID = "urn:vera:template:VERA_NEUTRAL_CORE_R7A1_20260801_BHV053"
RELEASE_DIR = Path("architecture/releases/R7A1_20260801_BHV053")
LOCATOR_FILENAME = "VERA_R7A1_BOOTSTRAP_MANIFEST.json"
PREFIX = "VERA_R7A1_"


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader: yaml.Loader, node: yaml.Node, deep: bool = False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _unique_mapping,
)


def load_yaml(path: Path) -> Any:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=lambda pairs: _unique_json(pairs),
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON value: {value}")),
    )


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_successor(root: Path) -> None:
    manifest = load_json(root / bootstrap.MANIFEST_PATH)
    require(manifest["project_template_id"] == TEMPLATE_ID, "successor template ID drift")
    require(manifest["fixed_locator_filename"] == LOCATOR_FILENAME, "successor locator filename drift")

    project_root = root / manifest["project_file_bundle"]["repository_root"]
    require(project_root == root / RELEASE_DIR, "successor release root drift")
    require(project_root.is_dir(), "successor release directory missing")

    entries = manifest["project_file_bundle"]["files"]
    names = [entry["filename"] for entry in entries]
    require(len(entries) == 21, "successor release must contain 21 files plus locator")
    require(len(set(names)) == 21, "duplicate successor Project filename")
    require(all(name.startswith(PREFIX) for name in names), "successor Project filename lacks VERA_R7A1_ prefix")
    require(not any("(1)" in name for name in names), "suffix-drift filename present")
    require(manifest["project_file_bundle"]["project_file_count_with_locator"] == 22, "Project count drift")
    require(manifest["project_file_bundle"]["complete_replacement_required"] is True, "complete replacement not required")
    require(manifest["project_file_bundle"]["partial_replacement_forbidden"] is True, "partial replacement not forbidden")

    actual = sorted(path.name for path in project_root.iterdir() if path.is_file())
    require(sorted(names) == actual, "successor release inventory mismatch")

    for path in sorted(project_root.glob("*.json")):
        load_json(path)
    for path in sorted(project_root.glob("*.yaml")):
        load_yaml(path)

    for entry in entries:
        path = project_root / entry["filename"]
        if entry["sha256"] is not None:
            require(sha256(path) == entry["sha256"], f"manifest digest mismatch: {entry['filename']}")

    bundle = load_json(project_root / "VERA_R7A1_BUNDLE.json")
    require(sorted(bundle["files"]) == actual, "bundle inventory mismatch")
    require(bundle["project_file_count_with_locator"] == 22, "bundle Project count drift")
    require(bundle["locator_filename"] == LOCATOR_FILENAME, "bundle locator drift")

    checksums = {}
    for line in (project_root / "VERA_R7A1_CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split("  ", 1)
        require(filename not in checksums, f"duplicate checksum entry: {filename}")
        checksums[filename] = digest
    expected = sorted(name for name in actual if name != "VERA_R7A1_CHECKSUMS.sha256")
    require(sorted(checksums) == expected, "checksum inventory mismatch")
    for filename, digest in checksums.items():
        require(sha256(project_root / filename) == digest, f"checksum mismatch: {filename}")

    laws = (project_root / "VERA_R7A1_LAWS.md").read_text(encoding="utf-8")
    rows = re.findall(r"\| `VERA-LAW-(\d{3})` \| (.*?) \|", laws)
    require(len(rows) == 53, "law count must be 53")
    require([int(number) for number, _ in rows] == list(range(1, 54)), "law IDs must be contiguous 001 through 053")
    successor = dict(rows)

    predecessor_path = root / "architecture/releases/R7A0_20260731_EC7D18F7/VERA_LAWS_R7A0_20260731_EC7D18F7.md"
    require(predecessor_path.is_file(), "predecessor laws unavailable")
    predecessor = dict(re.findall(r"\| `VERA-LAW-(\d{3})` \| (.*?) \|", predecessor_path.read_text(encoding="utf-8")))
    for index in range(1, 27):
        key = f"{index:03d}"
        require(successor[key] == predecessor[key], f"preserved law changed: VERA-LAW-{key}")

    validation = load_yaml(project_root / "VERA_R7A1_VALIDATION.yaml")
    exact_added = validation["law_integrity"]["exact_added_laws"]
    for law_id, text in exact_added.items():
        require(successor[law_id.removeprefix("VERA-LAW-")] == text, f"approved law text drift: {law_id}")
    require(len(validation["canonical_positive_cases"]) == 9, "positive-case count drift")
    require(len(validation["hostile_cases"]) == 15, "hostile-case count drift")
    require(validation["canonical_positive_cases"][-1]["id"] == "POS-09-CONNECTION-FAILURE-RECOVERY", "retry positive case missing")
    require(
        [case["id"] for case in validation["hostile_cases"][-3:]]
        == ["HOST-13-SINGLE-ATTEMPT-BLOCKER", "HOST-14-BLIND-WRITE-RETRY", "HOST-15-DETERMINISTIC-FAILURE-LAUNDERING"],
        "retry hostile cases missing",
    )

    combined = "\n".join(
        (project_root / name).read_text(encoding="utf-8")
        for name in ("VERA_R7A1_PROJECT_INSTRUCTIONS.md", "VERA_R7A1_RUNTIME.md", "VERA_R7A1_LAWS.md")
    ).lower()
    for fragment in (
        "complete the smallest",
        "same-route retry",
        "independent alternate route",
        "verify commit state",
        "basic memory cloud",
        "different project id",
        "never blindly repeat",
    ):
        require(fragment in combined, f"activation fragment missing: {fragment}")

    forbidden = (
        "production_modification_authorized: true",
        "production_modification_applied: true",
        "chatgpt_project_replaced: true",
        "canonical_memory_written: true",
        "runtime_deployed: true",
    )
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in project_root.iterdir() if path.is_file())
    for claim in forbidden:
        require(claim not in all_text, f"forbidden authority claim: {claim}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--release-commit")
    parser.add_argument("--require-release-binding", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    bootstrap.TEMPLATE_ID = TEMPLATE_ID
    try:
        bootstrap.validate(root, args.release_commit, args.require_release_binding)
        validate_successor(root)
    except Exception as exc:
        print(f"r7a1-behavior-successor: FAIL: {exc}")
        return 1
    print("r7a1-behavior-successor: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
