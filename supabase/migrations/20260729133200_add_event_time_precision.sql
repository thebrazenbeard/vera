-- Promoted from the reviewed temporal pilot draft at commit
-- 8ae8256378a158e74b51bb5baed59d2eb87f8f42.
-- Reconciled to the active R5A2 temporal precision model after independent audit.
-- Do not apply to production until the separately governed production gate is authorized.

begin;

alter table public.vera_save_state_events
  add column event_time_precision text not null default 'APPROXIMATE',
  add column event_time_lower_bound timestamptz,
  add column event_time_upper_bound timestamptz;

alter table public.vera_save_state_events
  add constraint vera_save_state_events_event_time_precision_check
  check (event_time_precision in ('EXACT', 'BOUNDED', 'APPROXIMATE', 'UNKNOWN'));

alter table public.vera_save_state_events
  add constraint vera_save_state_events_event_time_bounds_check
  check (
    (
      event_time_precision = 'BOUNDED'
      and event_time_lower_bound is not null
      and event_time_upper_bound is not null
      and event_time_lower_bound <= event_time_upper_bound
      and event_time between event_time_lower_bound and event_time_upper_bound
    )
    or
    (
      event_time_precision <> 'BOUNDED'
      and event_time_lower_bound is null
      and event_time_upper_bound is null
    )
  );

alter table public.vera_save_state_events
  alter column event_time set not null;

comment on column public.vera_save_state_events.event_time is
  'Best supported timestamp for the record-producing event. For BOUNDED evidence it must fall within event_time_lower_bound and event_time_upper_bound.';

comment on column public.vera_save_state_events.event_time_precision is
  'R5A2 temporal evidence confidence: EXACT, BOUNDED, APPROXIMATE, or UNKNOWN. RANGE is not a precision class.';

comment on column public.vera_save_state_events.event_time_lower_bound is
  'Inclusive earliest supported timestamp when event_time_precision is BOUNDED; otherwise NULL.';

comment on column public.vera_save_state_events.event_time_upper_bound is
  'Inclusive latest supported timestamp when event_time_precision is BOUNDED; otherwise NULL.';

comment on column public.vera_save_state_events.record_time is
  'Time Supabase persisted the external record.';

commit;
