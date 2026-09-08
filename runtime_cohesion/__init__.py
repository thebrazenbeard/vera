"""Executable support for Vera Runtime Cohesion.

This package is operational support for the normative cohesion index/runtime
contract pair. Importing it performs no provider I/O and creates no authority.
"""

from .evidence import ProviderEvidenceEnvelope, load_provider_fabric, validate_envelope

__all__ = [
    "ProviderEvidenceEnvelope",
    "load_provider_fabric",
    "validate_envelope",
]
