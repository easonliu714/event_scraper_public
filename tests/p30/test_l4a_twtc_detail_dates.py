"""P30-L4-A: offline 39-row candidate replay and detail-date fail-closed tests."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPT))
spec = importlib.util.spec_from_file_location("p30_l4a_twtc_detail_dates",
                                              SCRIPT / "p30_l4a_twtc_detail_dates.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

TITLE = "2026年電器空調影音大展"
URL = "https://twtc.com.tw/exhibition_more.aspx?id=29418&p=home"
HTML = """<html><h2>2026年電器空調影音大展</h2><p>展覽館別：世貿一館</p>
<p>展出日期：2026/11/06 ~ 2026/11/09</p><p>展出時間：10:00 ~ 18:00</p></html>""".encode("utf-8")


def row(n=29418):
    return {"platform": "台北世貿", "title": TITLE if n == 29418 else f"模擬活動 {n}",
            "official_url": "https://twtc.com.tw/exhibition_more.aspx?id=" + str(n) + "&p=home",
            "detail_url": "https://twtc.com.tw/exhibition_more.aspx?id=" + str(n) + "&p=home",
            "event_period_raw": "11/06 ~ 11/09",
            "date": None, "source_level": "LIST_TABLE_ONLY",
            "ticket_availability": "UNKNOWN", "golden_verified": False,
            "provenance_id": "synthetic-" + str(n)}


def frozen_rows():
    return [row(29418 + i) for i in range(p.EXPECTED_COUNT)]


def frozen_diagnostics():
    return {"kind": p.INPUT_KIND, "unique_candidates": p.EXPECTED_COUNT,
            "writer_executed": False, "notification_executed": False,
            "app_data_published": False, "golden_accepted": False,
            "auto_hidden": 0, "source_runtime": "DORMANT"}


class Resp:
    def __init__(self, code=200, data=HTML, ct="text/html"):
        self.status_code = code
        self.headers = {"content-type": ct}
        self.data = data
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def iter_content(self, chunk_size=32768):
        yield self.data


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.urls = []
    def get(self, url, **kwargs):
        self.urls.append(url)
        assert kwargs["allow_redirects"] is False and kwargs["stream"] is True
        return next(self.responses)


class DetailDates(unittest.TestCase):
    def test_actual_official_date_evidence(self):
        data = p.extract_verified_date(HTML, row(), URL)
        self.assertEqual(data["state"], "DATE_VERIFIED_BY_OFFICIAL_DETAIL_CANDIDATE")
        self.assertEqual(data["start"], "2026-11-06")
        self.assertEqual(data["end"], "2026-11-09")
        self.assertEqual(data["event_id"], "29418")

    def test_2026_cat_fair_crosscheck(self):
        x = row(29419)
        x["title"] = "2026展昭世界貓咪博覽會"
        x["event_period_raw"] = "10/08 ~ 10/11"
        content = "<h2>2026展昭世界貓咪博覽會</h2><div>展出日期：2026/10/08 ~ 2026/10/11</div>"
        data = p.extract_verified_date(content, x, x["detail_url"])
        self.assertEqual(data["start"], "2026-10-08")
        self.assertEqual(data["end"], "2026-10-11")

    def test_cross_year_detail_is_accepted_only_when_raw_month_day_matches(self):
        x = row()
        x["event_period_raw"] = "12/30 ~ 01/02"
        content = "<h2>2026年電器空調影音大展</h2>展出日期：2026/12/30 ~ 2027/01/02"
        self.assertEqual(p.extract_verified_date(content, x, URL)["start"], "2026-12-30")

    def test_missing_title_heading_is_not_date_verified(self):
        content = "<h2>別的活動</h2><div>"+TITLE+"</div>展出日期：2026/11/06 ~ 2026/11/09"
        self.assertEqual(p.extract_verified_date(content, row(), URL)["state"],
                         "DETAIL_HEADING_MISMATCH")

    def test_multiple_dates_or_bad_year_is_hold(self):
        content = "<h2>"+TITLE+"</h2>展出日期：2026/11/06 ~ 2026/11/09 " \
                  "展出日期：2027/11/06 ~ 2027/11/09"
        self.assertEqual(p.extract_verified_date(content, row(), URL)["state"],
                         "DATE_ABSENT_OR_AMBIGUOUS")
        content = "<h2>"+TITLE+"</h2>展出日期：2026/13/06 ~ 2026/13/09"
        self.assertEqual(p.extract_verified_date(content, row(), URL)["state"],
                         "INVALID_DATE")

    def test_conflicting_raw_period_is_hold_not_guess(self):
        r = row()
        r["event_period_raw"] = "10/08 ~ 10/11"
        self.assertEqual(p.extract_verified_date(HTML, r, URL)["state"],
                         "LIST_DETAIL_PERIOD_CONFLICT")
        r["event_period_raw"] = "延期未定"
        self.assertEqual(p.extract_verified_date(HTML, r, URL)["state"],
                         "LIST_DETAIL_PERIOD_CONFLICT")

    def test_redirect_identity_changed_is_hold(self):
        other = "https://twtc.com.tw/exhibition_more.aspx?id=29419&p=home"
        self.assertEqual(p.extract_verified_date(HTML, row(), other)["state"],
                         "REDIRECT_EVENT_ID_MISMATCH")

    def test_frozen_input_lineage(self):
        p.validate_input(frozen_rows(), frozen_diagnostics())
        for key in ("golden_accepted", "app_data_published",
                    "writer_executed", "notification_executed"):
            report = frozen_diagnostics()
            report[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "UNSAFE_SOURCE"):
                p.validate_input(frozen_rows(), report)

    def test_frozen_input_count_and_origin(self):
        with self.assertRaisesRegex(ValueError, "FROZEN_SOURCE_COUNT"):
            p.validate_input(frozen_rows()[:10], frozen_diagnostics())
        rows = frozen_rows()
        rows[0]["official_url"] = "https://evil.com/exhibition_more.aspx?id=29418"
        with self.assertRaisesRegex(ValueError, "DETAIL_URL"):
            p.validate_input(rows, frozen_diagnostics())

    def test_no_detail_link_never_fetched(self):
        x = row()
        x["detail_url"] = None
        x["official_url"] = p.l3.LISTING
        session = Session([])
        evidence, stat = p.run(session, [x], sleeper=lambda _: None)
        self.assertEqual(stat["requests_attempted"], 0)
        self.assertEqual(evidence[0]["state"], "NO_OFFICIAL_DETAIL_URL")

    def test_one_request_per_id_and_no_retry_403(self):
        x = row()
        sess = Session([Resp(403)])
        data, stat = p.run(sess, [x], sleeper=lambda _: None)
        self.assertEqual(stat["requests_attempted"], 1)
        self.assertEqual(len(sess.urls), 1)
        self.assertEqual(data[0]["state"], "HTTP_DETAIL_HOLD")
        self.assertEqual(stat["date_verified"], 0)

    def test_bounded_2_samples_and_detail_success(self):
        first = row()
        second = row(29419)
        second["detail_url"] = None
        second["official_url"] = p.l3.LISTING
        sess = Session([Resp()])
        events, stat = p.run(sess, [first, second], sleeper=lambda _: None)
        self.assertEqual(len(sess.urls), 1)
        self.assertEqual(stat["date_verified"], 1)
        self.assertEqual(stat["remaining_unverified"], 1)
        self.assertEqual(events[0]["source_time_role"], "OFFICIAL_EXHIBITION_DATE")

    def test_budget_negative(self):
        with self.assertRaisesRegex(ValueError, "REQUEST_BUDGET"):
            p.run(Session([]), [], delay=0)


if __name__ == "__main__":
    unittest.main()
