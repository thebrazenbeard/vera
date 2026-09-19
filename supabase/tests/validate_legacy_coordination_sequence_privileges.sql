-- Read-only post-migration validation for vera#54.
-- This query does not call nextval()/setval() and does not mutate sequence state.

select
  (
    not has_sequence_privilege(
      'anon',
      'public.vera_coordination_events_event_sequence_seq',
      'USAGE'
    )
    and not has_sequence_privilege(
      'anon',
      'public.vera_coordination_events_event_sequence_seq',
      'SELECT'
    )
    and not has_sequence_privilege(
      'anon',
      'public.vera_coordination_events_event_sequence_seq',
      'UPDATE'
    )
    and not has_sequence_privilege(
      'authenticated',
      'public.vera_coordination_events_event_sequence_seq',
      'USAGE'
    )
    and not has_sequence_privilege(
      'authenticated',
      'public.vera_coordination_events_event_sequence_seq',
      'SELECT'
    )
    and not has_sequence_privilege(
      'authenticated',
      'public.vera_coordination_events_event_sequence_seq',
      'UPDATE'
    )
  ) as expected_client_privileges_revoked,
  (
    has_sequence_privilege(
      'service_role',
      'public.vera_coordination_events_event_sequence_seq',
      'USAGE'
    )
    and has_sequence_privilege(
      'service_role',
      'public.vera_coordination_events_event_sequence_seq',
      'SELECT'
    )
    and has_sequence_privilege(
      'service_role',
      'public.vera_coordination_events_event_sequence_seq',
      'UPDATE'
    )
  ) as expected_service_role_preserved;
