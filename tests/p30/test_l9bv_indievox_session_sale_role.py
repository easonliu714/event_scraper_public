import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bv_indievox_session_sale_role import *

def sample():
    d = "https://www.indievox.com/activity/detail/" + EVENT_ID
    g = "https://www.indievox.com/activity/game/" + EVENT_ID
    return (dict(url=HOME, detail_url=d, title=TITLE, observed_at="2026-10-31"),
            dict(url=d, title=TITLE, sessions=list(SESSIONS), prices=list(PRICES),
                 sale_windows=list(SALE)),
            dict(url=g, title=TITLE, sessions=list(SESSIONS),
                 per_session_price_verified=False, inventory_verified=False))

class Tests(unittest.TestCase):
    def test_source_identity(self):
        self.assertTrue(first_party(sample()[1]["url"], "detail"))
    def test_six_distinct_sessions_and_roles(self):
        r=inspect(*sample())
        self.assertEqual(r["distinctSessionCandidates"], 6)
        self.assertEqual(len(r["candidateProvenance"]), 12)
        self.assertEqual(r["decision"], "HOLD_PER_SESSION_PRICE_AND_INDEPENDENT_ACCEPTANCE")
    def test_cross_origin_rejected(self):
        i,d,g=sample(); g["url"]=g["url"].replace("www.indievox.com","evil.example")
        self.assertEqual(inspect(i,d,g)["decision"], "HOLD_FIRST_PARTY_SAME_ID_EDGE")
    def test_query_injection_rejected(self):
        i,d,g=sample(); g["url"] += "?id=other"
        self.assertEqual(inspect(i,d,g)["decision"], "HOLD_FIRST_PARTY_SAME_ID_EDGE")
    def test_other_event_id_rejected(self):
        i,d,g=sample(); g["url"]=g["url"].replace(EVENT_ID,"26_iv0428143")
        self.assertEqual(inspect(i,d,g)["decision"], "HOLD_FIRST_PARTY_SAME_ID_EDGE")
    def test_title_drift_rejected(self):
        i,d,g=sample(); d["title"]="Different event"
        self.assertEqual(inspect(i,d,g)["decision"], "HOLD_LIST_DETAIL_GAME_TITLE_PARITY")
    def test_missing_session_rejected(self):
        i,d,g=sample(); g["sessions"].pop()
        self.assertEqual(inspect(i,d,g)["decision"], "HOLD_SIX_ROW_SESSION_IDENTITY")
    def test_sale_is_not_event(self):
        i,d,g=sample(); d["sale_windows"] = ["2026/12/05 20:00",SALE[1]]
        self.assertEqual(inspect(i,d,g)["decision"], "HOLD_PRICE_OR_SALE_ROLE_SOURCE_PARITY")
    def test_price_mapping_cannot_be_claimed(self):
        i,d,g=sample(); g["per_session_price_verified"]=True
        self.assertEqual(inspect(i,d,g)["decision"], "HOLD_PER_SESSION_PRICE_MAPPING_UNKNOWN")
    def test_live_inventory_not_verified(self):
        i,d,g=sample(); g["inventory_verified"]=True
        self.assertEqual(inspect(i,d,g)["decision"], "HOLD_LIVE_INVENTORY_UNKNOWN")
    def test_provenance(self):
        r=inspect(*sample())
        self.assertTrue(all(x["valueSHA256"] and x["observed_at"]=="2026-10-31" for x in r["candidateProvenance"]))
        self.assertEqual(r["acceptedFields"],0)
        self.assertEqual(r["goldenAccepted"],0)
        self.assertFalse(r["published"])
        self.assertEqual(r["releaseState"],HOLD)

if __name__ == "__main__":
    unittest.main()
