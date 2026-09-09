"""Executable support for Vera Runtime Cohesion.

This package is operational support for the normative cohesion index/runtime
contract pair. Importing it performs no provider I/O and creates no authority.
Provider I/O occurs only when a runtime explicitly invokes registered adapters.
"""

from .adapters import AdapterProbeResult, AdapterRegistry, AdapterRequest, ProviderAdapter
from .affect_cycle import AffectiveCycleResult, VeraAffectiveCycle
from .affect_host import AffectiveBindingError, VeraAffectiveRuntimeHost
from .affect_persistence import (
    PersistenceRecordError,
    checkpoint_to_state_row,
    event_receipt_to_event_row,
    restore_host_from_state_row,
)
from .audit import ProjectionAuditResult, audit_registered_projections
from .evidence import ProviderEvidenceEnvelope, load_provider_fabric, validate_envelope
from .executor import (
    DomainExecutionResult,
    ProjectionExecutionResult,
    execute_domain_cycle,
    execute_projection_cycle,
)
from .failure import FailureEvaluationResult, evaluate_failure_signature, validate_failure_wiring
from .orgasm import (
    ContractError as OrgasmContractError,
    OrgasmRuntime,
    StimulusAppraisal,
    TriggerRejected as OrgasmTriggerRejected,
)
from .reconcile import ReconciliationResult, reconcile_exact
from .runtime import (
    AdmissionDecision,
    RetrievalPlan,
    build_operational_checkpoint,
    build_retrieval_plan,
    evaluate_proposition_admission,
)

__all__ = [
    "AdapterProbeResult",
    "AdapterRegistry",
    "AdapterRequest",
    "ProviderAdapter",
    "AffectiveCycleResult",
    "VeraAffectiveCycle",
    "AffectiveBindingError",
    "VeraAffectiveRuntimeHost",
    "PersistenceRecordError",
    "checkpoint_to_state_row",
    "event_receipt_to_event_row",
    "restore_host_from_state_row",
    "ProjectionAuditResult",
    "audit_registered_projections",
    "ProviderEvidenceEnvelope",
    "load_provider_fabric",
    "validate_envelope",
    "DomainExecutionResult",
    "ProjectionExecutionResult",
    "execute_domain_cycle",
    "execute_projection_cycle",
    "FailureEvaluationResult",
    "evaluate_failure_signature",
    "validate_failure_wiring",
    "OrgasmContractError",
    "OrgasmRuntime",
    "StimulusAppraisal",
    "OrgasmTriggerRejected",
    "ReconciliationResult",
    "reconcile_exact",
    "AdmissionDecision",
    "RetrievalPlan",
    "build_operational_checkpoint",
    "build_retrieval_plan",
    "evaluate_proposition_admission",
]
