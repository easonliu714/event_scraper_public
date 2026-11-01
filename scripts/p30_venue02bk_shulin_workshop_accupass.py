"""P30-VENUE-02BK: Shulin official program → ACCUPASS exact workshop edge.
The workshop has two source-described occurrences, not verified ticket Session IDs.
No network, registration, checkout, production publication or source duplication.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.culture.ntpc.gov.tw/shulin_artcenter_chi/xmdoc?XsmSId=0J080506169482009359"
DETAIL = "https://www.culture.ntpc.gov.tw/shulin_artcenter_chi/xmdoc/cont?sid=0Q273522679833703495&xsmsid=0J080506169482009359"
TICKET = "https://www.accupass.com/event/2609151410103172453460"
BULLETIN_SID = "0Q273522679833703495"
TITLE = "親子工作坊《跟爸爸媽媽一起用身體揉一座山》"
VENUE = "樹林藝文中心3F排練室"
OCCURRENCES = ("2026-11-21T10:30/11:30", "2026-11-22T10:30/11:30")

def exact_url(actual, expected):
    if not isinstance(actual, str):
        return False
    a, e = urlsplit(actual), urlsplit(expected)
    return (a.scheme == e.scheme == "https" and a.netloc == e.netloc
            and a.username is None and a.password is None and a.port is None
            and a.path == e.path and a.query == e.query and not a.fragment)

def inspect(record, observed_at):
    out = {"gate": "P30-VENUE-02BK", "candidateFields": [], "acceptedFields": 0,
           "ticketSessionIdsVerified": 0, "goldenAccepted": 0, "published": False}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(record, dict) or not exact_url(record.get("list_url"), LIST):
        return dict(out, decision="HOLD_SHULIN_LIST")
    if not exact_url(record.get("list_detail_href"), DETAIL) or not exact_url(record.get("detail_url"), DETAIL):
        return dict(out, decision="HOLD_SAME_SOURCE_DETAIL")
    if record.get("bulletin_sid") != BULLETIN_SID or record.get("bulletin_date") != "2026-09-30":
        return dict(out, decision="HOLD_BULLETIN_ID_OR_PUBLISH_DATE")
    if not exact_url(record.get("venue_ticket_href"), TICKET) or not exact_url(record.get("ticket_event_url"), TICKET):
        return dict(out, decision="HOLD_DIRECT_ACCUPASS_EDGE")
    if record.get("ticket_event_id") != "2609151410103172453460":
        return dict(out, decision="HOLD_TICKET_EVENT_ID")
    if record.get("venue_title") != TITLE or record.get("ticket_title") != TITLE or record.get("venue") != VENUE:
        return dict(out, decision="HOLD_TITLE_OR_VENUE")
    if tuple(record.get("venue_occurrences") or ()) != OCCURRENCES or tuple(record.get("ticket_occurrences") or ()) != OCCURRENCES:
        return dict(out, decision="HOLD_TWO_OCCURRENCE_PARITY")
    if record.get("fee_amount") != 100 or record.get("fee_unit") != "one_parent_child_pair":
        return dict(out, decision="HOLD_FEE_PER_PAIR_NOT_PERSON")
    if (record.get("bulletin_date_is_show") is not False or
            record.get("festival_range_is_one_show") is not False or
            record.get("ticket_event_is_session") is not False):
        return dict(out, decision="HOLD_DATE_AND_ID_ROLES")
    if any(record.get(k) is not None for k in (
            "ticket_session_ids", "inventory", "checkout", "published_event",
            "cross_event_id", "other_workshop_as_same_event")):
        return dict(out, decision="HOLD_UNVERIFIED_SESSION_OR_CROSS_EVENT")
    def candidate(field, value, source, url, role):
        return {"field": field, "value": value, "source": source,
                "source_url": url, "observed_at": observed_at,
                "role": role, "decision": "REVIEW"}
    out["candidateFields"] = [
        candidate("bulletin_sid", BULLETIN_SID, "NTPC_SHULIN_OFFICIAL", DETAIL, "BULLETIN_NOT_TICKET_ID"),
        candidate("workshop_occurrences", list(OCCURRENCES), "NTPC_SHULIN_OFFICIAL", DETAIL, "TWO_WORKSHOP_OCCURRENCES"),
        candidate("ticket_event_id", "2609151410103172453460", "ACCUPASS_02", TICKET, "EVENT_NOT_SESSION"),
        candidate("ticket_occurrences", list(OCCURRENCES), "ACCUPASS_02", TICKET, "OCCURRENCES_NOT_SESSION_IDS"),
        candidate("fee_per_pair", 100, "ACCUPASS_02", TICKET, "ONE_PARENT_CHILD_PAIR_NOT_PER_PERSON"),
        candidate("bulletin_publish_date", "2026-09-30", "NTPC_SHULIN_OFFICIAL", DETAIL, "PUBLISHED_NOT_SHOW"),
    ]
    return dict(out, decision="REVIEW_SHULIN_WORKSHOP_HOLD_TICKET_SESSIONS")
