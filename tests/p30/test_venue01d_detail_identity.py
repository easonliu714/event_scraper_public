"""VENUE-01D synthetic identity negatives; no HTTP."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
import p30_venue01d_detail_identity as m
URL="https://www.arena.taipei/News_Content.aspx?n=0123456789ABCDEF&s=ABCDEF0123456789"
TITLE="虛構節目 2027/1/16-17"
BODY="活動日期/時間：2027/1/16-17"
def check(**kw):
    x=dict(data_sn="123",source_url=URL,list_title=TITLE,detail_url=URL,detail_title=TITLE,detail_body=BODY)
    x.update(kw)
    return m.assess(**x)
class Contract(unittest.TestCase):
    def test_01_review(self): self.assertEqual(check()["decision"],"REVIEW_OFFICIAL_DETAIL_TITLE_ONLY")
    def test_02_date_role(self): self.assertEqual(check()["dateRole"],"REVIEW_TITLE_BODY_ACTIVITY_DATE_PARITY_NOT_ACCEPTED")
    def test_03_conflict(self): self.assertEqual(check(detail_body="活動日期：2027/1/26-27")["dateRole"],"HOLD_TITLE_BODY_ACTIVITY_DATE_CONFLICT")
    def test_04_title_mismatch(self): self.assertEqual(check(detail_title="其他")["decision"],"HOLD_TITLE_MISMATCH")
    def test_05_url_drift(self): self.assertEqual(check(detail_url=URL.replace("ABCDEF0123456789","0123456789ABCDEF"))["decision"],"HOLD_SOURCE_URL_DRIFT")
    def test_06_host(self): self.assertEqual(check(detail_url=URL.replace("arena.taipei","evil.test"))["decision"],"HOLD_UNVERIFIED_OFFICIAL_URL")
    def test_07_query(self): self.assertEqual(check(source_url=URL+"&ticket=1")["decision"],"HOLD_UNVERIFIED_OFFICIAL_URL")
    def test_08_sn(self): self.assertEqual(check(data_sn="x123")["decision"],"HOLD_INVALID_INPUT")
    def test_09_no_raw(self):
        self.assertNotIn(TITLE,str(check()))
        self.assertNotIn(URL,str(check()))
        self.assertNotIn(BODY,str(check()))
    def test_10_no_ticket(self): self.assertIsNone(check()["ticketEventId"])
    def test_11_no_accept(self): self.assertEqual(check()["acceptedFields"],0)
    def test_12_no_publish(self): self.assertFalse(check()["published"])
    def test_13_no_get(self): self.assertEqual(m.offline_contract()["httpRequests"],0)
    def test_14_announcement(self): self.assertEqual(check(detail_body="日期時間：2027/1/16-17")["dateRole"],"HOLD_EXPLICIT_ACTIVITY_LABEL_MISSING_OR_AMBIGUOUS")
    def test_15_oversize(self): self.assertEqual(check(detail_body="x"*100001)["decision"],"HOLD_BODY_CAP")
if __name__=="__main__": unittest.main()
