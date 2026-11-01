"""FamiTicket #07 public source-bound voucher identity and role negatives."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cw_famiticket_voucher_role.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return dict(list_url=m.LIST, list_category="交換票", list_title=m.TITLE,
                list_detail_href=m.DETAIL, detail_url=m.DETAIL,
                detail_title=m.TITLE, detail_kind="電影交換券",
                film_release_date="2026-11-06", film_release_label="上映日期",
                refund_deadline="2026-11-05", refund_label="退票收件截止",
                exchange_for_one_cinema_admission=True,
                voucher_is_specific_screening=False,
                cinema_screening_time=None, cinema_venue=None,
                ticket_session_id=None, ticket_inventory=None,
                checkout_url=None, published_event=None)

class VoucherGate(unittest.TestCase):
    def inspect(self, field=None, value=None):
        x = fixture()
        if field is not None:
            x[field] = value
        return m.inspect(x, "2026-11-01")

    def test_source_bound_candidate_not_published(self):
        result = self.inspect()
        self.assertEqual(result["decision"], "REVIEW_FAMITICKET_VOUCHER_HOLD_SCREENING_SESSION")
        self.assertEqual(len(result["candidateFields"]), 5)
        self.assertEqual(result["acceptedFields"], 0)
        self.assertEqual(result["ticketSessionIdsVerified"], 0)
        self.assertFalse(result["published"])
        self.assertTrue(all(c["source"] == "FAMITICKET_07" and c["decision"] == "REVIEW"
                            and c["observed_at"] == "2026-11-01" for c in result["candidateFields"]))

    def test_list_and_detail_same_title_link(self):
        for k, v, expected in [
            ("list_url", m.LIST+"?fake=1", "HOLD_LIST_SOURCE"),
            ("list_category", "演唱會", "HOLD_LIST_IDENTITY_OR_CATEGORY"),
            ("list_title", "different", "HOLD_LIST_IDENTITY_OR_CATEGORY"),
            ("list_detail_href", "https://evil.example/Activity/Info/x", "HOLD_DIRECT_DETAIL_EDGE"),
            ("detail_url", m.DETAIL+"#checkout", "HOLD_DIRECT_DETAIL_EDGE"),
            ("detail_title", "another", "HOLD_DETAIL_IDENTITY_OR_VOUCHER"),
            ("detail_kind", "特定場次票", "HOLD_DETAIL_IDENTITY_OR_VOUCHER"),
        ]:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k, v)["decision"], expected)

    def test_release_refund_and_exchange_roles(self):
        for k, v, expected in [
            ("film_release_date", "2026-11-05", "HOLD_RELEASE_ROLE"),
            ("film_release_label", "演出時間", "HOLD_RELEASE_ROLE"),
            ("refund_deadline", "2026-11-06", "HOLD_REFUND_ROLE"),
            ("refund_label", "場次時間", "HOLD_REFUND_ROLE"),
            ("exchange_for_one_cinema_admission", False, "HOLD_EXCHANGE_NOT_SESSION"),
            ("voucher_is_specific_screening", True, "HOLD_EXCHANGE_NOT_SESSION"),
        ]:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k, v)["decision"], expected)

    def test_no_fabricated_screening_or_checkout(self):
        for k, v in [("cinema_screening_time", "2026-11-06T19:30"),
                     ("cinema_venue", "Taipei cinema"), ("ticket_session_id", "guessed"),
                     ("ticket_inventory", 2), ("checkout_url", m.DETAIL),
                     ("published_event", True)]:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k, v)["decision"], "HOLD_UNVERIFIED_SCREENING_OR_CHECKOUT")

    def test_bad_observation(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_LIST_SOURCE")

if __name__ == "__main__":
    unittest.main()
