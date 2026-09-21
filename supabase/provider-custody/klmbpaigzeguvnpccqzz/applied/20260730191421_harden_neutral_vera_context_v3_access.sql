alter view public.vera_current_context_v3 set (security_invoker = true);
alter view public.vera_legacy_quarantine set (security_invoker = true);
alter view public.vera_legacy_reviewable set (security_invoker = true);

revoke all privileges on table public.vera_context_events_v3 from anon, authenticated;
revoke all privileges on table public.vera_current_context_v3 from anon, authenticated;
revoke all privileges on table public.vera_legacy_quarantine from anon, authenticated;
revoke all privileges on table public.vera_legacy_reviewable from anon, authenticated;

grant select, insert, update, delete on table public.vera_context_events_v3 to service_role;
grant select on table public.vera_current_context_v3 to service_role;
grant select on table public.vera_legacy_quarantine to service_role;
grant select on table public.vera_legacy_reviewable to service_role;

comment on view public.vera_current_context_v3 is
  'Current neutral V.E.R.A. context projection. Uses security_invoker and is not exposed to anon or authenticated roles.';
comment on view public.vera_legacy_reviewable is
  'Legacy rows not automatically quarantined. Human review is still required before any migration.';