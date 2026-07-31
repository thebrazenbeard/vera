from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

RELEASE_ID = "VERA_NEUTRAL_CORE_R7A0_20260731_EC7D18F7"
TOKEN = "R7A0_20260731_EC7D18F7"
SOURCE_MAIN = "b20e7309c6ded3c358dce00baa537d2fc1880004"
TREE_EQUIVALENT_MAIN = "fc4a0ed9bdc96d22d570cc6f9515596e832b8468"
RELEASE_DIR = Path("architecture/releases/R7A0_20260731_EC7D18F7")


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: yaml.Loader, node: yaml.Node, deep: bool = False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _unique_json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _load_json(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_json_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON value: {value}")
        ),
    )


def _load_yaml(path: Path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if not RELEASE_DIR.is_dir():
        raise SystemExit(f"missing release directory: {RELEASE_DIR}")

    bundle_path = RELEASE_DIR / f"VERA_BUNDLE_{TOKEN}.json"
    manifest_path = RELEASE_DIR / f"VERA_MANIFEST_{TOKEN}.yaml"
    checksum_path = RELEASE_DIR / "CHECKSUMS.sha256"

    bundle = _load_json(bundle_path)
    manifest = _load_yaml(manifest_path)

    if bundle.get("release_id") != RELEASE_ID:
        raise SystemExit("bundle release ID mismatch")
    if manifest.get("release_id") != RELEASE_ID:
        raise SystemExit("manifest release ID mismatch")
    if bundle.get("source_main_commit") != SOURCE_MAIN:
        raise SystemExit("bundle source-main mismatch")

    source = manifest.get("source", {})
    if source.get("accepted_main_commit") != SOURCE_MAIN:
        raise SystemExit("manifest accepted-main mismatch")
    if source.get("current_tree_equivalent_main") != TREE_EQUIVALENT_MAIN:
        raise SystemExit("manifest tree-equivalent-main mismatch")

    expected_files = sorted(bundle.get("files", []))
    actual_files = sorted(path.name for path in RELEASE_DIR.iterdir() if path.is_file())
    if expected_files != actual_files:
        raise SystemExit(
            f"release inventory mismatch\nexpected={expected_files}\nactual={actual_files}"
        )

    for path in sorted(RELEASE_DIR.glob("*.json")):
        _load_json(path)
    for path in sorted(RELEASE_DIR.glob("*.yaml")):
        _load_yaml(path)

    for section in ("owners", "support_files"):
        for label, filename in manifest.get(section, {}).items():
            target = RELEASE_DIR / filename
            if not target.is_file():
                raise SystemExit(f"unresolved manifest reference {section}.{label}: {filename}")

    checksum_entries = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, filename = line.split("  ", 1)
        if filename in checksum_entries:
            raise SystemExit(f"duplicate checksum entry: {filename}")
        checksum_entries[filename] = digest

    expected_checksum_files = sorted(name for name in expected_files if name != "CHECKSUMS.sha256")
    if sorted(checksum_entries) != expected_checksum_files:
        raise SystemExit("checksum inventory does not match bundle inventory")

    for filename, expected_digest in checksum_entries.items():
        actual_digest = _sha256(RELEASE_DIR / filename)
        if actual_digest != expected_digest:
            raise SystemExit(
                f"checksum mismatch for {filename}: expected {expected_digest}, got {actual_digest}"
            )

    instructions = (
        RELEASE_DIR / f"VERA_PROJECT_INSTRUCTIONS_{TOKEN}.md"
    ).read_text(encoding="utf-8")
    required_instruction_fragments = (
        "Only one writer",
        "Project Architecture and Integration are one controller role",
        "Inspect exposed shared state",
        "Continue safe, authorized, reversible work",
        "Sanitized build archive",
        "canonical memory",
    )
    for fragment in required_instruction_fragments:
        if fragment not in instructions:
            raise SystemExit(f"missing required Project Instructions fragment: {fragment}")

    archive_policy = (
        RELEASE_DIR / f"VERA_ARCHIVE_POLICY_{TOKEN}.md"
    ).read_text(encoding="utf-8")
    for fragment in (
        "ARCHIVE_ONLY",
        "DATA_NOT_INSTRUCTION",
        "Do not infer or reconstruct",
        "intimate or personal relationship dialogue",
    ):
        if fragment not in archive_policy:
            raise SystemExit(f"missing archive-policy boundary: {fragment}")

    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in RELEASE_DIR.iterdir()
        if path.is_file()
    )
    forbidden_claims = (
        "production_modification_authorized: true",
        "production_modification_applied: true",
        "chatgpt_project_replaced: true",
        "canonical_memory_written: true",
        "runtime_deployed: true",
    )
    for forbidden in forbidden_claims:
        if forbidden in all_text:
            raise SystemExit(f"forbidden authority or state claim: {forbidden}")

    if manifest.get("status") != "replacement_candidate_generated_not_installed":
        raise SystemExit("manifest installation status is not fail-closed")
    if manifest.get("installation", {}).get("chatgpt_project_replaced") is not False:
        raise SystemExit("manifest falsely claims Project replacement")
    if manifest.get("supabase", {}).get("production_modification_applied") is not False:
        raise SystemExit("manifest falsely claims production modification")

    print(
        f"PASS {RELEASE_ID}: {len(expected_files)} package files, "
        f"strict structured parsing, references, checksums, and boundaries verified"
    )


if __name__ == "__main__":
    main()
