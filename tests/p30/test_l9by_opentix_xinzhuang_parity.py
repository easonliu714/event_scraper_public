"""P30-L9-BY exact ticket URL and venue bulletin field role negatives."""
import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9by_opentix_xinzhuang_parity.py"
spec=importlib.util.spec_from_file_location("l9by",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    ticket=dict(url=m.URL,title=m.TITLE,venue=m.VENUE,admission_time="13:30",
                show_start_text="14:00",ticket_session_date=None,live_inventory=None)
    row=dict(ticket_url=m.URL,title=m.TITLE,venue=m.VENUE,bulletin_url=m.BULLETIN,
             event_date=m.DATE,start=m.TIME)
    return ticket,row

class Gate(unittest.TestCase):
    def check(self,ticket=None,row=None,observed="2026-10-31"):
        a,b=fixture()
        return m.inspect(a if ticket is None else ticket,b if row is None else row,observed)
    def test_source_receipt_only(self):
        o=self.check()
        self.assertEqual(o["decision"],"HOLD_TICKET_SESSION_DATE_NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(len(o["candidateProvenance"]),6)
        self.assertEqual((o["acceptedFields"],o["goldenAccepted"],o["published"]),(0,0,False))
    def test_wrong_ticket_link(self):
        a,b=fixture(); b["ticket_url"]+="?ref=other"
        self.assertEqual(self.check(row=b)["decision"],"HOLD_EXACT_TICKET_EVENT_LINK")
    def test_wrong_ticket_origin(self):
        a,b=fixture(); a["url"]="https://other.example/event/"+m.EVENT_ID
        self.assertEqual(self.check(ticket=a)["decision"],"HOLD_EXACT_TICKET_EVENT_LINK")
    def test_title_conflict(self):
        a,b=fixture(); a["title"]+="?"
        self.assertEqual(self.check(ticket=a)["decision"],"HOLD_CROSS_SOURCE_TITLE")
    def test_venue_conflict(self):
        a,b=fixture(); b["venue"]="other"
        self.assertEqual(self.check(row=b)["decision"],"HOLD_CROSS_SOURCE_VENUE")
    def test_wrong_bulletin(self):
        a,b=fixture(); b["bulletin_url"]="https://other.example/"
        self.assertEqual(self.check(row=b)["decision"],"HOLD_FIRST_PARTY_VENUE_BULLETIN")
    def test_date_conflict(self):
        a,b=fixture(); b["event_date"]="2026-12-06"
        self.assertEqual(self.check(row=b)["decision"],"HOLD_VENUE_DATE_TIME_ROLE")
    def test_time_conflict(self):
        a,b=fixture(); b["start"]="13:30"
        self.assertEqual(self.check(row=b)["decision"],"HOLD_VENUE_DATE_TIME_ROLE")
    def test_admission_not_show(self):
        a,b=fixture(); a["admission_time"]="14:00"
        self.assertEqual(self.check(ticket=a)["decision"],"HOLD_TICKET_ADMISSION_VS_SHOW_START")
    def test_no_ticket_date_inference(self):
        a,b=fixture(); a["ticket_session_date"]=m.DATE
        self.assertEqual(self.check(ticket=a)["decision"],"HOLD_UNVERIFIED_TICKET_SESSION_OR_INVENTORY")
    def test_no_inventory_inference(self):
        a,b=fixture(); a["live_inventory"]=10
        self.assertEqual(self.check(ticket=a)["decision"],"HOLD_UNVERIFIED_TICKET_SESSION_OR_INVENTORY")
    def test_observed_at(self):
        self.assertEqual(self.check(observed="today")["decision"],"HOLD_OBSERVED_AT")
if __name__=="__main__":
    unittest.main()
