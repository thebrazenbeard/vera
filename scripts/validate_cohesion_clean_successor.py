from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


SCHEMA = "VERA_COHESION_CLEAN_SUCCESSOR_V1"
REPOSITORY = "thebrazenbeard/vera"
DONOR_HEAD = "f7dbc3deeaaaeb46dcf7c7ea6b56a822f253232d"
DONOR_TREE = "1582cefd1c5f20946b197da2e4268e45b2ef501f"
DONOR_RUNTIME_GENERATION = "ba6221f56b98be69c3ede1be9e3502eff897ca1a"
DONOR_BINDING_BLOB = "037883261bd324e8080c323f1d96ff32179780ee"
INITIAL_FLATTENED_COMMIT = "0c110eb1cde73f22ccd419ff4a9ef1b1e1eddcf2"
INITIAL_FLATTENED_TREE = "97aff3209701f4380ddf0c4bcb7577fe0ca44b5e"
CONSTRUCTION_PARENT = "b0b4cac1cd187b32a6e9012ef98ab0d136e35e92"
FINAL_CLEAN_SOURCE_COMMIT = "54fef2659f0a8633dcef60cd36b296c37b6fa4b0"
FINAL_CLEAN_SOURCE_TREE = "e6fc7cf8e77c39af77f2ab1fc57426b57344695d"
FROZEN_SEXUALITY_COMMIT = "150f1c8231423393bb66b0e2cb759ce7c018f8d7"
FROZEN_SEXUALITY_PATH = "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json"
FROZEN_SEXUALITY_BLOB = "a48eed5392fdadc073dccd1e799926042077f567"
OWNERSHIP_PATH = "architecture/cohesion/VERA_COHESION_OWNERSHIP_CONTRACT_V0.json"
OWNERSHIP_BLOB = "d6fdab49ddb691480757445148ecb77c52674c83"
BINDING_PATH = "architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json"


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json_strict(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    if not isinstance(value, dict):
        raise ValueError("document must be a JSON object")
    return value


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise ValueError(f"{label} must be an exact Git SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc
    return value


def _blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _resolve(root: Path, commit: str, path: str) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", f"{commit}:{path}"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"clean source commit cannot resolve {path}") from exc


def _commit_meta(root: Path, commit: str) -> tuple[str, list[str]]:
    try:
        meta = subprocess.run(
            ["git", "show", "-s", "--format=%T %P", commit],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip().split()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"commit is not locally resolvable: {commit}") from exc
    if not meta:
        raise ValueError(f"commit metadata is empty: {commit}")
    return meta[0], meta[1:]


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ValueError("git ancestry check is unavailable") from exc
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise ValueError("git ancestry check failed")


def validate_clean_successor(
    record: dict[str, Any],
    *,
    ownership_path: str | Path,
    binding_path: str | Path,
    repository_root: str | Path,
) -> None:
    root = Path(repository_root).resolve()
    if record.get("schema") != SCHEMA or record.get("repository") != REPOSITORY:
        raise ValueError("unsupported clean successor record")
    if record.get("status") != "SOURCE_BOUND_FLATTENED_NOT_INSTALLED_NOT_QUALIFIED":
        raise ValueError("clean successor status mismatch")

    clean_commit = _sha(record.get("clean_source_commit"), "clean_source_commit")
    clean_tree = _sha(record.get("clean_source_tree"), "clean_source_tree")
    if clean_commit != FINAL_CLEAN_SOURCE_COMMIT or clean_tree != FINAL_CLEAN_SOURCE_TREE:
        raise ValueError("clean source does not match the frozen post-flatten repair generation")

    donor = record.get("donor")
    if not isinstance(donor, dict):
        raise ValueError("donor must be an object")
    if donor != {
        "head": DONOR_HEAD,
        "tree": DONOR_TREE,
        "runtime_generation": DONOR_RUNTIME_GENERATION,
        "binding_blob": DONOR_BINDING_BLOB,
        "ancestry_imported": False,
    }:
        raise ValueError("donor provenance mismatch")

    initial = record.get("initial_flattened_source")
    expected_initial = {
        "commit": INITIAL_FLATTENED_COMMIT,
        "tree": INITIAL_FLATTENED_TREE,
        "construction_parent": CONSTRUCTION_PARENT,
        "mode": "ONE_COMMIT_SINGLE_PARENT_POLICY_LINEAGE",
    }
    if initial != expected_initial:
        raise ValueError("initial flattened source binding mismatch")
    if record.get("flattening") != "DONOR_TREE_FLATTENED_THEN_CLEAN_SUCCESSOR_REPAIRED":
        raise ValueError("clean successor flattening mode mismatch")
    if INITIAL_FLATTENED_COMMIT == DONOR_HEAD:
        raise ValueError("initial flattened source cannot equal donor head")

    initial_tree, initial_parents = _commit_meta(root, INITIAL_FLATTENED_COMMIT)
    if initial_tree != INITIAL_FLATTENED_TREE or initial_parents != [CONSTRUCTION_PARENT]:
        raise ValueError("initial flattened source is not the declared single-parent donor materialization")
    final_tree, final_parents = _commit_meta(root, clean_commit)
    if final_tree != clean_tree or len(final_parents) != 1:
        raise ValueError("final clean source commit/tree lineage mismatch")
    if not _is_ancestor(root, INITIAL_FLATTENED_COMMIT, clean_commit):
        raise ValueError("final clean source does not descend from the initial flattened source")
    if _is_ancestor(root, DONOR_HEAD, clean_commit):
        raise ValueError("donor ancestry was imported into the clean successor")

    frozen = record.get("frozen_sexuality_object")
    if frozen != {
        "repository": "thebrazenbeard/sexuality",
        "commit": FROZEN_SEXUALITY_COMMIT,
        "path": FROZEN_SEXUALITY_PATH,
        "blob": FROZEN_SEXUALITY_BLOB,
    }:
        raise ValueError("frozen sexuality object mismatch")

    ownership = Path(ownership_path)
    if _blob_sha(ownership.read_bytes()) != OWNERSHIP_BLOB:
        raise ValueError("ownership contract blob mismatch")
    declared_ownership = record.get("ownership_contract")
    if declared_ownership != {"path": OWNERSHIP_PATH, "blob": OWNERSHIP_BLOB}:
        raise ValueError("ownership contract binding mismatch")

    declared_runtime_binding = record.get("runtime_binding")
    if declared_runtime_binding != {
        "path": BINDING_PATH,
        "required_cut_commit": clean_commit,
        "binding_head_is_post_source_metadata": True,
    }:
        raise ValueError("runtime binding declaration mismatch")

    binding = load_json_strict(binding_path)
    runtime_cut = binding.get("runtime_implementation_cut")
    integration_cut = binding.get("cohesion_integration_cut")
    cross = binding.get("cross_binding")
    if not isinstance(runtime_cut, dict) or not isinstance(integration_cut, dict) or not isinstance(cross, dict):
        raise ValueError("runtime binding structure is incomplete")
    if runtime_cut.get("commit") != clean_commit or integration_cut.get("commit") != clean_commit or cross.get("generation_commit") != clean_commit:
        raise ValueError("runtime binding is not rebound to the clean source commit")
    for cut in (runtime_cut, integration_cut):
        modules = cut.get("modules")
        if not isinstance(modules, dict) or not modules:
            raise ValueError("runtime binding cut has no modules")
        for path, expected_blob in modules.items():
            _sha(expected_blob, f"blob for {path}")
            if _resolve(root, clean_commit, path) != expected_blob:
                raise ValueError(f"clean source commit resolves a different runtime blob: {path}")

    ceiling = record.get("claim_ceiling")
    expected_ceiling = {
        "source": "SOURCE_BOUND",
        "installation": "NOT_ESTABLISHED",
        "current_route": "NOT_ESTABLISHED",
        "provider_currentness": "NOT_ESTABLISHED",
        "production_atomic_durability": "NOT_QUALIFIED",
        "behavioral_qualification": "NOT_ESTABLISHED",
        "phenomenology": "UNRESOLVED",
    }
    if ceiling != expected_ceiling:
        if isinstance(ceiling, dict) and ceiling.get("phenomenology") != "UNRESOLVED":
            raise ValueError("phenomenology must remain unresolved")
        raise ValueError("claim ceiling mismatch")

    forbidden = set(record.get("protected_effects_not_authorized") or [])
    required = {
        "MERGE", "INSTALL_OR_CUTOVER", "PRODUCTION_PROVIDER_MUTATION",
        "PAID_CI_OR_OTHER_SPEND", "CANONICAL_MEMORY_PROMOTION",
        "BEHAVIORAL_QUALIFICATION", "AUTHORITY_PROMOTION", "PHENOMENOLOGY_PROMOTION",
    }
    if not required.issubset(forbidden):
        raise ValueError("protected effect ceiling is incomplete")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    validate_clean_successor(
        load_json_strict(root / "architecture/cohesion/VERA_COHESION_CLEAN_SUCCESSOR_V1.json"),
        ownership_path=root / OWNERSHIP_PATH,
        binding_path=root / BINDING_PATH,
        repository_root=root,
    )
    print("VERA_COHESION_CLEAN_SUCCESSOR_V1: SOURCE VALIDATION PASSED")
