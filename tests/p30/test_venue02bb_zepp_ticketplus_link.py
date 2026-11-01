"""P30-VENUE-02BB: Zepp same-rid venue href and Ticket Plus JS shell negative gates."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02bb_zepp_ticketplus_link.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"list_url": m.LIST, "list_detail_href": m.DETAIL, "detail_url": m.DETAIL,
            "rid": "163838", "list_title": m.TITLE, "detail_title": m.TITLE,
            "detail_ticket_href": m.TICKET, "ticket_platform_label": "Ticket Plus",
            "venue_text_ticket_url_status": "網頁建置中",
            "ticket_response_kind": "JS_SHELL_WITHOUT_EVENT_DETAIL",
            "show_datetime": m.SHOW, "sale_start": m.SALE, "benefit_cutoff": m.BENEFIT,
            "product_price_tiers": m.TIERS, "ticket_event_id": None, "ticket_session_id": None,
            "ticket_session_price": None, "inventory": None, "published_event": None}

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def reject(self, expected, key, value):
        out = self.check(key, value)
        self.assertEqual(out["decision"], expected)
        self.assertEqual(out["acceptedFields"], 0)
        self.assertFalse(out["published"])
    def test_review_source_bound(self):
        x = self.check()
        self.assertEqual(x["decision"], "REVIEW_VENUE_HREF_HOLD_TICKETPLUS_JS_DETAIL_AND_SESSION")
        self.assertEqual(len(x["candidateFields"]), 5)
        self.assertEqual(x["provenance"][1]["decision"], "HOLD_TICKETPLUS_JS_DETAIL_UNVERIFIED")
        self.assertEqual(x["provenance"][1]["source"], "TICKETPLUS_EXTERNAL_UNVERIFIED")
    def test_observed_at(self):
        self.assertEqual(m.inspect(fixture(), "invalid")["decision"], "HOLD_OBSERVATION")
    def test_list_host(self): self.reject("HOLD_ZEPP_LIST_URL", "list_url", "https://evil.example/hall/newtaipei/")
    def test_list_extra(self): self.reject("HOLD_ZEPP_LIST_URL", "list_url", m.LIST + "?page=2")
    def test_list_detail_rid(self): self.reject("HOLD_ZEPP_RID_DETAIL", "list_detail_href", m.DETAIL.replace("163838", "160668"))
    def test_detail_host(self): self.reject("HOLD_ZEPP_RID_DETAIL", "detail_url", m.DETAIL.replace("www.zepp.co.jp", "evil.example"))
    def test_detail_fragment(self): self.reject("HOLD_ZEPP_RID_DETAIL", "detail_url", m.DETAIL + "#buy")
    def test_title(self): self.reject("HOLD_ZEPP_TITLE_RID", "detail_title", "another event")
    def test_list_title(self): self.reject("HOLD_ZEPP_TITLE_RID", "list_title", "another event")
    def test_rid(self): self.reject("HOLD_ZEPP_TITLE_RID", "rid", "OTHER")
    def test_ticket_href_host(self): self.reject("HOLD_TICKETPLUS_DIRECT_HREF", "detail_ticket_href", m.TICKET.replace("ticketplus.com.tw", "evil.example"))
    def test_ticket_href_path(self): self.reject("HOLD_TICKETPLUS_DIRECT_HREF", "detail_ticket_href", m.TICKET + "abc")
    def test_ticket_href_fragment(self): self.reject("HOLD_TICKETPLUS_DIRECT_HREF", "detail_ticket_href", m.TICKET + "#order")
    def test_platform_label(self): self.reject("HOLD_VENUE_TICKET_ROLE_CONFLICT", "ticket_platform_label", "KKTIX")
    def test_text_contradiction(self): self.reject("HOLD_VENUE_TICKET_ROLE_CONFLICT", "venue_text_ticket_url_status", "verified")
    def test_js_shell(self): self.reject("HOLD_TICKETPLUS_JS_DETAIL_UNVERIFIED", "ticket_response_kind", "VERIFIED_EVENT_DETAIL")
    def test_show(self): self.reject("HOLD_PERFORMANCE_SALE_BENEFIT_PRICE_ROLES", "show_datetime", m.SALE)
    def test_sale(self): self.reject("HOLD_PERFORMANCE_SALE_BENEFIT_PRICE_ROLES", "sale_start", m.SHOW)
    def test_benefit(self): self.reject("HOLD_PERFORMANCE_SALE_BENEFIT_PRICE_ROLES", "benefit_cutoff", m.SHOW)
    def test_tiers(self): self.reject("HOLD_PERFORMANCE_SALE_BENEFIT_PRICE_ROLES", "product_price_tiers", m.TIERS[:3])
    def test_ticket_event_id(self): self.reject("HOLD_TICKET_SESSION_PROMOTION", "ticket_event_id", "993e73c01ab8d4c4380cc62bf1f203fe")
    def test_session_id(self): self.reject("HOLD_TICKET_SESSION_PROMOTION", "ticket_session_id", "163838")
    def test_session_price(self): self.reject("HOLD_TICKET_SESSION_PROMOTION", "ticket_session_price", 8500)
    def test_inventory(self): self.reject("HOLD_TICKET_SESSION_PROMOTION", "inventory", 100)
    def test_published(self): self.reject("HOLD_TICKET_SESSION_PROMOTION", "published_event", True)

if __name__ == "__main__":
    unittest.main()
