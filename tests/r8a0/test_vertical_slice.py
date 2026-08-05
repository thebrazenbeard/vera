from __future__ import annotations

import hashlib
import hmac
import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from r8a0.canonical import CanonicalizationError, canonical_bytes, canonical_dumps, strict_loads
from r8a0.memory import AdmissionRequest, GovernedMemoryStore, MemoryAdmissionError, MemoryClass, signed_policy_binding
from r8a0.recovery import CheckpointState, RecoveryError, recover, terminate, write_checkpoint
from r8a0.temporal import CURRENT_TIME, REQUIRED_DIMENSIONS, OrientationGate, OrientationState, TimeEvidence, current_evidence

NOW = datetime(2026, 8, 5, 21, 20, tzinfo=timezone.utc)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def times(at: datetime = NOW, *, bounded: bool = False) -> list[TimeEvidence]:
    value = at.isoformat()
    lo = (at - timedelta(minutes=1)).isoformat() if bounded else None
    hi = (at + timedelta(minutes=1)).isoformat() if bounded else None
    rows = current_evidence(at, source_digest=sha("clock"), lower_bound=lo, upper_bound=hi)
    rows += [TimeEvidence(d, value, f"SRC_{d}", d, value, sha(d), lo, hi) for d in REQUIRED_DIMENSIONS if d != CURRENT_TIME]
    return rows


class TemporalTests(unittest.TestCase):
    def test_complete_and_wall_clock_only(self):
        self.assertEqual(OrientationGate().evaluate(times(), now=NOW).state, OrientationState.COMPLETE)
        only_clock = OrientationGate().evaluate(current_evidence(NOW, source_digest=sha("clock")), now=NOW)
        self.assertEqual(only_clock.state, OrientationState.UNKNOWN)
        self.assertEqual(set(only_clock.missing_dimensions), set(REQUIRED_DIMENSIONS) - {CURRENT_TIME})

    def test_missing_never_degrades(self):
        result = OrientationGate().evaluate(times()[:-1], now=NOW, degraded_allowed=True, response_scope="event comparison")
        self.assertEqual(result.state, OrientationState.UNKNOWN)

    def test_partial_scope_requires_scope_and_bounds(self):
        required = (CURRENT_TIME, "event_time")
        unbounded = [r for r in times() if r.dimension in required]
        bounded = [r for r in times(bounded=True) if r.dimension in required]
        gate = OrientationGate()
        self.assertEqual(gate.evaluate(bounded, now=NOW, required_dimensions=required, degraded_allowed=True).state, OrientationState.UNKNOWN)
        self.assertEqual(gate.evaluate(unbounded, now=NOW, required_dimensions=required, degraded_allowed=True, response_scope="event comparison").state, OrientationState.UNKNOWN)
        result = gate.evaluate(bounded, now=NOW, required_dimensions=required, degraded_allowed=True, response_scope="event comparison")
        self.assertEqual(result.state, OrientationState.DEGRADED_BOUNDED)
        self.assertTrue(result.bounded_claims_only)

    def test_snapshot_wrong_kind_stale_conflict_and_partial_bounds(self):
        gate = OrientationGate()
        self.assertEqual(gate.evaluate(times(), now=NOW, source_mode="FRESH_BOUND_SNAPSHOT").state, OrientationState.UNKNOWN)
        self.assertEqual(gate.evaluate(times(bounded=True), now=NOW, source_mode="FRESH_BOUND_SNAPSHOT").state, OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT)
        rows = times(); rows[1] = replace(rows[1], source_kind=CURRENT_TIME)
        self.assertEqual(gate.evaluate(rows, now=NOW).state, OrientationState.UNKNOWN)
        self.assertEqual(gate.evaluate(times(NOW - timedelta(hours=1)), now=NOW).state, OrientationState.STALE)
        rows = times(); rows.append(TimeEvidence("event_time", (NOW - timedelta(minutes=1)).isoformat(), "OTHER", "event_time", NOW.isoformat(), sha("other")))
        self.assertEqual(gate.evaluate(rows, now=NOW).state, OrientationState.CONFLICTED)
        with self.assertRaises(ValueError):
            TimeEvidence("event_time", NOW.isoformat(), "SRC", "event_time", NOW.isoformat(), sha("x"), NOW.isoformat()).validate()


