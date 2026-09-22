-- Source-only hardening for Datum V2 mutation RPCs.
-- Current provider readback shows these SECURITY INVOKER functions still inherit
-- EXECUTE for PUBLIC/anon/authenticated even though client roles lack underlying
-- table DML privileges. Remove the ambient invocation surface without changing
-- read-only Datum V2 RPC exposure.

revoke all on function public.vera_register_datum_v2(
  text,text,text,text,text,jsonb,jsonb,text[],jsonb,text,text
) from public, anon, authenticated;
grant execute on function public.vera_register_datum_v2(
  text,text,text,text,text,jsonb,jsonb,text[],jsonb,text,text
) to service_role;

revoke all on function public.vera_mark_datum_referenced_v2(uuid)
  from public, anon, authenticated;
grant execute on function public.vera_mark_datum_referenced_v2(uuid)
  to service_role;

revoke all on function public.vera_mark_datum_verified_v2(
  uuid,jsonb,text,text,jsonb,uuid,text[],jsonb
) from public, anon, authenticated;
grant execute on function public.vera_mark_datum_verified_v2(
  uuid,jsonb,text,text,jsonb,uuid,text[],jsonb
) to service_role;

revoke all on function public.vera_mark_datum_rejected_v2(uuid,text,jsonb)
  from public, anon, authenticated;
grant execute on function public.vera_mark_datum_rejected_v2(uuid,text,jsonb)
  to service_role;

revoke all on function public.vera_mark_datum_unverifiable_v2(uuid,text,jsonb)
  from public, anon, authenticated;
grant execute on function public.vera_mark_datum_unverifiable_v2(uuid,text,jsonb)
  to service_role;
