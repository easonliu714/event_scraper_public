"""TPAC native admission-price source role and linked ticket-event identity.

Consumes archival official TPAC DETAIL bytes + original receipt (NO network).
A TPAC-authored first-party detail link is one-to-one evidence of a ticket
event relation; it NEVER proves ticket session IDs or seat availability.
All output is REVIEW-only until an independent field-quality/publication Gate.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup

PRICE = re.compile(
    r"^票價\s*(\d{1,3}(?:,\d{3})*|\d{3,6})\s*[-–－～~]\s*"
    r"(\d{1,3}(?:,\d{3})*|\d{3,6})\s*元$"
)
TPAC_URL = re.compile(r"^/program/([1-9]\d{0,9})$")
OPENTIX_URL = re.compile(r"^/event/([1-9]\d{4,21})$")
MAX_HTML_BYTES = 2 * 1024 * 1024
MAX_PRICE_NTD = 100000
TPAC_ORIGIN = "https://tpac.org.taipei"
TICKET_ORIGIN = "https://www.opentix.life"


def _plain(element):
    return " ".join(element.get_text(" ", strip=True).split()) if element else ""


def _validated_receipt(body, detail_url, source_event_id, receipt):
    """Receipt must agree with pinned bytes, canonical URL, timestamp and ID."""
    if not isinstance(body, bytes) or not 0 < len(body) <= MAX_HTML_BYTES:
        raise ValueError("TPAC_PRICE_SOURCE_BODY_CAP_HOLD")
    if not isinstance(receipt, dict):
        raise ValueError("TPAC_PRICE_SOURCE_RECEIPT_MISSING_HOLD")
    url = urlparse(detail_url)
    if (url.scheme + "://" + url.netloc != TPAC_ORIGIN
            or not TPAC_URL.fullmatch(url.path)
            or url.params or url.query or url.fragment
            or url.username or url.password
            or url.path.rsplit("/", 1)[-1] != str(source_event_id)):
        raise ValueError("TPAC_PRICE_SOURCE_EVENT_ID_HOLD")
    observed = receipt.get("started_at") if "started_at" in receipt else receipt.get("observed_at")
    try:
        dt = datetime.fromisoformat(observed.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as e:
        raise ValueError("TPAC_PRICE_OBSERVED_AT_HOLD") from e
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("TPAC_PRICE_OBSERVED_TZ_HOLD")
    sha = hashlib.sha256(body).hexdigest()
    # Accept both archived single-event native receipt and the reusable
    # per-detail Source Adapter receipt. Neither is an independent publication
    # attestation: exact original bytes must be independently replayed by CI.
    archived = (
        receipt.get("detail_sha256") == sha
        and receipt.get("detail_bytes") == len(body)
        and receipt.get("detail_url") == detail_url
        and receipt.get("decision") == "RAW_SOURCE_SAVED_FOR_INDEPENDENT_REPLAY_ONLY"
        and receipt.get("source_native_get") == 3
    )
    fresh_detail = (
        receipt.get("body_sha256") == sha
        and receipt.get("body_bytes") == len(body)
        and receipt.get("final_url") == detail_url
        and receipt.get("http_status") == 200
        and receipt.get("robots_allowed") is True
    )
    if not archived and not fresh_detail:
        raise ValueError("TPAC_PRICE_BODY_PROVENANCE_HOLD")
    return dt.astimezone(timezone.utc).isoformat(), sha


def extract_tpac_price_review(detail_body, receipt, expected_event_id, expected_title):
    """Require event-owned heading, exact standard-price block and one ticket link.

    Does not accept sales/discounts, fees, memberships or dynamic stock prices.
    Missing price or identity means HOLD, never guessed from unrelated page text.
    """
    url = TPAC_ORIGIN + "/program/" + str(expected_event_id)
    try:
        observed, sha = _validated_receipt(detail_body, url, expected_event_id, receipt)
        soup = BeautifulSoup(detail_body.decode("utf-8", "strict"), "html.parser")
        articles = soup.select("article.page-program__article")
        if (len(articles) != 1 or len(articles[0].select("h1")) != 1
                or _plain(articles[0].select_one("h1")) != expected_title):
            raise ValueError("TPAC_PRICE_TITLE_IDENTITY_HOLD")
        boxes = soup.select("div.page-program__aside-ticket-price")
        if len(boxes) != 1:
            raise ValueError("TPAC_PRICE_EVENT_OWNED_BOX_HOLD")
        box = boxes[0]
        labels = [x for x in box.select("span") if _plain(x) == "票價"]
        if len(labels) != 1:
            raise ValueError("TPAC_PRICE_EXACT_LABEL_HOLD")
        label = _plain(box)
        if any(x in label for x in (
                "優惠", "會員", "早鳥", "手續費", "服務費", "訂金", "加價",
                "文化幣", "套票", "折抵", "VIP", "票況")):
            raise ValueError("TPAC_PRICE_SPECIAL_OR_FEE_ROLE_HOLD")
        match = PRICE.fullmatch(label)
        if not match:
            raise ValueError("TPAC_PRICE_GENERAL_RANGE_FORMAT_HOLD")
        amounts = [int(x.replace(",", "")) for x in match.groups()]
        low, high = sorted(amounts)
        if not 100 <= low <= high <= MAX_PRICE_NTD:
            raise ValueError("TPAC_PRICE_RANGE_BOUNDS_HOLD")
        ticket_section = soup.select("div.page-program__aside-ticket")
        if len(ticket_section) != 1:
            raise ValueError("TPAC_PRICE_TICKET_SECTION_SCOPE_HOLD")
        linked = [a for a in ticket_section[0].select("a[href]") if _plain(a) == "購票去"]
        if len(linked) != 1:
            raise ValueError("TPAC_PRICE_TICKET_DIRECT_LINK_HOLD")
        link = urlparse(linked[0]["href"])
        if (link.scheme + "://" + link.netloc != TICKET_ORIGIN
                or not OPENTIX_URL.fullmatch(link.path)
                or link.params or link.query or link.fragment
                or link.username or link.password):
            raise ValueError("TPAC_PRICE_TICKET_IDENTITY_URL_HOLD")
        ticket_id = link.path.rsplit("/", 1)[-1]
        result = {
            "decision": "SOURCE_PRICE_ROLE_REVIEW_NOT_FORMAL",
            "source": "TPAC",
            "event_id": str(expected_event_id),
            "event_title": expected_title,
            "source_url": url,
            "source_body_sha256": sha,
            "observed_at": observed,
            "role": "EVENT_GENERAL_ADMISSION_PRICE_RANGE",
            "min_price_ntd": low,
            "max_price_ntd": high,
            "raw_price_label": label,
            "display_suggestion": "NT$" + format(low, ",") + " 起（詳官方）",
            "linked_ticket": {
                "platform": "OPENTIX",
                "ticket_event_id": ticket_id,
                "ticket_event_url": link.geturl(),
                "relation": "DIRECT_OFFICIAL_TPAC_DETAIL_LINK",
                "same_event_relation": "SOURCE_LINKED_NOT_TICKET_DETAIL_ATTESTED",
            },
            "held_fields": ["TICKET_SESSION_PARITY_NOT_ATTESTED",
                            "CURRENT_SEAT_STOCK_NOT_ATTESTED"],
            "formal_field_pass": False,
            "golden_accepted": False,
            "published": False,
        }
        return result
    except (ValueError, TypeError, AttributeError, UnicodeError, OverflowError) as error:
        return {
            "decision": "HOLD",
            "reason": str(error),
            "source_url": url,
            "event_id": str(expected_event_id),
            "published": False,
            "formal_field_pass": False,
        }


def inspect_opentix_native_body(body, receipt, *, event_url, expected_title, now):
    """Check caller-supplied ticket bytes against a bounded source receipt.

    This is an identity/provenance preflight, NOT independent artifact readback,
    ticket-price attestation, session parity, inventory, or publication.
    No network I/O. A boolean claim of native verification is never authority.
    """
    try:
        if type(body) is not bytes or not 0 < len(body) <= MAX_HTML_BYTES:
            raise ValueError("OPENTIX_BODY_MISSING_OR_CAP_HOLD")
        if not isinstance(receipt, dict):
            raise ValueError("OPENTIX_RECEIPT_MISSING_HOLD")
        u = urlparse(event_url)
        if (u.scheme + "://" + u.netloc != TICKET_ORIGIN
                or not OPENTIX_URL.fullmatch(u.path)
                or u.params or u.query or u.fragment
                or u.username or u.password):
            raise ValueError("OPENTIX_EXACT_EVENT_URL_HOLD")
        if (receipt.get("final_url") != event_url
                or receipt.get("http_status") != 200
                or receipt.get("robots_allowed") is not True
                or receipt.get("body_bytes") != len(body)
                or receipt.get("body_sha256") != hashlib.sha256(body).hexdigest()):
            raise ValueError("OPENTIX_NATIVE_RECEIPT_PARITY_HOLD")
        if (type(receipt.get("source_run_id")) is not int
                or receipt["source_run_id"] <= 0
                or not isinstance(receipt.get("artifact_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", receipt["artifact_sha256"])):
            raise ValueError("OPENTIX_ARTIFACT_PROVENANCE_MISSING_HOLD")
        try:
            observed = datetime.fromisoformat(
                receipt["observed_at"].replace("Z", "+00:00"))
        except (KeyError, AttributeError, ValueError) as e:
            raise ValueError("OPENTIX_OBSERVED_AT_HOLD") from e
        if observed.tzinfo is None or observed.utcoffset() is None:
            raise ValueError("OPENTIX_OBSERVED_TIMEZONE_HOLD")
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("OPENTIX_EVALUATION_CLOCK_HOLD")
        age = now.astimezone(timezone.utc) - observed.astimezone(timezone.utc)
        if age < timedelta(0) or age > timedelta(hours=24):
            raise ValueError("OPENTIX_SOURCE_FRESHNESS_HOLD")
        soup = BeautifulSoup(body.decode("utf-8", "strict"), "html.parser")
        mains = soup.select("main")
        if len(mains) != 1:
            raise ValueError("OPENTIX_EVENT_LOCAL_MAIN_HOLD")
        headings = mains[0].select("h1")
        if len(headings) != 1 or _plain(headings[0]) != expected_title:
            raise ValueError("OPENTIX_EVENT_LOCAL_TITLE_HOLD")
        return {
            "decision": "TICKET_BODY_IDENTITY_REVIEW_NOT_FIELD_AUTHORITY",
            "ticket_event_id": u.path.rsplit("/", 1)[-1],
            "ticket_event_url": event_url,
            "event_title": expected_title,
            "source_body_sha256": hashlib.sha256(body).hexdigest(),
            "observed_at": observed.astimezone(timezone.utc).isoformat(),
            "source_run_id": receipt["source_run_id"],
            "artifact_sha256_claim": receipt["artifact_sha256"],
            "independent_artifact_readback": False,
            "ticket_tiers_body_attested": False,
            "ticket_sessions_body_attested": False,
            "published": False,
        }
    except (ValueError, TypeError, UnicodeError, OverflowError) as error:
        return {"decision": "HOLD", "reason": str(error), "published": False}


# Ticket-session inputs are untrusted until event-local native roles are
# independently attested. Normalize *instants*, not strings, so UTC/+08:00
# aliases cannot create false parity or conceal duplicate showtimes.
SESSION_TIMESTAMP = re.compile(
    r"^20\\d{2}-\\d{2}-\\d{2}T(?:[01]\\d|2[0-3]):[0-5]\\d"
    r"(?:Z|[+-](?:[01]\\d|2[0-3]):[0-5]\\d)$"
)
TAIPEI = timezone(timedelta(hours=8))


def _canonical_session_instants(values):
    if not isinstance(values, (list, tuple)) or not 1 <= len(values) <= 40:
        raise ValueError("SESSION_EVIDENCE_SCHEMA_HOLD")
    canonical = []
    for value in values:
        if type(value) is not str or not SESSION_TIMESTAMP.fullmatch(value):
            raise ValueError("SESSION_TIMESTAMP_FORMAT_HOLD")
        try:
            instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("SESSION_TIMESTAMP_FORMAT_HOLD") from error
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("SESSION_TIMESTAMP_TIMEZONE_HOLD")
        canonical.append(
            instant.astimezone(TAIPEI).strftime("%Y-%m-%dT%H:%M+08:00"))
    if len(canonical) != len(set(canonical)):
        raise ValueError("DUPLICATE_SESSION_INSTANT_HOLD")
    return set(canonical)


def reconcile_opentix_price(venue_offer, *, ticket_event_url, title,
                            venue_name, normal_ticket_tiers, sessions,
                            independent_ticket_receipt_verified=False,
                            venue_sessions=None, ticket_body=None,
                            ticket_receipt=None, now=None):
    """Compare separate price and session roles; never elevate untrusted tiers.

    Ticket session prices and venue event prices are separate evidence roles.
    Passing a caller-created ticket dict is not independent HTTP attestation.
    """
    if venue_offer.get("decision") != "SOURCE_PRICE_ROLE_REVIEW_NOT_FORMAL":
        return {"decision": "HOLD", "reason": "VENUE_PRICE_NOT_QUALIFIED_HOLD"}
    linked = venue_offer["linked_ticket"]
    if ticket_event_url != linked["ticket_event_url"]:
        return {"decision": "HOLD", "reason": "TICKET_EVENT_LINK_ID_MISMATCH_HOLD"}
    if " ".join(title.split()) != " ".join(venue_offer["event_title"].split()):
        return {"decision": "HOLD", "reason": "TICKET_TITLE_MISMATCH_HOLD"}
    if venue_name != "臺北表演藝術中心":
        return {"decision": "HOLD", "reason": "TICKET_VENUE_MISMATCH_HOLD"}
    if (not isinstance(normal_ticket_tiers, (tuple, list))
            or not normal_ticket_tiers or len(normal_ticket_tiers) > 30
            or any(type(v) is not int or not 100 <= v <= MAX_PRICE_NTD
                   for v in normal_ticket_tiers)
            or len(set(normal_ticket_tiers)) != len(normal_ticket_tiers)):
        return {"decision": "HOLD", "reason": "TICKET_NORMAL_PRICE_TIERS_HOLD"}
    if (min(normal_ticket_tiers) != venue_offer["min_price_ntd"]
            or max(normal_ticket_tiers) != venue_offer["max_price_ntd"]):
        return {"decision": "HOLD", "reason": "VENUE_TICKET_PRICE_RANGE_CONFLICT_HOLD"}
    # Caller-provided sessions remain REVIEW, not ticket-body attestation.
    # Strict aware timestamps and instant-level dedup prevent unhashable
    # crashes, timezone alias mismatches and false cross-source parity.
    try:
        ticket_set = _canonical_session_instants(sessions)
        venue_set = _canonical_session_instants(venue_sessions)
    except ValueError as error:
        return {"decision": "HOLD", "reason": str(error)}
    hold = []
    if ticket_set != venue_set:
        hold.append("CROSS_SOURCE_SESSION_SET_CONFLICT_HOLD")
    # The old boolean could clear the receipt HOLD without any ticket bytes.
    # Never trust caller-asserted verification, even with matching price tiers.
    native = None
    if ticket_body is not None or ticket_receipt is not None:
        native = inspect_opentix_native_body(
            ticket_body, ticket_receipt, event_url=ticket_event_url,
            expected_title=title, now=now)
    if native is None or native["decision"] == "HOLD":
        hold.append("INDEPENDENT_TICKET_BODY_RECEIPT_REQUIRED_HOLD")
    else:
        # Even genuine ticket bytes + a claimed artifact digest prove only
        # source-bound event identity until an independent artifact readback
        # and event-local tier/session parser establish each separate role.
        hold.extend(["TICKET_ARTIFACT_INDEPENDENT_READBACK_REQUIRED_HOLD",
                     "TICKET_TIERS_NOT_NATIVE_FIELD_ATTESTED_HOLD",
                     "TICKET_SESSIONS_NOT_NATIVE_FIELD_ATTESTED_HOLD"])
    if independent_ticket_receipt_verified is True:
        hold.append("UNTRUSTED_BOOLEAN_TICKET_ATTESTATION_HOLD")
    return {
        "ticket_native_identity_review": native,
        "decision": "PRICE_RANGE_MATCH_REVIEW_NOT_FORMAL",
        "min_price_ntd": venue_offer["min_price_ntd"],
        "max_price_ntd": venue_offer["max_price_ntd"],
        "ordinary_tiers": sorted(normal_ticket_tiers),
        "same_event_relation": linked["relation"],
        "ticket_only_sessions": sorted(ticket_set - venue_set),
        "venue_only_sessions": sorted(venue_set - ticket_set),
        "held_fields": hold,
        "accepted_for_formal_publish": False,
    }
