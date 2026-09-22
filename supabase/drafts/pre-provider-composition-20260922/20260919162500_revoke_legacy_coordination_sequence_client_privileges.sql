begin;

-- Security hardening for vera#54.
-- The legacy coordination table is already client-denied, but its backing
-- identity sequence still grants rwU to anon/authenticated in production.
-- Preserve postgres/service_role sequence access; remove only public clients.

revoke all privileges on sequence
  public.vera_coordination_events_event_sequence_seq
  from public, anon, authenticated;

commit;
