"""P30-L9-BZ: first-party row #1 direct OPENTIX link is not exact-title or ticket-session acceptance."""
import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9bz_opentix_delisted_title.py"
s=importlib.util.spec_from_file_location("l9bz",p)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def fixture():
    row=dict(bulletin_url=m.BULLETIN,row_number=1,ticket_url=m.TICKET,
             title=m.VENUE_TITLE,event_date=m.DATE,event_time=m.TIME)
    ticket=dict(url=m.TICKET,title=m.TICKET_TITLE,status_text="本節目已下架",
                session_date=None,inventory=None)
    return row,ticket

class Gate(unittest.TestCase):
    def check(self,row=None,ticket=None,observed="2026-10-31"):
        a,b=fixture()
        return m.inspect(a if row is None else row,b if ticket is None else ticket,observed)
    def test_source_review_not_acceptance(self):
        r=self.check()
        self.assertEqual(r["decision"],"HOLD_DIRECT_LINK_BUT_NONEXACT_TITLE_AND_DELISTED")
        self.assertEqual(len(r["candidateProvenance"]),6)
        self.assertEqual((r["acceptedFields"],r["goldenAccepted"],r["published"]),(0,0,False))
    def test_wrong_row(self):
        a,b=fixture(); a["row_number"]=4
        self.assertEqual(self.check(row=a)["decision"],"HOLD_ROW_LOCAL_SOURCE")
    def test_wrong_bulletin(self):
        a,b=fixture(); a["bulletin_url"]+="&other=1"
        self.assertEqual(self.check(row=a)["decision"],"HOLD_ROW_LOCAL_SOURCE")
    def test_ticket_query(self):
        a,b=fixture(); b["url"]+="?ref=x"
        self.assertEqual(self.check(ticket=b)["decision"],"HOLD_DIRECT_EVENT_URL")
    def test_cross_origin(self):
        a,b=fixture(); a["ticket_url"]="https://fake.example/event/2071939794940801025"
        self.assertEqual(self.check(row=a)["decision"],"HOLD_DIRECT_EVENT_URL")
    def test_source_title_mutation(self):
        a,b=fixture(); a["title"]+="!"
        self.assertEqual(self.check(row=a)["decision"],"HOLD_SOURCE_TITLE_CHANGED")
    def test_ticket_title_mutation(self):
        a,b=fixture(); b["title"]+="!"
        self.assertEqual(self.check(ticket=b)["decision"],"HOLD_SOURCE_TITLE_CHANGED")
    def test_wrong_date(self):
        a,b=fixture(); a["event_date"]="2026-10-04"
        self.assertEqual(self.check(row=a)["decision"],"HOLD_VENUE_DATE_ROLE")
    def test_delisted_not_inventory(self):
        a,b=fixture(); b["status_text"]="售罄"
        self.assertEqual(self.check(ticket=b)["decision"],"HOLD_TICKET_STATUS_NOT_OBSERVED")
    def test_unverified_session(self):
        a,b=fixture(); b["session_date"]=m.DATE
        self.assertEqual(self.check(ticket=b)["decision"],"HOLD_UNVERIFIED_SESSION_OR_INVENTORY")
    def test_unverified_inventory(self):
        a,b=fixture(); b["inventory"]=0
        self.assertEqual(self.check(ticket=b)["decision"],"HOLD_UNVERIFIED_SESSION_OR_INVENTORY")
    def test_invalid_observed_date(self):
        self.assertEqual(self.check(observed="2026-02-30")["decision"],"HOLD_OBSERVED_AT")
if __name__=="__main__": unittest.main()
