-- Promoted from the reviewed temporal pilot draft at commit
-- 8ae8256378a158e74b51bb5baed59d2eb87f8f42.
-- Do not apply to production until the separately governed production gate is authorized.

begin;

alter table public.vera_save_state_events
  add column event_time_precision text not null default 'APPROXIMATE';

alter table public.vera_save_state_events
  add constraint vera_save_state_events_event_time_precision_check
  check (event_time_precision in ('EXACT', 'APPROXIMATE'));

alter table public.vera_save_state_events
  alter column event_time set not null;

comment on column public.vera_save_state_events.event_time is
  'Time of the record-producing event. For live records this should normally be close to record_time. Historical timing referenced by the event belongs in source-qualified payload data.';

comment on column public.vera_save_state_events.event_time_precision is
  'EXACT when the event itself has a trustworthy machine timestamp; APPROXIMATE when the event is reliably placed near the timestamp without claiming exact sub-second precision.';

comment on column public.vera_save_state_events.record_time is
  'Time Supabase persisted the external record.';

commit;
