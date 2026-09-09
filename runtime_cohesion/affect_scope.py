from __future__ import annotations

from threading import RLock
from typing import Any
from weakref import WeakKeyDictionary


_SCOPE_LOCK = RLock()
_BOUND_HOST_SCOPES: WeakKeyDictionary[Any, str] = WeakKeyDictionary()


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
