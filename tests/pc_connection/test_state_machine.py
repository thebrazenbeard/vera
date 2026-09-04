from __future__ import annotations

import unittest

from pc_connection.state_machine import (
    AttemptEvent,
    AttemptState,
    CancellationEvent,
    CancellationState,
    JobEvent,
    JobState,
    SideEffectStatus,
    StateTransitionError,
    TransitionGuards,
    transition_attempt,
    transition_cancellation,
    transition_job,
)


def guards(**changes) -> TransitionGuards:
    values = {
        "state_version": 3,
        "expected_state_version": 3,
        "lease_current": False,
        "fence_current": False,
        "attempts_remaining": False,
        "side_effect_status": SideEffectStatus.NONE,
        "independent_readback": False,
        "no_newer_attempt": False,
        "cancellation_state": CancellationState.NONE,
        "safe_to_expire": False,
    }
    values.update(changes)
    return TransitionGuards(**values)


class JobStateTests(unittest.TestCase):
    def test_authorization_to_running_path(self) -> None:
        state = transition_job(
            JobState.SUBMITTED,
            JobEvent.REQUEST_AUTHORIZATION,
            guards=guards(),
        )
        state = transition_job(
            state,
            JobEvent.AUTHORIZE,
            guards=guards(),
        )
        state = transition_job(
            state,
            JobEvent.QUEUE,
            guards=guards(),
        )
        state = transition_job(
            state,
            JobEvent.CLAIM,
            guards=guards(),
        )
        state = transition_job(
            state,
            JobEvent.START,
            guards=guards(
                lease_current=True,
                fence_current=True,
            ),
        )
        state = transition_job(
            state,
            JobEvent.COMPLETE,
            guards=guards(
                lease_current=True,
                fence_current=True,
            ),
        )
        self.assertEqual(state, JobState.SUCCEEDED)

    def test_claimed_cannot_succeed_directly(self) -> None:
        with self.assertRaisesRegex(StateTransitionError, "RUNNING"):
            transition_job(
                JobState.CLAIMED,
                JobEvent.COMPLETE,
                guards=guards(
                    lease_current=True,
                    fence_current=True,
                ),
            )

    def test_running_ambiguous_lease_expiry_requires_recovery(self) -> None:
        self.assertEqual(
            transition_job(
                JobState.RUNNING,
                JobEvent.LEASE_EXPIRE,
                guards=guards(
                    attempts_remaining=True,
                    side_effect_status=SideEffectStatus.UNKNOWN,
                ),
            ),
            JobState.RECOVERY_REQUIRED,
        )

    def test_recovery_success_requires_independent_readback(self) -> None:
        with self.assertRaisesRegex(StateTransitionError, "readback"):
            transition_job(
                JobState.RECOVERY_REQUIRED,
                JobEvent.RECOVER_SUCCESS,
                guards=guards(
                    side_effect_status=SideEffectStatus.CONFIRMED,
                ),
            )
        self.assertEqual(
            transition_job(
                JobState.RECOVERY_REQUIRED,
                JobEvent.RECOVER_SUCCESS,
                guards=guards(
                    side_effect_status=SideEffectStatus.CONFIRMED,
                    independent_readback=True,
                    no_newer_attempt=True,
                ),
            ),
            JobState.SUCCEEDED,
        )

    def test_cancellation_request_is_intent_for_active_job(self) -> None:
        self.assertEqual(
            transition_job(
                JobState.RUNNING,
                JobEvent.REQUEST_CANCEL,
                guards=guards(),
            ),
            JobState.RUNNING,
        )
        with self.assertRaisesRegex(
            StateTransitionError,
            "not requested",
        ):
            transition_job(
                JobState.RUNNING,
                JobEvent.ACK_CANCEL,
                guards=guards(
                    lease_current=True,
                    fence_current=True,
                ),
            )
        self.assertEqual(
            transition_job(
                JobState.RUNNING,
                JobEvent.ACK_CANCEL,
                guards=guards(
                    lease_current=True,
                    fence_current=True,
                    cancellation_state=CancellationState.STOPPING,
                ),
            ),
            JobState.CANCELLED,
        )

    def test_early_job_cancels_without_attempt(self) -> None:
        self.assertEqual(
            transition_job(
                JobState.QUEUED,
                JobEvent.REQUEST_CANCEL,
                guards=guards(),
            ),
            JobState.CANCELLED,
        )

    def test_state_version_conflict_fails(self) -> None:
        with self.assertRaisesRegex(
            StateTransitionError,
            "state_version",
        ):
            transition_job(
                JobState.QUEUED,
                JobEvent.CLAIM,
                guards=guards(expected_state_version=2),
            )

    def test_terminal_job_is_immutable(self) -> None:
        with self.assertRaisesRegex(StateTransitionError, "immutable"):
            transition_job(
                JobState.SUCCEEDED,
                JobEvent.REQUEST_CANCEL,
                guards=guards(),
            )


class AttemptStateTests(unittest.TestCase):
    def test_attempt_requires_starting_before_running(self) -> None:
        state = transition_attempt(
            AttemptState.CLAIMED,
            AttemptEvent.PREPARE_START,
            lease_current=True,
            fence_current=True,
        )
        state = transition_attempt(
            state,
            AttemptEvent.START,
            lease_current=True,
            fence_current=True,
        )
        state = transition_attempt(
            state,
            AttemptEvent.COMPLETE,
            lease_current=True,
            fence_current=True,
        )
        self.assertEqual(state, AttemptState.SUCCEEDED)

    def test_stale_fence_fails(self) -> None:
        with self.assertRaisesRegex(StateTransitionError, "fence"):
            transition_attempt(
                AttemptState.RUNNING,
                AttemptEvent.COMPLETE,
                lease_current=True,
                fence_current=False,
            )


class CancellationStateTests(unittest.TestCase):
    def test_full_cancellation_path(self) -> None:
        state = transition_cancellation(
            CancellationState.NONE,
            CancellationEvent.REQUEST,
        )
        state = transition_cancellation(
            state,
            CancellationEvent.OBSERVE,
        )
        state = transition_cancellation(
            state,
            CancellationEvent.BEGIN_STOP,
        )
        state = transition_cancellation(
            state,
            CancellationEvent.ACKNOWLEDGE,
        )
        self.assertEqual(state, CancellationState.ACKNOWLEDGED)

    def test_acknowledged_is_terminal(self) -> None:
        with self.assertRaisesRegex(StateTransitionError, "illegal"):
            transition_cancellation(
                CancellationState.ACKNOWLEDGED,
                CancellationEvent.REQUEST,
            )


if __name__ == "__main__":
    unittest.main()
