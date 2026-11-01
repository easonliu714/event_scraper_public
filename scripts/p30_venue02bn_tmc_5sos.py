"""P30-VENUE-02BN: Taipei Music Center official 5SOS LIST/DETAIL -> tixCraft detail.
Two first-party source observations with separate provenance. Venue event URL is
not a tixCraft Session ID. VIP upgrade without admission must remain distinct.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.tmc.taipei/tw/blog/show"
VENUE_DETAIL = "https://www.tmc.taipei/tw/blog/show/5SOS2026"
TICKET_DETAIL = "https://tixcraft.com/activity/detail/26_5sos"
VENUE_TITLE = "5 SECONDS OF SUMMER: EVERYONES A STAR！ WORLD TOUR"
TICKET_TITLE = "5 SECONDS OF SUMMER: EVERYONE’S A STAR! WORLD TOUR"
SHOW = "2026-11-25T20:00"
VENUE = "臺北流行音樂中心 表演廳"
VENUE_PUBLISHED = "2026-10-25"
ACCESSIBLE_PRICES = (1990, 2490)

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    a, b = urlsplit(value), urlsplit(expected)
    return (a.scheme == b.scheme == "https" and a.netloc == b.netloc
            and a.username is None and a.password is None and a.port is None
            and a.path == b.path and a.query == b.query and not a.fragment)

def inspect(row, observed_at):
    result = {"gate": "P30-VENUE-02BN", "candidateFields": [],
              "acceptedFields": 0, "ticketSessionIdsVerified": 0,
              "goldenAccepted": 0, "published": False}
    try:
        if date.fromisoformat(observed_at).isoformat() != observed_at:
            raise ValueError("noncanonical")
    except (TypeError, ValueError):
        return dict(result, decision="HOLD_OBSERVATION")
    if not isinstance(row, dict) or not exact_url(row.get("venue_list"), LIST):
        return dict(result, decision="HOLD_VENUE_LIST")
    if not exact_url(row.get("list_detail_href"), VENUE_DETAIL) or not exact_url(row.get("venue_detail"), VENUE_DETAIL):
        return dict(result, decision="HOLD_VENUE_DETAIL_IDENTITY")
    if row.get("venue_title") != VENUE_TITLE or row.get("venue_show") != SHOW or row.get("venue") != VENUE:
        return dict(result, decision="HOLD_VENUE_SHOW_TITLE")
    if not exact_url(row.get("venue_ticket_href"), TICKET_DETAIL) or not exact_url(row.get("ticket_detail"), TICKET_DETAIL):
        return dict(result, decision="HOLD_DIRECT_TICKET_LINK")
    if row.get("ticket_title") != TICKET_TITLE or row.get("ticket_show") != SHOW:
        return dict(result, decision="HOLD_TICKET_EVENT_PARITY")
    # Source publication date is not the show; conditional concessions are not general prices.
    if (row.get("venue_published_at") != VENUE_PUBLISHED or
            row.get("venue_publication_role") != "ARTICLE_PUBLICATION_NOT_SHOW"):
        return dict(result, decision="HOLD_PUBLICATION_NOT_SHOW")
    if (row.get("accessible_prices") != ACCESSIBLE_PRICES or
            row.get("accessible_price_role") != "DISABILITY_CONCESSION_NOT_GENERAL_MINIMUM"):
        return dict(result, decision="HOLD_CONCESSION_NOT_GENERAL_PRICE")
    if (row.get("venue_min_general_price") != 3380 or
            row.get("venue_vip_seat_package") != 8680 or
            row.get("ticket_vip_standing_package") != 7380):
        return dict(result, decision="HOLD_PRICE_CATEGORY")
    if (row.get("vip_upgrade_role") != "BENEFIT_ONLY_REQUIRES_VALID_CONCERT_TICKET"
            or row.get("vip_package_role") != "INCLUDES_ADMISSION"):
        return dict(result, decision="HOLD_UPGRADE_NOT_ADMISSION")
    if row.get("ticket_service_fee") != 200 or row.get("service_fee_role") != "ADDITIONAL_PER_TICKET":
        return dict(result, decision="HOLD_FEE_NOT_FACE_VALUE")
    if any(row.get(k) is not None for k in ("ticket_session_id", "inventory_count",
                                           "upgrade_is_admission", "published_event")):
        return dict(result, decision="HOLD_UNVERIFIED_SESSION_OR_PUBLICATION")
    def f(name, value, url, source, role):
        return {"field": name, "value": value, "source": source, "source_url": url,
                "observed_at": observed_at, "role": role, "decision": "REVIEW"}
    result["candidateFields"] = [
        f("venue_show", SHOW, VENUE_DETAIL, "TMC_VENUE_OFFICIAL", "VENUE_DESCRIBED_SHOW"),
        f("ticket_show", SHOW, TICKET_DETAIL, "TIXCRAFT_03", "TICKET_EVENT_SHOW_NOT_SESSION"),
        f("venue_ticket_href", TICKET_DETAIL, VENUE_DETAIL, "TMC_VENUE_OFFICIAL", "DIRECT_TICKET_EVENT_LINK"),
        f("vip_upgrade", "BENEFIT_ONLY", TICKET_DETAIL, "TIXCRAFT_03", "UPGRADE_NOT_ADMISSION"),
        f("service_fee", 200, TICKET_DETAIL, "TIXCRAFT_03", "ADDITIONAL_FEE_NOT_FACE_VALUE"),
        f("venue_publication", VENUE_PUBLISHED, VENUE_DETAIL, "TMC_VENUE_OFFICIAL", "ARTICLE_PUBLICATION_NOT_SHOW"),
        f("accessible_prices", list(ACCESSIBLE_PRICES), VENUE_DETAIL, "TMC_VENUE_OFFICIAL", "DISABILITY_CONCESSION_NOT_GENERAL_MINIMUM"),
    ]
    return dict(result, decision="REVIEW_DIRECT_TICKET_EVENT_HOLD_SESSION")
