"""Native TPAC robots and same-ID field-conflict safety tests."""
import unittest
from unittest.mock import patch
from scripts import p30_tpac_event2072_native_once as m
from scripts import p30_tpac_event_source as tpac


def receipt(url, mime):
    return {"url": url, "http_status": 200, "content_type": mime,
            "body_bytes": 40, "body_sha256": "a" * 64,
            "observed_at_utc": "2026-11-07T12:55:00+00:00",
            "transport": "NATIVE_NO_REDIRECT_NO_RETRY"}


class NativeTPACTests(unittest.TestCase):
    def test_robots_denied_no_event_get(self):
        with patch.object(m, "read_public", return_value=(
                b"User-agent: *\nDisallow: /event\n",
                receipt(m.ROBOTS_URL, "text/plain"))) as get:
            out = m.run_native_once()
        self.assertEqual(get.call_count, 1)
        self.assertEqual((out["native_list"], out["native_detail"]), (0, 0))
        self.assertIn("TPAC_ROBOTS_EVENT_PATH_DENIED_HOLD", out["first_failure"])

    def test_missing_applicable_group_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "APPLICABLE_GROUP_MISSING"):
            m.explicit_robots_allow(b"User-agent: OtherBot\nAllow: /\n")

    def test_no_exact_list_edge_no_detail_get(self):
        calls = [(b"User-agent: *\nAllow: /\n",
                  receipt(m.ROBOTS_URL, "text/plain")),
                 (b"<article><a href='/event/9999'>Other</a></article>",
                  receipt(tpac.LIST_URL, "text/html"))]
        with patch.object(m, "read_public", side_effect=calls) as get:
            out = m.run_native_once()
        self.assertEqual(get.call_count, 2)
        self.assertEqual((out["native_list"], out["native_detail"]), (1, 0))
        self.assertIn("TPAC_NATIVE_LIST_EXACT_EVENT_LOCAL_EDGE_HOLD",
                      out["first_failure"])

    def test_same_id_preserves_official_date_conflict(self):
        listing = ('<article><a href="/event/2072">' + tpac.TITLE +
                   '</a><p>2026-11-10 - 2026-11-12</p></article>').encode()
        detail = ('<article><h1>' + tpac.TITLE +
                  '</h1><p>2026-11-11 - 2026-11-13</p></article>').encode()
        calls = [(b"User-agent: *\nAllow: /\n",
                  receipt(m.ROBOTS_URL, "text/plain")),
                 (listing, receipt(tpac.LIST_URL, "text/html")),
                 (detail, receipt(tpac.DETAIL_URL, "text/html"))]
        with patch.object(m, "read_public", side_effect=calls) as get:
            out = m.run_native_once()
        self.assertEqual(get.call_count, 3)
        self.assertEqual((out["native_list"], out["native_detail"],
                          out["native_same_id_review"]), (1, 1, 1))
        self.assertTrue(out["date_conflict"])
        self.assertEqual(out["first_failure"],
                         "TPAC_EVENT_OFFICIAL_LIST_DETAIL_DATE_CONFLICT_HOLD")
        self.assertEqual((out["formal_accepted_fields"], out["golden"],
                          out["published"], out["native_body_lkg"]), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
