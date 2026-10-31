"""P30-VENUE-02AR strict venue SID -> ticket Event ID two-show parity."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02ar_shulin_opentix_parity.py"
spec = importlib.util.spec_from_file_location("venue02ar", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    index = dict(url=m.INDEX_URL, detail_url=m.DETAIL_URL, title="走戲人-兒童歌仔戲《酷麗鳥搞砸了》")
    venue = dict(url=m.DETAIL_URL, sid=m.VENUE_SID, ticket_url=m.TICKET_URL,
                 title="走戲人-兒童歌仔戲《酷麗鳥搞砸了》", venue=m.VENUE,
                 shows=[list(x) for x in m.SHOWS], listed_price=m.VENUE_PRICE,
                 update_date=m.UPDATE_DATE)
    ticket = dict(url=m.TICKET_URL, title="走戲人《酷麗鳥搞砸了》", venue=m.VENUE,
                  description_shows=[list(x) for x in m.SHOWS],
                  package_sale_period=list(m.PACKAGE_SALE),
                  ticket_session_ids=None, per_session_price=None, inventory=None)
    return index, venue, ticket

class Gate(unittest.TestCase):
    def check(self, mutation=None, date="2026-10-31"):
        i, v, t = fixture()
        if mutation:
            mutation(i, v, t)
        return m.inspect(i, v, t, date)
    def reject(self, code, mutation=None, date="2026-10-31"):
        x = self.check(mutation, date)
        self.assertEqual(x["decision"], code)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
    def test_direct_link_two_shows_review(self):
        x = self.check()
        self.assertEqual(x["decision"], "HOLD_OPENTIX_STATIC_CHOOSER_NO_TICKET_SESSION_IDS")
        self.assertEqual(len(x["candidateProvenance"]), 11)
    def test_invalid_date(self):
        self.reject("HOLD_OBSERVED_AT", date="2026-02-30")
    def test_index_sid_mismatch(self):
        self.reject("HOLD_OFFICIAL_INDEX_TO_SID", lambda i, v, t: i.update(detail_url=m.DETAIL_URL.replace(m.VENUE_SID, "other")))
    def test_index_query_duplicate(self):
        self.reject("HOLD_OFFICIAL_INDEX_TO_SID", lambda i, v, t: i.update(detail_url=m.DETAIL_URL+"&sid="+m.VENUE_SID))
    def test_index_malformed_query(self):
        self.reject("HOLD_OFFICIAL_INDEX_TO_SID", lambda i, v, t: i.update(detail_url=m.DETAIL_URL+"&bad"))
    def test_venue_sid_not_ticket(self):
        self.reject("HOLD_VENUE_SID", lambda i, v, t: v.update(sid=m.TICKET_EVENT_ID))
    def test_ticket_host(self):
        self.reject("HOLD_DIRECT_OPENTIX_EVENT_LINK", lambda i, v, t: t.update(url="https://opentix.life/event/"+m.TICKET_EVENT_ID))
    def test_ticket_query(self):
        self.reject("HOLD_DIRECT_OPENTIX_EVENT_LINK", lambda i, v, t: v.update(ticket_url=m.TICKET_URL+"?session=1"))
    def test_title_mismatch(self):
        self.reject("HOLD_CROSS_SOURCE_TITLE", lambda i, v, t: t.update(title="另一節目"))
    def test_venue_mismatch(self):
        self.reject("HOLD_CROSS_SOURCE_VENUE", lambda i, v, t: t.update(venue="另一場館"))
    def test_second_show_mismatch(self):
        self.reject("HOLD_TWO_SHOW_DESCRIPTION_PARITY", lambda i, v, t: t["description_shows"][1].__setitem__(1, "18:30"))
    def test_update_date_not_show(self):
        self.reject("HOLD_UPDATE_DATE_NOT_SHOW", lambda i, v, t: v.update(update_date="2026-11-14"))
    def test_price_not_session(self):
        self.reject("HOLD_PRICE_VS_PACKAGE_SALE", lambda i, v, t: v.update(listed_price=500))
    def test_package_sale_not_show(self):
        self.reject("HOLD_PRICE_VS_PACKAGE_SALE", lambda i, v, t: t.update(package_sale_period=["2026-11-14", "2026-11-14"]))
    def test_invented_session(self):
        self.reject("HOLD_TICKET_SESSION_PRICE_INVENTORY", lambda i, v, t: t.update(ticket_session_ids=["1", "2"]))
    def test_invented_session_price(self):
        self.reject("HOLD_TICKET_SESSION_PRICE_INVENTORY", lambda i, v, t: t.update(per_session_price=400))
    def test_invented_inventory(self):
        self.reject("HOLD_TICKET_SESSION_PRICE_INVENTORY", lambda i, v, t: t.update(inventory=40))

if __name__ == "__main__":
    unittest.main()
