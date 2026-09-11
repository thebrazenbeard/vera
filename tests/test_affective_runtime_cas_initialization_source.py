from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260909181500_close_vera_affective_runtime_first_write_race_v1.sql"


class AffectiveRuntimeCasInitializationSourceTests(unittest.TestCase):
    def test_first_write_cas_serializes_absent_runtime_before_row_read(self):
        self.assertTrue(MIGRATION.exists(), "forward-only CAS race hardening migration is required")
        sql = MIGRATION.read_text(encoding="utf-8").lower()
        runtime_id = sql.index("v_runtime_instance_id := p_state_row->>'runtime_instance_id'")
        row_read = sql.index("select s.state_version", runtime_id)
        pre_read = sql[runtime_id:row_read]

        self.assertIn("pg_advisory_xact_lock", pre_read)
        self.assertIn("hashtextextended(v_runtime_instance_id", pre_read)
        self.assertIn("create or replace function public.vera_affective_runtime_commit_v1", sql)


if __name__ == "__main__":
    unittest.main()