class MemoryTests(unittest.TestCase):
    KEY = b"r8a0-memory-integrity-key-32-bytes"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.path = Path(self.tmp.name) / "memory.json"

    def tearDown(self): self.tmp.cleanup()

    def req(self, **kw) -> AdmissionRequest:
        return replace(AdmissionRequest("m1", "Patrick authorized the bounded implementation.", MemoryClass.AUTOBIOGRAPHICAL, "Patrick", "active-chat", "op-1", "auth-1", "privacy-1"), **kw)

    def store(self, *requests: AdmissionRequest, auth="AUTHORIZED", privacy="ELIGIBLE", key: bytes | None = None) -> GovernedMemoryStore:
        key = key or self.KEY; ar = {}; pr = {}
        for r in requests:
            ar[r.authority_binding_id] = signed_policy_binding(binding_id=r.authority_binding_id, request_digest=r.request_digest(), source="OWNER", source_digest=sha("a"+r.authority_binding_id), decision=auth, kind="authority", integrity_key=key)
            pr[r.privacy_binding_id] = signed_policy_binding(binding_id=r.privacy_binding_id, request_digest=r.request_digest(), source="PRIVACY", source_digest=sha("p"+r.privacy_binding_id), decision=privacy, kind="privacy", integrity_key=key)
        return GovernedMemoryStore(self.path, authority_registry=ar, privacy_registry=pr, integrity_key=key)

    def data(self): return strict_loads(self.path.read_bytes())
    def save(self, data): self.path.write_text(canonical_dumps(data), encoding="utf-8")

    def test_exact_languages(self):
        expected = {
            MemoryClass.AUTOBIOGRAPHICAL: "I remember this through my persistent memory.",
            MemoryClass.WORKING_PROJECT: "I have this in my working or project memory.",
            MemoryClass.HISTORICAL_AUDIT: "The historical or audit record shows this.",
        }
        for cls, prefix in expected.items():
            with self.subTest(cls=cls):
                path = Path(self.tmp.name) / f"{cls.value}.json"
                r = self.req(memory_class=cls)
                s = self.store(r); s.path = path; s.admit(r)
                self.assertEqual(s.readback("m1"), f"{prefix} {r.text}")

    def test_policy_and_request_failures(self):
        r = self.req()
        with self.assertRaises(MemoryAdmissionError): GovernedMemoryStore(self.path, authority_registry={}, privacy_registry={}, integrity_key=self.KEY).admit(r)
        s = self.store(r)
        with self.assertRaises(MemoryAdmissionError): s.admit(replace(r, text="changed"))
        s.authority_registry["auth-1"]["decision"] = "DENIED"
        with self.assertRaisesRegex(MemoryAdmissionError, "authentication"): s.admit(r)
        with self.assertRaises(MemoryAdmissionError): self.store(r, auth="DENIED").admit(r)
        with self.assertRaises(MemoryAdmissionError): self.store(r, privacy="INELIGIBLE").admit(r)
        bad = self.req(provenance="")
        with self.assertRaises(MemoryAdmissionError): self.store(bad).admit(bad)

    def test_replay_and_integrity(self):
        r = self.req(); s = self.store(r); first = s.admit(r)
        self.assertEqual(first, s.admit(r))
        with self.assertRaises(MemoryAdmissionError): s.admit(self.req(text="changed"))
        for mutate, pattern in [
            (lambda d: d["operations"]["op-1"]["receipt"].__setitem__("result", "FORGED"), "operation replay authentication"),
            (lambda d: d["operations"]["op-1"].pop("receipt"), "fields"),
            (lambda d: d["records"][0].__setitem__("text", "tampered"), "record authentication"),
        ]:
            clean = self.data(); mutate(clean); self.save(clean)
            with self.assertRaisesRegex(MemoryAdmissionError, pattern): s.admit(r)
            self.path.unlink(); s = self.store(r); s.admit(r)

    def test_receipt_redirect_is_rejected_even_if_remacced(self):
        a = self.req(); b = self.req(record_id="m2", operation_id="op-2", text="second", authority_binding_id="auth-2", privacy_binding_id="privacy-2")
        s = self.store(a, b); s.admit(a); s.admit(b); d = self.data(); op = d["operations"]["op-1"]; receipt = op["receipt"]
        receipt["record_id"] = "m2"; receipt["admission_digest"] = d["records"][1]["admission_digest"]
        body = {k: v for k, v in receipt.items() if k != "receipt_mac"}; receipt["receipt_mac"] = hmac.new(self.KEY, canonical_bytes(body), hashlib.sha256).hexdigest()
        opbody = {"request_digest": op["request_digest"], "receipt": receipt}; op["operation_mac"] = hmac.new(self.KEY, canonical_bytes(opbody), hashlib.sha256).hexdigest(); self.save(d)
        with self.assertRaisesRegex(MemoryAdmissionError, "receipt-to-record"): s.admit(a)

    def test_revocation_supersession_and_wrong_key(self):
        r = self.req(); s = self.store(r); s.admit(r)
        for registry, ident, kind in [(s.authority_registry, "auth-1", "authority"), (s.privacy_registry, "privacy-1", "privacy")]:
            original = dict(registry[ident]); registry[ident]["decision"] = "REVOKED"
            with self.assertRaises(MemoryAdmissionError): s.readback("m1")
            registry[ident] = original
        successor = self.req(record_id="m2", operation_id="op-2", text="successor", authority_binding_id="auth-2", privacy_binding_id="privacy-2", supersedes="m1")
        s = self.store(r, successor); s.admit(r); s.admit(successor)
        with self.assertRaises(MemoryAdmissionError): s.readback("m1")
        with self.assertRaisesRegex(MemoryAdmissionError, "not current"): s.admit(r)
        self.assertEqual(len(s.head_digest()), 64)
        wrong = self.store(r, key=b"different-memory-key-material")
        with self.assertRaises(MemoryAdmissionError): wrong.readback("m1")


