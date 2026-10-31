"""P30-VENUE-02AO: Xinzhuang official row #3 has two showtimes, no ticket Event ID."""
import datetime,hashlib,re
BULLETIN="https://www.xzcac.ntpc.gov.tw/xmdoc/cont?sid=0Q252550255605202263&xsmsid=0G286655201682579075"
TITLE="朱宗慶打擊樂新莊大新教學中心2026年度音樂會"
def inspect(row,observed_at):
    out=dict(gate="P30-VENUE-02AO",source="XINZHUANG_VENUE_P0",acceptedFields=0,goldenAccepted=0,published=False,candidateProvenance=[],ticketEventIdVerified=False)
    try:
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}",observed_at or ""):raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except (TypeError,ValueError):return dict(out,decision="HOLD_OBSERVED_AT")
    if row.get("url")!=BULLETIN or row.get("row")!=3:return dict(out,decision="HOLD_ROW3_OWNERSHIP")
    if row.get("title")!=TITLE or row.get("performance_date")!="2026-10-18":
        return dict(out,decision="HOLD_ROW3_TITLE_DATE")
    if row.get("times")!=["11:00","15:00"]:
        return dict(out,decision="HOLD_TWO_SHOWTIMES_NO_COLLAPSE")
    if row.get("ticket_method")!="索票" or row.get("ticket_url") is not None:
        return dict(out,decision="HOLD_NO_DIRECT_TICKET_URL")
    if row.get("price") is not None or row.get("ticket_event_id") is not None or row.get("inventory") is not None:
        return dict(out,decision="HOLD_NO_PRICE_OR_TICKET_ID_INFERENCE")
    for role,value in (("ROW3_TITLE",TITLE),("ROW3_PERFORMANCE_DATE","2026-10-18"),("ROW3_SHOWTIME_1","11:00"),("ROW3_SHOWTIME_2","15:00"),("ROW3_TICKET_METHOD_NOT_FREE_PRICE","索票"),("BULLETIN_SID_NOT_TICKET_EVENT_ID","0Q252550255605202263")):
        out["candidateProvenance"].append(dict(source="XINZHUANG_VENUE",source_url=BULLETIN,observed_at=observed_at,role=role,valueSHA256=hashlib.sha256(value.encode()).hexdigest(),decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out,decision="HOLD_TWO_VENUE_SHOWTIMES_NO_TICKET_SESSION_ID")
