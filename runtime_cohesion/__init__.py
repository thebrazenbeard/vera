"""Executable support for Vera Runtime Cohesion.

This package is operational support for the normative cohesion index/runtime
contract pair. Importing it performs no provider I/O and creates no authority.
Provider I/O occurs only when a runtime explicitly invokes registered adapters.

The public ``audit_registered_projections`` surface cannot mint
production-equivalent VERIFIED_EXACT from caller-supplied observation metadata.
An exact candidate survives only when the exact live envelope objects already
carry runtime-owned provider/object/event provenance established at the read
boundary. Public proposition admission is provider-strict; lightweight policy
fixtures use the explicitly named abstract evaluator.
"""

from .adapters import AdapterProbeResult, AdapterRegistry, AdapterRequest, ProviderAdapter
from .audit import ProjectionAuditResult, audit_registered_projections
from .evidence import ProviderEvidenceEnvelope, load_provider_fabric, validate_envelope
from .executor import (
    DomainExecutionResult,
    GoverningResolutionRecord,
    ProjectionExecutionResult,
    execute_domain_cycle,
    execute_projection_cycle,
)
from .failure import FailureEvaluationResult, evaluate_failure_signature, validate_failure_wiring
from .provider_admission import evaluate_provider_proposition_admission
from .reconcile import ReconciliationResult, reconcile_exact
from .runtime import (
    AdmissionDecision,
    RetrievalPlan,
    build_operational_checkpoint,
    build_retrieval_plan,
    evaluate_abstract_proposition_admission,
)

# Public package-level admission is provider-strict. Lightweight policy fixtures
# remain available only through the explicitly named abstract evaluator.
evaluate_proposition_admission = evaluate_provider_proposition_admission

__all__ = [
    "AdapterProbeResult",
    "AdapterRegistry",
    "AdapterRequest",
    "ProviderAdapter",
    "ProjectionAuditResult",
    "audit_registered_projections",
    "ProviderEvidenceEnvelope",
    "load_provider_fabric",
    "validate_envelope",
    "DomainExecutionResult",
    "GoverningResolutionRecord",
    "ProjectionExecutionResult",
    "execute_domain_cycle",
    "execute_projection_cycle",
    "FailureEvaluationResult",
    "evaluate_failure_signature",
    "validate_failure_wiring",
    "ReconciliationResult",
    "reconcile_exact",
    "AdmissionDecision",
    "RetrievalPlan",
    "build_operational_checkpoint",
    "build_retrieval_plan",
    "evaluate_proposition_admission",
    "evaluate_provider_proposition_admission",
    "evaluate_abstract_proposition_admission",
]
