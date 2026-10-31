import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02aj_zepp_price_sale_boundary import *

def sample():
    return (dict(url=DETAIL,rid=RID,title="2026 GMMTV FANDAY 39 in TAIPEI",
                 date="2026-10-31",sessions=list(SESSIONS),ticket_url=TICKET,
                 ticket_body_status="網頁建置中",prices=list(PRICES),
                 sale_starts=list(SALE),price_to_session=None,
                 sale_to_session=None,observed_at="2026-10-31"),
            dict(url=TICKET,js_shell=True,title_verified=False,session_verified=False))

class Tests(unittest.TestCase):
    def test_source_observed_roles(self):
        r=inspect(*sample())
        self.assertEqual((r["priceTierCount"],r["saleWindowCount"],r["sessionCount"]),(9,2,2))
        self.assertEqual(len(r["candidateProvenance"]),13)
        self.assertEqual(r["decision"],"HOLD_PRICE_SALE_TO_SESSION_MAPPING_AND_TICKET_PARITY")
    def test_same_rid_required(self):
        d,t=sample();d["rid"]="999999"
        self.assertEqual(inspect(d,t)["decision"],"HOLD_VENUE_SAME_RID_SESSION_IDENTITY")
    def test_title_mismatch(self):
        d,t=sample();d["title"]="another"
        self.assertEqual(inspect(d,t)["decision"],"HOLD_VENUE_SAME_RID_SESSION_IDENTITY")
    def test_session_loss(self):
        d,t=sample();d["sessions"].pop()
        self.assertEqual(inspect(d,t)["decision"],"HOLD_VENUE_SAME_RID_SESSION_IDENTITY")
    def test_ticket_body_status_conflict(self):
        d,t=sample();d["ticket_body_status"]="已驗證"
        self.assertEqual(inspect(d,t)["decision"],"HOLD_TICKET_LINK_BODY_STATUS_CONFLICT")
    def test_price_cardinality(self):
        d,t=sample();d["prices"].pop()
        self.assertEqual(inspect(d,t)["decision"],"HOLD_PRICE_SALE_ROLE_OR_CARDINALITY")
    def test_sale_not_performance(self):
        d,t=sample();d["sale_starts"]=["2026-10-31 13:00",SALE[1]]
        self.assertEqual(inspect(d,t)["decision"],"HOLD_PRICE_SALE_ROLE_OR_CARDINALITY")
    def test_per_session_price_not_inferred(self):
        d,t=sample();d["price_to_session"]={0:8500}
        self.assertEqual(inspect(d,t)["decision"],"HOLD_UNSUPPORTED_PER_SESSION_MAPPING")
    def test_js_shell_not_verified(self):
        d,t=sample();t["js_shell"]=False
        self.assertEqual(inspect(d,t)["decision"],"HOLD_EXTERNAL_TICKET_OBSERVATION")
    def test_ticket_title_not_accepted(self):
        d,t=sample();t["title_verified"]=True
        self.assertEqual(inspect(d,t)["decision"],"HOLD_TICKET_PARITY_UNPROVEN")
    def test_hash_and_release_hold(self):
        r=inspect(*sample())
        self.assertTrue(all(len(x["valueSHA256"])==64 for x in r["candidateProvenance"]))
        self.assertEqual(r["acceptedFields"],0)
        self.assertFalse(r["published"])
        self.assertIsNone(r["ticketEventId"])
        self.assertEqual(r["releaseState"],HOLD)

if __name__=="__main__":
    unittest.main()
