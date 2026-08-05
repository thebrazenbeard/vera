from h07_support import *
from h07_support import _recover, _worker

class TemporalScopeTests(unittest.TestCase):

    def test_structured_claim_scope_is_exact_and_receipt_bound(self):
        required = CLAIM_DIMENSIONS['event_timestamp']
        rows = time_rows(NOW, dimensions=required, bounded=True)
        gate = OrientationGate(trusted_source_keys=temporal_keys(required))
        scope = {'scope_id': 'event-check', 'claims': ['event_timestamp']}
        receipt = gate.evaluate(rows, now=NOW, required_dimensions=required, degraded_allowed=True, claim_scope=scope)
        self.assertEqual(receipt.state, OrientationState.DEGRADED_BOUNDED)
        self.assertTrue(receipt.claims_allowed)
        self.assertEqual(receipt.claim_scope, scope)
        self.assertEqual(receipt.claim_scope_digest, canonical_sha256({'claim_scope': scope, 'required_dimensions': list(required)}))
        self.assertEqual(len(receipt.supporting_evidence_ids), len(required))
        with self.assertRaisesRegex(ValueError, 'free-form'):
            gate.evaluate(rows, now=NOW, required_dimensions=required, degraded_allowed=True, response_scope='anything broad and convenient')
        with self.assertRaisesRegex(ValueError, 'unknown claims'):
            gate.evaluate(rows, now=NOW, required_dimensions=required, degraded_allowed=True, claim_scope={'scope_id': 'broad', 'claims': ['everything']})
        with self.assertRaisesRegex(ValueError, 'map exactly'):
            gate.evaluate(rows, now=NOW, required_dimensions=(CURRENT_TIME,), degraded_allowed=True, claim_scope=scope)
        with self.assertRaisesRegex(ValueError, 'scope ID'):
            ClaimScope('   ', ('event_timestamp',)).validate()

class CheckpointSchemaTests(unittest.TestCase):

    def valid_mapping(self):
        return {'project_id': PROJECT, 'identity_id': IDENTITY, 'runtime_id': 'runtime-before', 'runtime_instance_nonce': 'instance-1', 'memory_head_digest': 'a' * 64, 'self_model_head_digest': 'b' * 64, 'authority_state_digest': 'c' * 64, 'active_commitments': ['finish final frozen cycle'], 'unfinished_work': ['Voss exact-head review'], 'created_at': NOW.isoformat(), 'predecessor_checkpoint_digest': 'd' * 64}

    def test_strict_types_are_enforced_before_persistence_and_recovery(self):
        self.assertIsInstance(checkpoint_state_from_mapping(self.valid_mapping()), CheckpointState)
        bad = self.valid_mapping()
        bad['active_commitments'] = 'not-a-list'
        with self.assertRaisesRegex(RecoveryError, 'list of strings'):
            checkpoint_state_from_mapping(bad)
        bad = self.valid_mapping()
        bad['unfinished_work'] = ['valid', 7]
        with self.assertRaisesRegex(RecoveryError, 'nonempty strings'):
            checkpoint_state_from_mapping(bad)
        bad = self.valid_mapping()
        bad['runtime_id'] = 42
        with self.assertRaisesRegex(RecoveryError, 'nonempty string'):
            checkpoint_state_from_mapping(bad)
        state = checkpoint_state_from_mapping(self.valid_mapping())
        malformed = CheckpointState(**{**state.__dict__, 'active_commitments': ('valid', 3)})
        with self.assertRaisesRegex(RecoveryError, 'nonempty strings'):
            malformed.validate()

class WorkflowTests(unittest.TestCase):

    def test_ci_uses_authorized_lineage_and_exact_acceptance_commands(self):
        workflow = (ROOT / '.github/workflows/r8a0-bounded-vertical-slice.yml').read_text()
        self.assertIn('AUTHORIZED_BASE_SHA: "12dd3cb4e3329324885a827506d4f7e8ac25d41d"', workflow)
        self.assertIn('APPROVED_PARENT_SHA: "974cb87f8267b03ced0d68a048c4f0e37a98d713"', workflow)
        self.assertIn('fetch-depth: 0', workflow)
        self.assertIn('git diff --name-only "$AUTHORIZED_BASE_SHA" HEAD', workflow)
        self.assertIn('test "$(git rev-parse HEAD^)" = "$APPROVED_PARENT_SHA"', workflow)
        self.assertIn('test "$DISPATCH_BASE_SHA" = "$AUTHORIZED_BASE_SHA"', workflow)
        self.assertIn('test "$EVENT_BASE_SHA" = "$AUTHORIZED_BASE_SHA"', workflow)
        self.assertNotIn('BASE_SHA="HEAD^"', workflow)
        self.assertIn('python -m compileall -q -f r8a0 tests/r8a0', workflow)
        self.assertIn("PYTHONHASHSEED=0 TERM=xterm python -X dev -m unittest discover -s tests/r8a0 -p 'test_*.py' -v", workflow)
if __name__ == '__main__':
    unittest.main()
