"""New teaching requirements, not original repository tests."""
import os
import unittest
from dataclasses import asdict
from tempfile import TemporaryDirectory
from adapter import build, audit_records
from northstar.audit import FileAuditStore
from northstar.auth import Actor
from northstar.errors import AuthorizationError, CustomerNotFoundError

SECRET = "PRIVATE-REASON-42"
class Contract(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.audit_path = os.path.join(tmp.name, "audit.jsonl")
        self.s = build(self.audit_path)
    def command(self, role="manager", reason=SECRET, customer_id="c1"):
        return self.s.lifecycle.deactivate(Actor("u-review", role), customer_id, reason)
    def test_01_reason_stays_out_of_public_event(self):
        self.command()
        self.assertEqual(len(self.s.bus.published), 1)
        event = self.s.bus.published[0]
        self.assertEqual(event.event_type, "customer.deactivated")
        self.assertEqual(event.customer_id, "c1")
        self.assertEqual(event.payload.get("email"), "case@example.com")
        self.assertNotIn(SECRET, repr(self.s.bus.published))
        self.assertNotIn("reason", event.payload)
    def test_02_customer_gets_generic_notification(self):
        self.command()
        self.assertEqual(self.s.client.sent_messages,
            [("case@example.com", "Your Atlas account has been deactivated.")])
    def test_03_reason_is_retained_in_internal_audit(self):
        self.command(reason="  " + SECRET + "  ")
        self.assertEqual(audit_records(self.s),
            [{"customer_id":"c1", "actor_id":"u-review", "reason":SECRET}])
    def test_09_five_character_reason_is_trimmed_and_audited(self):
        result = self.command(reason="  abcde  ")
        self.assertFalse(result.active)
        self.assertEqual(audit_records(self.s),
            [{"customer_id": "c1", "actor_id": "u-review", "reason": "abcde"}])
        self.assertEqual(self.s.bus.published[0].payload, {"email": "case@example.com"})

    def test_04_success_preserves_customer_result(self):
        result = self.command(role="admin")
        self.assertEqual(result.customer_id, "c1")
        self.assertFalse(result.active)
        self.assertFalse(self.s.repository.get("c1").active)
    def test_05_denied_command_has_no_effects(self):
        with self.assertRaises(AuthorizationError): self.command(role="viewer")
        self.assert_no_effects()
    def test_06_short_reason_has_no_effects(self):
        with self.assertRaises(ValueError): self.command(reason="  no  ")
        self.assert_no_effects()
    def test_07_missing_customer_has_no_effects(self):
        with self.assertRaises(CustomerNotFoundError): self.command(customer_id="missing")
        self.assert_no_effects()
    def assert_no_effects(self):
        self.assertTrue(self.s.repository.get("c1").active)
        self.assertEqual(self.s.bus.published, [])
        self.assertEqual(self.s.client.sent_messages, [])
        self.assertEqual(audit_records(self.s), [])
    def test_08_notification_failure_does_not_erase_audit(self):
        def fail(*args): raise RuntimeError("simulated notification failure")
        self.s.client.send = fail
        with self.assertRaises(RuntimeError): self.command()
        self.assertFalse(self.s.repository.get("c1").active)
        self.assertEqual(audit_records(self.s),
            [{"customer_id":"c1", "actor_id":"u-review", "reason":SECRET}])
        self.assertNotIn(SECRET, repr(self.s.bus.published))
        self.assertEqual(self.s.client.sent_messages, [])
    def test_10_file_audit_persists_across_fresh_store_instances(self):
        first = FileAuditStore(self.audit_path)
        first.record_deactivation("c-synthetic-1", "u-synthetic", "  synthetic first reason  ")
        reopened = FileAuditStore(self.audit_path)
        self.assertEqual([asdict(r) for r in reopened.records],
            [{"customer_id":"c-synthetic-1", "actor_id":"u-synthetic", "reason":"synthetic first reason"}])
        reopened.record_deactivation("c-synthetic-2", "u-synthetic", "synthetic second reason")
        final = FileAuditStore(self.audit_path)
        self.assertEqual([asdict(r) for r in final.records],
            [{"customer_id":"c-synthetic-1", "actor_id":"u-synthetic", "reason":"synthetic first reason"},
             {"customer_id":"c-synthetic-2", "actor_id":"u-synthetic", "reason":"synthetic second reason"}])

if __name__ == "__main__": unittest.main()
