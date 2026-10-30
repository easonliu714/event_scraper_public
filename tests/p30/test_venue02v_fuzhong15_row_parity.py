#!/usr/bin/env python3
"""P30-VENUE-02V Fuzhong15 film/screening role and row-local date parity tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02v_fuzhong15_row_parity import index_rows, year_hint, detail_screening_dates, inspect_pair

URL = "/xcmovie/cont?sid=0Q231405699420480958&xsmsid=0M361641875264878260"
TITLE = "最後的棋局"
def index(date="10/14(三)", time="18:40", marker="售"):
    return ('<h2>2026年10月放映場次表</h2><table><tr><th>日期</th><th>時間</th><th>片名</th><th>片長</th><th>級別</th></tr>'
            '<tr><td>' + date + '</td><td>' + time + '</td><td><a href="' + URL + '">' + TITLE +
            '</a> ' + marker + '</td><td>124 min</td><td>輔12級</td></tr></table>')
def detail(dates="2026/09/25 14:00 2026/10/14 18:40", title=TITLE):
    return '<h3>' + title + '</h3><section><strong>放映日期：</strong><div>' + dates + '</div></section><p>更新日期：2026-08-25</p>'

class Cases(unittest.TestCase):
    def test_year(self):
        self.assertEqual(year_hint(index()), ("2026", "10"))
    def test_year_conflict(self):
        self.assertIsNone(year_hint(index() + "<h2>2027年11月放映場次表</h2>"))
    def test_row(self):
        rows = index_rows(index())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["time"], "18:40")
    def test_row_marker_not_ticket_id(self):
        self.assertEqual(index_rows(index())[0]["admissionMarker"], "售")
    def test_row_invalid_time(self):
        self.assertEqual(index_rows(index(time="26:99")), [])
    def test_row_invalid_date(self):
        self.assertEqual(index_rows(index(date="不明日期")), [])
    def test_row_external(self):
        self.assertEqual(index_rows(index().replace(URL, "https://evil.example" + URL)), [])
    def test_local_dates(self):
        dates, count = detail_screening_dates(detail())
        self.assertEqual(count, 1)
        self.assertEqual(len(dates), 2)
    def test_update_date_excluded(self):
        dates, _ = detail_screening_dates(detail("2026/10/14 18:40"))
        self.assertEqual(dates, ["2026/10/14 18:40"])
    def test_review_multi(self):
        html = index()
        row = index_rows(html)[0]
        value = inspect_pair(html, detail(), row)
        self.assertEqual(value["decision"], "REVIEW_FILM_MULTI_SCREENING_DATES_NO_FIELDS")
        self.assertEqual(value["matchingRowDateTimeCount"], 1)
        self.assertEqual(value["acceptedFields"], 0)
    def test_review_single(self):
        html = index()
        value = inspect_pair(html, detail("2026/10/14 18:40"), index_rows(html)[0])
        self.assertEqual(value["decision"], "REVIEW_EXACT_ROW_DETAIL_SCREENING_NO_FIELDS")
    def test_mismatch_time(self):
        html = index()
        value = inspect_pair(html, detail("2026/10/14 19:40"), index_rows(html)[0])
        self.assertEqual(value["decision"], "HOLD_TITLE_OR_ROW_DETAIL_DATETIME_PARITY")
    def test_mismatch_title(self):
        html = index()
        value = inspect_pair(html, detail(title="不同影片"), index_rows(html)[0])
        self.assertEqual(value["decision"], "HOLD_TITLE_OR_ROW_DETAIL_DATETIME_PARITY")
    def test_ambiguous_label(self):
        html = index()
        value = inspect_pair(html, detail() + "<p>放映日期：</p>", index_rows(html)[0])
        self.assertEqual(value["decision"], "HOLD_TITLE_OR_ROW_DETAIL_DATETIME_PARITY")
    def test_duplicate_showing(self):
        html = index()
        value = inspect_pair(html, detail("2026/10/14 18:40 2026/10/14 18:40"), index_rows(html)[0])
        self.assertEqual(value["decision"], "HOLD_TITLE_OR_ROW_DETAIL_DATETIME_PARITY")
    def test_no_year(self):
        html = index().replace("2026年10月放映場次表", "放映場次表")
        self.assertEqual(inspect_pair(html, detail(), index_rows(html)[0])["decision"], "HOLD_INDEX_YEAR_MONTH_SCOPE_AMBIGUOUS")

if __name__ == "__main__":
    unittest.main()
