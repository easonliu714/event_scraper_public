"""VENUE-01C synthetic date-role conflict refusal tests; no HTTP or production writes."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_venue01c_date_conflict as m


def inspect(title="虛構節目 2027/1/16-17", body="活動日期/時間：2027/1/16-17"):
    return m.inspect_date_role(title, body)


class DateRoleTests(unittest.TestCase):
    def test_01_release(self): self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_02_parent(self): self.assertEqual(len(m.PARENT), 40)
    def test_03_parity_review(self): self.assertEqual(inspect()["decision"], "REVIEW_TITLE_BODY_ACTIVITY_DATE_PARITY_NOT_ACCEPTED")
    def test_04_conflict(self): self.assertEqual(inspect(body="活動日期/時間：2027/1/26-27")["decision"], "HOLD_TITLE_BODY_ACTIVITY_DATE_CONFLICT")
    def test_05_conflict_flag(self): self.assertFalse(inspect(body="活動日期/時間：2027/1/26-27")["titleBodyDateParity"])
    def test_06_parity_flag(self): self.assertTrue(inspect()["titleBodyDateParity"])
    def test_07_announcement_not_event(self):
        self.assertEqual(inspect(body="日期時間：2027/1/16-17")["decision"], "HOLD_EXPLICIT_ACTIVITY_LABEL_MISSING_OR_AMBIGUOUS")
    def test_08_sale_not_event(self):
        self.assertEqual(inspect(body="售票時間：2027/1/16-17")["decision"], "HOLD_EXPLICIT_ACTIVITY_LABEL_MISSING_OR_AMBIGUOUS")
    def test_09_registration_not_event(self):
        self.assertEqual(inspect(body="報名時間：2027/1/16-17")["decision"], "HOLD_EXPLICIT_ACTIVITY_LABEL_MISSING_OR_AMBIGUOUS")
    def test_10_missing_title_date(self):
        self.assertEqual(inspect(title="虛構節目")["decision"], "HOLD_TITLE_DATE_MISSING_OR_AMBIGUOUS")
    def test_11_multiple_title_dates(self):
        self.assertEqual(inspect(title="2027/1/16 2027/1/17")["decision"], "HOLD_TITLE_DATE_MISSING_OR_AMBIGUOUS")
    def test_12_multiple_activity_labels(self):
        self.assertEqual(inspect(body="活動日期：2027/1/16-17\n演出日期：2027/1/16-17")["decision"], "HOLD_EXPLICIT_ACTIVITY_LABEL_MISSING_OR_AMBIGUOUS")
    def test_13_multiple_dates_one_label(self):
        self.assertEqual(inspect(body="活動日期：2027/1/16、2027/1/17")["decision"], "HOLD_LABELED_ACTIVITY_DATE_MISSING_OR_AMBIGUOUS")
    def test_14_invalid_date(self):
        self.assertEqual(inspect(body="活動日期：2027/2/30")["decision"], "HOLD_LABELED_ACTIVITY_DATE_MISSING_OR_AMBIGUOUS")
    def test_15_reverse_range(self):
        self.assertEqual(inspect(body="活動日期：2027/1/17-16")["decision"], "HOLD_LABELED_ACTIVITY_DATE_MISSING_OR_AMBIGUOUS")
    def test_16_html_line(self):
        self.assertEqual(inspect(body="<p>活動日期/時間：2027/1/16-17</p><p>售票時間：2026/12/1</p>")["decision"], "REVIEW_TITLE_BODY_ACTIVITY_DATE_PARITY_NOT_ACCEPTED")
    def test_17_empty_title(self):
        self.assertEqual(inspect(title="")["decision"], "HOLD_EMPTY_TITLE")
    def test_18_invalid_input(self):
        self.assertEqual(m.inspect_date_role(None, "活動日期：2027/1/16")["decision"], "HOLD_INPUT_SHAPE_OR_CAP")
    def test_19_cap(self):
        self.assertEqual(inspect(body="x" * (m.MAX_TEXT + 1))["decision"], "HOLD_INPUT_SHAPE_OR_CAP")
    def test_20_accepted_zero(self):
        self.assertEqual(inspect()["acceptedFields"], 0)
    def test_21_no_raw_date(self):
        self.assertNotIn("2027/1/16", str(inspect()))
    def test_22_no_ticket_identity(self):
        self.assertIsNone(inspect()["ticketEventId"])
    def test_23_no_published(self):
        self.assertFalse(inspect()["published"])
    def test_24_no_network(self):
        self.assertEqual(m.offline_contract_report()["httpRequests"], 0)
    def test_25_no_live_fetch(self):
        self.assertFalse(hasattr(m, "fetch_once"))
    def test_26_single_day(self):
        self.assertEqual(inspect(title="虛構 2027/1/16", body="演出日期：2027/1/16")["decision"], "REVIEW_TITLE_BODY_ACTIVITY_DATE_PARITY_NOT_ACCEPTED")
    def test_27_other_month_end(self):
        self.assertEqual(inspect(title="虛構 2027/1/31-2/1", body="活動日期：2027/1/31-2/1")["decision"], "REVIEW_TITLE_BODY_ACTIVITY_DATE_PARITY_NOT_ACCEPTED")
    def test_28_month_end_invalid(self):
        self.assertEqual(inspect(title="虛構 2027/1/31-2/30", body="活動日期：2027/1/31-2/30")["decision"], "HOLD_TITLE_DATE_MISSING_OR_AMBIGUOUS")


if __name__ == "__main__":
    unittest.main()
