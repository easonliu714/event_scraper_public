"""P30-L9-CD: independent source-bound game/detail and refund contradiction regressions."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cd_indievox_refund_roles.py"
spec = importlib.util.spec_from_file_location("l9cd", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    detail = dict(url=m.DETAIL_URL, title=m.TITLE, venue=m.VENUE,
        performance=list(m.PERFORMANCE), door_time=m.DOOR_TIME,
        price_tiers=[list(x) for x in m.PRICE_TIERS], sale_start=m.SALE_START,
        presale_end=m.PRESALE_END, refund_cutoff=m.REFUND_CUTOFF,
        refund_no_accept_from=m.REFUND_NO_ACCEPT_FROM, ticket_session_id=None)
    game = dict(url=m.GAME_URL, title=m.TITLE, venue=m.VENUE,
        performance=list(m.PERFORMANCE), action="Start ordering",
        ticket_session_id=None, inventory=None, checkout_price=None)
    return detail, game

class Gate(unittest.TestCase):
    def check(self, detail=None, game=None, date="2026-10-31"):
        a,b=fixture()
        return m.inspect(a if detail is None else detail, b if game is None else game, date)
    def reject(self, code, detail=None, game=None, date="2026-10-31"):
        x=self.check(detail,game,date)
        self.assertEqual(x["decision"],code)
        self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
    def test_source_review_with_explicit_refund_conflict(self):
        x=self.check()
        self.assertEqual(x["decision"],"HOLD_REFUND_DEADLINE_CONTRADICTION_AND_NO_TICKET_SESSION_ID")
        self.assertEqual(len(x["candidateProvenance"]),11)
        self.assertEqual({y["decision"] for y in x["candidateProvenance"]},{"REVIEW_NOT_FORMALLY_ACCEPTED"})
    def test_invalid_observed_date(self):
        self.reject("HOLD_OBSERVED_AT",date="2026-02-30")
    def test_detail_wrong_id(self):
        a,b=fixture();a["url"]=m.DETAIL_URL+"x";self.reject("HOLD_SAME_EVENT_PATH_ID",detail=a)
    def test_game_wrong_id(self):
        a,b=fixture();b["url"]=m.GAME_URL.replace(m.EVENT_ID,"26_iv0000000");self.reject("HOLD_SAME_EVENT_PATH_ID",game=b)
    def test_game_query_not_identity(self):
        a,b=fixture();b["url"]+="?sessionId=123";self.reject("HOLD_SAME_EVENT_PATH_ID",game=b)
    def test_host_mismatch(self):
        a,b=fixture();a["url"]=a["url"].replace("www.indievox.com","indievox.com");self.reject("HOLD_SAME_EVENT_PATH_ID",detail=a)
    def test_title_mismatch(self):
        a,b=fixture();b["title"]+="!";self.reject("HOLD_SAME_EVENT_TITLE",game=b)
    def test_venue_mismatch(self):
        a,b=fixture();b["venue"]="其他場館";self.reject("HOLD_VENUE_PARITY",game=b)
    def test_game_date_mismatch(self):
        a,b=fixture();b["performance"][0]="2026-12-11";self.reject("HOLD_PERFORMANCE_PARITY",game=b)
    def test_door_is_not_showtime(self):
        a,b=fixture();a["door_time"]="19:30";self.reject("HOLD_DOOR_NOT_SHOWTIME",detail=a)
    def test_presale_price_not_at_door(self):
        a,b=fixture();a["price_tiers"][1][1]=850;self.reject("HOLD_PRICE_TIER_ROLES",detail=a)
    def test_sale_start_not_performance(self):
        a,b=fixture();a["sale_start"]="2026-12-12 19:30";self.reject("HOLD_SALE_PERIOD_NOT_PERFORMANCE",detail=a)
    def test_refund_claim_not_silently_rewritten(self):
        a,b=fixture();a["refund_no_accept_from"]="2026-12-03";self.reject("HOLD_REFUND_SOURCE_EVIDENCE",detail=a)
    def test_action_not_inventory(self):
        a,b=fixture();b["action"]="Available";self.reject("HOLD_GAME_ACTION_ROLE",game=b)
    def test_invented_session_id(self):
        a,b=fixture();b["ticket_session_id"]="1";self.reject("HOLD_UNVERIFIED_TICKET_SESSION_OR_INVENTORY",game=b)
    def test_invented_checkout_price(self):
        a,b=fixture();b["checkout_price"]=850;self.reject("HOLD_UNVERIFIED_TICKET_SESSION_OR_INVENTORY",game=b)
    def test_invented_inventory(self):
        a,b=fixture();b["inventory"]=10;self.reject("HOLD_UNVERIFIED_TICKET_SESSION_OR_INVENTORY",game=b)

if __name__=="__main__":
    unittest.main()
