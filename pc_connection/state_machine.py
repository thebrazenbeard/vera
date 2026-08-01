from __future__ import annotations

from enum import Enum


class StateTransitionError(ValueError):
    """Raised when a job lifecycle transition is not legal."""


class JobState(str, Enum):
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    CANCELLATION_REQUESTED = "CANCELLATION_REQUESTED"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    DEAD_LETTER = "DEAD_LETTER"


class JobEvent(str, Enum):
    CLAIM = "CLAIM"
    START = "START"
    REQUEST_CANCELLATION = "REQUEST_CANCELLATION"
    ACKNOWLEDGE_CANCELLATION = "ACKNOWLEDGE_CANCELLATION"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"
    LEASE_EXPIRE = "LEASE_EXPIRE"
    REQUEUE = "REQUEUE"
    DEAD_LETTER = "DEAD_LETTER"
    EXPIRE_UNCLAIMED = "EXPIRE_UNCLAIMED"


TERMINAL_STATES = frozenset(
    {
        JobState.SUCCEEDED,
        JobState.FAILED,
        JobState.CANCELLED,
        JobState.EXPIRED,
        JobState.DEAD_LETTER,
    }
)

_STATIC_TRANSITIONS: dict[tuple[JobState, JobEvent], JobState] = {
    (JobState.QUEUED, JobEvent.CLAIM): JobState.CLAIMED,
    (JobState.QUEUED, JobEvent.REQUEST_CANCELLATION):
        JobState.CANCELLATION_REQUESTED,
    (JobState.QUEUED, JobEvent.EXPIRE_UNCLAIMED): JobState.EXPIRED,
    (JobState.CLAIMED, JobEvent.START): JobState.RUNNING,
    (JobState.CLAIMED, JobEvent.REQUEST_CANCELLATION):
        JobState.CANCELLATION_REQUESTED,
    (JobState.CLAIMED, JobEvent.COMPLETE): JobState.SUCCEEDED,
    (JobState.CLAIMED, JobEvent.FAIL): JobState.FAILED,
    (JobState.CLAIMED, JobEvent.LEASE_EXPIRE): JobState.LEASE_EXPIRED,
    (JobState.RUNNING, JobEvent.REQUEST_CANCELLATION):
        JobState.CANCELLATION_REQUESTED,
    (JobState.RUNNING, JobEvent.COMPLETE): JobState.SUCCEEDED,
    (JobState.RUNNING, JobEvent.FAIL): JobState.FAILED,
    (JobState.RUNNING, JobEvent.LEASE_EXPIRE): JobState.LEASE_EXPIRED,
    (JobState.CANCELLATION_REQUESTED, JobEvent.ACKNOWLEDGE_CANCELLATION):
        JobState.CANCELLED,
    (JobState.CANCELLATION_REQUESTED, JobEvent.COMPLETE):
        JobState.SUCCEEDED,
    (JobState.CANCELLATION_REQUESTED, JobEvent.FAIL):
        JobState.FAILED,
    (JobState.CANCELLATION_REQUESTED, JobEvent.LEASE_EXPIRE):
        JobState.LEASE_EXPIRED,
}


def transition(
    state: JobState | str,
    event: JobEvent | str,
    *,
    attempt_number: int,
    max_attempts: int,
) -> JobState:
    """Return the next state or fail closed.

    Cancellation intent is not cancellation completion. A job reaches
    CANCELLED only after an explicit host acknowledgement. A late completion
    after cancellation request remains truthfully SUCCEEDED.
    """

    try:
        current = JobState(state)
        observed_event = JobEvent(event)
    except ValueError as exc:
        raise StateTransitionError("unknown state or event") from exc

    if isinstance(attempt_number, bool) or not isinstance(attempt_number, int):
        raise StateTransitionError("attempt_number must be an integer")
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
        raise StateTransitionError("max_attempts must be an integer")
    if attempt_number < 0 or max_attempts < 1 or attempt_number > max_attempts:
        raise StateTransitionError("invalid attempt bounds")
    if current in TERMINAL_STATES:
        raise StateTransitionError(f"terminal state {current.value} is immutable")

    if current == JobState.LEASE_EXPIRED:
        if observed_event == JobEvent.REQUEUE and attempt_number < max_attempts:
            return JobState.QUEUED
        if (
            observed_event == JobEvent.DEAD_LETTER
            and attempt_number >= max_attempts
        ):
            return JobState.DEAD_LETTER
        raise StateTransitionError(
            "expired lease must requeue before max attempts or dead-letter "
            "at the limit"
        )

    target = _STATIC_TRANSITIONS.get((current, observed_event))
    if target is None:
        raise StateTransitionError(
            f"illegal transition: {current.value} + {observed_event.value}"
        )
    return target


__all__ = [
    "JobEvent",
    "JobState",
    "StateTransitionError",
    "TERMINAL_STATES",
    "transition",
]
