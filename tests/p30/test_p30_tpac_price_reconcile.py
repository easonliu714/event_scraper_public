"""Only synthetic negative/positive fixtures here; CI replays sealed real TPAC HTML."""
import hashlib
import unittest
from copy import deepcopy

from scripts.p30_tpac_price_reconcile import (
    extract_tpac_price_review, reconcile_opentix_price,
)

TITLE = "沉浸式劇場《士林YES！》"
TPAC = "https://tpac.org.taipei/program/2040"
OPENTIX = "https://www.opentix.life/event/2065059039769808896"
VENUE_SESSIONS = [
    "2026-11-20T19:30+08:00",
    "2026-11-21T12:30+08:00",
    "2026-11-21T18:00+08:00",
    "2026-11-22T12:30+08:00",
    "2026-11-26T19:30+08:00",
    "2026-11-27T19:30+08:00",
    "2026-11-28T18:00+08:00",
    "2026-11-29T12:30+08:00",
]
TICKET_SESSIONS = sorted(VENUE_SESSIONS + [
    "2026-11-22T18:00+08:00",
    "2026-11-28T12:30+08:00",
])


def sample():
    html = (f'<main><article class="page-program__article"><h1>{TITLE}</h1>'
            f'</article><div class="page-program__aside-ticket">'
            f'<div class="page-program__aside-ticket-price">'
            f'<span>票價</span><strong>3500-1500 元</strong></div>'
            f'<a href="{OPENTIX}">購票去</a></div></main>').encode()
    receipt = {
        "detail_url": TPAC,
        "detail_bytes": len(html),
        "detail_sha256": hashlib.sha256(html).hexdigest(),
        "started_at": "2026-11-08T13:15:54Z",
        "decision": "RAW_SOURCE_SAVED_FOR_INDEPENDENT_REPLAY_ONLY",
        "source_native_get": 3,
    }
    return html, receipt


def rehash(html, receipt):
    receipt["detail_bytes"] = len(html)
    receipt["detail_sha256"] = hashlib.sha256(html).hexdigest()


