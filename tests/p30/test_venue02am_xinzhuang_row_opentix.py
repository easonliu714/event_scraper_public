"""P30-VENUE-02AM official Xinzhuang stage bulletin row to ticket event strict negatives."""
import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02am_xinzhuang_row_opentix.py"
spec=importlib.util.spec_from_file_location("v02am",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def fixture():
    index=dict(url=m.INDEX,detail_url=m.BULLETIN)
    bulletin=dict(url=m.BULLETIN,sid=m.SID,row_count=9,row_number=4,title=m.TITLE,
        venue=m.VENUE,ticket_url=m.TICKET,event_date=m.DATE,event_time=m.TIME,price_classes=[400,500])
    ticket=dict(url=m.TICKET,title=m.TITLE,venue=m.VENUE,event_session_date=None,
                per_session_price=None,inventory=None)
    return index,bulletin,ticket
class Gate(unittest.TestCase):
    def check(self,index=None,bulletin=None,ticket=None,observed="2026-10-31"):
        a,b,c=fixture()
        return m.inspect(a if index is None else index,b if bulletin is None else bulletin,
                         c if ticket is None else ticket,observed)
    def test_real_source_candidate_review(self):
        o=self.check()
        self.assertEqual(o["decision"],"HOLD_VENUE_ROW_TO_TICKET_EVENT_LINK_SESSION_NOT_CONFIRMED")
        self.assertEqual(len(o["candidateProvenance"]),7)
        self.assertEqual((o["acceptedFields"],o["goldenAccepted"],o["published"]),(0,0,False))
    def test_bad_index(self):
        a,b,c=fixture(); a["detail_url"]+="?x"
        self.assertEqual(self.check(index=a)["decision"],"HOLD_VENUE_INDEX_LINK")
    def test_bad_sid(self):
        a,b,c=fixture(); b["sid"]="other"
        self.assertEqual(self.check(bulletin=b)["decision"],"HOLD_SAME_SID_BULLETIN")
    def test_row_count(self):
        a,b,c=fixture(); b["row_count"]=8
        self.assertEqual(self.check(bulletin=b)["decision"],"HOLD_BULLETIN_ROW_OWNERSHIP")
    def test_row_number(self):
        a,b,c=fixture(); b["row_number"]=1
        self.assertEqual(self.check(bulletin=b)["decision"],"HOLD_BULLETIN_ROW_OWNERSHIP")
    def test_title_mismatch(self):
        a,b,c=fixture(); c["title"]+="!"
        self.assertEqual(self.check(ticket=c)["decision"],"HOLD_TICKET_TITLE_PARITY")
    def test_venue_mismatch(self):
        a,b,c=fixture(); c["venue"]="other"
        self.assertEqual(self.check(ticket=c)["decision"],"HOLD_TICKET_VENUE_PARITY")
    def test_external_ticket_mismatch(self):
        a,b,c=fixture(); b["ticket_url"]="https://other.example/event/2089995501384269825"
        self.assertEqual(self.check(bulletin=b)["decision"],"HOLD_EXACT_EXTERNAL_TICKET_EVENT_ID")
    def test_wrong_date(self):
        a,b,c=fixture(); b["event_date"]="2026-12-06"
        self.assertEqual(self.check(bulletin=b)["decision"],"HOLD_ROW_LOCAL_EVENT_DATE_TIME")
    def test_price_inference(self):
        a,b,c=fixture(); c["per_session_price"]=400
        self.assertEqual(self.check(ticket=c)["decision"],"HOLD_PRICE_CLASS_NOT_SESSION_PRICE")
    def test_inventory(self):
        a,b,c=fixture(); c["inventory"]=5
        self.assertEqual(self.check(ticket=c)["decision"],"HOLD_TICKET_SESSION_OR_INVENTORY_UNVERIFIED")
    def test_observed(self):
        self.assertEqual(self.check(observed="today")["decision"],"HOLD_OBSERVED_AT")
if __name__=="__main__":
    unittest.main()
