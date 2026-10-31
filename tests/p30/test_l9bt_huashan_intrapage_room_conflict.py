#!/usr/bin/env python3
"""P30-L9-BT: source-local room conflict is not ticket-room correction."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from p30_l9bt_huashan_intrapage_room_conflict import inspect
from test_l9bs_huashan_accupass_direct_edge import samples
STAMP="2026-10-31T01:58:00Z"
def sample():
    v,t=samples()
    return v,t,[
        dict(role="HEADER_VENUE_ROOM",label="地點",source=v["source"],
             source_url=v["url"],observed_at=STAMP,value="中3A館 2樓拱廳"),
        dict(role="BODY_VENUE_ROOM",label="►活動地點",source=v["source"],
             source_url=v["url"],observed_at=STAMP,
             value="華山1914文化創意產業園區 中3館2樓拱廳")]
class Cases(unittest.TestCase):
    def test_official_header_body_conflict_hold(self):
        v,t,rows=sample();x=inspect(v,t,rows)
        self.assertEqual(x["decision"],"HOLD_SAME_SOURCE_HEADER_BODY_ROOM_CONFLICT")
        self.assertTrue(x["sameSourceConflict"])
        self.assertEqual(len(x["candidateProvenance"]),3)
        self.assertEqual(x["acceptedFields"],0)
        self.assertFalse(x["published"])
    def test_ticket_matching_body_does_not_override_header(self):
        v,t,rows=sample();t["room"]=rows[1]["value"]
        self.assertEqual(inspect(v,t,rows)["decision"],"HOLD_SAME_SOURCE_HEADER_BODY_ROOM_CONFLICT")
    def test_ticket_matching_header_does_not_override_body(self):
        v,t,rows=sample();t["room"]=rows[0]["value"]
        self.assertEqual(inspect(v,t,rows)["decision"],"HOLD_SAME_SOURCE_HEADER_BODY_ROOM_CONFLICT")
    def test_missing_body_refused(self):
        v,t,rows=sample()
        self.assertEqual(inspect(v,t,rows[:1])["decision"],"HOLD_NOT_EXACT_TWO_ROOM_CLAIMS")
    def test_duplicate_role_refused(self):
        v,t,rows=sample();rows[1]["role"]=rows[0]["role"]
        self.assertEqual(inspect(v,t,rows)["decision"],"HOLD_DUPLICATE_OR_UNKNOWN_ROOM_ROLE")
    def test_source_url_spoof_refused(self):
        v,t,rows=sample();rows[1]["source_url"]="https://evil.example"
        self.assertEqual(inspect(v,t,rows)["decision"],"HOLD_ROOM_LABEL_SOURCE_PROVENANCE")
    def test_label_mismatch_refused(self):
        v,t,rows=sample();rows[1]["label"]="售票日期"
        self.assertEqual(inspect(v,t,rows)["decision"],"HOLD_ROOM_LABEL_SOURCE_PROVENANCE")
    def test_missing_provenance_refused(self):
        v,t,rows=sample();rows[1].pop("observed_at")
        self.assertEqual(inspect(v,t,rows)["decision"],"HOLD_ROOM_LABEL_SOURCE_PROVENANCE")
    def test_same_source_parity_ticket_conflict_still_hold(self):
        v,t,rows=sample();rows[1]["value"]=rows[0]["value"]
        self.assertEqual(inspect(v,t,rows)["decision"],"HOLD_CROSS_SOURCE_ROOM_CONFLICT")
    def test_full_parity_review_not_formal(self):
        v,t,rows=sample();rows[1]["value"]=rows[0]["value"];t["room"]=v["room"]
        x=inspect(v,t,rows)
        self.assertEqual(x["decision"],"REVIEW_ROOM_PARITY_NOT_FORMALLY_ACCEPTED")
        self.assertEqual(x["acceptedFields"],0)
        self.assertEqual(x["goldenAccepted"],0)
if __name__=="__main__":
    unittest.main()
