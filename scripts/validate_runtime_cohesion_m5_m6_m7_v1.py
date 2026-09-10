#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
FABRIC_PATH = ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json"
HOOK_PATH = ROOT / "architecture" / "VERA_RUNTIME_COHESION_NATIVE_HOOK_V1.json"
AUDIT_PATH = ROOT / "runtime_cohesion" / "audit.py"
EXECUTOR_PATH = ROOT / "runtime_cohesion" / "executor.py"
RECONCILE_PATH = ROOT / "runtime_cohesion" / "reconcile.py"
ITEM_TYPING_PATH = ROOT / "runtime_cohesion" / "item_typing.py"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    fabric = load(FABRIC_PATH)
    hook = load(HOOK_PATH)
    audit_text = AUDIT_PATH.read_text(encoding="utf-8")
    executor_text = EXECUTOR_PATH.read_text(encoding="utf-8")
    reconcile_text = RECONCILE_PATH.read_text(encoding="utf-8")
    typing_text = ITEM_TYPING_PATH.read_text(encoding="utf-8")

    audit_rule = str(hook.get("operations", {}).get("PROJECTION_AUDIT", {}).get("rule", "")).lower()
    if "cannot mint verified_exact" not in audit_rule or "runtime-owned" not in audit_rule:
        errors.append("native hook must deny caller-supplied VERIFIED_EXACT and require runtime-owned event provenance")
    if "validated_item_event_binding" not in audit_text:
        errors.append("projection audit must consume the runtime-owned item/event provenance boundary")
    if "event_binding_validated" in audit_text:
        errors.append("projection audit must not accept a caller-controlled event-binding boolean")
    if "return audit_registered_projections(fabric, observations)" not in audit_text:
        errors.append("internal audit compatibility helper must carry no qualification privilege over the public audit")
    if "_audit_registered_projections_qualifying" not in executor_text:
        errors.append("projection executor must route through the shared audit surface after its read/event checks")

    if "validated_item_type(request, envelope)" not in executor_text:
        errors.append("executor _validate_read must require independently validated item typing")
    if "derived.derived_evidence_class != envelope.evidence_class" not in executor_text:
        errors.append("executor must compare independently derived item type against envelope claim")
    if "derived.derived_evidence_class not in _allowed_evidence_classes(request)" not in executor_text:
        errors.append("executor capability ceiling must be checked against independently derived item type")
    lower_typing = typing_text.lower()
    if "capability set is intentionally ignored" not in lower_typing:
        errors.append("item typing module must preserve capability non-promotion semantics")
    if "request.domain_id" in typing_text or "envelope.referent" in typing_text:
        errors.append("lowest-level item origin/type verifier must remain below domain-specific referent policy")
    if "proof.event_ref, request.event_ref" not in typing_text or "proof.event_path, request.event_path" not in typing_text:
        errors.append("item provenance proof must cross-bind exact projection event ref/path when present")
    if "content-sensitive item typing requires an exact content_digest" not in typing_text:
        errors.append("content-sensitive item typing must conditionally require an exact content digest")
    if "receipt-sensitive item typing requires an exact receipt_ref" not in typing_text:
        errors.append("receipt-sensitive item typing must conditionally require an exact receipt identity")
    if 'envelope.scope == "PROVIDER_RECEIPT"' not in typing_text:
        errors.append("provider receipt items must enforce receipt-sensitive provenance requirements")
    if "verifier outputs derived from provider/object evidence" not in lower_typing:
        errors.append("item typing source must state currentness labels are cross-checks, not derivation")

    modes = fabric.get("comparison_modes", {})
    receipt_mode = str(modes.get("EXACT_RECEIPT", "")).lower()
    if "not target revision equality" not in receipt_mode:
        errors.append("EXACT_RECEIPT fabric semantics must distinguish receipt proof from target revision equality")
    if "schema/type" not in receipt_mode or "receipt object/digest" not in receipt_mode:
        errors.append("EXACT_RECEIPT fabric semantics must bind receipt schema/type and receipt object digest")

    receipt_rows = [row for row in fabric.get("projections", []) if row.get("comparison_mode") == "EXACT_RECEIPT"]
    if len(receipt_rows) != 1:
        errors.append("expected exactly one EXACT_RECEIPT projection in V1 fabric")
    else:
        binding = receipt_rows[0].get("receipt_binding")
        expected_fields = {
            "receipt_schema",
            "receipt_type",
            "source_subject",
            "target_subject",
            "source_locator",
            "source_revision",
            "source_content_digest",
            "event_ref",
            "event_path",
            "receipt_ref",
            "receipt_digest",
        }
        if not isinstance(binding, dict):
            errors.append("EXACT_RECEIPT projection requires receipt_binding")
        else:
            if binding.get("target_scope") != "PROVIDER_RECEIPT":
                errors.append("receipt_binding target_scope must be PROVIDER_RECEIPT")
            if binding.get("metadata_field") != "receipt_binding":
                errors.append("receipt_binding metadata_field must be receipt_binding")
            if binding.get("receipt_schema") != "VERA_MEMORY_EPOCH_PROVIDER_RECEIPT_V1":
                errors.append("receipt_binding must name the exact V1 memory-epoch provider receipt schema")
            if binding.get("receipt_type") != "GOOGLE_DRIVE_DURABLE":
                errors.append("receipt_binding must name the exact Google Drive durable receipt type")
            if binding.get("digest_algorithm") != "SHA256_CANONICAL_JSON_EXCLUDING_RECEIPT_DIGEST":
                errors.append("receipt_binding must declare canonical SHA-256 receipt digest semantics")
            if set(binding.get("required_fields", [])) != expected_fields:
                errors.append("receipt_binding required_fields do not bind exact schema/type/receipt/event/object identity")

    if "def reconcile_exact_receipt(" not in reconcile_text:
        errors.append("EXACT_RECEIPT requires a separate reconcile_exact_receipt implementation")
    if "_canonical_receipt_binding_digest" not in reconcile_text:
        errors.append("receipt reconciler must recompute canonical receipt-binding digest")
    if "source receipt_ref was not required" not in reconcile_text:
        errors.append("target receipt must prove the source without requiring the source object to know downstream receipt identity")
    if "source.receipt_ref is not None and source.receipt_ref != target.receipt_ref" not in reconcile_text:
        errors.append("optional source receipt_ref must be cross-checked only when independently present")
    if "source.receipt_ref is None or target.receipt_ref is None" in reconcile_text:
        errors.append("source receipt_ref must not be a prerequisite for downstream receipt proof")
    if "target revision equality was not used" not in reconcile_text:
        errors.append("receipt reconciler must explicitly avoid target revision equality as proof")
    if "target.content_digest != receipt_digest" not in reconcile_text:
        errors.append("receipt reconciler must bind the target receipt object digest to canonical receipt semantics")

    rules = fabric.get("global_rules", {})
    item_rule = str(rules.get("returned_item_typing", "")).lower()
    if "runtime-owned verifier" not in item_rule or "capability" not in item_rule or "not item type" not in item_rule:
        errors.append("provider fabric must bind independent item typing and capability non-promotion")
    conflict_rule = str(rules.get("conflict", "")).lower()
    for term in ("wrong-schema/type", "receipt-digest/locator"):
        if term not in conflict_rule:
            errors.append(f"provider fabric EXACT_RECEIPT conflict rule lacks {term}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VERA Runtime Cohesion M5/M6/M7 source closure: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
