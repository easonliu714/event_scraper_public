"""VENUE-01B no-network contract and fail-closed source-shape tests."""
import sys
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_venue01_live_shape as m

def sample():
    return {"gate":"P30-VENUE-01","records":[{
        "venue_source_key_hash":"0123456789abcdef0123",
        "ticket_event_id":None,"ticket_event_url":None,
        "event_date":None,"sale_date":None,"admission_date":None,
        "registration_date":None,"voucher_date":None,"price":None,
        "session":None,"field_status":"HOLD_SEMANTIC_ROLES_NOT_VERIFIED"
    }],"announcement_count":1,"platform_claim_counts":{"ibon":1},
    "published":False,"golden_accepted":0,"hard_hold_no_publication":True}

class GateTests(unittest.TestCase):
    def test_01_review(self): self.assertEqual(m.assess(sample())["decision"],"REVIEW_LIVE_OFFICIAL_SOURCE_SHAPE_ONLY")
    def test_02_release(self): self.assertEqual(m.RELEASE,"HARD_HOLD_NO_PUBLICATION")
    def test_03_count(self):
        x=sample();x["announcement_count"]=2
        self.assertEqual(m.assess(x)["decision"],"HOLD_COUNT_MISMATCH")
    def test_04_hash(self):
        x=sample();x["records"][0]["venue_source_key_hash"]="bad"
        self.assertEqual(m.assess(x)["decision"],"HOLD_SOURCE_HASH")
    def test_05_id(self):
        x=sample();x["records"][0]["ticket_event_id"]="123"
        self.assertEqual(m.assess(x)["decision"],"HOLD_TICKET_IDENTITY_PROMOTION")
    def test_06_url(self):
        x=sample();x["records"][0]["ticket_event_url"]="https://example.com"
        self.assertEqual(m.assess(x)["decision"],"HOLD_TICKET_IDENTITY_PROMOTION")
    def test_07_date(self):
        x=sample();x["records"][0]["event_date"]="2099-01-01"
        self.assertEqual(m.assess(x)["decision"],"HOLD_UNVERIFIED_FIELD_PROMOTION")
    def test_08_price(self):
        x=sample();x["records"][0]["price"]="100"
        self.assertEqual(m.assess(x)["decision"],"HOLD_UNVERIFIED_FIELD_PROMOTION")
    def test_09_field(self):
        x=sample();x["records"][0]["field_status"]="PASS"
        self.assertEqual(m.assess(x)["decision"],"HOLD_FIELD_STATUS")
    def test_10_publish(self):
        x=sample();x["published"]=True
        self.assertEqual(m.assess(x)["decision"],"HOLD_RELEASE_CONTRACT")
    def test_11_golden(self):
        x=sample();x["golden_accepted"]=1
        self.assertEqual(m.assess(x)["decision"],"HOLD_RELEASE_CONTRACT")
    def test_12_empty(self):
        x=sample();x["records"]=[];x["announcement_count"]=0
        self.assertEqual(m.assess(x)["announcementCount"],0)
    def test_13_duplicate(self):
        x=sample();x["records"].append(dict(x["records"][0]));x["announcement_count"]=2
        self.assertEqual(m.assess(x)["decision"],"HOLD_DUPLICATE_SOURCE_HASH")
    def test_14_cap(self):
        x=sample();x["records"]*=41;x["announcement_count"]=41
        self.assertEqual(m.assess(x)["decision"],"HOLD_RECORDS_OR_CAP")
    def test_15_no_network(self):
        with mock.patch.object(m.prior,"fetch_once",side_effect=AssertionError("NETWORK")):
            self.assertEqual(m.assess(sample())["announcementCount"],1)
    def test_16_bad_report(self): self.assertEqual(m.assess(None)["decision"],"HOLD_INVALID_ADAPTER_REPORT")
    def test_17_wrong_gate(self):
        x=sample();x["gate"]="OTHER"
        self.assertEqual(m.assess(x)["decision"],"HOLD_INVALID_ADAPTER_REPORT")
    def test_18_missing_rows(self):
        x=sample();x.pop("records")
        self.assertEqual(m.assess(x)["decision"],"HOLD_RECORDS_OR_CAP")
    def test_19_non_dict_row(self):
        x=sample();x["records"]=[None]
        self.assertEqual(m.assess(x)["decision"],"HOLD_RECORD_SHAPE")
    def test_20_no_promote(self):
        r=m.assess(sample());self.assertEqual((r["ticketEventIdentityAccepted"],r["fieldsAccepted"],r["goldenAccepted"]),(0,0,0))

if __name__=="__main__": unittest.main()
