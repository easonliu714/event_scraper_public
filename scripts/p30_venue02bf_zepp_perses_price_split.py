"""P30-VENUE-02BF: Zepp Nov 28 PERSES price composition and AKASAKI cancellation.

Official venue schedule is not a verified KKTIX activity/session link. No external GET.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.zepp.co.jp/hall/newtaipei/schedule/"
PERSES = "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=169301"
CANCELLED = "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=160673"
TITLE = "ALL PIECES, ONE PERSES"
CANCELLED_TITLE = 'AKASAKI 1st WORLD TOUR "ONIGIRI"'
SHOW = "2026-11-28T18:00"
TIERS = (("SVIP", 7980, 7979, 1), ("VIP A", 5980, 5979, 1),
         ("VIP B", 4980, 4979, 1), ("VIP C", 3980, 3979, 1),
         ("GA", 2980, 2979, 1))

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-VENUE-02BF", "acceptedFields": 0,
           "ticketSessionIdsVerified": 0, "goldenAccepted": 0,
           "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("schedule_list"), LIST):
        return dict(out, decision="HOLD_OFFICIAL_SCHEDULE_LIST")
    if not exact_url(x.get("perses_list_href"), PERSES) or not exact_url(x.get("perses_detail"), PERSES):
        return dict(out, decision="HOLD_PERSES_RID")
    if not exact_url(x.get("akasaki_list_href"), CANCELLED) or not exact_url(x.get("akasaki_detail"), CANCELLED):
        return dict(out, decision="HOLD_CANCELLED_RID")
    if (x.get("perses_rid"), x.get("akasaki_rid"), x.get("perses_title"),
        x.get("akasaki_title")) != ("169301", "160673", TITLE, CANCELLED_TITLE):
        return dict(out, decision="HOLD_DISTINCT_RID_TITLE")
    if x.get("perses_show") != SHOW or x.get("akasaki_show") != SHOW:
        return dict(out, decision="HOLD_SAME_DAY_DIFFERENT_EVENT")
    if x.get("akasaki_cancelled") is not True or x.get("perses_cancelled") is not False:
        return dict(out, decision="HOLD_CANCELLATION_SCOPE")
    tiers = x.get("price_components")
    if not isinstance(tiers, (list, tuple)) or tuple(map(tuple, tiers)) != TIERS:
        return dict(out, decision="HOLD_PRICE_COMPONENTS")
    if any(total != base + welfare for _, total, base, welfare in TIERS):
        return dict(out, decision="HOLD_PRICE_ARITHMETIC")
    if x.get("accessible_price") != 2490 or x.get("accessible_equivalence") != 4980:
        return dict(out, decision="HOLD_ACCESSIBLE_ELIGIBILITY")
    if x.get("sale_start") != "2026-10-17T12:00" or x.get("sale_is_show") is not False:
        return dict(out, decision="HOLD_SALE_ROLE")
    if x.get("claimed_platform") != "KKTIX" or x.get("ticket_href_text") != "Link in Bio":
        return dict(out, decision="HOLD_CLAIMED_PLATFORM")
    if any(x.get(k) is not None for k in ("verified_kktix_url", "ticket_session_id",
                                          "inventory", "ticket_price_verified", "published_event")):
        return dict(out, decision="HOLD_NO_DIRECT_TICKET_EDGE")
    def candidate(field, value, url, role):
        return {"field": field, "value": value, "source": "ZEPP_NEW_TAIPEI_OFFICIAL",
                "source_url": url, "observed_at": observed_at, "role": role, "decision": "REVIEW"}
    out["candidateFields"] = [
        candidate("perses_show", SHOW, PERSES, "VENUE_DESCRIPTIVE_SHOW"),
        candidate("price_components", [list(t) for t in TIERS], PERSES, "VENUE_TIER_PLUS_ONE_WELFARE_NOT_TICKET_SESSION"),
        candidate("accessible_price", 2490, PERSES, "ELIGIBILITY_CONDITIONAL_NOT_STANDARD_TIER"),
        candidate("sale_start", "2026-10-17T12:00", PERSES, "SALE_NOT_SHOW"),
        candidate("akasaki_cancelled", True, CANCELLED, "OTHER_RID_CANCELLED_ONLY"),
        candidate("claimed_platform", "KKTIX", PERSES, "VENUE_CLAIM_NOT_VERIFIED_KKTIX_URL")]
    return dict(out, decision="REVIEW_PERSES_PRICE_SPLIT_CANCELLED_OTHER_RID_HOLD_KKTIX_URL")
