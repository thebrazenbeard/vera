from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


SCHEMA = "VERA_COHESION_CLEAN_SUCCESSOR_V1"
REPOSITORY = "thebrazenbeard/vera"
R2_CLEAN_SOURCE_COMMIT = "349de790a583bb2fbe7ad8e3f4663854f9d98e50"
R2_CLEAN_SOURCE_TREE = "8754e26d2a7428a37e0ac0ff00992343869b417c"
R2_CONSTRUCTION_PARENT = "b0b4cac1cd187b32a6e9012ef98ab0d136e35e92"
R1_CLEAN_SOURCE_COMMIT = "0c110eb1cde73f22ccd419ff4a9ef1b1e1eddcf2"
R1_REVIEW_HEAD = "75bcdae943bb6034d4be8899aba163550a8f39bd"
RUNTIME_IMPLEMENTATION_CUT = "54fef2659f0a8633dcef60cd36b296c37b6fa4b0"
DONOR_HEAD = "f7dbc3deeaaaeb46dcf7c7ea6b56a822f253232d"
DONOR_TREE = "1582cefd1c5f20946b197da2e4268e45b2ef501f"
DONOR_RUNTIME_GENERATION = "ba6221f56b98be69c3ede1be9e3502eff897ca1a"
DONOR_BINDING_BLOB = "037883261bd324e8080c323f1d96ff32179780ee"
FROZEN_SEXUALITY_COMMIT = "150f1c8231423393bb66b0e2cb759ce7c018f8d7"
FROZEN_SEXUALITY_PATH = "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json"
FROZEN_SEXUALITY_BLOB = "a48eed5392fdadc073dccd1e799926042077f567"
OWNERSHIP_PATH = "architecture/cohesion/VERA_COHESION_OWNERSHIP_CONTRACT_V0.json"
OWNERSHIP_BLOB = "d6fdab49ddb691480757445148ecb77c52674c83"
BINDING_PATH = "architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json"
SOURCE_REGISTRY_PATH = "architecture/cohesion/VERA_COHESION_SOURCE_REGISTRY_V0_20260911.json"
R3_SOURCE_HEAD = "810d778e6a53d0bd5cc74bba17538d0f508f9644"


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


def _resolve(root: Path, commit: str, path: str, label: str) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", f"{commit}:{path}"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"{label} cannot resolve {path}") from exc


def _require_ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"{label} is not ancestry-bound to the candidate") from exc


