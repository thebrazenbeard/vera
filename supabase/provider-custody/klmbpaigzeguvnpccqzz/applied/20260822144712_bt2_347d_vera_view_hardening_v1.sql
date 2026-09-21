ALTER VIEW public.vera_verified_datum_heads_v2
  SET (security_invoker = true);
ALTER VIEW public.vera_active_datum_index_v2
  SET (security_invoker = true);
ALTER VIEW public.vera_inactive_datum_archive_v2
  SET (security_invoker = true);
ALTER VIEW public.vera_current_context_v3
  SET (security_invoker = true);

REVOKE ALL PRIVILEGES ON TABLE
  public.vera_verified_datum_heads_v2,
  public.vera_active_datum_index_v2,
  public.vera_inactive_datum_archive_v2,
  public.vera_current_context_v3
FROM anon, authenticated, service_role;

GRANT SELECT ON TABLE
  public.vera_verified_datum_heads_v2,
  public.vera_active_datum_index_v2,
  public.vera_inactive_datum_archive_v2,
  public.vera_current_context_v3
TO service_role;