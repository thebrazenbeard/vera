begin;

-- Restore the privacy posture already required by the canonical save-state
-- lineage source after later provider-side view recreation dropped
-- security_invoker and reintroduced default client grants.
--
-- This migration intentionally does not rewrite view definitions or data.

alter view public.vera_save_state_heads
  set (security_invoker = true);

alter view public.vera_save_state_head_status
  set (security_invoker = true);

alter view public.vera_current_save_state
  set (security_invoker = true);

revoke all privileges on table public.vera_save_state_heads
  from public, anon, authenticated;
revoke all privileges on table public.vera_save_state_head_status
  from public, anon, authenticated;
revoke all privileges on table public.vera_current_save_state
  from public, anon, authenticated;
revoke all privileges on table public.vera_save_state_supersession_edges
  from public, anon, authenticated;

-- Service reads remain explicit and least-privilege. Underlying event-table
-- service access is governed separately by the existing save-state contract.
revoke all privileges on table public.vera_save_state_heads from service_role;
revoke all privileges on table public.vera_save_state_head_status from service_role;
revoke all privileges on table public.vera_current_save_state from service_role;
revoke all privileges on table public.vera_save_state_supersession_edges from service_role;

grant select on table public.vera_save_state_heads to service_role;
grant select on table public.vera_save_state_head_status to service_role;
grant select on table public.vera_current_save_state to service_role;
grant select on table public.vera_save_state_supersession_edges to service_role;

commit;
