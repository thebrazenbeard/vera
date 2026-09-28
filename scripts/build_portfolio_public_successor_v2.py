from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "architecture" / "portfolio" / "vendor" / "project-runner" / "PROJECT_RUNNER_PORTFOLIO_CORPUS_V1_20260924.json"
PORTFOLIO = ROOT / "architecture" / "portfolio"
PREDECESSOR = "078d2d7242384c58676305d47654406713e599cf"
CORPUS_SOURCE_COMMIT = "848c2172e6fa98cdab722b43d1ff4817990c5968"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def git_show_json(path: str):
    raw = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", f"{PREDECESSOR}:{path}"],
        text=True,
        encoding="utf-8",
    )
    return json.loads(raw)

def git_blob_sha(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", f"--path={relative}", str(path)],
        text=True,
        encoding="utf-8",
    ).strip()

def canonical_sha256(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def live_head(repository: str, branch: str) -> str:
    url = f"https://github.com/{repository}.git"
    raw = subprocess.check_output(
        ["git", "ls-remote", url, f"refs/heads/{branch}"],
        text=True,
        encoding="utf-8",
        timeout=30,
    ).strip()
    if not raw:
        raise RuntimeError(f"missing live ref for {repository}:{branch}")
    return raw.split()[0]

def write_json(name: str, value) -> None:
    (PORTFOLIO / name).write_text(
        json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

corpus = load_json(CORPUS)
counts = corpus["counts"]
assert counts["total"] == 67
assert counts["public"] == 49
assert counts["private"] == 18
assert corpus["private_inventory"]["public_commitment_scheme"] == "COUNT_ONLY_PUBLIC_V1"
assert corpus["private_inventory"]["exact_membership_publicly_committed"] is False
records = corpus["records"]
assert len(records) == 49
assert all(row["visibility"] == "public" for row in records)

old_abs = git_show_json("architecture/portfolio/VERA_PORTFOLIO_ABSORPTION_V1.json")
old_cap = git_show_json("architecture/portfolio/VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V1.json")
old_harvest = git_show_json("architecture/portfolio/VERA_PORTFOLIO_HARVEST_V1.json")
old_bindings = git_show_json("architecture/portfolio/VERA_PORTFOLIO_MIGRATION_BINDINGS_V1.json")

old_modules = {row["source_repository"]: row for row in old_abs["modules"]}
old_cap_modules = {row["source_repository"]: row for row in old_cap["modules"]}
old_harvest_rows = {row["source_repository"]: row for row in old_harvest["repositories"]}
public_repositories = {row["repository"] for row in records}

heads = {}
for row in records:
    heads[row["repository"]] = live_head(row["repository"], row["default_branch"])

head_rows = [
    {
        "repository": row["repository"],
        "default_branch": row["default_branch"],
        "observed_head": heads[row["repository"]],
    }
    for row in records
]
existing_cut_path = PORTFOLIO / "VERA_PORTFOLIO_PUBLIC_CUT_V2.json"
existing_refresh = None
if existing_cut_path.is_file():
    existing_cut = load_json(existing_cut_path)
    candidate = existing_cut.get("public_head_refresh")
    if isinstance(candidate, dict) and candidate.get("heads") == head_rows:
        existing_refresh = candidate
observed_at = (
    existing_refresh["observed_at"]
    if existing_refresh is not None
    else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
)

cut = {
    "schema": "VERA_PORTFOLIO_PUBLIC_CUT_V2",
    "status": "IMMUTABLE_OBSERVED_CUT_NOT_STANDING_CURRENTNESS",
    "owner_repository": "thebrazenbeard/vera",
    "source_corpus": {
        "repository": "thebrazenbeard/project-runner",
        "commit": CORPUS_SOURCE_COMMIT,
        "path": "portfolio/corpus.public.json",
        "git_blob": git_blob_sha(CORPUS),
        "corpus_id": corpus["corpus_id"],
        "observed_at": corpus["observed_at"],
    },
    "cut_counts": counts,
    "private_inventory": corpus["private_inventory"],
    "freshness_rule": corpus["freshness_rule"],
    "public_records": records,
    "public_head_refresh": {
        "observed_at": observed_at,
        "semantics": "MUTABLE_HEAD_REFRESH_SEPARATE_FROM_IMMUTABLE_MEMBERSHIP_CUT",
        "heads": head_rows,
    },
}
immutable_cut = {
    key: value
    for key, value in cut.items()
    if key not in {"public_head_refresh", "cut_sha256"}
}
cut["cut_sha256"] = canonical_sha256(immutable_cut)
write_json("VERA_PORTFOLIO_PUBLIC_CUT_V2.json", cut)

new_defaults = {
    "thebrazenbeard/fuckup": (
        "FAILURE_RECOVERY_PROTOCOL_SOURCE",
        "NO_AUTO_BIND",
        ["ASSURANCE_REPAIR_AND_SECURITY", "CONTROL_AND_GOVERNANCE"],
    ),
    "thebrazenbeard/sql-connectome": (
        "COGNITIVE_DATABASE_RESEARCH_SOURCE",
        "NO_AUTO_BIND",
        ["COGNITION_REASONING_AND_LEARNING", "CONTEXT_MEMORY_AND_PROVENANCE"],
    ),
    "thebrazenbeard/vera-mono": (
        "VERA_MONO_RUNTIME_SOURCE",
        "NO_AUTO_BIND",
        ["RUNTIME_IO_AND_ENVIRONMENT", "COORDINATION_AND_EXECUTION", "ASSURANCE_REPAIR_AND_SECURITY"],
    ),
}

modules = []
cap_modules = []
for row in records:
    repo = row["repository"]
    old = old_modules.get(repo)
    if old is not None:
        source_role = old["source_role"]
        activation = old["source_activation_mode"]
        ceiling = old["source_authority_ceiling"]
        privacy_class = old.get("source_privacy_class", "PUBLIC")
    else:
        source_role, activation, _planes = new_defaults[repo]
        ceiling = "Public portfolio source/provenance only; presence transfers no identity, memory, authority, installation, runtime, or effect status."
        privacy_class = "PUBLIC"
    module_id = "VERA_PORTFOLIO_PUBLIC_MODULE__" + row["id"].upper().replace("-", "_")
    modules.append({
        "module_id": module_id,
        "source_repository": repo,
        "source_visibility": "public",
        "source_default_branch": row["default_branch"],
        "source_archived_at_cut": row["archived"],
        "source_cut_record_id": row["id"],
        "source_cut_priority": row["priority"],
        "source_cut_family_id": row["family_id"],
        "source_evidence_commit": heads[repo],
        "source_evidence_semantics": "HEAD_REFRESH_AFTER_IMMUTABLE_PORTFOLIO_CUT_NOT_STANDING_AUTHORITY",
        "source_role": source_role,
        "source_activation_mode": activation,
        "source_authority_ceiling": ceiling,
        "source_privacy_class": privacy_class,
        "absorption_mode": "VERA_INTERNAL_ARCHITECTURE_MODULE",
        "internal_owner_repository": "thebrazenbeard/vera",
        "internal_semantics": "Vera owns only the integrated architectural interpretation, interfaces, guards, and reusable mechanisms; source identity/state/authority does not transfer.",
        "runtime_dependency_rule": "NO_RUNTIME_DEPENDENCY_BY_PRESENCE",
        "currentness_rule": "Refresh mutable source evidence when material; the 67-repository cut is immutable provenance, not a permanent estate cardinality.",
    })
    old_cap_row = old_cap_modules.get(repo)
    if old_cap_row is not None:
        planes = list(old_cap_row["capability_planes"])
    else:
        planes = list(new_defaults[repo][2])
    cap_modules.append({
        "module_id": module_id,
        "source_repository": repo,
        "capability_planes": planes,
    })

absorption = {
    "schema": "VERA_PORTFOLIO_ABSORPTION_V2",
    "status": "SOURCE_INTEGRATION_CANDIDATE_NOT_MERGED_NOT_INSTALLED",
    "owner_repository": "thebrazenbeard/vera",
    "predecessor": {
        "pull_request": 200,
        "head": PREDECESSOR,
        "disposition": "SUPERSEDED_BY_PUBLIC_SAFE_IMMUTABLE_CUT_MODEL",
    },
    "portfolio_cut": {
        "artifact": "architecture/portfolio/VERA_PORTFOLIO_PUBLIC_CUT_V2.json",
        "total_at_cut": 67,
        "public_modules": 49,
        "private_membership": {
            "count_at_cut": 18,
            "public_commitment_scheme": "COUNT_ONLY_PUBLIC_V1",
            "exact_membership_publicly_committed": False,
        },
    },
    "cardinality_semantics": "Counts describe one immutable observed cut only. They are never permanent assertions about the later portfolio estate.",
    "freshness_semantics": "Refresh live repository/provider/runtime evidence before any currentness-sensitive decision or effect claim.",
    "protected_effect_rule": "Source architecture work only; no merge, deploy, install, provider mutation, permission change, private publication, memory promotion, or runtime-effect claim.",
    "modules": modules,
}
write_json("VERA_PORTFOLIO_ABSORPTION_V2.json", absorption)

plane_templates = old_cap["planes"]
planes = {}
for plane_name, template in plane_templates.items():
    if plane_name == "UNRESOLVED_EMPTY_REPOSITORY":
        template = dict(template)
    planes[plane_name] = {
        **{k: v for k, v in template.items() if k != "module_ids"},
        "module_ids": sorted(
            row["module_id"]
            for row in cap_modules
            if plane_name in row["capability_planes"]
        ),
    }
capability = {
    "schema": "VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V2",
    "status": "PUBLIC_SAFE_CAPABILITY_MAPPING_FOR_IMMUTABLE_CUT",
    "portfolio_cut_artifact": "architecture/portfolio/VERA_PORTFOLIO_PUBLIC_CUT_V2.json",
    "public_module_count": 49,
    "private_membership_count_at_cut": 18,
    "private_membership_publicly_enumerated": False,
    "freshness_rule": "Capability membership is bound to the immutable cut; later repository movement requires a newer cut, not mutation of this record.",
    "planes": planes,
    "modules": cap_modules,
}
write_json("VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V2.json", capability)

harvest_rows = []
for row in records:
    repo = row["repository"]
    old = old_harvest_rows.get(repo)
    if old is not None:
        item = {k: v for k, v in old.items() if k not in {"source_visibility"}}
        item["source_visibility"] = "public"
        item["source_evidence_commit"] = heads[repo]
        item["currentness_rule"] = "Harvest disposition is bound to this cut/head refresh; re-inspect when material."
    else:
        item = {
            "source_repository": repo,
            "source_visibility": "public",
            "source_evidence_commit": heads[repo],
            "harvest_status": "INSPECTED_PUBLIC_CUT_SOURCE",
            "decision": row["current_frontier"],
            "inspected_surface": [
                "Project Runner public portfolio corpus",
                "current default-branch head refresh",
            ],
            "effect_ceiling": "SOURCE_ARCHITECTURE_ONLY",
            "vera_targets": [],
            "currentness_rule": "No automatic bind; inspect exact source before mechanism migration.",
        }
    harvest_rows.append(item)

harvest = {
    "schema": "VERA_PORTFOLIO_HARVEST_V2",
    "status": "PUBLIC_SAFE_HARVEST_SUCCESSOR",
    "predecessor_pr": 200,
    "predecessor_head": PREDECESSOR,
    "portfolio_cut_artifact": "architecture/portfolio/VERA_PORTFOLIO_PUBLIC_CUT_V2.json",
    "public_repository_count_at_cut": 49,
    "private_repository_count_at_cut": 18,
    "private_membership_publicly_enumerated": False,
    "cardinality_semantics": "Observed-cut counts only; no timeless cardinality assertion.",
    "repositories": harvest_rows,
}
write_json("VERA_PORTFOLIO_HARVEST_V2.json", harvest)

public_bindings = [
    row for row in old_bindings["bindings"]
    if (
        row["source_repository"] in public_repositories
        and (ROOT / row["target_path"]).is_file()
    )
]
deferred_public_bindings = []
for row in old_bindings["bindings"]:
    if (
        row["source_repository"] in public_repositories
        and not (ROOT / row["target_path"]).is_file()
    ):
        deferred_public_bindings.append({
            "source_repository": row["source_repository"],
            "source_commit": row["source_commit"],
            "source_path": row["source_path"],
            "source_blob": row["source_blob"],
            "predecessor_target_path": row["target_path"],
            "predecessor_target_blob": row["target_blob"],
            "predecessor_transfer_kind": row["transfer_kind"],
            "predecessor_verified_blob_equal": row["verified_blob_equal"],
            "disposition": "DEFERRED_TO_SEPARATE_VCP_NO_AUTO_BIND_RESTACK",
            "current_successor_target_present": False,
            "activation_effect": False,
            "rule": "Historical public provenance is retained, but the stale embedded target is not copied into this successor. Rebind only through the separately reviewed VCP NO_AUTO_BIND restack.",
        })
private_targets = []
for namespace in ("portfolio_runtime/evidence_runtime", "portfolio_runtime/work_state_runtime"):
    root = ROOT / namespace
    paths = []
    for target in sorted(
        p for p in root.rglob("*")
        if (
            p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix in {".py", ".json"}
        )
    ):
        paths.append({
            "target_path": target.relative_to(ROOT).as_posix(),
            "target_blob": git_blob_sha(target),
        })
    private_targets.append({
        "vera_owned_namespace": namespace,
        "target_files": paths,
    })

bindings = {
    "schema": "VERA_PORTFOLIO_MIGRATION_BINDINGS_V2",
    "status": "PUBLIC_SAFE_PROVENANCE_BINDINGS",
    "predecessor_pr": 200,
    "predecessor_head": PREDECESSOR,
    "public_exact_bindings": public_bindings,
    "public_exact_binding_count": len(public_bindings),
    "deferred_public_binding_provenance": deferred_public_bindings,
    "deferred_public_binding_count": len(deferred_public_bindings),
    "public_predecessor_binding_conservation": {
        "predecessor_public_binding_count": len(public_bindings) + len(deferred_public_bindings),
        "active_exact_binding_count": len(public_bindings),
        "deferred_provenance_count": len(deferred_public_bindings),
        "rule": "Every public predecessor binding is either retained as an exact present target or carried as explicit deferred provenance for a separately governed restack.",
    },
    "private_donor_mechanism_provenance": {
        "donor_repository_count": 2,
        "membership_publicly_committed": False,
        "rule": "Exact private donor membership/source paths remain outside public source. Vera-owned mechanism bytes are integrity-bound only by target blob in this public artifact.",
        "mechanism_sets": private_targets,
    },
    "derived_integrations": [{
        "source_repository": "thebrazenbeard/discovery",
        "transfer_kind": "DERIVED_ARCHITECTURE",
        "target_paths": [
            "architecture/portfolio/VERA_PORTFOLIO_PUBLIC_CUT_V2.json",
            "architecture/portfolio/VERA_PORTFOLIO_ABSORPTION_V2.json",
            "architecture/portfolio/VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V2.json",
            "architecture/portfolio/VERA_PORTFOLIO_HARVEST_V2.json",
        ],
        "rule": "Discovery-style open-world intake is adapted into Vera architecture; these targets are not represented as byte-identical donor copies.",
    }],
    "claim_ceiling": "Source-byte/mechanism provenance only. No donor supersession, private membership disclosure, runtime activation, installation, authority, memory admission, or qualification.",
}
write_json("VERA_PORTFOLIO_MIGRATION_BINDINGS_V2.json", bindings)

manifest = {
    "schema": "VERA_SYSTEM_MANIFEST_V3",
    "status": "SOURCE_NAVIGATION_SUCCESSOR_NOT_INSTALLATION_PROOF",
    "owner_repository": "thebrazenbeard/vera",
    "portfolio": {
        "cut": "architecture/portfolio/VERA_PORTFOLIO_PUBLIC_CUT_V2.json",
        "absorption": "architecture/portfolio/VERA_PORTFOLIO_ABSORPTION_V2.json",
        "capabilities": "architecture/portfolio/VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V2.json",
        "harvest": "architecture/portfolio/VERA_PORTFOLIO_HARVEST_V2.json",
        "migration_bindings": "architecture/portfolio/VERA_PORTFOLIO_MIGRATION_BINDINGS_V2.json",
        "cut_counts": {"total": 67, "public": 49, "private": 18},
        "private_membership_publicly_enumerated": False,
        "cardinality_semantics": "IMMUTABLE_OBSERVED_CUT_ONLY",
        "freshness_semantics": "LIVE_MUTABLE_EVIDENCE_MUST_BE_REFRESHED_WHEN_MATERIAL",
    },
    "control_plane": {
        "source_repository": "thebrazenbeard/vera-control-plane",
        "activation_mode": "NO_AUTO_BIND_PENDING_SEPARATE_VCP_RESTACK",
        "embedded_mirror": False,
    },
    "mechanism_namespaces": [
        "portfolio_runtime/attune",
        "portfolio_runtime/intranel",
        "portfolio_runtime/lantern",
        "portfolio_runtime/roots",
        "portfolio_runtime/evidence_runtime",
        "portfolio_runtime/work_state_runtime",
    ],
    "effect_ceiling": "SOURCE_ONLY_NOT_MERGED_NOT_INSTALLED_NOT_RUNTIME_PROOF",
}
(ROOT / "architecture" / "VERA_SYSTEM_MANIFEST_V3.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps({
    "cut_sha256": cut["cut_sha256"],
    "public_modules": len(modules),
    "harvest_rows": len(harvest_rows),
    "public_exact_bindings": len(public_bindings),
    "deferred_public_bindings": len(deferred_public_bindings),
    "head_refresh_observed_at": observed_at,
}, indent=2))
