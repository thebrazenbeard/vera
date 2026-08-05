"""Fail-closed, externally authenticated temporal orientation."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from enum import Enum
from typing import Iterable,Mapping
from .canonical import canonical_sha256
from .signatures import public_key_id,verify_signature
class OrientationState(str,Enum):
 COMPLETE='COMPLETE';COMPLETE_FROM_FRESH_SNAPSHOT='COMPLETE_FROM_FRESH_SNAPSHOT';DEGRADED_BOUNDED='DEGRADED_BOUNDED';STALE='STALE';CONFLICTED='CONFLICTED';UNKNOWN='UNKNOWN';RECOVERY_REQUIRED='RECOVERY_REQUIRED'
CURRENT_TIME='current_time'
SEMANTIC_TIME_DIMENSIONS=('current_chat_time','project_interaction_time','durable_state_time','event_time','record_time','retrieval_time')
REQUIRED_DIMENSIONS=(CURRENT_TIME,*SEMANTIC_TIME_DIMENSIONS)
SOURCE_MODES={'CURRENT_SOURCE','FRESH_BOUND_SNAPSHOT'}
def parse_time(value:str)->datetime:
 p=datetime.fromisoformat(value.replace('Z','+00:00'))
 if p.tzinfo is None:raise ValueError('timestamps must include a timezone')
 return p.astimezone(timezone.utc)
@dataclass(frozen=True)
class TimeEvidence:
 dimension:str;value:str;source:str;source_kind:str;observed_at:str;source_digest:str;source_key_id:str;source_signature:str;lower_bound:str|None=None;upper_bound:str|None=None
 def signed_body(self)->dict[str,str|None]:
  return {'dimension':self.dimension,'value':self.value,'source':self.source,'source_kind':self.source_kind,'observed_at':self.observed_at,'source_digest':self.source_digest,'source_key_id':self.source_key_id,'lower_bound':self.lower_bound,'upper_bound':self.upper_bound}
 def evidence_id(self)->str:return canonical_sha256(self.as_dict())
 def validate(self,trusted_source_keys:Mapping[str,Mapping])->None:
  key=trusted_source_keys.get(self.source)
  if key is None or public_key_id(key)!=self.source_key_id or not verify_signature(self.signed_body(),self.source_signature,key):raise ValueError('time evidence source authentication mismatch')
  if self.dimension not in REQUIRED_DIMENSIONS:raise ValueError('unknown time dimension')
  if not self.source or not self.source_digest:raise ValueError('source and source digest are required')
  if self.source_kind!=self.dimension:raise ValueError('time evidence source kind mismatch')
  if len(self.source_digest)!=64 or any(c not in '0123456789abcdef' for c in self.source_digest):raise ValueError('source digest must be lowercase SHA-256')
  v=parse_time(self.value);o=parse_time(self.observed_at);lo=parse_time(self.lower_bound) if self.lower_bound else None;hi=parse_time(self.upper_bound) if self.upper_bound else None
  if (lo is None)!=(hi is None):raise ValueError('bounded evidence requires both bounds')
  if lo and (lo>hi or v<lo or v>hi):raise ValueError('invalid temporal bounds')
  if o<v-timedelta(minutes=5):raise ValueError('observation predates value')
 def as_dict(self)->dict[str,str|None]:return self.signed_body()|{'source_signature':self.source_signature}
@dataclass(frozen=True)
class OrientationReceipt:
 state:OrientationState;evaluated_at:str;evidence_digest:str;missing_dimensions:tuple[str,...];stale_dimensions:tuple[str,...];conflicted_dimensions:tuple[str,...];invalid_dimensions:tuple[str,...];claims_allowed:bool;source_mode:str;required_dimensions:tuple[str,...];response_scope:str|None;bounded_claims_only:bool;supporting_evidence_ids:tuple[str,...]
 def as_dict(self)->dict[str,object]:return {'schema':'VERA_R8A0_TEMPORAL_ORIENTATION_RECEIPT_V2','state':self.state.value,'evaluated_at':self.evaluated_at,'evidence_digest':self.evidence_digest,'missing_dimensions':list(self.missing_dimensions),'stale_dimensions':list(self.stale_dimensions),'conflicted_dimensions':list(self.conflicted_dimensions),'invalid_dimensions':list(self.invalid_dimensions),'claims_allowed':self.claims_allowed,'source_mode':self.source_mode,'required_dimensions':list(self.required_dimensions),'response_scope':self.response_scope,'bounded_claims_only':self.bounded_claims_only,'supporting_evidence_ids':list(self.supporting_evidence_ids)}
class OrientationGate:
 def __init__(self,*,trusted_source_keys:Mapping[str,Mapping],max_age:timedelta=timedelta(minutes=10)):
  if not trusted_source_keys:raise ValueError('trusted temporal source keys are required')
  self.keys=dict(trusted_source_keys)
  if max_age<=timedelta(0):raise ValueError('max_age must be positive')
  self.max_age=max_age
 def evaluate(self,evidence:Iterable[TimeEvidence],*,now:datetime,required_dimensions:Iterable[str]=REQUIRED_DIMENSIONS,source_mode:str='CURRENT_SOURCE',degraded_allowed:bool=False,response_scope:str|None=None)->OrientationReceipt:
  if now.tzinfo is None:raise ValueError('now must include a timezone')
  if source_mode not in SOURCE_MODES:raise ValueError('unsupported source mode')
  now=now.astimezone(timezone.utc);required=tuple(dict.fromkeys(required_dimensions));scope=response_scope.strip() if isinstance(response_scope,str) else None
  if not required or any(d not in REQUIRED_DIMENSIONS for d in required):raise ValueError('required dimensions are empty or unknown')
  if CURRENT_TIME not in required:raise ValueError('every temporal scope must require current_time')
  grouped:dict[str,list[TimeEvidence]]={};invalid:set[str]=set();rows=[]
  for item in evidence:
   grouped.setdefault(item.dimension,[]).append(item);rows.append(item.as_dict())
   try:item.validate(self.keys)
   except ValueError:invalid.add(item.dimension)
  missing=tuple(sorted(set(required)-set(grouped)));stale:set[str]=set();conflict:set[str]=set()
  for d,items in grouped.items():
   valid=[x for x in items if d not in invalid]
   if len(valid)>1:conflict.add(d)
   for x in valid:
    o=parse_time(x.observed_at);v=parse_time(x.value)
    if now-o>self.max_age or o-now>timedelta(minutes=5):stale.add(d)
    if d==CURRENT_TIME and abs(now-v)>self.max_age:stale.add(d)
    if source_mode=='FRESH_BOUND_SNAPSHOT' and not(x.lower_bound and x.upper_bound):invalid.add(d)
  full=set(required)==set(REQUIRED_DIMENSIONS);selected=[grouped[d][0] for d in required if len(grouped.get(d,()))==1]
  bounded=len(selected)==len(required) and all(x.lower_bound and x.upper_bound for x in selected)
  if conflict:state=OrientationState.CONFLICTED
  elif invalid or missing:state=OrientationState.UNKNOWN
  elif stale:state=OrientationState.STALE
  elif source_mode=='FRESH_BOUND_SNAPSHOT':state=OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT if full else (OrientationState.DEGRADED_BOUNDED if degraded_allowed and scope and bounded else OrientationState.UNKNOWN)
  elif full:state=OrientationState.COMPLETE
  else:state=OrientationState.DEGRADED_BOUNDED if degraded_allowed and scope and bounded else OrientationState.UNKNOWN
  allowed=state in {OrientationState.COMPLETE,OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT,OrientationState.DEGRADED_BOUNDED}
  support=tuple(x.evidence_id() for x in selected) if state is OrientationState.DEGRADED_BOUNDED else ()
  return OrientationReceipt(state,now.isoformat(),canonical_sha256(rows),missing,tuple(sorted(stale)),tuple(sorted(conflict)),tuple(sorted(invalid)),allowed,source_mode,required,scope,state is OrientationState.DEGRADED_BOUNDED,support)
def evidence_from_mapping(rows:Mapping[str,Mapping[str,str|None]])->list[TimeEvidence]:
 out=[]
 required={'dimension','value','source','source_kind','observed_at','source_digest','source_key_id','source_signature','lower_bound','upper_bound'}
 for dimension,row in rows.items():
  if set(row)!=required or row['dimension']!=dimension:raise ValueError('time evidence fields or dimension mismatch')
  out.append(TimeEvidence(dimension,str(row['value']),str(row['source']),str(row['source_kind']),str(row['observed_at']),str(row['source_digest']),str(row['source_key_id']),str(row['source_signature']),str(row['lower_bound']) if row['lower_bound'] else None,str(row['upper_bound']) if row['upper_bound'] else None))
 return out
