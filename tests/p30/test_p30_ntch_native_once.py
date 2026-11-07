"""Fail-closed NTCH native source identity and policy tests; all HTTP mocked."""
import unittest
from unittest.mock import patch
from scripts import p30_ntch_native_once as m

URL = "https://npac-ntch.org/programs/panai-2026"
LIST = '<article><a href="/programs/panai-2026">' + m.TITLE + '</a></article>'
DETAIL = '<article><h1>' + m.TITLE + '</h1></article>'
ROBOTS = b"User-agent: *\nAllow: /programs\n"


class NTCHGateTests(unittest.TestCase):
    def test_exact_same_source_local_identity_review(self):
        result = m.inspect_pair(LIST, DETAIL, URL)
        self.assertEqual(result["same_id_review"], 1)
        self.assertIn("REVIEW", result["decision"])

    def test_cross_event_and_js_only_rejected(self):
        for bad in ('<script><a href="/programs/panai-2026">' + m.TITLE + '</a></script>',
                    '<a href="https://www.opentix.life/event/2070446724700692480">' + m.TITLE + '</a>',
                    '<a href="/programs/another-2026">' + m.TITLE + '</a><a href="/programs/panai-2026">' + m.TITLE + '</a>'):
            self.assertNotEqual(m.unique_list_detail(bad), URL)
        self.assertEqual(m.inspect_pair(LIST, "<div>" + m.TITLE + "</div>", URL)["same_id_review"], 0)

    def test_robots_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "PATH_DENIED"):
            m.explicit_robots_allow(b"User-agent: *\nDisallow: /programs\n", (m.LIST_URL,))
        with self.assertRaisesRegex(ValueError, "NO_APPLICABLE"):
            m.explicit_robots_allow(b"User-agent: OtherBot\nAllow: /\n", (m.LIST_URL,))

    @patch.object(m, "read_public")
    def test_one_shot_in_memory_receipts_no_publish(self, read):
        def response(url, mime, cap):
            bodies = {m.ROBOTS_URL: ROBOTS, m.LIST_URL: LIST.encode(),
                      URL: DETAIL.encode()}
            body = bodies[url]
            return body, {"url": url, "http_status": 200,
                          "body_sha256": "0" * 64, "observed_at_utc": "2026-11-07T17:55:00+00:00"}
        read.side_effect = response
        out = m.run_native_once()
        self.assertEqual((out["native_list"], out["native_detail"],
                          out["native_same_id_review"]), (1, 1, 1))
        self.assertEqual(out["source_event_id"], "panai-2026")
        self.assertEqual((out["native_body_lkg"], out["formal_accepted_fields"],
                          out["golden"], out["published"]), (0, 0, 0, 0))
        self.assertEqual(read.call_count, 3)

    @patch.object(m, "read_public")
    def test_js_only_stops_before_detail(self, read):
        read.side_effect = [(ROBOTS, {}), (b"<html><script>render()</script></html>", {})]
        out = m.run_native_once()
        self.assertEqual(out["native_event_get_attempted"], 1)
        self.assertEqual(out["native_detail"], 0)
        self.assertIn("LIST_EVENT_LOCAL_ID_HOLD", out["first_failure"])
        self.assertEqual(read.call_count, 2)


if __name__ == "__main__":
    unittest.main()
