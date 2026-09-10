from __future__ import annotations

from threading import RLock
from typing import Any
from weakref import WeakKeyDictionary


_SCOPE_LOCK = RLock()
_BOUND_HOST_SCOPES: WeakKeyDictionary[Any, str] = WeakKeyDictionary()
_CHECKPOINT_REPLAY_HOSTS: WeakKeyDictionary[Any, bool] = WeakKeyDictionary()
_PROVIDER_CURRENT_HOSTS: WeakKeyDictionary[Any, tuple[str, int, object]] = WeakKeyDictionary()
_PROVIDER_BOUND_WRITERS: WeakKeyDictionary[Any, tuple[Any, str, int, object]] = WeakKeyDictionary()


def mark_affective_host_checkpoint_replay(host: Any) -> None:
    """Mark a raw checkpoint-restored host as replay/evidence-only.

    Exact checkpoint bytes and source binding do not establish provider
    lifecycle/currentness. A replay host stays non-live until a provider-current
    attestation is minted by the runtime-owned provider composition after a fresh
    provider read.
    """
    with _SCOPE_LOCK:
        _CHECKPOINT_REPLAY_HOSTS[host] = True


def require_affective_host_cycle_eligible(host: Any) -> None:
    """Reject replay hosts that lack provider-current attestation.

    Generic host-scope binding is deliberately insufficient. This prevents a
    low-level row/checkpoint restore from becoming live merely because caller
    bytes self-label lifecycle_status=CURRENT and carry a plausible scope.
    Fresh, non-replay hosts remain eligible for ephemeral/non-qualifying test
    cycles; production durable status is independently gated on a provider-bound
    writer capability.
    """
    with _SCOPE_LOCK:
        replay_only = bool(_CHECKPOINT_REPLAY_HOSTS.get(host))
        provider_current = _PROVIDER_CURRENT_HOSTS.get(host) is not None
    if replay_only and not provider_current:
        raise ValueError(
            "restored affective host is replay-only; live durable cycle requires fresh provider CURRENT attestation"
        )


def bind_affective_host_scope(host: Any, host_scope: str) -> str:
    """Bind one host object to exactly one durable scope for its lifetime.

    This is an identity/scope consistency binding only. It does NOT establish
    provider CURRENT status and therefore cannot make a replay host cycle-live.
    """
    if not isinstance(host_scope, str) or not host_scope:
        raise ValueError("host_scope is required")
    with _SCOPE_LOCK:
        bound = _BOUND_HOST_SCOPES.get(host)
        if bound is None:
            _BOUND_HOST_SCOPES[host] = host_scope
            return host_scope
        if bound != host_scope:
            raise ValueError("affective host is already bound to a different durable host_scope")
        return bound


def _attest_affective_host_provider_current(
    host: Any,
    *,
    host_scope: str,
    state_version: int,
    attestation_token: object,
) -> None:
    """Internal composition hook for one freshly provider-read host frontier."""
    if isinstance(state_version, bool) or not isinstance(state_version, int) or state_version < 1:
        raise ValueError("provider CURRENT attestation requires positive state_version")
    if attestation_token is None:
        raise ValueError("provider CURRENT attestation token is required")
    bind_affective_host_scope(host, host_scope)
    record = (host_scope, state_version, attestation_token)
    with _SCOPE_LOCK:
        existing = _PROVIDER_CURRENT_HOSTS.get(host)
        if existing is not None and existing != record:
            raise ValueError("affective host already has a different provider CURRENT attestation")
        _PROVIDER_CURRENT_HOSTS[host] = record


def _mark_provider_bound_atomic_writer(
    writer: Any,
    *,
    host: Any,
    host_scope: str,
    state_version: int,
    attestation_token: object,
) -> None:
    """Bind a writer capability to the exact freshly attested host frontier."""
    if not callable(writer):
        raise TypeError("provider-bound atomic writer must be callable")
    with _SCOPE_LOCK:
        current = _PROVIDER_CURRENT_HOSTS.get(host)
        expected = (host_scope, state_version, attestation_token)
        if current != expected:
            raise ValueError("provider-bound writer does not match provider CURRENT host attestation")
        _PROVIDER_BOUND_WRITERS[writer] = (host, host_scope, state_version, attestation_token)


def _provider_bound_atomic_writer_matches(writer: Any, host: Any, host_scope: str) -> bool:
    """Return whether writer and host share the same internal provider attestation."""
    with _SCOPE_LOCK:
        writer_record = _PROVIDER_BOUND_WRITERS.get(writer)
        host_record = _PROVIDER_CURRENT_HOSTS.get(host)
    if writer_record is None or host_record is None:
        return False
    writer_host, writer_scope, writer_version, writer_token = writer_record
    host_scope_record, host_version, host_token = host_record
    return (
        writer_host is host
        and writer_scope == host_scope == host_scope_record
        and writer_version == host_version
        and writer_token is host_token
    )
