alter table bug_ops.dispatch_events_v2
  add column if not exists claim_read_ct integer;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid='bug_ops.dispatch_events_v2'::regclass
      and conname='dispatch_events_v2_claim_read_ct_check'
  ) then
    alter table bug_ops.dispatch_events_v2
      add constraint dispatch_events_v2_claim_read_ct_check
      check (claim_read_ct is null or claim_read_ct >= 1);
  end if;
end $$;

create or replace function bug_ops.ack_work(
  p_role text,
  p_msg_id bigint,
  p_dispatch_id uuid,
  p_expected_read_ct integer,
  p_handled_event_id uuid,
  p_note text default null
) returns uuid
language plpgsql
set search_path=''
as $$
declare
  v_role text:=upper(btrim(p_role));
  v_message jsonb;
  v_read_ct integer;
  enq bug_ops.dispatch_events_v2%rowtype;
  terminal bug_ops.dispatch_events_v2%rowtype;
  src bug_ops.bug_events%rowtype;
  handled bug_ops.bug_events%rowtype;
  v_digest text;
  v_id uuid:=gen_random_uuid();
  ok boolean;
begin
  perform bug_ops.assert_queue_filter_contract();
  if bug_ops.queue_for_role(v_role) is null then raise exception 'INVALID_ROLE'; end if;
  if p_expected_read_ct < 1 then raise exception 'INVALID_READ_CT'; end if;

  select * into enq
  from bug_ops.dispatch_events_v2 d
  where d.dispatch_id=p_dispatch_id and d.event_type='ENQUEUED';
  if not found or enq.queue_name<>'bug_dispatch' or enq.msg_id<>p_msg_id or enq.target_role is distinct from v_role then
    raise exception 'ACK_DISPATCH_BINDING_MISMATCH';
  end if;

  select * into terminal
  from bug_ops.dispatch_events_v2 d
  where d.dispatch_id=p_dispatch_id and d.event_type<>'ENQUEUED';
  if found then
    if terminal.event_type='HANDLED'
       and terminal.queue_name='bug_dispatch'
       and terminal.msg_id=p_msg_id
       and terminal.handled_event_id is not distinct from p_handled_event_id
       and terminal.claim_read_ct is not distinct from p_expected_read_ct
       and terminal.target_role is not distinct from v_role
       and terminal.note is not distinct from p_note then
      return terminal.dispatch_event_id;
    end if;
    raise exception 'ACK_REPLAY_CONFLICT';
  end if;

  select q.message,q.read_ct
    into v_message,v_read_ct
  from pgmq.q_bug_dispatch q
  where q.msg_id=p_msg_id
  for update;

  if v_message is null then raise exception 'QUEUE_MESSAGE_NOT_ACTIVE'; end if;
  if v_read_ct <> p_expected_read_ct then raise exception 'STALE_CLAIM expected %, actual %',p_expected_read_ct,v_read_ct; end if;

  v_digest:=bug_ops.sha256_jsonb(v_message);
  if enq.payload_digest is distinct from v_digest then raise exception 'ACK_PAYLOAD_DIGEST_MISMATCH'; end if;

  select * into src from bug_ops.bug_events e where e.event_id=enq.bug_event_id;
  if not found or src.bug_id is distinct from enq.bug_id or src.dispatch_id is distinct from p_dispatch_id then
    raise exception 'ACK_SOURCE_BINDING_MISMATCH';
  end if;

  select * into handled from bug_ops.bug_events e where e.event_id=p_handled_event_id;
  if not found or handled.bug_id<>src.bug_id or handled.state_version<=src.state_version then
    raise exception 'ACK_REQUIRES_LATER_BUG_EVENT';
  end if;

  select pgmq.archive('bug_dispatch',p_msg_id) into ok;
  if not coalesce(ok,false) then raise exception 'QUEUE_MESSAGE_NOT_ACTIVE'; end if;

  insert into bug_ops.dispatch_events_v2(
    dispatch_event_id,dispatch_id,queue_name,msg_id,event_type,bug_id,bug_event_id,
    handled_event_id,target_role,payload_digest,observed_message,note,claim_read_ct
  ) values(
    v_id,p_dispatch_id,'bug_dispatch',p_msg_id,'HANDLED',src.bug_id,src.event_id,
    p_handled_event_id,v_role,v_digest,v_message,p_note,p_expected_read_ct
  );
  return v_id;