class RecoveryTests(unittest.TestCase):
    KEY = b"r8a0-receipt-authentication-key"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); root = Path(self.tmp.name)
        self.checkpoint_path = root / "checkpoint.json"; self.cp_receipt = root / "checkpoint-receipt.json"; self.term_receipt = root / "termination-receipt.json"
        self.pred, self.mem, self.selfhead, self.auth = "d"*64, "a"*64, "b"*64, "c"*64
        self.state = CheckpointState("VERA_COGNITIVE_REPAIR_R8A0", "VERA", "runtime-before", self.mem, self.selfhead, self.auth, ("finish",), ("audit",), NOW.isoformat(), self.pred)

    def tearDown(self): self.tmp.cleanup()

    def checkpoint(self):
        return write_checkpoint(self.checkpoint_path, self.state, checkpoint_receipt_path=self.cp_receipt, verified_predecessor_digest=self.pred, verified_self_model_head_digest=self.selfhead, verified_authority_state_digest=self.auth, receipt_key=self.KEY)

    def termination(self):
        return terminate(self.state.runtime_id, checkpoint_receipt_path=self.cp_receipt, termination_receipt_path=self.term_receipt, receipt_key=self.KEY)

    def kwargs(self, cp, term, **kw):
        args = dict(orientation_evidence=times(), orientation_now=NOW, orientation_source_mode="CURRENT_SOURCE", checkpoint_receipt_path=self.cp_receipt, termination_receipt_path=self.term_receipt, expected_checkpoint_receipt_mac=cp["receipt_mac"], expected_termination_receipt_mac=term["receipt_mac"], expected_predecessor_checkpoint_digest=self.pred, expected_memory_head_digest=self.mem, expected_self_model_head_digest=self.selfhead, expected_authority_state_digest=self.auth, successor_runtime_id="runtime-after", receipt_key=self.KEY)
        args.update(kw); return args

    def recovery_input(self, cp, term, **kw):
        data = {"now": NOW.isoformat(), "orientation_source_mode": "CURRENT_SOURCE", "orientation_evidence": {r.dimension: r.as_dict() for r in times()}, "checkpoint_receipt_path": str(self.cp_receipt), "termination_receipt_path": str(self.term_receipt), "expected_checkpoint_receipt_mac": cp["receipt_mac"], "expected_termination_receipt_mac": term["receipt_mac"], "expected_predecessor_checkpoint_digest": self.pred, "expected_memory_head_digest": self.mem, "expected_self_model_head_digest": self.selfhead, "expected_authority_state_digest": self.auth, "successor_runtime_id": "runtime-after"}
        data.update(kw); return data

    def run_recover(self, cp, term, **kw):
        p = Path(self.tmp.name) / "recovery-input.json"; p.write_text(canonical_dumps(self.recovery_input(cp, term, **kw)), encoding="utf-8")
        env = os.environ.copy(); env["VERA_R8A0_RECEIPT_KEY_HEX"] = self.KEY.hex()
        return subprocess.run([sys.executable, "-m", "r8a0.cli", "recover", str(self.checkpoint_path), "--recovery-input", str(p)], cwd=ROOT, env=env, text=True, capture_output=True)

    def test_persisted_receipts_and_same_process_rejection(self):
        cp = self.checkpoint(); term = self.termination()
        self.assertTrue(self.cp_receipt.exists() and self.term_receipt.exists())
        with self.assertRaisesRegex(RecoveryError, "process distinct"): recover(self.checkpoint_path, **self.kwargs(cp, term))

    def test_fresh_process_cycle_and_runtime_binding(self):
        root = Path(self.tmp.name); state_input = root / "state.json"
        state_input.write_text(canonical_dumps({"state": self.state.payload(), "verified_predecessor_digest": self.pred, "verified_self_model_head_digest": self.selfhead, "verified_authority_state_digest": self.auth}), encoding="utf-8")
        env = os.environ.copy(); env["VERA_R8A0_RECEIPT_KEY_HEX"] = self.KEY.hex()
        first = subprocess.run([sys.executable, "-m", "r8a0.cli", "checkpoint-terminate", "--state-input", str(state_input), "--checkpoint", str(self.checkpoint_path), "--checkpoint-receipt", str(self.cp_receipt), "--termination-receipt", str(self.term_receipt)], cwd=ROOT, env=env, text=True, capture_output=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        cp, term = strict_loads(self.cp_receipt.read_bytes()), strict_loads(self.term_receipt.read_bytes())
        result = self.run_recover(cp, term, successor_runtime_id="fresh-runtime")
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["successor_runtime_id"], "fresh-runtime")
        self.assertNotEqual(receipt["prior_process_id"], receipt["successor_process_id"])
        supplied = receipt.pop("receipt_mac"); self.assertEqual(supplied, hmac.new(self.KEY, canonical_bytes(receipt), hashlib.sha256).hexdigest())
        receipt["successor_runtime_id"] = "altered"
        self.assertNotEqual(supplied, hmac.new(self.KEY, canonical_bytes(receipt), hashlib.sha256).hexdigest())

    def test_unpersisted_forged_and_tampered_receipts_fail(self):
        cp = self.checkpoint(); term = self.termination()
        self.cp_receipt.unlink()
        with self.assertRaisesRegex(RecoveryError, "checkpoint receipt is missing"): recover(self.checkpoint_path, **self.kwargs(cp, term))
        cp = self.checkpoint(); term = self.termination(); d = strict_loads(self.term_receipt.read_bytes()); d["runtime_id"] = "forged"; self.term_receipt.write_text(canonical_dumps(d), encoding="utf-8")
        result = self.run_recover(cp, term); self.assertNotEqual(result.returncode, 0)

    def test_expected_bindings_and_runtime_failures(self):
        cp = self.checkpoint(); term = self.termination()
        cases = {
            "expected_checkpoint_receipt_mac": "e"*64,
            "expected_termination_receipt_mac": "e"*64,
            "expected_predecessor_checkpoint_digest": "e"*64,
            "expected_memory_head_digest": "9"*64,
            "expected_self_model_head_digest": "e"*64,
            "expected_authority_state_digest": "e"*64,
            "successor_runtime_id": "runtime-before",
        }
        for key, value in cases.items():
            with self.subTest(key=key):
                result = self.run_recover(cp, term, **{key: value}); self.assertNotEqual(result.returncode, 0)
        result = self.run_recover(cp, term, successor_runtime_id=""); self.assertNotEqual(result.returncode, 0)

    def test_wrong_key_corrupt_partial_and_stale_fail(self):
        cp = self.checkpoint(); term = self.termination()
        with self.assertRaises(RecoveryError): recover(self.checkpoint_path, **self.kwargs(cp, term, receipt_key=b"different-receipt-key-material"))
        d = strict_loads(self.checkpoint_path.read_bytes()); d["payload"]["runtime_id"] = "tampered"; self.checkpoint_path.write_text(canonical_dumps(d), encoding="utf-8")
        self.assertNotEqual(self.run_recover(cp, term).returncode, 0)
        self.checkpoint_path.write_text('{"schema":"VERA_R8A0_CHECKPOINT_V2","complete":false}', encoding="utf-8")
        self.assertNotEqual(self.run_recover(cp, term).returncode, 0)
        self.checkpoint_path.unlink(); cp = self.checkpoint(); term = self.termination()
        result = self.run_recover(cp, term, orientation_evidence={r.dimension: r.as_dict() for r in times(NOW - timedelta(hours=1))})
        self.assertNotEqual(result.returncode, 0)


class SerializationAndScopeTests(unittest.TestCase):
    def test_strict_json_and_scope(self):
        with self.assertRaises(CanonicalizationError): strict_loads('{"a":1,"a":2}')
        with self.assertRaises(CanonicalizationError): strict_loads('{"a":NaN}')
        self.assertEqual(canonical_dumps({"b": 2, "a": 1}), '{"a":1,"b":2}')
        paths = ["docs/r8a0/BOUND_VERTICAL_SLICE.md", "r8a0/__init__.py", "r8a0/cli.py", "r8a0/memory.py", "r8a0/recovery.py", "r8a0/temporal.py", "tests/r8a0/test_vertical_slice.py"]
        self.assertTrue(all(p.startswith(("r8a0/", "tests/r8a0/", "docs/r8a0/")) for p in paths))


if __name__ == "__main__": unittest.main()
