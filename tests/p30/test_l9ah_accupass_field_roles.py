"""P30-L9-AH synthetic local DOM semantic-role and refusal tests (no network)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
import p30_l9ah_accupass_field_roles as m

def doc(content):
    return "<html><main><h1>虛構活動</h1>"+content+"</main></html>"
def dl(label,value):
    return f"<dl><dt>{label}</dt><dd>{value}</dd></dl>"
def tr(label,value):
    return f"<table><tr><th>{label}</th><td>{value}</td></tr></table>"
class RoleTests(unittest.TestCase):
    def test_01_release(self):self.assertEqual(m.RELEASE,"HARD_HOLD_NO_PUBLICATION")
    def test_02_parent(self):self.assertEqual(len(m.PARENT),40)
    def test_03_eight_roles(self):self.assertEqual(len(m.ROLE_LABELS),8)
    def test_04_event(self):
        r=m.scoped_pairs(doc(dl("活動日期","2099/01/01")))
        self.assertEqual(r["roles"]["EVENT"]["localPairCount"],1)
    def test_05_sale(self):
        r=m.scoped_pairs(doc(dl("開賣時間","2098/12/01")))
        self.assertEqual(r["roles"]["SALE"]["localPairCount"],1)
        self.assertEqual(r["roles"]["EVENT"]["localPairCount"],0)
    def test_06_admission(self):self.assertEqual(m.scoped_pairs(doc(tr("入場時間","17:00")))["roles"]["ADMISSION"]["localPairCount"],1)
    def test_07_registration(self):self.assertEqual(m.scoped_pairs(doc(dl("報名期間","2098")))["roles"]["REGISTRATION"]["localPairCount"],1)
    def test_08_voucher(self):self.assertEqual(m.scoped_pairs(doc(dl("兌換時間","2098")))["roles"]["VOUCHER"]["localPairCount"],1)
    def test_09_venue(self):self.assertEqual(m.scoped_pairs(doc(dl("活動地點","虛構場館")))["roles"]["VENUE"]["localPairCount"],1)
    def test_10_price(self):self.assertEqual(m.scoped_pairs(doc(dl("票價","100")))["roles"]["PRICE"]["localPairCount"],1)
    def test_11_session(self):self.assertEqual(m.scoped_pairs(doc(dl("場次","第一場")))["roles"]["SESSION"]["localPairCount"],1)
    def test_12_no_global_regex(self):
        r=m.scoped_pairs(doc("<p>活動日期 2099/01/01 售票時間 2098/12/01</p>"))
        self.assertEqual(r["roles"]["EVENT"]["localPairCount"],0)
    def test_13_no_semantic_root(self):self.assertEqual(m.scoped_pairs("<body>"+dl("票價","100")+"</body>")["hold"],"NO_SEMANTIC_ROOT")
    def test_14_conflict(self):
        r=m.scoped_pairs(doc(dl("活動日期","2099/01/01")+dl("活動日期","2099/01/02")))
        self.assertEqual(r["roles"]["EVENT"]["decision"],"HOLD_CONFLICTING_LOCAL_VALUES")
    def test_15_duplicate_same(self):
        r=m.scoped_pairs(doc(dl("票價","100")+dl("票價","100")))
        self.assertEqual(r["roles"]["PRICE"]["distinctValueCount"],1)
    def test_16_bad_pair(self):
        r=m.scoped_pairs(doc("<dl><dt>活動日期</dt><span>2099</span></dl>"))
        self.assertEqual(r["roles"]["EVENT"]["localPairCount"],0)
    def test_17_bad_table(self):
        r=m.scoped_pairs(doc("<table><tr><td>活動日期</td><td>2099</td></tr></table>"))
        self.assertEqual(r["roles"]["EVENT"]["localPairCount"],0)
    def test_18_missing_value(self):
        r=m.scoped_pairs(doc(dl("票價","")))
        self.assertEqual(r["roles"]["PRICE"]["localPairCount"],0)
    def test_19_long_value(self):
        r=m.scoped_pairs(doc(dl("票價","x"*(m.MAX_VALUE_CHARS+1))))
        self.assertEqual(r["roles"]["PRICE"]["localPairCount"],0)
    def test_20_html_cap(self):
        self.assertEqual(m.scoped_pairs("x"*(m.MAX_HTML_BYTES+1))["hold"],"HTML_CAP")
    def test_21_scope_cap(self):
        self.assertEqual(m.scoped_pairs("<main></main>"*(m.MAX_SCOPES+1))["hold"],"SCOPE_CAP")
    def test_22_pair_cap(self):
        self.assertEqual(m.scoped_pairs(doc(dl("票價","100")*(m.MAX_PAIRS+1)))["hold"],"PAIR_CAP")
    def test_23_label_normalization(self):self.assertEqual(m.clean_label(" 票 價 ： "),"票價")
    def test_24_accepted_zero(self):self.assertEqual(m.scoped_pairs(doc(dl("票價","100")))["acceptedFields"],0)
    def test_25_no_values_in_report(self):
        self.assertNotIn("虛構場館",str(m.scoped_pairs(doc(dl("活動地點","虛構場館")))))
    def test_26_no_dates_in_report(self):
        self.assertNotIn("2099/01/01",str(m.scoped_pairs(doc(dl("活動日期","2099/01/01")))))
    def test_27_unrecognized_label(self):
        self.assertEqual(m.scoped_pairs(doc(dl("公告時間","2099")))["roles"]["EVENT"]["localPairCount"],0)
    def test_28_mixed_roles(self):
        r=m.scoped_pairs(doc(dl("售票時間","2098")+dl("入場時間","18:00")+dl("活動日期","2099")))
        self.assertEqual([r["roles"][k]["localPairCount"] for k in ("SALE","ADMISSION","EVENT")],[1,1,1])
    def test_29_review_not_pass(self):
        r=m.scoped_pairs(doc(dl("活動日期","2099")))
        self.assertEqual(r["roles"]["EVENT"]["decision"],"REVIEW_ONE_LOCAL_ROLE_NOT_ACCEPTED")
        self.assertFalse(r["roles"]["EVENT"]["accepted"])
    def test_30_no_publish_function(self):self.assertFalse(hasattr(m,"publish"))

if __name__=="__main__":unittest.main()
