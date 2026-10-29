"""P30-L9-AP list cause classification and no-extra-GET contract."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_l9ap_accupass_list_cause as m

class Contract(unittest.TestCase):
    def test_01_timeout(self):
        self.assertEqual(m.classify("HOLD_LIST_TimeoutError"), "HOLD_NAVIGATION_TIMEOUT")
    def test_02_http_url(self):
        self.assertEqual(m.classify("HOLD_LIST_HTTP_OR_URL"), "HOLD_HTTP_OR_FINAL_URL")
    def test_03_static_dom_scope(self):
        self.assertEqual(m.classify("HOLD_LIST_STABILITY_OR_SCOPE"), "HOLD_STATIC_DOM_PARITY_OR_SCOPE")
    def test_04_exception_no_message_leak(self):
        self.assertEqual(m.classify("HOLD_LIST_NetworkError"), "HOLD_NAVIGATION_EXCEPTION_CLASS")
    def test_05_unknown_sanitized(self):
        self.assertEqual(m.classify("HOLD_LIST_token=SECRET"), "HOLD_UNCLASSIFIED_LIST_CAUSE")
    def test_06_ready_not_golden(self):
        self.assertEqual(m.classify("REVIEW_SOURCE_BOUND_CANDIDATES"), "REVIEW_LIST_CANDIDATES")
    def test_07_single_probe_no_extra_navigation(self):
        source = {"listHttp": None, "listDecision": "HOLD_LIST_TimeoutError",
                  "details": [], "decision": "HOLD_LIST_OR_DETAIL_SAMPLE"}
        with patch.object(m.prior.prior.ah, "probe", return_value=source) as call:
            result = m.probe()
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result["listCause"], "HOLD_NAVIGATION_TIMEOUT")
        self.assertEqual(result["detailCount"], 0)
        self.assertIsNone(result["listHttp"])
        self.assertEqual(result["acceptedFields"], 0)
        self.assertFalse(result["published"])
    def test_08_release(self):
        self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")

if __name__ == "__main__":
    unittest.main()
