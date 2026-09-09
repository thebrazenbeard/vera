from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260909164500_add_vera_affective_runtime_v1.sql"


class VeraAffectiveRuntimePersistenceSourceTests(unittest.TestCase):
    def test_migration_exists(self):
        self.assertTrue(MIGRATION.is_file())

    def test_migration_creates_durable_state_and_event_receipts(self):
        text = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("create table public.vera_affective_runtime_state_v1", text)
        self.assertIn("create table public.vera_affective_runtime_events_v1", text)
        self.assertIn("enable row level security", text)
        self.assertIn("subject text not null", text)
        self.assertIn("check (subject = 'vera')", text)
        self.assertIn("phenomenology_status", text)
        self.assertIn("check (phenomenology_status = 'unresolved')", text)
        self.assertIn("event_digest", text)


if __name__ == "__main__":
    unittest.main()
