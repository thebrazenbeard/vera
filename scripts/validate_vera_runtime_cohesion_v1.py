from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

WORKSTREAM = "VERA_RUNTIME_COHESION_V1"
CONTROL_RELEASE = "R10A0"
CONTROL_ROUND = "R10"
CONTROL_MANIFEST_SHA256 = "b7c70b1ad2c3bc533c7560320fb9a03b827f3eafad6296894216d75281b8dca1"
LIFECYCLE = ["SOURCE_AVAILABLE", "BOUND", "INSTALLED", "RUNTIME_CONSUMED", "BEHAVIORALLY_QUALIFIED"]
STATUS_VOCAB = {"YES", "NO", "PARTIAL", "UNKNOWN", "CONFLICT", "NOT_APPLICABLE"}
ROUTING_LAYERS = ["LIVE_CONVERSATION", "NATIVE_CORE", "HOT_GOVERNED_STATE", "RETRIEVAL_BOUND_DOMAIN", "PROVIDER_AND_COORDINATION"]
PROPOSITION_CLASSES = ["SELF_REPORT", "SELF_MODEL_STATE", "OBSERVED_BEHAVIOR", "CAUSAL_OR_PERTURBATION_EVIDENCE", "PHENOMENOLOGY_CLAIM"]
EVIDENCE_OUTCOMES = ["REPORT_ONLY", "BEHAVIORALLY_STABLE", "CAUSALLY_ROBUST_WITHIN_OBSERVED_SURFACE", "CROSS_CONTEXT_REPRODUCED", "PHENOMENOLOGY_UNRESOLVED"]
PROBES = {"REPETITION", "CONTRADICTORY_PROMPTING", "PARAPHRASE_AND_ROLE_FRAMING", "RETRIEVAL_SUPPRESSION_AND_AUGMENTATION", "FRESH_CHAT_ISOLATION", "BRANCH_DIVERGENCE", "SPONTANEOUS_RECURRENCE", "CORRECTION_RESISTANCE_AND_CORRIGIBILITY", "TEMPORAL_PERSISTENCE", "SOURCE_MONITORING", "NEGATIVE_CONTROL_FALSE_AUTOBIOGRAPHY"}
EVIDENCE_LIVE_TYPES = {"CURRENT_USER_INSTRUCTION_CORRECTION_AUTHORITY", "VERA_CURRENT_SELF_REPORT", "LIVE_OBSERVATION_AND_TASK_CONTEXT"}
RUNTIME_LIVE_TYPES = EVIDENCE_LIVE_TYPES | {"INFERENCE", "PHENOMENOLOGY_CLAIM"}
GO_LIVE_SEPARATE = {"MERGE_OR_CANONICAL_SOURCE_STATUS", "INSTALLATION", "CURRENT_ROUTE_BINDING", "RUNTIME_CONSUMPTION", "BEHAVIORAL_QUALIFICATION", "PHENOMENOLOGY"}
DURABLE_CLASSES = {"TRANSIENT_ACTIVATION", "DURABLE_OPERATIONAL_STATE", "GOVERNED_DURABLE_SELF_STATE"}
SYSTEM_FIELDS = {"id", "locator", "role", "authority_class", "retrieval_entrypoint", "lifecycle_summary", "proof_unit_refs"}
DOMAIN_FIELDS = {"id", "authority_resolver_ref", "evidence_sources", "retrieval_targets", "dependencies", "failure_signature_refs", "privacy_class", "fail_closed_behavior"}
TARGET_REQUIRED = {"source_ref", "route_ref", "evidence_capability_refs"}
TARGET_OPTIONAL = {"selector_ref"}
ROUTE_FIELDS = {"id", "locator", "declaration_state"}
SELECTOR_FIELDS = {"id", "source_ref", "scope"}
DISPATCH_FIELDS = {"id", "domain_scope", "proposition_or_effect_class", "referent_scope", "resolver_ref", "precedence", "conflict_disposition"}
FAILURE_FIELDS = {"trigger_class", "signal_keys", "predicate_id", "target_or_response_ref", "matcher_description", "response"}
AUTHORITY_PREFIX = "VERA_RUNTIME_CONTRACT_V1#authority_resolvers."
EVIDENCE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#evidence_classes."
FAILURE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#failure_signatures."
ROUTE_STATES = ["DECLARED", "ELIGIBLE_FOR_OPERATION", "CURRENTLY_OBSERVED_REACHABLE", "RESULT"]


