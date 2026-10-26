"""P30-L7-A immutable source bridge, forbidden-write and mobile UI static tests."""
import importlib.util
import unittest
from pathlib import Path

S = Path(__file__).resolve().parents[2] / "scripts"
spec = importlib.util.spec_from_file_location("p30_l7a_build", S / "p30_l7a_build_candidate.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(platform, idx):
    if platform == "中正紀念堂":
        return {"platform": platform, "title": "文化活動候選 " + str(idx),
                "official_url": "https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId=" + str(idx + 50000),
                "source_list_url": "https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr",
                "source_level": "LIST_ONLY", "date": None, "location": None,
                "ticket_availability": "UNKNOWN", "golden_verified": False}
    result = {"platform": platform, "title": "展覽候選 " + str(idx),
              "official_url": "https://twtc.com.tw/exhibition_more.aspx?id=" + str(idx + 40000) + "&p=home",
              "source_list_url": "https://twtc.com.tw/exhibition?p=home",
              "source_level": "LIST_TABLE_ONLY", "source_time_role": "EXHIBITION_PERIOD_RAW_UNNORMALIZED",
              "event_period_raw": "11/01 ~ 11/03",
              "date": None, "location": "世貿一館", "ticket_availability": "UNKNOWN",
              "golden_verified": False}
    if idx == 1:
        result.update({"source_level": "DETAIL_DATE_CANDIDATE",
                       "source_time_role": "OFFICIAL_EXHIBITION_DATE",
                       "event_date_start": "2026-11-01", "event_date_end": "2026-11-03"})
    return result


def diag(kind, count, key):
    return {"kind": kind, key: count, "writer_executed": False,
            "notification_executed": False, "app_data_published": False,
            "golden_accepted": False, "source_runtime": "DORMANT", "auto_hidden": 0}


def fixtures():
    return ([row("中正紀念堂", x) for x in range(5)],
            diag(m.KIND_CKSMH, 5, "unique_list_candidates"),
            [row("台北世貿", x) for x in range(39)],
            diag(m.KIND_TWTC, 39, "unique_candidates"))


class Tests(unittest.TestCase):
    def test_exact_two_sources_and_no_golden(self):
        out = m.build(*fixtures())
        self.assertEqual(out["count"], 44)
        self.assertEqual(len(out["sources"]), 2)
        self.assertEqual(len({i["id"] for i in out["items"]}), 44)
        self.assertFalse(out["published"])
        self.assertFalse(out["goldenAccepted"])
        self.assertFalse(out["fullPlatformCoverageProven"])
        self.assertTrue(all(e["ticketStatus"] == "UNKNOWN" for e in out["items"]))

    def test_only_bound_twtc_detail_dates(self):
        out = m.build(*fixtures())
        date_rows = [x for x in out["items"] if x["dateStart"]]
        self.assertEqual(len(date_rows), 1)
        self.assertEqual(date_rows[0]["dateStart"], "2026-11-01")
        self.assertEqual(date_rows[0]["timeRole"], "OFFICIAL_EXHIBITION_DATE")

    def test_no_guess_on_raw_period_or_ceased_source(self):
        out = m.build(*fixtures())
        self.assertTrue(all(x["validity"] == "UNCERTAIN" for x in out["items"]))
        self.assertEqual(sum(x["dateStart"] is None for x in out["items"]), 43)

    def test_forbid_false_golden_writers_and_wrong_counts(self):
        for field in ("golden_accepted", "app_data_published",
                      "writer_executed", "notification_executed"):
            fixture = list(fixtures())
            fixture[1][field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "UNSAFE_"):
                m.build(*fixture)
        fixture = list(fixtures())
        fixture[3]["unique_candidates"] = 40
        with self.assertRaisesRegex(ValueError, "SOURCE_COUNT_DRIFT"):
            m.build(*fixture)

    def test_domain_and_credential_rejection(self):
        for bad in ("http://event.culture.tw/mocweb/reg/CKSMH/",
                    "https://event.culture.tw.evil.com/mocweb/reg/CKSMH",
                    "https://event.culture.tw@evil.com/x",
                    "https://twtc.com.tw:8080/exhibition",
                    "file:///tmp/test"):
            self.assertFalse(m.is_official(bad, "event.culture.tw"))
        fixture = list(fixtures())
        fixture[0][0]["official_url"] = "https://evil.com/example"
        with self.assertRaisesRegex(ValueError, "UNBOUND_ORIGIN"):
            m.build(*fixture)

    def test_missing_or_unbound_date_fails_closed(self):
        fixture = list(fixtures())
        fixture[2][1]["source_time_role"] = "SALE_WINDOW"
        with self.assertRaisesRegex(ValueError, "UNBOUND_DATE_ROLE"):
            m.build(*fixture)
        fixture = list(fixtures())
        fixture[2][1]["event_date_end"] = "2026-10-01"
        with self.assertRaisesRegex(ValueError, "INVALID_DETAIL_DATE"):
            m.build(*fixture)

    def test_candidate_title_and_ticket_status_validation(self):
        fixture = list(fixtures())
        fixture[0][0]["ticket_availability"] = "AVAILABLE"
        with self.assertRaisesRegex(ValueError, "FALSE_GOLDEN_OR_TICKET"):
            m.build(*fixture)
        fixture = list(fixtures())
        fixture[0][0]["title"] = ""
        with self.assertRaisesRegex(ValueError, "INVALID_TITLE"):
            m.build(*fixture)

    def test_mobile_preview_has_no_remote_code_or_html_injection(self):
        html = (S / "p30_l7a_smoke_index.html").read_text(encoding="utf-8")
        self.assertIn('<meta name="viewport"', html)
        self.assertIn('fetch("./data.json"', html)
        self.assertIn('textContent=', html)
        self.assertIn("rel=\"noopener noreferrer\"", html)
        self.assertIn("HOLD candidate contract", html)
        self.assertNotIn("innerHTML", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("https://cdn.", html)
        self.assertNotIn("navigator.serviceWorker.register", html)


if __name__ == "__main__":
    unittest.main()
