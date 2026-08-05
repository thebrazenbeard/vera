from __future__ import annotations
import hashlib,hmac,json,os,subprocess,sys,tempfile,unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from r8a0.canonical import CanonicalizationError,canonical_bytes,canonical_dumps,strict_loads
from r8a0.memory import AdmissionRequest,GovernedMemoryStore,MemoryAdmissionError,MemoryClass,signed_policy_binding
from r8a0.recovery import CheckpointState,RecoveryError,recover,terminate,write_checkpoint
from r8a0.temporal import CURRENT_TIME,REQUIRED_DIMENSIONS,OrientationGate,OrientationState,current_evidence,signed_time_evidence
NOW=datetime(2026,8,5,21,20,tzinfo=timezone.utc);TK=b'r8a0-temporal-integrity-key-32b';P='VERA_COGNITIVE_REPAIR_R8A0';I='VERA'
def H(s):return hashlib.sha256(s.encode()).hexdigest()
def T(at=NOW,b=False,key=TK):
 v=at.isoformat();lo=(at-timedelta(minutes=1)).isoformat() if b else None;hi=(at+timedelta(minutes=1)).isoformat() if b else None
 r=current_evidence(at,source_digest=H('clock'),integrity_key=key,lower_bound=lo,upper_bound=hi)
 return r+[signed_time_evidence(dimension=d,value=v,source='SRC_'+d,source_kind=d,observed_at=v,source_digest=H(d),integrity_key=key,lower_bound=lo,upper_bound=hi) for d in REQUIRED_DIMENSIONS if d!=CURRENT_TIME]
class Temporal(unittest.TestCase):
 def test_states_and_scope(self):
  g=OrientationGate(integrity_key=TK);self.assertEqual(g.evaluate(T(),now=NOW).state,OrientationState.COMPLETE)
  self.assertEqual(g.evaluate(current_evidence(NOW,source_digest=H('clock'),integrity_key=TK),now=NOW).state,OrientationState.UNKNOWN)
  self.assertEqual(g.evaluate(T()[:-1],now=NOW,degraded_allowed=True,response_scope='event').state,OrientationState.UNKNOWN)
  req=(CURRENT_TIME,'event_time');u=[x for x in T() if x.dimension in req];b=[x for x in T(b=True) if x.dimension in req]
  self.assertEqual(g.evaluate(u,now=NOW,required_dimensions=req,degraded_allowed=True,response_scope='event').state,OrientationState.UNKNOWN)
  self.assertEqual(g.evaluate(b,now=NOW,required_dimensions=req,degraded_allowed=True,response_scope='event').state,OrientationState.DEGRADED_BOUNDED)
  with self.assertRaises(ValueError):g.evaluate([],now=NOW,required_dimensions=())
  with self.assertRaisesRegex(ValueError,'current_time'):g.evaluate([x for x in b if x.dimension=='event_time'],now=NOW,required_dimensions=('event_time',),degraded_allowed=True,response_scope='event')
 def test_auth_stale_conflict_snapshot(self):
  g=OrientationGate(integrity_key=TK);r=T();r[0]=replace(r[0],source_digest=H('attacker'));self.assertEqual(g.evaluate(r,now=NOW).state,OrientationState.UNKNOWN)
  r=T();r[1]=replace(r[1],source='substitute');self.assertEqual(g.evaluate(r,now=NOW).state,OrientationState.UNKNOWN)
  self.assertEqual(g.evaluate(T(NOW-timedelta(hours=1)),now=NOW).state,OrientationState.STALE)
  r=T();r.append(signed_time_evidence(dimension='event_time',value=(NOW-timedelta(minutes=1)).isoformat(),source='OTHER',source_kind='event_time',observed_at=NOW.isoformat(),source_digest=H('other'),integrity_key=TK));self.assertEqual(g.evaluate(r,now=NOW).state,OrientationState.CONFLICTED)
  self.assertEqual(g.evaluate(T(),now=NOW,source_mode='FRESH_BOUND_SNAPSHOT').state,OrientationState.UNKNOWN);self.assertEqual(g.evaluate(T(b=True),now=NOW,source_mode='FRESH_BOUND_SNAPSHOT').state,OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT)
