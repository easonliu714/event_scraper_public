"""P30-L9-CB: strict official TWTC same-ID list/detail provenance negatives."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cb_twtc_row_detail_roles.py"
spec = importlib.util.spec_from_file_location("l9cb", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    row = dict(url=m.LIST, detail_url=m.DETAIL, title=m.TITLE,
               start="2026-11-06", end="2026-11-09", venue=m.VENUE)
    detail = dict(url=m.DETAIL, detail_id="29251", title=m.TITLE,
                  start="2026-11-06", end="2026-11-09", venue=m.VENUE,
                  hours="10:00 ~ 18:00", organizer=m.ORGANIZER,
                  admission="請逕洽主辦單位", ticket_url=None,
                  ticket_event_id=None, session_id=None, price=None, inventory=None)
    return row, detail

class Gate(unittest.TestCase):
    def check(self, row=None, detail=None, date="2026-10-31"):
        a, b = fixture()
        return m.inspect(a if row is None else row, b if detail is None else detail, date)

    def test_review(self):
        x = self.check()
        self.assertEqual(x["decision"], "HOLD_ADMISSION_PRICE_TICKET_SESSION_UNVERIFIED")
        self.assertEqual(len(x["candidateProvenance"]), 9)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
    def test_bad_observed(self):
        self.assertEqual(self.check(date="2026-02-30")["decision"], "HOLD_OBSERVED_AT")
    def test_index_link(self):
        a, b = fixture(); a["detail_url"] += "&utm=1"
        self.assertEqual(self.check(row=a)["decision"], "HOLD_INDEX_DETAIL_LINK")
    def test_detail_id(self):
        a, b = fixture(); b["detail_id"] = "29252"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_DETAIL_ID_URL")
    def test_title_mismatch(self):
        a, b = fixture(); b["title"] += "!"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_SAME_ID_EXACT_TITLE")
    def test_list_date(self):
        a, b = fixture(); a["end"] = "2026-11-08"
        self.assertEqual(self.check(row=a)["decision"], "HOLD_LIST_DATE_RANGE")
    def test_detail_date(self):
        a, b = fixture(); b["start"] = "2026-11-07"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_DETAIL_DATE_RANGE")
    def test_venue(self):
        a, b = fixture(); b["venue"] = "南港展覽館1館"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_VENUE_IDENTITY")
    def test_hours(self):
        a, b = fixture(); b["hours"] = "10:00 ~ 17:00"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_DETAIL_HOURS_OR_ORGANIZER")
    def test_organizer(self):
        a, b = fixture(); b["organizer"] = "UNKNOWN"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_DETAIL_HOURS_OR_ORGANIZER")
    def test_admission_not_free(self):
        a, b = fixture(); b["admission"] = "免費"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_ADMISSION_UNKNOWN_ROLE")
    def test_no_ticket_url_inference(self):
        a, b = fixture(); b["ticket_url"] = "https://example.org/ticket"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_UNVERIFIED_TICKET_FIELDS")
    def test_no_ticket_id_inference(self):
        a, b = fixture(); b["ticket_event_id"] = "29251"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_UNVERIFIED_TICKET_FIELDS")
    def test_no_price_inference(self):
        a, b = fixture(); b["price"] = 0
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_UNVERIFIED_TICKET_FIELDS")
    def test_no_session_inference(self):
        a, b = fixture(); b["session_id"] = "29251-1"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_UNVERIFIED_TICKET_FIELDS")

if __name__ == "__main__":
    unittest.main()
