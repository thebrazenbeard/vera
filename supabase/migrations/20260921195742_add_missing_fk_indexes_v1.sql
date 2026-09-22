-- Resolve Supabase performance advisor lint 0001 (unindexed foreign keys)
-- for the 21 currently reported Vera project constraints.
--
-- These are ordinary btree indexes whose leading columns exactly match each
-- foreign-key column sequence. No existing/unused indexes are dropped here:
-- the separate unused_index advisor is observational and does not prove that
-- an index is safe to remove.

create index bt2_memory_events_task_id_fkey_idx
  on build_team_2.memory_events (task_id);

create index bt2_roc_qualification_id_fkey_idx
  on build_team_2.role_operational_checkpoints (qualification_id);

create index bt2_roc_training_package_fkey_idx
  on build_team_2.role_operational_checkpoints
  (role_key, training_package_version, training_source_set_digest_sha256);

create index bt2_role_training_current_package_fkey_idx
  on build_team_2.role_training_current
  (role_key, package_version, source_set_digest_sha256);

create index bt2_role_training_qualifications_package_fkey_idx
  on build_team_2.role_training_qualifications
  (role_key, package_version, source_set_digest_sha256);

create index brigit_save_state_edges_parent_fkey_idx
  on public.brigit_save_state_supersession_edges (parent_record_id);

create index vera_memory_archive_admission_receipt_fkey_idx
  on public.vera_memory_epoch_archive_receipts_v1 (admission_receipt_id);

create index vera_memory_archive_drive_receipt_fkey_idx
  on public.vera_memory_epoch_archive_receipts_v1 (drive_receipt_id);

create index vera_memory_archive_supabase_receipt_fkey_idx
  on public.vera_memory_epoch_archive_receipts_v1 (supabase_receipt_id);

create index vera_memory_archive_subject_fkey_idx
  on public.vera_memory_epoch_archive_receipts_v1
  (subject_id, project_id, branch_id, logical_memory_id, epoch_id);

create index vera_memory_provider_subject_fkey_idx
  on public.vera_memory_epoch_provider_receipts_v1
  (subject_id, project_id, branch_id, logical_memory_id, epoch_id);

create index vera_optional_invocation_runtime_fkey_idx
  on public.vera_optional_invocation_test_events_v1 (runtime_instance_id);

create index portable_bootstrap_bindings_request_fkey_idx
  on public.vera_portable_bootstrap_bindings (request_claim_id, project_instance_id);

create index portable_bootstrap_events_predecessor_fkey_idx
  on public.vera_portable_bootstrap_events
  (predecessor_event_id, request_claim_id, attempt_id);

create index portable_bootstrap_readback_request_fkey_idx
  on public.vera_portable_bootstrap_readback_confirmations
  (request_claim_id, project_instance_id);

create index vera_save_state_edges_parent_fkey_idx
  on public.vera_save_state_supersession_edges (parent_record_id);

create index radar_identity_visuals_supersedes_fkey_idx
  on radar.identity_visuals (supersedes);

create index redworm_lineage_holder_runtime_fkey_idx
  on redworm.lineage_state (holder_runtime_token);

create index redworm_lineage_transfer_fkey_idx
  on redworm.lineage_state (transfer_id);

create index redworm_transfer_source_runtime_fkey_idx
  on redworm.succession_transfers (source_runtime_token);

create index redworm_transfer_successor_runtime_fkey_idx
  on redworm.succession_transfers (successor_runtime_token);