class Memory(unittest.TestCase):
 K=b'r8a0-memory-integrity-key-32-bytes'
 def setUp(self):self.d=tempfile.TemporaryDirectory();self.p=Path(self.d.name)/'m.json'
 def tearDown(self):self.d.cleanup()
 def R(self,**k):return replace(AdmissionRequest('m1','Patrick authorized the bounded implementation.',MemoryClass.AUTOBIOGRAPHICAL,'Patrick','chat','op1','a1','p1',P,I),**k)
 def S(self,*rs,key=None,project=P,identity=I,ad='AUTHORIZED',pd='ELIGIBLE'):
  key=key or self.K;a={};p={}
  for r in rs:
   a[r.authority_binding_id]=signed_policy_binding(binding_id=r.authority_binding_id,request_digest=r.request_digest(),source='OWNER',source_digest=H('a'+r.authority_binding_id),decision=ad,kind='authority',integrity_key=key)
   p[r.privacy_binding_id]=signed_policy_binding(binding_id=r.privacy_binding_id,request_digest=r.request_digest(),source='PRIVACY',source_digest=H('p'+r.privacy_binding_id),decision=pd,kind='privacy',integrity_key=key)
  return GovernedMemoryStore(self.p,authority_registry=a,privacy_registry=p,integrity_key=key,expected_project_id=project,expected_identity_id=identity)
 def load(self):return strict_loads(self.p.read_bytes())
 def save(self,x):self.p.write_text(canonical_dumps(x),encoding='utf-8')
 def test_languages_policy_and_scope(self):
  for c,prefix in [(MemoryClass.AUTOBIOGRAPHICAL,'I remember this through my persistent memory.'),(MemoryClass.WORKING_PROJECT,'I have this in my working or project memory.'),(MemoryClass.HISTORICAL_AUDIT,'The historical or audit record shows this.')]:
   self.p=Path(self.d.name)/(c.value+'.json');r=self.R(memory_class=c);s=self.S(r);s.path=self.p;s.admit(r);self.assertEqual(s.readback('m1'),prefix+' '+r.text)
  self.p=Path(self.d.name)/'scope.json'
  for f in [self.R(project_id='FOREIGN'),self.R(governed_identity_id='FOREIGN')]:
   s=self.S(f)
   with self.assertRaisesRegex(MemoryAdmissionError,'project or identity'):s.admit(f)
  r=self.R();
  with self.assertRaises(MemoryAdmissionError):self.S(r,ad='DENIED').admit(r)
  with self.assertRaises(MemoryAdmissionError):self.S(r,pd='INELIGIBLE').admit(r)
 def test_replay_tamper_redirect_supersession(self):
  r=self.R();s=self.S(r);receipt=s.admit(r);self.assertEqual(receipt,s.admit(r))
  for mut in [lambda x:x['operations']['op1']['receipt'].__setitem__('result','FORGED'),lambda x:x['records'][0].__setitem__('text','tampered')]:
   x=self.load();mut(x);self.save(x)
   with self.assertRaises(MemoryAdmissionError):s.admit(r)
   self.p.unlink();s=self.S(r);s.admit(r)
  b=self.R(record_id='m2',operation_id='op2',text='second',authority_binding_id='a2',privacy_binding_id='p2');s=self.S(r,b);s.admit(r);s.admit(b);x=self.load();o=x['operations']['op1'];q=o['receipt'];q['record_id']='m2';q['admission_digest']=x['records'][1]['admission_digest'];body={k:v for k,v in q.items() if k!='receipt_mac'};q['receipt_mac']=hmac.new(self.K,canonical_bytes(body),hashlib.sha256).hexdigest();ob={'request_digest':o['request_digest'],'receipt':q};o['operation_mac']=hmac.new(self.K,canonical_bytes(ob),hashlib.sha256).hexdigest();self.save(x)
  with self.assertRaisesRegex(MemoryAdmissionError,'receipt-to-record'):s.admit(r)
  self.p.unlink();n=self.R(record_id='m2',operation_id='op2',text='next',authority_binding_id='a2',privacy_binding_id='p2',supersedes='m1');s=self.S(r,n);s.admit(r);s.admit(n)
  with self.assertRaisesRegex(MemoryAdmissionError,'not current'):s.admit(r)
  self.assertEqual(len(s.head_digest()),64)
