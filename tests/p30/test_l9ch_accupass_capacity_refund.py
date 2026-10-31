import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9ch_accupass_capacity_refund.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"url": m.SOURCE, "event_id": m.EVENT_ID,
            "capacity_role": "PER_WORKSHOP_LIMIT", "capacity": 20,
            "fee_role": "PER_WORKSHOP_FEE", "fee_ntd": 100,
            "refund_role": "RELATIVE_TO_PURCHASE_AND_TICKET_START",
            "refund_after_purchase_hours": 24, "refund_before_ticket_start_days": 8,
            "refund_fee_percent": 10, "absolute_refund_deadline": None,
            "walkin_role": "NO_SHOW_WAITLIST_ONLY", "walkin_guaranteed": False,
            "ticket_session_ids": None, "inventory": None, "remaining_seats": None}

class TestGate(unittest.TestCase):
    def check(self, change=None):
        x = fixture()
        if change:
            change(x)
        return m.inspect(x, "2026-11-01")

    def reject(self, expected, change):
        result = self.check(change)
        self.assertEqual(result["decision"], expected)
        self.assertEqual(result["acceptedFields"], 0)
        self.assertFalse(result["published"])

    def test_source_bound_relative_terms(self):
        x = self.check()
        self.assertEqual(x["decision"], "HOLD_RELATIVE_TERMS_NO_TICKET_SESSION_ID")
        self.assertEqual(len(x["provenance"]), 6)
        self.assertTrue(all(p["decision"] == "REVIEW_NOT_FORMALLY_ACCEPTED" for p in x["provenance"]))

    def test_bad_observation(self):
        self.assertEqual(m.inspect(fixture(), "2026-02-30")["decision"], "HOLD_OBSERVED_AT")

    def test_cross_host(self):
        self.reject("HOLD_SAME_EVENT_ID", lambda x: x.update(url="https://evil.test/event/" + m.EVENT_ID))

    def test_query_injection(self):
        self.reject("HOLD_SAME_EVENT_ID", lambda x: x.update(url=m.SOURCE + "?foo=1"))

    def test_other_event(self):
        self.reject("HOLD_SAME_EVENT_ID", lambda x: x.update(event_id="other"))

    def test_inventory_from_capacity(self):
        self.reject("HOLD_NO_PUBLIC_SESSION_OR_INVENTORY", lambda x: x.update(inventory=20))

    def test_remaining_seats(self):
        self.reject("HOLD_NO_PUBLIC_SESSION_OR_INVENTORY", lambda x: x.update(remaining_seats=20))

    def test_fabricated_ticket_session(self):
        self.reject("HOLD_NO_PUBLIC_SESSION_OR_INVENTORY", lambda x: x.update(ticket_session_ids=["invented"]))

    def test_capacity_role(self):
        self.reject("HOLD_CAPACITY_NOT_LIVE_INVENTORY", lambda x: x.update(capacity_role="AVAILABLE_SEATS"))

    def test_capacity_bool_not_int(self):
        self.reject("HOLD_CAPACITY_NOT_LIVE_INVENTORY", lambda x: x.update(capacity=True))

    def test_fee_role(self):
        self.reject("HOLD_WORKSHOP_FEE_ROLE", lambda x: x.update(fee_role="SESSION_TICKET_PRICE"))

    def test_refund_role(self):
        self.reject("HOLD_REFUND_ROLE", lambda x: x.update(refund_role="SHOWTIME"))

    def test_refund_days(self):
        self.reject("HOLD_REFUND_CONDITION", lambda x: x.update(refund_before_ticket_start_days=7))

    def test_refund_hours(self):
        self.reject("HOLD_REFUND_CONDITION", lambda x: x.update(refund_after_purchase_hours=0))

    def test_refund_fee(self):
        self.reject("HOLD_REFUND_CONDITION", lambda x: x.update(refund_fee_percent=0))

    def test_absolute_deadline_without_ticket_start(self):
        self.reject("HOLD_NO_VERIFIED_TICKET_START_FOR_DEADLINE", lambda x: x.update(absolute_refund_deadline="2026-11-08"))

    def test_walkin_not_guaranteed(self):
        self.reject("HOLD_WAITLIST_NOT_AVAILABILITY", lambda x: x.update(walkin_guaranteed=True))

if __name__ == "__main__":
    unittest.main()