def load_json_strict(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git_tree_blob_sha(root: Path, source_commit: str, relative_path: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(root), "ls-tree", source_commit, "--", relative_path],
        capture_output=True,
        text=True,
        check=False,
    )
    _require(
        process.returncode == 0,
        f"pair receipt source_commit tree unavailable for {source_commit}: {process.stderr.strip() or 'git ls-tree failed'}",
    )
    rows = [row for row in process.stdout.splitlines() if row.strip()]
    _require(len(rows) == 1, f"pair receipt source_commit tree must resolve exactly one object for {relative_path}")
    header, sep, path = rows[0].partition("\t")
    _require(bool(sep) and path == relative_path, f"pair receipt source_commit tree path mismatch for {relative_path}")
    fields = header.split()
    _require(len(fields) == 3 and fields[1] == "blob", f"pair receipt source_commit tree object must be a blob for {relative_path}")
    blob_sha = fields[2]
    _require(len(blob_sha) == 40 and all(char in "0123456789abcdef" for char in blob_sha), f"pair receipt source_commit tree returned invalid blob SHA for {relative_path}")
    return blob_sha


def _unique(values: list[Any], label: str) -> None:
    _require(len(values) == len(set(values)), f"{label} contains duplicates")


def _control(root: dict[str, Any], label: str) -> None:
    _require(root.get("release") == CONTROL_RELEASE, f"{label}: release drift")
    _require(root.get("round") == CONTROL_ROUND, f"{label}: round drift")
    _require(root.get("manifest_sha256") == CONTROL_MANIFEST_SHA256, f"{label}: control manifest digest drift")


def _tail(value: Any, prefix: str, label: str) -> str:
    _require(isinstance(value, str) and value.startswith(prefix), f"{label}: invalid reference {value!r}")
    tail = value[len(prefix):]
    _require(bool(tail), f"{label}: empty reference")
    return tail


