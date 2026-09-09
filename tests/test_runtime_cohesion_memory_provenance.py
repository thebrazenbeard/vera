import unittest

from runtime_cohesion.live_sources import classify_memory_epoch_object


class MemoryEpochProvenanceTests(unittest.TestCase):
    def test_nested_not_autobiographical_limitation_blocks_autobiographical_candidate(self):
        decision = classify_memory_epoch_object({
            "memory_class": "AUTOBIOGRAPHICAL",
            "provenance": {
                "epistemic_class": "DOCUMENTED_SOURCE",
                "limitations": ["NOT_AUTOBIOGRAPHICAL_MEMORY"],
            },
        })
        self.assertEqual(decision["status"], "PERSISTED_PROVENANCE_CONFLICT")
        self.assertFalse(decision["autobiographical_admission_eligible"])
        self.assertFalse(decision["present_state_established"])

    def test_nested_synthetic_qualification_limitation_remains_synthetic(self):
        decision = classify_memory_epoch_object({
            "memory_class": "AUTOBIOGRAPHICAL",
            "provenance": {
                "epistemic_class": "DOCUMENTED_SOURCE",
                "limitations": ["SYNTHETIC_QUALIFICATION_ONLY"],
            },
        })
        self.assertEqual(decision["status"], "PERSISTED_SYNTHETIC_FIXTURE")
        self.assertFalse(decision["autobiographical_admission_eligible"])
        self.assertFalse(decision["present_state_established"])

    def test_unlimited_autobiographical_payload_remains_only_a_persisted_candidate(self):
        decision = classify_memory_epoch_object({
            "memory_class": "AUTOBIOGRAPHICAL",
            "provenance": {
                "epistemic_class": "DOCUMENTED_SOURCE",
                "limitations": [],
            },
        })
        self.assertEqual(decision["status"], "AUTOBIOGRAPHICAL_CANDIDATE_PERSISTED")
        self.assertTrue(decision["autobiographical_admission_eligible"])
        self.assertFalse(decision["present_state_established"])


if __name__ == "__main__":
    unittest.main()