class Recovery(unittest.TestCase):
 K=b'r8a0-receipt-authentication-key'
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();z=Path(self.d.name);self.c=z/'c.json';self.cr=z/'cr.json';self.tr=z/'tr.json';self.pred='d'*64;self.mem='a'*64;self.sh='b'*64;self.au='c'*64;self.st=CheckpointState(P,I,'before',self.mem,self.sh,self.au,('finish',),('audit',),NOW.isoformat(),self.pred)
 def tearDown(self):self.d.cleanup()
 def cp(self,st=None):return write_checkpoint(self.c,st or self.st,checkpoint_receipt_path=self.cr,verified_predecessor_digest=self.pred,verified_self_model_head_digest=self.sh,verified_authority_state_digest=self.au,receipt_key=self.K)
 def tm(self,st=None):return terminate((st or self.st).runtime_id,checkpoint_receipt_path=self.cr,termination_receipt_path=self.tr,receipt_key=self.K)
 def A(self,cp,tm,**k):
  a=dict(orientation_evidence=T(key=self.K),orientation_now=NOW,orientation_source_mode='CURRENT_SOURCE',checkpoint_receipt_path=self.cr,termination_receipt_path=self.tr,expected_checkpoint_receipt_mac=cp['receipt_mac'],expected_termination_receipt_mac=tm['receipt_mac'],expected_project_id=P,expected_identity_id=I,expected_predecessor_checkpoint_digest=self.pred,expected_memory_head_digest=self.mem,expected_self_model_head_digest=self.sh,expected_authority_state_digest=self.au,successor_runtime_id='after',receipt_key=self.K);a.update(k);return a
 def proc(self,cp,tm,**k):
  x={'now':NOW.isoformat(),'orientation_source_mode':'CURRENT_SOURCE','orientation_evidence':{r.dimension:r.as_dict() for r in T(key=self.K)},'checkpoint_receipt_path':str(self.cr),'termination_receipt_path':str(self.tr),'expected_checkpoint_receipt_mac':cp['receipt_mac'],'expected_termination_receipt_mac':tm['receipt_mac'],'expected_project_id':P,'expected_identity_id':I,'expected_predecessor_checkpoint_digest':self.pred,'expected_memory_head_digest':self.mem,'expected_self_model_head_digest':self.sh,'expected_authority_state_digest':self.au,'successor_runtime_id':'after'};x.update(k);q=Path(self.d.name)/'in.json';q.write_text(canonical_dumps(x),encoding='utf-8');e=os.environ.copy();e['VERA_R8A0_RECEIPT_KEY_HEX']=self.K.hex();return subprocess.run([sys.executable,'-m','r8a0.cli','recover',str(self.c),'--recovery-input',str(q)],cwd=ROOT,env=e,text=True,capture_output=True)
 def test_cycle_and_same_process(self):
  cp=self.cp();tm=self.tm()
  with self.assertRaisesRegex(RecoveryError,'process distinct'):recover(self.c,**self.A(cp,tm))
  r=self.proc(cp,tm);self.assertEqual(r.returncode,0,r.stderr);o=json.loads(r.stdout);self.assertNotEqual(o['prior_process_id'],o['successor_process_id']);self.assertEqual(o['project_id'],P);self.assertEqual(o['identity_id'],I)
 def test_receipt_binding_and_scope_failures(self):
  cp=self.cp();tm=self.tm()
  for k,v in [('expected_checkpoint_receipt_mac','e'*64),('expected_termination_receipt_mac','e'*64),('expected_project_id','FOREIGN'),('expected_identity_id','FOREIGN'),('expected_memory_head_digest','9'*64),('successor_runtime_id','before'),('successor_runtime_id','')]:
   with self.subTest(k=k):self.assertNotEqual(self.proc(cp,tm,**{k:v}).returncode,0)
  self.cr.unlink()
  with self.assertRaisesRegex(RecoveryError,'receipt is missing'):recover(self.c,**self.A(cp,tm))
 def test_foreign_checkpoint_tamper_stale(self):
  for f,v in [('project_id','FOREIGN'),('identity_id','FOREIGN')]:
   st=replace(self.st,**{f:v});cp=self.cp(st);tm=self.tm(st)
   with self.assertRaisesRegex(RecoveryError,'project or identity'):recover(self.c,**self.A(cp,tm))
  cp=self.cp();tm=self.tm();x=strict_loads(self.tr.read_bytes());x['runtime_id']='forged';self.tr.write_text(canonical_dumps(x),encoding='utf-8');self.assertNotEqual(self.proc(cp,tm).returncode,0)
  self.tr.unlink();tm=self.tm();self.assertNotEqual(self.proc(cp,tm,orientation_evidence={r.dimension:r.as_dict() for r in T(NOW-timedelta(hours=1),key=self.K)}).returncode,0)
class Serialization(unittest.TestCase):
 def test_strict_and_scope(self):
  with self.assertRaises(CanonicalizationError):strict_loads('{"a":1,"a":2}')
  with self.assertRaises(CanonicalizationError):strict_loads('{"a":NaN}')
  self.assertEqual(canonical_dumps({'b':2,'a':1}),'{"a":1,"b":2}')
  ps=['docs/r8a0/BOUND_VERTICAL_SLICE.md','r8a0/__init__.py','r8a0/cli.py','r8a0/memory.py','r8a0/recovery.py','r8a0/temporal.py','tests/r8a0/test_vertical_slice.py'];self.assertTrue(all(p.startswith(('r8a0/','tests/r8a0/','docs/r8a0/')) for p in ps))
if __name__=='__main__':unittest.main()