class TPACAdmissionReviewTests(unittest.TestCase):
    def assert_hold(self, raw, receipt, reason):
        result = extract_tpac_price_review(raw, receipt, "2040", TITLE)
        self.assertEqual(result["decision"], "HOLD", result)
        self.assertEqual(result["reason"], reason, result)

    def test_exact_official_range_reversed_order_and_linked_ticket_identity(self):
        html, receipt = sample()
        data = extract_tpac_price_review(html, receipt, "2040", TITLE)
        self.assertEqual(data["decision"], "SOURCE_PRICE_ROLE_REVIEW_NOT_FORMAL")
        self.assertEqual(data["role"], "EVENT_GENERAL_ADMISSION_PRICE_RANGE")
        self.assertEqual((data["min_price_ntd"], data["max_price_ntd"]), (1500, 3500))
        self.assertEqual(data["display_suggestion"], "NT$1,500 起（詳官方）")
        self.assertEqual(data["linked_ticket"]["ticket_event_url"], OPENTIX)
        self.assertEqual(data["linked_ticket"]["ticket_event_id"], "2065059039769808896")
        self.assertEqual(data["linked_ticket"]["relation"], "DIRECT_OFFICIAL_TPAC_DETAIL_LINK")
        self.assertFalse(data["published"])
        self.assertFalse(data["formal_field_pass"])
        self.assertFalse(data["golden_accepted"])

    def test_range_does_not_accept_discount_membership_fee_or_presale(self):
        for special in ("會員優惠 3500-1500 元", "票價 3500-1500 元 手續費50元",
                        "VIP票價 3500-1500 元", "票價 3500-1500 元 早鳥優惠"):
            html, receipt = sample()
            changed = html.replace("票價</span><strong>3500-1500 元".encode(),
                                   ("票價</span><strong>" + special).encode())
            rehash(changed, receipt)
            self.assertEqual(extract_tpac_price_review(changed, receipt, "2040", TITLE)["decision"],
                             "HOLD", special)

    def test_title_wrong_event_id_body_sha_and_stale_receipt_hold(self):
        html, receipt = sample()
        self.assertEqual(extract_tpac_price_review(html, receipt, "2041", TITLE)["reason"],
                         "TPAC_PRICE_SOURCE_EVENT_ID_HOLD")
        self.assertEqual(extract_tpac_price_review(html, receipt, "2040", "不同活動")["reason"],
                         "TPAC_PRICE_TITLE_IDENTITY_HOLD")
        self.assert_hold(html+b"!",receipt,"TPAC_PRICE_BODY_PROVENANCE_HOLD")
        raw, receipt = sample()
        receipt["detail_url"] = "https://tpac.org.taipei/program/9999"
        self.assert_hold(raw, receipt, "TPAC_PRICE_BODY_PROVENANCE_HOLD")

    def test_spoofed_ticket_link_or_duplicate_buy_links_hold(self):
        html, receipt = sample()
        for url in ("https://www.opentix.life.evil.org/event/2065059039769808896",
                    "http://www.opentix.life/event/2065059039769808896",
                    OPENTIX+"?session=3"):
            changed = html.replace(OPENTIX.encode(),url.encode())
            changed_receipt = deepcopy(receipt)
            rehash(changed, changed_receipt)
            self.assert_hold(changed,changed_receipt,"TPAC_PRICE_TICKET_IDENTITY_URL_HOLD")
        html, receipt = sample()
        changed = html.replace(b"</a></div>",b"</a><a href='"+OPENTIX.encode()+b"'>購票去</a></div>")
        rehash(changed, receipt)
        self.assert_hold(changed,receipt,"TPAC_PRICE_TICKET_DIRECT_LINK_HOLD")

    def test_unlabeled_or_missing_general_price_holds(self):
        html, receipt = sample()
        changed = html.replace("票價</span>".encode(), "會員</span>".encode())
        rehash(changed,receipt)
        self.assert_hold(changed,receipt,"TPAC_PRICE_EXACT_LABEL_HOLD")
        html, receipt = sample()
        changed = html.replace(b"3500-1500",b"???")
        rehash(changed,receipt)
        self.assert_hold(changed,receipt,"TPAC_PRICE_GENERAL_RANGE_FORMAT_HOLD")

    def test_tier_cross_check_confirms_min_but_holds_extra_ticket_sessions(self):
        html, receipt = sample()
        offer = extract_tpac_price_review(html, receipt, "2040", TITLE)
        result = reconcile_opentix_price(
            offer,ticket_event_url=OPENTIX,title=TITLE,
            venue_name="臺北表演藝術中心",
            normal_ticket_tiers=[1500,2000,2500,3000,3500],
            sessions=TICKET_SESSIONS,venue_sessions=VENUE_SESSIONS,
        )
        self.assertEqual(result["decision"], "PRICE_RANGE_MATCH_REVIEW_NOT_FORMAL")
        self.assertEqual(result["min_price_ntd"], 1500)
        self.assertEqual(result["ordinary_tiers"], [1500,2000,2500,3000,3500])
        self.assertEqual(result["ticket_only_sessions"], [
            "2026-11-22T18:00+08:00", "2026-11-28T12:30+08:00"])
        self.assertIn("CROSS_SOURCE_SESSION_SET_CONFLICT_HOLD", result["held_fields"])
        self.assertIn("INDEPENDENT_TICKET_BODY_RECEIPT_REQUIRED_HOLD", result["held_fields"])
        self.assertFalse(result["accepted_for_formal_publish"])

    def test_cross_source_rejects_wrong_event_title_venue_price_and_ticket_ids(self):
        html, receipt = sample()
        offer=extract_tpac_price_review(html,receipt,"2040",TITLE)
        base={
            "ticket_event_url":OPENTIX,"title":TITLE,
            "venue_name":"臺北表演藝術中心",
            "normal_ticket_tiers":[1500,2000,2500,3000,3500],
            "sessions":TICKET_SESSIONS,"venue_sessions":VENUE_SESSIONS}
        for key,value,reason in [
            ("ticket_event_url","https://www.opentix.life/event/99999","TICKET_EVENT_LINK_ID_MISMATCH_HOLD"),
            ("title","士林YES!不同活動","TICKET_TITLE_MISMATCH_HOLD"),
            ("venue_name","其他場館","TICKET_VENUE_MISMATCH_HOLD"),
            ("normal_ticket_tiers",[500,2000,3500],"VENUE_TICKET_PRICE_RANGE_CONFLICT_HOLD"),
            ("normal_ticket_tiers",[2000,2500,3500],"VENUE_TICKET_PRICE_RANGE_CONFLICT_HOLD")
        ]:
            kwargs=base.copy()
            kwargs[key]=value
            result=reconcile_opentix_price(offer,**kwargs)
            self.assertEqual(result["reason"],reason,(key,result))

    def test_even_independent_ticket_receipt_does_not_enable_formal_publish(self):
        html,receipt=sample()
        offer=extract_tpac_price_review(html,receipt,"2040",TITLE)
        result=reconcile_opentix_price(offer,ticket_event_url=OPENTIX,title=TITLE,
             venue_name="臺北表演藝術中心",normal_ticket_tiers=[1500,2000,2500,3000,3500],
             sessions=VENUE_SESSIONS,venue_sessions=VENUE_SESSIONS,
             independent_ticket_receipt_verified=True)
        self.assertEqual(result["decision"],"PRICE_RANGE_MATCH_REVIEW_NOT_FORMAL")
        self.assertEqual(result["held_fields"],[])
        self.assertFalse(result["accepted_for_formal_publish"])


if __name__=="__main__":
    unittest.main()
