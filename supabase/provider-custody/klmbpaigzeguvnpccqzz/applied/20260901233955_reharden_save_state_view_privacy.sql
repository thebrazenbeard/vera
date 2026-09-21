begin;

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

revoke all privileges on table public.vera_save_state_heads from service_role;
revoke all privileges on table public.vera_save_state_head_status from service_role;
revoke all privileges on table public.vera_current_save_state from service_role;
revoke all privileges on table public.vera_save_state_supersession_edges from service_role;

grant select on table public.vera_save_state_heads to service_role;
grant select on table public.vera_save_state_head_status to service_role;
grant select on table public.vera_current_save_state to service_role;
grant select on table public.vera_save_state_supersession_edges to service_role;

commit;