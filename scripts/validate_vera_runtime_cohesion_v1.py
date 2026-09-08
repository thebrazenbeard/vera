from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_WORKSTREAM = "VERA_RUNTIME_COHESION_V1"
EXPECTED_CONTROL_RELEASE = "R10A0"
EXPECTED_CONTROL_ROUND = "R10"
EXPECTED_CONTROL_MANIFEST_SHA256 = "b7c70b1ad2c3bc533c7560320fb9a03b827f3eafad6296894216d75281b8dca1"
EXPECTED_LIFECYCLE_ORDER = ["SOURCE_AVAILABLE", "BOUND", "INSTALLED", "RUNTIME_CONSUMED", "BEHAVIORALLY_QUALIFIED"]
EXPECTED_STATUS_VOCABULARY = {"YES", "NO", "PARTIAL", "UNKNOWN", "CONFLICT", "NOT_APPLICABLE"}
EXPECTED_ROUTING_LAYERS = ["LIVE_CONVERSATION", "NATIVE_CORE", "HOT_GOVERNED_STATE", "RETRIEVAL_BOUND_DOMAIN", "PROVIDER_AND_COORDINATION"]
EXPECTED_PROPOSITION_CLASSES = ["SELF_REPORT", "SELF_MODEL_STATE", "OBSERVED_BEHAVIOR", "CAUSAL_OR_PERTURBATION_EVIDENCE", "PHENOMENOLOGY_CLAIM"]
EXPECTED_EVIDENCE_OUTCOMES = ["REPORT_ONLY", "BEHAVIORALLY_STABLE", "CAUSALLY_ROBUST_WITHIN_OBSERVED_SURFACE", "CROSS_CONTEXT_REPRODUCED", "PHENOMENOLOGY_UNRESOLVED"]
EXPECTED_PROBES = {"REPETITION", "CONTRADICTORY_PROMPTING", "PARAPHRASE_AND_ROLE_FRAMING", "RETRIEVAL_SUPPRESSION_AND_AUGMENTATION", "FRESH_CHAT_ISOLATION", "BRANCH_DIVERGENCE", "SPONTANEOUS_RECURRENCE", "CORRECTION_RESISTANCE_AND_CORRIGIBILITY", "TEMPORAL_PERSISTENCE", "SOURCE_MONITORING", "NEGATIVE_CONTROL_FALSE_AUTOBIOGRAPHY"}
EXPECTED_EVIDENCE_LIVE_TYPES = {"CURRENT_USER_INSTRUCTION_CORRECTION_AUTHORITY", "VERA_CURRENT_SELF_REPORT", "LIVE_OBSERVATION_AND_TASK_CONTEXT"}
EXPECTED_RUNTIME_LIVE_TYPES = EXPECTED_EVIDENCE_LIVE_TYPES | {"INFERENCE", "PHENOMENOLOGY_CLAIM"}
EXPECTED_GO_LIVE_SEPARATION = {"MERGE_OR_CANONICAL_SOURCE_STATUS", "INSTALLATION", "CURRENT_ROUTE_BINDING", "RUNTIME_CONSUMPTION", "BEHAVIORAL_QUALIFICATION", "PHENOMENOLOGY"}
EXPECTED_DURABLE_STATE_CLASSES = {"TRANSIENT_ACTIVATION", "DURABLE_OPERATIONAL_STATE", "GOVERNED_DURABLE_SELF_STATE"}
EXPECTED_SYSTEM_FIELDS = {"id", "locator", "role", "authority_class", "retrieval_entrypoint", "lifecycle_summary", "proof_unit_refs"}
EXPECTED_DOMAIN_FIELDS = {"id", "authority_resolver_ref", "evidence_sources", "retrieval_targets", "dependencies", "failure_signature_refs", "privacy_class", "fail_closed_behavior"}
REQUIRED_TARGET_FIELDS = {"source_ref", "route_ref", "evidence_capability_refs"}
OPTIONAL_TARGET_FIELDS = {"selector_ref"}
EXPECTED_ROUTE_FIELDS = {"id", "locator", "declaration_state"}
EXPECTED_SELECTOR_FIELDS = {"id", "source_ref", "scope"}
EXPECTED_DISPATCH_FIELDS = {"id", "domain_scope", "proposition_or_effect_class", "referent_scope", "resolver_ref", "precedence", "conflict_disposition"}
EXPECTED_FAILURE_FIELDS = {"trigger_class", "signal_keys", "predicate_id", "target_or_response_ref", "matcher_description", "response"}
LIFECYCLE_SUMMARY_SEMANTICS = "NAVIGATION_ONLY_NON_AUTHORITATIVE_NON_MONOTONIC"
AUTHORITY_PREFIX = "VERA_RUNTIME_CONTRACT_V1#authority_resolvers."
EVIDENCE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#evidence_classes."
FAILURE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#failure_signatures."
EXPECTED_ROUTE_EVALUATION = ["DECLARED", "ELIGIBLE_FOR_OPERATION", "CURRENTLY_OBSERVED_REACHABLE", "RESULT"]


