"""P30-L9-BX: first-party event identity and sale/registration conflict refusal."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9bx_eventgo_status_roles.py"
spec = importlib.util.spec_from_file_location("l9bx", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    a = dict(url=m.INDEX, detail_url=m.DETAIL, title=m.TITLE,
             event_date=m.DATE, venue=m.VENUE)
    b = dict(url=m.DETAIL, title=m.TITLE, event_date=m.DATE,
             event_start="09:00", event_end="12:00", venue=m.VENUE,
             ticket_class="FREE_REGISTRATION_NT0", sale_banner="ENDED",
             ticket_badge="HOT", inventory=None, registration_open=None)
    return a, b

class Gate(unittest.TestCase):
    def check(self, index=None, detail=None, observed="2026-10-31"):
        a, b = fixture()
        return m.inspect(a if index is None else index,
                         b if detail is None else detail, observed)

    def test_conflicting_status_never_open(self):
        o = self.check()
        self.assertEqual(o["decision"], "HOLD_CONFLICTING_SALE_BANNER_AND_TICKET_BADGE")
        self.assertEqual(len(o["candidateProvenance"]), 6)
        self.assertEqual((o["acceptedFields"], o["goldenAccepted"], o["published"]), (0, 0, False))
        self.assertFalse(o["verifiedRegistrationOpen"])

    def test_offsite_detail(self):
        a, b = fixture()
        b["url"] = "https://other.example/event/detail/" + m.ID
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_SAME_ID_FIRST_PARTY_LINK")

    def test_index_link_mismatch(self):
        a, b = fixture()
        a["detail_url"] += "?copy=1"
        self.assertEqual(self.check(index=a)["decision"], "HOLD_SAME_ID_FIRST_PARTY_LINK")

    def test_title_mismatch(self):
        a, b = fixture()
        b["title"] += " copy"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_TITLE_PARITY")

    def test_date_mismatch(self):
        a, b = fixture()
        b["event_date"] = "2026-11-05"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_EVENT_DATE_PARITY")

    def test_venue_mismatch(self):
        a, b = fixture()
        b["venue"] = "another"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_VENUE_PARITY")

    def test_registration_open_not_proven(self):
        a, b = fixture()
        b["registration_open"] = True
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_DYNAMIC_INVENTORY_OR_OPEN_CLAIM")

    def test_inventory_not_proven(self):
        a, b = fixture()
        b["inventory"] = 10
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_DYNAMIC_INVENTORY_OR_OPEN_CLAIM")

    def test_bad_observed_at(self):
        self.assertEqual(self.check(observed="today")["decision"], "HOLD_OBSERVED_AT")

    def test_status_not_overwritten(self):
        a, b = fixture()
        b["sale_banner"] = "HOT"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_STATUS_SOURCE_PARITY")

if __name__ == "__main__":
    unittest.main()
