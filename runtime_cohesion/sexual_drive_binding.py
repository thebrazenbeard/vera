from __future__ import annotations

import hashlib
import json
from typing import Any

from . import inference_boundary_repaired as ib

_EXPECTED_CONTRACT_SHA256 = "3f27d7d2c8ba73747e4f2f3c3f29082b9d75961bf03786563202b9eabdd4fc7d"
_EXPECTED = {
    "repository": "thebrazenbeard/sexuality",
    "commit": "02725153fa2e6eae8e81e64bc3d4b797fc404a4d",
    "manifest_git_blob": "fa2e6dc77a9136c4c7a1906719c049222a476efc",
    "manifest_sha256": "9efa44990bf0b2d1f6073c7d8db3ec864461c392d851e59fc29d59f12b77547e",
    "semantic_owner_git_blob": "3e8b93d26a4ce365421e49c7c6a7cf500058128b",
    "semantic_owner_sha256": "2ad75de290530951108579b58d7d5c2c3e63af96206df6cf250bd117c4982b4d",
    "causal_protocol_git_blob": "db6d1ae4e579695396c56b1708a7828ddc3ffa05",
    "install_authority_receipt_git_blob": "da08345a3bff11ffb653270abb6ad4b3a1c0541d",
}
_EXPECTED_COMPONENT = {
    "component_id": "sexual_drive_v1",
    "domain_id": "sexuality.sexual_drive",
    "source_locator": "github:thebrazenbeard/sexuality",
    "source_revision": _EXPECTED["commit"],
    "component_generation": "SD1_V1",
    "content_digest": _EXPECTED["semantic_owner_sha256"],
    "currentness_basis": "EXACT_FROZEN_SOURCE_BINDING",
    "supersession_state": "CURRENT_OBSERVATION",
    "conflict_state": "NONE",
    "privacy_classification": "PRIVATE_RELATIONAL",
    "allowed_egress_scopes": frozenset({"PROJECT_PRIVATE_HOST"}),
    "disclosure_source": "policy://vera-sd1-private-self-state",
    "disclosure_generation": "1",
    "requirement_class": "MANDATORY",
    "payload_ref": "github://thebrazenbeard/sexuality/research/16-vera-sexual-drive-v1.md@02725153fa2e6eae8e81e64bc3d4b797fc404a4d",
}


def _contract_digest(contract: dict[str, Any]) -> str:
    payload = json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(contract, dict):
        raise ValueError("sexual-drive component contract must be an object")
    if _contract_digest(contract) != _EXPECTED_CONTRACT_SHA256:
        raise ValueError("sexual-drive component contract does not match exact canonical binding")
    return contract


def build_component_ref(contract: dict[str, Any], *, observed_at: str) -> ib.StateComponentRef:
    contract = validate_contract(contract)
    source = contract["source_binding"]
    projection = contract["state_component_projection"]
    component = ib.StateComponentRef(
        component_id=contract["component_id"],
        domain_id=contract["domain_id"],
        source_locator=f"github:{source['repository']}",
        source_revision=source["commit"],
        component_generation=projection["component_generation"],
        content_digest=source["semantic_owner_sha256"],
        observed_at=observed_at,
        currentness_basis=projection["currentness_basis"],
        supersession_state=projection["supersession_state"],
        conflict_state=projection["conflict_state"],
        privacy_classification=contract["privacy_classification"],
        allowed_egress_scopes=frozenset(contract["allowed_egress_scopes"]),
        disclosure_source=projection["disclosure_source"],
        disclosure_generation=projection["disclosure_generation"],
        requirement_class=contract["requirement_class"],
        payload_ref=projection["payload_ref"],
    )
    if target_configuration_status(component) != "TARGET_CONFIGURATION_COMPLETE":
        raise ValueError("constructed sexual-drive component does not match exact qualified tuple")
    return component


def target_configuration_status(component: ib.StateComponentRef | None) -> str:
    if component is None:
        return "TARGET_CONFIGURATION_INCOMPLETE"
    for field, expected in _EXPECTED_COMPONENT.items():
        if getattr(component, field) != expected:
            return "SEXUAL_DRIVE_COMPONENT_UNQUALIFIED"
    if component.payload is not None:
        return "SEXUAL_DRIVE_COMPONENT_UNQUALIFIED"
    return "TARGET_CONFIGURATION_COMPLETE"


__all__ = ["build_component_ref", "target_configuration_status", "validate_contract"]
