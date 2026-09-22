drop trigger if exists role_registry_no_truncate_v1 on bug_ops.role_registry;
create trigger role_registry_no_truncate_v1
before truncate on bug_ops.role_registry
for each statement execute function bug_ops.block_immutable_mutation();

drop trigger if exists operation_receipts_no_truncate on bug_ops.operation_receipts;
create trigger operation_receipts_no_truncate
before truncate on bug_ops.operation_receipts
for each statement execute function bug_ops.block_immutable_mutation();

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
  br bug_ops.bug_reports%rowtype;
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

  -- Response-loss replay resolves historical terminal identity first.
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

  -- First ACK must still own the exact active carrier generation.
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
  if handled.dispatch_revision is distinct from src.dispatch_revision then
    raise exception 'ACK_HANDLED_EVENT_STALE_DISPATCH';
  end if;

  -- Lock canonical work row so route/close/reopen cannot invalidate after the check and before archive.
  select * into br from bug_ops.bug_reports b where b.bug_id=src.bug_id for update;
  if not found then raise exception 'ACK_BUG_NOT_FOUND'; end if;
  if br.status='CLOSED' then raise exception 'ACK_BUG_CLOSED'; end if;
  if br.assigned_role is distinct from v_role or br.dispatch_revision is distinct from src.dispatch_revision then
    raise exception 'ACK_DISPATCH_STALE';
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

revoke all on function bug_ops.ack_work(text,bigint,uuid,integer,uuid,text) from public,anon,authenticated,service_role;
grant execute on function bug_ops.ack_work(text,bigint,uuid,integer,uuid,text) to postgres;