"""P30-VENUE-02AN: Xinzhuang row #2 direct ERA #08 URL is opaque, not a verified ticket event."""
import datetime
import hashlib
import re

BULLETIN="https://www.xzcac.ntpc.gov.tw/xmdoc/cont?sid=0Q252550255605202263&xsmsid=0G286655201682579075"
TICKET="https://ticket.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1CXDGLJ"
VENUE_TITLE="2026新莊有好戲 英雄傳-武聖關公/南臺灣交響樂團"
DATE="2026-10-17"
TIME="14:30"
PRICE_CLASSES=(500,1000,1500,2000,2500,3000)

def inspect(row, ticket_view, observed_at):
    out=dict(gate="P30-VENUE-02AN",source="XINZHUANG_VENUE_P0",
             ticketSource="ERA#08",acceptedFields=0,goldenAccepted=0,
             published=False,candidateProvenance=[],ticketEventIdentityVerified=False)
    try:
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}",observed_at or ""):
            raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except (TypeError,ValueError):
        return dict(out,decision="HOLD_OBSERVED_AT")
    if row.get("bulletin_url")!=BULLETIN or row.get("row_number")!=2:
        return dict(out,decision="HOLD_ROW2_OWNERSHIP")
    if row.get("title")!=VENUE_TITLE or row.get("event_date")!=DATE or row.get("event_time")!=TIME:
        return dict(out,decision="HOLD_VENUE_ROW_ROLE")
    if tuple(row.get("price_classes") or ())!=PRICE_CLASSES:
        return dict(out,decision="HOLD_VENUE_PRICE_CLASSES")
    if row.get("ticket_url")!=TICKET or ticket_view.get("url")!=TICKET:
        return dict(out,decision="HOLD_DIRECT_ERA_URL")
    if ticket_view.get("visible_event_title") or ticket_view.get("visible_event_date") or ticket_view.get("visible_venue"):
        return dict(out,decision="HOLD_TICKET_FIELDS_NOT_IN_PUBLIC_READER")
    if ticket_view.get("session_id") or ticket_view.get("inventory") is not None or ticket_view.get("session_price") is not None:
        return dict(out,decision="HOLD_TICKET_SESSION_INVENTORY_PRICE_UNVERIFIED")
    if ticket_view.get("rendered_section_labels")!=["節目資訊","場次列表"]:
        return dict(out,decision="HOLD_TICKET_VIEW_SECTION_SHAPE")
    for source,url,role,value in (
        ("XINZHUANG_VENUE",BULLETIN,"ROW2_VENUE_TITLE",VENUE_TITLE),
        ("XINZHUANG_VENUE",BULLETIN,"ROW2_VENUE_DATE",DATE),
        ("XINZHUANG_VENUE",BULLETIN,"ROW2_VENUE_TIME",TIME),
        ("XINZHUANG_VENUE",BULLETIN,"ROW2_VENUE_PRICE_CLASSES","500/1000/1500/2000/2500/3000"),
        ("XINZHUANG_VENUE",BULLETIN,"ROW2_DIRECT_ERA_URL",TICKET),
        ("ERA#08",TICKET,"OPAQUE_PRODUCT_TOKEN_NOT_EVENT_ID","P1CXDGLJ")):
        out["candidateProvenance"].append(dict(source=source,source_url=url,
            observed_at=observed_at,role=role,valueSHA256=hashlib.sha256(value.encode()).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out,decision="HOLD_ERA_TICKET_TITLE_DATE_SESSION_NOT_RENDERED")
