"""Fail-closed field-level Golden-readiness contract; NEVER grants Golden acceptance."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

TICKET = "https://www.opentix.life/event/2072516129034670080"
VENUE = "https://tpac.org.taipei/program/2088"
LIST = "https://tpac.org.taipei/program"
TICKET_IMAGE = "https://s3.resource.opentix.life/upload/program/1783488303546FNFfEObGMQ.jpeg"
VENUE_IMAGE = "https://backstage.tpac-taipei.org/storage/uploads/program/images/f5182a1f85017d7b56d4643927ed8484.jpg"
READY = "READY_FOR_INDEPENDENT_GOLDEN_REVIEW"
HOLD = "HOLD"
READY_FIELDS = {
    ("A", "title"): ("EVENT_TITLE", TICKET),
    ("A", "ticket_event_url"): ("EVENT_URL", TICKET),
    ("A", "venue"): ("EVENT_VENUE", TICKET),
    ("A", "img_url"): ("OFFICIAL_IMAGE_URL", TICKET),
    ("B", "title"): ("EVENT_TITLE", VENUE),
    ("B", "venue_room"): ("VENUE_ROOM", VENUE),
    ("B", "showtimes"): ("VENUE_ANNOUNCED_SHOWTIME", VENUE),
    ("B", "direct_ticket_event_url"): ("VENUE_TO_TICKET_EVENT_EDGE", VENUE),
    ("B", "img_url"): ("OFFICIAL_IMAGE_URL", VENUE),
}
HOLD_FIELDS = {
    ("A", "age_min"), ("A", "sale_markers"), ("A", "ticket_session_id"),
    ("A", "admission_price"),
    ("B", "index_advertised_range"), ("B", "age_min"),
    ("B", "advertised_price_range"),
}
def exact_https(value, expected):
    if not isinstance(value, str): return False
    try:
        a, b = urlsplit(value), urlsplit(expected)
        return (a.scheme == b.scheme == "https" and a.netloc == b.netloc
                and a.path == b.path and not a.query and not a.fragment
                and not a.username and not a.password)
    except ValueError: return False

def validate(data):
    if not isinstance(data, dict): raise ValueError("NOT_OBJECT")
    if (data.get("kind") != "P30_L7_FIELD_GOLDEN_READINESS_V1"
        or data.get("scope") != "ISOLATED_EVIDENCE_ONLY"
        or data.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
        or any(type(data.get(k)) is not int or data[k] != 0 for k in
               ("native_official_get_this_gate", "formal_accepted_fields",
                "golden_accepted_events", "published_events"))
        or data.get("reader_is_not_native_get") is not True
        or data.get("observation_method") != "PUBLIC_INDEXED_TEXT_READER_REOBSERVATION"):
        raise ValueError("RELEASE_OR_READER_PROVENANCE_HOLD")
    sources = data.get("source_urls")
    if not isinstance(sources, dict) or sources != {"A":TICKET,"B_list":LIST,"B_detail":VENUE}:
        raise ValueError("SOURCE_ALLOWLIST_HOLD")
    identity = data.get("identity")
    if not isinstance(identity, dict) or (identity.get("canonical_ticket_platform_id") != "05"
        or identity.get("venue_source_id") != "TPAC_OFFICIAL"
        or identity.get("ticket_event_id") != "2072516129034670080"
        or identity.get("venue_detail_id") != "2088"
        or identity.get("title") != "C MUSICAL 音樂劇《小王子》"
        or not exact_https(identity.get("venue_direct_ticket_edge"), TICKET)
        or identity.get("ticket_session_id") is not None
        or identity.get("identity_decision") != "SAME_EVENT_URL_EDGE_REVIEW_NOT_SESSION"):
        raise ValueError("IDENTITY_OR_SESSION_HOLD")
    rows = data.get("field_receipts")
    if not isinstance(rows, list) or len(rows) != len(READY_FIELDS) + len(HOLD_FIELDS):
        raise ValueError("FIELD_COUNT_HOLD")
    seen = set()
    for f in rows:
        if not isinstance(f, dict): raise ValueError("FIELD_NOT_OBJECT")
        key = (f.get("line"), f.get("name"))
        if key in seen: raise ValueError("DUPLICATE_FIELD")
        seen.add(key)
        try:
            t = datetime.fromisoformat(f["observed_at"].replace("Z","+00:00"))
            if t.utcoffset() is None: raise ValueError()
        except (ValueError, TypeError, KeyError, AttributeError):
            raise ValueError("FIELD_OBSERVED_AT_HOLD")
        if not isinstance(f.get("reason"), str) or not f["reason"].strip():
            raise ValueError("FIELD_REASON_MISSING")
        if f.get("formal_accepted") is not False:
            raise ValueError("FORMAL_PROMOTION_FORBIDDEN")
        if key in READY_FIELDS:
            role, source = READY_FIELDS[key]
            if (f.get("decision") != READY or f.get("role") != role
                or not exact_https(f.get("source"), source)):
                raise ValueError("READY_SOURCE_ROLE_HOLD")
        elif key in HOLD_FIELDS:
            expected = LIST if key == ("B","index_advertised_range") else TICKET if key[0] == "A" else VENUE
            if f.get("decision") != HOLD or not exact_https(f.get("source"), expected):
                raise ValueError("HOLD_FIELD_MUST_STAY_HOLD")
        else:
            raise ValueError("UNRECOGNIZED_FIELD")
    if seen != set(READY_FIELDS) | HOLD_FIELDS: raise ValueError("MISSING_FIELD")
    by = {(x["line"],x["name"]): x["value"] for x in rows}
    if by["A","title"] != identity["title"] or by["B","title"] != identity["title"]:
        raise ValueError("TITLE_IDENTITY_MISMATCH")
    if not exact_https(by["A","ticket_event_url"],TICKET) or not exact_https(by["B","direct_ticket_event_url"],TICKET):
        raise ValueError("TICKET_EVENT_EDGE_HOLD")
    if by["A","venue"] != "臺北表演藝術中心 藍盒子" or by["B","venue_room"] != "藍盒子":
        raise ValueError("VENUE_ROOM_PARITY_HOLD")
    if by["A","age_min"] != 7 or by["B","age_min"] != 6:
        raise ValueError("AGE_CONFLICT_NOT_PRESERVED")
    if by["A","ticket_session_id"] is not None or by["A","admission_price"] is not None:
        raise ValueError("UNVERIFIED_TICKET_FIELDS")
    # Indexed same-event source-page image links are REVIEW-only; never infer Golden or download assets.
    if not exact_https(by["A","img_url"], TICKET_IMAGE) or not exact_https(by["B","img_url"], VENUE_IMAGE):
        raise ValueError("SOURCE_EVENT_IMAGE_URL_HOLD")
    if by["B","advertised_price_range"] != [1200,2200]:
        raise ValueError("VENUE_ADVERTISED_PRICE_CHANGED")
    if by["B","index_advertised_range"] != ["2026-11-04","2026-11-14"]:
        raise ValueError("INDEX_DATE_CONFLICT_NOT_PRESERVED")
    shows = by["B","showtimes"]
    if not isinstance(shows,list) or len(shows) != 12 or len(set(shows)) != 12:
        raise ValueError("VENUE_SHOWS_HOLD")
    expected_shows = ["2026-11-05T19:30:00+08:00","2026-11-06T19:30:00+08:00",
        "2026-11-07T14:30:00+08:00","2026-11-07T19:30:00+08:00",
        "2026-11-08T14:30:00+08:00","2026-11-10T19:30:00+08:00",
        "2026-11-11T19:30:00+08:00","2026-11-12T19:30:00+08:00",
        "2026-11-13T19:30:00+08:00","2026-11-14T14:30:00+08:00",
        "2026-11-14T19:30:00+08:00","2026-11-15T14:30:00+08:00"]
    if shows != expected_shows: raise ValueError("SOURCE_EXACT_SHOWTIMES_HOLD")
    for show in shows:
        try:
            dt=datetime.fromisoformat(show)
            if dt.utcoffset().total_seconds()!=28800: raise ValueError()
        except (ValueError,TypeError,AttributeError):
            raise ValueError("VENUE_SHOW_TIMEZONE_HOLD")
    return {"A_review_ready":4,"B_review_ready":5,"formal_accepted":0,
            "golden":0,"published":0,"native_get":0,
            "decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"}


def audit_l7_candidate_parity(source_contract, candidate):
    """Audit an existing L7 REVIEW candidate against independent same-event A receipts.

    Does not create a candidate, validate a live fetch, or promote any field.
    The venue B source is an identity edge, never a ticket-session/price owner.
    """
    validate(source_contract)
    from scripts.p30_candidate_review_pipeline import normalize_record
    row, failures = normalize_record(candidate)
    if failures:
        return {"decision": "HOLD", "reasons": sorted(set(failures)),
                "formal_accepted": 0, "golden": 0, "published": 0}
    receipts = {(f["line"], f["name"]): f for f in source_contract["field_receipts"]}
    venue_receipt = receipts[("A", "venue")]
    meta = row["_candidate"]
    reasons = []
    if (row["platform"] != "OPENTIX" or meta["platform_id"] != "05"
        or meta["source_event_id"] != "2072516129034670080"
        or not exact_https(row["url"], TICKET)
        or row["title"] != receipts[("A", "title")]["value"]):
        reasons.append("CANONICAL_EVENT_IDENTITY_MISMATCH")
    # A candidate may not attach extra/duplicate HTTPS sources to launder
    # unrelated event or venue evidence into this exact ticket Event ID.
    if meta.get("sources") != [TICKET]:
        reasons.append("UNVERIFIED_EXTRA_OR_DUPLICATE_SOURCE")
    # L7 may preserve the independently source-bound A venue, but it cannot
    # infer an eligible price, show date, ticket Session or cross-venue fields.
    if (row.get("location") != venue_receipt["value"]
        or meta["field_evidence"].get("location") != {
            "value": venue_receipt["value"],
            "source": TICKET,
            "observed_at": venue_receipt["observed_at"],
            "role": "EVENT_VENUE",
            "decision": "REVIEW",
        }):
        reasons.append("TICKET_OWNED_VENUE_FIELD_PARITY_HOLD")
    if (not exact_https(meta["field_evidence"].get("location", {}).get("source"), TICKET)
        or set(meta["field_evidence"]) != {"location"}):
        reasons.append("UNVERIFIED_FIELD_OWNER_OR_ROLE")
    if any(row.get(k) != "未確認" for k in ("date", "price", "description", "region")):
        reasons.append("UNVERIFIED_OPTIONAL_FIELD_IN_REVIEW")
    if (row["img_url"] is not None or row["_candidate"]["sessions"]
        or row["_candidate"]["ticket_session_id"] is not None
        or row["_candidate"]["inventory"] is not None):
        reasons.append("IMAGE_SESSION_OR_INVENTORY_NOT_INDEPENDENTLY_ACCEPTED")
    if isinstance(candidate, dict) and candidate.get("img_url"):
        reasons.append("UNVERIFIED_IMAGE_IN_RAW_CANDIDATE")
    if isinstance(candidate, dict) and any(candidate.get(k) not in (None, "", "未確認")
                                           for k in ("date", "price", "description", "region")):
        reasons.append("UNVERIFIED_RAW_OPTIONAL_FIELD")
    if (meta["formal_field_pass"] is not False
        or meta["golden_accepted"] is not False
        or meta["published"] is not False):
        reasons.append("FORMAL_PROMOTION_FORBIDDEN")
    return {"decision": "HOLD" if reasons else "REVIEW_PARITY_ONLY",
            "reasons": sorted(set(reasons)), "review_fields": ["title", "url", "location"] if not reasons else [],
            "formal_accepted": 0, "golden": 0, "published": 0}


# Independent indexed-reader KHAM/TMC edge: exact field owner, role, value and time.
# This is an isolated REVIEW contract, never an event, price or Session release.
TMC_LIST = "https://www.tmc.taipei/tw/blog/show"
TMC_DETAIL = "https://www.tmc.taipei/tw/blog/show/2026SungNien-Yu"
KHAM_DETAIL = "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2"
TMC_KHAM_TICKET_POSTER = "https://imgs2.utiki.com.tw/Data/KHAM/Images/UTK2401/P1DF32E2_Large.JPG?v=202610231202"
TMC_KHAM_VENUE_SEAT_MAP = "https://www.tmc.taipei/files/20261015113742345.jpg"
TMC_KHAM_FIELDS = {
    "ticket_title": ("A", KHAM_DETAIL, "TICKET_EVENT_TITLE", "2026 小宇 宋念宇《不，完美的人》演唱會"),
    "ticket_sale_open": ("A", KHAM_DETAIL, "TICKET_SALE_OPEN", "2026-08-22T12:00:00+08:00"),
    "ticket_age_recommendation": ("A", KHAM_DETAIL, "AGE_RECOMMENDATION_NOT_RESTRICTION", 6),
    "ticket_one_person_one_ticket": ("A", KHAM_DETAIL, "ADMISSION_RULE", True),
    "ticket_product_poster": ("A", KHAM_DETAIL, "TICKET_PRODUCT_LINKED_POSTER_REVIEW_ONLY", TMC_KHAM_TICKET_POSTER),
    "venue_title": ("B", TMC_DETAIL, "VENUE_EVENT_TITLE", "小宇 宋念宇 《不，完美的人》 演唱會"),
    "venue_showtime": ("B", TMC_DETAIL, "VENUE_ANNOUNCED_SHOWTIME", "2026-11-07T19:30:00+08:00"),
    "venue_room": ("B", TMC_DETAIL, "VENUE_ROOM", "臺北流行音樂中心 表演廳"),
    "venue_advertised_prices": ("B", TMC_DETAIL, "VENUE_ADVERTISED_PRICE_TIERS_NOT_TICKET_ELIGIBILITY", [4280,3880,3480,2880,2480,1880]),
    "venue_direct_ticket_url": ("B", TMC_DETAIL, "VENUE_TO_TICKET_PRODUCT_EDGE", KHAM_DETAIL),
    "venue_seat_map_not_poster": ("B", TMC_DETAIL, "SEAT_MAP_REJECT_AS_EVENT_POSTER", TMC_KHAM_VENUE_SEAT_MAP),
}

def exact_source_url(value, expected):
    """Preserve a canonical allowlisted PRODUCT_ID query, never strip it."""
    if not isinstance(value, str) or value != expected:
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.fragment and not parsed.username and not parsed.password
    except ValueError:
        return False

def validate_tmc_kham_receipt(evidence):
    """Reject cross-event/session, sale/show and advertised/eligible price laundering."""
    if not isinstance(evidence, dict) or evidence.get("kind") != "P30_L7_TMC_KHAM_REVIEW_EDGE_V1":
        raise ValueError("TMC_KHAM_KIND_HOLD")
    if (evidence.get("observation_method") != "PUBLIC_INDEXED_TEXT_READER_REOBSERVATION"
        or evidence.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
        or any(type(evidence.get(k)) is not int or evidence[k] != 0 for k in
               ("native_official_get", "formal_accepted_fields", "golden_accepted_events", "published_events"))):
        raise ValueError("TMC_KHAM_RELEASE_OR_NATIVE_HOLD")
    if evidence.get("sources") != {"B_list":TMC_LIST, "B_detail":TMC_DETAIL, "A_ticket":KHAM_DETAIL}:
        raise ValueError("TMC_KHAM_SOURCE_ALLOWLIST_HOLD")
    identity = evidence.get("identity")
    if (not isinstance(identity,dict) or identity.get("venue_detail_id") != "2026SungNien-Yu"
        or identity.get("ticket_product_id") != "P1DF32E2"
        or identity.get("ticket_session_id") is not None
        or identity.get("eligible_general_price") is not None
        or identity.get("image_url") is not None):
        raise ValueError("TMC_KHAM_IDENTITY_SESSION_PRICE_IMAGE_HOLD")
    receipts=evidence.get("field_receipts")
    if not isinstance(receipts,list) or len(receipts)!=len(TMC_KHAM_FIELDS):
        raise ValueError("TMC_KHAM_FIELD_COUNT_HOLD")
    seen=set()
    for f in receipts:
        if not isinstance(f,dict) or f.get("name") not in TMC_KHAM_FIELDS:
            raise ValueError("TMC_KHAM_UNKNOWN_FIELD")
        name=f["name"]
        if name in seen: raise ValueError("TMC_KHAM_DUPLICATE_FIELD")
        seen.add(name)
        line,source,role,value=TMC_KHAM_FIELDS[name]
        if (f.get("line")!=line or not exact_source_url(f.get("source"),source)
            or f.get("role")!=role or type(f.get("value")) is not type(value)
            or f.get("value")!=value
            or f.get("decision")!=("REJECT_FOR_EVENT_POSTER" if name=="venue_seat_map_not_poster" else "REVIEW")
            or f.get("formal_accepted") is not False):
            raise ValueError("TMC_KHAM_FIELD_OWNER_ROLE_VALUE_HOLD")
        try:
            stamp=datetime.fromisoformat(f["observed_at"].replace("Z","+00:00"))
            if stamp.utcoffset() is None: raise ValueError()
        except (ValueError,TypeError,KeyError,AttributeError):
            raise ValueError("TMC_KHAM_TIMESTAMP_HOLD")
    if seen!=set(TMC_KHAM_FIELDS): raise ValueError("TMC_KHAM_MISSING_FIELD")
    return {"A_review":5,"B_review":5,"B_rejected_as_poster":1,"formal_accepted":0,"golden":0,
            "published":0,"native_get":0,"decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"}



# 2026-11-03 A/B source rotation: distinguish advertised admission from restricted
# categories, transaction fees, bundles and image roles. Indexed-reader REVIEW
# evidence only; no ticket checkout, inventory, native GET or Golden promotion.
TIX_FOREVER = "https://tixcraft.com/activity/detail/26_forever"
TMC_SCENE = "https://www.tmc.taipei/tw/blog/show/2026SingTheScene"
TMC_SCENE_POSTER = "https://www.tmc.taipei/files/20260916122654324.png"
TMC_SCENE_SEAT_MAP = "https://www.tmc.taipei/files/20261015113836233.jpg"
ROTATION_FIELDS = {
    "ticket_showtimes": ("A", TIX_FOREVER, "TICKET_ANNOUNCED_SHOWTIMES", ["2026-11-28T19:00:00+08:00", "2026-11-29T19:00:00+08:00"], "REVIEW"),
    "ticket_standard_advertised_tiers": ("A", TIX_FOREVER, "TICKET_ADVERTISED_STANDARD_TIERS_NOT_STOCK", [5880,5280,4880,4280,3680,3280,2680,1680], "REVIEW"),
    "ticket_disability_restricted_tiers": ("A", TIX_FOREVER, "TICKET_RESTRICTED_DISABILITY_TIERS", [2440,1840], "REVIEW"),
    "ticket_ibon_pickup_fee": ("A", TIX_FOREVER, "TICKET_COLLECTION_FEE_NOT_ADMISSION", 30, "REJECT_FOR_ADMISSION_PRICE"),
    "ticket_bank_transfer_fee": ("A", TIX_FOREVER, "CONDITIONAL_BANK_FEE_NOT_ADMISSION", 15, "REJECT_FOR_ADMISSION_PRICE"),
    "venue_showtime": ("B", TMC_SCENE, "VENUE_ANNOUNCED_SHOWTIME", "2026-11-21T19:30:00+08:00", "REVIEW"),
    "venue_room": ("B", TMC_SCENE, "VENUE_ROOM", "臺北流行音樂中心 Legacy TERA", "REVIEW"),
    "venue_standard_presale_tiers": ("B", TMC_SCENE, "VENUE_ADVERTISED_STANDARD_PRESELL_NOT_STOCK", [1600,1200,800], "REVIEW"),
    "venue_accessibility_restricted_tiers": ("B", TMC_SCENE, "VENUE_RESTRICTED_ACCESSIBILITY_TIERS", [800,600,400], "REVIEW"),
    "venue_cassette_bundle_tiers": ("B", TMC_SCENE, "VENUE_CONDITIONAL_MERCH_BUNDLE_TIERS", [1799,1399,999], "REJECT_FOR_BASE_ADMISSION"),
    "venue_ticket_platform_claim": ("B", TMC_SCENE, "VENUE_CLAIMED_TICKET_PLATFORM_NOT_EVENT_ID", "Klook", "REVIEW"),
    "venue_event_poster": ("B", TMC_SCENE, "VENUE_EVENT_POSTER_LINK_REVIEW_ONLY", TMC_SCENE_POSTER, "REVIEW"),
    "venue_seating_chart": ("B", TMC_SCENE, "SEAT_MAP_NOT_EVENT_POSTER", TMC_SCENE_SEAT_MAP, "REJECT_FOR_EVENT_POSTER"),
}

def validate_role_rotation_receipt(evidence):
    """Fail closed on identity, source, role, value, image and release claims."""
    if not isinstance(evidence, dict) or evidence.get("kind") != "P30_L7_A_B_ROLE_ROTATION_REVIEW_V1":
        raise ValueError("ROTATION_KIND_HOLD")
    if (evidence.get("observation_method") != "PUBLIC_INDEXED_TEXT_READER_REOBSERVATION"
        or evidence.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
        or any(type(evidence.get(k)) is not int or evidence[k] != 0 for k in
               ("native_official_get", "formal_accepted_fields", "golden_accepted_events", "published_events"))):
        raise ValueError("ROTATION_RELEASE_HOLD")
    if evidence.get("sources") != {"A_detail":TIX_FOREVER,"B_list":TMC_LIST,"B_detail":TMC_SCENE}:
        raise ValueError("ROTATION_SOURCES_HOLD")
    identity=evidence.get("identity")
    if identity != {"A_canonical_platform_id":"03","A_event_path":"26_forever",
                    "B_venue_detail_id":"2026SingTheScene","A_ticket_session_id":None,
                    "B_ticket_event_id":None,"B_ticket_session_id":None,
                    "formal_eligible_min_price":None,"formal_img_url":None,
                    "cross_event_identity_merge":False}:
        raise ValueError("ROTATION_IDENTITY_HOLD")
    receipts=evidence.get("field_receipts")
    if not isinstance(receipts,list) or len(receipts)!=len(ROTATION_FIELDS):
        raise ValueError("ROTATION_COUNT_HOLD")
    seen=set()
    for row in receipts:
        if not isinstance(row,dict) or row.get("name") not in ROTATION_FIELDS:
            raise ValueError("ROTATION_UNKNOWN_FIELD_HOLD")
        name=row["name"]
        if name in seen: raise ValueError("ROTATION_DUPLICATE_FIELD_HOLD")
        seen.add(name)
        line,source,role,value,decision=ROTATION_FIELDS[name]
        if (row.get("line")!=line or not exact_source_url(row.get("source"),source)
            or row.get("role")!=role or type(row.get("value")) is not type(value)
            or row.get("value")!=value or row.get("decision")!=decision
            or row.get("formal_accepted") is not False):
            raise ValueError("ROTATION_ROLE_VALUE_PROVENANCE_HOLD")
        try:
            stamp=datetime.fromisoformat(row["observed_at"].replace("Z","+00:00"))
            if stamp.utcoffset() is None: raise ValueError()
        except (ValueError,TypeError,KeyError,AttributeError):
            raise ValueError("ROTATION_TIMESTAMP_HOLD")
    if seen!=set(ROTATION_FIELDS): raise ValueError("ROTATION_MISSING_FIELD_HOLD")
    return {"A_review":3,"A_rejected_as_admission":2,"B_review":6,
            "B_rejected_as_base_or_poster":2,"native_get":0,"formal_accepted":0,
            "golden":0,"published":0,"decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"}



# 2026-11-03 03:54 independent ticket/venue cross-source identity evidence.
# This is indexed public evidence, not native GET, ticket Session, checkout or Golden.
KLOOK_SCENE = "https://www.klook.com/zh-TW/event-detail/102001087-2026-singoursongs-concert-tmc/"
TICKET_BRIDGE_FIELDS = {
    "ticket_initial_general_sale": ("A", TIX_FOREVER, "TICKET_GENERAL_SALE_START_NOT_SHOW", "2026-10-04T14:00:00+08:00", "REVIEW"),
    "ticket_partial_release": ("A", TIX_FOREVER, "TICKET_PARTIAL_RELEASE_NOTICE_NOT_SHOW", "2026-10-13T18:00:00+08:00", "REVIEW"),
    "ticket_partial_release_not_inventory": ("A", TIX_FOREVER, "RELEASE_NOTICE_NOT_CURRENT_INVENTORY", True, "REJECT_FOR_STOCK"),
    "klook_ticket_event_url": ("B", KLOOK_SCENE, "INDEPENDENT_SAME_EVENT_TICKET_DETAIL_URL_NOT_SESSION", KLOOK_SCENE, "REVIEW"),
    "klook_event_title": ("B", KLOOK_SCENE, "TICKET_EVENT_TITLE_SAME_EVENT_REVIEW", "2026〖唱 我們的歌〗金曲再現 演唱會｜我的電影K歌時代", "REVIEW"),
    "klook_showtime": ("B", KLOOK_SCENE, "TICKET_ANNOUNCED_SHOWTIME_NOT_SESSION", "2026-11-21T19:30:00+08:00", "REVIEW"),
    "klook_venue": ("B", KLOOK_SCENE, "TICKET_EVENT_VENUE", "Legacy TERA", "REVIEW"),
    "klook_standard_tiers": ("B", KLOOK_SCENE, "TICKET_ADVERTISED_STANDARD_TIERS_NOT_STOCK", [1600,1200,800], "REVIEW"),
    "klook_accessibility_tiers": ("B", KLOOK_SCENE, "TICKET_RESTRICTED_ACCESSIBILITY_TIERS", [800,600,400], "REVIEW"),
    "klook_bundle_tiers": ("B", KLOOK_SCENE, "TICKET_BUNDLE_TIERS_NOT_BASE_ADMISSION", [1799,1399,999], "REJECT_FOR_BASE_ADMISSION"),
    "klook_display_range": ("B", KLOOK_SCENE, "MIXED_PACKAGE_RANGE_NOT_ELIGIBLE_CHECKOUT_MIN", [800,1799], "REJECT_FOR_ELIGIBLE_MIN"),
}

def validate_ticket_bridge_receipt(evidence):
    """Require exact independent ticket Event identity, role and source ownership."""
    if not isinstance(evidence, dict) or evidence.get("kind") != "P30_L7_A_B_INDEPENDENT_TICKET_BRIDGE_V1":
        raise ValueError("BRIDGE_KIND_HOLD")
    if (evidence.get("observation_method") != "PUBLIC_INDEXED_TEXT_READER_REOBSERVATION"
        or evidence.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
        or any(type(evidence.get(k)) is not int or evidence[k] != 0 for k in
               ("native_official_get", "formal_accepted_fields", "golden_accepted_events", "published_events"))):
        raise ValueError("BRIDGE_RELEASE_HOLD")
    if evidence.get("sources") != {"A_ticket_detail":TIX_FOREVER,
                                    "B_venue_detail":TMC_SCENE,
                                    "B_ticket_detail":KLOOK_SCENE}:
        raise ValueError("BRIDGE_SOURCE_ALLOWLIST_HOLD")
    if evidence.get("identity") != {
        "A_event_path":"26_forever", "A_ticket_session_id":None,
        "B_venue_detail_id":"2026SingTheScene", "B_ticket_event_id":"102001087",
        "B_ticket_session_id":None, "B_venue_direct_href_verified":False,
        "B_same_event_evidence":"INDEPENDENT_TITLE_SHOWTIME_VENUE_ORGANIZER_PARITY_REVIEW",
        "formal_eligible_min_price":None, "formal_img_url":None,
        "cross_event_identity_merge":False}:
        raise ValueError("BRIDGE_IDENTITY_OR_SESSION_HOLD")
    rows=evidence.get("field_receipts")
    if not isinstance(rows,list) or len(rows)!=len(TICKET_BRIDGE_FIELDS):
        raise ValueError("BRIDGE_COUNT_HOLD")
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or row.get("name") not in TICKET_BRIDGE_FIELDS:
            raise ValueError("BRIDGE_UNKNOWN_FIELD_HOLD")
        name=row["name"]
        if name in seen: raise ValueError("BRIDGE_DUPLICATE_FIELD_HOLD")
        seen.add(name)
        line,source,role,value,decision=TICKET_BRIDGE_FIELDS[name]
        if (row.get("line")!=line or not exact_source_url(row.get("source"),source)
            or row.get("role")!=role or type(row.get("value")) is not type(value)
            or row.get("value")!=value or row.get("decision")!=decision
            or row.get("formal_accepted") is not False):
            raise ValueError("BRIDGE_SOURCE_ROLE_VALUE_HOLD")
        try:
            dt=datetime.fromisoformat(row["observed_at"].replace("Z","+00:00"))
            if dt.utcoffset() is None: raise ValueError()
        except (ValueError,TypeError,KeyError,AttributeError):
            raise ValueError("BRIDGE_TIMESTAMP_HOLD")
    if seen!=set(TICKET_BRIDGE_FIELDS):
        raise ValueError("BRIDGE_MISSING_FIELD_HOLD")
    return {"A_review":2,"A_reject_stock":1,"B_review":6,"B_reject_price":2,
            "B_ticket_event_id_review":"102001087","B_ticket_session_id":None,
            "native_get":0,"formal_accepted":0,"golden":0,"published":0,
            "decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"}


def main():
    path = Path(__file__).resolve().parents[1] / "tests/p30/fixtures/p30_l7_prince_field_readiness.json"
    print(json.dumps(validate(json.loads(path.read_text(encoding="utf-8"))),sort_keys=True))
if __name__ == "__main__": main()
