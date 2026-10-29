"""P30-L9-AI: synthetic bounded local sibling topology positives and negatives; no network."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_l9ai_accupass_sibling_roles as m


def doc(body):
    return "<html><main><h1>虛構節目</h1>" + body + "</main></html>"


def pair(label, value):
    return "<div class='info'><span>" + label + "</span><span>" + value + "</span></div>"


class LocalSiblingContractTests(unittest.TestCase):
    def test_01_release(self):
        self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")

    def test_02_parent_sha(self):
        self.assertEqual(len(m.PARENT), 40)

    def test_03_roles(self):
        self.assertEqual(len(m.ROLE_LABELS), 8)

    def test_04_event(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("活動日期", "2099/01/01")))["roles"]["EVENT"]["localPairCount"], 1)

    def test_05_sale_not_event(self):
        x = m.inspect_local_siblings(doc(pair("售票時間", "2098/01/01")))["roles"]
        self.assertEqual((x["SALE"]["localPairCount"], x["EVENT"]["localPairCount"]), (1, 0))

    def test_06_admission(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("入場時間", "18:00")))["roles"]["ADMISSION"]["localPairCount"], 1)

    def test_07_registration(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("報名期間", "2098")))["roles"]["REGISTRATION"]["localPairCount"], 1)

    def test_08_voucher(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("兌換時間", "2098")))["roles"]["VOUCHER"]["localPairCount"], 1)

    def test_09_venue(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("活動地點", "虛構場地")))["roles"]["VENUE"]["localPairCount"], 1)

    def test_10_price(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("票價", "100")))["roles"]["PRICE"]["localPairCount"], 1)

    def test_11_session(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("場次", "第一場")))["roles"]["SESSION"]["localPairCount"], 1)

    def test_12_no_global_regex(self):
        self.assertEqual(m.inspect_local_siblings(doc("<p>活動日期 2099/01/01</p>"))["roles"]["EVENT"]["localPairCount"], 0)

    def test_13_no_root(self):
        self.assertEqual(m.inspect_local_siblings("<body>" + pair("票價", "100") + "</body>")["hold"], "HOLD_NO_SEMANTIC_ROOT")

    def test_14_conflict(self):
        x = m.inspect_local_siblings(doc(pair("票價", "100") + pair("票價", "200")))
        self.assertEqual(x["roles"]["PRICE"]["decision"], "HOLD_CONFLICTING_LOCAL_VALUES")

    def test_15_duplicate_value(self):
        x = m.inspect_local_siblings(doc(pair("票價", "100") + pair("票價", "100")))
        self.assertEqual(x["roles"]["PRICE"]["distinctValueCount"], 1)

    def test_16_bad_structure(self):
        x = m.inspect_local_siblings(doc("<div><span>票價</span><span>100</span><span>200</span></div>"))
        self.assertEqual(x["roles"]["PRICE"]["localPairCount"], 0)

    def test_17_hidden(self):
        x = m.inspect_local_siblings(doc("<div hidden><span>票價</span><span>100</span></div>"))
        self.assertEqual(x["roles"]["PRICE"]["localPairCount"], 0)

    def test_18_interactive(self):
        x = m.inspect_local_siblings(doc("<div><span>票價</span><span><button>100</button></span></div>"))
        self.assertEqual(x["roles"]["PRICE"]["localPairCount"], 0)

    def test_19_empty(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("票價", "")))["roles"]["PRICE"]["localPairCount"], 0)

    def test_20_long(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("票價", "x" * 241)))["roles"]["PRICE"]["localPairCount"], 0)

    def test_21_html_cap(self):
        self.assertEqual(m.inspect_local_siblings("x" * (m.MAX_HTML_BYTES + 1))["hold"], "HOLD_HTML_CAP_OR_TYPE")

    def test_22_root_cap(self):
        self.assertEqual(m.inspect_local_siblings("<main></main>" * (m.MAX_ROOTS + 1))["hold"], "HOLD_ROOT_CAP")

    def test_23_container_cap(self):
        self.assertEqual(m.inspect_local_siblings(doc("<div></div>" * (m.MAX_CONTAINERS + 1)))["hold"], "HOLD_CONTAINER_CAP")

    def test_24_pair_cap(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("票價", "100") * (m.MAX_PAIRS + 1)))["hold"], "HOLD_PAIR_CAP")

    def test_25_no_raw_values(self):
        x = m.inspect_local_siblings(doc(pair("活動地點", "虛構場地")))
        self.assertNotIn("虛構場地", str(x))

    def test_26_no_raw_dates(self):
        x = m.inspect_local_siblings(doc(pair("活動日期", "2099/01/01")))
        self.assertNotIn("2099/01/01", str(x))

    def test_27_announcement_not_event(self):
        self.assertEqual(m.inspect_local_siblings(doc(pair("公告時間", "2099")))["roles"]["EVENT"]["localPairCount"], 0)

    def test_28_label_normalization(self):
        self.assertEqual(m.compact(" 票 價 ： "), "票價")

    def test_29_accepted_zero(self):
        x = m.inspect_local_siblings(doc(pair("票價", "100")))
        self.assertEqual(x["acceptedFields"], 0)
        self.assertFalse(x["roles"]["PRICE"]["accepted"])

    def test_30_offline_no_get(self):
        x = m.offline_contract_report()
        self.assertEqual(x["httpRequests"], 0)
        self.assertFalse(x["published"])
        self.assertEqual(x["goldenAccepted"], 0)

    def test_31_no_live_mode(self):
        self.assertFalse(hasattr(m, "fetch_once"))

    def test_32_aria_hidden(self):
        x = m.inspect_local_siblings(doc("<div aria-hidden='true'><span>票價</span><span>100</span></div>"))
        self.assertEqual(x["roles"]["PRICE"]["localPairCount"], 0)


if __name__ == "__main__":
    unittest.main()