def _validate_bound_modules(
    *,
    root: Path,
    clean_commit: str,
    cut: dict[str, Any],
    cut_commit: str,
    label: str,
) -> None:
    modules = cut.get("modules")
    if not isinstance(modules, dict) or not modules:
        raise ValueError(f"{label} has no modules")
    for path, expected_blob in modules.items():
        _sha(expected_blob, f"blob for {path}")
        at_cut = _resolve(root, cut_commit, path, label)
        at_clean = _resolve(root, clean_commit, path, "clean source commit")
        if at_cut != expected_blob:
            raise ValueError(f"{label} resolves a different runtime blob: {path}")
        if at_clean != expected_blob:
            raise ValueError(
                "clean R2 source is not byte-equivalent to the bound runtime cut: "
                f"{path}"
            )


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
    construction_parent = _sha(record.get("construction_parent"), "construction_parent")
    if (
        clean_commit != R2_CLEAN_SOURCE_COMMIT
        or clean_tree != R2_CLEAN_SOURCE_TREE
        or construction_parent != R2_CONSTRUCTION_PARENT
    ):
        raise ValueError("clean successor must bind the exact R2 source tuple")

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
    if clean_commit == donor["head"] or record.get("flattening") != "ONE_COMMIT_SINGLE_PARENT_POLICY_LINEAGE":
        raise ValueError("flattened clean source must be distinct from donor ancestry")

    r1 = record.get("r1_predecessor")
    if not isinstance(r1, dict):
        raise ValueError("r1_predecessor must be an object")
    if (
        r1.get("clean_source_commit") != R1_CLEAN_SOURCE_COMMIT
        or r1.get("review_head") != R1_REVIEW_HEAD
        or r1.get("status") != "SUPERSEDED_AFTER_STATIC_BLOCKERS"
    ):
        raise ValueError("R1 predecessor provenance mismatch")

    repair_input = record.get("repair_input")
    if not isinstance(repair_input, dict):
        raise ValueError("repair_input must be an object")
    if (
        repair_input.get("runtime_generation") != RUNTIME_IMPLEMENTATION_CUT
        or repair_input.get("history_imported") is not False
    ):
        raise ValueError("R2 repair-input provenance mismatch")

    try:
        meta = subprocess.run(
            ["git", "show", "-s", "--format=%T %P", clean_commit],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip().split()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("clean source commit is not locally resolvable") from exc
    if len(meta) != 2 or meta[0] != clean_tree or meta[1] != construction_parent:
        raise ValueError("clean source commit is not the declared single-parent flattened commit")

    current_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _require_ancestor(root, clean_commit, current_head, "clean R2 source")

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

    declared_binding = record.get("runtime_binding")
    if not isinstance(declared_binding, dict):
        raise ValueError("runtime_binding must be an object")
    if declared_binding.get("path") != BINDING_PATH:
        raise ValueError("runtime binding path mismatch")
    if declared_binding.get("clean_source_commit") != clean_commit:
        raise ValueError("runtime binding clean-source provenance mismatch")
    if declared_binding.get("runtime_implementation_cut_commit") != RUNTIME_IMPLEMENTATION_CUT:
        raise ValueError("runtime implementation cut mismatch")
    if declared_binding.get("cohesion_integration_cut_commit") != RUNTIME_IMPLEMENTATION_CUT:
        raise ValueError("cohesion integration cut mismatch")
    if declared_binding.get("generation_commit") != RUNTIME_IMPLEMENTATION_CUT:
        raise ValueError("cross-binding generation mismatch")
    if declared_binding.get("bound_module_byte_equivalence_required") is not True:
        raise ValueError("runtime binding must require bound-module byte equivalence")

    binding = load_json_strict(binding_path)
    runtime_cut = binding.get("runtime_implementation_cut")
    integration_cut = binding.get("cohesion_integration_cut")
    cross = binding.get("cross_binding")
    if not isinstance(runtime_cut, dict) or not isinstance(integration_cut, dict) or not isinstance(cross, dict):
        raise ValueError("runtime binding structure is incomplete")

    runtime_commit = _sha(runtime_cut.get("commit"), "runtime implementation cut")
    integration_commit = _sha(integration_cut.get("commit"), "cohesion integration cut")
    generation_commit = _sha(cross.get("generation_commit"), "cross-binding generation")
    if runtime_commit != declared_binding["runtime_implementation_cut_commit"]:
        raise ValueError("runtime binding file does not match declared implementation cut")
    if integration_commit != declared_binding["cohesion_integration_cut_commit"]:
        raise ValueError("runtime binding file does not match declared integration cut")
    if generation_commit != declared_binding["generation_commit"]:
        raise ValueError("runtime binding file does not match declared generation")

    _validate_bound_modules(
        root=root,
        clean_commit=clean_commit,
        cut=runtime_cut,
        cut_commit=runtime_commit,
        label="runtime implementation cut",
    )
    _validate_bound_modules(
        root=root,
        clean_commit=clean_commit,
        cut=integration_cut,
        cut_commit=integration_commit,
        label="cohesion integration cut",
    )

    source_registry = record.get("source_registry")
    if not isinstance(source_registry, dict):
        raise ValueError("source_registry must be an object")
    if source_registry.get("path") != SOURCE_REGISTRY_PATH:
        raise ValueError("source registry path mismatch")
    if source_registry.get("role") != "CURRENT_NON_NORMATIVE_EVIDENCE_REGISTRY":
        raise ValueError("source registry role mismatch")
    required_registry_entries = {
        "vera-ov-cv-pr113",
        "vera-clean-successor-repair-generation",
        "orgasm-qualification-subject",
    }
    if set(source_registry.get("required_entries") or []) != required_registry_entries:
        raise ValueError("source registry required-entry binding mismatch")

    successor = record.get("downstream_successor")
    if not isinstance(successor, dict):
        raise ValueError("downstream_successor must be an object")
    if (
        successor.get("generation") != "R3_INFERENCE_BOUNDARY"
        or successor.get("material_source_head") != R3_SOURCE_HEAD
        or successor.get("predecessor_clean_r2_source") != clean_commit
        or successor.get("current_main_contains_successor") is not True
    ):
        raise ValueError("R3 downstream-successor binding mismatch")
    _require_ancestor(root, R3_SOURCE_HEAD, current_head, "R3 inference-boundary source")

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
