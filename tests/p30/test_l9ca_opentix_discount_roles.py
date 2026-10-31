"""P30-L9-CA strict role tests, based on independently observed first-party static page."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9ca_opentix_discount_roles.py"
s=importlib.util.spec_from_file_location("l9ca",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    v=dict(url=m.VENUE,row=4,ticket_url=m.TICKET,title=m.TITLE,performance_date="2026-12-05",performance_time="14:00")
    t=dict(url=m.TICKET,title=m.TITLE,venue=m.HALL,admission_time="13:30",show_start_time="14:00",early_bird_deadline="2026-10-11 23:59",early_bird_price_classes=[500,400],dated_session=None,session_id=None,inventory=None)
    return v,t
class Gate(unittest.TestCase):
    def check(self,v=None,t=None,date="2026-10-31"):
        a,b=fixture();return m.inspect(a if v is None else v,b if t is None else t,date)
    def test_review_only(self):
        o=self.check();self.assertEqual(o["decision"],"HOLD_DISCOUNT_DEADLINE_NOT_DATED_TICKET_SESSION");self.assertEqual(len(o["candidateProvenance"]),8);self.assertEqual((o["acceptedFields"],o["goldenAccepted"],o["published"]),(0,0,False))
    def test_bad_date(self):self.assertEqual(self.check(date="2026-02-30")["decision"],"HOLD_OBSERVED_AT")
    def test_wrong_row(self):
        a,b=fixture();a["row"]=3;self.assertEqual(self.check(v=a)["decision"],"HOLD_VENUE_ROW_AND_LINK")
    def test_wrong_venue_url(self):
        a,b=fixture();a["url"]+="&x=1";self.assertEqual(self.check(v=a)["decision"],"HOLD_VENUE_ROW_AND_LINK")
    def test_wrong_ticket_url(self):
        a,b=fixture();b["url"]+="?ref=1";self.assertEqual(self.check(t=b)["decision"],"HOLD_EXACT_TICKET_ID_TITLE")
    def test_wrong_title(self):
        a,b=fixture();b["title"]+="!";self.assertEqual(self.check(t=b)["decision"],"HOLD_EXACT_TICKET_ID_TITLE")
    def test_venue_date(self):
        a,b=fixture();a["performance_date"]="2026-10-11";self.assertEqual(self.check(v=a)["decision"],"HOLD_VENUE_PERFORMANCE_ROLE")
    def test_venue_time(self):
        a,b=fixture();a["performance_time"]="13:30";self.assertEqual(self.check(v=a)["decision"],"HOLD_VENUE_PERFORMANCE_ROLE")
    def test_hall(self):
        a,b=fixture();b["venue"]="其他場館";self.assertEqual(self.check(t=b)["decision"],"HOLD_TICKET_VENUE_OR_TIME_ROLE")
    def test_admission_not_show(self):
        a,b=fixture();b["admission_time"]="14:00";self.assertEqual(self.check(t=b)["decision"],"HOLD_TICKET_VENUE_OR_TIME_ROLE")
    def test_discount_not_performance(self):
        a,b=fixture();b["early_bird_deadline"]="2026-12-05 14:00";self.assertEqual(self.check(t=b)["decision"],"HOLD_DISCOUNT_ROLE_NOT_OBSERVED")
    def test_price_classes_not_inventory(self):
        a,b=fixture();b["early_bird_price_classes"]=[400,500];self.assertEqual(self.check(t=b)["decision"],"HOLD_DISCOUNT_ROLE_NOT_OBSERVED")
    def test_invented_session(self):
        a,b=fixture();b["dated_session"]="2026-12-05";self.assertEqual(self.check(t=b)["decision"],"HOLD_UNVERIFIED_TICKET_SESSION")
    def test_invented_session_id(self):
        a,b=fixture();b["session_id"]="2089995501384269825";self.assertEqual(self.check(t=b)["decision"],"HOLD_UNVERIFIED_TICKET_SESSION")
    def test_invented_inventory(self):
        a,b=fixture();b["inventory"]=0;self.assertEqual(self.check(t=b)["decision"],"HOLD_UNVERIFIED_TICKET_SESSION")
if __name__=="__main__":unittest.main()