end $$;

create or replace function bug_ops.janitor_dispatch(p_qty integer default 20)
returns table(msg_id bigint,event_type text)
language plpgsql
set search_path=''
as $$
declare r record; v_target text; v_type text;
begin
 perform bug_ops.assert_queue_filter_contract();
 if p_qty<1 or p_qty>100 then raise exception 'INVALID_QTY'; end if;
 for r in
   select q.msg_id,q.message from pgmq.q_bug_dispatch q
   where q.vt<=clock_timestamp()
     and (jsonb_typeof(q.message)<>'object' or not(q.message?'target_role') or not exists(select 1 from bug_ops.role_registry rr where rr.role_key=upper(btrim(q.message->>'target_role')) and rr.active))
   order by q.msg_id limit p_qty for update skip locked
 loop
   v_target:=case when jsonb_typeof(r.message)='object' then upper(btrim(r.message->>'target_role')) else null end;
   v_type:=case when v_target is null or length(v_target)=0 then 'POISON' else 'UNKNOWN_TARGET_ROLE' end;
   perform bug_ops.archive_dispatch_internal_v2(r.msg_id,v_type,r.message,null,null,null,null,v_target,case when v_type='POISON' then 'missing/malformed target_role' else 'unknown target_role' end);
   return query select r.msg_id,v_type;
 end loop;
end $$;

create or replace function bug_ops.update_bug_status(
  p_operation_id uuid,
  p_bug_id uuid,
  p_expected_state_version bigint,
  p_status text,
  p_actor text default null,
  p_note text default null
) returns table(out_bug_id uuid,out_event_id uuid,out_state_version bigint,out_dispatch_revision bigint,idempotent_replay boolean)
language plpgsql
set search_path=''
as $$
declare
 br bug_ops.bug_reports%rowtype;
 ev bug_ops.bug_events%rowtype;
 cfg bug_ops.system_config%rowtype;
 v_requested text:=upper(btrim(p_status));
 v_current text;
 v_payload jsonb;
 v_digest text;
 v_event uuid:=gen_random_uuid();
 v_state bigint;
 v_dispatch_rev bigint;
 v_routing bigint;
 v_type text;
 v_role text;
 v_dispatch uuid;
 v_snapshot jsonb;
 v_pdigest text;
 v_msg bigint;
