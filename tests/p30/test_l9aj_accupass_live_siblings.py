"""P30-L9-AJ synthetic-only regression tests: no HTTP or event publication."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_l9aj_accupass_live_siblings as m
import p30_l9ah_accupass_field_roles as ah
import p30_l9ai_accupass_sibling_roles as ai


def item(identity="REVIEW_SAME_EVENT_PATH_TITLE", value="100", assessed=True):
    return {"http": 200, "identityDecision": identity,
            "fieldTopology": {"assessed": assessed, "hold": None,
                "roles": {"PRICE": {"localPairCount": 1, "distinctValueCount": 1,
                                     "decision": "REVIEW_ONE_LOCAL_SIBLING_NOT_ACCEPTED",
                                     "accepted": False, "raw": value}}}}


def source(*items):
    return {"listHttp": 200, "listDecision": "REVIEW_SOURCE_BOUND_CANDIDATES",
            "details": list(items)}


class LiveSiblingContract(unittest.TestCase):
    def test_01_hold(self):
        self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")

    def test_02_parent_pin(self):
        self.assertEqual(len(m.PARENT), 40)

    def test_03_eight_roles(self):
        self.assertEqual(len(ai.ROLE_LABELS), 8)

    def test_04_two_details_review_only(self):
        r = m.summarize(source(item(), item()))
        self.assertEqual(r["decision"], "REVIEW_LOCAL_SIBLING_ROLE_EVIDENCE_NOT_ACCEPTED")

    def test_05_zero_accept(self):
        self.assertFalse(m.summarize(source(item(), item()))["details"][0]["roles"]["PRICE"]["accepted"])

    def test_06_raw_values_removed(self):
        self.assertNotIn("SENSITIVE_VALUE", str(m.summarize(source(item(value="SENSITIVE_VALUE"), item()))))

    def test_07_identity_hold(self):
        self.assertEqual(m.summarize(source(item(identity="HOLD_TITLE_MISMATCH"), item()))["decision"],
                         "HOLD_DETAIL_IDENTITY_OR_COUNT")

    def test_08_missing_detail_hold(self):
        self.assertEqual(m.summarize(source(item()))["decision"], "HOLD_DETAIL_IDENTITY_OR_COUNT")

    def test_09_extra_detail_hold(self):
        self.assertEqual(m.summarize(source(item(), item(), item()))["decision"], "HOLD_DETAIL_SCOPE")

    def test_10_unassessed_hold(self):
        self.assertEqual(m.summarize(source(item(assessed=False), item()))["decision"],
                         "HOLD_LOCAL_TOPOLOGY_UNASSESSED")

    def test_11_no_local_evidence_hold(self):
        r = source(item(), item())
        for d in r["details"]:
            d["fieldTopology"]["roles"] = {}
        self.assertEqual(m.summarize(r)["decision"], "HOLD_NO_LOCAL_SIBLING_EVIDENCE")

    def test_12_conflict_not_accepted(self):
        r = source(item(), item())
        r["details"][0]["fieldTopology"]["roles"]["PRICE"].update(
            localPairCount=2, distinctValueCount=2, decision="HOLD_CONFLICTING_LOCAL_VALUES")
        self.assertFalse(m.summarize(r)["details"][0]["roles"]["PRICE"]["accepted"])

    def test_13_bad_count_hold(self):
        r = source(item(), item())
        r["details"][0]["fieldTopology"]["roles"]["PRICE"]["localPairCount"] = -1
        self.assertEqual(m.summarize(r)["details"][0]["roles"]["PRICE"]["decision"], "HOLD_INVALID_ROLE_METRIC")

    def test_14_invalid_decision_hold(self):
        r = source(item(), item())
        r["details"][0]["fieldTopology"]["roles"]["PRICE"]["decision"] = "ACCEPTED"
        self.assertEqual(m.summarize(r)["details"][0]["roles"]["PRICE"]["decision"], "HOLD_INVALID_ROLE_METRIC")

    def test_15_no_http_offline(self):
        self.assertEqual(m.offline_contract()["httpRequests"], 0)

    def test_16_no_golden(self):
        self.assertEqual(m.offline_contract()["goldenAccepted"], 0)

    def test_17_no_publication(self):
        self.assertFalse(m.offline_contract()["published"])

    def test_18_no_raw_html(self):
        self.assertFalse(m.offline_contract()["rawHtmlPersisted"])

    def test_19_no_raw_ids(self):
        self.assertFalse(m.offline_contract()["rawEventIdsPersisted"])

    def test_20_no_raw_query(self):
        self.assertFalse(m.offline_contract()["queryValuesPersisted"])

    def test_21_patch_scoped(self):
        before = ah.scoped_pairs
        with patch.object(ah, "probe", return_value=source(item(), item())):
            result = m.probe()
        self.assertIs(ah.scoped_pairs, before)
        self.assertEqual(result["detailCount"], 2)

    def test_22_local_sibling_synthetic(self):
        h = "<main><div><span>票價</span><span>100</span></div></main>"
        self.assertEqual(ai.inspect_local_siblings(h)["roles"]["PRICE"]["localPairCount"], 1)

    def test_23_no_global_date_regex(self):
        h = "<main><p>活動日期 2099/01/01</p></main>"
        self.assertEqual(ai.inspect_local_siblings(h)["roles"]["EVENT"]["localPairCount"], 0)

    def test_24_announcement_not_event(self):
        h = "<main><div><span>公告時間</span><span>2099/01/01</span></div></main>"
        self.assertEqual(ai.inspect_local_siblings(h)["roles"]["EVENT"]["localPairCount"], 0)


if __name__ == "__main__":
    unittest.main()