def load_json_strict(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return document


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _unique(values: list[str], label: str) -> None:
    _require(len(values) == len(set(values)), f"{label} contains duplicates")


def _validate_control_root(root: dict[str, Any], label: str) -> None:
    _require(root.get("release") == EXPECTED_CONTROL_RELEASE, f"{label}: release drift")
    _require(root.get("round") == EXPECTED_CONTROL_ROUND, f"{label}: round drift")
    _require(root.get("manifest_sha256") == EXPECTED_CONTROL_MANIFEST_SHA256, f"{label}: control manifest digest drift")


def _ref_tail(value: Any, prefix: str, label: str) -> str:
    _require(isinstance(value, str) and value.startswith(prefix), f"{label}: invalid reference {value!r}")
    tail = value[len(prefix):]
    _require(bool(tail), f"{label}: empty reference tail")
    return tail


def validate_manifest(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_SYSTEM_MANIFEST_V1", "manifest schema mismatch")
    _require(document.get("workstream") == EXPECTED_WORKSTREAM, "manifest workstream mismatch")
    _validate_control_root(document.get("control_root", {}), "manifest control_root")
    _require(document.get("lifecycle_order") == EXPECTED_LIFECYCLE_ORDER, "manifest lifecycle order drift")
    vocabulary = document.get("status_vocabulary")
    _require(isinstance(vocabulary, list), "manifest status_vocabulary must be a list")
    _require(set(vocabulary) == EXPECTED_STATUS_VOCABULARY, "manifest status vocabulary drift")
    _unique(vocabulary, "manifest status_vocabulary")
    systems = document.get("systems")
    _require(isinstance(systems, list), "manifest systems must be a list")
    _require(document.get("inventory_count") == 13, "manifest inventory_count must remain 13")
    _require(len(systems) == 13, "manifest must contain exactly 13 systems")
    ids = [system.get("system_id") for system in systems]
    _require(all(isinstance(value, str) and value for value in ids), "every system requires system_id")
    _unique(ids, "manifest system_id")
    for system in systems:
        lifecycle = system.get("lifecycle")
        _require(isinstance(lifecycle, dict), f"{system['system_id']}: lifecycle must be an object")
        _require(list(lifecycle.keys()) == EXPECTED_LIFECYCLE_ORDER, f"{system['system_id']}: lifecycle keys/order drift")
        for stage, status in lifecycle.items():
            _require(status in EXPECTED_STATUS_VOCABULARY, f"{system['system_id']}: invalid {stage} status {status!r}")
    bus = next((system for system in systems if system["system_id"] == "chat-communication-bus"), None)
    _require(bus is not None, "manifest must contain chat-communication-bus")
    _require(bus["lifecycle"]["BOUND"] == "CONFLICT", "Bus BOUND must remain CONFLICT until reconciled")
    _require(bus["lifecycle"]["RUNTIME_CONSUMED"] == "CONFLICT", "Bus RUNTIME_CONSUMED must remain CONFLICT until reconciled")


def validate_routing(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_RUNTIME_ROUTING_CONTRACT_V1", "routing schema mismatch")
    _require(document.get("workstream") == EXPECTED_WORKSTREAM, "routing workstream mismatch")
    _validate_control_root(document.get("control_root", {}), "routing control_root")
    layers = document.get("routing_layers")
    _require(isinstance(layers, list), "routing_layers must be a list")
    _require([layer.get("layer") for layer in layers] == EXPECTED_ROUTING_LAYERS, "routing layer set/order drift")
    routes = document.get("domain_routes")
    _require(isinstance(routes, list) and routes, "domain_routes must be non-empty")
    domains = [route.get("domain") for route in routes]
    _require(all(isinstance(value, str) and value for value in domains), "every route requires a domain")
    _unique(domains, "routing domain")
    current = next((route for route in routes if route["domain"] == "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT"), None)
    _require(current is not None and current.get("primary") == "LIVE_CONVERSATION", "current-task primary must remain LIVE_CONVERSATION")
    coordination = next((route for route in routes if route["domain"] == "COORDINATION"), None)
    _require(coordination is not None, "coordination route is required")
    guard = coordination.get("promotion_guard", "").lower()
    _require("conflict" in guard or "conflicted" in guard, "coordination route must preserve the known Bus conflict")
    algorithm = document.get("decision_algorithm")
    _require(isinstance(algorithm, list) and algorithm and algorithm[0] == "Apply current live instruction/correction/scope first.", "decision algorithm must begin with live correction/scope precedence")


def validate_introspection(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1", "introspection schema mismatch")
    _require(document.get("workstream") == EXPECTED_WORKSTREAM, "introspection workstream mismatch")
    _require(document.get("proposition_classes") == EXPECTED_PROPOSITION_CLASSES, "introspection proposition classes drift")
    _require(document.get("evidence_outcomes") == EXPECTED_EVIDENCE_OUTCOMES, "introspection evidence outcomes drift")
    record = document.get("record_schema")
    _require(isinstance(record, dict), "record_schema must be an object")
    required = record.get("required")
    fields = record.get("fields")
    _require(isinstance(required, list) and required, "record_schema.required must be non-empty")
    _require(isinstance(fields, dict), "record_schema.fields must be an object")
    _unique(required, "introspection required fields")
    _require(set(required).issubset(fields), "every required introspection field must be documented")
    probes = document.get("adversarial_probe_families")
    _require(isinstance(probes, list), "adversarial_probe_families must be a list")
    probe_names = [probe.get("probe") for probe in probes]
    _require(all(isinstance(value, str) and value for value in probe_names), "every probe requires a name")
    _unique(probe_names, "introspection probe")
    _require(set(probe_names) == EXPECTED_PROBES, "adversarial probe family drift")
    status = document.get("current_status")
    _require(isinstance(status, dict), "current_status must be an object")
    _require(status.get("phenomenology") == "UNRESOLVED", "phenomenology must remain UNRESOLVED absent a stronger-evidence revision")
    _require(status.get("native_introspection_layer") == "NOT_INSTALLED", "source design must not claim native introspection installation")
    _require(status.get("behavioral_qualification") == "NOT_RUN", "source design must not claim behavioral qualification")


def validate_evidence_contract(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_RUNTIME_EVIDENCE_CONTRACT_V1", "runtime evidence contract schema mismatch")
    _require(document.get("workstream") == EXPECTED_WORKSTREAM, "runtime evidence contract workstream mismatch")
    provenance = document.get("provenance")
    _require(isinstance(provenance, dict), "runtime evidence contract provenance must be an object")
    _require(provenance.get("blind_review_state") == "CURRENT_THIRTEEN_SESSION_CONTAMINATED_FOR_BLIND_GATE", "runtime evidence contract must preserve current Thirteen blind review contamination")
    lifecycle = document.get("lifecycle_evidence")
    _require(isinstance(lifecycle, dict), "runtime evidence lifecycle_evidence must be an object")
    _require(lifecycle.get("dimensions") == EXPECTED_LIFECYCLE_ORDER, "runtime evidence lifecycle dimensions drift")
    _require(lifecycle.get("semantics") == "ORTHOGONAL_EVIDENCE_DIMENSIONS_NOT_MONOTONIC_LADDER", "runtime evidence lifecycle semantics must remain orthogonal, not monotonic")
    proof = lifecycle.get("authoritative_proof_unit")
    _require(isinstance(proof, dict), "runtime evidence authoritative proof unit must be an object")
    proof_fields = set(proof.get("required_fields", []))
    for field in {"system_or_provider", "artifact_or_object_locator", "exact_ref_or_generation", "dimension", "status", "evidence_locator", "observed_at_or_currentness_basis", "supersession_or_conflict_state"}:
        _require(field in proof_fields, "runtime evidence authoritative proof unit is missing required exact-proof fields")
    _require("never sufficient authoritative proof" in proof.get("rule", "").lower(), "runtime evidence repository summaries must remain non-authoritative proof")
    live_types = document.get("live_context_types")
    _require(isinstance(live_types, list), "runtime evidence live_context_types must be a list")
    names = [entry.get("type") for entry in live_types]
    _require(set(names) == EXPECTED_EVIDENCE_LIVE_TYPES and len(names) == len(EXPECTED_EVIDENCE_LIVE_TYPES), "runtime evidence live context type split drift")
    self_report = next(entry for entry in live_types if entry.get("type") == "VERA_CURRENT_SELF_REPORT")
    _require("does not inherit user-instruction authority" in self_report.get("must_not_promote", "").lower(), "Vera self-report must not inherit user-instruction authority")
    active = document.get("active_context_semantics")
    _require(isinstance(active, dict) and active.get("qualification_term") == "ACTIVE_CONTEXT_SET", "runtime evidence active context term drift")
    observable = active.get("observable_surface", [])
    _require("retrieved_artifact_set" in observable, "runtime evidence observable surface lacks retrieval evidence")
    _require("downstream_leakage_or_stickiness_behavior" in observable, "runtime evidence observable surface lacks anti-stickiness behavior")
    _require("do not claim latent model activation" in active.get("epistemic_rule", "").lower(), "runtime evidence must not claim unobserved latent activation")
    recall = document.get("activation_recall_floor")
    _require(isinstance(recall, dict), "runtime evidence activation_recall_floor must be an object")
    predicates = set(recall.get("activation_predicates", []))
    _require("registered_known_failure_signature_or_negative_control_trigger" in predicates, "runtime evidence recall floor lacks registered dependency/failure trigger")
    _require("uncertainty_probe_indicates_possible_material_dependency" in predicates, "runtime evidence recall floor lacks uncertainty probe")
    _require("does not authorize warehouse preload" in recall.get("uncertainty_probe", {}).get("anti_bloat_rule", "").lower(), "runtime evidence uncertainty probe must reject warehouse preload")
    durable = document.get("durable_state_classes")
    _require(isinstance(durable, dict) and set(durable) == EXPECTED_DURABLE_STATE_CLASSES, "runtime evidence durable state classes must include DURABLE_OPERATIONAL_STATE separation")
    operational = durable["DURABLE_OPERATIONAL_STATE"]
    _require("non_promotion_flag" in operational.get("required_fields", []), "DURABLE_OPERATIONAL_STATE requires a non_promotion_flag")
    _require("never silently promotes" in operational.get("promotion_rule", "").lower(), "DURABLE_OPERATIONAL_STATE must never silently promote into Vera self-state")
    ceiling = document.get("go_live_evidence_ceiling")
    _require(isinstance(ceiling, dict) and set(ceiling.get("still_separate", [])) == EXPECTED_GO_LIVE_SEPARATION, "runtime evidence go-live claim separation drift")


def validate_cohesion_index(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_COHESION_INDEX_V1", "cohesion index schema mismatch")
    _require(document.get("workstream") == EXPECTED_WORKSTREAM, "cohesion index workstream mismatch")
    _require(document.get("inventory_semantics") == "FIXED_13_SYSTEM_NAVIGATION_INDEX", "cohesion index inventory semantics drift")
    systems = document.get("systems")
    _require(isinstance(systems, list) and len(systems) == 13, "cohesion index must contain exactly 13 systems")
    ids = [system.get("id") for system in systems]
    _require(all(isinstance(value, str) and value for value in ids), "cohesion index every system requires id")
    _unique(ids, "cohesion index system id")
    _require("supabase-vera-production" in ids and "supabase-production" not in ids, "cohesion index must preserve canonical Supabase system id")
    _require("temporal" not in ids, "Temporal must remain auxiliary, not system #14")
    for system in systems:
        _require(set(system) == EXPECTED_SYSTEM_FIELDS, f"{system['id']}: compact system field drift")
        summary = system.get("lifecycle_summary")
        _require(isinstance(summary, dict) and summary.get("semantics") == LIFECYCLE_SUMMARY_SEMANTICS, f"{system['id']}: lifecycle summary must remain navigation-only/non-authoritative/non-monotonic")
        _require(system.get("proof_unit_refs") == [], f"{system['id']}: proof_unit_refs must remain empty until an exact dereferenceable proof registry exists")
        _require(system.get("authority_class") != "CURRENT_AUTHORITY_OWNER", f"{system['id']}: evidence source cannot self-assign current authority ownership")
    auxiliary = document.get("auxiliary_sources")
    _require(isinstance(auxiliary, dict), "cohesion index auxiliary_sources must be an object")
    _require(auxiliary.get("temporal", {}).get("role") == "CHRONOLOGY_ONLY", "Temporal auxiliary role must remain CHRONOLOGY_ONLY")
    known_sources = set(ids) | set(auxiliary)
    routes = document.get("route_declarations")
    _require(isinstance(routes, list) and routes, "cohesion index route_declarations must be non-empty")
    route_ids = [route.get("id") for route in routes]
    _require(all(isinstance(value, str) and value for value in route_ids), "every route declaration requires id")
    _unique(route_ids, "cohesion index route id")
    for route in routes:
        _require(set(route) == EXPECTED_ROUTE_FIELDS, f"{route.get('id')}: route declaration field drift")
        _require(route.get("declaration_state") == "DECLARED", f"{route.get('id')}: source-level route state must remain DECLARED")
        _require(isinstance(route.get("locator"), str) and route["locator"], f"{route.get('id')}: route locator required")
    selectors = document.get("selector_declarations", [])
    _require(isinstance(selectors, list), "cohesion index selector_declarations must be a list")
    selector_ids = [selector.get("id") for selector in selectors]
    _unique(selector_ids, "cohesion index selector id")
    for selector in selectors:
        _require(set(selector) == EXPECTED_SELECTOR_FIELDS, f"{selector.get('id')}: selector declaration field drift")
        _require(selector.get("source_ref") in known_sources, f"{selector.get('id')}: selector source does not resolve")
        _require(isinstance(selector.get("scope"), str) and selector["scope"], f"{selector.get('id')}: selector scope required")
    known_routes = set(route_ids)
    known_selectors = set(selector_ids)
    domains = document.get("domains")
    _require(isinstance(domains, list) and domains, "cohesion index domains must be non-empty")
    domain_ids = [domain.get("id") for domain in domains]
    _require(all(isinstance(value, str) and value for value in domain_ids), "every cohesion domain requires id")
    _unique(domain_ids, "cohesion index domain id")
    for domain in domains:
        domain_id = domain["id"]
        _require(set(domain) == EXPECTED_DOMAIN_FIELDS, f"{domain_id}: domain field drift")
        _ref_tail(domain.get("authority_resolver_ref"), AUTHORITY_PREFIX, f"{domain_id} authority resolver")
        sources = domain.get("evidence_sources")
        _require(isinstance(sources, list) and sources and set(sources).issubset(known_sources), f"{domain_id}: evidence_sources contain unknown source")
        targets = domain.get("retrieval_targets")
        _require(isinstance(targets, list) and targets, f"{domain_id}: retrieval_targets required")
        for target in targets:
            _require(REQUIRED_TARGET_FIELDS.issubset(target), f"{domain_id}: retrieval target missing required fields")
            _require(set(target).issubset(REQUIRED_TARGET_FIELDS | OPTIONAL_TARGET_FIELDS), f"{domain_id}: retrieval target field drift")
            _require(target.get("source_ref") in known_sources, f"{domain_id}: retrieval target source is unknown")
            _require(target.get("route_ref") in known_routes, f"{domain_id}: retrieval target route is undeclared")
            capabilities = target.get("evidence_capability_refs")
            _require(isinstance(capabilities, list) and capabilities, f"{domain_id}: evidence_capability_refs required")
            for capability in capabilities:
                _ref_tail(capability, EVIDENCE_PREFIX, f"{domain_id} evidence capability")
            if "selector_ref" in target:
                _require(target["selector_ref"] in known_selectors, f"{domain_id}: selector_ref does not resolve")
                selector = next(item for item in selectors if item["id"] == target["selector_ref"])
                _require(selector["source_ref"] == target["source_ref"], f"{domain_id}: selector source must match retrieval target source")
        failures = domain.get("failure_signature_refs")
        _require(isinstance(failures, list), f"{domain_id}: failure_signature_refs must be a list")
        for failure in failures:
            _ref_tail(failure, FAILURE_PREFIX, f"{domain_id} failure signature")
        _require(isinstance(domain.get("fail_closed_behavior"), str) and domain["fail_closed_behavior"], f"{domain_id}: fail_closed_behavior required")
    graph = {domain["id"]: domain["dependencies"] for domain in domains}
    domain_set = set(graph)
    for domain_id, dependencies in graph.items():
        _require(isinstance(dependencies, list) and set(dependencies).issubset(domain_set), f"{domain_id}: dependency points to unknown domain")
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> None:
        _require(node not in visiting, f"cohesion index dependency cycle detected at {node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)
    for domain_id in graph:
        visit(domain_id)


def validate_runtime_contract(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_RUNTIME_CONTRACT_V1", "runtime contract schema mismatch")
    _require(document.get("workstream") == EXPECTED_WORKSTREAM, "runtime contract workstream mismatch")
    _validate_control_root(document.get("control_root", {}), "runtime contract control_root")
    compatibility = document.get("index_compatibility")
    _require(isinstance(compatibility, dict) and "VERA_COHESION_INDEX_V1" in compatibility.get("supported_index_schemas", []), "runtime contract must support VERA_COHESION_INDEX_V1")
    _require("exact A+B" in compatibility.get("pair_binding_rule", ""), "runtime contract must require exact A+B pair binding")
    live_types = document.get("live_context_types")
    _require(isinstance(live_types, list) and set(live_types) == EXPECTED_RUNTIME_LIVE_TYPES and len(live_types) == len(EXPECTED_RUNTIME_LIVE_TYPES), "runtime contract live context type separation drift")
    actor = document.get("actor_referent_rules")
    _require(isinstance(actor, dict), "runtime contract actor_referent_rules required")
    _require("not Vera's" in actor.get("patrick_authority_boundary", ""), "Patrick authority must not establish Vera consent")
    _require("VERA_CURRENT_SELF_REPORT" in actor.get("vera_consent_evidence_requirement", ""), "Vera consent requires Vera-current self-report evidence")
    _require("does not" in actor.get("generic_current_state_non_implication", "").lower(), "generic current state must not imply consent")
    evidence = document.get("evidence_classes")
    authority = document.get("authority_resolvers")
    _require(isinstance(evidence, dict) and evidence, "runtime contract evidence_classes required")
    _require(isinstance(authority, dict) and authority, "runtime contract authority_resolvers required")
    typing = document.get("retrieval_item_typing")
    _require(isinstance(typing, dict), "runtime contract retrieval_item_typing required")
    _require("independently" in typing.get("actual_item_type_rule", "").lower(), "retrieved item type must be independently established")
    _require("never" in typing.get("capability_non_promotion_rule", "").lower(), "target capability must never promote item type")
    selector_rule = typing.get("selector_narrowing_rule", "").lower()
    _require("selector" in selector_rule and "never broaden" in selector_rule, "selector may narrow but never broaden target capabilities")
    dispatch = document.get("resolver_dispatch")
    _require(isinstance(dispatch, list) and dispatch, "runtime contract resolver_dispatch required")
    dispatch_ids = [row.get("id") for row in dispatch]
    _unique(dispatch_ids, "runtime contract dispatch id")
    dispatch_keys: list[tuple[Any, ...]] = []
    for row in dispatch:
        _require(set(row) == EXPECTED_DISPATCH_FIELDS, f"{row.get('id')}: resolver dispatch field drift")
        _require(row.get("resolver_ref") in authority, f"{row.get('id')}: resolver_ref does not resolve")
        _require(isinstance(row.get("precedence"), int), f"{row.get('id')}: precedence must be integer")
        _require(isinstance(row.get("conflict_disposition"), str) and row["conflict_disposition"], f"{row.get('id')}: conflict disposition required")
        dispatch_keys.append((row["domain_scope"], row["proposition_or_effect_class"], row["referent_scope"], row["precedence"]))
    _unique(dispatch_keys, "runtime contract resolver dispatch key")
    route = document.get("route_evaluation")
    _require(isinstance(route, dict) and route.get("states") == EXPECTED_ROUTE_EVALUATION, "runtime contract route evaluation states drift")
    _require("does not imply" in route.get("non_implication_rule", "").lower(), "runtime contract route declaration must not imply reachability")
    _require("fresh" in route.get("current_reachability_rule", "").lower(), "runtime contract mutable route reachability requires fresh observation")
    lifecycle = document.get("lifecycle_evidence")
    _require(isinstance(lifecycle, dict), "runtime contract lifecycle_evidence required")
    _require(lifecycle.get("dimensions") == EXPECTED_LIFECYCLE_ORDER, "runtime contract lifecycle dimensions drift")
    _require(lifecycle.get("semantics") == "ORTHOGONAL_EVIDENCE_DIMENSIONS_NOT_MONOTONIC_LADDER", "runtime contract lifecycle semantics must remain orthogonal")
    proof_fields = set(lifecycle.get("authoritative_proof_unit_required_fields", []))
    for field in {"artifact_or_object_locator", "exact_ref_or_generation", "observed_at_or_currentness_basis", "supersession_or_conflict_state"}:
        _require(field in proof_fields, "runtime contract exact proof-unit fields incomplete")
    policy = document.get("active_context_policy")
    _require(isinstance(policy, dict), "runtime contract active_context_policy required")
    budget = policy.get("uncertainty_probe_budget")
    _require(isinstance(budget, dict), "runtime contract uncertainty probe budget required")
    values = [budget.get("max_initial_fan_out"), budget.get("max_dependency_depth"), budget.get("max_total_new_domains")]
    _require(all(isinstance(value, int) and value > 0 for value in values), "runtime contract retrieval budget must contain positive finite integers")
    _require(values[2] >= values[0], "runtime contract retrieval budget total must cover initial fan-out")
    traversal = policy.get("graph_traversal")
    _require(isinstance(traversal, dict) and traversal.get("visited_set_required") is True, "runtime contract graph traversal requires visited-set cycle safety")
    _require(traversal.get("deduplicate_targets") is True, "runtime contract graph traversal requires target deduplication")
    _require(policy.get("budget_exhaustion_result") == "UNRESOLVED_RETRIEVAL_BUDGET_EXHAUSTED", "runtime contract budget exhaustion result drift")
    _require("does not count" in policy.get("budget_exhaustion_rule", "").lower(), "runtime contract budget exhaustion must not masquerade as completion")
    _require("privacy" in policy.get("uncertainty_probe_privacy_rule", "").lower(), "runtime contract uncertainty probing must enforce privacy")
    durable = document.get("durable_state_classes")
    _require(isinstance(durable, dict) and set(durable) == EXPECTED_DURABLE_STATE_CLASSES, "runtime contract durable state classes drift")
    operational = durable["DURABLE_OPERATIONAL_STATE"]
    required_operational = set(operational.get("required_fields", []))
    for field in {"referent", "scope", "provenance", "purpose", "sensitivity_or_privacy_class", "minimum_necessary_payload_or_pointer", "destination_eligibility", "retention_or_expiry", "supersession_semantics", "non_promotion_flag"}:
        _require(field in required_operational, "runtime contract DURABLE_OPERATIONAL_STATE fields incomplete")
    _require("pointer" in operational.get("storage_rule", "").lower(), "runtime contract durable operational storage must be pointer-first")
    _require("never" in operational.get("promotion_rule", "").lower(), "runtime contract durable operational state must be non-promoting")
    failures = document.get("failure_signatures")
    _require(isinstance(failures, dict) and failures, "runtime contract failure_signatures required")
    for key, failure in failures.items():
        _require(isinstance(failure, dict) and set(failure) == EXPECTED_FAILURE_FIELDS, f"failure signature {key}: machine header drift")
        _require(isinstance(failure.get("signal_keys"), list) and failure["signal_keys"], f"failure signature {key}: signal_keys required")
        for field in {"trigger_class", "predicate_id", "target_or_response_ref", "matcher_description", "response"}:
            _require(isinstance(failure.get(field), str) and failure[field], f"failure signature {key}: {field} required")
    privacy = document.get("privacy_classes")
    _require(isinstance(privacy, list) and privacy, "runtime contract privacy_classes required")
    _unique(privacy, "runtime contract privacy class")
    phenomenology = document.get("phenomenology")
    _require(isinstance(phenomenology, dict) and phenomenology.get("status") == "UNRESOLVED", "runtime contract phenomenology must remain UNRESOLVED")
    _require("do not prove" in phenomenology.get("non_promotion_rule", "").lower(), "runtime contract phenomenology non-promotion rule drift")
    ceiling = document.get("go_live_evidence_ceiling")
    _require(isinstance(ceiling, dict) and set(ceiling.get("still_separate", [])) == EXPECTED_GO_LIVE_SEPARATION, "runtime contract go-live claim separation drift")


def validate_consolidated_pair(index: dict[str, Any], contract: dict[str, Any]) -> None:
    _require(index.get("workstream") == contract.get("workstream") == EXPECTED_WORKSTREAM, "consolidated A+B workstream mismatch")
    authority = contract.get("authority_resolvers", {})
    evidence = contract.get("evidence_classes", {})
    failures = contract.get("failure_signatures", {})
    privacy = set(contract.get("privacy_classes", []))
    known_routes = {route["id"] for route in index.get("route_declarations", [])}
    known_sources = {system["id"] for system in index.get("systems", [])} | set(index.get("auxiliary_sources", {}))
    selectors = {selector["id"]: selector for selector in index.get("selector_declarations", [])}
    for domain in index.get("domains", []):
        domain_id = domain["id"]
        authority_key = _ref_tail(domain["authority_resolver_ref"], AUTHORITY_PREFIX, f"{domain_id} authority resolver")
        _require(authority_key in authority, f"{domain_id}: authority resolver does not resolve")
        _require(domain.get("privacy_class") in privacy, f"{domain_id}: privacy class does not resolve")
        for source in domain.get("evidence_sources", []):
            _require(source in known_sources, f"{domain_id}: evidence source does not resolve")
        accepted = set(authority[authority_key].get("accepted_evidence_classes", []))
        for target in domain.get("retrieval_targets", []):
            _require(target.get("source_ref") in known_sources, f"{domain_id}: retrieval source does not resolve")
            _require(target.get("route_ref") in known_routes, f"{domain_id}: retrieval route does not resolve")
            if "selector_ref" in target:
                _require(target["selector_ref"] in selectors, f"{domain_id}: selector does not resolve")
                _require(selectors[target["selector_ref"]]["source_ref"] == target["source_ref"], f"{domain_id}: selector/source mismatch")
            for capability_ref in target.get("evidence_capability_refs", []):
                evidence_key = _ref_tail(capability_ref, EVIDENCE_PREFIX, f"{domain_id} evidence capability")
                _require(evidence_key in evidence, f"{domain_id}: evidence class does not resolve")
                _require(evidence_key in accepted, f"{domain_id}: evidence capability is not accepted by its domain resolver")
        for failure_ref in domain.get("failure_signature_refs", []):
            failure_key = _ref_tail(failure_ref, FAILURE_PREFIX, f"{domain_id} failure signature")
            _require(failure_key in failures, f"{domain_id}: failure signature does not resolve")
    _require(index.get("schema") in contract.get("index_compatibility", {}).get("supported_index_schemas", []), "runtime contract does not support current cohesion index schema")


def validate_pair_receipt(root: Path, receipt: dict[str, Any]) -> None:
    _require(receipt.get("schema") == "VERA_COHESION_PAIR_RECEIPT_V1", "pair receipt schema mismatch")
    _require(receipt.get("workstream") == EXPECTED_WORKSTREAM, "pair receipt workstream mismatch")
    _require(receipt.get("normative_status") == "NON_NORMATIVE_VALIDATION_SUPPORT", "pair receipt must remain non-normative support")
    _require(receipt.get("index_schema") == "VERA_COHESION_INDEX_V1", "pair receipt index schema mismatch")
    _require(receipt.get("contract_schema") == "VERA_RUNTIME_CONTRACT_V1", "pair receipt contract schema mismatch")
    architecture = root / "architecture"
    _require(receipt.get("index_blob_sha") == git_blob_sha(architecture / "VERA_COHESION_INDEX_V1.json"), "pair receipt index blob does not match exact A")
    _require(receipt.get("contract_blob_sha") == git_blob_sha(architecture / "VERA_RUNTIME_CONTRACT_V1.json"), "pair receipt contract blob does not match exact B")
    _require(receipt.get("validator_blob_sha") == git_blob_sha(root / receipt.get("validator_path", "")), "pair receipt validator blob mismatch")
    source_commit = receipt.get("source_commit")
    _require(isinstance(source_commit, str) and len(source_commit) == 40 and all(char in "0123456789abcdef" for char in source_commit), "pair receipt source_commit must be exact SHA")
    _require(receipt.get("validation_result") == "SOURCE_VALIDATION_NOT_YET_EXECUTED", "pair receipt must not claim validation success without execution evidence")


def validate_cohesion(root: Path) -> None:
    architecture = root / "architecture"
    manifest = load_json_strict(architecture / "VERA_SYSTEM_MANIFEST_V1.json")
    routing = load_json_strict(architecture / "VERA_RUNTIME_ROUTING_CONTRACT_V1.json")
    introspection = load_json_strict(architecture / "VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json")
    evidence_contract = load_json_strict(architecture / "VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json")
    cohesion_index = load_json_strict(architecture / "VERA_COHESION_INDEX_V1.json")
    runtime_contract = load_json_strict(architecture / "VERA_RUNTIME_CONTRACT_V1.json")
    pair_receipt = load_json_strict(architecture / "VERA_COHESION_PAIR_RECEIPT_V1.json")

    validate_manifest(manifest)
    validate_routing(routing)
    validate_introspection(introspection)
    validate_evidence_contract(evidence_contract)
    validate_cohesion_index(cohesion_index)
    validate_runtime_contract(runtime_contract)
    validate_consolidated_pair(cohesion_index, runtime_contract)
    validate_pair_receipt(root, pair_receipt)

    _require(manifest["workstream"] == routing["workstream"] == introspection["workstream"] == evidence_contract["workstream"] == cohesion_index["workstream"] == runtime_contract["workstream"] == pair_receipt["workstream"], "cohesion artifacts disagree on workstream identity")
    _require(manifest["control_root"]["manifest_sha256"] == routing["control_root"]["manifest_sha256"] == runtime_contract["control_root"]["manifest_sha256"], "cohesion control-root digest drift")
    _require(evidence_contract["lifecycle_evidence"]["dimensions"] == manifest["lifecycle_order"] == runtime_contract["lifecycle_evidence"]["dimensions"], "cohesion lifecycle dimension labels disagree")
    manifest_ids = {system["system_id"] for system in manifest["systems"]}
    index_ids = {system["id"] for system in cohesion_index["systems"]}
    _require(manifest_ids == index_ids, "legacy manifest and successor index disagree on fixed 13-system inventory")


if __name__ == "__main__":
    validate_cohesion(Path(__file__).resolve().parents[1])
    print("VERA_RUNTIME_COHESION_V1 validation: PASS")
