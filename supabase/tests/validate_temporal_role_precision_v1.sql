\set ON_ERROR_STOP on

begin;

do $$
declare
    result_row record;
    stored public.vera_temporal_events_v1%rowtype;
    blocked boolean;
begin
    select * into result_row
    from public.append_vera_temporal_event_v1(
        jsonb_build_object(
            'project_id', 'vera-reciprocal-agency-environment',
            'workstream', 'workstream/time',
            'anchor_key', 'anchor:role-precision:exact',
            'scope_instance_id', 'scope:role-precision:exact',
            'scope_stability', 'EPHEMERAL',
            'session_id', 'session:role-precision:exact',
            'event_kind', 'ENTRY',
            'anchor_status', 'ANCHORED',
            'event_time', '2026-07-30T23:10:00Z',
            'state_time', '2026-07-30T23:10:01Z',
            'retrieval_time', '2026-07-30T23:10:02Z',
            'event_time_precision', 'EXACT',
            'idempotency_key', 'role-precision-exact',
            'source_evidence', jsonb_build_array(
                jsonb_build_object(
                    'system', 'HOST',
                    'operation', 'strict_role_precision_test',
                    'reference_id', 'host:role-precision:exact',
                    'subject_hash', repeat('a', 64)
                )
            ),
            'payload', jsonb_build_object(
                'temporal', jsonb_build_object(
                    'state_time', jsonb_build_object('precision', 'EXACT'),
                    'retrieval_time', jsonb_build_object('precision', 'EXACT')
                )
            )
        )
    );

    select * into stored
    from public.vera_temporal_events_v1
    where temporal_event_id = result_row.temporal_event_id;

    if stored.event_time_precision <> 'EXACT'
       or stored.state_time_precision <> 'EXACT'
       or stored.record_time_precision <> 'EXACT'
       or stored.retrieval_time_precision <> 'EXACT'
       or stored.state_time is null
       or stored.retrieval_time is null then
        raise exception 'role precision validation failed for exact record: %', to_jsonb(stored);
    end if;

    -- A state timestamp without explicit state precision must fail rather than
    -- being silently promoted to EXACT.
    blocked := false;
    begin
        perform public.append_vera_temporal_event_v1(
            jsonb_build_object(
                'workstream', 'workstream/time',
                'anchor_key', 'anchor:role-precision:missing-state',
                'scope_instance_id', 'scope:role-precision:missing-state',
                'scope_stability', 'EPHEMERAL',
                'session_id', 'session:role-precision:missing-state',
                'event_kind', 'ENTRY',
                'anchor_status', 'ANCHORED',
                'event_time', '2026-07-30T23:11:00Z',
                'state_time', '2026-07-30T23:11:01Z',
                'event_time_precision', 'EXACT',
                'idempotency_key', 'role-precision-missing-state',
                'source_evidence', jsonb_build_array(
                    jsonb_build_object(
                        'system', 'HOST',
                        'operation', 'strict_role_precision_test',
                        'reference_id', 'host:role-precision:missing-state',
                        'subject_hash', repeat('b', 64)
                    )
                )
            )
        );
    exception when check_violation then
        blocked := true;
    end;
    if not blocked then
        raise exception 'state timestamp without explicit precision was accepted';
    end if;

    -- A retrieval timestamp without explicit retrieval precision must also fail.
    blocked := false;
    begin
        perform public.append_vera_temporal_event_v1(
            jsonb_build_object(
                'workstream', 'workstream/time',
                'anchor_key', 'anchor:role-precision:missing-retrieval',
                'scope_instance_id', 'scope:role-precision:missing-retrieval',
                'scope_stability', 'EPHEMERAL',
                'session_id', 'session:role-precision:missing-retrieval',
                'event_kind', 'RETRIEVAL',
                'anchor_status', 'ANCHORED',
                'event_time', '2026-07-30T23:12:00Z',
                'retrieval_time', '2026-07-30T23:12:01Z',
                'event_time_precision', 'EXACT',
                'idempotency_key', 'role-precision-missing-retrieval',
                'source_evidence', jsonb_build_array(
                    jsonb_build_object(
                        'system', 'SUPABASE',
                        'operation', 'strict_role_precision_test',
                        'reference_id', 'supabase:role-precision:missing-retrieval',
                        'subject_hash', repeat('c', 64)
                    )
                )
            )
        );
    exception when check_violation then
        blocked := true;
    end;
    if not blocked then
        raise exception 'retrieval timestamp without explicit precision was accepted';
    end if;

    -- Independent bounded and approximate classifications are preserved.
    select * into result_row
    from public.append_vera_temporal_event_v1(
        jsonb_build_object(
            'workstream', 'workstream/time',
            'anchor_key', 'anchor:role-precision:mixed',
            'scope_instance_id', 'scope:role-precision:mixed',
            'scope_stability', 'EPHEMERAL',
            'session_id', 'session:role-precision:mixed',
            'event_kind', 'RETRIEVAL',
            'anchor_status', 'ANCHORED',
            'event_time', '2026-07-30T23:13:00Z',
            'state_time', '2026-07-30T23:13:01Z',
            'retrieval_time', '2026-07-30T23:13:02Z',
            'event_time_precision', 'APPROXIMATE',
            'idempotency_key', 'role-precision-mixed',
            'source_evidence', jsonb_build_array(
                jsonb_build_object(
                    'system', 'SUPABASE',
                    'operation', 'strict_role_precision_test',
                    'reference_id', 'supabase:role-precision:mixed',
                    'subject_hash', repeat('d', 64)
                )
            ),
            'payload', jsonb_build_object(
                'temporal', jsonb_build_object(
                    'state_time', jsonb_build_object(
                        'precision', 'BOUNDED',
                        'lower_bound', '2026-07-30T23:13:00Z',
                        'upper_bound', '2026-07-30T23:13:03Z'
                    ),
                    'retrieval_time', jsonb_build_object(
                        'precision', 'APPROXIMATE'
                    )
                )
            )
        )
    );

    select * into stored
    from public.vera_temporal_events_v1
    where temporal_event_id = result_row.temporal_event_id;

    if stored.event_time_precision <> 'APPROXIMATE'
       or stored.state_time_precision <> 'BOUNDED'
       or stored.state_time_lower_bound <> '2026-07-30T23:13:00Z'::timestamptz
       or stored.state_time_upper_bound <> '2026-07-30T23:13:03Z'::timestamptz
       or stored.retrieval_time_precision <> 'APPROXIMATE' then
        raise exception 'independent role precision was not preserved: %', to_jsonb(stored);
    end if;

    -- UNKNOWN is a non-claim and therefore cannot accompany a timestamp.
    blocked := false;
    begin
        perform public.append_vera_temporal_event_v1(
            jsonb_build_object(
                'workstream', 'workstream/time',
                'anchor_key', 'anchor:role-precision:false-unknown',
                'scope_instance_id', 'scope:role-precision:false-unknown',
                'scope_stability', 'EPHEMERAL',
                'session_id', 'session:role-precision:false-unknown',
                'event_kind', 'ENTRY',
                'anchor_status', 'ANCHORED',
                'event_time', '2026-07-30T23:14:00Z',
                'state_time', '2026-07-30T23:14:01Z',
                'event_time_precision', 'EXACT',
                'idempotency_key', 'role-precision-false-unknown',
                'source_evidence', jsonb_build_array(
                    jsonb_build_object(
                        'system', 'HOST',
                        'operation', 'strict_role_precision_test',
                        'reference_id', 'host:role-precision:false-unknown',
                        'subject_hash', repeat('e', 64)
                    )
                ),
                'payload', jsonb_build_object(
                    'temporal', jsonb_build_object(
                        'state_time', jsonb_build_object('precision', 'UNKNOWN')
                    )
                )
            )
        );
    exception when check_violation then
        blocked := true;
    end;
    if not blocked then
        raise exception 'UNKNOWN state_time accepted a timestamp';
    end if;
end;
$$;

rollback;
