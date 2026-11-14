"""Distinct official activity roles; entirely synthetic fixtures, not native PASS."""
import hashlib
import unittest
from datetime import datetime, timezone

from scripts.p30_tpac_catalog_topology import discover_catalog
from scripts.p30_tpac_event_detail_review import inspect_event_detail

NOW = datetime(2026, 11, 8, 14, 54, tzinfo=timezone.utc)
ROOT = "https://tpac.org.taipei/event"
OBS = "2026-11-08T14:49:00Z"


def receipt(url, body):
    return {"http_status": 200, "final_url": url, "robots_allowed": True,
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "body_bytes": len(body), "observed_at": OBS}


def card(event_id, title, category, list_period):
    raw = ('<a class="card-event" title="連結到' + title
           + '" href="/event/' + event_id + '">'
           + '<div class="card-event__text-title">' + title + '</div>'
           + '<div class="card-event__text-datecate"><p>' + list_period
           + '</p><p>' + category + '</p></div></a>').encode()
    return discover_catalog("event", raw, receipt(ROOT, raw), NOW)[event_id]


def detail(title, category, period, shows=()):
    content = ''.join('<li><p>' + show + '</p></li>' for show in shows)
    aside = ('<div class="page-event__aside-place-showtimes"><h3>場次</h3>'
             '<ul>' + content + '</ul></div>') if shows else ''
    return ('<main><article class="page-event__article">'
            '<h1>' + title + '</h1><div class="page-event__article-top">'
            '<div class="page-event__article-top-text"><div><span>'
            + category + '</span></div><div>' + period
            + '</div></div></div></article>' + aside + '</main>').encode()


class RealRoleSemanticsTests(unittest.TestCase):
    def test_exhibition_period_cannot_become_event_show_start(self):
        title = "「親．建築」計畫：高德亮《晚風》"
        entry = card("1301", title, "展覽", "2025-07-23 - 2026-12-30")
        data = detail(title, "展覽", "2025-07-24 - 2026-12-31")
        result = inspect_event_detail(entry, data, receipt(entry["detail_url"], data), NOW)
        self.assertEqual(result["decision"], "SOURCE_OWNED_PARTIAL_FIELDS_REQUIRE_INDEPENDENT_ACCEPTANCE")
        self.assertEqual(result["verified_core_roles"]["EXHIBITION_PERIOD"], ["2025-07-24", "2026-12-31"])
        self.assertNotIn("NEXT_EVENT_SHOW_START", result["verified_core_roles"])
        self.assertIn("LIST_DETAIL_ACTIVITY_PERIOD_CONFLICT_HOLD", result["held_fields"])
        self.assertFalse(result["published"])

    def test_guide_event_has_three_exact_future_showtime_roles(self):
        title = "2026北藝夜遊：Beats到天臺"
        entry = card("2072", title, "專題導覽", "2026-11-10 - 2026-11-12")
        data = detail(title, "專題導覽", "2026-11-11 - 2026-11-13",
                      ["2026-11-11 (三) 19:00",
                       "2026-11-12 (四) 19:00",
                       "2026-11-13 (五) 19:00"])
        result = inspect_event_detail(entry, data, receipt(entry["detail_url"], data), NOW)
        self.assertEqual(result["verified_core_roles"]["NEXT_EVENT_SHOW_START"], "2026-11-11T19:00:00+08:00")
        self.assertEqual(result["verified_core_roles"]["EXACT_EVENT_SHOW_COUNT"], 3)
        self.assertNotIn("EXHIBITION_PERIOD", result["verified_core_roles"])
        self.assertIn("LIST_DETAIL_ACTIVITY_PERIOD_CONFLICT_HOLD", result["held_fields"])
        self.assertFalse(result["formal_field_pass"])

    def test_mismatched_title_or_category_holds(self):
        entry = card("2072", "正確活動名稱", "專題導覽", "2026-11-10 - 2026-11-12")
        data = detail("別的活動", "專題導覽", "2026-11-11 - 2026-11-13")
        with self.assertRaisesRegex(ValueError, "DETAIL_TITLE_IDENTITY_HOLD"):
            inspect_event_detail(entry, data, receipt(entry["detail_url"], data), NOW)
        data = detail("正確活動名稱", "展覽", "2026-11-11 - 2026-11-13")
        with self.assertRaisesRegex(ValueError, "CATEGORY_PARITY_HOLD"):
            inspect_event_detail(entry, data, receipt(entry["detail_url"], data), NOW)

    def test_sale_label_not_accepted_as_show_start(self):
        entry = card("2072", "活動名稱 ABC", "專題導覽", "2026-11-10 - 2026-11-12")
        data = detail("活動名稱 ABC", "專題導覽", "2026-11-11 - 2026-11-13",
                      ["2026-11-11 開賣 19:00"])
        with self.assertRaisesRegex(ValueError, "SHOW_ROLE_HOLD"):
            inspect_event_detail(entry, data, receipt(entry["detail_url"], data), NOW)

    def test_native_receipt_hash_drift_fail_closed(self):
        entry = card("1301", "展覽 ABC", "展覽", "2025-07-23 - 2026-12-30")
        data = detail("展覽 ABC", "展覽", "2025-07-24 - 2026-12-31")
        evidence = receipt(entry["detail_url"], data)
        evidence["body_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "RECEIPT_STATUS_URL_ROBOTS_SHA_HOLD"):
            inspect_event_detail(entry, data, evidence, NOW)


if __name__ == "__main__":
    unittest.main()
