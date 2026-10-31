"""P30-L9-CC: UDN #06 exact source identity and sale/event/visit-role tests."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cc_udn_itf_price_roles.py"
spec = importlib.util.spec_from_file_location("l9cc", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    row = dict(url=m.LIST_URL, detail_url=m.DETAIL_URL, title=m.TITLE,
               venue=m.VENUE, event_dates=list(m.EVENT_DATES), display_price=180)
    detail = dict(url=m.DETAIL_URL, product_id=m.PRODUCT_ID, title=m.TITLE,
                  venue=m.VENUE, event_dates=list(m.EVENT_DATES), display_price=180,
                  price_periods=[list(x) for x in m.PRICE_PERIODS],
                  visit_hours=[list(x) for x in m.VISIT_HOURS],
                  session_id=None, inventory=None, ticket_checkout_price=None)
    return row, detail

class Gate(unittest.TestCase):
    def check(self, row=None, detail=None, date="2026-10-31"):
        a,b=fixture()
        return m.inspect(a if row is None else row, b if detail is None else detail, date)
    def assert_hold(self,expected,row=None,detail=None,date="2026-10-31"):
        x=self.check(row,detail,date)
        self.assertEqual(x["decision"],expected)
        self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
    def test_review(self):
        x=self.check()
        self.assertEqual(x["decision"],"HOLD_PRODUCT_NOT_SESSION_AND_CHECKOUT_UNVERIFIED")
        self.assertEqual(len(x["candidateProvenance"]),11)
        self.assertEqual({a["decision"] for a in x["candidateProvenance"]},{"REVIEW_NOT_FORMALLY_ACCEPTED"})
    def test_bad_observed(self):
        self.assert_hold("HOLD_OBSERVED_AT",date="2026-02-30")
    def test_list_url(self):
        a,b=fixture();a["url"]="https://example.com";self.assert_hold("HOLD_OFFICIAL_LIST_DETAIL_LINK",row=a)
    def test_list_link(self):
        a,b=fixture();a["detail_url"]+="&SESSION=1";self.assert_hold("HOLD_OFFICIAL_LIST_DETAIL_LINK",row=a)
    def test_detail_url(self):
        a,b=fixture();b["url"]="http://tickets.udnfunlife.com/Application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1FSZGF7";self.assert_hold("HOLD_PRODUCT_ID_URL",detail=b)
    def test_detail_product_id(self):
        a,b=fixture();b["product_id"]="P1FSZGF8";self.assert_hold("HOLD_PRODUCT_ID_URL",detail=b)
    def test_exact_title(self):
        a,b=fixture();b["title"]+="!!";self.assert_hold("HOLD_SAME_PRODUCT_EXACT_TITLE",detail=b)
    def test_venue(self):
        a,b=fixture();b["venue"]="世貿一館";self.assert_hold("HOLD_VENUE",detail=b)
    def test_list_dates(self):
        a,b=fixture();a["event_dates"][1]="2026-11-08";self.assert_hold("HOLD_EXHIBITION_DATE_RANGE",row=a)
    def test_detail_dates(self):
        a,b=fixture();b["event_dates"][0]="2026-10-13";self.assert_hold("HOLD_EXHIBITION_DATE_RANGE",detail=b)
    def test_list_banner_price(self):
        a,b=fixture();a["display_price"]=150;self.assert_hold("HOLD_INDEX_DETAIL_PRICE_BANNER",row=a)
    def test_detail_banner_price(self):
        a,b=fixture();b["display_price"]=200;self.assert_hold("HOLD_INDEX_DETAIL_PRICE_BANNER",detail=b)
    def test_early_bird_not_event_date(self):
        a,b=fixture();b["price_periods"][0][0]="2026-11-06";self.assert_hold("HOLD_PRICE_PERIOD_ROLE",detail=b)
    def test_presale_not_event_date(self):
        a,b=fixture();b["price_periods"][1][2]=200;self.assert_hold("HOLD_PRICE_PERIOD_ROLE",detail=b)
    def test_exhibition_price_not_presale(self):
        a,b=fixture();b["price_periods"][2][2]=180;self.assert_hold("HOLD_PRICE_PERIOD_ROLE",detail=b)
    def test_first_day_no_time_collapse(self):
        a,b=fixture();b["visit_hours"][0][1]="10:00";self.assert_hold("HOLD_DAY_SPECIFIC_VISIT_HOURS",detail=b)
    def test_other_days_hours(self):
        a,b=fixture();b["visit_hours"][1][2]="17:00";self.assert_hold("HOLD_DAY_SPECIFIC_VISIT_HOURS",detail=b)
    def test_product_not_session(self):
        a,b=fixture();b["session_id"]=m.PRODUCT_ID;self.assert_hold("HOLD_UNVERIFIED_SESSION_INVENTORY_CHECKOUT",detail=b)
    def test_inventory_unknown(self):
        a,b=fixture();b["inventory"]=10;self.assert_hold("HOLD_UNVERIFIED_SESSION_INVENTORY_CHECKOUT",detail=b)
    def test_checkout_price_unknown(self):
        a,b=fixture();b["ticket_checkout_price"]=180;self.assert_hold("HOLD_UNVERIFIED_SESSION_INVENTORY_CHECKOUT",detail=b)

if __name__=="__main__":
    unittest.main()
