\set ON_ERROR_STOP on

begin;

insert into public.vera_temporal_events_v1 (
    temporal_event_id,
    project_id,
    workstream,
    anchor_key,
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
    'anchor:stable:one',
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
    '[{"system":"HOST","operation":"current_time","reference_id":"host:test:entry-one","subject_hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]',
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
            workstream, anchor_key, scope_instance_id, scope_stability,
            provider_conversation_id, provider_branch_id, session_id,
            event_kind, anchor_status, event_time, event_time_precision,
            idempotency_key, source_evidence
        ) values (
            'workstream/time', 'anchor:stable:one', 'scope:stable:one', 'STABLE',
            'conversation-one', 'branch-one', 'session:two',
            'RETRIEVAL', 'ANCHORED', '2026-07-30T21:06:00Z', 'EXACT',
            'entry-one',
            '[{"system":"HOST","operation":"current_time","reference_id":"host:test:duplicate","subject_hash":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]'
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
            workstream, anchor_key, scope_instance_id, scope_stability,
            session_id, event_kind, anchor_status,
            event_time, event_time_precision,
            event_time_lower_bound, event_time_upper_bound,
            idempotency_key, source_evidence
        ) values (
            'workstream/time', 'anchor:bad-bounds', 'scope:ephemeral:two', 'EPHEMERAL',
            'session:three', 'ENTRY', 'ANCHORED',
            '2026-07-30T21:10:00Z', 'BOUNDED',
            '2026-07-30T21:11:00Z', '2026-07-30T21:12:00Z',
            'bad-bounds',
            '[{"system":"HOST","operation":"current_time","reference_id":"host:test:bounds","subject_hash":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"}]'
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
            workstream, anchor_key, scope_instance_id, scope_stability,
            session_id, event_kind, anchor_status,
            event_time, event_time_precision,
            idempotency_key, source_evidence
        ) values (
            'workstream/time', 'anchor:bad-stable', 'scope:bad-stable', 'STABLE',
            'session:four', 'ENTRY', 'ANCHORED',
            '2026-07-30T21:10:00Z', 'EXACT',
            'missing-provider-identity',
            '[{"system":"HOST","operation":"current_time","reference_id":"host:test:stable","subject_hash":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"}]'
        );
        raise exception 'stable scope without provider identity was accepted';
    exception when check_violation then
        null;
    end;
end;
$$;

insert into public.vera_temporal_events_v1 (
    temporal_event_id, project_id, workstream, anchor_key, scope_instance_id,
    scope_stability, provider_conversation_id, provider_branch_id,
    session_id, event_kind, anchor_status, event_time,
    event_time_precision, idempotency_key, supersedes_event_id,
    source_evidence, payload
) values (
    '00000000-0000-0000-0000-000000000102',
    'vera-reciprocal-agency-environment',
    'workstream/time',
    'anchor:stable:one',
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
    '[{"system":"SUPABASE","operation":"append_temporal_event","reference_id":"supabase:test:transition","subject_hash":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"}]',
    '{"test":"valid successor"}'
);

do $$
begin
    begin
        insert into public.vera_temporal_events_v1 (
            workstream, anchor_key, scope_instance_id, scope_stability,
            provider_conversation_id, provider_branch_id,
            session_id, event_kind, anchor_status, event_time,
            event_time_precision, idempotency_key, supersedes_event_id,
            source_evidence
        ) values (
            'workstream/time', 'anchor:stable:one', 'scope:stable:one', 'STABLE',
            'conversation-one', 'branch-one',
            'session:six', 'MATERIAL_TRANSITION', 'ANCHORED',
            '2026-07-30T21:16:00Z', 'EXACT', 'fork-one',
            '00000000-0000-0000-0000-000000000101',
            '[{"system":"SUPABASE","operation":"append_temporal_event","reference_id":"supabase:test:fork","subject_hash":"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"}]'
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
            workstream, anchor_key, scope_instance_id, scope_stability,
            session_id, event_kind, anchor_status, event_time,
            event_time_precision, idempotency_key, supersedes_event_id,
            source_evidence
        ) values (
            'workstream/time', 'anchor:stable:one', 'scope:ephemeral:different', 'EPHEMERAL',
            'session:seven', 'MATERIAL_TRANSITION', 'ANCHORED',
            '2026-07-30T21:17:00Z', 'EXACT', 'cross-scope',
            '00000000-0000-0000-0000-000000000102',
            '[{"system":"SUPABASE","operation":"append_temporal_event","reference_id":"supabase:test:cross-scope","subject_hash":"1111111111111111111111111111111111111111111111111111111111111111"}]'
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
        insert into public.vera_temporal_events_v1 (
            workstream, anchor_key, scope_instance_id, scope_stability,
            provider_conversation_id, provider_branch_id,
            session_id, event_kind, anchor_status, event_time,
            event_time_precision, idempotency_key, supersedes_event_id,
            source_evidence
        ) values (
            'workstream/time', 'anchor:different', 'scope:stable:one', 'STABLE',
            'conversation-one', 'branch-one',
            'session:eight', 'MATERIAL_TRANSITION', 'ANCHORED',
            '2026-07-30T21:18:00Z', 'EXACT', 'cross-anchor',
            '00000000-0000-0000-0000-000000000102',
            '[{"system":"SUPABASE","operation":"append_temporal_event","reference_id":"supabase:test:cross-anchor","subject_hash":"2222222222222222222222222222222222222222222222222222222222222222"}]'
        );
        raise exception 'cross-anchor supersession was accepted';
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
       or has_table_privilege('service_role', 'public.vera_temporal_events_v1', 'INSERT')
       or not has_table_privilege('service_role', 'public.vera_temporal_events_v1', 'SELECT')
       or has_sequence_privilege('service_role', 'public.vera_temporal_events_v1_event_sequence_seq', 'USAGE')
       or not has_function_privilege('service_role', 'public.append_vera_temporal_event_v1(jsonb)', 'EXECUTE') then
        raise exception 'service_role privileges do not enforce governed append-only access';
    end if;
end;
$$;

rollback;
