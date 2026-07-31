begin;

alter table public.vera_temporal_events_v1
    add column state_time_precision text not null default 'UNKNOWN',
    add column state_time_lower_bound timestamptz,
    add column state_time_upper_bound timestamptz,
    add column record_time_precision text not null default 'EXACT',
    add column record_time_lower_bound timestamptz,
    add column record_time_upper_bound timestamptz,
    add column retrieval_time_precision text not null default 'UNKNOWN',
    add column retrieval_time_lower_bound timestamptz,
    add column retrieval_time_upper_bound timestamptz;

create or replace function public.vera_temporal_events_v1_role_precision()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
begin
    if jsonb_typeof(new.payload) <> 'object' then
        raise exception using
            errcode = '23514',
            message = 'temporal event payload must be a JSON object';
    end if;

    new.state_time_precision := coalesce(
        nullif(btrim(new.payload#>>'{temporal,state_time,precision}'), ''),
        'UNKNOWN'
    );
    new.state_time_lower_bound :=
        nullif(new.payload#>>'{temporal,state_time,lower_bound}', '')::timestamptz;
    new.state_time_upper_bound :=
        nullif(new.payload#>>'{temporal,state_time,upper_bound}', '')::timestamptz;

    -- record_time is assigned by the database and represents persistence only.
    new.record_time_precision := 'EXACT';
    new.record_time_lower_bound := null;
    new.record_time_upper_bound := null;

    new.retrieval_time_precision := coalesce(
        nullif(btrim(new.payload#>>'{temporal,retrieval_time,precision}'), ''),
        'UNKNOWN'
    );
    new.retrieval_time_lower_bound :=
        nullif(new.payload#>>'{temporal,retrieval_time,lower_bound}', '')::timestamptz;
    new.retrieval_time_upper_bound :=
        nullif(new.payload#>>'{temporal,retrieval_time,upper_bound}', '')::timestamptz;

    return new;
end;
$$;

-- PostgreSQL runs same-kind triggers in name order. This trigger must classify
-- role precision before the existing prepare-insert trigger computes the
-- logical hash. The canonical payload already carries the classified values.
create trigger vera_temporal_events_v1_00_role_precision
before insert on public.vera_temporal_events_v1
for each row execute function public.vera_temporal_events_v1_role_precision();

alter table public.vera_temporal_events_v1
    add constraint vera_temporal_events_v1_state_precision_check check (
        state_time_precision in ('EXACT', 'BOUNDED', 'APPROXIMATE', 'UNKNOWN')
    ),
    add constraint vera_temporal_events_v1_state_precision_shape check (
        (
            state_time_precision = 'EXACT'
            and state_time is not null
            and state_time_lower_bound is null
            and state_time_upper_bound is null
        )
        or
        (
            state_time_precision = 'BOUNDED'
            and state_time is not null
            and state_time_lower_bound is not null
            and state_time_upper_bound is not null
            and state_time_lower_bound <= state_time
            and state_time <= state_time_upper_bound
        )
        or
        (
            state_time_precision = 'APPROXIMATE'
            and state_time is not null
            and state_time_lower_bound is null
            and state_time_upper_bound is null
        )
        or
        (
            state_time_precision = 'UNKNOWN'
            and state_time is null
            and state_time_lower_bound is null
            and state_time_upper_bound is null
        )
    ),
    add constraint vera_temporal_events_v1_record_precision_check check (
        record_time_precision = 'EXACT'
        and record_time is not null
        and record_time_lower_bound is null
        and record_time_upper_bound is null
    ),
    add constraint vera_temporal_events_v1_retrieval_precision_check check (
        retrieval_time_precision in ('EXACT', 'BOUNDED', 'APPROXIMATE', 'UNKNOWN')
    ),
    add constraint vera_temporal_events_v1_retrieval_precision_shape check (
        (
            retrieval_time_precision = 'EXACT'
            and retrieval_time is not null
            and retrieval_time_lower_bound is null
            and retrieval_time_upper_bound is null
        )
        or
        (
            retrieval_time_precision = 'BOUNDED'
            and retrieval_time is not null
            and retrieval_time_lower_bound is not null
            and retrieval_time_upper_bound is not null
            and retrieval_time_lower_bound <= retrieval_time
            and retrieval_time <= retrieval_time_upper_bound
        )
        or
        (
            retrieval_time_precision = 'APPROXIMATE'
            and retrieval_time is not null
            and retrieval_time_lower_bound is null
            and retrieval_time_upper_bound is null
        )
        or
        (
            retrieval_time_precision = 'UNKNOWN'
            and retrieval_time is null
            and retrieval_time_lower_bound is null
            and retrieval_time_upper_bound is null
        )
    );

comment on column public.vera_temporal_events_v1.event_time_precision is
'Precision of event_time only. It does not classify state, record, or retrieval time.';
comment on column public.vera_temporal_events_v1.state_time_precision is
'Independent precision of state_time, derived from payload.temporal.state_time.precision. Missing precision is UNKNOWN and cannot accompany a timestamp.';
comment on column public.vera_temporal_events_v1.record_time_precision is
'EXACT relative to the database persistence clock. It does not imply exact event, state, retrieval, delivery, or consumption time.';
comment on column public.vera_temporal_events_v1.retrieval_time_precision is
'Independent precision of retrieval_time, derived from payload.temporal.retrieval_time.precision. Retrieval does not refresh represented state.';

revoke all on function public.vera_temporal_events_v1_role_precision()
from public, anon, authenticated, service_role;

commit;
