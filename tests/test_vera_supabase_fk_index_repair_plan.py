from __future__ import annotations

import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL = ROOT / "supabase/repair-plans/VERA_SUPABASE_FK_INDEX_REPAIR_V1.sql"
MANIFEST = ROOT / "supabase/repair-plans/VERA_SUPABASE_FK_INDEX_REPAIR_V1.json"

EXPECTED_INDEXES = {
    "idx_bt2_memory_events_task_id_fk",
    "idx_bt2_role_ops_checkpoint_qualification_fk",
    "idx_bt2_role_ops_checkpoint_training_subject_fk",
    "idx_bt2_role_training_current_subject_fk",
    "idx_bt2_role_training_qual_subject_fk",
    "idx_brigit_save_state_supersession_parent_fk",
    "idx_vera_mem_archive_admission_receipt_fk",
    "idx_vera_mem_archive_drive_receipt_fk",
    "idx_vera_mem_archive_supabase_receipt_fk",
    "idx_vera_mem_archive_subject_fk",
    "idx_vera_mem_provider_subject_fk",
    "idx_vera_optional_invocation_runtime_instance_fk",
    "idx_vera_bootstrap_bindings_request_project_fk",
    "idx_vera_bootstrap_events_predecessor_request_attempt_fk",
    "idx_vera_bootstrap_readback_request_project_fk",
    "idx_vera_save_state_supersession_parent_fk",
    "idx_radar_identity_visuals_supersedes_fk",
    "idx_redworm_lineage_state_holder_runtime_fk",
    "idx_redworm_lineage_state_transfer_fk",
    "idx_redworm_succession_source_runtime_fk",
    "idx_redworm_succession_successor_runtime_fk",
}


class VeraSupabaseFkIndexRepairPlanTests(unittest.TestCase):
    def test_manifest_binds_exact_live_finding_count(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("SOURCE_PREPARED_NOT_APPLIED", data["status"])
        self.assertEqual("klmbpaigzeguvnpccqzz", data["provider"]["project_id"])
        self.assertEqual(21, data["advisor"]["reported_count"])
        self.assertEqual(21, len(data["observations"]))
        self.assertFalse(data["provider_effect"]["applied"])
        self.assertFalse(data["provider_effect"]["readback_verified"])

    def test_sql_contains_exactly_21_idempotent_index_creations(self):
        text = SQL.read_text(encoding="utf-8")
        names = re.findall(
            r"create\s+index\s+if\s+not\s+exists\s+([a-z0-9_]+)",
            text,
            flags=re.IGNORECASE,
        )
        self.assertEqual(21, len(names))
        self.assertEqual(EXPECTED_INDEXES, set(names))
        self.assertEqual(len(names), len(set(names)))

    def test_plan_excludes_supabase_managed_system_schemas(self):
        text = SQL.read_text(encoding="utf-8").lower()
        self.assertNotRegex(text, r"\bon\s+auth\.")
        self.assertNotRegex(text, r"\bon\s+storage\.")

    def test_plan_is_index_only_ddl(self):
        text = SQL.read_text(encoding="utf-8")
        stripped = "\n".join(
            line for line in text.splitlines()
            if not line.lstrip().startswith("--")
        ).lower()
        for forbidden in (
            " drop ",
            " alter ",
            " grant ",
            " revoke ",
            " insert ",
            " update ",
            " delete ",
            " truncate ",
            " create table ",
            " create function ",
            " create policy ",
        ):
            self.assertNotIn(forbidden, f" {stripped} ")

    def test_index_names_fit_postgres_identifier_limit(self):
        for name in EXPECTED_INDEXES:
            self.assertLessEqual(len(name.encode("utf-8")), 63)


if __name__ == "__main__":
    unittest.main()
