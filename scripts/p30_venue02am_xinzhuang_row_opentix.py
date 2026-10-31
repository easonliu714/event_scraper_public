"""P30-VENUE-02AM: Xinzhuang stage bulletin row-local official OPENTIX link; no publication."""
import hashlib
import re
INDEX="https://www.xzcac.ntpc.gov.tw/xmdoc?xsmsid=0G286655201682579075"
BULLETIN="https://www.xzcac.ntpc.gov.tw/xmdoc/cont?sid=0Q252550255605202263&xsmsid=0G286655201682579075"
SID="0Q252550255605202263"
TITLE="「Da Capo」2026年彩虹城市管樂團年度音樂會"
VENUE="新莊文化藝術中心演藝廳"
TICKET="https://www.opentix.life/event/2089995501384269825"
DATE="2026-12-05"
TIME="14:00"

def inspect(index,bulletin,ticket,observed_at):
    out=dict(source="XINZHUANG_VENUE_P0",acceptedFields=0,goldenAccepted=0,
             published=False,candidateProvenance=[],ticketSessionVerified=False)
    if not re.fullmatch(r"20\d\d-\d\d-\d\d",observed_at or ""):
        return dict(out,decision="HOLD_OBSERVED_AT")
    if index.get("url")!=INDEX or index.get("detail_url")!=BULLETIN:
        return dict(out,decision="HOLD_VENUE_INDEX_LINK")
    if bulletin.get("url")!=BULLETIN or bulletin.get("sid")!=SID:
        return dict(out,decision="HOLD_SAME_SID_BULLETIN")
    if bulletin.get("row_count")!=9 or bulletin.get("row_number")!=4:
        return dict(out,decision="HOLD_BULLETIN_ROW_OWNERSHIP")
    if bulletin.get("title")!=TITLE or ticket.get("title")!=TITLE:
        return dict(out,decision="HOLD_TICKET_TITLE_PARITY")
    if bulletin.get("venue")!=VENUE or ticket.get("venue")!=VENUE:
        return dict(out,decision="HOLD_TICKET_VENUE_PARITY")
    if bulletin.get("ticket_url")!=TICKET or ticket.get("url")!=TICKET:
        return dict(out,decision="HOLD_EXACT_EXTERNAL_TICKET_EVENT_ID")
    if bulletin.get("event_date")!=DATE or bulletin.get("event_time")!=TIME:
        return dict(out,decision="HOLD_ROW_LOCAL_EVENT_DATE_TIME")
    if bulletin.get("price_classes")!=[400,500] or ticket.get("per_session_price") is not None:
        return dict(out,decision="HOLD_PRICE_CLASS_NOT_SESSION_PRICE")
    if ticket.get("event_session_date") is not None or ticket.get("inventory") is not None:
        return dict(out,decision="HOLD_TICKET_SESSION_OR_INVENTORY_UNVERIFIED")
    for url,role,value in ((BULLETIN,"VENUE_BULLETIN_SID_NOT_EVENT_ID",SID),
        (BULLETIN,"ROW4_EVENT_TITLE",TITLE),(BULLETIN,"ROW4_EVENT_DATE",DATE),
        (BULLETIN,"ROW4_EVENT_TIME",TIME),(BULLETIN,"ROW4_PRICE_CLASSES_NOT_INVENTORY","400/500"),
        (BULLETIN,"ROW4_DIRECT_TICKET_URL",TICKET),
        (TICKET,"TICKET_EVENT_ID","2089995501384269825")):
        out["candidateProvenance"].append(dict(source=out["source"] if url==BULLETIN else "OPENTIX#05",
          source_url=url,observed_at=observed_at,role=role,
          valueSHA256=hashlib.sha256(value.encode()).hexdigest(),
          decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out,decision="HOLD_VENUE_ROW_TO_TICKET_EVENT_LINK_SESSION_NOT_CONFIRMED")
