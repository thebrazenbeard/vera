-- Vera Supabase foreign-key index repair plan V1
-- Status: SOURCE PREPARATION ONLY / NOT APPLIED TO PROVIDER
-- Observed project: klmbpaigzeguvnpccqzz
-- Observed advisor state: 21 application-owned unindexed foreign keys
-- Generated from live pg_constraint/pg_index readback on 2026-09-21.
--
-- IMPORTANT:
-- This file is intentionally under supabase/repair-plans rather than
-- supabase/migrations. Before production application, materialize it into a
-- migration using the current Supabase CLI workflow, review exact provider
-- currentness again, and obtain Patrick's exact authorization for the live DDL.
--
-- No auth/storage/system-table indexes are included.

create index if not exists idx_bt2_memory_events_task_id_fk
  on build_team_2.memory_events (task_id);

create index if not exists idx_bt2_role_ops_checkpoint_qualification_fk
  on build_team_2.role_operational_checkpoints (qualification_id);

create index if not exists idx_bt2_role_ops_checkpoint_training_subject_fk
  on build_team_2.role_operational_checkpoints
  (role_key, training_package_version, training_source_set_digest_sha256);

create index if not exists idx_bt2_role_training_current_subject_fk
  on build_team_2.role_training_current
  (role_key, package_version, source_set_digest_sha256);

create index if not exists idx_bt2_role_training_qual_subject_fk
  on build_team_2.role_training_qualifications
  (role_key, package_version, source_set_digest_sha256);

create index if not exists idx_brigit_save_state_supersession_parent_fk
  on public.brigit_save_state_supersession_edges (parent_record_id);

create index if not exists idx_vera_mem_archive_admission_receipt_fk
  on public.vera_memory_epoch_archive_receipts_v1 (admission_receipt_id);

create index if not exists idx_vera_mem_archive_drive_receipt_fk
  on public.vera_memory_epoch_archive_receipts_v1 (drive_receipt_id);

create index if not exists idx_vera_mem_archive_supabase_receipt_fk
  on public.vera_memory_epoch_archive_receipts_v1 (supabase_receipt_id);

create index if not exists idx_vera_mem_archive_subject_fk
  on public.vera_memory_epoch_archive_receipts_v1
  (subject_id, project_id, branch_id, logical_memory_id, epoch_id);

create index if not exists idx_vera_mem_provider_subject_fk
  on public.vera_memory_epoch_provider_receipts_v1
  (subject_id, project_id, branch_id, logical_memory_id, epoch_id);

create index if not exists idx_vera_optional_invocation_runtime_instance_fk
  on public.vera_optional_invocation_test_events_v1 (runtime_instance_id);

create index if not exists idx_vera_bootstrap_bindings_request_project_fk
  on public.vera_portable_bootstrap_bindings
  (request_claim_id, project_instance_id);

create index if not exists idx_vera_bootstrap_events_predecessor_request_attempt_fk
  on public.vera_portable_bootstrap_events
  (predecessor_event_id, request_claim_id, attempt_id);

create index if not exists idx_vera_bootstrap_readback_request_project_fk
  on public.vera_portable_bootstrap_readback_confirmations
  (request_claim_id, project_instance_id);

create index if not exists idx_vera_save_state_supersession_parent_fk
  on public.vera_save_state_supersession_edges (parent_record_id);

create index if not exists idx_radar_identity_visuals_supersedes_fk
  on radar.identity_visuals (supersedes);

create index if not exists idx_redworm_lineage_state_holder_runtime_fk
  on redworm.lineage_state (holder_runtime_token);

create index if not exists idx_redworm_lineage_state_transfer_fk
  on redworm.lineage_state (transfer_id);

create index if not exists idx_redworm_succession_source_runtime_fk
  on redworm.succession_transfers (source_runtime_token);

create index if not exists idx_redworm_succession_successor_runtime_fk
  on redworm.succession_transfers (successor_runtime_token);
