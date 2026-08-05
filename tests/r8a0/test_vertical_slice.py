from __future__ import annotations
import hashlib,json,os,subprocess,sys,tempfile,threading,unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from r8a0.canonical import CanonicalizationError,canonical_bytes,canonical_dumps,strict_loads
from r8a0.memory import AdmissionRequest,GovernedMemoryStore,MemoryAdmissionError,MemoryClass,StaleMemoryHead
from r8a0.recovery import CheckpointState,RecoveryError,recover,write_checkpoint,write_exit_attestation,write_termination_intent
from r8a0.lifecycle import LifecycleRegistry,LifecycleRegistryError
from r8a0.temporal import CURRENT_TIME,REQUIRED_DIMENSIONS,OrientationGate,OrientationState,TimeEvidence
NOW=datetime.now(timezone.utc).replace(microsecond=0);P='VERA_COGNITIVE_REPAIR_R8A0';I='VERA'
K={
'AUTH':('a5a1af06e1784531a4b712eab5cc752f72343f7a733bd3ff83f9efb8c20075070742ed4bae3cfe93374f8cf61c9b0955e33de947499eff4b57d5bbab590466b1b489c428c7fed7f8a3a6a0527d827638f0573af9f847174fa0b17dbbfaa0709b8faecc8b6ffd9fcd9f116172118fd8f14b0a03bcdfa06b345f88d7f42f12f327','567f2e3968abf76eaa7754f0afca3b7470aeaa6bd71bea6568d5b0840b0454193c888e05d4d3539b2bea6651ecb46656ad1a9ae5b8a3c8ecdecce679e03df5268719dbc94dd3dcaf9ed756caa615e74305cccce3ba87804e02a4fb8dee6a2bb1afa177e5668511d8440bfb0fa7d2ed9a8594706bdc3e66c2d15da409a723fba9'),
'PRIV':('cfa0d91dd3fa58897cad422c01da168cfa5cd912c6b8b59190c93836af319b298bb168329d02e35b81ac58121d54528ec8f730cdd6654e5a571bdf91b5e786049415f44ffa5bd2c9247911655fa44aeb28258c4ff3f5acd1fe4da9a28e7371d40a1e2d53c6d8e5bda96e86b03c3c4319c58f4ab9b1b99e0365bf934f0d9a02a7','7d9096fd74ff07a04e2831c68f702707273a1385496cd751ab3025b0dc8eb17994a3bb92306658bd3454d8064c7a7c5b21aa6c776f5b60e13da0fbba113a6d4f2c823b7211d2cebc5359cc7ccef75fd9ada133b9d4149bd3f860a774fe8cf39e479efab0bba416de7440b92cffa26071b591809994bfa6f9c276b6b0c3a0ad81'),
'TIME':('cf0074096a67475691b2477fc4b78d06fdf87608580aaea9f21cc6820e6b27678571e744d86e58e8dfe74c4f6b4f51fc0ded6e678ca71a73d32b0c3c1e32b5743dcd549e1aa340f5676e77f9e0d7456db24c611009f0e15a250d2e1333bb5534436a67d6a8d8bfca19b1ae81870852a36e760eab8485fd078ef5592c860cba2f','403de0c5274b841d3ebc386a53afaf49d339efcfa91b2f97b876ebb8632728247d8a9afe87b8bf490e6be707e2c2cc2bd05ab65fd68be9aeb6836e999db9990c3a5a0a516c784e127c9723e343ef2b00d7dc3723e38b03dd8badf659f48ca6800663b2cc2cf24efc0600ae04f6090fc2a77b0fdca92ba205dcba23e04c43b8b1'),
'STATE':('bdf01f7076ddf91aa0f60545f9c44eabcd322f7dbda1e8beb4c2627554daa7cbf3b22e00c183d3fa19a86e2b8981fdfe70c8cea3d6751689cf0376af0d8a0aa3484adb00321f00ea5f24df93e213d527f648089b12f80ab2e0b3f1bf1a72cda3ddf37ccc60c3da007aed983f46042f46d15a5272e476abc7e75554d7901d2093','12a4dc612cb9d336e2efe34aa01ebdde2d512cca39f007a99892b019764fd442b7d418a1e85ce954d669eb0e88fbe293b43c71d4313be30f79eb8c1dd8c5610fc4795558d465d74a8a53b92e670ef408bbd6ba39752003e8eb56c2bf086fc7511f1ff5a4b7162702ca0cf5051093e9c1dc6531968abee16678270c97a3cf8379'),
'LIFE':('d03bb1d372d8210e6b6be6c88e9a95fe38ddc2f81be4dc7c71e4327c8ef4b324e407ff0aa314cd6038c0598fbccc59a5c396f4d43cd5114638d98b8e5196e1c5be8704e55b7f21e2ee3684e45062ef0ba72a4e9f3c15b1b2bd6d20a027f11746aa761b0f937f63430fde63c89ecc72d1859ec4c3ea9829872bddd687b0e8082d','afdcca896f23b37f4f1ff8f006e7eda79ff5427572716df937e2e6f4a5736a5cccad282b9ea1b1f602d8088bc982b86fb3e928ea9a59c4560f2b439eb5af7d0a93a96182405f7f92934f3399001fef24db3b0990fc918ed1e7a05e3e7d01109e0a4ea46417edc2e9e7f26c04e551dd0645a8cd1ef835bfd97a125e51d746bfad'),
'SUP':('b0f5e7077ab1e1348624853cda65c5dec3f3bedd6e92ceb81ffd2eb72ab67fc8e5d03861982a174a14ed149d400ea264b85e807178a77cfccac872ea1bfb2a09a6475cf17ba5e37b2e4bceaefa8010b7638c9a99a3bb2e5319d772e51905921d7caaa08be1e7b6d786b337eca00a272bf014cf2ca4a710c52f19c56ac6f176e5','2920fe113ef318e49c48e0aec413e3696321c3bab3786b935fdbf87f99edd0c560a484762a679e0219db006f8bf3daca8e0f68caf6bff6ccca54cc609d20432497dbfe3095b55ab8cedc2ade8e4b8fb8c82f09076ff6a769dc30ae756154007fb9edaf4f086eacf1ca24cba7a58d3df78ec10ec564a0c21de5e1ce52fdce5a1')}
DER=bytes.fromhex('3031300d060960864801650304020105000420')
def pub(name):return {'key_id':name.lower(),'n_hex':K[name][0],'e':65537}
def sign(payload,name):
 n=int(K[name][0],16);d=int(K[name][1],16);k=(n.bit_length()+7)//8;tail=DER+hashlib.sha256(canonical_bytes(payload)).digest();em=b'\0\1'+b'\xff'*(k-len(tail)-3)+b'\0'+tail;return format(pow(int.from_bytes(em,'big'),d,n),'x')
