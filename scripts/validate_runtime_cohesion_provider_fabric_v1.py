#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json"
CONTRACT_PATH = ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json"
FABRIC_PATH = ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json"
RECEIPT_PATH = ROOT / "architecture" / "VERA_COHESION_PAIR_RECEIPT_V1.json"
EVENT_SELECTOR_TOKENS = {"$source_ref", "$source_path", "$source_revision"}
SUPPORT_COMMIT_SEMANTICS = "GIT_TREE_CONTAINS_EXACT_OPERATIONAL_SUPPORT_PATH_BLOBS"
GOVERNING_STATES = {"SATISFIED", "UNRESOLVED", "CONFLICT"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(char in "0123456789abcdef" for char in value)


def _tree_blob(root: Path, source_commit: str, relative_path: str) -> tuple[str | None, str | None]:
    process = subprocess.run(
        ["git", "-C", str(root), "ls-tree", source_commit, "--", relative_path],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        return None, process.stderr.strip() or "git ls-tree failed"
    rows = [row for row in process.stdout.splitlines() if row.strip()]
    if len(rows) != 1:
        return None, f"expected exactly one tree object for {relative_path!r}; got {len(rows)}"
    header, sep, path = rows[0].partition("\t")
    if not sep or path != relative_path:
        return None, f"tree path mismatch for {relative_path!r}"
    fields = header.split()
    if len(fields) != 3 or fields[1] != "blob" or not _is_sha(fields[2]):
        return None, f"tree object for {relative_path!r} is not an exact blob"
    return fields[2], None


def validate_operational_support_bindings(root: Path, receipt: Mapping[str, Any]) -> list[str]:
    """Bind every operational-support path/blob claim to one immutable Git commit."""

    errors: list[str] = []
    source_commit = receipt.get("operational_support_source_commit")
    if not _is_sha(source_commit):
        errors.append("pair receipt operational_support_source_commit must be an exact lowercase 40-hex Git commit")
        return errors
    if receipt.get("operational_support_source_commit_semantics") != SUPPORT_COMMIT_SEMANTICS:
        errors.append(
            f"pair receipt operational_support_source_commit_semantics must be {SUPPORT_COMMIT_SEMANTICS}"
        )

    commit_check = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", f"{source_commit}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if commit_check.returncode != 0:
        errors.append("pair receipt operational_support_source_commit does not resolve to an available immutable commit")
        return errors

    support = receipt.get("operational_support")
    if not isinstance(support, Mapping):
        return errors + ["pair receipt operational support mapping is required"]
    if support.get("normative_status") != "NON_NORMATIVE_OPERATIONAL_SUPPORT":
        errors.append("pair receipt operational support must remain NON_NORMATIVE_OPERATIONAL_SUPPORT")

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
        pure = PurePosixPath(relative_path)
        if pure.is_absolute() or ".." in pure.parts or relative_path.startswith("./"):
            errors.append(f"operational support {name!r} path escapes or aliases repository root: {relative_path!r}")
            continue
        if not _is_sha(blob_sha):
            errors.append(f"operational support {name!r} requires exact lowercase Git blob SHA")
            continue
        observed_blob, issue = _tree_blob(root, source_commit, relative_path)
        if issue is not None:
            errors.append(f"operational support {name!r} path does not resolve in operational_support_source_commit: {issue}")
            continue
        if observed_blob != blob_sha:
            errors.append(
                f"operational support {name!r} blob mismatch in operational_support_source_commit: receipt={blob_sha} observed={observed_blob} path={relative_path}"
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

    hard_rule = str(semantics.get("hard_prerequisite_rule", "")).lower()
    if "route reachability" not in hard_rule or "satisfied" not in hard_rule or "dependent" not in hard_rule:
        errors.append("dependency_semantics.hard_prerequisite_rule must state that route reachability does not release dependent I/O and explicit governing satisfaction is required")

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

    incoming_targets = {dependency for dependencies in dependencies_by_domain.values() for dependency in dependencies}
    for hard_domain in sorted(hard_domains.intersection(domain_ids)):
        if hard_domain not in incoming_targets:
            errors.append(f"hard prerequisite domain {hard_domain!r} has no declared incoming dependency edge and cannot govern any dependent domain")

    hard_graph = {
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


def _validate_dispatch_decisiveness(contract: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    dispatch_rows = contract.get("resolver_dispatch")
    registry = contract.get("resolver_dispatch_decisive_evidence")
    resolvers = contract.get("authority_resolvers")
    evidence_classes = set(contract.get("evidence_classes", {}))
    if not isinstance(dispatch_rows, list) or not dispatch_rows:
        return ["runtime contract resolver_dispatch is required before decisive evidence can be validated"]
    if not isinstance(registry, Mapping):
        return ["runtime contract resolver_dispatch_decisive_evidence mapping is required"]
    if not isinstance(resolvers, Mapping):
        return ["runtime contract authority_resolvers mapping is required"]

    dispatch_ids = {
        row.get("id") for row in dispatch_rows
        if isinstance(row, Mapping) and isinstance(row.get("id"), str) and row.get("id")
    }
    if set(registry) != dispatch_ids:
        errors.append("resolver_dispatch_decisive_evidence keys must exactly match resolver_dispatch ids")

    for row in dispatch_rows:
        if not isinstance(row, Mapping):
            continue
        dispatch_id = row.get("id")
        resolver_ref = row.get("resolver_ref")
        rule = registry.get(dispatch_id) if isinstance(dispatch_id, str) else None
        required_keys = {"all_of", "any_of", "relational_binding"} if dispatch_id == "dispatch:semantic-currentness" else {"all_of", "any_of"}
        if not isinstance(rule, Mapping) or set(rule) != required_keys:
            errors.append(f"dispatch {dispatch_id!r} decisive evidence keys must be exactly {sorted(required_keys)!r}")
            continue
        all_of = rule.get("all_of")
        any_of = rule.get("any_of")
        if not isinstance(all_of, list) or not isinstance(any_of, list):
            errors.append(f"dispatch {dispatch_id!r} decisive all_of/any_of must be lists")
            continue
        classes = all_of + any_of
        if not classes or any(not isinstance(value, str) or not value for value in classes):
            errors.append(f"dispatch {dispatch_id!r} decisive evidence requires at least one non-empty evidence class")
            continue
        if len(classes) != len(set(classes)):
            errors.append(f"dispatch {dispatch_id!r} decisive evidence contains duplicate/overlapping classes")
        unknown = set(classes).difference(evidence_classes)
        if unknown:
            errors.append(f"dispatch {dispatch_id!r} decisive evidence references unknown classes {sorted(unknown)!r}")
        resolver = resolvers.get(resolver_ref)
        accepted = set(resolver.get("accepted_evidence_classes", [])) if isinstance(resolver, Mapping) else set()
        excess = set(classes).difference(accepted)
        if excess:
            errors.append(f"dispatch {dispatch_id!r} decisive evidence exceeds resolver {resolver_ref!r} accepted set: {sorted(excess)!r}")
        if dispatch_id == "dispatch:semantic-currentness":
            relational = rule.get("relational_binding")
            if not isinstance(relational, Mapping):
                errors.append("dispatch:semantic-currentness requires relational_binding")
            else:
                for field in ("mode", "control_root_ref", "required_source_identity", "required_currentness_state", "required_supersession_state", "shared_metadata_fields"):
                    value = relational.get(field)
                    if value in (None, "", []):
                        errors.append(f"dispatch:semantic-currentness relational_binding requires {field}")

    control_rule = registry.get("dispatch:control-binding")
    if isinstance(control_rule, Mapping):
        if set(control_rule.get("all_of", [])) != {"control_source", "live_observation"} or control_rule.get("any_of") != []:
            errors.append("dispatch:control-binding must require all_of control_source + live_observation and no any_of shortcut")

    policy = contract.get("active_context_policy", {})
    if set(policy.get("governing_dependency_states", [])) != GOVERNING_STATES:
        errors.append("active_context_policy governing_dependency_states must be SATISFIED/UNRESOLVED/CONFLICT")
    release_rule = str(policy.get("governing_dependency_release_rule", "")).lower()
    if "route reachability" not in release_rule or "satisfied" not in release_rule or "dependent" not in release_rule:
        errors.append("active_context_policy governing_dependency_release_rule must separate route reachability from governing satisfaction")
    return errors


def _validate_receipt_binding(projection: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    binding = projection.get("receipt_binding")
    if not isinstance(binding, Mapping):
        return [f"projection {projection.get('id')!r} EXACT_RECEIPT requires receipt_binding"]
    expected_fields = {
        "receipt_schema", "receipt_type", "source_subject", "target_subject",
        "source_locator", "source_revision", "source_content_digest", "event_ref",
        "event_path", "receipt_ref", "receipt_digest",
    }
    if binding.get("target_scope") != "PROVIDER_RECEIPT":
        errors.append(f"projection {projection.get('id')!r} receipt_binding target_scope must be PROVIDER_RECEIPT")
    if binding.get("metadata_field") != "receipt_binding":
        errors.append(f"projection {projection.get('id')!r} receipt_binding metadata_field must be receipt_binding")
    if not isinstance(binding.get("receipt_schema"), str) or not binding.get("receipt_schema"):
        errors.append(f"projection {projection.get('id')!r} receipt_binding requires receipt_schema")
    if not isinstance(binding.get("receipt_type"), str) or not binding.get("receipt_type"):
        errors.append(f"projection {projection.get('id')!r} receipt_binding requires receipt_type")
    if binding.get("digest_algorithm") != "SHA256_CANONICAL_JSON_EXCLUDING_RECEIPT_DIGEST":
        errors.append(f"projection {projection.get('id')!r} receipt_binding digest algorithm drift")
    if set(binding.get("required_fields", [])) != expected_fields:
        errors.append(f"projection {projection.get('id')!r} receipt_binding required_fields drift")
    return errors


def validate_provider_fabric(index: Mapping[str, Any], contract: Mapping[str, Any], fabric: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if fabric.get("schema") != "VERA_PROVIDER_FABRIC_V1":
        errors.append("fabric schema must be VERA_PROVIDER_FABRIC_V1")
    if fabric.get("normative_status") != "NON_NORMATIVE_OPERATIONAL_SUPPORT":
        errors.append("provider fabric must be NON_NORMATIVE_OPERATIONAL_SUPPORT")
    if set(fabric.get("normative_pair_refs", [])) != {"VERA_COHESION_INDEX_V1", "VERA_RUNTIME_CONTRACT_V1"}:
        errors.append("provider fabric normative_pair_refs must point only to the A+B schemas")

    errors.extend(_validate_dependency_semantics(index))
    errors.extend(_validate_dispatch_decisiveness(contract))

    evidence_classes = set(contract.get("evidence_classes", {}))
    privacy_classes = set(contract.get("privacy_classes", []))
    route_ids = {
        row.get("id") for row in index.get("route_declarations", [])
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
        if mode == "EXACT_RECEIPT":
            errors.extend(_validate_receipt_binding(projection))

        for field in (
            "source_subject", "target_subject", "source_route_ref", "target_route_ref",
            "source_evidence_class", "target_evidence_class", "privacy_class",
            "source_ref_pattern", "source_path_pattern", "source_revision_field",
            "target_revision_field", "claim_ceiling",
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
                    errors.append(f"projection {projection_id!r} {selector_field} references unsupported token {template!r}")

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
    for field in ("projection_scope", "event_instance_binding", "newest_timestamp", "returned_item_typing", "missing_observation", "conflict", "temporal"):
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
