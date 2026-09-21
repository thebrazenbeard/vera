-- Make the existing deny-all RLS posture explicit on every table currently
-- reported by Supabase lint 0008 (RLS enabled, no policy).
--
-- Semantics are intentionally unchanged for ordinary roles: without a policy,
-- RLS already denies them. These explicit PUBLIC false policies document and
-- regress that boundary while preserving PostgreSQL/Supabase BYPASSRLS behavior
-- for trusted backend roles such as service_role and superuser-owned maintenance.
--
-- No grants are added and no RLS setting is weakened.

create policy deny_all_untrusted_v1
  on public.vera_affective_runtime_events_v1
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_affective_runtime_state_v1
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_memory_epoch_archive_receipts_v1
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_memory_epoch_events_v1
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_memory_epoch_provider_receipts_v1
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_memory_epoch_subjects_v1
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_optional_invocation_route_evidence_v1
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_optional_invocation_test_events_v1
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_portable_bootstrap_bindings
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_portable_bootstrap_events
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_portable_bootstrap_readback_confirmations
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_portable_bootstrap_requests
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on public.vera_save_state_supersession_edges
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.assignment_events
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.assignments
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.dead_letters
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.dependencies
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.endpoints
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.health_events
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.identities
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.identity_visuals
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.messages
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.nodes
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.reconciliation_events
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.subscriptions
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on radar.telemetry
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on semantic_atlas.capture_policy
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on semantic_atlas.runtime_objects
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on semantic_atlas.runtime_snapshots
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on semantic_atlas.semantic_capture_events
  for all to public using (false) with check (false);

create policy deny_all_untrusted_v1
  on semantic_atlas.semantic_capture_outcomes
  for all to public using (false) with check (false);
