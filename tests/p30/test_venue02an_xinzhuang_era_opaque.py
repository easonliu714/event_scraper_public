"""P30-VENUE-02AN: no inference from ERA opaque ticket page or venue bulletin row."""
import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02an_xinzhuang_era_opaque.py"
s=importlib.util.spec_from_file_location("v02an",p)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def fixture():
    row=dict(bulletin_url=m.BULLETIN,row_number=2,title=m.VENUE_TITLE,
             event_date=m.DATE,event_time=m.TIME,price_classes=list(m.PRICE_CLASSES),
             ticket_url=m.TICKET)
    view=dict(url=m.TICKET,visible_event_title=None,visible_event_date=None,
              visible_venue=None,session_id=None,inventory=None,session_price=None,
              rendered_section_labels=["節目資訊","場次列表"])
    return row,view

class Gate(unittest.TestCase):
    def check(self,row=None,view=None,observed="2026-10-31"):
        a,b=fixture()
        return m.inspect(a if row is None else row,b if view is None else view,observed)
    def test_source_opaque_review(self):
        o=self.check()
        self.assertEqual(o["decision"],"HOLD_ERA_TICKET_TITLE_DATE_SESSION_NOT_RENDERED")
        self.assertEqual(len(o["candidateProvenance"]),6)
        self.assertEqual((o["acceptedFields"],o["goldenAccepted"],o["published"]),(0,0,False))
    def test_row_not_ticket_event_id(self):
        a,b=fixture(); a["row_number"]=4
        self.assertEqual(self.check(row=a)["decision"],"HOLD_ROW2_OWNERSHIP")
    def test_wrong_bulletin(self):
        a,b=fixture(); a["bulletin_url"]+="&x=1"
        self.assertEqual(self.check(row=a)["decision"],"HOLD_ROW2_OWNERSHIP")
    def test_wrong_title(self):
        a,b=fixture(); a["title"]+="!"
        self.assertEqual(self.check(row=a)["decision"],"HOLD_VENUE_ROW_ROLE")
    def test_date_role(self):
        a,b=fixture(); a["event_date"]="2026-10-18"
        self.assertEqual(self.check(row=a)["decision"],"HOLD_VENUE_ROW_ROLE")
    def test_price_tier_order(self):
        a,b=fixture(); a["price_classes"]=[500,1000]
        self.assertEqual(self.check(row=a)["decision"],"HOLD_VENUE_PRICE_CLASSES")
    def test_cross_origin(self):
        a,b=fixture(); b["url"]="https://fake.example/"+m.TICKET.rsplit("/",1)[-1]
        self.assertEqual(self.check(view=b)["decision"],"HOLD_DIRECT_ERA_URL")
    def test_extra_query(self):
        a,b=fixture(); a["ticket_url"]+="&campaign=1"
        self.assertEqual(self.check(row=a)["decision"],"HOLD_DIRECT_ERA_URL")
    def test_hallucinated_ticket_title(self):
        a,b=fixture(); b["visible_event_title"]=m.VENUE_TITLE
        self.assertEqual(self.check(view=b)["decision"],"HOLD_TICKET_FIELDS_NOT_IN_PUBLIC_READER")
    def test_hallucinated_ticket_date(self):
        a,b=fixture(); b["visible_event_date"]=m.DATE
        self.assertEqual(self.check(view=b)["decision"],"HOLD_TICKET_FIELDS_NOT_IN_PUBLIC_READER")
    def test_hallucinated_session_id(self):
        a,b=fixture(); b["session_id"]="P1CXDGLJ"
        self.assertEqual(self.check(view=b)["decision"],"HOLD_TICKET_SESSION_INVENTORY_PRICE_UNVERIFIED")
    def test_inferred_price(self):
        a,b=fixture(); b["session_price"]=500
        self.assertEqual(self.check(view=b)["decision"],"HOLD_TICKET_SESSION_INVENTORY_PRICE_UNVERIFIED")
    def test_inferred_inventory(self):
        a,b=fixture(); b["inventory"]=0
        self.assertEqual(self.check(view=b)["decision"],"HOLD_TICKET_SESSION_INVENTORY_PRICE_UNVERIFIED")
    def test_no_section_parity(self):
        a,b=fixture(); b["rendered_section_labels"]=["節目資訊"]
        self.assertEqual(self.check(view=b)["decision"],"HOLD_TICKET_VIEW_SECTION_SHAPE")
    def test_bad_observed_date(self):
        self.assertEqual(self.check(observed="2026-02-30")["decision"],"HOLD_OBSERVED_AT")
if __name__=="__main__": unittest.main()
