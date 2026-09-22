create or replace view public.vera_current_context_v3 as
select distinct on (project_id, branch_id, record_key)
  record_id,
  project_id,
  branch_id,
  record_key,
  record_type,
  statement,
  lifecycle_status,
  epistemic_status,
  source_actor,
  privacy_scope,
  event_time,
  state_time,
  record_time,
  supersedes_record_id,
  legacy_record_id,
  payload,
  source_evidence,
  semantic_tags,
  limitations,
  notes,
  datum_expires_at,
  datum_verified_at
from public.vera_context_events_v3
order by project_id, branch_id, record_key, state_time desc, record_time desc, record_id desc;