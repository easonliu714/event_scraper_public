"""P30-L9-DE: canonical KHAM #04 direct product and venue evidence; REVIEW only."""
from datetime import datetime
from urllib.parse import urlsplit, parse_qs

KHAM = "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2"
TMC = "https://www.tmc.taipei/tw/blog/show/2026SungNien-Yu"
KHAM_SESSION_LIST = "https://kham.com.tw/application/UTK02/UTK0201_00.aspx?PRODUCT_ID=P1DF32E2"
KHAM_TITLE = "2026 小宇 宋念宇《不，完美的人》演唱會"
TMC_TITLE = "小宇 宋念宇 《不，完美的人》 演唱會"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    try:
        a, b = urlsplit(value), urlsplit(expected)
        return (a.scheme == b.scheme == "https" and a.hostname == b.hostname
                and a.netloc == b.netloc and a.path == b.path and a.query == b.query
                and not a.fragment and a.username is None and a.password is None)
    except ValueError:
        return False

def inspect(obs, observed_at):
    result = dict(gate="P30-L9-DE", canonicalPlatformId="04",
                  decision="HOLD_SOURCE", candidateFields=[], acceptedFields=0,
                  ticketSessionIdsVerified=0, goldenAccepted=0, published=False,
                  releaseState="HARD_HOLD_NO_PUBLICATION")
    try:
        t = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if t.tzinfo is None or t.utcoffset() is None:
            raise ValueError("naive")
    except (ValueError, TypeError, AttributeError, OverflowError):
        result["decision"] = "HOLD_OBSERVATION"
        return result
    if not isinstance(obs, dict):
        return result
    if not exact_url(obs.get("kham_detail_url"), KHAM):
        result["decision"] = "HOLD_KHAM_IDENTITY"
        return result
    if not exact_url(obs.get("venue_detail_url"), TMC) or not exact_url(obs.get("venue_ticket_href"), KHAM):
        result["decision"] = "HOLD_DIRECT_VENUE_LINK"
        return result
    if parse_qs(urlsplit(KHAM).query) != {"PRODUCT_ID": ["P1DF32E2"]}:
        result["decision"] = "HOLD_PRODUCT_ID"
        return result
    if obs.get("kham_title") != KHAM_TITLE or obs.get("tmc_title") != TMC_TITLE:
        result["decision"] = "HOLD_SOURCE_TITLE"
        return result
    if obs.get("kham_sale_start") != "2026-08-22T12:00:00+08:00":
        result["decision"] = "HOLD_SALE_ROLE"
        return result
    if obs.get("venue_show") != "2026-11-07T19:30:00+08:00":
        result["decision"] = "HOLD_SHOW_ROLE"
        return result
    if obs.get("venue_name") != "臺北流行音樂中心 表演廳":
        result["decision"] = "HOLD_VENUE"
        return result
    if obs.get("venue_price_bands") != [4280, 3880, 3480, 2880, 2480, 1880]:
        result["decision"] = "HOLD_PRICE_ROLE"
        return result
    # The KHAM product's public session-selection page contains two distinct rows.
    # Struck prices are display styling, not independent inventory or sell-out evidence.
    if not exact_url(obs.get("kham_session_list_url"), KHAM_SESSION_LIST):
        result["decision"] = "HOLD_KHAM_SESSION_LIST_URL"
        return result
    if obs.get("session_list_title") != KHAM_TITLE:
        result["decision"] = "HOLD_KHAM_SESSION_LIST_TITLE"
        return result
    show = "2026-11-07T19:30:00+08:00"
    venue = "臺北流行音樂中心 表演廳"
    standard = {"show": show, "venue": venue, "label": "",
                "displayed_prices": [1880, 2480, 2880, 3480, 3880, 4280],
                "struck_through": True}
    wheelchair = {"show": show, "venue": venue, "label": "輪椅席",
                  "displayed_prices": [3480, 4280], "struck_through": False}
    if obs.get("standard_row") != standard or obs.get("wheelchair_row") != wheelchair:
        result["decision"] = "HOLD_KHAM_DISTINCT_SESSION_ROWS"
        return result
    for k in ("checkout_url", "ticket_session_id", "inventory", "formal_accepted", "golden_accepted"):
        if k in obs and obs[k] is not None:
            result["decision"] = "HOLD_UNVERIFIED_" + k.upper()
            return result
    facts = [
        ("kham_product_id", "P1DF32E2", "TICKET_PRODUCT_NOT_SESSION", KHAM),
        ("kham_sale_start", obs["kham_sale_start"], "SALE_START_NOT_SHOW", KHAM),
        ("venue_show", obs["venue_show"], "VENUE_ANNOUNCED_SHOW_NOT_TICKET_SESSION", TMC),
        ("venue_name", obs["venue_name"], "VENUE", TMC),
        ("venue_price_bands", obs["venue_price_bands"], "VENUE_ADVERTISED_PRICE_BANDS_NOT_CHECKOUT", TMC),
        ("venue_ticket_href", KHAM, "VENUE_TO_EXACT_KHAM_PRODUCT_LINK", TMC),
        ("kham_session_list_url", KHAM_SESSION_LIST, "PRODUCT_SESSION_SELECTION_PAGE_NOT_SESSION_ID", KHAM_SESSION_LIST),
        ("standard_row", standard, "KHAM_STANDARD_PRICE_STRUCK_NOT_STOCK_PROOF", KHAM_SESSION_LIST),
        ("wheelchair_row", wheelchair, "KHAM_WHEELCHAIR_SEPARATE_ROW_NOT_GENERAL_PRICE", KHAM_SESSION_LIST)
    ]
    result["candidateFields"] = [
        dict(field=k, value=v, role=role, source=src,
             observed_at=observed_at, decision="REVIEW")
        for k, v, role, src in facts
    ]
    result["decision"] = "REVIEW_DIRECT_PRODUCT_LINK_HOLD_SESSION_AND_PRICE_AUTHORITY"
    return result
