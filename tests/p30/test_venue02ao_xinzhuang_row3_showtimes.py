"""P30-VENUE-02AO strict two-showtime and ticket-method boundary tests."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02ao_xinzhuang_row3_showtimes.py"
s=importlib.util.spec_from_file_location("v02ao",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():return dict(url=m.BULLETIN,row=3,title=m.TITLE,performance_date="2026-10-18",times=["11:00","15:00"],ticket_method="索票",ticket_url=None,price=None,ticket_event_id=None,inventory=None)
class Gate(unittest.TestCase):
    def check(self,row=None,date="2026-10-31"):return m.inspect(fixture() if row is None else row,date)
    def test_review_only(self):
        x=self.check();self.assertEqual(x["decision"],"HOLD_TWO_VENUE_SHOWTIMES_NO_TICKET_SESSION_ID");self.assertEqual(len(x["candidateProvenance"]),6);self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
    def test_observed_date(self):self.assertEqual(self.check(date="2026-02-30")["decision"],"HOLD_OBSERVED_AT")
    def test_row4_not_row3(self):
        x=fixture();x["row"]=4;self.assertEqual(self.check(x)["decision"],"HOLD_ROW3_OWNERSHIP")
    def test_bulletin_url(self):
        x=fixture();x["url"]+="&foo=1";self.assertEqual(self.check(x)["decision"],"HOLD_ROW3_OWNERSHIP")
    def test_title(self):
        x=fixture();x["title"]+="!";self.assertEqual(self.check(x)["decision"],"HOLD_ROW3_TITLE_DATE")
    def test_date(self):
        x=fixture();x["performance_date"]="2026-10-19";self.assertEqual(self.check(x)["decision"],"HOLD_ROW3_TITLE_DATE")
    def test_only_one_time(self):
        x=fixture();x["times"]=["11:00"];self.assertEqual(self.check(x)["decision"],"HOLD_TWO_SHOWTIMES_NO_COLLAPSE")
    def test_time_order(self):
        x=fixture();x["times"]=["15:00","11:00"];self.assertEqual(self.check(x)["decision"],"HOLD_TWO_SHOWTIMES_NO_COLLAPSE")
    def test_wrong_time(self):
        x=fixture();x["times"]=["11:00","14:00"];self.assertEqual(self.check(x)["decision"],"HOLD_TWO_SHOWTIMES_NO_COLLAPSE")
    def test_not_free_price(self):
        x=fixture();x["price"]=0;self.assertEqual(self.check(x)["decision"],"HOLD_NO_PRICE_OR_TICKET_ID_INFERENCE")
    def test_ticket_method(self):
        x=fixture();x["ticket_method"]="免費";self.assertEqual(self.check(x)["decision"],"HOLD_NO_DIRECT_TICKET_URL")
    def test_invented_url(self):
        x=fixture();x["ticket_url"]="https://www.opentix.life/event/1";self.assertEqual(self.check(x)["decision"],"HOLD_NO_DIRECT_TICKET_URL")
    def test_invented_event_id(self):
        x=fixture();x["ticket_event_id"]="0Q252550255605202263";self.assertEqual(self.check(x)["decision"],"HOLD_NO_PRICE_OR_TICKET_ID_INFERENCE")
    def test_invented_inventory(self):
        x=fixture();x["inventory"]=0;self.assertEqual(self.check(x)["decision"],"HOLD_NO_PRICE_OR_TICKET_ID_INFERENCE")
if __name__=="__main__":unittest.main()