def signed(body,name,issuer):
 x=dict(body)|{'issuer':issuer,'key_id':name.lower()};return x|{'signature':sign(x,name)}
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def time_rows_at(at,bounded=False):
 lo=(at-timedelta(minutes=1)).isoformat() if bounded else None;hi=(at+timedelta(minutes=1)).isoformat() if bounded else None;out=[]
 for d in REQUIRED_DIMENSIONS:
  body={'dimension':d,'value':at.isoformat(),'source':'clock' if d==CURRENT_TIME else d,'source_kind':d,'observed_at':at.isoformat(),'source_digest':h(d),'source_key_id':'time','lower_bound':lo,'upper_bound':hi};out.append(TimeEvidence(**body,source_signature=sign(body,'TIME')))
 return out
def time_rows(bounded=False):return time_rows_at(NOW,bounded)
class TemporalTests(unittest.TestCase):
 def test_scope_auth_and_selection(self):
  g=OrientationGate(trusted_source_keys={'clock':pub('TIME'),**{d:pub('TIME') for d in REQUIRED_DIMENSIONS if d!=CURRENT_TIME}});self.assertEqual(g.evaluate(time_rows(),now=NOW).state,OrientationState.COMPLETE)
  req=(CURRENT_TIME,'event_time');b=[x for x in time_rows(True) if x.dimension in req]
  q=g.evaluate(b,now=NOW,required_dimensions=req,degraded_allowed=True,response_scope='event');self.assertEqual(q.state,OrientationState.DEGRADED_BOUNDED);self.assertEqual(len(q.supporting_evidence_ids),2)
  self.assertEqual(g.evaluate(b,now=NOW,required_dimensions=req,degraded_allowed=True,response_scope='   ').state,OrientationState.UNKNOWN)
  with self.assertRaisesRegex(ValueError,'current_time'):g.evaluate([x for x in b if x.dimension=='event_time'],now=NOW,required_dimensions=('event_time',))
  dup=b+[b[1]];self.assertEqual(g.evaluate(dup,now=NOW,required_dimensions=req,degraded_allowed=True,response_scope='event').state,OrientationState.CONFLICTED)
  bad=list(time_rows());bad[0]=replace(bad[0],source_digest=h('forged'));self.assertEqual(g.evaluate(bad,now=NOW).state,OrientationState.UNKNOWN)
  old=NOW-timedelta(hours=1);body={'dimension':CURRENT_TIME,'value':old.isoformat(),'source':'clock','source_kind':CURRENT_TIME,'observed_at':NOW.isoformat(),'source_digest':h('old-clock'),'source_key_id':'time','lower_bound':None,'upper_bound':None};oldrow=TimeEvidence(**body,source_signature=sign(body,'TIME'));rows=time_rows();rows[0]=oldrow;self.assertEqual(g.evaluate(rows,now=NOW).state,OrientationState.STALE)
