"""P30-VENUE-02AQ: exact official month list to film SID and two dates."""
import importlib.util
import pathlib
import unittest

p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02aq_fuzhong15_screenings.py"
spec=importlib.util.spec_from_file_location("venue02aq",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    idx=dict(url=m.LIST_URL,detail_url=m.DETAIL_URL,title=m.TITLE,
             screenings=[list(x) for x in m.SCREENINGS])
    det=dict(url=m.DETAIL_URL,film_sid=m.FILM_SID,title=m.TITLE,
             screenings=[list(x[:2]) for x in m.SCREENINGS],updated_at=m.DETAIL_UPDATED,
             duration_minutes=m.DURATION_MIN,ticket_event_id=None,ticket_session_ids=None,
             ticket_price=None,inventory=None)
    return idx,det

class Gate(unittest.TestCase):
    def check(self,index=None,detail=None,date="2026-10-31"):
        a,b=fixture()
        return m.inspect(a if index is None else index,b if detail is None else detail,date)
    def reject(self,code,index=None,detail=None,date="2026-10-31"):
        x=self.check(index,detail,date)
        self.assertEqual(x["decision"],code)
        self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
    def test_two_screenings_source_review(self):
        x=self.check()
        self.assertEqual(x["decision"],"HOLD_FILM_SID_NOT_TICKET_SESSION_AND_PRICE_UNVERIFIED")
        self.assertEqual(len(x["candidateProvenance"]),10)
        self.assertEqual({v["decision"] for v in x["candidateProvenance"]},{"REVIEW_NOT_FORMALLY_ACCEPTED"})
    def test_bad_observed(self):
        self.reject("HOLD_OBSERVED_AT",date="2026-02-30")
    def test_index_month_changed(self):
        a,b=fixture();a["url"]=a["url"].replace("2026-11","2026-12");self.reject("HOLD_OFFICIAL_MONTH_INDEX_LINK",index=a)
    def test_index_link_wrong_sid(self):
        a,b=fixture();a["detail_url"]=a["detail_url"].replace(m.FILM_SID,"other");self.reject("HOLD_OFFICIAL_MONTH_INDEX_LINK",index=a)
    def test_index_link_malformed_query(self):
        a,b=fixture();a["detail_url"]+="&bad";self.reject("HOLD_OFFICIAL_MONTH_INDEX_LINK",index=a)
    def test_index_link_duplicate_sid(self):
        a,b=fixture();a["detail_url"]+="&sid="+m.FILM_SID;self.reject("HOLD_OFFICIAL_MONTH_INDEX_LINK",index=a)
    def test_detail_wrong_id(self):
        a,b=fixture();b["film_sid"]="0Q289851686942598502";self.reject("HOLD_FILM_SID_IDENTITY",detail=b)
    def test_detail_url_host(self):
        a,b=fixture();b["url"]=b["url"].replace("www.fuzhong15.ntpc.gov.tw","fuzhong15.ntpc.gov.tw");self.reject("HOLD_FILM_SID_IDENTITY",detail=b)
    def test_title_mismatch(self):
        a,b=fixture();b["title"]="96分鍾";self.reject("HOLD_EXACT_FILM_TITLE",detail=b)
    def test_list_second_time(self):
        a,b=fixture();a["screenings"][1][1]="16:00";self.reject("HOLD_MONTHLY_LIST_SCREENINGS",index=a)
    def test_list_role_sale_not_free(self):
        a,b=fixture();a["screenings"][0][2]="索";self.reject("HOLD_MONTHLY_LIST_SCREENINGS",index=a)
    def test_detail_missing_second_date(self):
        a,b=fixture();b["screenings"].pop();self.reject("HOLD_DETAIL_SCREENING_PARITY",detail=b)
    def test_detail_update_not_screening(self):
        a,b=fixture();b["updated_at"]="2026-11-08";self.reject("HOLD_UPDATE_DATE_NOT_SHOWTIME",detail=b)
    def test_duration_not_time(self):
        a,b=fixture();b["duration_minutes"]=96;self.reject("HOLD_DURATION_NOT_SCREENING_TIME",detail=b)
    def test_film_sid_not_ticket_event_id(self):
        a,b=fixture();b["ticket_event_id"]=m.FILM_SID;self.reject("HOLD_TICKET_ID_PRICE_INVENTORY_UNVERIFIED",detail=b)
    def test_no_invented_ticket_session(self):
        a,b=fixture();b["ticket_session_ids"]=["a","b"];self.reject("HOLD_TICKET_ID_PRICE_INVENTORY_UNVERIFIED",detail=b)
    def test_no_invented_ticket_price(self):
        a,b=fixture();b["ticket_price"]=20;self.reject("HOLD_TICKET_ID_PRICE_INVENTORY_UNVERIFIED",detail=b)
    def test_no_invented_inventory(self):
        a,b=fixture();b["inventory"]=40;self.reject("HOLD_TICKET_ID_PRICE_INVENTORY_UNVERIFIED",detail=b)

if __name__=="__main__":
    unittest.main()
