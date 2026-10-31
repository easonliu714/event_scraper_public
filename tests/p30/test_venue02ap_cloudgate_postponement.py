"""P30-VENUE-02AP: strict venue/ticket event and two postponements regressions."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02ap_cloudgate_postponement.py"
spec = importlib.util.spec_from_file_location("venue02ap", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    venue = dict(url=m.VENUE_URL, venue_id="1680", title=m.TITLE, venue=m.VENUE,
                 ticket_url=m.TICKET_URL + "?previewTime=1787200144171",
                 showtimes=[list(x) for x in m.SHOWTIMES],
                 postponements=[list(x) for x in m.POSTPONED], price_label="400")
    ticket = dict(url=m.TICKET_URL, event_id=m.EVENT_ID, title=m.TITLE,
                  venue=m.VENUE, postponements=[list(x) for x in m.POSTPONED],
                  ticket_session_ids=None, session_inventory=None, session_prices=None)
    return venue, ticket

class Gate(unittest.TestCase):
    def check(self, venue=None, ticket=None, date="2026-10-31"):
        a, b = fixture()
        return m.inspect(a if venue is None else venue, b if ticket is None else ticket, date)
    def assert_hold(self, expected, venue=None, ticket=None, date="2026-10-31"):
        x = self.check(venue, ticket, date)
        self.assertEqual(x["decision"], expected)
        self.assertEqual(x["acceptedFields"], 0)
        self.assertEqual(x["goldenAccepted"], 0)
        self.assertFalse(x["published"])
    def test_review(self):
        x = self.check()
        self.assertEqual(x["decision"], "HOLD_TICKET_SESSION_ID_AND_INVENTORY_UNVERIFIED")
        self.assertEqual(len(x["candidateProvenance"]), 11)
        self.assertEqual({y["decision"] for y in x["candidateProvenance"]}, {"REVIEW_NOT_FORMALLY_ACCEPTED"})
        self.assertEqual({y["source"] for y in x["candidateProvenance"]}, {"VENUE", "TICKET_05"})
    def test_bad_observed_date(self):
        self.assert_hold("HOLD_OBSERVED_AT", date="2026-02-30")
    def test_bad_detail_id(self):
        a,b=fixture();a["venue_id"]="1681";self.assert_hold("HOLD_VENUE_DETAIL_ID",venue=a)
    def test_bad_venue_url(self):
        a,b=fixture();a["url"]+="?utm=1";self.assert_hold("HOLD_VENUE_DETAIL_ID",venue=a)
    def test_bad_ticket_host(self):
        a,b=fixture();a["ticket_url"]="https://opentix.life/event/"+m.EVENT_ID;self.assert_hold("HOLD_DIRECT_TICKET_URL",venue=a)
    def test_bad_ticket_query(self):
        a,b=fixture();a["ticket_url"]+="&sessionId=123";self.assert_hold("HOLD_DIRECT_TICKET_URL",venue=a)
    def test_ticket_query_not_session(self):
        a,b=fixture();a["ticket_url"]=m.TICKET_URL;self.assert_hold("HOLD_TICKET_SESSION_ID_AND_INVENTORY_UNVERIFIED",venue=a)
    def test_ticket_event_id(self):
        a,b=fixture();b["event_id"]="2086059234803216386";self.assert_hold("HOLD_TICKET_EVENT_ID",ticket=b)
    def test_ticket_detail_url(self):
        a,b=fixture();b["url"]+="?previewTime=1787200144171";self.assert_hold("HOLD_TICKET_EVENT_ID",ticket=b)
    def test_title(self):
        a,b=fixture();b["title"]+="!";self.assert_hold("HOLD_CROSS_SOURCE_EXACT_TITLE",ticket=b)
    def test_venue_name(self):
        a,b=fixture();a["venue"]="臺北小巨蛋";self.assert_hold("HOLD_CROSS_SOURCE_VENUE",venue=a)
    def test_four_showtimes(self):
        a,b=fixture();a["showtimes"].pop();self.assert_hold("HOLD_FOUR_VENUE_SHOWTIMES",venue=a)
    def test_two_distinct_december_sessions(self):
        a,b=fixture();a["showtimes"][3][1]="13:30";self.assert_hold("HOLD_FOUR_VENUE_SHOWTIMES",venue=a)
    def test_venue_old_new_postponement(self):
        a,b=fixture();a["postponements"][0][0]="2026-12-19";self.assert_hold("HOLD_POSTPONEMENT_OLD_NEW_ROLE",venue=a)
    def test_ticket_postponement_conflict(self):
        a,b=fixture();b["postponements"][1][2]="2026-11-14";self.assert_hold("HOLD_TICKET_POSTPONEMENT_PARITY",ticket=b)
    def test_price_is_venue_declared_only(self):
        a,b=fixture();a["price_label"]="0";self.assert_hold("HOLD_PRICE_OR_TICKET_SESSION_INFERENCE",venue=a)
    def test_invented_ticket_session(self):
        a,b=fixture();b["ticket_session_ids"]=["2086059234803216385-1"];self.assert_hold("HOLD_PRICE_OR_TICKET_SESSION_INFERENCE",ticket=b)
    def test_invented_inventory(self):
        a,b=fixture();b["session_inventory"]=0;self.assert_hold("HOLD_INVENTORY_OR_SESSION_PRICE_INFERENCE",ticket=b)
    def test_invented_session_price(self):
        a,b=fixture();b["session_prices"]=[400];self.assert_hold("HOLD_INVENTORY_OR_SESSION_PRICE_INFERENCE",ticket=b)

if __name__ == "__main__":
    unittest.main()
