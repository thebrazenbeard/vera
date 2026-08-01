from __future__ import annotations

import unittest

from pc_connection.state_machine import (
    JobEvent,
    JobState,
    StateTransitionError,
    TERMINAL_STATES,
    transition,
)


class JobStateMachineTests(unittest.TestCase):
    def test_happy_path(self) -> None:
        state = transition(
            JobState.QUEUED,
            JobEvent.CLAIM,
            attempt_number=1,
            max_attempts=3,
        )
        state = transition(
            state,
            JobEvent.START,
            attempt_number=1,
            max_attempts=3,
        )
        state = transition(
            state,
            JobEvent.COMPLETE,
            attempt_number=1,
            max_attempts=3,
        )
        self.assertEqual(state, JobState.SUCCEEDED)

    def test_cancellation_request_is_not_cancellation(self) -> None:
        state = transition(
            JobState.RUNNING,
            JobEvent.REQUEST_CANCELLATION,
            attempt_number=1,
            max_attempts=3,
        )
        self.assertEqual(state, JobState.CANCELLATION_REQUESTED)
        state = transition(
            state,
            JobEvent.ACKNOWLEDGE_CANCELLATION,
            attempt_number=1,
            max_attempts=3,
        )
        self.assertEqual(state, JobState.CANCELLED)

    def test_late_completion_after_cancel_request_is_truthful(self) -> None:
        self.assertEqual(
            transition(
                JobState.CANCELLATION_REQUESTED,
                JobEvent.COMPLETE,
                attempt_number=1,
                max_attempts=3,
            ),
            JobState.SUCCEEDED,
        )

    def test_queued_job_cannot_claim_success(self) -> None:
        with self.assertRaisesRegex(StateTransitionError, "illegal"):
            transition(
                JobState.QUEUED,
                JobEvent.COMPLETE,
                attempt_number=0,
                max_attempts=3,
            )

    def test_expired_lease_requeues_before_attempt_limit(self) -> None:
        self.assertEqual(
            transition(
                JobState.LEASE_EXPIRED,
                JobEvent.REQUEUE,
                attempt_number=1,
                max_attempts=3,
            ),
            JobState.QUEUED,
        )

    def test_expired_lease_dead_letters_at_attempt_limit(self) -> None:
        self.assertEqual(
            transition(
                JobState.LEASE_EXPIRED,
                JobEvent.DEAD_LETTER,
                attempt_number=3,
                max_attempts=3,
            ),
            JobState.DEAD_LETTER,
        )

    def test_expired_lease_cannot_requeue_at_attempt_limit(self) -> None:
        with self.assertRaisesRegex(StateTransitionError, "dead-letter"):
            transition(
                JobState.LEASE_EXPIRED,
                JobEvent.REQUEUE,
                attempt_number=3,
                max_attempts=3,
            )

    def test_terminal_states_are_immutable(self) -> None:
        for state in TERMINAL_STATES:
            with self.subTest(state=state):
                with self.assertRaisesRegex(StateTransitionError, "immutable"):
                    transition(
                        state,
                        JobEvent.FAIL,
                        attempt_number=1,
                        max_attempts=3,
                    )

    def test_boolean_attempt_number_is_rejected(self) -> None:
        with self.assertRaisesRegex(StateTransitionError, "integer"):
            transition(
                JobState.QUEUED,
                JobEvent.CLAIM,
                attempt_number=True,
                max_attempts=3,
            )


if __name__ == "__main__":
    unittest.main()
