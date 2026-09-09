#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json"
CONTRACT_PATH = ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json"
FABRIC_PATH = ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json"
RECEIPT_PATH = ROOT / "architecture" / "VERA_COHESION_PAIR_RECEIPT_V1.json"
EVENT_SELECTOR_TOKENS = {"$source_ref", "$source_path", "$source_revision"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def validate_operational_support_bindings(root: Path, receipt: Mapping[str, Any]) -> list[str]:
    """Mechanically bind every path/blob pair claimed by receipt operational support.

    Operational support is non-normative, but an exact blob claim is still an
    exact claim. Validation therefore proves the repository-local file exists and
    hashes to the named Git blob. Extra metadata such as status/semantic ceilings
    remains descriptive and does not become authority through this check.
    """

    errors: list[str] = []
    support = receipt.get("operational_support")
    if not isinstance(support, Mapping):
        return ["pair receipt operational support mapping is required"]
    if support.get("normative_status") != "NON_NORMATIVE_OPERATIONAL_SUPPORT":
        errors.append("pair receipt operational support must remain NON_NORMATIVE_OPERATIONAL_SUPPORT")

    root_resolved = root.resolve()
    rows = [(name, row) for name, row in support.items() if name != "normative_status"]
    if not rows:
        errors.append("pair receipt operational support requires at least one bound support object")
        return errors

    for name, row in rows:
        if not isinstance(name, str) or not name:
            errors.append("operational support entry requires a non-empty name")
            continue
        if not isinstance(row, Mapping):
            errors.append(f"operational support {name!r} must be an object")
            continue

        relative_path = row.get("path")
        blob_sha = row.get("blob_sha")
        if not isinstance(relative_path, str) or not relative_path.strip():
            errors.append(f"operational support {name!r} requires non-empty path")
            continue
        if not isinstance(blob_sha, str) or len(blob_sha) != 40 or any(char not in "0123456789abcdef" for char in blob_sha):
            errors.append(f"operational support {name!r} requires exact lowercase Git blob SHA")
            continue

        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError:
            errors.append(f"operational support {name!r} path escapes repository root: {relative_path!r}")
            continue
        if not candidate.is_file():
            errors.append(f"operational support {name!r} path does not resolve to a repository file: {relative_path!r}")
            continue

        observed_blob = _git_blob_sha(candidate)
        if observed_blob != blob_sha:
            errors.append(
                f"operational support {name!r} blob mismatch: receipt={blob_sha} observed={observed_blob} path={relative_path}"
            )

    return errors


def _validate_dependency_semantics(index: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    domain_rows = index.get("domains")
    if not isinstance(domain_rows, list) or not domain_rows:
        return ["cohesion index requires domains before dependency_semantics can be validated"]

    domain_ids: set[str] = set()
    dependencies_by_domain: dict[str, list[str]] = {}
    for row in domain_rows:
        if not isinstance(row, Mapping):
            errors.append("cohesion index domain rows must be mappings")
            continue
        domain_id = row.get("id")
        if not isinstance(domain_id, str) or not domain_id:
            errors.append("cohesion index domain requires id")
            continue
        if domain_id in domain_ids:
            errors.append(f"duplicate cohesion domain id {domain_id!r}")
            continue
        domain_ids.add(domain_id)
        declared = row.get("dependencies", [])
        if not isinstance(declared, list) or any(not isinstance(dep, str) or not dep for dep in declared):
            errors.append(f"domain {domain_id!r} dependencies must be a list of non-empty domain ids")
            dependencies_by_domain[domain_id] = []
        else:
            dependencies_by_domain[domain_id] = list(declared)

    for domain_id, dependencies in dependencies_by_domain.items():
        for dependency in dependencies:
            if dependency not in domain_ids:
                errors.append(f"domain {domain_id!r} references unknown dependency {dependency!r}")

    semantics = index.get("dependency_semantics")
    if not isinstance(semantics, Mapping):
        errors.append("cohesion index dependency_semantics mapping is required")
        return errors

    for field in ("classification_rule", "hard_prerequisite_rule", "contextual_dependency_rule"):
        value = semantics.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"dependency_semantics requires non-empty {field}")

    hard_raw = semantics.get("hard_prerequisite_domains")
    if not isinstance(hard_raw, list) or not hard_raw or any(not isinstance(value, str) or not value for value in hard_raw):
        errors.append("dependency_semantics.hard_prerequisite_domains must be a non-empty list of domain ids")
        return errors
    if len(hard_raw) != len(set(hard_raw)):
        errors.append("dependency_semantics.hard_prerequisite_domains contains duplicates")
    hard_domains = set(hard_raw)

    for hard_domain in sorted(hard_domains):
        if hard_domain not in domain_ids:
            errors.append(f"dependency_semantics references unknown hard prerequisite domain {hard_domain!r}")

    incoming_targets = {
        dependency
        for dependencies in dependencies_by_domain.values()
        for dependency in dependencies
    }
    for hard_domain in sorted(hard_domains.intersection(domain_ids)):
        if hard_domain not in incoming_targets:
            errors.append(
                f"hard prerequisite domain {hard_domain!r} has no declared incoming dependency edge and cannot govern any dependent domain"
            )

    hard_graph: dict[str, list[str]] = {
        domain_id: [dependency for dependency in dependencies if dependency in hard_domains]
        for domain_id, dependencies in dependencies_by_domain.items()
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(domain_id: str, path: tuple[str, ...]) -> None:
        if domain_id in visited:
            return
        if domain_id in visiting:
            cycle_start = path.index(domain_id) if domain_id in path else 0
            cycle = path[cycle_start:] + (domain_id,)
            errors.append("hard prerequisite dependency cycle: " + " -> ".join(cycle))
            return
        visiting.add(domain_id)
        next_path = path + (domain_id,)
        for dependency in hard_graph.get(domain_id, []):
            if dependency in domain_ids:
                visit(dependency, next_path)
        visiting.remove(domain_id)
        visited.add(domain_id)

    for domain_id in sorted(domain_ids):
        if domain_id not in visited:
            visit(domain_id, ())

    return errors


def validate_provider_fabric(
    index: Mapping[str, Any],
    contract: Mapping[str, Any],
    fabric: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []

    if fabric.get("schema") != "VERA_PROVIDER_FABRIC_V1":
        errors.append("fabric schema must be VERA_PROVIDER_FABRIC_V1")
    if fabric.get("normative_status") != "NON_NORMATIVE_OPERATIONAL_SUPPORT":
        errors.append("provider fabric must be NON_NORMATIVE_OPERATIONAL_SUPPORT")
    if set(fabric.get("normative_pair_refs", [])) != {
        "VERA_COHESION_INDEX_V1",
        "VERA_RUNTIME_CONTRACT_V1",
    }:
        errors.append("provider fabric normative_pair_refs must point only to the A+B schemas")

    errors.extend(_validate_dependency_semantics(index))

    evidence_classes = set(contract.get("evidence_classes", {}))
    privacy_classes = set(contract.get("privacy_classes", []))
    route_ids = {
        row.get("id")
        for row in index.get("route_declarations", [])
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    }
    providers = fabric.get("providers")
    if not isinstance(providers, Mapping) or not providers:
        errors.append("provider fabric requires a non-empty providers map")
        providers = {}

    for provider_id, provider in providers.items():
        if not isinstance(provider, Mapping):
            errors.append(f"provider {provider_id!r} must be an object")
            continue
        if not provider.get("promotion_guard"):
            errors.append(f"provider {provider_id!r} requires promotion_guard")
        capabilities = provider.get("evidence_capability_refs")
        if not isinstance(capabilities, list) or not capabilities:
            errors.append(f"provider {provider_id!r} requires evidence_capability_refs")
        else:
            for capability in capabilities:
                if capability not in evidence_classes:
                    errors.append(f"provider {provider_id!r} references unknown evidence class {capability!r}")
        provider_routes = provider.get("route_refs")
        if not isinstance(provider_routes, list) or not provider_routes:
            errors.append(f"provider {provider_id!r} requires route_refs")
        else:
            for route_ref in provider_routes:
                if route_ref not in route_ids:
                    errors.append(f"provider {provider_id!r} references unknown route {route_ref!r}")

    comparison_modes = set(fabric.get("comparison_modes", {}))
    projection_ids: set[str] = set()
    for projection in fabric.get("projections", []):
        if not isinstance(projection, Mapping):
            errors.append("projection rows must be objects")
            continue
        projection_id = projection.get("id")
        if not isinstance(projection_id, str) or not projection_id:
            errors.append("projection requires id")
        elif projection_id in projection_ids:
            errors.append(f"duplicate projection id {projection_id!r}")
        else:
            projection_ids.add(projection_id)

        for field in ("source_provider", "target_provider"):
            provider_id = projection.get(field)
            if provider_id not in providers:
                errors.append(f"projection {projection_id!r} references unknown provider {provider_id!r} in {field}")
        mode = projection.get("comparison_mode")
        if mode not in comparison_modes:
            errors.append(f"projection {projection_id!r} references unknown comparison mode {mode!r}")
        for field in (
            "source_subject",
            "target_subject",
            "source_route_ref",
            "target_route_ref",
            "source_evidence_class",
            "target_evidence_class",
            "privacy_class",
            "source_ref_pattern",
            "source_path_pattern",
            "source_revision_field",
            "target_revision_field",
            "claim_ceiling",
        ):
            if not isinstance(projection.get(field), str) or not projection.get(field).strip():
                errors.append(f"projection {projection_id!r} requires non-empty {field}")

        for selector_field in ("source_event_selector", "target_event_selector"):
            selector = projection.get(selector_field)
            if selector is None:
                continue
            if not isinstance(selector, Mapping):
                errors.append(f"projection {projection_id!r} {selector_field} must be a mapping")
                continue
            for field_name, template in selector.items():
                if not isinstance(field_name, str) or not field_name.strip():
                    errors.append(f"projection {projection_id!r} {selector_field} has an invalid field name")
                if not isinstance(template, str) or not template.strip():
                    errors.append(f"projection {projection_id!r} {selector_field} has an invalid selector value")
                    continue
                if template.startswith("$") and template not in EVENT_SELECTOR_TOKENS:
                    errors.append(
                        f"projection {projection_id!r} {selector_field} references unsupported token {template!r}"
                    )

        source_provider_id = projection.get("source_provider")
        target_provider_id = projection.get("target_provider")
        source_provider = providers.get(source_provider_id, {}) if isinstance(providers, Mapping) else {}
        target_provider = providers.get(target_provider_id, {}) if isinstance(providers, Mapping) else {}
        source_route = projection.get("source_route_ref")
        target_route = projection.get("target_route_ref")
        source_class = projection.get("source_evidence_class")
        target_class = projection.get("target_evidence_class")
        privacy_class = projection.get("privacy_class")

        if source_route not in source_provider.get("route_refs", []):
            errors.append(f"projection {projection_id!r} source_route_ref is not bound to source provider")
        if target_route not in target_provider.get("route_refs", []):
            errors.append(f"projection {projection_id!r} target_route_ref is not bound to target provider")
        if source_class not in evidence_classes or source_class not in source_provider.get("evidence_capability_refs", []):
            errors.append(f"projection {projection_id!r} source_evidence_class is not supported by source provider/B")
        if target_class not in evidence_classes or target_class not in target_provider.get("evidence_capability_refs", []):
            errors.append(f"projection {projection_id!r} target_evidence_class is not supported by target provider/B")
        if privacy_class not in privacy_classes:
            errors.append(f"projection {projection_id!r} privacy_class is not declared by B")

    rules = fabric.get("global_rules", {})
    for field in (
        "projection_scope",
        "event_instance_binding",
        "newest_timestamp",
        "returned_item_typing",
        "missing_observation",
        "conflict",
        "temporal",
    ):
        if not isinstance(rules.get(field), str) or not rules.get(field).strip():
            errors.append(f"provider fabric global_rules requires {field}")

    return errors


def main() -> int:
    errors = validate_provider_fabric(load(INDEX_PATH), load(CONTRACT_PATH), load(FABRIC_PATH))
    errors.extend(validate_operational_support_bindings(ROOT, load(RECEIPT_PATH)))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VERA_PROVIDER_FABRIC_V1 + operational support receipt: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
