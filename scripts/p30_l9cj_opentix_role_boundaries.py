"""Source-bound OPENTIX #05 event-level SALE/ADMISSION/REFUND semantics; no ticket session."""
import datetime
from urllib.parse import urlsplit
EVENT_URL="https://www.opentix.life/event/2086734015886159873"
EVENT_ID="2086734015886159873"
VENUE="新北市藝文中心演藝廳"
SALE=[("2026-08-18","12:00","2026-09-20","23:59","MEMBER_EARLY_75"),
      ("2026-08-28","12:00","2026-09-20","23:59","GENERAL_EARLY_85")]
SHOWS=[("2026-11-07","14:30"),("2026-11-08","10:30"),("2026-11-08","14:30")]
def inspect(x, observed_at):
    out={"gate":"P30-L9-CJ","acceptedFields":0,"goldenAccepted":0,"published":False,"provenance":[]}
    try: datetime.date.fromisoformat(observed_at)
    except (ValueError,TypeError): return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(x,dict) or x.get("url")!=EVENT_URL or urlsplit(x["url"]).path!="/event/"+EVENT_ID or x.get("event_id")!=EVENT_ID:
        return dict(out,decision="HOLD_EVENT_ID")
    if x.get("venue")!=VENUE or x.get("venue_count")!=9 or x.get("venue_count_role")!="CHOOSER_NOT_SESSIONS":
        return dict(out,decision="HOLD_VENUE_ROLE")
    if x.get("sale_windows")!=SALE or x.get("sale_role")!="DISCOUNT_ELIGIBILITY_NOT_SHOW":
        return dict(out,decision="HOLD_SALE_WINDOW")
    if x.get("shows")!=SHOWS or x.get("show_role")!="VENUE_DESCRIPTIVE_NOT_TICKET_SESSION":
        return dict(out,decision="HOLD_SHOW_ROLE")
    if x.get("admission_minutes_before")!=30 or x.get("admission_role")!="DOOR_OPEN_RELATIVE_NOT_SHOWTIME":
        return dict(out,decision="HOLD_ADMISSION_ROLE")
    if x.get("duration_minutes")!=95 or x.get("stage_minutes")!=80 or x.get("intermission_minutes")!=15 or x.get("duration_role")!="DURATION_NOT_SESSION":
        return dict(out,decision="HOLD_DURATION_ROLE")
    if x.get("refund_days_before")!=10 or x.get("refund_excludes_show_date") is not True or x.get("refund_fee_percent")!=10 or x.get("refund_role")!="RELATIVE_POLICY_NOT_DEADLINE":
        return dict(out,decision="HOLD_REFUND_POLICY")
    if any(x.get(k) is not None for k in ("ticket_session_ids","session_price","inventory","absolute_refund_deadline")):
        return dict(out,decision="HOLD_UNVERIFIED_TICKET_FIELD")
    for start,st,end,et,role in SALE:
        out["provenance"].append({"source":"OPENTIX_05","source_url":EVENT_URL,"observed_at":observed_at,"role":role,"value":[start,st,end,et],"decision":"REVIEW"})
    out["provenance"].append({"source":"OPENTIX_05","source_url":EVENT_URL,"observed_at":observed_at,"role":"ADMISSION_DURATION_REFUND_POLICY","decision":"REVIEW"})
    return dict(out,decision="HOLD_ROLE_EVIDENCE_NO_TICKET_SESSION_ID")
