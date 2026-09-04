from __future__ import annotations

import unittest

from pc_connection import (
    BRIDGE_ID,
    FORBIDDEN_CAPABILITIES,
    PHASE_ONE_OPERATIONS,
    READ_ONLY_ROOTS,
    WRITABLE_ROOT,
)


class PcConnectionScaffoldTests(unittest.TestCase):
    def test_bridge_identifier_is_versioned(self):
        self.assertEqual(BRIDGE_ID, "VERA_PC_CONNECTION_BRIDGE_V1")

    def test_local_roots_match_authorized_boundary(self):
        self.assertEqual(
            READ_ONLY_ROOTS,
            (r"C:\VERA", r"C:\Users\patri\VERA"),
        )
        self.assertEqual(WRITABLE_ROOT, r"C:\VERA\PCCC")
        self.assertNotIn(WRITABLE_ROOT, READ_ONLY_ROOTS)

    def test_phase_one_does_not_include_command_execution(self):
        self.assertNotIn("RUN_COMMAND", PHASE_ONE_OPERATIONS)
        self.assertNotIn("RUN_APPROVED_COMMAND", PHASE_ONE_OPERATIONS)
        self.assertNotIn("START_PROCESS", PHASE_ONE_OPERATIONS)

    def test_forbidden_capabilities_preserve_authorization_boundary(self):
        required = {
            "ARBITRARY_SHELL",
            "INBOUND_LISTENER",
            "ADMIN_INSTALL",
            "AUTOMATIC_UPDATE",
            "MODEL_EXECUTION",
            "TRAINING",
            "PRODUCTION_MIGRATION",
            "CREDENTIAL_CREATION",
            "CANONICAL_MEMORY_WRITE",
        }
        self.assertEqual(FORBIDDEN_CAPABILITIES, required)


if __name__ == "__main__":
    unittest.main()
