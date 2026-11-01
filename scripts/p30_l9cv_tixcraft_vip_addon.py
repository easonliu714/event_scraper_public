"""P30-L9-CV: first-party tixCraft standard admission vs conditional VIP upgrade.
Evidence-bound negative guard only; no HTTP requests, login or publishing.
"""
from datetime import date
from urllib.parse import urlsplit

STANDARD = "https://tixcraft.com/activity/detail/26_vashhsu"
UPGRADE = "https://tixcraft.com/activity/detail/26_vashhsu_v"
TITLE = "徐暐翔《愛火山的人》專場演唱會"
SHOW = "2026-11-08T18:00"
VENUE = "Legacy Taipei"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-L9-CV", "acceptedFields": 0,
           "ticketSessionIdsVerified": 0, "goldenAccepted": 0,
           "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("standard_url"), STANDARD):
        return dict(out, decision="HOLD_STANDARD_SOURCE")
    if not exact_url(x.get("upgrade_url"), UPGRADE):
        return dict(out, decision="HOLD_UPGRADE_SOURCE")
    if not exact_url(x.get("standard_links_upgrade"), UPGRADE) or not exact_url(x.get("upgrade_links_standard"), STANDARD):
        return dict(out, decision="HOLD_RECIPROCAL_FIRST_PARTY_EDGE")
    if x.get("standard_activity_id") != "26_vashhsu" or x.get("upgrade_activity_id") != "26_vashhsu_v":
        return dict(out, decision="HOLD_DISTINCT_ACTIVITY_IDENTITIES")
    if x.get("standard_title") != TITLE or x.get("upgrade_title") != TITLE:
        return dict(out, decision="HOLD_SAME_SHOW_TITLE")
    if (x.get("standard_show") != SHOW or x.get("upgrade_show") != SHOW
            or x.get("standard_venue") != VENUE or x.get("upgrade_venue") != VENUE):
        return dict(out, decision="HOLD_SAME_SHOW_AND_VENUE")
    if x.get("standard_price") != 1450 or x.get("accessible_price") != 725 or x.get("upgrade_price") != 600:
        return dict(out, decision="HOLD_PRICE_SCOPE")
    if (x.get("upgrade_requires_same_show_admission") is not True
            or x.get("upgrade_valid_alone") is not False
            or x.get("upgrade_is_admission") is not False
            or x.get("upgrade_is_second_show") is not False
            or x.get("accessible_is_general") is not False):
        return dict(out, decision="HOLD_ADDON_NOT_ADMISSION")
    if any(x.get(k) is not None for k in ("ticket_session_id", "inventory", "checkout",
                                         "published_event", "combined_ticket_price")):
        return dict(out, decision="HOLD_UNVERIFIED_SESSION_OR_PRICE")
    def candidate(field, value, url, role):
        return {"field": field, "value": value, "source": "TIXCRAFT_03",
                "source_url": url, "observed_at": observed_at, "role": role,
                "decision": "REVIEW"}
    out["candidateFields"] = [
        candidate("standard_activity", "26_vashhsu", STANDARD, "EVENT_NOT_SESSION"),
        candidate("upgrade_activity", "26_vashhsu_v", UPGRADE, "ADD_ON_NOT_EVENT"),
        candidate("show", SHOW, STANDARD, "SINGLE_SHOW_NOT_TWO"),
        candidate("admission_price", 1450, STANDARD, "DESCRIPTIVE_ADMISSION"),
        candidate("accessible_price", 725, STANDARD, "ELIGIBILITY_ONLY"),
        candidate("upgrade_price", 600, UPGRADE, "CONDITIONAL_ADD_ON"),
        candidate("requires_same_show_ticket", True, UPGRADE, "DEPENDENCY_NOT_CHECKOUT"),
    ]
    return dict(out, decision="REVIEW_TIXCRAFT_VIP_ADDON_HOLD_SESSIONS")
