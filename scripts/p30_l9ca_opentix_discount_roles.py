"""P30-L9-CA: official OPENTIX event discount cutoff is not a dated performance session."""
import datetime, hashlib, re
VENUE="https://www.xzcac.ntpc.gov.tw/xmdoc/cont?sid=0Q252550255605202263&xsmsid=0G286655201682579075"
TICKET="https://www.opentix.life/event/2089995501384269825"
TITLE="「Da Capo」2026年彩虹城市管樂團年度音樂會"
HALL="新莊文化藝術中心演藝廳"
def inspect(venue_row,ticket,observed_at):
    out=dict(gate="P30-L9-CA",source="OPENTIX#05",candidateProvenance=[],acceptedFields=0,goldenAccepted=0,published=False,sessionDateVerified=False,inventoryVerified=False)
    try:
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}",observed_at or ""): raise ValueError("date format")
        datetime.date.fromisoformat(observed_at)
    except (ValueError,TypeError): return dict(out,decision="HOLD_OBSERVED_AT")
    if venue_row.get("url")!=VENUE or venue_row.get("row")!=4 or venue_row.get("ticket_url")!=TICKET:
        return dict(out,decision="HOLD_VENUE_ROW_AND_LINK")
    if ticket.get("url")!=TICKET or ticket.get("title")!=TITLE or venue_row.get("title")!=TITLE:
        return dict(out,decision="HOLD_EXACT_TICKET_ID_TITLE")
    if venue_row.get("performance_date")!="2026-12-05" or venue_row.get("performance_time")!="14:00":
        return dict(out,decision="HOLD_VENUE_PERFORMANCE_ROLE")
    if ticket.get("venue")!=HALL or ticket.get("admission_time")!="13:30" or ticket.get("show_start_time")!="14:00":
        return dict(out,decision="HOLD_TICKET_VENUE_OR_TIME_ROLE")
    if ticket.get("early_bird_deadline")!="2026-10-11 23:59" or ticket.get("early_bird_price_classes")!=[500,400]:
        return dict(out,decision="HOLD_DISCOUNT_ROLE_NOT_OBSERVED")
    if ticket.get("dated_session") is not None or ticket.get("session_id") is not None or ticket.get("inventory") is not None:
        return dict(out,decision="HOLD_UNVERIFIED_TICKET_SESSION")
    for source,url,role,value in (
        ("XINZHUANG_VENUE",VENUE,"ROW4_PERFORMANCE_DATE","2026-12-05"),
        ("XINZHUANG_VENUE",VENUE,"ROW4_DIRECT_TICKET_URL",TICKET),
        ("OPENTIX#05",TICKET,"TICKET_TITLE",TITLE),
        ("OPENTIX#05",TICKET,"TICKET_VENUE",HALL),
        ("OPENTIX#05",TICKET,"ADMISSION_TIME","13:30"),
        ("OPENTIX#05",TICKET,"SHOW_START_TIME","14:00"),
        ("OPENTIX#05",TICKET,"DISCOUNT_DEADLINE_NOT_SESSION","2026-10-11 23:59"),
        ("OPENTIX#05",TICKET,"DISCOUNT_ELIGIBLE_PRICE_CLASSES_NOT_INVENTORY","500/400")):
        out["candidateProvenance"].append(dict(source=source,source_url=url,observed_at=observed_at,role=role,valueSHA256=hashlib.sha256(value.encode()).hexdigest(),decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out,decision="HOLD_DISCOUNT_DEADLINE_NOT_DATED_TICKET_SESSION")
