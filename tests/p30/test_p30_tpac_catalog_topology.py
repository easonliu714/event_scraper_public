"""Source-grounded topology tests; synthetic inventory is not native HTTP."""
import hashlib
import unittest
from datetime import datetime, timezone

from scripts.p30_tpac_catalog_topology import (
    CATALOGS, discover_catalog, safe_union,
)

NOW = datetime(2026, 11, 8, 14, 0, tzinfo=timezone.utc)


def receipt(kind, content, status=200, robots=True):
    return {"http_status": status,
            "final_url": CATALOGS[kind]["list_url"],
            "robots_allowed": robots,
            "body_sha256": hashlib.sha256(content).hexdigest(),
            "body_bytes": len(content),
            "observed_at": "2026-11-08T13:56:00Z"}


def listing(kind, ident="1301", title="《晚風》展覽", hidden=False):
    start = "<template>" if hidden else "<main>"
    end = "</template>" if hidden else "</main>"
    date = (
        '<div class="card-event__text-datecate">'
        '<p>2025-07-23 - 2026-12-30</p><p>展覽</p></div>'
        if kind == "event" else
        '<span class="card-program__text-date">2025-07-23 - 2026-12-30</span>'
    )
    link_title = "連結到" + title if kind == "event" else title
    return (start
        + '<a class="card-' + kind + '" title="' + link_title
        + '" href="/' + kind + '/' + ident + '">'
        + '<span class="card-' + kind + '__text-title">' + title + '</span>'
        + date + "</a>" + end).encode()


class TPACCatalogTopologyTests(unittest.TestCase):
    def test_program_and_event_are_two_official_list_namespaces(self):
        self.assertEqual(CATALOGS["program"]["list_url"],
                         "https://tpac.org.taipei/program")
        self.assertEqual(CATALOGS["event"]["list_url"],
                         "https://tpac.org.taipei/event")
        self.assertNotEqual(CATALOGS["program"]["identity_prefix"],
                            CATALOGS["event"]["identity_prefix"])
        self.assertRaisesRegex(ValueError, "KIND_HOLD",
                               discover_catalog, "unsupported", b"x", {}, NOW)

    def test_event_exhibition_range_is_not_showtime(self):
        raw = listing("event")
        records = discover_catalog("event", raw, receipt("event", raw), NOW)
        event = records["1301"]
        self.assertEqual(event["identity"], "tpac:event:1301")
        self.assertEqual(event["detail_url"], "https://tpac.org.taipei/event/1301")
        self.assertEqual(event["list_date_label"], "2025-07-23 - 2026-12-30")
        self.assertEqual(event["list_event_category"], "展覽")
        self.assertEqual(event["list_date_role"],
                         "ACTIVITY_LIST_PERIOD_NOT_SHOW_START")
        self.assertTrue(event["list_title_owned"])
        self.assertIsNone(event["accepted_show_start"])
        self.assertIsNone(event["accepted_exhibition_hours"])
        self.assertIsNone(event["accepted_sale_start"])
        self.assertEqual(event["decision"], "REVIEW_DETAIL_ID_AND_FIELDS_REQUIRED")

    def test_same_numeric_id_never_implies_cross_catalog_same_event(self):
        rawp = listing("program", "1301", "音樂劇 A")
        rawe = listing("event", "1301", "展覽 B")
        p = discover_catalog("program", rawp, receipt("program", rawp), NOW)
        e = discover_catalog("event", rawe, receipt("event", rawe), NOW)
        joined = safe_union(p, e)
        self.assertEqual(len(joined), 2)
        self.assertEqual(set(joined), {"tpac:program:1301", "tpac:event:1301"})
        self.assertEqual(joined["tpac:program:1301"]["list_date_role"],
                         "PERFORMANCE_LIST_PERIOD_NOT_SHOW_START")

    def test_cross_host_spoof_and_query_or_session_links_are_rejected(self):
        safe = listing("event")
        for href in ("https://fake.example.org/event/1301",
                     "/event/1301?session=45", "/event/1301#ticket",
                     "/program/1301", "https://tpac.org.taipei.evil.org/event/1301"):
            raw = safe.replace(b"/event/1301", href.encode())
            with self.subTest(href=href):
                with self.assertRaisesRegex(ValueError, "NO_VALID_EVENT_LINK_HOLD"):
                    discover_catalog("event", raw, receipt("event", raw), NOW)

    def test_duplicate_ids_and_conflicting_title_hold(self):
        raw = listing("event")
        double = raw.replace(b"</main>", raw[6:-7] + b"</main>")
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ID_HOLD"):
            discover_catalog("event", double, receipt("event", double), NOW)
        wrong = raw.replace(b'card-event__text-title', b'card-event__text-title')
        wrong = wrong.replace("《晚風》展覽</span>".encode(), b"Different Event</span>")
        with self.assertRaisesRegex(ValueError, "TITLE_CONFLICT_HOLD"):
            discover_catalog("event", wrong, receipt("event", wrong), NOW)

    def test_hidden_and_robots_denied_and_source_drift_hold(self):
        raw = listing("event", hidden=True)
        with self.assertRaisesRegex(ValueError, r"(NO_VALID_EVENT_LINK|LINK_CAP)_HOLD"):
            discover_catalog("event", raw, receipt("event", raw), NOW)
        raw = listing("event")
        denied = receipt("event", raw, robots=False)
        with self.assertRaisesRegex(ValueError, "RECEIPT_STATUS_URL_ROBOTS_SHA_HOLD"):
            discover_catalog("event", raw, denied, NOW)
        drift = receipt("event", raw)
        drift["body_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "RECEIPT_STATUS_URL_ROBOTS_SHA_HOLD"):
            discover_catalog("event", raw, drift, NOW)

    def test_safe_union_never_accepts_mismatched_identity(self):
        raw = listing("event")
        entries = discover_catalog("event", raw, receipt("event", raw), NOW)
        entries["1301"]["identity"] = "tpac:program:1301"
        with self.assertRaisesRegex(ValueError, "UNION_IDENTITY_HOLD"):
            safe_union({}, entries)


if __name__ == "__main__":
    unittest.main()