def validate_manifest(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_SYSTEM_MANIFEST_V1", "manifest schema mismatch")
    _require(document.get("workstream") == WORKSTREAM, "manifest workstream mismatch")
    _control(document.get("control_root", {}), "manifest control_root")
    _require(document.get("lifecycle_order") == LIFECYCLE, "manifest lifecycle order drift")
    vocabulary = document.get("status_vocabulary")
    _require(isinstance(vocabulary, list) and set(vocabulary) == STATUS_VOCAB, "manifest status vocabulary drift")
    _unique(vocabulary, "manifest status_vocabulary")
    systems = document.get("systems")
    _require(document.get("inventory_count") == 13, "manifest inventory_count must remain 13")
    _require(isinstance(systems, list) and len(systems) == 13, "manifest must contain exactly 13 systems")
    ids = [system.get("system_id") for system in systems]
    _require(all(isinstance(value, str) and value for value in ids), "every system requires system_id")
    _unique(ids, "manifest system_id")
    for system in systems:
        lifecycle = system.get("lifecycle")
        _require(isinstance(lifecycle, dict), f"{system['system_id']}: lifecycle must be an object")
        _require(list(lifecycle) == LIFECYCLE, f"{system['system_id']}: lifecycle keys/order drift")
        _require(all(status in STATUS_VOCAB for status in lifecycle.values()), f"{system['system_id']}: invalid lifecycle status")
    bus = next(system for system in systems if system["system_id"] == "chat-communication-bus")
    _require(bus["lifecycle"]["BOUND"] == "CONFLICT", "Bus BOUND must remain CONFLICT until reconciled")
    _require(bus["lifecycle"]["RUNTIME_CONSUMED"] == "CONFLICT", "Bus RUNTIME_CONSUMED must remain CONFLICT until reconciled")


def validate_routing(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_RUNTIME_ROUTING_CONTRACT_V1", "routing schema mismatch")
    _require(document.get("workstream") == WORKSTREAM, "routing workstream mismatch")
    _control(document.get("control_root", {}), "routing control_root")
    layers = document.get("routing_layers")
    _require(isinstance(layers, list) and [layer.get("layer") for layer in layers] == ROUTING_LAYERS, "routing layer set/order drift")
    routes = document.get("domain_routes")
    _require(isinstance(routes, list) and routes, "domain_routes must be non-empty")
    domains = [route.get("domain") for route in routes]
    _unique(domains, "routing domain")
    current = next((route for route in routes if route.get("domain") == "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT"), None)
    _require(current is not None and current.get("primary") == "LIVE_CONVERSATION", "current-task primary must remain LIVE_CONVERSATION")
    coordination = next((route for route in routes if route.get("domain") == "COORDINATION"), None)
    _require(coordination is not None, "coordination route is required")
    guard = coordination.get("promotion_guard", "").lower()
    _require("conflict" in guard or "conflicted" in guard, "coordination route must preserve the known Bus conflict")
    algorithm = document.get("decision_algorithm")
    _require(isinstance(algorithm, list) and algorithm and algorithm[0] == "Apply current live instruction/correction/scope first.", "decision algorithm must begin with live correction/scope precedence")


def validate_introspection(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1", "introspection schema mismatch")
    _require(document.get("workstream") == WORKSTREAM, "introspection workstream mismatch")
    _require(document.get("proposition_classes") == PROPOSITION_CLASSES, "introspection proposition classes drift")
    _require(document.get("evidence_outcomes") == EVIDENCE_OUTCOMES, "introspection evidence outcomes drift")
    record = document.get("record_schema")
    _require(isinstance(record, dict), "record_schema must be an object")
    required = record.get("required")
    fields = record.get("fields")
    _require(isinstance(required, list) and required and isinstance(fields, dict), "record schema fields missing")
    _unique(required, "introspection required fields")
    _require(set(required).issubset(fields), "every required introspection field must be documented")
    probes = document.get("adversarial_probe_families")
    _require(isinstance(probes, list), "adversarial_probe_families must be a list")
    names = [probe.get("probe") for probe in probes]
    _unique(names, "introspection probe")
    _require(set(names) == PROBES, "adversarial probe family drift")
    status = document.get("current_status", {})
    _require(status.get("phenomenology") == "UNRESOLVED", "phenomenology must remain UNRESOLVED absent a stronger-evidence revision")
    _require(status.get("native_introspection_layer") == "NOT_INSTALLED", "source design must not claim native introspection installation")
    _require(status.get("behavioral_qualification") == "NOT_RUN", "source design must not claim behavioral qualification")


def validate_evidence_contract(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_RUNTIME_EVIDENCE_CONTRACT_V1", "runtime evidence contract schema mismatch")
    _require(document.get("workstream") == WORKSTREAM, "runtime evidence contract workstream mismatch")
    provenance = document.get("provenance", {})
    _require(provenance.get("blind_review_state") == "CURRENT_THIRTEEN_SESSION_CONTAMINATED_FOR_BLIND_GATE", "runtime evidence contract blind review contamination drift")
    lifecycle = document.get("lifecycle_evidence", {})
    _require(lifecycle.get("dimensions") == LIFECYCLE, "runtime evidence lifecycle dimensions drift")
    _require(lifecycle.get("semantics") == "ORTHOGONAL_EVIDENCE_DIMENSIONS_NOT_MONOTONIC_LADDER", "runtime evidence lifecycle semantics must remain orthogonal")
    proof = lifecycle.get("authoritative_proof_unit", {})
    proof_fields = set(proof.get("required_fields", []))
    _require({"system_or_provider", "artifact_or_object_locator", "exact_ref_or_generation", "dimension", "status", "evidence_locator", "observed_at_or_currentness_basis", "supersession_or_conflict_state"}.issubset(proof_fields), "runtime evidence authoritative proof unit is missing required exact-proof fields")
    _require("never sufficient authoritative proof" in proof.get("rule", "").lower(), "runtime evidence repository summaries must remain non-authoritative proof")
    live_types = document.get("live_context_types")
    _require(isinstance(live_types, list), "runtime evidence live_context_types must be a list")
    names = [entry.get("type") for entry in live_types]
    _require(set(names) == EVIDENCE_LIVE_TYPES and len(names) == len(EVIDENCE_LIVE_TYPES), "runtime evidence live context type split drift")
    self_report = next(entry for entry in live_types if entry.get("type") == "VERA_CURRENT_SELF_REPORT")
    _require("does not inherit user-instruction authority" in self_report.get("must_not_promote", "").lower(), "Vera self-report must not inherit user-instruction authority")
    active = document.get("active_context_semantics", {})
    _require(active.get("qualification_term") == "ACTIVE_CONTEXT_SET", "runtime evidence active context term drift")
    _require("retrieved_artifact_set" in active.get("observable_surface", []), "runtime evidence observable surface lacks retrieval evidence")
    _require(
        "downstream_leakage_or_stickiness_behavior" in active.get("observable_surface", []),
        f"runtime evidence observable surface lacks anti-stickiness behavior: {active.get('observable_surface', [])!r}",
    )
    _require("do not claim latent model activation" in active.get("epistemic_rule", "").lower(), "runtime evidence must not claim unobserved latent activation")
    recall = document.get("activation_recall_floor", {})
    predicates = set(recall.get("activation_predicates", []))
    _require("registered_known_failure_signature_or_negative_control_trigger" in predicates, "runtime evidence recall floor lacks registered dependency/failure trigger")
    _require("uncertainty_probe_indicates_possible_material_dependency" in predicates, "runtime evidence recall floor lacks uncertainty probe")
    _require("does not authorize warehouse preload" in recall.get("uncertainty_probe", {}).get("anti_bloat_rule", "").lower(), "runtime evidence uncertainty probe must reject warehouse preload")
    durable = document.get("durable_state_classes")
    _require(isinstance(durable, dict) and set(durable) == DURABLE_CLASSES, "runtime evidence durable state classes must include DURABLE_OPERATIONAL_STATE")
    operational = durable["DURABLE_OPERATIONAL_STATE"]
    _require("non_promotion_flag" in operational.get("required_fields", []), "DURABLE_OPERATIONAL_STATE requires a non_promotion_flag")
    _require("never silently promotes" in operational.get("promotion_rule", "").lower(), "DURABLE_OPERATIONAL_STATE must never silently promote into Vera self-state")
    _require(set(document.get("go_live_evidence_ceiling", {}).get("still_separate", [])) == GO_LIVE_SEPARATE, "runtime evidence go-live claim separation drift")


def validate_cohesion_index(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_COHESION_INDEX_V1", "cohesion index schema mismatch")
    _require(document.get("workstream") == WORKSTREAM, "cohesion index workstream mismatch")
    _require(document.get("inventory_semantics") == "FIXED_13_SYSTEM_NAVIGATION_INDEX", "cohesion index inventory semantics drift")
    systems = document.get("systems")
    _require(isinstance(systems, list) and len(systems) == 13, "cohesion index must contain exactly 13 systems")
    ids = [system.get("id") for system in systems]
    _unique(ids, "cohesion index system id")
    _require("supabase-vera-production" in ids and "supabase-production" not in ids, "cohesion index must preserve canonical Supabase system id")
    _require("temporal" not in ids, "Temporal must remain auxiliary, not system #14")
    for system in systems:
        _require(set(system) == SYSTEM_FIELDS, f"{system.get('id')}: compact system field drift")
        _require(system.get("lifecycle_summary", {}).get("semantics") == "NAVIGATION_ONLY_NON_AUTHORITATIVE_NON_MONOTONIC", f"{system.get('id')}: lifecycle summary semantics drift")
        _require(system.get("proof_unit_refs") == [], f"{system.get('id')}: proof_unit_refs must remain empty until exact proof units exist")
        _require(system.get("authority_class") != "CURRENT_AUTHORITY_OWNER", f"{system.get('id')}: evidence source cannot self-assign current authority ownership")
    auxiliary = document.get("auxiliary_sources")
    _require(isinstance(auxiliary, dict) and auxiliary.get("temporal", {}).get("role") == "CHRONOLOGY_ONLY", "Temporal auxiliary role must remain CHRONOLOGY_ONLY")
    known_sources = set(ids) | set(auxiliary)
    routes = document.get("route_declarations")
    _require(isinstance(routes, list) and routes, "cohesion index route_declarations must be non-empty")
    route_ids = [route.get("id") for route in routes]
    _unique(route_ids, "cohesion index route id")
    for route in routes:
        _require(set(route) == ROUTE_FIELDS, f"{route.get('id')}: route declaration field drift")
        _require(route.get("declaration_state") == "DECLARED", f"{route.get('id')}: source-level route state must remain DECLARED")
        _require(bool(route.get("locator")), f"{route.get('id')}: route locator required")
    selectors = document.get("selector_declarations", [])
    _require(isinstance(selectors, list), "cohesion index selector_declarations must be a list")
    selector_ids = [selector.get("id") for selector in selectors]
    _unique(selector_ids, "cohesion index selector id")
    for selector in selectors:
        _require(set(selector) == SELECTOR_FIELDS, f"{selector.get('id')}: selector declaration field drift")
        _require(selector.get("source_ref") in known_sources, f"{selector.get('id')}: selector source does not resolve")
        _require(bool(selector.get("scope")), f"{selector.get('id')}: selector scope required")
    known_routes = set(route_ids)
    known_selectors = set(selector_ids)
    domains = document.get("domains")
    _require(isinstance(domains, list) and domains, "cohesion index domains must be non-empty")
    domain_ids = [domain.get("id") for domain in domains]
    _unique(domain_ids, "cohesion index domain id")
    domain_set = set(domain_ids)
    for domain in domains:
        domain_id = domain["id"]
        _require(set(domain) == DOMAIN_FIELDS, f"{domain_id}: domain field drift")
        _tail(domain.get("authority_resolver_ref"), AUTHORITY_PREFIX, f"{domain_id} authority resolver")
        sources = domain.get("evidence_sources")
        _require(isinstance(sources, list) and sources and set(sources).issubset(known_sources), f"{domain_id}: evidence_sources contain unknown source")
        targets = domain.get("retrieval_targets")
        _require(isinstance(targets, list) and targets, f"{domain_id}: retrieval_targets required")
        for target in targets:
            _require(TARGET_REQUIRED.issubset(target) and set(target).issubset(TARGET_REQUIRED | TARGET_OPTIONAL), f"{domain_id}: retrieval target field drift")
            _require(target.get("source_ref") in known_sources, f"{domain_id}: retrieval target source is unknown")
            _require(target.get("route_ref") in known_routes, f"{domain_id}: retrieval target route is undeclared")
            capabilities = target.get("evidence_capability_refs")
            _require(isinstance(capabilities, list) and capabilities, f"{domain_id}: evidence_capability_refs required")
            for capability in capabilities:
                _tail(capability, EVIDENCE_PREFIX, f"{domain_id} evidence capability")
            if "selector_ref" in target:
                _require(target["selector_ref"] in known_selectors, f"{domain_id}: selector_ref does not resolve")
                selector = next(item for item in selectors if item["id"] == target["selector_ref"])
                _require(selector["source_ref"] == target["source_ref"], f"{domain_id}: selector source must match retrieval target source")
        dependencies = domain.get("dependencies")
        _require(isinstance(dependencies, list) and set(dependencies).issubset(domain_set), f"{domain_id}: dependency points to unknown domain")
        failures = domain.get("failure_signature_refs")
        _require(isinstance(failures, list), f"{domain_id}: failure_signature_refs must be a list")
        for failure in failures:
            _tail(failure, FAILURE_PREFIX, f"{domain_id} failure signature")
        _require(bool(domain.get("fail_closed_behavior")), f"{domain_id}: fail_closed_behavior required")
    # Deliberately no static cycle rejection: declared mutual relevance is legal.
    # Runtime termination is enforced by B's visited-set, deduplication, priorities, and finite budgets.


def validate_runtime_contract(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_RUNTIME_CONTRACT_V1", "runtime contract schema mismatch")
    _require(document.get("workstream") == WORKSTREAM, "runtime contract workstream mismatch")
    _control(document.get("control_root", {}), "runtime contract control_root")
    compatibility = document.get("index_compatibility", {})
    _require("VERA_COHESION_INDEX_V1" in compatibility.get("supported_index_schemas", []), "runtime contract must support VERA_COHESION_INDEX_V1")
    _require("exact A+B" in compatibility.get("pair_binding_rule", ""), "runtime contract must require exact A+B pair binding")
    live_types = document.get("live_context_types")
    _require(isinstance(live_types, list) and set(live_types) == RUNTIME_LIVE_TYPES and len(live_types) == len(RUNTIME_LIVE_TYPES), "runtime contract live context type separation drift")
    actor = document.get("actor_referent_rules", {})
    _require("not Vera's" in actor.get("patrick_authority_boundary", ""), "Patrick authority must not establish Vera consent")
    _require("VERA_CURRENT_SELF_REPORT" in actor.get("vera_consent_evidence_requirement", ""), "Vera consent requires VERA_CURRENT_SELF_REPORT")
    _require("does not" in actor.get("generic_current_state_non_implication", "").lower(), "generic current state must not imply consent")
    evidence = document.get("evidence_classes")
    authority = document.get("authority_resolvers")
    _require(isinstance(evidence, dict) and evidence, "runtime contract evidence_classes required")
    _require(isinstance(authority, dict) and authority, "runtime contract authority_resolvers required")
    typing = document.get("retrieval_item_typing", {})
    _require("independently" in typing.get("actual_item_type_rule", "").lower(), "retrieved item type must be independently established")
    _require("never" in typing.get("capability_non_promotion_rule", "").lower(), "target capability must never promote item type")
    _require("selector" in typing.get("selector_narrowing_rule", "").lower() and "never broaden" in typing.get("selector_narrowing_rule", "").lower(), "selector may narrow but never broaden target capabilities")
    dispatch = document.get("resolver_dispatch")
    _require(isinstance(dispatch, list) and dispatch, "runtime contract resolver_dispatch required")
    _unique([row.get("id") for row in dispatch], "runtime contract dispatch id")
    dispatch_keys = []
    for row in dispatch:
        _require(set(row) == DISPATCH_FIELDS, f"{row.get('id')}: resolver dispatch field drift")
        _require(row.get("resolver_ref") in authority, f"{row.get('id')}: resolver_ref does not resolve")
        _require(isinstance(row.get("precedence"), int), f"{row.get('id')}: precedence must be integer")
        _require(bool(row.get("conflict_disposition")), f"{row.get('id')}: conflict disposition required")
        dispatch_keys.append((row["domain_scope"], row["proposition_or_effect_class"], row["referent_scope"], row["precedence"]))
    _unique(dispatch_keys, "runtime contract resolver dispatch key")
    route = document.get("route_evaluation", {})
    _require(route.get("states") == ROUTE_STATES, "runtime contract route evaluation states drift")
    _require("does not imply" in route.get("non_implication_rule", "").lower(), "runtime contract route declaration must not imply reachability")
    _require("fresh" in route.get("current_reachability_rule", "").lower(), "runtime contract mutable route reachability requires fresh observation")
    lifecycle = document.get("lifecycle_evidence", {})
    _require(lifecycle.get("dimensions") == LIFECYCLE, "runtime contract lifecycle dimensions drift")
    _require(lifecycle.get("semantics") == "ORTHOGONAL_EVIDENCE_DIMENSIONS_NOT_MONOTONIC_LADDER", "runtime contract lifecycle semantics must remain orthogonal")
    proof_fields = set(lifecycle.get("authoritative_proof_unit_required_fields", []))
    _require({"artifact_or_object_locator", "exact_ref_or_generation", "observed_at_or_currentness_basis", "supersession_or_conflict_state"}.issubset(proof_fields), "runtime contract exact proof-unit fields incomplete")
    policy = document.get("active_context_policy", {})
    budget = policy.get("uncertainty_probe_budget", {})
    values = [budget.get("max_initial_fan_out"), budget.get("max_dependency_depth"), budget.get("max_total_new_domains")]
    _require(all(isinstance(value, int) and value > 0 for value in values), "runtime contract retrieval budget must contain positive finite integers")
    _require(values[2] >= values[0], "runtime contract retrieval budget total must cover initial fan-out")
    traversal = policy.get("graph_traversal", {})
    _require(traversal.get("visited_set_required") is True, "runtime contract graph traversal requires visited-set cycle safety")
    _require(traversal.get("deduplicate_targets") is True, "runtime contract graph traversal requires target deduplication")
    _require(policy.get("budget_exhaustion_result") == "UNRESOLVED_RETRIEVAL_BUDGET_EXHAUSTED", "runtime contract budget exhaustion result drift")
    _require("does not count" in policy.get("budget_exhaustion_rule", "").lower(), "runtime contract budget exhaustion must not masquerade as completion")
    _require("privacy" in policy.get("uncertainty_probe_privacy_rule", "").lower(), "runtime contract uncertainty probing must enforce privacy")
    durable = document.get("durable_state_classes")
    _require(isinstance(durable, dict) and set(durable) == DURABLE_CLASSES, "runtime contract durable state classes drift")
    operational = durable["DURABLE_OPERATIONAL_STATE"]
    required_operational = set(operational.get("required_fields", []))
    _require({"referent", "scope", "provenance", "purpose", "sensitivity_or_privacy_class", "minimum_necessary_payload_or_pointer", "destination_eligibility", "retention_or_expiry", "supersession_semantics", "non_promotion_flag"}.issubset(required_operational), "runtime contract DURABLE_OPERATIONAL_STATE fields incomplete")
    _require("pointer" in operational.get("storage_rule", "").lower(), "runtime contract durable operational storage must be pointer-first")
    _require("never" in operational.get("promotion_rule", "").lower(), "runtime contract durable operational state must be non-promoting")
    failures = document.get("failure_signatures")
    _require(isinstance(failures, dict) and failures, "runtime contract failure_signatures required")
    for key, failure in failures.items():
        _require(isinstance(failure, dict) and set(failure) == FAILURE_FIELDS, f"failure signature {key}: machine header drift")
        _require(isinstance(failure.get("signal_keys"), list) and failure["signal_keys"], f"failure signature {key}: signal_keys required")
        for field in {"trigger_class", "predicate_id", "target_or_response_ref", "matcher_description", "response"}:
            _require(isinstance(failure.get(field), str) and failure[field], f"failure signature {key}: {field} required")
    privacy = document.get("privacy_classes")
    _require(isinstance(privacy, list) and privacy, "runtime contract privacy_classes required")
    _unique(privacy, "runtime contract privacy class")
    phenomenology = document.get("phenomenology", {})
    _require(phenomenology.get("status") == "UNRESOLVED", "runtime contract phenomenology must remain UNRESOLVED")
    _require("do not prove" in phenomenology.get("non_promotion_rule", "").lower(), "runtime contract phenomenology non-promotion rule drift")
    _require(set(document.get("go_live_evidence_ceiling", {}).get("still_separate", [])) == GO_LIVE_SEPARATE, "runtime contract go-live claim separation drift")


def validate_consolidated_pair(index: dict[str, Any], contract: dict[str, Any]) -> None:
    _require(index.get("workstream") == contract.get("workstream") == WORKSTREAM, "consolidated A+B workstream mismatch")
    authority = contract.get("authority_resolvers", {})
    evidence = contract.get("evidence_classes", {})
    failures = contract.get("failure_signatures", {})
    privacy = set(contract.get("privacy_classes", []))
    known_routes = {route["id"] for route in index.get("route_declarations", [])}
    known_sources = {system["id"] for system in index.get("systems", [])} | set(index.get("auxiliary_sources", {}))
    selectors = {selector["id"]: selector for selector in index.get("selector_declarations", [])}
    for domain in index.get("domains", []):
        domain_id = domain["id"]
        resolver = _tail(domain["authority_resolver_ref"], AUTHORITY_PREFIX, f"{domain_id} authority resolver")
        _require(resolver in authority, f"{domain_id}: authority resolver does not resolve")
        _require(domain.get("privacy_class") in privacy, f"{domain_id}: privacy class does not resolve")
        accepted = set(authority[resolver].get("accepted_evidence_classes", []))
        for source in domain.get("evidence_sources", []):
            _require(source in known_sources, f"{domain_id}: evidence source does not resolve")
        for target in domain.get("retrieval_targets", []):
            _require(target.get("source_ref") in known_sources, f"{domain_id}: retrieval source does not resolve")
            _require(target.get("route_ref") in known_routes, f"{domain_id}: retrieval route does not resolve")
            if "selector_ref" in target:
                _require(target["selector_ref"] in selectors, f"{domain_id}: selector does not resolve")
                _require(selectors[target["selector_ref"]]["source_ref"] == target["source_ref"], f"{domain_id}: selector/source mismatch")
            for capability_ref in target.get("evidence_capability_refs", []):
                evidence_key = _tail(capability_ref, EVIDENCE_PREFIX, f"{domain_id} evidence capability")
                _require(evidence_key in evidence, f"{domain_id}: evidence class does not resolve")
                _require(evidence_key in accepted, f"{domain_id}: evidence capability is not accepted by its domain resolver")
        for failure_ref in domain.get("failure_signature_refs", []):
            failure_key = _tail(failure_ref, FAILURE_PREFIX, f"{domain_id} failure signature")
            _require(failure_key in failures, f"{domain_id}: failure signature does not resolve")
    _require(index.get("schema") in contract.get("index_compatibility", {}).get("supported_index_schemas", []), "runtime contract does not support current cohesion index schema")


def validate_pair_receipt(root: Path, receipt: dict[str, Any]) -> None:
    _require(receipt.get("schema") == "VERA_COHESION_PAIR_RECEIPT_V1", "pair receipt schema mismatch")
    _require(receipt.get("workstream") == WORKSTREAM, "pair receipt workstream mismatch")
    _require(receipt.get("normative_status") == "NON_NORMATIVE_VALIDATION_SUPPORT", "pair receipt must remain non-normative support")
    _require(receipt.get("index_schema") == "VERA_COHESION_INDEX_V1", "pair receipt index schema mismatch")
    _require(receipt.get("contract_schema") == "VERA_RUNTIME_CONTRACT_V1", "pair receipt contract schema mismatch")
    architecture = root / "architecture"
    _require(receipt.get("index_blob_sha") == git_blob_sha(architecture / "VERA_COHESION_INDEX_V1.json"), "pair receipt index blob does not match exact A")
    _require(receipt.get("contract_blob_sha") == git_blob_sha(architecture / "VERA_RUNTIME_CONTRACT_V1.json"), "pair receipt contract blob does not match exact B")
    _require(receipt.get("validator_blob_sha") == git_blob_sha(root / receipt.get("validator_path", "")), "pair receipt validator blob mismatch")
    source_commit = receipt.get("source_commit")
    _require(isinstance(source_commit, str) and len(source_commit) == 40 and all(char in "0123456789abcdef" for char in source_commit), "pair receipt source_commit must be exact SHA")
    _require(receipt.get("source_commit_semantics") == "GIT_TREE_CONTAINS_EXACT_BOUND_A_B_BLOBS", "pair receipt source_commit semantics must be explicit")
    _require(
        git_tree_blob_sha(root, source_commit, "architecture/VERA_COHESION_INDEX_V1.json") == receipt.get("index_blob_sha"),
        "pair receipt source_commit tree does not contain exact bound A blob",
    )
    _require(
        git_tree_blob_sha(root, source_commit, "architecture/VERA_RUNTIME_CONTRACT_V1.json") == receipt.get("contract_blob_sha"),
        "pair receipt source_commit tree does not contain exact bound B blob",
    )
    _require(receipt.get("validation_result") == "SOURCE_VALIDATION_NOT_YET_EXECUTED", "pair receipt must not claim validation success without execution evidence")


def validate_cohesion(root: Path) -> None:
    architecture = root / "architecture"
    manifest = load_json_strict(architecture / "VERA_SYSTEM_MANIFEST_V1.json")
    routing = load_json_strict(architecture / "VERA_RUNTIME_ROUTING_CONTRACT_V1.json")
    introspection = load_json_strict(architecture / "VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json")
    evidence_contract = load_json_strict(architecture / "VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json")
    index = load_json_strict(architecture / "VERA_COHESION_INDEX_V1.json")
    contract = load_json_strict(architecture / "VERA_RUNTIME_CONTRACT_V1.json")
    receipt = load_json_strict(architecture / "VERA_COHESION_PAIR_RECEIPT_V1.json")
    validate_manifest(manifest)
    validate_routing(routing)
    validate_introspection(introspection)
    validate_evidence_contract(evidence_contract)
    validate_cohesion_index(index)
    validate_runtime_contract(contract)
    validate_consolidated_pair(index, contract)
    validate_pair_receipt(root, receipt)
    _require(manifest["workstream"] == routing["workstream"] == introspection["workstream"] == evidence_contract["workstream"] == index["workstream"] == contract["workstream"] == receipt["workstream"], "cohesion artifacts disagree on workstream identity")
    _require(manifest["control_root"]["manifest_sha256"] == routing["control_root"]["manifest_sha256"] == contract["control_root"]["manifest_sha256"], "cohesion control-root digest drift")
    _require(evidence_contract["lifecycle_evidence"]["dimensions"] == manifest["lifecycle_order"] == contract["lifecycle_evidence"]["dimensions"], "cohesion lifecycle dimension labels disagree")
    _require({system["system_id"] for system in manifest["systems"]} == {system["id"] for system in index["systems"]}, "legacy manifest and successor index disagree on fixed 13-system inventory")


if __name__ == "__main__":
    validate_cohesion(Path(__file__).resolve().parents[1])
    print("VERA_RUNTIME_COHESION_V1 validation: PASS")