class MemoryTests(unittest.TestCase):
 SK=b'store-integrity-key-material-32bytes';RH={'authority':h('auth-head'),'privacy':h('privacy-head')}
 def setUp(self):self.d=tempfile.TemporaryDirectory();self.p=Path(self.d.name)/'memory.json'
 def tearDown(self):self.d.cleanup()
 def request(self,n='1',cls=MemoryClass.AUTOBIOGRAPHICAL):return AdmissionRequest('m'+n,'text'+n,cls,'Patrick','chat','op'+n,'a'+n,'p'+n,P,I)
 def policies(self,*rs):
  a={};p={}
  for r in rs:
   ab={'binding_id':r.authority_binding_id,'request_digest':r.request_digest(),'source':'owner','source_digest':h('a'+r.record_id),'decision':'AUTHORIZED','kind':'authority','registry_head_digest':self.RH['authority']};a[r.authority_binding_id]=signed(ab,'AUTH','auth-issuer')
   pb={'binding_id':r.privacy_binding_id,'request_digest':r.request_digest(),'source':'privacy','source_digest':h('p'+r.record_id),'decision':'ELIGIBLE','kind':'privacy','registry_head_digest':self.RH['privacy']};p[r.privacy_binding_id]=signed(pb,'PRIV','privacy-issuer')
  return a,p
 def store(self,*rs):
  a,p=self.policies(*rs);return GovernedMemoryStore(self.p,authority_registry=a,privacy_registry=p,trusted_policy_keys={'auth-issuer':pub('AUTH'),'privacy-issuer':pub('PRIV')},expected_registry_heads=self.RH,store_integrity_key=self.SK,expected_project_id=P,expected_identity_id=I)
 def test_external_policy_and_receipt_class(self):
  for cls in MemoryClass:
   self.p=Path(self.d.name)/(cls.value+'.json');r=self.request(cls=cls);s=self.store(r);head=s.current_head();q=s.admit(r,expected_store_head=head);self.assertEqual(q,s.admit(r,expected_store_head=head));self.assertEqual(q['schema'],'VERA_R8A0_GOVERNED_MEMORY_ADMISSION_RECEIPT_V1');self.assertEqual(q['memory_class'],cls.value)
  self.p=Path(self.d.name)/'fake.json';r=self.request();a,p=self.policies(r);a['a1']['signature']='1';s=GovernedMemoryStore(self.p,authority_registry=a,privacy_registry=p,trusted_policy_keys={'auth-issuer':pub('AUTH'),'privacy-issuer':pub('PRIV')},expected_registry_heads=self.RH,store_integrity_key=self.SK,expected_project_id=P,expected_identity_id=I)
  with self.assertRaisesRegex(MemoryAdmissionError,'signature'):s.admit(r,expected_store_head=s.current_head())
 def test_cas_concurrency_and_rollback(self):
  a,b=self.request('1'),self.request('2');s1=self.store(a,b);s2=self.store(a,b);head=s1.current_head();bar=threading.Barrier(2)
  def work(s,r):bar.wait();return s.admit(r,expected_store_head=head)
  with ThreadPoolExecutor(2) as ex:
   fs=[ex.submit(work,s1,a),ex.submit(work,s2,b)];results=[];errors=[]
   for f in fs:
    try:results.append(f.result())
    except Exception as e:errors.append(e)
  self.assertEqual(len(results),1);self.assertTrue(any(isinstance(e,StaleMemoryHead) for e in errors));winner=s1.current_head();old=self.p.read_bytes();loser=b if results[0]['record_id']=='m1' else a;q=s1.admit(loser,expected_store_head=winner);latest=q['store_head'];self.assertEqual(s1.verify_head(latest),latest);cur=self.p.read_bytes();x=strict_loads(cur);x['records'].pop();x['operations'].pop(next(iter(x['operations'])));self.p.write_text(canonical_dumps(x),encoding='utf-8')
  with self.assertRaises(MemoryAdmissionError):s1.current_head()
  self.p.write_bytes(old)
  with self.assertRaises(StaleMemoryHead):s1.readback(results[0]['record_id'],expected_store_head=latest)
  self.p.write_bytes(cur);data=strict_loads(self.p.read_bytes());data['records'][0]['text']='unrelated-corruption';sealed=s1._seal_store({k:v for k,v in data.items() if k not in {'head_digest','head_mac'}});self.p.write_text(canonical_dumps(sealed),encoding='utf-8')
  with self.assertRaises(MemoryAdmissionError):s1.readback(data['records'][-1]['record_id'],expected_store_head=sealed['head_digest'])
  self.p.write_bytes(cur);data=strict_loads(self.p.read_bytes());data['operations'].pop(next(iter(data['operations'])));sealed=s1._seal_store({k:v for k,v in data.items() if k not in {'head_digest','head_mac'}});self.p.write_text(canonical_dumps(sealed),encoding='utf-8')
  with self.assertRaisesRegex(MemoryAdmissionError,'graph mismatch'):s1.current_head()
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();z=Path(self.d.name);self.cp=z/'cp.json';self.cr=z/'cr.json';self.ti=z/'ti.json';self.ex=z/'exit.json';self.lr=z/'lifecycle.json';self.lk=b'lifecycle-registry-key-material';self.pred='d'*64;self.mem='a'*64;self.sh='b'*64;self.au='c'*64;self.st=CheckpointState(P,I,'before','nonce-1',self.mem,self.sh,self.au,('finish',),('audit',),NOW.isoformat(),self.pred)
  self.statekeys={'state-issuer':pub('STATE')};self.lifekeys={'life-issuer':pub('LIFE')};self.supkeys={'supervisor':pub('SUP')};self.timekeys={'clock':pub('TIME'),**{d:pub('TIME') for d in REQUIRED_DIMENSIONS if d!=CURRENT_TIME}}
 def tearDown(self):self.d.cleanup()
 def attest(self,st=None):
  st=st or self.st;roots={'predecessor_checkpoint':st.predecessor_checkpoint_digest,'memory_head':st.memory_head_digest,'self_model_head':st.self_model_head_digest,'authority_state':st.authority_state_digest};return {k:signed({'schema':'VERA_R8A0_STATE_ROOT_ATTESTATION_V1','kind':k,'project_id':st.project_id,'identity_id':st.identity_id,'digest':v,'generation':1,'observed_at':NOW.isoformat()},'STATE','state-issuer') for k,v in roots.items()}
 def direct(self,st=None,pid=None):
  st=st or self.st;cp=write_checkpoint(self.cp,st,checkpoint_receipt_path=self.cr,state_attestations=self.attest(st),trusted_state_keys=self.statekeys,lifecycle_issuer='life-issuer',lifecycle_key_id='life',lifecycle_signer=lambda x:sign(x,'LIFE'));ti=write_termination_intent(checkpoint_receipt_path=self.cr,termination_intent_path=self.ti,trusted_lifecycle_keys=self.lifekeys,lifecycle_issuer='life-issuer',lifecycle_key_id='life',lifecycle_signer=lambda x:sign(x,'LIFE'),process_id=pid or os.getpid());ex=write_exit_attestation(path=self.ex,checkpoint_receipt=cp,termination_intent=ti,exit_code=0,observed_at=NOW.isoformat(),supervisor_issuer='supervisor',supervisor_key_id='sup',supervisor_signer=lambda x:sign(x,'SUP'));return cp,ti,ex
 def args(self,cp,ti,ex,**kw):
  a=dict(orientation_evidence=time_rows(),orientation_source_mode='CURRENT_SOURCE',trusted_temporal_keys=self.timekeys,checkpoint_receipt_path=self.cr,termination_intent_path=self.ti,exit_attestation_path=self.ex,trusted_lifecycle_keys=self.lifekeys,trusted_supervisor_keys=self.supkeys,trusted_state_keys=self.statekeys,expected_checkpoint_receipt_signature=cp['signature'],expected_termination_intent_signature=ti['signature'],expected_exit_attestation_signature=ex['signature'],expected_project_id=P,expected_identity_id=I,expected_predecessor_checkpoint_digest=self.pred,expected_memory_head_digest=self.mem,expected_self_model_head_digest=self.sh,expected_authority_state_digest=self.au,successor_runtime_id='after',lifecycle_registry_path=self.lr,lifecycle_registry_key=self.lk,expected_lifecycle_registry_head=LifecycleRegistry(self.lr,self.lk).current_head());a.update(kw);return a
 def test_live_predecessor_and_state_attestation(self):
  cp,ti,ex=self.direct()
  with self.assertRaisesRegex(RecoveryError,'remains alive'):recover(self.cp,**self.args(cp,ti,ex))
  cp,ti,ex=self.direct(pid=99999999)
  with self.assertRaisesRegex(RecoveryError,'fresh temporal authority'):recover(self.cp,**self.args(cp,ti,ex,orientation_evidence=time_rows_at(NOW-timedelta(hours=1))))
  bad=self.attest();bad['memory_head']=dict(bad['memory_head']);bad['memory_head']['signature']='1'
  with self.assertRaisesRegex(RecoveryError,'verification'):write_checkpoint(self.cp,self.st,checkpoint_receipt_path=self.cr,state_attestations=bad,trusted_state_keys=self.statekeys,lifecycle_issuer='life-issuer',lifecycle_key_id='life',lifecycle_signer=lambda x:sign(x,'LIFE'))
 def test_supervised_exit_and_foreign_scope(self):
  z=Path(self.d.name);inp=z/'input.json';inp.write_text(canonical_dumps({'state':self.st.payload(),'state_attestations':self.attest(),'trusted_state_keys':self.statekeys,'trusted_lifecycle_keys':self.lifekeys}),encoding='utf-8');env=os.environ.copy()
  for prefix,name,issuer,kid in [('VERA_R8A0_LIFECYCLE','LIFE','life-issuer','life'),('VERA_R8A0_SUPERVISOR','SUP','supervisor','sup')]:env[prefix+'_ISSUER']=issuer;env[prefix+'_KEY_ID']=kid;env[prefix+'_N_HEX']=K[name][0];env[prefix+'_D_HEX']=K[name][1]
  r=subprocess.run([sys.executable,'-m','r8a0.cli','supervise','--input',str(inp),'--checkpoint',str(self.cp),'--checkpoint-receipt',str(self.cr),'--termination-intent',str(self.ti),'--exit-attestation',str(self.ex)],cwd=ROOT,env=env,text=True,capture_output=True);self.assertEqual(r.returncode,0,r.stderr);cp,ti,ex=map(lambda p:strict_loads(p.read_bytes()),(self.cr,self.ti,self.ex));head=LifecycleRegistry(self.lr,self.lk).current_head();out=recover(self.cp,**self.args(cp,ti,ex,expected_lifecycle_registry_head=head));self.assertEqual(out['result'],'RECOVERED_FROM_VERIFIED_CHECKPOINT')
  with self.assertRaises(LifecycleRegistryError):recover(self.cp,**self.args(cp,ti,ex,expected_lifecycle_registry_head=out['lifecycle_registry_head'],successor_runtime_id='fork'))
  self.assertEqual(LifecycleRegistry(self.lr,self.lk).event(ti['signature'])['successor_runtime_id'],'after')
  with self.assertRaisesRegex(RecoveryError,'scope or state-root'):recover(self.cp,**self.args(cp,ti,ex,expected_project_id='FOREIGN',expected_lifecycle_registry_head=out['lifecycle_registry_head']))
class StrictTests(unittest.TestCase):
 def test_json_and_scope(self):
  with self.assertRaises(CanonicalizationError):strict_loads('{"a":1,"a":2}')
  with self.assertRaises(CanonicalizationError):strict_loads('{"a":NaN}')
  self.assertEqual(canonical_dumps({'b':2,'a':1}),'{"a":1,"b":2}')
if __name__=='__main__':unittest.main()