begin
 perform pg_advisory_xact_lock(hashtextextended(p_operation_id::text,0));
 select * into cfg from bug_ops.system_config where singleton=true;
 v_payload:=jsonb_build_object('kind','STATUS','home_project',cfg.project_key,'bug_id',p_bug_id,'expected_state_version',p_expected_state_version,'status',v_requested,'actor',p_actor,'note',p_note);
 v_digest:=bug_ops.sha256_jsonb(v_payload);
 select * into ev from bug_ops.bug_events e where e.operation_id=p_operation_id;
 if found then
   if ev.request_digest<>v_digest then raise exception 'OPERATION_ID_REUSE_CONFLICT'; end if;
   return query select ev.bug_id,ev.event_id,ev.state_version,ev.dispatch_revision,true; return;
 end if;
 if v_requested not in ('NEW','TRIAGED','IN_PROGRESS','BLOCKED','FIXED','VERIFYING','CLOSED','REOPENED') then raise exception 'INVALID_STATUS'; end if;
 select * into br from bug_ops.bug_reports b where b.bug_id=p_bug_id for update;
 if not found then raise exception 'BUG_NOT_FOUND'; end if;
 if br.state_version<>p_expected_state_version then raise exception 'STALE_STATE_VERSION expected %, actual %',p_expected_state_version,br.state_version; end if;
 if v_requested='REOPENED' and br.status<>'CLOSED' then raise exception 'REOPEN_REQUIRES_CLOSED'; end if;
 if br.status='CLOSED' and v_requested<>'REOPENED' then raise exception 'BUG_CLOSED_REQUIRES_REOPEN'; end if;

 v_state:=br.state_version+1;

 if v_requested='REOPENED' then
   v_role:=cfg.coordinator_role;
   if bug_ops.queue_for_role(v_role) is null then raise exception 'COORDINATOR_ROLE_INELIGIBLE'; end if;
   v_dispatch_rev:=br.dispatch_revision+1;
   v_routing:=br.routing_revision + case when br.assigned_role is distinct from v_role then 1 else 0 end;
   v_dispatch:=gen_random_uuid();
   v_current:='NEW';
   v_type:='REOPENED';
   v_snapshot:=jsonb_build_object(
     'dispatch_id',v_dispatch,'bug_id',p_bug_id,'home_project',br.home_project,
     'event_id',v_event,'state_version',v_state,'dispatch_revision',v_dispatch_rev,
     'target_role',v_role,'action','BUG_REOPENED','operation_id',p_operation_id
   );
   v_pdigest:=bug_ops.sha256_jsonb(v_snapshot);
   insert into bug_ops.bug_events(
     event_id,bug_id,state_version,routing_revision,dispatch_revision,event_type,actor,
     operation_id,request_digest,request_payload,details,dispatch_id,dispatch_snapshot,dispatch_payload_digest
   ) values(
     v_event,p_bug_id,v_state,v_routing,v_dispatch_rev,v_type,p_actor,
     p_operation_id,v_digest,v_payload,
     jsonb_build_object('from_status',br.status,'to_status',v_current,'from_role',br.assigned_role,'to_role',v_role,'note',p_note),
     v_dispatch,v_snapshot,v_pdigest
   );
   select s into v_msg from pgmq.send('bug_dispatch',v_snapshot,0) s limit 1;
   insert into bug_ops.dispatch_events_v2(
     dispatch_id,queue_name,msg_id,event_type,bug_id,bug_event_id,target_role,payload_digest,observed_message
   ) values(v_dispatch,'bug_dispatch',v_msg,'ENQUEUED',p_bug_id,v_event,v_role,v_pdigest,v_snapshot);
   update bug_ops.bug_reports
      set status='NEW',assigned_role=v_role,state_version=v_state,routing_revision=v_routing,
          dispatch_revision=v_dispatch_rev,updated_at=clock_timestamp(),closed_at=null
    where bug_id=p_bug_id;
   return query select p_bug_id,v_event,v_state,v_dispatch_rev,false; return;
 end if;

 v_current:=v_requested;
 v_type:='STATUS_CHANGED';
 v_dispatch_rev:=br.dispatch_revision + case when v_current='CLOSED' then 1 else 0 end;
 v_routing:=br.routing_revision;
 update bug_ops.bug_reports
    set status=v_current,state_version=v_state,dispatch_revision=v_dispatch_rev,
        updated_at=clock_timestamp(),closed_at=case when v_current='CLOSED' then clock_timestamp() else null end
  where bug_id=p_bug_id;
 insert into bug_ops.bug_events(
   event_id,bug_id,state_version,routing_revision,dispatch_revision,event_type,actor,
   operation_id,request_digest,request_payload,details
 ) values(
   v_event,p_bug_id,v_state,v_routing,v_dispatch_rev,v_type,p_actor,
   p_operation_id,v_digest,v_payload,jsonb_build_object('from_status',br.status,'to_status',v_current,'note',p_note)
 );
 return query select p_bug_id,v_event,v_state,v_dispatch_rev,false;
end $$;

create or replace function bug_ops.list_open_bugs(p_role text)
returns table(
  bug_id uuid,home_project text,intake_key text,title text,description text,severity text,
  status text,component text,reported_by text,assigned_role text,state_version bigint,
  dispatch_revision bigint,evidence jsonb,created_at timestamptz,updated_at timestamptz
)
language plpgsql
stable
set search_path=''
as $$
declare v_role text:=upper(btrim(p_role));
begin
  if bug_ops.queue_for_role(v_role) is null then raise exception 'INVALID_ROLE'; end if;
  return query
  select b.bug_id,b.home_project,b.intake_key,b.title,b.description,b.severity,b.status,b.component,
         b.reported_by,b.assigned_role,b.state_version,b.dispatch_revision,b.evidence,b.created_at,b.updated_at
  from bug_ops.bug_reports b
  where b.assigned_role=v_role and b.status<>'CLOSED'
  order by b.updated_at asc,b.bug_id asc;
end $$;

revoke all on function bug_ops.list_open_bugs(text) from public,anon,authenticated,service_role;
grant execute on function bug_ops.list_open_bugs(text) to postgres;