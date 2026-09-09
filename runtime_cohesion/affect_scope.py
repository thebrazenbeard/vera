from __future__ import annotations

from threading import RLock
from typing import Any
from weakref import WeakKeyDictionary


_SCOPE_LOCK = RLock()
_BOUND_HOST_SCOPES: WeakKeyDictionary[Any, str] = WeakKeyDictionary()
_CHECKPOINT_REPLAY_HOSTS: WeakKeyDictionary[Any, bool] = WeakKeyDictionary()


def mark_affective_host_checkpoint_replay(host: Any) -> None:
    """Mark a raw checkpoint-restored host as replay/evidence-only.

    An exact checkpoint digest proves checkpoint bytes and source binding. It does
    not prove provider lifecycle, CURRENT generation, or durable host scope, so a
    raw checkpoint restore must not enter a live durable cycle by first binding
    caller-supplied scope/version values.
    """
    with _SCOPE_LOCK:
        _CHECKPOINT_REPLAY_HOSTS[host] = True


def require_affective_host_cycle_eligible(host: Any) -> None:
    """Reject unattested raw-checkpoint hosts at the public live cycle boundary.

    The validated provider-row restore path binds its exact host scope before it
    returns the host. A raw checkpoint restore has no such binding, so it remains
    replay-only. Fresh hosts are also unbound, but are not checkpoint restores and
    may establish their first durable scope when a new cycle is constructed.
    """
    with _SCOPE_LOCK:
        replay_only = bool(_CHECKPOINT_REPLAY_HOSTS.get(host))
        provider_scope_bound = _BOUND_HOST_SCOPES.get(host) is not None
    if replay_only and not provider_scope_bound:
        raise ValueError(
            "raw checkpoint restore is replay-only; live durable cycle requires provider CURRENT scope attestation"
        )


def bind_affective_host_scope(host: Any, host_scope: str) -> str:
    """Bind one host object to exactly one durable scope for its lifetime.

    The binding is held outside the mutable host attribute namespace so callers
    cannot rewrite a trust-bearing scope by assigning an arbitrary host field.
    Rebinding the same host to a different scope fails closed.
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
