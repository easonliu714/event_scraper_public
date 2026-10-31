import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02au_opentix_marathon_segments.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"url": m.SOURCE, "event_id": m.EVENT_ID,
            "title": "身體我的名片", "venue": "樹林藝文中心演藝廳",
            "artist_count": 16, "artist_role": "PROGRAM_ARTISTS_NOT_TICKETS",
            "price_role": "EVENT_FACE_AND_LIMITED_DISCOUNT",
            "face_price_ntd": 1000, "limited_prices_ntd": [650, 800],
            "per_session_price": None, "bundle_price": None,
            "ticket_session_ids": None, "inventory": None,
            "shortlink_redirect_verified": False,
            "description_shows": {day: [{"start": a, "end": b, "role": "INTERNAL_PROGRAM_BLOCK",
                                         "ticket_session_id": None, "ticket_inventory": None}
                                        for a, b in blocks] for day, blocks in m.SHOWS.items()}}

class TestGate(unittest.TestCase):
    def check(self, change=None):
        x = fixture()
        if change:
            change(x)
        return m.inspect(x, "2026-11-01")

    def reject(self, expected, change):
        x = self.check(change)
        self.assertEqual(x["decision"], expected)
        self.assertEqual(x["acceptedFields"], 0)
        self.assertFalse(x["published"])

    def test_two_shows_eight_blocks_are_not_ticket_sessions(self):
        x = self.check()
        self.assertEqual(x["decision"], "HOLD_EIGHT_PROGRAM_BLOCKS_NOT_TICKET_SESSIONS")
        self.assertEqual(len(x["provenance"]), 9)

    def test_invalid_observation(self):
        self.assertEqual(m.inspect(fixture(), "2026-02-30")["decision"], "HOLD_OBSERVED_AT")

    def test_host(self):
        self.reject("HOLD_CANONICAL_EVENT_ID", lambda x: x.update(url="https://evil.test/event/" + m.EVENT_ID))

    def test_query(self):
        self.reject("HOLD_CANONICAL_EVENT_ID", lambda x: x.update(url=m.SOURCE + "?other=1"))

    def test_wrong_id(self):
        self.reject("HOLD_CANONICAL_EVENT_ID", lambda x: x.update(event_id="2099700588990402561"))

    def test_fabricated_ticket_session(self):
        self.reject("HOLD_TICKET_SESSION_OR_REDIRECT_UNVERIFIED", lambda x: x.update(ticket_session_ids=["fake"]))

    def test_claim_shortlink_redirect(self):
        self.reject("HOLD_TICKET_SESSION_OR_REDIRECT_UNVERIFIED", lambda x: x.update(shortlink_redirect_verified=True))

    def test_venue(self):
        self.reject("HOLD_TITLE_VENUE", lambda x: x.update(venue="other"))

    def test_artists_not_tickets(self):
        self.reject("HOLD_ARTIST_COUNT_ROLE", lambda x: x.update(artist_role="TICKET_INVENTORY"))

    def test_price_role(self):
        self.reject("HOLD_PRICE_TIER_ROLE", lambda x: x.update(price_role="SESSION_PRICE"))

    def test_discount_price(self):
        self.reject("HOLD_PRICE_TIER_ROLE", lambda x: x.update(limited_prices_ntd=[650, 700]))

    def test_bundle_price_not_event_price(self):
        self.reject("HOLD_PRICE_NOT_SESSION_OR_BUNDLE", lambda x: x.update(bundle_price=1000))

    def test_session_price_unverified(self):
        self.reject("HOLD_PRICE_NOT_SESSION_OR_BUNDLE", lambda x: x.update(per_session_price=1000))

    def test_missing_show(self):
        self.reject("HOLD_TWO_DESCRIPTION_SHOWS", lambda x: x["description_shows"].pop("2026-11-29"))

    def test_extra_segment(self):
        self.reject("HOLD_FOUR_PROGRAM_BLOCKS", lambda x: x["description_shows"]["2026-11-28"].append({}))

    def test_segment_wrong_date_local(self):
        self.reject("HOLD_PROGRAM_BLOCK_LOCAL_TIME", lambda x: x["description_shows"]["2026-11-28"][0].update(start="11:00"))

    def test_segment_role(self):
        self.reject("HOLD_PROGRAM_BLOCK_LOCAL_TIME", lambda x: x["description_shows"]["2026-11-29"][0].update(role="TICKET_SESSION"))

    def test_segment_id_fabrication(self):
        self.reject("HOLD_PROGRAM_BLOCK_NOT_TICKET_SESSION", lambda x: x["description_shows"]["2026-11-28"][0].update(ticket_session_id="fake"))

    def test_segment_inventory_fabrication(self):
        self.reject("HOLD_PROGRAM_BLOCK_NOT_TICKET_SESSION", lambda x: x["description_shows"]["2026-11-29"][3].update(ticket_inventory=20))

if __name__ == "__main__":
    unittest.main()
