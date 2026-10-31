#!/usr/bin/env python3
"""P30-VENUE-02AJ: Zepp rid=163025 source price/sale roles, external ticket HOLD.

Venue detail explicitly lists nine ticket-price tiers and two SALE start
times, but does not assign tiers/sale windows to the two named sessions.
TicketPlus JavaScript shell cannot establish independent event parity.
"""
import hashlib
import re
from urllib.parse import urlsplit

SOURCE="Zepp New Taipei P0 venue"
RID="163025"
DETAIL="https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=163025"
TICKET="https://ticketplus.com.tw/activity/a3cb941035a5a7e6898f4000f76bd25c"
HOLD="HARD_HOLD_NO_PUBLICATION"
PRICES=(8500,8000,6500,5500,4500,4000,3500,2500,1500)
SALE=("2026-09-12 14:00","2026-09-12 15:00")
SESSIONS=(("13:00","AlmondProgress"),("19:30","SkyNani"))

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def inspect(detail, ticket):
    out=dict(gate="P30-VENUE-02AJ",source=SOURCE,officialGETinCI=0,
             candidateProvenance=[],acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=HOLD,ticketEventId=None)
    if not isinstance(detail,dict) or not isinstance(ticket,dict):
        return dict(out,decision="HOLD_UNSTRUCTURED_SOURCE")
    if (detail.get("url")!=DETAIL or detail.get("rid")!=RID
            or detail.get("title")!="2026 GMMTV FANDAY 39 in TAIPEI"
            or detail.get("date")!="2026-10-31"
            or detail.get("sessions")!=list(SESSIONS)):
        return dict(out,decision="HOLD_VENUE_SAME_RID_SESSION_IDENTITY")
    if detail.get("ticket_url")!=TICKET or detail.get("ticket_body_status")!="網頁建置中":
        return dict(out,decision="HOLD_TICKET_LINK_BODY_STATUS_CONFLICT")
    if detail.get("prices")!=list(PRICES) or detail.get("sale_starts")!=list(SALE):
        return dict(out,decision="HOLD_PRICE_SALE_ROLE_OR_CARDINALITY")
    if detail.get("price_to_session") is not None or detail.get("sale_to_session") is not None:
        return dict(out,decision="HOLD_UNSUPPORTED_PER_SESSION_MAPPING")
    if ticket.get("url")!=TICKET or ticket.get("js_shell") is not True:
        return dict(out,decision="HOLD_EXTERNAL_TICKET_OBSERVATION")
    if ticket.get("title_verified") is not False or ticket.get("session_verified") is not False:
        return dict(out,decision="HOLD_TICKET_PARITY_UNPROVEN")
    stamp=detail.get("observed_at")
    if not isinstance(stamp,str) or not re.fullmatch(r"20\d\d-\d\d-\d\d",stamp):
        return dict(out,decision="HOLD_OBSERVED_AT")
    vals=[("VENUE_PRICE_TIER_UNMAPPED",str(p)) for p in PRICES]
    vals += [("SALE_START_NOT_PERFORMANCE",s) for s in SALE]
    vals += [("VENUE_SESSION", "|".join(s)) for s in SESSIONS]
    for role,value in vals:
        out["candidateProvenance"].append(dict(source=SOURCE,source_url=DETAIL,
            source_rid=RID,observed_at=stamp,role=role,valueSHA256=sha(value),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    out["priceTierCount"]=len(PRICES)
    out["saleWindowCount"]=len(SALE)
    out["sessionCount"]=len(SESSIONS)
    return dict(out,decision="HOLD_PRICE_SALE_TO_SESSION_MAPPING_AND_TICKET_PARITY")

if __name__=="__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_NETWORK")
