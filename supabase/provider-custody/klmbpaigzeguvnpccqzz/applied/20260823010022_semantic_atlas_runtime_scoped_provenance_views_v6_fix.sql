create or replace view semantic_atlas.active_runtime_objects as
select
  o.snapshot_id,
  s.git_commit_sha,
  s.source_branch,
  s.authority_scope,
  s.loaded_at,
  o.object_id,
  o.object_type,
  o.source_path,
  o.payload_sha256,
  o.payload,
  s.git_repository_locator,
  s.git_ref,
  s.materialization_version,
  s.manifest_contract,
  s.attempt_no,
  s.activated_at,
  s.activation_git_repository_locator,
  s.activation_git_readback_sha,
  s.activation_git_readback_at,
  s.activation_git_readback_source,
  s.manifest_sha256,
  s.pathset_sha256,
  s.snapshot_sha256,
  s.expected_object_count,
  s.validated_at,
  s.sealed_at
from semantic_atlas.runtime_objects o
join semantic_atlas.runtime_snapshots s using(snapshot_id)
where s.state='ACTIVE';

create or replace view semantic_atlas.canonical_runtime_objects as
select
  snapshot_id,
  git_commit_sha,
  source_branch,
  authority_scope,
  loaded_at,
  object_id,
  object_type,
  source_path,
  payload_sha256,
  payload,
  git_repository_locator,
  git_ref,
  materialization_version,
  manifest_contract,
  attempt_no,
  activated_at,
  activation_git_repository_locator,
  activation_git_readback_sha,
  activation_git_readback_at,
  activation_git_readback_source,
  manifest_sha256,
  pathset_sha256,
  snapshot_sha256,
  expected_object_count,
  validated_at,
  sealed_at
from semantic_atlas.active_runtime_objects
where authority_scope='CANONICAL_LEDGER';

create or replace view semantic_atlas.research_runtime_objects as
select
  snapshot_id,
  git_commit_sha,
  source_branch,
  authority_scope,
  loaded_at,
  object_id,
  object_type,
  source_path,
  payload_sha256,
  payload,
  git_repository_locator,
  git_ref,
  materialization_version,
  manifest_contract,
  attempt_no,
  activated_at,
  activation_git_repository_locator,
  activation_git_readback_sha,
  activation_git_readback_at,
  activation_git_readback_source,
  manifest_sha256,
  pathset_sha256,
  snapshot_sha256,
  expected_object_count,
  validated_at,
  sealed_at
from semantic_atlas.active_runtime_objects
where authority_scope='RESEARCH_STAGING';