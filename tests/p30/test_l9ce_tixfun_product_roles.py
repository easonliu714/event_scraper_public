"""P30-L9-CE official index link, price/date/discount/session boundary negatives."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9ce_tixfun_product_roles.py"
spec = importlib.util.spec_from_file_location("l9ce", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    index = dict(url=m.INDEX_URL, detail_url=m.DETAIL_URL,
                 title="AM創意2026《恐龍復活了2：勇闖神秘島》音樂劇")
    detail = dict(url=m.DETAIL_URL, product_id=m.PRODUCT_ID,
                  title="《恐龍復活了2：勇闖神秘島》音樂劇",
                  date_range=list(m.RANGE), price_range=list(m.PRICE_RANGE),
                  early_bird=list(m.EARLY_BIRD), general_onsale=m.GENERAL_ONSALE,
                  discount_deadline=m.DISCOUNT_DEADLINE,
                  session_rows=None, ticket_session_id=None,
                  session_price=None, inventory=None)
    return index, detail

class Gate(unittest.TestCase):
    def check(self, mutation=None, date="2026-10-31"):
        i, d = fixture()
        if mutation:
            mutation(i, d)
        return m.inspect(i, d, date)
    def reject(self, code, mutation=None, date="2026-10-31"):
        x = self.check(mutation, date)
        self.assertEqual(x["decision"], code)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
    def test_eight_source_bound_review_receipts(self):
        x = self.check()
        self.assertEqual(x["decision"], "HOLD_PRODUCT_RANGE_AND_DYNAMIC_SESSION_CHOOSER")
        self.assertEqual(len(x["candidateProvenance"]), 8)
        self.assertTrue(all(v["decision"] == "REVIEW_NOT_FORMALLY_ACCEPTED" for v in x["candidateProvenance"]))
    def test_bad_date(self):
        self.reject("HOLD_OBSERVED_AT", date="2026-02-30")
    def test_index_link_cross_host(self):
        self.reject("HOLD_OFFICIAL_INDEX_LINK", lambda i, d: i.update(detail_url="https://evil.test/UTK0201_?PRODUCT_ID=Q029ZSDJ"))
    def test_index_link_duplicate_product(self):
        self.reject("HOLD_OFFICIAL_INDEX_LINK", lambda i, d: i.update(detail_url=m.DETAIL_URL+"&PRODUCT_ID=Q029ZSDJ"))
    def test_index_link_malformed_query(self):
        self.reject("HOLD_OFFICIAL_INDEX_LINK", lambda i, d: i.update(detail_url=m.DETAIL_URL+"&bad"))
    def test_detail_other_product(self):
        self.reject("HOLD_PRODUCT_ID", lambda i, d: d.update(product_id="Q029ZSDX"))
    def test_title_core_mismatch(self):
        self.reject("HOLD_SOURCE_LOCAL_TITLE_CORE", lambda i, d: d.update(title="另一齣音樂劇"))
    def test_range_is_not_session(self):
        self.reject("HOLD_PRODUCT_DATE_RANGE", lambda i, d: d.update(date_range=["2026-12-19"]))
    def test_price_band_is_not_ticket_price(self):
        self.reject("HOLD_PRODUCT_PRICE_BAND", lambda i, d: d.update(price_range=[600, 850]))
    def test_sale_date_not_showtime(self):
        self.reject("HOLD_SALE_PERIOD_ROLE", lambda i, d: d.update(general_onsale="2026-12-19 14:30"))
    def test_discount_not_session(self):
        self.reject("HOLD_DISCOUNT_NOT_SHOWTIME", lambda i, d: d.update(discount_deadline="2026-12-20"))
    def test_invented_session(self):
        self.reject("HOLD_NO_PUBLIC_SESSION_ALLOCATION", lambda i, d: d.update(ticket_session_id="123"))
    def test_invented_price(self):
        self.reject("HOLD_NO_PUBLIC_SESSION_ALLOCATION", lambda i, d: d.update(session_price=600))
    def test_invented_inventory(self):
        self.reject("HOLD_NO_PUBLIC_SESSION_ALLOCATION", lambda i, d: d.update(inventory=20))
    def test_invented_rows(self):
        self.reject("HOLD_NO_PUBLIC_SESSION_ALLOCATION", lambda i, d: d.update(session_rows=[["2026-12-19", "14:30"]]))

if __name__ == "__main__":
    unittest.main()
