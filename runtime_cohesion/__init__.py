"""Executable support for Vera Runtime Cohesion.

This package is operational support for the normative cohesion index/runtime
contract pair. Importing it performs no provider I/O and creates no authority.
Provider I/O occurs only when a runtime explicitly invokes registered adapters.
"""

from .adapters import AdapterProbeResult, AdapterRegistry, AdapterRequest, ProviderAdapter
from .audit import ProjectionAuditResult, audit_registered_projections
from .evidence import ProviderEvidenceEnvelope, load_provider_fabric, validate_envelope
from .executor import DomainExecutionResult, execute_domain_cycle
from .reconcile import ReconciliationResult, reconcile_exact
from .runtime import RetrievalPlan, build_operational_checkpoint, build_retrieval_plan

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
    "execute_domain_cycle",
    "ReconciliationResult",
    "reconcile_exact",
    "RetrievalPlan",
    "build_operational_checkpoint",
    "build_retrieval_plan",
]
