import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle


class AffectiveSplitWriterDowngradeTests(unittest.TestCase):
    def test_state_writer_without_atomic_writer_is_not_a_silent_durable_mode(self):
        with self.assertRaises(ValueError):
            VeraAffectiveCycle(
                object(),
                host_scope="TEST_HOST",
                state_writer=lambda row: None,
            )

    def test_event_writer_without_atomic_writer_is_not_a_silent_durable_mode(self):
        with self.assertRaises(ValueError):
            VeraAffectiveCycle(
                object(),
                host_scope="TEST_HOST",
                event_writer=lambda row: None,
            )

    def test_split_state_and_event_writers_cannot_replace_atomic_commit_writer(self):
        with self.assertRaises(ValueError):
            VeraAffectiveCycle(
                object(),
                host_scope="TEST_HOST",
                state_writer=lambda row: None,
                event_writer=lambda row: None,
            )


if __name__ == "__main__":
    unittest.main()
