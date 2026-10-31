"""P30-L9-CM: KKTIX official three purchase-edge identities; registration 403 is not ticket-session proof."""
from datetime import date
from urllib.parse import urlsplit
LIST_URL="https://freeplanetml.kktix.cc/events/takasetoya202611"
REG_URLS=tuple(f"https://kktix.com/events/takasetoya202611-{i}/registrations/new" for i in (1,2,3))
ROLES=("TWO_DAY_BUNDLE_NOT_THIRD_PERFORMANCE","NOV07_SINGLE_DAY","NOV08_SINGLE_DAY")
DATES=("2026-11-07/2026-11-08","2026-11-07","2026-11-08")
TIMES=("18:00/17:00","18:00","17:00")
def inspect(x,observed_at):
    out={"gate":"P30-L9-CM","acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,"published":False,"provenance":[]}
    try: date.fromisoformat(observed_at)
    except (ValueError,TypeError): return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(x,dict) or x.get("source_url")!=LIST_URL:
        return dict(out,decision="HOLD_KKTIX_SOURCE")
    if x.get("event_title")!='TAKASE TOYA 5th Album “∞” Release Live in Taipei' or x.get("venue")!="Zepp New Taipei":
        return dict(out,decision="HOLD_TITLE_VENUE_IDENTITY")
    if x.get("registration_urls")!=REG_URLS or x.get("registration_roles")!=ROLES:
        return dict(out,decision="HOLD_THREE_EXACT_EDGES")
    if x.get("date_roles")!=DATES or x.get("start_times")!=TIMES:
        return dict(out,decision="HOLD_DAY_BUNDLE_ROLE")
    for u in (LIST_URL,)+REG_URLS:
        p=urlsplit(u)
        if p.scheme!="https" or p.username or p.password or p.fragment or p.query:
            return dict(out,decision="HOLD_URL_POLICY")
    if x.get("registration_http_status")!=(403,403,403) or x.get("registration_decision")!="HOLD_FORBIDDEN_NO_BYPASS":
        return dict(out,decision="HOLD_REGISTRATION_ACCESS")
    if any(x.get(k) is not None for k in ("ticket_session_id","inventory","available_for_purchase","verified_ticket_session_price","canonical_published_event_id")):
        return dict(out,decision="HOLD_UNVERIFIED_PROMOTION")
    out["provenance"]=[{"source":"KKTIX_01","source_url":LIST_URL,"observed_at":observed_at,"role":"EVENT_LIST_AND_THREE_DISTINCT_REGISTRATION_EDGES","decision":"REVIEW"}]
    out["provenance"] += [{"source":"KKTIX_01","source_url":u,"observed_at":observed_at,"role":r,"decision":"HOLD_HTTP403_REGISTRATION_NOT_VERIFIED"} for u,r in zip(REG_URLS,ROLES)]
    return dict(out,decision="HOLD_REGISTRATION_403_NOT_SESSION_ID")
