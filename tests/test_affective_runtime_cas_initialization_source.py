from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260909175000_harden_vera_affective_runtime_integrity_v1.sql"


class AffectiveRuntimeCasInitializationSourceTests(unittest.TestCase):
    def test_first_write_cas_serializes_absent_runtime_before_row_read(self):
        sql = MIGRATION.read_text(encoding="utf-8").lower()
        runtime_id = sql.index("v_runtime_instance_id := p_state_row->>'runtime_instance_id'")
        lock = sql.index("pg_advisory_xact_lock", runtime_id)
        row_read = sql.index("select s.state_version", runtime_id)

        self.assertLess(lock, row_read)
        self.assertIn("hashtextextended(v_runtime_instance_id", sql[lock:row_read])


if __name__ == "__main__":
    unittest.main()
