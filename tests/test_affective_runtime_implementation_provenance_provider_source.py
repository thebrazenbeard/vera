from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"


class AffectiveRuntimeImplementationProvenanceProviderSourceTests(unittest.TestCase):
    def migration_source(self):
        return "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(MIGRATIONS.glob("*vera_affective_runtime*.sql"))
        ).lower()

    def test_state_and_event_provider_schema_carry_runtime_implementation_cut(self):
        sql = self.migration_source()
        self.assertIn("runtime_implementation_cut", sql)
        self.assertIn("alter table public.vera_affective_runtime_state_v1", sql)
        self.assertIn("alter table public.vera_affective_runtime_events_v1", sql)
        self.assertIn("thebrazenbeard/vera", sql)
        for path in (
            "runtime_cohesion/__init__.py",
            "runtime_cohesion/orgasm.py",
            "runtime_cohesion/affect_host.py",
            "runtime_cohesion/affect_cycle.py",
            "runtime_cohesion/affect_persistence.py",
            "runtime_cohesion/affect_scope.py",
        ):
            self.assertIn(path, sql)

    def test_atomic_commit_requires_state_cut_and_exact_event_cut_match(self):
        sql = self.migration_source()
        self.assertIn("runtime implementation cut is required", sql)
        self.assertIn("runtime implementation commit is required", sql)
        self.assertIn(
            "v_event->'runtime_implementation_cut' is distinct from p_state_row->'runtime_implementation_cut'",
            sql,
        )
        self.assertIn("event runtime implementation cut does not match state row", sql)


if __name__ == "__main__":
    unittest.main()
