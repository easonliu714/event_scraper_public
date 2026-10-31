"""P30-L9-BY: source-bound OPENTIX #05 and Xinzhuang venue evidence, no network or publication."""
import hashlib
import re

EVENT_ID = "2089995501384269825"
URL = "https://www.opentix.life/event/" + EVENT_ID
TITLE = "「Da Capo」2026年彩虹城市管樂團年度音樂會"
VENUE = "新莊文化藝術中心演藝廳"
BULLETIN = "https://www.xzcac.ntpc.gov.tw/xmdoc/cont?sid=0Q252550255605202263&xsmsid=0G286655201682579075"
DATE = "2026-12-05"
TIME = "14:00"

def inspect(ticket, venue_row, observed_at):
    out = dict(source="OPENTIX#05", acceptedFields=0, goldenAccepted=0,
               published=False, candidateProvenance=[], sessionDateVerified=False,
               ticketAvailabilityVerified=False)
    if not re.fullmatch(r"20\d\d-\d\d-\d\d", observed_at or ""):
        return dict(out, decision="HOLD_OBSERVED_AT")
    if ticket.get("url") != URL or venue_row.get("ticket_url") != URL:
        return dict(out, decision="HOLD_EXACT_TICKET_EVENT_LINK")
    if ticket.get("title") != TITLE or venue_row.get("title") != TITLE:
        return dict(out, decision="HOLD_CROSS_SOURCE_TITLE")
    if ticket.get("venue") != VENUE or venue_row.get("venue") != VENUE:
        return dict(out, decision="HOLD_CROSS_SOURCE_VENUE")
    if venue_row.get("bulletin_url") != BULLETIN:
        return dict(out, decision="HOLD_FIRST_PARTY_VENUE_BULLETIN")
    if venue_row.get("event_date") != DATE or venue_row.get("start") != TIME:
        return dict(out, decision="HOLD_VENUE_DATE_TIME_ROLE")
    if ticket.get("admission_time") != "13:30" or ticket.get("show_start_text") != TIME:
        return dict(out, decision="HOLD_TICKET_ADMISSION_VS_SHOW_START")
    if ticket.get("ticket_session_date") or ticket.get("live_inventory") is not None:
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION_OR_INVENTORY")
    for source,url,role,value in (
        ("OPENTIX#05",URL,"TICKET_EVENT_ID",EVENT_ID),
        ("OPENTIX#05",URL,"EVENT_TITLE",TITLE),
        ("OPENTIX#05",URL,"VENUE",VENUE),
        ("OPENTIX#05",URL,"ADMISSION_TIME_NOT_SESSION_DATE","13:30"),
        ("XINZHUANG_VENUE",BULLETIN,"VENUE_EVENT_DATE",DATE),
        ("XINZHUANG_VENUE",BULLETIN,"VENUE_EVENT_START",TIME)):
        out["candidateProvenance"].append(dict(source=source,source_url=url,observed_at=observed_at,
            role=role,valueSHA256=hashlib.sha256(value.encode()).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out, decision="HOLD_TICKET_SESSION_DATE_NOT_INDEPENDENTLY_VERIFIED")
