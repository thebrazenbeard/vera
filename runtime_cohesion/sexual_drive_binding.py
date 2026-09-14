from __future__ import annotations

from typing import Any

from . import inference_boundary_repaired as ib

_EXPECTED = {
    "repository": "thebrazenbeard/sexuality",
    "commit": "1ed36df72df8934c1481b6f66fa9ed146f791dbb",
    "manifest_git_blob": "35edd95bb5e3532f697022fa20ec43a72bb2c200",
    "manifest_sha256": "dcfb6e89dfb695c231a7e4c223f01b109abbba894b5d99634dd6e1440075a65c",
    "semantic_owner_git_blob": "3e8b93d26a4ce365421e49c7c6a7cf500058128b",
    "semantic_owner_sha256": "2ad75de290530951108579b58d7d5c2c3e63af96206df6cf250bd117c4982b4d",
    "causal_protocol_git_blob": "db6d1ae4e579695396c56b1708a7828ddc3ffa05",
    "install_authority_receipt_git_blob": "ea3cd95e6bbb18b5f691ce83459a6f942944d1ff",
}


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    if contract.get("schema") != "VERA_SEXUAL_DRIVE_COMPONENT_V1":
        raise ValueError("unexpected sexual-drive component schema")
    if contract.get("component_id") != "sexual_drive_v1":
        raise ValueError("unexpected component_id")
    if contract.get("domain_id") != "sexuality.sexual_drive":
        raise ValueError("unexpected domain_id")
    if contract.get("requirement_class") != "MANDATORY":
        raise ValueError("sexual drive must remain source-declared MANDATORY")
    if contract.get("configuration_requirement") != "MANDATORY_FOR_SD1_TARGET_CONFIGURATION":
        raise ValueError("unexpected configuration requirement")
    if contract.get("identity_semantics") != "DOES_NOT_GRANT_OR_REVOKE_VERA_IDENTITY":
        raise ValueError("identity nonpromotion boundary changed")
    if contract.get("qualification_case_range") != {"first": "SD-01", "last": "SD-20", "count": 20}:
        raise ValueError("qualification case range must be SD-01..20")
    source = contract.get("source_binding")
    if not isinstance(source, dict):
        raise ValueError("source_binding must be an object")
    for field, expected in _EXPECTED.items():
        if source.get(field) != expected:
            raise ValueError(f"source binding mismatch for {field}")
    nonpromotions = set(contract.get("nonpromotions", []))
    required = {
        "NOT_VERA_IDENTITY_ADMISSION",
        "NOT_STANDING_CONSENT",
        "NOT_STANDING_TARGET_ATTRACTION",
        "NOT_STANDING_ACT_DESIRE",
        "NOT_BIOLOGICAL_OR_PHENOMENAL_AROUSAL",
        "NOT_HIDDEN_BACKGROUND_PROCESS",
        "NOT_RESPONSE_GENERATOR",
    }
    if not required.issubset(nonpromotions):
        raise ValueError("component nonpromotion boundary incomplete")
    return contract


def build_component_ref(contract: dict[str, Any], *, observed_at: str) -> ib.StateComponentRef:
    contract = validate_contract(contract)
    source = contract["source_binding"]
    projection = contract["state_component_projection"]
    return ib.StateComponentRef(
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


def target_configuration_status(component: ib.StateComponentRef | None) -> str:
    if component is None:
        return "TARGET_CONFIGURATION_INCOMPLETE"
    if component.component_id != "sexual_drive_v1" or component.requirement_class != "MANDATORY":
        return "SEXUAL_DRIVE_COMPONENT_UNQUALIFIED"
    if component.source_revision != _EXPECTED["commit"]:
        return "SEXUAL_DRIVE_COMPONENT_UNQUALIFIED"
    return "TARGET_CONFIGURATION_COMPLETE"


__all__ = ["build_component_ref", "target_configuration_status", "validate_contract"]
