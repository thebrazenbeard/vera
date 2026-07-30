\set ON_ERROR_STOP on

begin;

insert into public.vera_temporal_events_v1 (
    temporal_event_id,
    project_id,
    workstream,
    scope_instance_id,
    scope_stability,
    provider_conversation_id,
    provider_branch_id,
    session_id,
    event_kind,
    anchor_status,
    event_time,
    state_time,
    record_time,
    retrieval_time,
    event_time_precision,
    idempotency_key,
    source_evidence,
    limitations,
    payload
) values (
    '00000000-0000-0000-0000-000000000101',
    'vera-reciprocal-agency-environment',
    'workstream/time',
    'scope:stable:one',
    'STABLE',
    'conversation-one',
    'branch-one',
    'session:one',
    'ENTRY',
    'ANCHORED',
    '2026-07-30T21:05:00Z',
    '2026-07-30T21:05:00Z',
    '2000-01-01T00:00:00Z',
    '2026-07-30T21:05:01Z',
    'EXACT',
    'entry-one',
    '[{"system":"HOST","operation":"current_time","confirmed":true}]',
    '[]',
    '{"test":"stable exact entry"}'
);

do $$
begin
    if (
        select record_time = '2000-01-01T00:00:00Z'::timestamptz
          from public.vera_temporal_events_v1
         where temporal_event_id = '00000000-0000-0000-0000-000000000101'
    ) then
        raise exception 'record_time was not database-assigned';
    end if;
end;
$$;

do $$
begin
    begin
        insert into public.vera_temporal_events_v1 (
            workstream, scope_instance_id, scope_stability,
            provider_conversation_id, provider_branch_id, session_id,
            event_kind, anchor_status, event_time, event_time_precision,
            idempotency_key, source_evidence
        ) values (
            'workstream/time', 'scope:stable:one', 'STABLE',
            'conversation-one', 'branch-one', 'session:two',
            'RETRIEVAL', 'ANCHORED', '2026-07-30T21:06:00Z', 'EXACT',
            'entry-one', '[]'
        );
        raise exception 'duplicate idempotency key was accepted';
    exception when unique_violation then
        null;
    end;
end;
$$;

do $$
begin
    begin
        insert into public.vera_temporal_events_v1 (
            workstream, scope_instance_id, scope_stability,
            session_id, event_kind, anchor_status,
            event_time, event_time_precision,
            event_time_lower_bound, event_time_upper_bound,
            idempotency_key, source_evidence
        ) values (
            'workstream/time', 'scope:ephemeral:two', 'EPHEMERAL',
            'session:three', 'ENTRY', 'ANCHORED',
            '2026-07-30T21:10:00Z', 'BOUNDED',
            '2026-07-30T21:11:00Z', '2026-07-30T21:12:00Z',
            'bad-bounds', '[]'
        );
        raise exception 'out-of-bounds event_time was accepted';
    exception when check_violation then
        null;
    end;
end;
$$;

do $$
begin
    begin
        insert into public.vera_temporal_events_v1 (
            workstream, scope_instance_id, scope_stability,
            session_id, event_kind, anchor_status,
            event_time, event_time_precision,
            idempotency_key, source_evidence
        ) values (
            'workstream/time', 'scope:bad-stable', 'STABLE',
            'session:four', 'ENTRY', 'ANCHORED',
            '2026-07-30T21:10:00Z', 'EXACT',
            'missing-provider-identity', '[]'
        );
        raise exception 'stable scope without provider identity was accepted';
    exception when check_violation then
        null;
    end;
end;
$$;

insert into public.vera_temporal_events_v1 (
    temporal_event_id, project_id, workstream, scope_instance_id,
    scope_stability, provider_conversation_id, provider_branch_id,
    session_id, event_kind, anchor_status, event_time,
    event_time_precision, idempotency_key, supersedes_event_id,
    source_evidence, payload
) values (
    '00000000-0000-0000-0000-000000000102',
    'vera-reciprocal-agency-environment',
    'workstream/time',
    'scope:stable:one',
    'STABLE',
    'conversation-one',
    'branch-one',
    'session:five',
    'MATERIAL_TRANSITION',
    'ANCHORED',
    '2026-07-30T21:15:00Z',
    'EXACT',
    'transition-one',
    '00000000-0000-0000-0000-000000000101',
    '[{"system":"SUPABASE","operation":"append_temporal_event","confirmed":true}]',
    '{"test":"valid successor"}'
);

do $$
begin
    begin
        insert into public.vera_temporal_events_v1 (
            workstream, scope_instance_id, scope_stability,
            provider_conversation_id, provider_branch_id,
            session_id, event_kind, anchor_status, event_time,
            event_time_precision, idempotency_key, supersedes_event_id,
            source_evidence
        ) values (
            'workstream/time', 'scope:stable:one', 'STABLE',
            'conversation-one', 'branch-one',
            'session:six', 'MATERIAL_TRANSITION', 'ANCHORED',
            '2026-07-30T21:16:00Z', 'EXACT', 'fork-one',
            '00000000-0000-0000-0000-000000000101', '[]'
        );
        raise exception 'supersession fork was accepted';
    exception when unique_violation then
        null;
    end;
end;
$$;

do $$
begin
    begin
        insert into public.vera_temporal_events_v1 (
            workstream, scope_instance_id, scope_stability,
            session_id, event_kind, anchor_status, event_time,
            event_time_precision, idempotency_key, supersedes_event_id,
            source_evidence
        ) values (
            'workstream/time', 'scope:ephemeral:different', 'EPHEMERAL',
            'session:seven', 'MATERIAL_TRANSITION', 'ANCHORED',
            '2026-07-30T21:17:00Z', 'EXACT', 'cross-scope',
            '00000000-0000-0000-0000-000000000102', '[]'
        );
        raise exception 'cross-scope supersession was accepted';
    exception when check_violation then
        null;
    end;
end;
$$;

do $$
begin
    begin
        update public.vera_temporal_events_v1
           set payload = '{"mutated":true}'
         where temporal_event_id = '00000000-0000-0000-0000-000000000101';
        raise exception 'update was accepted';
    exception when object_not_in_prerequisite_state then
        null;
    end;
end;
$$;

do $$
begin
    begin
        delete from public.vera_temporal_events_v1
         where temporal_event_id = '00000000-0000-0000-0000-000000000101';
        raise exception 'delete was accepted';
    exception when object_not_in_prerequisite_state then
        null;
    end;
end;
$$;

do $$
begin
    if has_table_privilege('service_role', 'public.vera_temporal_events_v1', 'UPDATE')
       or has_table_privilege('service_role', 'public.vera_temporal_events_v1', 'DELETE')
       or not has_table_privilege('service_role', 'public.vera_temporal_events_v1', 'SELECT')
       or not has_table_privilege('service_role', 'public.vera_temporal_events_v1', 'INSERT') then
        raise exception 'service_role privileges are not select/insert only';
    end if;
end;
$$;

rollback;
