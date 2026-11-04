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



# 2026-11-03 04:58 source re-observation: separate ticket payment reconciliation
# from sale/session/stock, and Klook entrance/presale/2-person bundle from show
# and single-ticket price. Venue's actual shortlink is not a verified redirect.
TMC_KLOOK_SHORTLINK = "https://s.klook.com/c/mXkdqlAMyQ"
TIMELINE_PACKAGE_FIELDS = {
    "ticket_failed_payment_window": ("A", TIX_FOREVER, "FAILED_PAYMENT_RECONCILIATION_NOT_SESSION", ["2026-10-04T14:00:00+08:00","2026-10-04T14:30:00+08:00"], "REJECT_FOR_TICKET_SESSION"),
    "ticket_oct4_release_notice": ("A", TIX_FOREVER, "ACCOUNT_RECONCILIATION_RELEASE_NOT_CURRENT_STOCK", "2026-10-04T17:00:00+08:00", "REJECT_FOR_STOCK"),
    "venue_klook_shortlink": ("B", TMC_SCENE, "VENUE_TICKET_SHORTLINK_FINAL_EVENT_DESTINATION_UNVERIFIED", TMC_KLOOK_SHORTLINK, "HOLD_FOR_FINAL_DESTINATION"),
    "klook_entrance_time": ("B", KLOOK_SCENE, "DOORS_OPEN_NOT_SHOWTIME", "2026-11-21T18:30:00+08:00", "REVIEW"),
    "klook_presale_start": ("B", KLOOK_SCENE, "TICKET_PRESELL_START_NOT_SHOWTIME", "2026-09-09T18:00:00+08:00", "REVIEW"),
    "klook_presale_end": ("B", KLOOK_SCENE, "TICKET_PRESELL_END_NOT_SHOWTIME", "2026-11-20T23:59:00+08:00", "REVIEW"),
    "klook_two_person_bundle_total": ("B", KLOOK_SCENE, "TWO_TICKET_PACKAGE_TOTAL_NOT_SINGLE_ADMISSION", [3200,2400], "REJECT_FOR_SINGLE_ADMISSION"),
    "klook_two_person_bundle_quantity": ("B", KLOOK_SCENE, "TWO_TICKETS_PER_PACKAGE_NOT_ONE", 2, "REVIEW"),
    "klook_accessibility_cassette_bundle": ("B", KLOOK_SCENE, "ACCESSIBILITY_PLUS_MERCH_NOT_GENERAL_ADMISSION", [999,799,599], "REJECT_FOR_GENERAL_PRICE"),
}

def validate_timeline_package_receipt(evidence):
    """Require exact A/B source ownership; never promote sale/doors/package to Golden."""
    if not isinstance(evidence, dict) or evidence.get("kind") != "P30_L7_A_B_TIMELINE_PACKAGE_REVIEW_V1":
        raise ValueError("TIMELINE_PACKAGE_KIND_HOLD")
    if (evidence.get("observation_method") != "PUBLIC_INDEXED_TEXT_READER_REOBSERVATION"
        or evidence.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
        or any(type(evidence.get(k)) is not int or evidence[k] != 0 for k in
               ("native_official_get", "formal_accepted_fields", "golden_accepted_events", "published_events"))):
        raise ValueError("TIMELINE_PACKAGE_RELEASE_HOLD")
    if evidence.get("sources") != {"A_ticket_detail":TIX_FOREVER,
                                   "B_venue_detail":TMC_SCENE,
                                   "B_ticket_detail":KLOOK_SCENE}:
        raise ValueError("TIMELINE_PACKAGE_SOURCES_HOLD")
    if evidence.get("identity") != {
        "A_event_path":"26_forever", "A_ticket_session_id":None,
        "B_venue_detail_id":"2026SingTheScene", "B_ticket_event_id":"102001087",
        "B_ticket_session_id":None, "B_shortlink_final_destination_verified":False,
        "B_checkout_eligible_single_ticket_min":None, "formal_img_url":None,
        "cross_event_identity_merge":False}:
        raise ValueError("TIMELINE_PACKAGE_IDENTITY_HOLD")
    rows=evidence.get("field_receipts")
    if not isinstance(rows,list) or len(rows)!=len(TIMELINE_PACKAGE_FIELDS):
        raise ValueError("TIMELINE_PACKAGE_COUNT_HOLD")
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or row.get("name") not in TIMELINE_PACKAGE_FIELDS:
            raise ValueError("TIMELINE_PACKAGE_UNKNOWN_FIELD_HOLD")
        name=row["name"]
        if name in seen: raise ValueError("TIMELINE_PACKAGE_DUPLICATE_FIELD_HOLD")
        seen.add(name)
        line,source,role,value,decision=TIMELINE_PACKAGE_FIELDS[name]
        if (row.get("line")!=line or not exact_source_url(row.get("source"),source)
            or row.get("role")!=role or type(row.get("value")) is not type(value)
            or row.get("value")!=value or row.get("decision")!=decision
            or row.get("formal_accepted") is not False):
            raise ValueError("TIMELINE_PACKAGE_ROLE_VALUE_HOLD")
        try:
            stamp=datetime.fromisoformat(row["observed_at"].replace("Z","+00:00"))
            if stamp.utcoffset() is None: raise ValueError()
        except (ValueError,TypeError,KeyError,AttributeError):
            raise ValueError("TIMELINE_PACKAGE_TIMESTAMP_HOLD")
    if seen!=set(TIMELINE_PACKAGE_FIELDS): raise ValueError("TIMELINE_PACKAGE_MISSING_FIELD_HOLD")
    return {"A_rejected_session_or_stock":2,"B_review":4,"B_shortlink_hold":1,
            "B_rejected_general_price":2,"native_get":0,"formal_accepted":0,
            "golden":0,"published":0,"decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"}


# 2026-11-03 05:55 Asia/Taipei: rotate BOTH workstreams to independent
# canonical sources. Indexed public source reads are not native GET or Golden.
# A same-ID detail/GAME conflicts with body and poster time (19:30 vs 19:00).
# B venue rid=160668 directly links KKTIX, which distinguishes 3 ticket
# options, 2 SHOW dates, FC-only two-day pass and restricted admission.
MYCELIUM_DETAIL = "https://www.indievox.com/activity/detail/26_iv04256e8"
MYCELIUM_GAME = "https://www.indievox.com/activity/game/26_iv04256e8"
MYCELIUM_POSTER = "https://indievox.static.tixcraft.com/images/activity/26_iv04256e8_37bc28c64de943aeb6fecf15fd7916a6.jpg"
ZEPP_TAKASE_LIST = "https://www.zepp.co.jp/hall/newtaipei/"
ZEPP_TAKASE_DETAIL = "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=160668"
KKTIX_TAKASE = "https://freeplanetml.kktix.cc/events/takasetoya202611"
ZEPP_TAKASE_POSTER = "https://www.zepp.co.jp/data/Reserved/image_160668_1"
KKTIX_TAKASE_POSTER = "https://assets.kktix.io/organization_resource_files/7267/80108/6c8115f58e266791.jpg"
ROTATED_EVENT_FIELDS = {
    "a_event_title": ("A",MYCELIUM_DETAIL,"SAME_ID_EVENT_TITLE","菌網 MYCELIUM","REVIEW"),
    "a_header_show": ("A",MYCELIUM_DETAIL,"HEADER_SHOWTIME_CONFLICT_NOT_FORMAL","2026-11-13T19:30:00+08:00","REVIEW"),
    "a_game_show": ("A",MYCELIUM_GAME,"SAME_ID_GAME_ROW_SHOWTIME_NOT_CHECKOUT","2026-11-13T19:30:00+08:00","REVIEW"),
    "a_body_show": ("A",MYCELIUM_DETAIL,"BODY_SHOWTIME_CONFLICT_WITH_HEADER_GAME_POSTER","2026-11-13T19:00:00+08:00","HOLD_CONFLICT"),
    "a_single_presale": ("A",MYCELIUM_DETAIL,"ADVERTISED_SINGLE_PRESELL_NOT_STOCK",700,"REVIEW"),
    "a_two_person_total": ("A",MYCELIUM_DETAIL,"TWO_PERSON_BUNDLE_NOT_SINGLE_PRICE",1200,"REJECT_FOR_SINGLE_MIN"),
    "a_accessibility": ("A",MYCELIUM_DETAIL,"RESTRICTED_ACCESSIBILITY_NOT_GENERAL",350,"REJECT_FOR_GENERAL_MIN"),
    "a_event_poster": ("A",MYCELIUM_DETAIL,"SOURCE_LINKED_POSTER_TIME_CONFLICT_REVIEW_ONLY",MYCELIUM_POSTER,"REVIEW"),
    "a_ticket_session": ("A",MYCELIUM_GAME,"TICKET_SESSION_ID_NOT_VISIBLE",None,"HOLD"),
    "b_venue_shows": ("B",ZEPP_TAKASE_DETAIL,"VENUE_ANNOUNCED_TWO_SHOWS_NOT_TICKET_SESSIONS",["2026-11-07T18:00:00+08:00","2026-11-08T17:00:00+08:00"],"REVIEW"),
    "b_direct_ticket_event": ("B",ZEPP_TAKASE_DETAIL,"DIRECT_KKTIX_EVENT_URL_NOT_SESSION",KKTIX_TAKASE,"REVIEW"),
    "b_ticket_options": ("B",KKTIX_TAKASE,"KKTIX_THREE_DISTINCT_TICKET_OPTIONS_NOT_SESSION_IDS",["TWO_DAY_PASS","NOV_07_SINGLE_DAY","NOV_08_SINGLE_DAY"],"REVIEW"),
    "b_kktix_showtimes": ("B",KKTIX_TAKASE,"TICKET_ANNOUNCED_SHOWTIMES_NOT_STOCK",["2026-11-07T18:00:00+08:00","2026-11-08T17:00:00+08:00"],"REVIEW"),
    "b_general_single": ("B",KKTIX_TAKASE,"SINGLE_DAY_GENERAL_ADVERTISED_NOT_CHECKOUT",1480,"REVIEW"),
    "b_fanclub_two_day": ("B",KKTIX_TAKASE,"FC_RESTRICTED_TWO_DAY_PASS_NOT_SINGLE_ADMISSION",2600,"REJECT_FOR_SINGLE_MIN"),
    "b_accessibility": ("B",KKTIX_TAKASE,"RESTRICTED_ACCESSIBILITY_NOT_GENERAL",900,"REJECT_FOR_GENERAL_MIN"),
    "b_pickup_fee": ("B",KKTIX_TAKASE,"PER_ORDER_PICKUP_FEE_NOT_ADMISSION",30,"REJECT_FOR_ADMISSION"),
    "b_venue_poster": ("B",ZEPP_TAKASE_DETAIL,"VENUE_EVENT_POSTER_REVIEW_ONLY",ZEPP_TAKASE_POSTER,"REVIEW"),
    "b_ticket_poster": ("B",KKTIX_TAKASE,"TICKET_EVENT_POSTER_REVIEW_ONLY",KKTIX_TAKASE_POSTER,"REVIEW"),
    "b_ticket_session": ("B",KKTIX_TAKASE,"TICKET_SESSION_ID_NOT_IN_INDEXED_TEXT",None,"HOLD"),
    "b_current_stock": ("B",KKTIX_TAKASE,"LIVE_INVENTORY_UNVERIFIED",None,"HOLD"),
    # 2026-11-03 07:00 public indexed reader: three KKTIX option-specific
    # registration hrefs were observed, but each GET returned HTTP 403.
    # Route identity is not a checkout Session ID or evidence of stock.
    "a_explicit_start_time_conflict": ("A",MYCELIUM_DETAIL,"OFFICIAL_BODY_EXPLICIT_START_1900_VS_HEADER_GAME_1930","開演時間為 19：00","HOLD_CONFLICT"),
    "b_kktix_two_day_registration": ("B",KKTIX_TAKASE,"TWO_DAY_OPTION_REGISTRATION_HREF_403_NOT_SESSION","https://kktix.com/events/takasetoya202611-1/registrations/new","HOLD_403"),
    "b_kktix_nov07_registration": ("B",KKTIX_TAKASE,"NOV07_OPTION_REGISTRATION_HREF_403_NOT_SESSION","https://kktix.com/events/takasetoya202611-2/registrations/new","HOLD_403"),
    "b_kktix_nov08_registration": ("B",KKTIX_TAKASE,"NOV08_OPTION_REGISTRATION_HREF_403_NOT_SESSION","https://kktix.com/events/takasetoya202611-3/registrations/new","HOLD_403"),
}

def validate_rotated_event_receipt(evidence):
    """Strict A/B exact event, source, role and price receipt; never publishes."""
    if not isinstance(evidence,dict) or evidence.get("kind")!="P30_L7_A_B_SOURCE_ROTATION_V1":
        raise ValueError("ROTATION_KIND_HOLD")
    if (evidence.get("observation_method")!="PUBLIC_INDEXED_TEXT_READER_REOBSERVATION"
        or evidence.get("release_state")!="HARD_HOLD_NO_PUBLICATION"
        or any(type(evidence.get(k)) is not int or evidence[k]!=0 for k in
               ("native_official_get","formal_accepted_fields","golden_accepted_events","published_events"))):
        raise ValueError("ROTATION_RELEASE_OR_NATIVE_HOLD")
    if evidence.get("sources")!={"A_detail":MYCELIUM_DETAIL,"A_game":MYCELIUM_GAME,
                                  "B_venue_list":ZEPP_TAKASE_LIST,"B_venue_detail":ZEPP_TAKASE_DETAIL,
                                  "B_ticket_detail":KKTIX_TAKASE}:
        raise ValueError("ROTATION_SOURCE_ALLOWLIST_HOLD")
    if evidence.get("identity")!={"A_event_id":"26_iv04256e8","A_game_event_id":"26_iv04256e8",
        "A_header_game_time_conflict_with_body_poster":True,"A_ticket_session_id":None,
        "B_venue_rid":"160668","B_ticket_event_url":KKTIX_TAKASE,
        "B_ticket_session_id":None,"B_fanclub_two_day_is_single_day":False,
        "formal_eligible_checkout_min":None,"formal_img_url":None,
        "cross_event_identity_merge":False}:
        raise ValueError("ROTATION_IDENTITY_CONFLICT_OR_SESSION_HOLD")
    rows=evidence.get("field_receipts")
    if not isinstance(rows,list) or len(rows)!=len(ROTATED_EVENT_FIELDS):
        raise ValueError("ROTATION_FIELD_COUNT_HOLD")
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or row.get("name") not in ROTATED_EVENT_FIELDS:
            raise ValueError("ROTATION_UNKNOWN_FIELD_HOLD")
        name=row["name"]
        if name in seen: raise ValueError("ROTATION_DUPLICATE_FIELD_HOLD")
        seen.add(name)
        line,source,role,value,decision=ROTATED_EVENT_FIELDS[name]
        if (row.get("line")!=line or not exact_source_url(row.get("source"),source)
            or row.get("role")!=role or type(row.get("value")) is not type(value)
            or row.get("value")!=value or row.get("decision")!=decision
            or row.get("formal_accepted") is not False):
            raise ValueError("ROTATION_SOURCE_ROLE_VALUE_HOLD")
        try:
            stamp=datetime.fromisoformat(row["observed_at"].replace("Z","+00:00"))
            if stamp.utcoffset() is None: raise ValueError()
        except (ValueError,TypeError,KeyError,AttributeError):
            raise ValueError("ROTATION_TIMESTAMP_HOLD")
    if seen!=set(ROTATED_EVENT_FIELDS): raise ValueError("ROTATION_MISSING_FIELD_HOLD")
    return {"A_review":5,"A_conflict_hold":1,"A_explicit_start_conflict_hold":1,"A_reject_general_price":2,"A_session_hold":1,
            "B_review":7,"B_reject_general_price":3,"B_session_stock_hold":2,"B_registration_href_403_hold":3,
            "native_get":0,"formal_accepted":0,"golden":0,"published":0,
            "decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"}



# 2026-11-03 07:55 Asia/Taipei. Public indexed official ticket detail and
# Taipei Dome calendar: same title/dates/venue REVIEW, not a direct ID edge.
# A 19:00 SHOW cannot be inferred from B calendar date; 11/12-15 is another event.
DOME_TICKET = "https://tixcraft.com/activity/detail/26_forever"
DOME_CALENDAR = "https://www.taipeidome.com.tw/Web/dome/"
DOME_FIELDS = {
    "a_event_id": ("A", DOME_TICKET, "TICKET_EVENT_ID", "26_forever", "REVIEW"),
    "a_shows": ("A", DOME_TICKET, "TICKET_SHOW_TIMES_NOT_STOCK",
                ["2026-11-28T19:00:00+08:00", "2026-11-29T19:00:00+08:00"], "REVIEW"),
    "a_general_prices": ("A", DOME_TICKET, "ADVERTISED_GENERAL_NOT_CHECKOUT",
                         [5880,5280,4880,4280,3680,3280,2680,1680], "REVIEW"),
    "a_accessibility": ("A", DOME_TICKET, "RESTRICTED_NOT_GENERAL", [2440,1840], "REJECT_GENERAL_MIN"),
    "a_ibon_fee": ("A", DOME_TICKET, "PER_ORDER_PICKUP_NOT_ADMISSION", 30, "REJECT_ADMISSION"),
    "a_age_advisory": ("A", DOME_TICKET, "UNDER_SEVEN_NOT_RECOMMENDED_NOT_BANNED", 7, "REVIEW"),
    "a_child_companion": ("A", DOME_TICKET, "TWELVE_AND_UNDER_REQUIRES_ADULT", 12, "REVIEW"),
    "a_session": ("A", DOME_TICKET, "CHECKOUT_SESSION_UNVERIFIED", None, "HOLD"),
    "a_stock": ("A", DOME_TICKET, "ELIGIBLE_STOCK_UNVERIFIED", None, "HOLD"),
    "b_calendar_title": ("B", DOME_CALENDAR, "VENUE_CALENDAR_TITLE_SHUTTLE_SUFFIX",
        "F✦FOREVER 恆星之城・光年赴約・臺北 限定場演唱會〖活動加開2線接駁車〗", "REVIEW"),
    "b_dates": ("B", DOME_CALENDAR, "CALENDAR_DATES_NOT_SHOW_TIMES", ["2026-11-28","2026-11-29"], "REVIEW"),
    "b_other_event": ("B", DOME_CALENDAR, "DISTINCT_EVENT_NOV12_15",
        ["2026-11-12","2026-11-13","2026-11-14","2026-11-15"], "REJECT_CROSS_EVENT"),
    "b_shuttle": ("B", DOME_CALENDAR, "SHUTTLE_ROUTES_NOT_SESSIONS", 2, "REJECT_SESSION"),
    "b_ticket_href": ("B", DOME_CALENDAR, "DIRECT_TICKET_HREF_UNVERIFIED", None, "HOLD"),
    "b_show_time": ("B", DOME_CALENDAR, "VENUE_CALENDAR_TIME_UNVERIFIED", None, "HOLD"),
    "b_img_url": ("B", DOME_CALENDAR, "FORMAL_HERO_IMAGE_UNVERIFIED", None, "HOLD"),
}

def validate_dome_crosscheck(e):
    """Source/role/identity fail-closed contract; cannot authorize Golden."""
    if not isinstance(e, dict) or e.get("kind") != "P30_L7_DOME_CROSSCHECK_V1":
        raise ValueError("DOME_KIND_HOLD")
    if (e.get("scope") != "ISOLATED_EVIDENCE_ONLY"
        or e.get("observation_method") != "PUBLIC_INDEXED_TEXT_READER_REOBSERVATION"
        or e.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
        or any(type(e.get(k)) is not int or e[k] != 0 for k in
               ("native_official_get","formal_accepted_fields","golden_accepted_events","published_events"))):
        raise ValueError("DOME_RELEASE_HOLD")
    if e.get("sources") != {"A":DOME_TICKET,"B":DOME_CALENDAR}:
        raise ValueError("DOME_SOURCE_HOLD")
    if e.get("identity") != {
        "A_platform_id":"03","A_ticket_event_id":"26_forever",
        "B_venue_source":"TAIPEI_DOME_OFFICIAL_NOT_FORMAL_19",
        "B_calendar_event_id":None,"B_direct_ticket_href":None,
        "B_calendar_show_time":None,"ticket_session_id":None,
        "formal_eligible_min":None,"formal_img_url":None,
        "cross_source_identity":"TITLE_DATES_VENUE_REVIEW_NO_DIRECT_ID_EDGE",
        "cross_event_merge":False}:
        raise ValueError("DOME_IDENTITY_HOLD")
    rows=e.get("field_receipts")
    if not isinstance(rows,list) or len(rows)!=len(DOME_FIELDS):
        raise ValueError("DOME_COUNT_HOLD")
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or row.get("name") not in DOME_FIELDS:
            raise ValueError("DOME_UNKNOWN_FIELD_HOLD")
        name=row["name"]
        if name in seen: raise ValueError("DOME_DUPLICATE_HOLD")
        seen.add(name)
        line,source,role,value,decision=DOME_FIELDS[name]
        if (row.get("line")!=line or not exact_https(row.get("source"),source)
            or row.get("role")!=role or type(row.get("value")) is not type(value)
            or row.get("value")!=value or row.get("decision")!=decision
            or row.get("formal_accepted") is not False
            or not isinstance(row.get("reason"),str) or not row["reason"].strip()):
            raise ValueError("DOME_FIELD_OR_PROMOTION_HOLD")
        try:
            dt=datetime.fromisoformat(row["observed_at"].replace("Z","+00:00"))
            if dt.utcoffset() is None: raise ValueError()
        except (ValueError,TypeError,KeyError,AttributeError):
            raise ValueError("DOME_TIMESTAMP_HOLD")
    if seen!=set(DOME_FIELDS): raise ValueError("DOME_MISSING_HOLD")
    return {"A_review":5,"A_reject":2,"A_hold":2,
            "B_review":2,"B_reject":2,"B_hold":3,
            "native_get":0,"formal_accepted":0,"golden":0,"published":0,
            "decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"}



# 2026-11-03: Independent indexed official source review, no native GET.
# A: TMC venue exact direct KHAM PRODUCT_ID edge; B: TWTC same-site
# exhibition LIST -> id=29418 DETAIL with explicit opening hours.
# This is a readiness matrix, NOT a Golden decision or release permission.
PUBLIC_KHAM_PRODUCT = "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2"
PUBLIC_TMC_LIST = "https://www.tmc.taipei/tw/blog/show"
PUBLIC_TMC_DETAIL = "https://www.tmc.taipei/tw/blog/show/2026SungNien-Yu"
PUBLIC_TWTC_LIST = "https://twtc.com.tw/exhibition?p=home"
PUBLIC_TWTC_DETAIL = "https://twtc.com.tw/exhibition_more.aspx?id=29418&p=home"
PUBLIC_NON_SESSION_FIELDS = {
    "a_kham_title": ("A", PUBLIC_KHAM_PRODUCT, "TICKET_EVENT_TITLE",
                     "2026 小宇 宋念宇《不，完美的人》演唱會", "REVIEW"),
    "a_venue_direct_ticket_href": ("A", PUBLIC_TMC_DETAIL, "EXACT_VENUE_TO_TICKET_PRODUCT_EDGE",
                                   PUBLIC_KHAM_PRODUCT, "REVIEW"),
    "a_venue_showtime": ("A", PUBLIC_TMC_DETAIL, "VENUE_ANNOUNCED_SHOWTIME",
                         "2026-11-07T19:30:00+08:00", "REVIEW"),
    "a_venue_hall": ("A", PUBLIC_TMC_DETAIL, "VENUE_HALL",
                     "臺北流行音樂中心 表演廳", "REVIEW"),
    "a_ticket_sale_start": ("A", PUBLIC_KHAM_PRODUCT, "TICKET_SALE_START_NOT_SHOWTIME",
                            "2026-08-22T12:00:00+08:00", "REVIEW"),
    "a_ticket_duration": ("A", PUBLIC_KHAM_PRODUCT, "APPROXIMATE_DURATION_MINUTES_NOT_SHOWTIME",
                          120, "REVIEW"),
    "a_ticket_age_advisory": ("A", PUBLIC_KHAM_PRODUCT, "RECOMMENDED_AGE_NOT_MINIMUM",
                              6, "REVIEW"),
    "a_ticket_session": ("A", PUBLIC_KHAM_PRODUCT, "CHECKOUT_SESSION_UNVERIFIED",
                         None, "HOLD"),
    "a_current_stock": ("A", PUBLIC_KHAM_PRODUCT, "LIVE_INVENTORY_UNVERIFIED",
                        None, "HOLD"),
    "a_eligible_min": ("A", PUBLIC_KHAM_PRODUCT, "ELIGIBLE_CHECKOUT_MIN_UNVERIFIED",
                       None, "HOLD"),
    "b_list_title": ("B", PUBLIC_TWTC_LIST, "OFFICIAL_EXHIBITION_LIST_TITLE",
                     "2026年電器空調影音大展", "REVIEW"),
    "b_detail_title": ("B", PUBLIC_TWTC_DETAIL, "SAME_EVENT_DETAIL_TITLE",
                       "2026年電器空調影音大展", "REVIEW"),
    "b_exhibition_dates": ("B", PUBLIC_TWTC_DETAIL, "EXHIBITION_DATES_NOT_TICKET_SESSIONS",
                           ["2026-11-06", "2026-11-09"], "REVIEW"),
    "b_daily_open_hours": ("B", PUBLIC_TWTC_DETAIL, "EXHIBITION_DAILY_OPEN_HOURS_NOT_SHOWTIME",
                           ["10:00", "18:00"], "REVIEW"),
    "b_exhibition_hall": ("B", PUBLIC_TWTC_DETAIL, "EXHIBITION_VENUE_HALL",
                          "世貿一館", "REVIEW"),
    "b_admission_rules": ("B", PUBLIC_TWTC_DETAIL, "ADMISSION_AND_CHILD_RULES_UNVERIFIED",
                          None, "HOLD"),
    "b_ticket_event_id": ("B", PUBLIC_TWTC_DETAIL, "TICKET_EVENT_ID_UNVERIFIED",
                          None, "HOLD"),
    "b_event_image": ("B", PUBLIC_TWTC_DETAIL, "EVENT_HERO_IMG_URL_UNVERIFIED",
                      None, "HOLD"),
}

def validate_public_non_session_receipt(e):
    """Reject role laundering; indexed reader alone cannot pass formal Golden."""
    if not isinstance(e, dict) or e.get("kind") != "P30_L7_NON_SESSION_FIELD_READINESS_V1":
        raise ValueError("NON_SESSION_KIND_HOLD")
    if (e.get("scope") != "ISOLATED_EVIDENCE_ONLY"
        or e.get("observation_method") != "PUBLIC_INDEXED_TEXT_READER_NOT_NATIVE_GET"
        or e.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
        or e.get("source_freshness") != "HOLD_INDEXED_CACHE_NOT_SAME_SESSION_NATIVE"
        or any(type(e.get(k)) is not int or e[k] != 0 for k in
               ("native_official_get", "formal_accepted_fields",
                "golden_accepted_events", "published_events"))):
        raise ValueError("NON_SESSION_FRESHNESS_RELEASE_HOLD")
    if e.get("sources") != {"A_venue_list": PUBLIC_TMC_LIST,
                            "A_venue_detail": PUBLIC_TMC_DETAIL,
                            "A_ticket_detail": PUBLIC_KHAM_PRODUCT,
                            "B_venue_list": PUBLIC_TWTC_LIST,
                            "B_venue_detail": PUBLIC_TWTC_DETAIL}:
        raise ValueError("NON_SESSION_SOURCE_HOLD")
    if e.get("identity") != {
        "A_ticket_platform_id": "04", "A_product_id": "P1DF32E2",
        "A_venue_detail_id": "2026SungNien-Yu",
        "A_direct_official_ticket_edge": PUBLIC_KHAM_PRODUCT,
        "A_ticket_session_id": None, "A_checkout_eligible_min": None,
        "B_platform_id": "16", "B_exhibition_detail_id": "29418",
        "B_ticket_session_id": None, "B_admission_verified": False,
        "B_list_detail_same_native_session": False,
        "formal_img_url": None, "cross_event_merge": False}:
        raise ValueError("NON_SESSION_IDENTITY_OR_SESSION_HOLD")
    rows = e.get("field_receipts")
    if not isinstance(rows, list) or len(rows) != len(PUBLIC_NON_SESSION_FIELDS):
        raise ValueError("NON_SESSION_COUNT_HOLD")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("name") not in PUBLIC_NON_SESSION_FIELDS:
            raise ValueError("NON_SESSION_UNKNOWN_FIELD_HOLD")
        name = row["name"]
        if name in seen:
            raise ValueError("NON_SESSION_DUPLICATE_HOLD")
        seen.add(name)
        line, source, role, value, decision = PUBLIC_NON_SESSION_FIELDS[name]
        if (row.get("line") != line
            or not exact_source_url(row.get("source"), source)
            or row.get("role") != role
            or type(row.get("value")) is not type(value)
            or row.get("value") != value
            or row.get("decision") != decision
            or row.get("formal_accepted") is not False
            or not isinstance(row.get("reason"), str) or not row["reason"].strip()):
            raise ValueError("NON_SESSION_SOURCE_ROLE_PROMOTION_HOLD")
        try:
            stamp = datetime.fromisoformat(row["observed_at"].replace("Z", "+00:00"))
            if stamp.utcoffset() is None:
                raise ValueError()
        except (ValueError, TypeError, KeyError, AttributeError):
            raise ValueError("NON_SESSION_TIMESTAMP_HOLD")
    if seen != set(PUBLIC_NON_SESSION_FIELDS):
        raise ValueError("NON_SESSION_MISSING_FIELD_HOLD")
    return {"A_review": 7, "A_hold": 3, "B_review": 5, "B_hold": 3,
            "native_get": 0, "formal_accepted": 0, "golden": 0, "published": 0,
            "decision": "INDEPENDENT_NATIVE_FRESHNESS_AND_GOLDEN_STILL_REQUIRED"}


# Independent public OFFICIAL reader adjudication of prior native value receipts.
# This is a separate read of the same public URLs, NOT a new native GET,
# a checkout session, or permission to write Golden/production data.
INDEPENDENT_PUBLIC_FIELDS = {
    ("A", "direct_ticket_product"): ("LOCAL_PURCHASE_ANCHOR_NOT_SESSION",
        PUBLIC_TMC_DETAIL, {"product_id":"P1DF32E2","official_ticket_url":PUBLIC_KHAM_PRODUCT},
        "590adff847afe491d89b26b6e7820e2f6b8a8ed9631320e0f2f5161dd101d210"),
    ("A", "venue_showtime"): ("VENUE_SHOW_NOT_SALE", PUBLIC_TMC_DETAIL,
        "2026/11/07 19:30", "590adff847afe491d89b26b6e7820e2f6b8a8ed9631320e0f2f5161dd101d210"),
    ("A", "venue_hall"): ("VENUE_HALL", PUBLIC_TMC_DETAIL,
        "臺北流行音樂中心 表演廳", "590adff847afe491d89b26b6e7820e2f6b8a8ed9631320e0f2f5161dd101d210"),
    ("B", "list_detail_identity"): ("SAME_ROW_SAME_ID", PUBLIC_TWTC_LIST,
        {"exhibition_id":"29418","same_row_title":"2026年電器空調影音大展"},
        "385aee1ce2d85ab432e32add10c8fc5ffb27ce2d72a71f0d73375df079906149"),
    ("B", "exhibition_title"): ("EXACT_EVENT_TITLE", PUBLIC_TWTC_DETAIL,
        "2026年電器空調影音大展",
        "887761a28e4afb991d5b81e3f6e5cc2e5af57adbc751b0e9274d227f8ee00116"),
    ("B", "exhibition_dates"): ("EXHIBITION_DATE_NOT_SALE", PUBLIC_TWTC_DETAIL,
        {"start":"2026/11/06","end":"2026/11/09"},
        "887761a28e4afb991d5b81e3f6e5cc2e5af57adbc751b0e9274d227f8ee00116"),
    ("B", "open_hours"): ("DAILY_OPEN_HOURS_NOT_SHOWTIME", PUBLIC_TWTC_DETAIL,
        {"open":"10:00","close":"18:00"},
        "887761a28e4afb991d5b81e3f6e5cc2e5af57adbc751b0e9274d227f8ee00116"),
    ("B", "venue_hall"): ("EXHIBITION_HALL_NOT_TICKET_ID", PUBLIC_TWTC_DETAIL,
        "世貿一館", "887761a28e4afb991d5b81e3f6e5cc2e5af57adbc751b0e9274d227f8ee00116"),
}

def validate_independent_public_field_crosscheck(e):
    """Strictly validate separate reader-vs-native receipts; review only."""
    if not isinstance(e,dict) or e.get("kind")!="P30_L7_INDEPENDENT_PUBLIC_FIELD_CROSSCHECK_V1":
        raise ValueError("CROSSCHECK_KIND_HOLD")
    if (e.get("method")!="INDEPENDENT_PUBLIC_OFFICIAL_WEB_READER_NOT_NATIVE_GET"
        or e.get("prior_native_run_id")!=41587253858
        or e.get("prior_native_artifact_id")!=13209075143
        or e.get("prior_native_matrix_sha256")!="ae060f8cb7e00cb7a3376599b577dd4ebfea71c7b3930b5dd890270e0724e76a"
        or e.get("release_state")!="HARD_HOLD_NO_PUBLICATION"
        or e.get("source_authority")!={"A":"04_KHAM_TMC_VENUE","B":"16_TWTC_EXISTING_CANONICAL"}
        or e.get("conflict_guards")!={"A_ticket_sale_not_show":True,
            "A_product_id_not_checkout_session":True,
            "B_exhibition_date_not_ticket_sale":True,
            "B_open_hours_not_performance_showtime":True,
            "B_exhibition_id_not_ticket_event_id":True,
            "B_admission_and_child_policy_unverified":True,
            "no_cross_event_merge":True}
        or any(type(e.get(k)) is not int or e[k]!=0 for k in
            ("this_gate_native_get","formal_accepted_fields","golden_accepted_events",
             "published_events","formal_pwa_feed_events"))):
        raise ValueError("CROSSCHECK_AUTHORITY_RELEASE_HOLD")
    rows=e.get("field_receipts")
    if not isinstance(rows,list) or len(rows)!=len(INDEPENDENT_PUBLIC_FIELDS):
        raise ValueError("CROSSCHECK_COUNT_HOLD")
    seen=set()
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("CROSSCHECK_ROW_HOLD")
        key=(row.get("line"),row.get("field"))
        if key not in INDEPENDENT_PUBLIC_FIELDS or key in seen:
            raise ValueError("CROSSCHECK_DUPLICATE_OR_UNKNOWN_HOLD")
        seen.add(key)
        role,url,value,prior_hash=INDEPENDENT_PUBLIC_FIELDS[key]
        if (row.get("event_id")!=("P1DF32E2" if key[0]=="A" else "29418")
            or row.get("role")!=role or row.get("source_url")!=url
            or row.get("prior_native_body_sha256")!=prior_hash
            or type(row.get("observed_value")) is not type(value)
            or row.get("observed_value")!=value
            or row.get("independent_decision")!="SOURCE_VALUE_CROSSCHECK_REVIEW_ONLY"
            or row.get("formal_accepted") is not False):
            raise ValueError("CROSSCHECK_VALUE_ROLE_PROVENANCE_HOLD")
        try:
            stamp=datetime.fromisoformat(row["reader_observed_at_utc"].replace("Z","+00:00"))
            if stamp.utcoffset() is None: raise ValueError()
        except (KeyError,ValueError,TypeError,AttributeError):
            raise ValueError("CROSSCHECK_TIMESTAMP_HOLD")
    if seen!=set(INDEPENDENT_PUBLIC_FIELDS):
        raise ValueError("CROSSCHECK_MISSING_HOLD")
    return {"A_crosschecked":3,"B_crosschecked":5,"review_only":8,
            "native_get_this_gate":0,"formal_accepted":0,"golden":0,
            "published":0,"decision":"INDEPENDENT_GOLDEN_ADJUDICATION_STILL_REQUIRED"}


# First non-session usable-field subset: exact source/value-bound proposal only.
# These fields do NOT require ticket checkout Session, inventory, or price.
# No independent authority grants formal FIELD/Golden/PWA publication here.
FIELD_SUBSET_KEYS = (
    ("A", "venue_showtime"), ("A", "venue_hall"),
    ("B", "exhibition_dates"), ("B", "open_hours"), ("B", "venue_hall"),
)
FIELD_SUBSET_DEPENDENCIES = (
    ("A", "direct_ticket_product"), ("B", "list_detail_identity"),
)
FIELD_SUBSET_FORBIDDEN_ROLES = (
    "TICKET_SESSION", "LIVE_INVENTORY", "ADMISSION_PRICE",
    "OFFICIAL_IMAGE_URL", "SALE_AS_SHOWTIME",
)

def build_independent_field_subset_proposal(crosscheck):
    """Derive a review-only, source-locked five-field proposal; no fresh GET."""
    from copy import deepcopy
    validate_independent_public_field_crosscheck(crosscheck)
    lookup = {(r["line"], r["field"]): r for r in crosscheck["field_receipts"]}
    return {
        "kind": "P30_L7_FIRST_USABLE_NON_SESSION_FIELD_SUBSET_V1",
        "scope": "ISOLATED_ARTIFACT_REVIEW_ONLY",
        "release_state": "HARD_HOLD_NO_PUBLICATION",
        "source_freshness": "HISTORIC_NATIVE_PLUS_SEPARATE_PUBLIC_READER_NOT_NEW_GET",
        "prior_native_run_id": crosscheck["prior_native_run_id"],
        "prior_native_artifact_id": crosscheck["prior_native_artifact_id"],
        "prior_native_matrix_sha256": crosscheck["prior_native_matrix_sha256"],
        "reader_observed_at_utc": crosscheck["reader_observed_at_utc"],
        "source_receipts_total": len(lookup),
        "candidate_fields": [deepcopy(lookup[k]) for k in FIELD_SUBSET_KEYS],
        "identity_dependencies": [deepcopy(lookup[k]) for k in FIELD_SUBSET_DEPENDENCIES],
        "excluded_roles": list(FIELD_SUBSET_FORBIDDEN_ROLES),
        "conflict_disposition": {
            "A_show_vs_KHAM_sale": "DISTINCT_ROLES_NO_MERGE",
            "A_product_id_vs_checkout_session": "PRODUCT_ID_NOT_SESSION",
            "B_exhibition_dates_vs_sale": "EXHIBITION_PERIOD_ONLY",
            "B_daily_hours_vs_showtime": "DAILY_OPEN_HOURS_ONLY",
            "B_exhibition_id_vs_ticket_id": "CANONICAL_TWTC_DETAIL_ONLY",
            "B_admission_children_price_image": "HOLD_UNVERIFIED",
        },
        "independent_formal_field_authority": "PENDING_SEPARATE_OWNER_APPROVAL",
        "decision": "PROPOSE_FOR_INDEPENDENT_FIELD_ADJUDICATION_NOT_ACCEPTED",
        "native_get_this_gate": 0,
        "formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "formal_pwa_feed_events": 0,
    }

def validate_independent_field_subset_proposal(crosscheck, proposal):
    """Fail closed on every literal, role, identity edge, release and evidence hash."""
    expected = build_independent_field_subset_proposal(crosscheck)
    if not isinstance(proposal, dict) or proposal != expected:
        raise ValueError("FIELD_SUBSET_SOURCE_VALUE_AUTHORITY_OR_RELEASE_HOLD")
    if (len(proposal["candidate_fields"]) != 5
        or len(proposal["identity_dependencies"]) != 2
        or any(row["formal_accepted"] is not False
               for row in proposal["candidate_fields"] + proposal["identity_dependencies"])):
        raise ValueError("FIELD_SUBSET_FORMAL_PROMOTION_HOLD")
    return {
        "A_candidate_fields": 2, "B_candidate_fields": 3,
        "identity_dependencies": 2, "prior_source_value_crosschecks": 8,
        "native_get_this_gate": 0, "formal_accepted": 0,
        "golden": 0, "published": 0, "formal_pwa_feed": 0,
        "decision": "PENDING_INDEPENDENT_FIELD_ADJUDICATION_AND_OWNER_AUTHORITY",
    }


# Fixed, reusable HTML-input field adapter for the two existing canonical sources.
# This is a parser, NOT an HTTP client or a Golden/publication authority.
# It never saves HTML and never claims a native GET from a supplied string.
def parse_official_non_session_html(source_url, html, expected_title,
                                    expected_identity_id, observed_at_utc, now_utc=None):
    """Parse exact-source HTML into non-session REVIEW values; fail closed."""
    import re
    from html.parser import HTMLParser
    from urllib.parse import parse_qs, urlsplit
    from datetime import timezone

    class PublicFields(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts, self.headings, self.links = [], [], []
            self.heading, self.anchor, self.skip = None, None, 0
        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "noscript"):
                self.skip += 1
            if tag in ("h1", "h2") and not self.skip:
                self.heading = []
            if tag == "a" and not self.skip:
                self.anchor = {"href": dict(attrs).get("href", ""), "text": []}
        def handle_data(self, value):
            if self.skip or not value.strip():
                return
            value = " ".join(value.split())
            self.parts.append(value)
            if self.heading is not None:
                self.heading.append(value)
            if self.anchor is not None:
                self.anchor["text"].append(value)
        def handle_endtag(self, tag):
            if tag in ("script", "style", "noscript"):
                self.skip = max(0, self.skip - 1)
            if tag in ("h1", "h2") and self.heading is not None:
                self.headings.append(" ".join(self.heading))
                self.heading = None
            if tag == "a" and self.anchor is not None:
                self.links.append((self.anchor["href"], " ".join(self.anchor["text"])))
                self.anchor = None

    def one(items, label):
        values = set(items)
        if len(values) != 1:
            raise ValueError("SOURCE_FIELD_MISSING_OR_CONFLICT_" + label)
        return next(iter(values))

    if not isinstance(html, str) or not 0 < len(html) <= 524288:
        raise ValueError("SOURCE_HTML_EMPTY_OR_OVERSIZE_HOLD")
    if not isinstance(expected_title, str) or not expected_title.strip():
        raise ValueError("SOURCE_TITLE_REQUIRED_HOLD")
    try:
        observed = datetime.fromisoformat(observed_at_utc.replace("Z", "+00:00"))
        now = (now_utc if now_utc is not None
               else datetime.now(timezone.utc))
        if observed.utcoffset() is None or now.utcoffset() is None:
            raise ValueError()
        age = (now - observed).total_seconds()
        if age < 0 or age > 86400:
            raise ValueError()
    except (ValueError, AttributeError, TypeError):
        raise ValueError("SOURCE_FRESHNESS_UNATTESTED_OR_STALE_HOLD")

    url = urlsplit(source_url)
    if (url.scheme != "https" or url.username or url.password or url.fragment):
        raise ValueError("SOURCE_URL_AUTHORITY_HOLD")
    tmc = (url.netloc == "www.tmc.taipei"
           and re.fullmatch(r"/tw/blog/show/[A-Za-z0-9_-]+", url.path)
           and not url.query)
    twtc = (url.netloc in ("twtc.com.tw", "www.twtc.com.tw")
            and url.path == "/exhibition_more.aspx"
            and set(parse_qs(url.query)) == {"id", "p"}
            and parse_qs(url.query)["p"] == ["home"]
            and len(parse_qs(url.query)["id"]) == 1
            and re.fullmatch(r"[0-9]{1,10}", parse_qs(url.query)["id"][0]))
    if not (tmc or twtc):
        raise ValueError("SOURCE_NOT_CANONICAL_ALLOWLIST_HOLD")

    page = PublicFields()
    page.feed(html)
    if expected_title not in page.headings:
        raise ValueError("LIST_DETAIL_TITLE_IDENTITY_HOLD")
    scope = " ".join(page.parts).split("其他展演活動", 1)[0]
    if tmc:
        shows = re.findall(r"20[0-9]{2}[./][0-9]{2}[./][0-9]{2}\s+[0-9]{2}:[0-9]{2}", scope)
        show = one((re.sub(r"\s+", " ", x.replace(".", "/")) for x in shows),
                   "TMC_SHOW")
        halls = re.findall(r"活動地點\s+(臺北流行音樂中心\s+[^\s]{1,16})\s+主辦單位", scope)
        hall = one((" ".join(x.split()) for x in halls), "TMC_HALL")
        products = []
        for href, label in page.links:
            h = urlsplit(href)
            if (label == "購票連結" and h.scheme == "https"
                and h.netloc in ("kham.com.tw", "www.kham.com.tw")
                and h.path == "/application/UTK02/UTK0201_.aspx"
                and not h.fragment and not h.username and not h.password
                and set(parse_qs(h.query)) == {"PRODUCT_ID"}
                and len(parse_qs(h.query)["PRODUCT_ID"]) == 1
                and re.fullmatch(r"P[A-Za-z0-9]{6,12}",
                                 parse_qs(h.query)["PRODUCT_ID"][0])):
                products.append(parse_qs(h.query)["PRODUCT_ID"][0])
        product_id = one(products, "TMC_DIRECT_PRODUCT_EDGE")
        fields = [
            {"field": "venue_showtime", "role": "VENUE_SHOW_NOT_SALE",
             "value": show},
            {"field": "venue_hall", "role": "VENUE_HALL", "value": hall},
        ]
        identity = {"kind": "VENUE_TO_KHAM_PRODUCT_NOT_SESSION",
                    "product_id": product_id}
        line = "A"
    else:
        def label_value(label, pattern):
            matches = re.findall(re.escape(label) + r"\s*[：:]\s*" + pattern,
                                 scope)
            return one(matches, "TWTC_" + label)
        period = label_value("展出日期",
            r"(20[0-9]{2}/[0-9]{2}/[0-9]{2}\s*[~～]\s*20[0-9]{2}/[0-9]{2}/[0-9]{2})")
        hours = label_value("展出時間",
            r"([0-9]{2}:[0-9]{2}\s*[~～]\s*[0-9]{2}:[0-9]{2})")
        hall = label_value("展覽館別", r"([^\s]{2,20})")
        start, end = [x.strip() for x in re.split(r"[~～]", period)]
        opening, closing = [x.strip() for x in re.split(r"[~～]", hours)]
        if start > end or opening >= closing:
            raise ValueError("TWTC_PERIOD_OR_HOURS_CONFLICT_HOLD")
        fields = [
            {"field": "exhibition_dates", "role": "EXHIBITION_DATE_NOT_SALE",
             "value": {"start": start, "end": end}},
            {"field": "open_hours", "role": "DAILY_OPEN_HOURS_NOT_SHOWTIME",
             "value": {"open": opening, "close": closing}},
            {"field": "venue_hall", "role": "EXHIBITION_HALL_NOT_TICKET_ID",
             "value": hall},
        ]
        identity = {"kind": "TWTC_DETAIL_ID_NOT_TICKET_SESSION",
                    "exhibition_id": parse_qs(url.query)["id"][0]}
        line = "B"
    # LIST-derived identity is a separate required input; never infer it from a
    # similar title or silently accept a different ticket Product / exhibition ID.
    actual_id = (identity["product_id"] if tmc else identity["exhibition_id"])
    if not isinstance(expected_identity_id, str) or actual_id != expected_identity_id:
        raise ValueError("LIST_DETAIL_OR_PRODUCT_ID_CONFLICT_HOLD")
    return {"kind": "P30_L7_FIXED_OFFICIAL_DETAIL_HTML_PARSER_V1",
            "source_url": source_url, "expected_list_title": expected_title,
            "observed_at_utc": observed.isoformat(),
            "input_attestation": "CALLER_SUPPLIED_HTML_NOT_NATIVE_GET_PROOF",
            "line": line, "identity": identity,
            "candidate_fields": [
                dict(row, source_url=source_url, observed_at_utc=observed.isoformat(),
                     decision="SOURCE_LOCAL_PARSE_REVIEW_ONLY",
                     formal_accepted=False) for row in fields],
            "native_get_verified": False, "formal_accepted_fields": 0,
            "golden_accepted_events": 0, "published_events": 0,
            "release_state": "HARD_HOLD_NO_PUBLICATION"}




# Source-specific, non-publishing DOM root-cause audit. This deliberately
# returns only bounded structural counts/IDs, never source HTML or other titles.
# It cannot establish an accepted FIELD or a source freshness claim by itself.
def diagnose_twtc_title_row_structure(html, expected_title, expected_id):
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlsplit, parse_qs

    if expected_title != "2026年電器空調影音大展" or expected_id != "29418":
        raise ValueError("TWTC_AUDIT_EXACT_SOURCE_ID_REQUIRED")
    if (not isinstance(html, str) or not html.strip()
            or len(html.encode("utf-8")) > 524288):
        raise ValueError("TWTC_AUDIT_BODY_SIZE_HOLD")

    class StructuralProbe(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack, self.rows = [], []
            self.cell, self.anchor, self.skip = None, None, 0

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "noscript"):
                self.skip += 1
            if self.skip:
                return
            if tag in ("article", "tr", "li"):
                if self.stack:
                    self.stack[-1]["nested"] = True
                self.stack.append({"tag": tag, "text": [], "links": [],
                                   "cells": [], "nested": False})
            if tag in ("td", "th") and self.stack:
                if self.cell is not None:
                    raise ValueError("TWTC_AUDIT_NESTED_CELL_HOLD")
                self.cell = {"text": [], "links": []}
                self.stack[-1]["cells"].append(self.cell)
            if tag == "a":
                if self.anchor is not None:
                    raise ValueError("TWTC_AUDIT_NESTED_ANCHOR_HOLD")
                self.anchor = dict(attrs).get("href", "")

        def handle_data(self, data):
            if self.skip:
                return
            value = " ".join(data.split())
            if not value:
                return
            for row in self.stack:
                row["text"].append(value)
            if self.cell is not None:
                self.cell["text"].append(value)

        def handle_endtag(self, tag):
            if tag in ("script", "style", "noscript"):
                self.skip = max(0, self.skip - 1)
                return
            if self.skip:
                return
            if tag == "a" and self.anchor is not None:
                if self.stack:
                    self.stack[-1]["links"].append(self.anchor)
                if self.cell is not None:
                    self.cell["links"].append(self.anchor)
                self.anchor = None
            if tag in ("td", "th") and self.cell is not None:
                self.cell = None
            if tag in ("article", "tr", "li") and self.stack:
                if self.stack[-1]["tag"] != tag:
                    raise ValueError("TWTC_AUDIT_MISMATCHED_ROW_HOLD")
                self.rows.append(self.stack.pop())

    def ids(links):
        values = set()
        for href in links:
            url = urlsplit(urljoin(PUBLIC_TWTC_LIST, href))
            query = parse_qs(url.query)
            if (url.scheme == "https"
                    and url.netloc in ("twtc.com.tw", "www.twtc.com.tw")
                    and url.path == "/exhibition_more.aspx"
                    and set(query) == {"id", "p"}
                    and query["p"] == ["home"]
                    and len(query["id"]) == 1
                    and query["id"][0].isdigit()):
                values.add(query["id"][0])
        return sorted(values)[:12]

    parser = StructuralProbe()
    parser.feed(html)
    if parser.stack or parser.cell is not None or parser.anchor is not None:
        raise ValueError("TWTC_AUDIT_UNCLOSED_MARKUP_HOLD")
    if len(parser.rows) > 5000:
        raise ValueError("TWTC_AUDIT_ROW_LIMIT_HOLD")
    matched = [row for row in parser.rows
               if expected_title in " ".join(row["text"])]
    atomic = [row for row in matched if not row["nested"]]
    title_cells = [cell for row in atomic for cell in row["cells"]
                   if expected_title in " ".join(cell["text"])]
    cell_ids = sorted({item for cell in title_cells for item in ids(cell["links"])})
    row_ids = sorted({item for row in atomic for item in ids(row["links"])})
    if not atomic:
        root = "NO_ATOMIC_SEMANTIC_TITLE_ROW"
    elif len(cell_ids) > 1:
        root = "TITLE_CELL_MULTIPLE_DETAIL_IDS"
    elif expected_id in cell_ids:
        root = "TITLE_CELL_EXACT_ID_EDGE_HYPOTHESIS"
    elif len(row_ids) > 1:
        root = "TITLE_ROW_MULTIPLE_IDS_WITHOUT_CELL_EDGE"
    elif expected_id not in row_ids:
        root = "EXPECTED_DETAIL_ID_NOT_IN_ATOMIC_TITLE_ROW"
    else:
        root = "STRICT_ROW_SINGLE_ID_EDGE_HYPOTHESIS"
    return {
        "kind": "P30_L7_TWTC_STRUCTURAL_ROOT_CAUSE_AUDIT_V1",
        "semantic_rows": len(parser.rows),
        "title_rows": len(matched),
        "atomic_title_rows": len(atomic),
        "title_cells": len(title_cells),
        "title_cell_detail_ids": cell_ids[:12],
        "atomic_row_detail_ids": row_ids[:12],
        "root_cause_class": root,
        "decision": "STRUCTURAL_DIAGNOSIS_REVIEW_NOT_IDENTITY_PASS",
        "formal_accepted_fields": 0, "golden": 0, "published": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }


# Fixed LIST -> exact DETAIL -> source-local FIELD candidate integration.
# This consumes caller-supplied HTML only: no HTTP, formal feed, Golden or publisher.
# A TMC ticket PRODUCT_ID is a detail-side edge, never a LIST-derived Session ID.
def build_non_session_list_detail_candidate(
        list_url, list_html, detail_url, detail_html, expected_title,
        expected_identity_id, observed_at_utc, now_utc=None):
    """Return an in-memory, hash-bound REVIEW snapshot; reject cross-row joins."""
    import hashlib
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlsplit, parse_qs

    if list_url not in (PUBLIC_TMC_LIST, PUBLIC_TWTC_LIST):
        raise ValueError("LIST_CANONICAL_SOURCE_HOLD")
    if not isinstance(list_html, str) or not 0 < len(list_html.encode("utf-8")) <= 524288:
        raise ValueError("LIST_HTML_EMPTY_OR_OVERSIZE_HOLD")
    if not isinstance(detail_html, str) or not 0 < len(detail_html.encode("utf-8")) <= 524288:
        raise ValueError("DETAIL_HTML_EMPTY_OR_OVERSIZE_HOLD")
    if not isinstance(expected_title, str) or not expected_title.strip():
        raise ValueError("LIST_EXPECTED_TITLE_HOLD")
    # Exact URL equality is intentional: different query variants can represent
    # different field granularity (TWTC p=home versus p=menu1).
    d = urlsplit(detail_url)
    if list_url == PUBLIC_TMC_LIST:
        if (d.scheme != "https" or d.netloc != "www.tmc.taipei"
            or not d.path.startswith("/tw/blog/show/")
            or not d.path[len("/tw/blog/show/"):]
            or "/" in d.path[len("/tw/blog/show/"):]
            or d.query or d.fragment or d.username or d.password):
            raise ValueError("TMC_DETAIL_AUTHORITY_HOLD")
        line = "A"
    else:
        if (d.scheme != "https" or d.netloc not in ("twtc.com.tw", "www.twtc.com.tw")
            or d.path != "/exhibition_more.aspx" or d.fragment
            or d.username or d.password
            or set(parse_qs(d.query)) != {"id", "p"}
            or parse_qs(d.query)["p"] != ["home"]
            or parse_qs(d.query)["id"] != [expected_identity_id]):
            raise ValueError("TWTC_LIST_DETAIL_ID_OR_SCOPE_HOLD")
        line = "B"

    class RowAnchors(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []
            self.rows = []
            self.anchors = []
            self.active_anchor = None
            self.active_cell = None
            self.skip = 0

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "noscript"):
                self.skip += 1
            if self.skip:
                return
            if tag in ("article", "tr", "li"):
                # A composite responsive container can wrap MANY event rows.
                # It is not an atomic title->detail identity authority.
                if self.stack:
                    self.stack[-1]["has_nested_semantic"] = True
                self.stack.append({"tag": tag, "text": [], "links": [],
                                   "cells": [], "has_nested_semantic": False})
            if tag in ("td", "th") and self.stack:
                # Bind identity to the exact title-bearing cell, not a
                # responsive row containing links for unrelated events.
                if self.active_cell is not None:
                    raise ValueError("LIST_NESTED_TABLE_CELL_AMBIGUOUS_HOLD")
                self.active_cell = {"tag": tag, "text": [], "links": []}
                self.stack[-1]["cells"].append(self.active_cell)
            if tag == "a":
                self.active_anchor = {"href": dict(attrs).get("href", ""), "text": []}

        def handle_data(self, data):
            if self.skip:
                return
            value = " ".join(data.split())
            if not value:
                return
            for row in self.stack:
                row["text"].append(value)
            if self.active_cell is not None:
                self.active_cell["text"].append(value)
            if self.active_anchor is not None:
                self.active_anchor["text"].append(value)

        def handle_endtag(self, tag):
            if tag in ("script", "style", "noscript"):
                self.skip = max(0, self.skip - 1)
                return
            if self.skip:
                return
            if tag == "a" and self.active_anchor is not None:
                link = (self.active_anchor["href"],
                        " ".join(self.active_anchor["text"]))
                self.anchors.append(link)
                # An anchor belongs to its nearest semantic row only.
                # Assigning it to all ancestors creates false duplicate edges
                # for responsive <article>/<tr> nesting.
                if self.stack:
                    self.stack[-1]["links"].append(link)
                if self.active_cell is not None:
                    self.active_cell["links"].append(link)
                self.active_anchor = None
            if tag in ("td", "th") and self.active_cell is not None:
                if self.active_cell["tag"] != tag:
                    raise ValueError("LIST_CELL_MARKUP_AMBIGUOUS_HOLD")
                self.active_cell = None
            if tag in ("article", "tr", "li") and self.stack:
                if self.stack[-1]["tag"] != tag:
                    raise ValueError("LIST_ROW_MARKUP_AMBIGUOUS_HOLD")
                self.rows.append(self.stack.pop())

    parser = RowAnchors()
    parser.feed(list_html)
    if parser.stack or parser.skip or parser.active_cell is not None:
        raise ValueError("LIST_HTML_UNCLOSED_ROW_OR_CELL_HOLD")
    matched = []
    for row in parser.rows:
        # Only the innermost semantic row may attest an exact event edge.
        # Outer article/li/tr containers can include multiple unrelated IDs;
        # using them caused native TWTC LIST_ROW_CONFLICTING_DETAIL_IDS_HOLD.
        if row.get("has_nested_semantic"):
            continue
        text = " ".join(row["text"])
        # Whole title, not a fuzzy substring of another event.
        if expected_title not in text:
            continue
        # Prefer a source-local exact-title cell containing its own DETAIL
        # link. A sibling cell's unrelated event link must not poison the
        # target cell or become a false same-ID edge. Without such a local
        # edge, retain the strict whole-row single-ID fallback.
        title_cells = [cell for cell in row.get("cells", [])
                       if expected_title in " ".join(cell["text"])]
        cell_links = [
            (urljoin(list_url, href), " ".join(cell["text"]))
            for cell in title_cells for href, label in cell["links"]
            if urlsplit(urljoin(list_url, href)).path
            == "/exhibition_more.aspx"]
        if line == "B" and cell_links:
            # Native source may put both p=home and p=menu1 URLs for the
            # SAME exhibition ID in one exact-title cell. A p=menu1 link is
            # not the canonical DETAIL evidence, but is not another event.
            # Reject foreign IDs/hosts, malformed scopes and missing exact
            # p=home href; do not weaken cross-event negative safety.
            def local_exhibition_id(href):
                u = urlsplit(href)
                query = parse_qs(u.query)
                if (u.scheme != "https" or u.netloc not in (
                        "twtc.com.tw", "www.twtc.com.tw")
                        or u.path != "/exhibition_more.aspx" or u.fragment
                        or u.username or u.password
                        or set(query) != {"id", "p"}
                        or query["p"] not in (["home"], ["menu1"])
                        or len(query["id"]) != 1
                        or not query["id"][0].isdigit()):
                    raise ValueError("LIST_TITLE_CELL_UNTRUSTED_DETAIL_HREF_HOLD")
                return query["id"][0]
            if (detail_url not in {url for url, _ in cell_links}
                    or {local_exhibition_id(url) for url, _ in cell_links}
                    != {expected_identity_id}):
                raise ValueError("LIST_TITLE_CELL_CONFLICTING_DETAIL_IDS_HOLD")
            # One atomic title cell is one edge, even with a same-ID
            # secondary display link; dates remain part of the row fingerprint.
            matched.append((text, detail_url))
            continue
        row_detail_links = [urljoin(list_url, href)
                            for href, label in row["links"]
                            if urlsplit(urljoin(list_url, href)).path
                            == "/exhibition_more.aspx"]
        # A title-only cell cannot be joined to one of multiple row IDs.
        if line == "B" and row_detail_links:
            if set(row_detail_links) != {detail_url}:
                raise ValueError("LIST_ROW_CONFLICTING_DETAIL_IDS_HOLD")
            matched.extend((text, detail_url) for link in row_detail_links
                           if link == detail_url)
    # TMC official LIST cards may have no semantic <article>/<tr> wrapper.
    # Bind the complete title and exact URL within the SAME anchor, never
    # across unrelated cards or by a page-wide fuzzy title search.
    if line == "A":
        matched = [(label, urljoin(list_url, href)) for href, label in parser.anchors
                   if urljoin(list_url, href) == detail_url
                   and expected_title in " ".join(label.split())]
    # Identical responsive desktop/mobile copies of the SAME exact title/ID
    # are one identity edge, not two distinct events. Different row text or
    # conflicting IDs must still fail closed; never fuzzy-merge by title.
    # TMC has no documented responsive duplicate identity contract: a
    # repeated A anchor remains ambiguous even if its text is identical.
    if line == "A" and len(matched) != 1:
        raise ValueError("LIST_EXACT_ROW_DETAIL_EDGE_MISSING_OR_AMBIGUOUS_HOLD")
    unique_matches = set(matched)
    duplicate_period = None
    if len(unique_matches) != 1:
        # Native TWTC has two responsive title cells for the same official ID.
        # Ignore layout-only row wording ONLY if each atomic title+ID row has
        # exactly the same explicit two-date period. Different dates, missing
        # dates, extra date labels or more than two copies fail closed.
        if line != "B" or not 1 <= len(unique_matches) <= 2:
            raise ValueError("LIST_EXACT_ROW_DETAIL_EDGE_MISSING_OR_AMBIGUOUS_HOLD")

        def row_period(row_text):
            import re
            tokens = re.findall(
                r"(?<!\d)(?:20\d{2}[/-])?\d{1,2}[/-]\d{1,2}(?!\d)",
                row_text)
            if len(tokens) != 2:
                return None
            normalized = []
            for token in tokens:
                parts = [int(p) for p in token.replace("-", "/").split("/")]
                if len(parts) == 3:
                    year, month, day = parts
                    if year != 2026:
                        return None
                else:
                    month, day = parts
                if not (1 <= month <= 12 and 1 <= day <= 31):
                    return None
                normalized.append("2026/%02d/%02d" % (month, day))
            return tuple(normalized)

        periods = {row_period(row_text) for row_text, _ in unique_matches}
        if None in periods or len(periods) != 1:
            raise ValueError("LIST_RESPONSIVE_PERIOD_CONFLICT_OR_AMBIGUOUS_HOLD")
        duplicate_period = next(iter(periods))
    # Deterministic representative; never manufacture a source row or identity.
    matched = [min(unique_matches, key=lambda pair: (len(pair[0]), pair[0]))]

    detail = parse_official_non_session_html(
        detail_url, detail_html, expected_title, expected_identity_id,
        observed_at_utc, now_utc=now_utc)
    if detail["line"] != line:
        raise ValueError("LIST_DETAIL_CROSS_SOURCE_HOLD")
    if duplicate_period is not None:
        period = next((f["value"] for f in detail["candidate_fields"]
                       if f["field"] == "exhibition_dates"), None)
        if (not isinstance(period, dict)
                or (period.get("start"), period.get("end")) != duplicate_period):
            raise ValueError("LIST_RESPONSIVE_PERIOD_DETAIL_MISMATCH_HOLD")
    # A product identity is proven by the detail's direct KHAM href; not by
    # the TMC LIST row. B exhibition identity is the exact same LIST href ID.
    identity_scope = ("DETAIL_DIRECT_KHAM_PRODUCT_NOT_LIST_SESSION" if line == "A"
                      else "LIST_EXACT_TWTC_EXHIBITION_ID_NOT_TICKET_SESSION")
    return {
        "kind": "P30_L7_LIST_DETAIL_SAFE_CANDIDATE_V1",
        "line": line,
        "list_url": list_url, "detail_url": detail_url,
        "list_row_title": expected_title,
        "list_row_text": matched[0][0],
        "identity": detail["identity"],
        "identity_scope": identity_scope,
        "observed_at_utc": detail["observed_at_utc"],
        "source_receipts": {
            "list_html_sha256": hashlib.sha256(list_html.encode("utf-8")).hexdigest(),
            "detail_html_sha256": hashlib.sha256(detail_html.encode("utf-8")).hexdigest(),
            "attestation": "CALLER_SUPPLIED_HTML_HASH_ONLY_NOT_NATIVE_GET",
            "freshness": "INPUT_TIMESTAMP_ONLY_SOURCE_FRESHNESS_UNVERIFIED",
        },
        "candidate_fields": detail["candidate_fields"],
        "source_quality": "LIST_ROW_DETAIL_ID_AND_FIELD_PARSE_REVIEW_ONLY",
        "conflict_policy": {
            "A_show_not_sale_or_session": True,
            "B_daily_hours_not_showtime": True,
            "B_p_home_hall_not_p_menu1_hall": True,
            "ticket_price_stock_image_admission": "HOLD",
        },
        "native_get_verified": False, "formal_accepted_fields": 0,
        "golden_accepted_events": 0, "published_events": 0,
        "formal_pwa_feed_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }




# Native source acquisition and conflict adjudication are deliberately one process.
# Caller-supplied fixture/HTML can test the contract but cannot establish a live GET,
# source freshness, formal acceptance, Golden status or production publication.
def collect_native_five_field_readiness(fetcher=None, now_utc=None):
    """One-shot, exact-URL public GET -> same-run LIST/DETAIL -> field matrix."""
    import hashlib
    import re
    import socket
    import ssl
    import urllib.error
    import urllib.request
    from datetime import datetime, timezone

    now = now_utc if now_utc is not None else datetime.now(timezone.utc)
    if now.utcoffset() is None:
        raise ValueError("NATIVE_CLOCK_MUST_BE_TIMEZONE_AWARE")
    native = fetcher is None
    targets = (
        ("A_LIST", PUBLIC_TMC_LIST),
        ("A_DETAIL", PUBLIC_TMC_DETAIL),
        ("A_KHAM", "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2"),
        ("B_LIST", PUBLIC_TWTC_LIST),
        ("B_DETAIL", PUBLIC_TWTC_DETAIL),
    )
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect) if native else None
    records, htmls = [], {}
    for role, url in targets:
        receipt = {"role": role, "url": url, "http_status": None,
                   "body_sha256": None, "bytes": 0, "observed_at_utc": None,
                   "decision": "SOURCE_FRESHNESS_HOLD"}
        try:
            if native:
                req = urllib.request.Request(url, method="GET", headers={
                    "User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Encoding": "identity"})
                with opener.open(req, timeout=8) as response:
                    status = response.status
                    content_type = response.headers.get("Content-Type", "")
                    final_url = response.geturl()
                    body = response.read(524289)
            else:
                # Test injection is explicitly untrusted; never promote its results.
                item = fetcher(role, url)
                status = item["status"]
                content_type = item.get("content_type", "text/html; charset=utf-8")
                final_url = item.get("url", url)
                body = item["body"]
            observed = datetime.now(timezone.utc) if native else now
            receipt["observed_at_utc"] = observed.isoformat()
            receipt["http_status"] = status
            receipt["bytes"] = len(body)
            receipt["body_sha256"] = hashlib.sha256(body).hexdigest()
            receipt["content_type"] = content_type[:100]
            if (status != 200 or final_url != url or len(body) > 524288
                    or not body or not isinstance(body, bytes)
                    or not content_type.lower().startswith("text/html")
                    or ("charset=" in content_type.lower()
                        and not re.search(r"charset=['\"]?utf-8\b", content_type, re.I))):
                receipt["decision"] = "STATUS_REDIRECT_SIZE_OR_CHARSET_HOLD"
            else:
                htmls[role] = body.decode("utf-8", errors="strict")
                receipt["decision"] = "NATIVE_HTTP200_NOT_FIELD_PASS" if native else "MOCK_HTTP200_NOT_NATIVE"
        except urllib.error.HTTPError as exc:
            receipt["http_status"] = exc.code
            receipt["decision"] = "REDIRECT_BLOCKED" if 300 <= exc.code < 400 else "HTTP_ERROR_HOLD"
        except urllib.error.URLError as exc:
            receipt["error_type"] = type(exc.reason).__name__
            receipt["decision"] = ("DNS_OR_EGRESS_HOLD" if isinstance(exc.reason, socket.gaierror)
                                   else "NETWORK_OR_TLS_HOLD")
        except (TimeoutError, socket.timeout, ssl.SSLError, OSError, UnicodeError,
                ValueError, KeyError, TypeError) as exc:
            receipt["error_type"] = type(exc).__name__
            receipt["decision"] = "SOURCE_BODY_OR_NETWORK_HOLD"
        records.append(receipt)

    fields = (
        ("A", "venue_showtime", "VENUE_SHOW_NOT_SALE", "A_DETAIL"),
        ("A", "venue_hall", "VENUE_HALL", "A_DETAIL"),
        ("B", "exhibition_dates", "EXHIBITION_DATE_NOT_SALE", "B_DETAIL"),
        ("B", "open_hours", "DAILY_OPEN_HOURS_NOT_SHOWTIME", "B_DETAIL"),
        ("B", "venue_hall", "EXHIBITION_HALL_NOT_TICKET_ID", "B_DETAIL"),
    )
    result = {
        "kind": "P30_L7_NATIVE_FIVE_FIELD_SAME_RUN_REVIEW_GATE_V1",
        "attestation": ("CI_NATIVE_PUBLIC_GET_SAME_PROCESS" if native
                        else "MOCK_CALLER_SUPPLIED_NOT_NATIVE"),
        "observed_at_utc": now.isoformat(),
        "request_count": len(records),
        "native_http_200_count": sum(x["http_status"] == 200 for x in records) if native else 0,
        "source_receipts": records,
        "source_identity_dependencies": 2,
        "field_matrix": [],
        "source_consistent_fields": 0,
        "independent_native_review_ready_fields": 0,
        "formal_accepted_fields": 0, "golden_accepted_events": 0,
        "published_events": 0, "formal_pwa_feed_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
        "raw_html_saved": False,
        "decision": "SOURCE_FRESHNESS_HOLD",
    }
    def hold(reason):
        result["decision"] = reason
        result["field_matrix"] = [
            {"line": line, "field": field, "role": field_role,
             "source_url": dict(targets)[source_role],
             "decision": "HOLD", "formal_accepted": False}
            for line, field, field_role, source_role in fields]
        return result

    if len(htmls) != len(targets):
        return hold("NATIVE_SOURCE_ACQUISITION_INCOMPLETE_HOLD")
    if native and any(
            abs((now - datetime.fromisoformat(x["observed_at_utc"])).total_seconds()) > 120
            for x in records):
        return hold("NATIVE_SNAPSHOT_TIME_SKEW_HOLD")
    try:
        a = build_non_session_list_detail_candidate(
            PUBLIC_TMC_LIST, htmls["A_LIST"], PUBLIC_TMC_DETAIL, htmls["A_DETAIL"],
            "小宇 宋念宇 《不，完美的人》 演唱會", "P1DF32E2",
            records[1]["observed_at_utc"], now_utc=(
                datetime.now(timezone.utc) if native else now))
        b = build_non_session_list_detail_candidate(
            PUBLIC_TWTC_LIST, htmls["B_LIST"], PUBLIC_TWTC_DETAIL, htmls["B_DETAIL"],
            "2026年電器空調影音大展", "29418",
            records[4]["observed_at_utc"], now_utc=(
                datetime.now(timezone.utc) if native else now))
        # Conflict policy: LIST and DETAIL must agree on date and hall for
        # the SAME exact event row; KHAM product page must identify this act.
        a_row = a["list_row_text"]
        b_row = b["list_row_text"]
        if not ("2026.11.07" in a_row and "表演廳" in a_row):
            raise ValueError("A_LIST_DETAIL_SHOW_HALL_CONFLICT")
        if not (re.search(r"11/06\s*[~～]\s*11/09", b_row)
                and "世貿一館" in b_row):
            raise ValueError("B_LIST_DETAIL_PERIOD_HALL_CONFLICT")
        kham = re.sub(r"\s+", "", htmls["A_KHAM"])
        if not ("宋念宇" in kham and "不，完美的人" in kham):
            raise ValueError("A_KHAM_PRODUCT_EVENT_TITLE_UNVERIFIED")
        if (a["identity"]["product_id"] != "P1DF32E2"
                or b["identity"]["exhibition_id"] != "29418"):
            raise ValueError("CROSS_SOURCE_IDENTITY_CONFLICT")
        a_fields = {x["field"]: x for x in a["candidate_fields"]}
        b_fields = {x["field"]: x for x in b["candidate_fields"]}
        receipt_by_role = {x["role"]: x for x in records}
        result["field_matrix"] = [
            {"line": line, "field": field, "role": field_role,
             "source_url": receipt_by_role[source_role]["url"],
             "body_sha256": receipt_by_role[source_role]["body_sha256"],
             "observed_at_utc": receipt_by_role[source_role]["observed_at_utc"],
             "value": (a_fields if line == "A" else b_fields)[field]["value"],
             "decision": ("INDEPENDENT_NATIVE_REVIEW_READY_NOT_FORMAL"
                          if native else "MOCK_SOURCE_CONSISTENT_NOT_NATIVE"),
             "formal_accepted": False}
            for line, field, field_role, source_role in fields]
        result["source_consistent_fields"] = len(fields)
        result["independent_native_review_ready_fields"] = len(fields) if native else 0
        result["decision"] = ("NATIVE_SOURCE_BOUND_REVIEW_READY_NOT_GOLDEN" if native
                              else "MOCK_ONLY_NOT_NATIVE_OR_GOLDEN")
    except (ValueError, KeyError, TypeError) as exc:
        result["hold_reason"] = str(exc)[:100]
        return hold("IDENTITY_FIELD_OR_CONFLICT_HOLD")
    return result



# Independent cross-language conflict scope, NOT a native GET or publication authority.
# Same TWTC exhibition ID may corroborate dates/hours/hall while a stale translated
# title year must remain HOLD. Caller-transcribed reader values never prove freshness.
def adjudicate_twtc_bilingual_same_id(cn, en):
    """Scope official bilingual disagreement per field; all results remain REVIEW/HOLD."""
    import re
    from datetime import datetime
    expected = (
        ("https://twtc.com.tw/exhibition_more.aspx?id=29418&p=home", "ZH"),
        ("https://www.twtc.com.tw/en/exhibition_More.aspx?id=29418&p=home", "EN"),
    )
    def check(record, url, language):
        if (not isinstance(record, dict) or record.get("source_url") != url
                or record.get("language") != language
                or record.get("exhibition_id") != "29418"
                or record.get("evidence_kind") != "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE"):
            raise ValueError("BILINGUAL_SOURCE_ID_OR_ATTESTATION_HOLD")
        try:
            when = datetime.fromisoformat(record["observed_at_utc"].replace("Z", "+00:00"))
            if when.utcoffset() is None:
                raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValueError("BILINGUAL_OBSERVATION_CLOCK_HOLD")
    check(cn, *expected[0])
    check(en, *expected[1])

    def period(record):
        d = record.get("dates")
        if not isinstance(d, dict) or set(d) != {"start", "end"}:
            raise ValueError("BILINGUAL_DATE_SCHEMA_HOLD")
        try:
            a, b = (datetime.strptime(d[k], "%Y/%m/%d") for k in ("start", "end"))
        except (TypeError, ValueError, KeyError):
            raise ValueError("BILINGUAL_DATE_VALUE_HOLD")
        if a > b:
            raise ValueError("BILINGUAL_DATE_ORDER_HOLD")
        return (a.strftime("%Y/%m/%d"), b.strftime("%Y/%m/%d"))

    def hours(record):
        h = record.get("hours")
        if not isinstance(h, dict) or set(h) != {"open", "close"}:
            raise ValueError("BILINGUAL_HOURS_SCHEMA_HOLD")
        def norm(x):
            if not isinstance(x, str) or not re.fullmatch(
                    r"(?:[01]?\d|2[0-3])(?::[0-5]\d)?", x):
                raise ValueError("BILINGUAL_HOURS_VALUE_HOLD")
            parts = x.split(":")
            return f"{int(parts[0]):02d}:{parts[1] if len(parts) == 2 else '00'}"
        a, b = norm(h["open"]), norm(h["close"])
        if a >= b:
            raise ValueError("BILINGUAL_HOURS_ORDER_HOLD")
        return a, b

    dates_ok = period(cn) == period(en)
    hours_ok = hours(cn) == hours(en)
    # Only the explicitly identified official TWTC Hall 1 translation is in scope.
    hall_ok = cn.get("hall") == "世貿一館" and en.get("hall") == "Hall 1"
    if not all(isinstance(x.get("title"), str) for x in (cn, en)):
        raise ValueError("BILINGUAL_TITLE_SCHEMA_HOLD")
    year_cn = re.search(r"20\d{2}", cn["title"])
    year_en = re.search(r"20\d{2}", en["title"])
    title_conflict = bool(year_cn and year_en and year_cn.group() != year_en.group())
    fields = (
        ("exhibition_dates", dates_ok, "CROSS_LANGUAGE_DATE_MISMATCH_HOLD"),
        ("open_hours", hours_ok, "CROSS_LANGUAGE_HOURS_MISMATCH_HOLD"),
        ("venue_hall", hall_ok, "CROSS_LANGUAGE_HALL_IDENTITY_HOLD"),
    )
    return {
        "kind": "P30_L7_TWTC_BILINGUAL_FIELD_CONFLICT_V1",
        "source_identity": "TWTC_EXHIBITION_ID_29418_NOT_TICKET_SESSION",
        "input_attestation": "CALLER_SUPPLIED_READER_VALUES_NOT_NATIVE_GET",
        "source_freshness": "READER_TIMESTAMP_NOT_NATIVE_ATTESTATION",
        "title_decision": ("HOLD_CROSS_LANGUAGE_TITLE_YEAR_CONFLICT" if title_conflict
                           else "HOLD_TRANSLATION_NOT_INDEPENDENTLY_ATTESTED"),
        "field_matrix": [
            {"field": name,
             "decision": ("REVIEW_BILINGUAL_AGREEMENT_NOT_NATIVE" if ok else hold),
             "formal_accepted": False}
            for name, ok, hold in fields
        ],
        "source_consistent_fields": sum(ok for _, ok, _ in fields),
        "independent_formal_ready_fields": 0,
        "formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "formal_pwa_feed_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }





# Third official public source: the executing agency's event page corroborates
# venue dates/hours/hall and the Chinese 2026 year. It has NO TWTC exhibition
# ID and its reader transcript is NOT a native GET, source-body hash or formal
# acceptance authority. Keep the English 2025 title disagreement quarantined.
def adjudicate_twtc_executing_agency_public_crosscheck(cn, en, agency):
    """Corroborate field roles across TWTC and event executor; fail closed."""
    from datetime import datetime, timedelta, timezone
    bilingual = adjudicate_twtc_bilingual_same_id(cn, en)
    required = {
        "source_url": "https://www.sheng-dong.com.tw/activity/appliances-expo/TECO",
        "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
        "event_label": "2026台北電器空調影音展",
        "organizer": "台北市電器商業同業公會",
        "executor": "生動國際展覽事業股份有限公司",
        "venue": "台北世貿一館",
        "dates": {"start": "2026/11/06", "end": "2026/11/09"},
        "hours": {"open": "10:00", "close": "18:00"},
    }
    if not isinstance(agency, dict) or any(agency.get(k) != v for k,v in required.items()):
        raise ValueError("EXECUTOR_SOURCE_OR_FIELD_CONFLICT_HOLD")
    if (cn.get("title") != "2026年電器空調影音大展"
            or en.get("title") != "2025 ELECTRIC APPLIANCE FAIR"
            or cn.get("dates") != required["dates"]
            or cn.get("hours") != required["hours"]
            or cn.get("hall") != "世貿一館"
            or bilingual["source_consistent_fields"] != 3
            or bilingual["title_decision"] != "HOLD_CROSS_LANGUAGE_TITLE_YEAR_CONFLICT"):
        raise ValueError("TWTC_ID_OR_TRANSLATION_CONFLICT_NOT_ISOLATED")
    try:
        observations = []
        for record in (cn, en, agency):
            stamp = datetime.fromisoformat(record["observed_at_utc"].replace("Z", "+00:00"))
            if stamp.utcoffset() is None:
                raise ValueError()
            observations.append(stamp.astimezone(timezone.utc))
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ValueError("EXECUTOR_READER_CLOCK_UNATTESTED")
    if max(observations)-min(observations)>timedelta(hours=24):
        raise ValueError("EXECUTOR_READER_CLOCK_SKEW_HOLD")
    return {
        "kind": "P30_L7_TWTC_EXECUTOR_THIRD_SOURCE_REVIEW_V1",
        "source_roles": ["TWTC_ZH_EXHIBITION_29418", "TWTC_EN_EXHIBITION_29418",
                         "EXECUTING_AGENCY_NO_TWTC_EVENT_ID"],
        "source_count": 3,
        "identity_decision": "HOLD_EXECUTOR_HAS_NO_DIRECT_TWTC_ID",
        "title_decision": "HOLD_EN_2025_VS_ZH_AND_EXECUTOR_2026",
        "source_freshness": "READER_CLOCK_ONLY_NATIVE_GET_NOT_ATTESTED",
        "field_matrix": [
            {"field": field, "decision": "THIRD_SOURCE_CORROBORATED_REVIEW_NOT_NATIVE",
             "formal_accepted": False}
            for field in ("exhibition_dates", "open_hours", "venue_hall")
        ],
        "formal_accepted_fields": 0, "golden_accepted_events": 0,
        "published_events": 0, "formal_pwa_feed_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }



# TWTC April/November records share an organizer and telephone number. These are
# NOT event keys. This source-observed negative identity edge prevents a bilingual
# November record from inheriting the April title, dates or a ticket Session.
# All inputs are caller-transcribed public-reader evidence, never native GET.
def adjudicate_twtc_same_organizer_collision(cn, en, april, now_utc):
    """Prove same organizer != same event ID; keep five candidate fields unaccepted."""
    from datetime import datetime, timedelta, timezone
    bilingual = adjudicate_twtc_bilingual_same_id(cn, en)
    expected = {
        "source_url": "https://www.twtc.com.tw/en/exhibition_More.aspx?id=29417&p=menu1",
        "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
        "exhibition_id": "29417",
        "title": "THE 36TH TAIPEI ELECTRIC APPLIANCE FAIR",
        "organizer": "TAIPEI ELECTRICAL COMMERCIAL ASSOCIATION",
        "organizer_phone": "886-2-25064871Ext26",
        "dates": {"start": "2026/04/10", "end": "2026/04/13"},
        "hours": {"open": "10:00", "close": "18:00"},
    }
    if not isinstance(april, dict) or any(april.get(k) != v for k, v in expected.items()):
        raise ValueError("TWTC_NEIGHBOR_EVENT_IDENTITY_HOLD")
    if (cn.get("organizer") != "台北市電器商業同業公會"
            or en.get("organizer") != expected["organizer"]
            or cn.get("organizer_phone") != expected["organizer_phone"]
            or en.get("organizer_phone") != expected["organizer_phone"]
            or cn.get("title") != "2026年電器空調影音大展"
            or en.get("title") != "2025 ELECTRIC APPLIANCE FAIR"
            or bilingual["source_consistent_fields"] != 3
            or bilingual["title_decision"] != "HOLD_CROSS_LANGUAGE_TITLE_YEAR_CONFLICT"):
        raise ValueError("TWTC_ORGANIZER_OR_TITLE_CONFLICT_HOLD")
    if not isinstance(now_utc, datetime) or now_utc.utcoffset() is None:
        raise ValueError("INDEPENDENT_READER_CLOCK_UNATTESTED")
    now_utc = now_utc.astimezone(timezone.utc)
    for record in (cn, en, april):
        try:
            stamp = datetime.fromisoformat(record["observed_at_utc"].replace("Z", "+00:00"))
            if stamp.utcoffset() is None:
                raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValueError("TWTC_READER_CLOCK_UNATTESTED")
        age = now_utc - stamp.astimezone(timezone.utc)
        if not timedelta(minutes=-5) <= age <= timedelta(hours=24):
            raise ValueError("TWTC_READER_CLOCK_STALE_OR_FUTURE")
    if (cn["exhibition_id"] == april["exhibition_id"]
            or cn["dates"] == april["dates"]
            or en["dates"] == april["dates"]):
        raise ValueError("TWTC_CROSS_EVENT_COLLISION_HOLD")
    return {
        "kind": "P30_L7_TWTC_ORGANIZER_PHONE_COLLISION_V1",
        "source_identity": "NOVEMBER_29418_NOT_APRIL_29417",
        "organizer_phone_parity": "MATCHES_BUT_NOT_EVENT_IDENTITY",
        "negative_identity_edge": "REJECT_SAME_ORGANIZER_PHONE_DIFFERENT_ID_DATE",
        "bilingual_title": "HOLD_EN_2025_VS_ZH_2026",
        "independent_source_freshness": "READER_CLOCK_BOUNDED_NOT_NATIVE_GET",
        "reviewable_non_session_fields": 3,
        "independent_formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "formal_pwa_feed_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }


# Independent exported native-evidence audit. Caller-provided JSON and internal SHA
# consistency do not authenticate the downloaded ZIP or grant field acceptance.
# This gate never issues HTTP requests or writes production data.
def audit_native_same_session_field_matrix(matrix, now_utc=None):
    import re
    from datetime import datetime, timezone, timedelta
    urls = (
        'https://www.tmc.taipei/tw/blog/show/2026SungNien-Yu',
        'https://twtc.com.tw/exhibition?p=home',
        'https://twtc.com.tw/exhibition_more.aspx?id=29418&p=home',
    )
    title = '2026年電器空調影音大展'
    ticket = 'https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2'
    expected = (
        ('A','direct_ticket_product','LOCAL_PURCHASE_ANCHOR_NOT_SESSION',urls[0],
         {'product_id':'P1DF32E2','official_ticket_url':ticket}),
        ('A','venue_showtime','VENUE_SHOW_NOT_SALE',urls[0],'2026/11/07 19:30'),
        ('A','venue_hall','VENUE_HALL',urls[0],'臺北流行音樂中心 表演廳'),
        ('B','list_detail_identity','SAME_ROW_SAME_ID',urls[1],
         {'exhibition_id':'29418','same_row_title':title}),
        ('B','exhibition_title','EXACT_EVENT_TITLE',urls[2],title),
        ('B','exhibition_dates','EXHIBITION_DATE_NOT_SALE',urls[2],
         {'start':'2026/11/06','end':'2026/11/09'}),
        ('B','open_hours','DAILY_OPEN_HOURS_NOT_SHOWTIME',urls[2],
         {'open':'10:00','close':'18:00'}),
        ('B','venue_hall','EXHIBITION_HALL_NOT_TICKET_ID',urls[2],'世貿一館'),
    )
    result = {
        'kind':'P30_L7_INDEPENDENT_NATIVE_ARTIFACT_AUTHORITY_AUDIT_V1',
        'internally_consistent_native_sources':0,'source_bound_review_fields':0,
        'field_matrix':[{'line':line,'field':field,'decision':'HOLD_UNVERIFIED',
                         'formal_accepted':False} for line,field,_,_,_ in expected
                        if field not in ('direct_ticket_product','list_detail_identity','exhibition_title')],
        'identity_dependencies':{
            'A_KHAM':'HOLD_KHAM_PRODUCT_DETAIL_NOT_NATIVE_FETCHED',
            'B_TWTC':'HOLD_NATIVE_SAME_ID_NOT_VALIDATED'},
        'independent_artifact_integrity':'HOLD_EXTERNAL_ZIP_CRC_SHA_READBACK_REQUIRED',
        'independent_formal_authority':'HOLD_NOT_DELEGATED',
        'bilingual_title':'HOLD_TWTC_EN_2025_VS_ZH_2026_SOURCE_CONFLICT',
        'formal_accepted_fields':0,'golden_accepted_events':0,
        'published_events':0,'formal_pwa_feed_events':0,
        'release_state':'HARD_HOLD_NO_PUBLICATION','decision':'HOLD_SOURCE_EVIDENCE',
    }
    def fail(reason):
        result['hold_reason']=reason
        return result
    if now_utc is None: now_utc=datetime.now(timezone.utc)
    if not isinstance(now_utc,datetime) or now_utc.utcoffset() is None:
        return fail('AUDIT_CLOCK_UNATTESTED')
    now_utc=now_utc.astimezone(timezone.utc)
    if not isinstance(matrix,dict) or matrix.get('kind')!='P30_L7_NATIVE_SAME_SESSION_FIELD_MATRIX_V1':
        return fail('NATIVE_ARTIFACT_KIND_UNVERIFIED')
    if (matrix.get('request_count')!=3 or matrix.get('native_http_200')!=3
            or matrix.get('acceptability_review')!=8 or matrix.get('hold')!=0
            or matrix.get('raw_html_saved') is not False
            or matrix.get('release_state')!='HARD_HOLD_NO_PUBLICATION'
            or any(matrix.get(k)!=0 for k in ('formal_accepted_fields','golden','published'))):
        return fail('NATIVE_ARTIFACT_RELEASE_OR_COUNTS_CONFLICT')
    sources=matrix.get('sources')
    if not isinstance(sources,list) or len(sources)!=3:
        return fail('NATIVE_SOURCE_COUNT_HOLD')
    by_url={}
    times=[]
    for source in sources:
        if not isinstance(source,dict) or source.get('url') not in urls:
            return fail('NATIVE_SOURCE_URL_HOLD')
        url=source['url']
        if url in by_url: return fail('NATIVE_DUPLICATE_SOURCE_HOLD')
        if (source.get('http_status')!=200 or source.get('decision')!='NATIVE_PARSED_REVIEW_ONLY'
                or not isinstance(source.get('bytes'),int)
                or not 0<source['bytes']<=524288
                or not isinstance(source.get('sha256'),str)
                or not re.fullmatch('[0-9a-f]{64}',source['sha256'])):
            return fail('NATIVE_SOURCE_BODY_HASH_STATUS_HOLD')
        try:
            observed=datetime.fromisoformat(source['observed_at_utc'].replace('Z','+00:00'))
            if observed.utcoffset() is None: raise ValueError()
            observed=observed.astimezone(timezone.utc)
        except (KeyError,TypeError,ValueError,AttributeError):
            return fail('NATIVE_SOURCE_CLOCK_HOLD')
        if not timedelta(minutes=-5)<=now_utc-observed<=timedelta(hours=24):
            return fail('NATIVE_SOURCE_STALE_OR_FUTURE_HOLD')
        times.append(observed)
        by_url[url]=source
    if set(by_url)!=set(urls) or max(times)-min(times)>timedelta(minutes=10):
        return fail('NATIVE_SOURCE_SAME_RUN_SKEW_HOLD')
    receipts=matrix.get('field_receipts')
    if not isinstance(receipts,list) or len(receipts)!=8:
        return fail('NATIVE_FIELD_RECEIPT_COUNT_HOLD')
    by_key={}
    for receipt in receipts:
        if not isinstance(receipt,dict): return fail('NATIVE_FIELD_RECEIPT_SCHEMA_HOLD')
        key=(receipt.get('line'),receipt.get('field'))
        if key in by_key: return fail('NATIVE_DUPLICATE_FIELD_HOLD')
        by_key[key]=receipt
    for line,field,role,url,value in expected:
        receipt=by_key.get((line,field))
        if receipt is None: return fail('NATIVE_FIELD_MISSING_HOLD')
        source=by_url[url]
        if (receipt.get('event_id')!=('P1DF32E2' if line=='A' else '29418')
                or receipt.get('role')!=role or receipt.get('source_url')!=url
                or receipt.get('observed_at_utc')!=source['observed_at_utc']
                or receipt.get('body_sha256')!=source['sha256']
                or receipt.get('native_same_session_match') is not True
                or receipt.get('observed_value')!=value
                or receipt.get('value_basis')!='EXACT_SOURCE_LOCAL_PATTERN_OR_ANCHOR'
                or receipt.get('decision')!='ACCEPTABLE_FOR_INDEPENDENT_GOLDEN_REVIEW_ONLY'
                or receipt.get('formal_accepted') is not False):
            return fail('NATIVE_FIELD_VALUE_IDENTITY_PROVENANCE_HOLD')
    result['internally_consistent_native_sources']=3
    result['source_bound_review_fields']=5
    result['identity_dependencies']['B_TWTC']='NATIVE_SAME_ROW_SAME_ID_REVIEW_NOT_FORMAL'
    result['field_matrix']=[{'line':line,'field':field,
        'source_url':url,'body_sha256':by_url[url]['sha256'],
        'decision':'NATIVE_VALUE_REVIEW_PENDING_INDEPENDENT_AUTHORITY',
        'formal_accepted':False} for line,field,_,url,_ in expected
        if field not in ('direct_ticket_product','list_detail_identity','exhibition_title')]
    result['decision']='INTERNAL_RECEIPT_PARITY_ONLY_FORMAL_AUTHORITY_HOLD'
    return result


def audit_downloaded_native_artifact_zip(zip_bytes, github_digest, expected_head, now_utc):
    """Independently validate downloaded evidence bytes; never authorize Golden."""
    import hashlib
    import io
    import re
    import zipfile

    outcome = {
        'decision': 'HOLD_UNVERIFIED_ARTIFACT',
        'zip_sha256': 'HOLD', 'zip_crc': 'HOLD',
        'evidence_member_hashes': 'HOLD',
        'native_receipt_parity': 'HOLD',
        'independently_verified_evidence_members': 0,
        'formal_accepted_fields': 0, 'golden_accepted_events': 0,
        'published_events': 0, 'formal_pwa_feed_events': 0,
        'raw_source_html_verified': False,
        'code_files_in_zip_verified': False,
        'independent_field_authority': 'HOLD',
        'release_state': 'HARD_HOLD_NO_PUBLICATION',
    }
    def refuse(reason):
        outcome['decision'] = 'HOLD_' + reason
        return outcome
    if (not isinstance(zip_bytes, bytes) or not 0 < len(zip_bytes) <= 2_000_000
            or not isinstance(github_digest, str)
            or not re.fullmatch(r'sha256:[0-9a-f]{64}', github_digest)
            or not isinstance(expected_head, str)
            or not re.fullmatch(r'[0-9a-f]{40}', expected_head)):
        return refuse('ARTIFACT_INPUT_SCHEMA')
    if hashlib.sha256(zip_bytes).hexdigest() != github_digest.split(':', 1)[1]:
        return refuse('GITHUB_DIGEST_MISMATCH')
    outcome['zip_sha256'] = 'PASS'
    names = {
        'SHA256SUMS.txt', 'readiness.txt',
        'native_same_session_field_matrix.json', 'field_subset_review_proposal.json',
    }
    manifest_paths = {
        '.github/workflows/eventradar_p30_l7_field_readiness.yml',
        'scripts/p30_l7_field_golden_readiness.py',
        'tests/p30/test_p30_l7_field_golden_readiness.py',
        'tests/p30/fixtures/p30_l7_prince_field_readiness.json',
        'evidence/readiness.txt',
        'evidence/native_same_session_field_matrix.json',
        'evidence/field_subset_review_proposal.json',
    }
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            infos = z.infolist()
            if (len(infos) != 4 or {x.filename for x in infos} != names
                    or any(x.is_dir() or x.flag_bits & 1 or x.file_size > 500_000
                           for x in infos)):
                return refuse('ZIP_MEMBERS_OR_LIMITS')
            if z.testzip() is not None:
                return refuse('ZIP_CRC')
            outcome['zip_crc'] = 'PASS'
            lines = z.read('SHA256SUMS.txt').decode('utf-8').splitlines()
            entries = {}
            for line in lines:
                match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
                if not match or match.group(2) in entries:
                    return refuse('MANIFEST_SCHEMA_OR_DUPLICATE')
                entries[match.group(2)] = match.group(1)
            if set(entries) != manifest_paths:
                return refuse('MANIFEST_PATH_SET')
            for member in names - {'SHA256SUMS.txt'}:
                if hashlib.sha256(z.read(member)).hexdigest() != entries['evidence/' + member]:
                    return refuse('MANIFEST_EVIDENCE_HASH')
            outcome['evidence_member_hashes'] = 'PASS'
            outcome['independently_verified_evidence_members'] = 3
            readiness = z.read('readiness.txt').decode('utf-8')
            if (f'head={expected_head}\n' not in readiness
                    or 'formal_fields=0\n' not in readiness
                    or 'golden=0\n' not in readiness
                    or 'published=0\n' not in readiness):
                return refuse('HEAD_OR_RELEASE_READINESS')
            matrix = json.loads(z.read('native_same_session_field_matrix.json'))
    except (zipfile.BadZipFile, UnicodeDecodeError, KeyError, ValueError,
            OSError, RuntimeError, TypeError):
        return refuse('ZIP_READ_OR_JSON')
    reviewed = audit_native_same_session_field_matrix(matrix, now_utc)
    if (reviewed.get('internally_consistent_native_sources') != 3
            or reviewed.get('source_bound_review_fields') != 5
            or len(reviewed.get('field_matrix', [])) != 5):
        return refuse('NATIVE_RECEIPT_PARITY_OR_FRESHNESS')
    outcome['native_receipt_parity'] = 'PASS_INTERNAL_ONLY'
    outcome['decision'] = 'ARTIFACT_INTEGRITY_PASS_FORMAL_AUTHORITY_HOLD'
    return outcome


# 2026-11-04: Independent public executor index shows three different exhibitions
# sharing the same dates and hall. Date+hall is therefore a NEGATIVE identity
# discriminator, never an event-ID bridge or independent Golden authority.
# Caller-transcribed public-reader evidence is not a native HTTP receipt.
def audit_executor_same_day_venue_collision(index, now_utc):
    from datetime import datetime, timedelta, timezone
    expected_titles = {
        "2026台北電器空調影音大展｜超越雙11家電週年慶",
        "台北Méng萌寵物用品展",
        "2026玩轉文具暨手作創意展｜11/6-9世貿一館",
    }
    if (not isinstance(index, dict)
            or index.get("source_url") != "https://www.sheng-dong.com.tw/"
            or index.get("evidence_kind") != "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE"
            or index.get("native_official_get") != 0
            or index.get("formal_accepted_fields") != 0
            or index.get("golden_accepted_events") != 0
            or index.get("published_events") != 0):
        raise ValueError("EXECUTOR_INDEX_PROVENANCE_OR_RELEASE_HOLD")
    if not isinstance(now_utc, datetime) or now_utc.utcoffset() is None:
        raise ValueError("EXECUTOR_INDEX_AUDITOR_CLOCK_HOLD")
    try:
        observed = datetime.fromisoformat(
            index["observed_at_utc"].replace("Z", "+00:00"))
        if observed.utcoffset() is None:
            raise ValueError()
    except (KeyError, AttributeError, TypeError, ValueError):
        raise ValueError("EXECUTOR_INDEX_READER_CLOCK_HOLD")
    age = now_utc.astimezone(timezone.utc) - observed.astimezone(timezone.utc)
    if not timedelta(minutes=-5) <= age <= timedelta(hours=24):
        raise ValueError("EXECUTOR_INDEX_STALE_OR_FUTURE_HOLD")
    rows = index.get("events")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("EXECUTOR_INDEX_COLLISION_ROW_COUNT_HOLD")
    titles = set()
    for row in rows:
        if (not isinstance(row, dict)
                or row.get("title") not in expected_titles
                or row.get("start_date") != "2026/11/06"
                or row.get("end_date") != "2026/11/09"
                or row.get("venue") != "台北世貿一館"
                or row.get("twtc_exhibition_id") is not None
                or row.get("ticket_session_id") is not None):
            raise ValueError("EXECUTOR_INDEX_CROSS_EVENT_ID_OR_ROLE_HOLD")
        if row["title"] in titles:
            raise ValueError("EXECUTOR_INDEX_DUPLICATE_EVENT_HOLD")
        titles.add(row["title"])
    if titles != expected_titles:
        raise ValueError("EXECUTOR_INDEX_UNEXPECTED_EVENT_SET_HOLD")
    return {
        "kind": "P30_L7_EXECUTOR_SAME_DAY_VENUE_COLLISION_V1",
        "distinct_event_labels": 3,
        "shared_date_venue_is_unique_event_identity": False,
        "twtc_id_29418_from_executor_index": None,
        "identity_decision": "REJECT_DATE_VENUE_ONLY_CROSS_EVENT_MERGE",
        "A_tmc_non_session_fields": "2_REVIEW_UNCHANGED",
        "B_twtc_non_session_fields": "3_REVIEW_UNCHANGED",
        "native_official_get": 0,
        "independent_formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "formal_pwa_feed_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }



def audit_twtc_official_same_id_host_mirror(receipt, now_taipei):
    """Public-reader official mirror identity only; no native GET or formal acceptance."""
    from urllib.parse import urlsplit, parse_qs
    if now_taipei.tzinfo is None or now_taipei.utcoffset() is None:
        raise ValueError("MIRROR_CLOCK_MUST_HAVE_OFFSET")
    expected = {
        "index_url": "https://twtc.org.tw/exhibition.aspx",
        "mirror_detail_url": "https://twtc.org.tw/exhibition_more.aspx?id=29418&p=home",
        "primary_detail_url": "https://www.twtc.com.tw/exhibition_more.aspx?id=29418&p=menu1",
        "organizer_url": "https://www.teca.org.tw/",
        "organizer_edge_scope": "ORGANIZER_HOMEPAGE_ONLY_NOT_EVENT_ID",
        "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
        "observed_date_taipei": "2026-11-04",
        "event_title": "2026年電器空調影音大展",
        "organizer": "台北市電器商業同業公會",
        "date_start": "2026/11/06",
        "date_end": "2026/11/09",
        "hours": "10:00 ~ 18:00",
        "venue": "世貿一館",
        "native_official_get": 0,
        "formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "formal_pwa_feed_events": 0,
    }
    if type(receipt) is not dict or set(receipt) != set(expected):
        raise ValueError("MIRROR_RECEIPT_SHAPE_HOLD")
    for key, value in expected.items():
        if type(receipt[key]) is not type(value) or receipt[key] != value:
            raise ValueError("MIRROR_RECEIPT_MISMATCH_" + key)
    if (datetime.fromisoformat(receipt["observed_date_taipei"]).date()
            != now_taipei.date()):
        raise ValueError("MIRROR_READER_DATE_STALE")
    for key in ("mirror_detail_url", "primary_detail_url"):
        u = urlsplit(receipt[key])
        if parse_qs(u.query).get("id") != ["29418"]:
            raise ValueError("MIRROR_EVENT_ID_HOLD")
    return {
        "kind": "P30_L7_TWTC_OFFICIAL_SAME_ID_HOST_MIRROR_READER_V1",
        "same_id_official_host_pair": 2,
        "source_local_identity": "REVIEW_CORROBORATED_SAME_TWTC_ID_29418",
        "field_roles": {"exhibition_dates": "REVIEW", "daily_open_hours": "REVIEW", "hall": "REVIEW"},
        "organizer_homepage_is_event_identity": False,
        "executor_to_twtc_id_edge": "HOLD",
        "english_title_year_conflict": "HOLD",
        "native_official_get": 0,
        "independent_formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "formal_pwa_feed_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }



def audit_native_source_link_edges(tmc_html, twtc_index_html, twtc_detail_html,
                                   receipts, now_utc):
    """Native public-page link edges; no checkout request, formal acceptance or fuzzy join.

    A: TMC event detail -> exact KHAM product URL (not a ticket Session).
    B: TWTC index SAME ROW -> exact id=29418 detail -> same-event field labels.
    """
    import re
    from html.parser import HTMLParser
    from urllib.parse import urljoin
    from datetime import timezone, timedelta

    urls = (
        "https://www.tmc.taipei/tw/blog/show/2026SungNien-Yu",
        "https://twtc.org.tw/exhibition.aspx",
        "https://twtc.org.tw/exhibition_more.aspx?id=29418&p=home",
    )
    if not isinstance(now_utc, datetime) or now_utc.utcoffset() is None:
        raise ValueError("NATIVE_LINK_AUDITOR_CLOCK_HOLD")
    if not isinstance(receipts, list) or len(receipts) != 3:
        raise ValueError("NATIVE_LINK_RECEIPT_COUNT_HOLD")
    for receipt, url in zip(receipts, urls):
        if not isinstance(receipt, dict) or receipt.get("url") != url:
            raise ValueError("NATIVE_LINK_SOURCE_URL_HOLD")
        if receipt.get("http_status") != 200 or receipt.get("decision") != "NATIVE_HTTP200_BODY_HASH_ONLY":
            raise ValueError("NATIVE_LINK_HTTP_AUTHORITY_HOLD")
        if (not isinstance(receipt.get("body_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", receipt["body_sha256"])
                or type(receipt.get("bytes")) is not int
                or not 0 < receipt["bytes"] <= 524288):
            raise ValueError("NATIVE_LINK_BODY_RECEIPT_HOLD")
        try:
            observed = datetime.fromisoformat(receipt["observed_at_utc"].replace("Z", "+00:00"))
            age = now_utc.astimezone(timezone.utc) - observed.astimezone(timezone.utc)
            if observed.utcoffset() is None or not timedelta(minutes=-5) <= age <= timedelta(hours=24):
                raise ValueError()
        except (KeyError, TypeError, AttributeError, ValueError):
            raise ValueError("NATIVE_LINK_FRESHNESS_HOLD")

    class AnchorsAndRows(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.anchors, self.rows, self.current_anchor, self.current_row = [], [], None, None
            self.hidden = 0
        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self.hidden += 1
            if tag == "tr":
                if self.current_row is not None:
                    raise ValueError("NESTED_ROW_HOLD")
                self.current_row = {"text": [], "hrefs": []}
            if tag == "a":
                if self.current_anchor is not None:
                    raise ValueError("NESTED_ANCHOR_HOLD")
                self.current_anchor = {"href": dict(attrs).get("href", ""), "text": []}
                if self.current_row is not None:
                    self.current_row["hrefs"].append(self.current_anchor["href"])
        def handle_data(self, data):
            if self.hidden:
                return
            if self.current_anchor is not None:
                self.current_anchor["text"].append(data)
            if self.current_row is not None:
                self.current_row["text"].append(data)
        def handle_endtag(self, tag):
            if tag in ("script", "style"):
                self.hidden = max(0, self.hidden - 1)
            if tag == "a" and self.current_anchor is not None:
                self.current_anchor["text"] = " ".join(" ".join(self.current_anchor["text"]).split())
                self.anchors.append(self.current_anchor)
                self.current_anchor = None
            if tag == "tr" and self.current_row is not None:
                self.current_row["text"] = " ".join(" ".join(self.current_row["text"]).split())
                self.rows.append(self.current_row)
                self.current_row = None

    parsers = []
    for body in (tmc_html, twtc_index_html, twtc_detail_html):
        if not isinstance(body, str) or not body or len(body) > 524288:
            raise ValueError("NATIVE_LINK_HTML_INPUT_HOLD")
        parser = AnchorsAndRows()
        parser.feed(body)
        parsers.append(parser)

    expected_ticket = "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2"
    # Native site can render desktop/mobile duplicate anchors and image-only labels.
    # Identity is the exact official event-page href, not visible anchor wording.
    tmc_ticket = [a for a in parsers[0].anchors
                  if urljoin(urls[0], a["href"]) == expected_ticket]
    if not 1 <= len(tmc_ticket) <= 4:
        raise ValueError("TMC_EXACT_PRODUCT_HREF_ABSENT_OR_EXCESSIVE_HOLD")
    if ("宋念宇" not in tmc_html or "2026" not in tmc_html
            or "11.07" not in tmc_html or "19:30" not in tmc_html
            or "臺北流行音樂中心" not in tmc_html or "表演廳" not in tmc_html):
        raise ValueError("TMC_EVENT_CONTEXT_HOLD")

    expected_detail = urls[2]
    rows = [row for row in parsers[1].rows
            if "2026年電器空調影音大展" in row["text"]
            and any(urljoin(urls[1], href) == expected_detail for href in row["hrefs"])]
    # Independent A/B decisions: a B layout/identity failure must not erase a
    # proven A exact href. B remains HOLD, never promoted by global title/date.
    detail_text = " ".join(twtc_detail_html.split())
    # The official index may duplicate the exact same row for desktop/mobile.
    # Accept at most two identical source-local ID/title rows; never join by date alone.
    b_row_valid = (1 <= len(rows) <= 2 and all(
        "11/06" in row["text"] and "11/09" in row["text"] for row in rows))
    b_detail_valid = all(s in detail_text for s in (
        "2026年電器空調影音大展", "世貿一館", "台北市電器商業同業公會",
        "2026/11/06", "2026/11/09", "10:00", "18:00"))
    b_valid = b_row_valid and b_detail_valid

    return {
        "kind": "P30_L7_NATIVE_OFFICIAL_SOURCE_LINK_EDGES_V1",
        "source_local_native_link_edges": 1 + int(b_valid),
        "A_venue_to_kham_product": "REVIEW_DIRECT_ANCHOR_PRODUCT_NOT_SESSION",
        "A_kham_product_same_event_native": "HOLD_NO_KHAM_GET",
        "B_twtc_index_to_same_id_detail": (
            "REVIEW_DIRECT_SAME_ROW_ID29418" if b_valid
            else "HOLD_SAME_ROW_OR_DETAIL_CONTEXT_UNPROVEN"),
        "B_executor_to_twtc_id": "HOLD_NO_EXECUTOR_ID_EDGE",
        "B_bilingual_title_year": "HOLD_2025_VS_2026",
        "field_roles": {"A_show": "REVIEW", "A_hall": "REVIEW",
                        "B_dates": "REVIEW", "B_daily_hours": "REVIEW", "B_hall": "REVIEW"},
        "formal_accepted_fields": 0, "golden": 0, "published": 0,
        "formal_pwa_feed": 0, "release_state": "HARD_HOLD_NO_PUBLICATION",
    }


def main():
    path = Path(__file__).resolve().parents[1] / "tests/p30/fixtures/p30_l7_prince_field_readiness.json"
    print(json.dumps(validate(json.loads(path.read_text(encoding="utf-8"))),sort_keys=True))
if __name__ == "__main__": main()


# Fixed source-list entry -> exact same-event DETAIL -> provenance -> existing
# REVIEW candidate pipeline. No network, checkout, formal feed, or publisher.
def build_source_adapter_review_snapshot(
        list_url, list_html, detail_url, detail_html, expected_title,
        expected_identity_id, observed_at_utc, now_utc=None, previous=None):
    """Produce a bounded in-memory LKG/diff snapshot; never a formal event."""
    import hashlib
    from urllib.parse import urlsplit
    from scripts.p30_candidate_review_pipeline import build_candidate_dataset

    def digest(rows):
        payload = json.dumps(rows, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    old_rows = []
    if previous is not None:
        if (not isinstance(previous, dict)
                or previous.get("kind") != "P30_L7_ISOLATED_SOURCE_ADAPTER_SNAPSHOT_V1"
                or previous.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
                or not isinstance(previous.get("rows"), list)
                or not previous["rows"]
                or previous.get("last_known_good_sha256") != digest(previous["rows"])):
            raise ValueError("UNTRUSTED_LAST_KNOWN_GOOD_HOLD")
        old_rows, old_quality = build_candidate_dataset(previous["rows"])
        if len(old_rows) != len(previous["rows"]) or old_quality["rejectedRows"]:
            raise ValueError("LAST_KNOWN_GOOD_SCHEMA_HOLD")

    try:
        parsed = build_non_session_list_detail_candidate(
            list_url, list_html, detail_url, detail_html, expected_title,
            expected_identity_id, observed_at_utc, now_utc)
        line = parsed["line"]
        roles = {f["field"]: f for f in parsed["candidate_fields"]}
        if line == "A":
            source_id = urlsplit(detail_url).path.rsplit("/", 1)[-1]
            platform_id, platform, event_type = (
                "TMC_OFFICIAL", "臺北流行音樂中心", "音樂會/演唱會")
            date = roles["venue_showtime"]["value"]
            location = roles["venue_hall"]["value"]
            holds = ["KHAM_PRODUCT_NOT_CHECKOUT_SESSION"]
        else:
            source_id = parsed["identity"]["exhibition_id"]
            platform_id, platform, event_type = ("16", "台北世貿", "展覽")
            period = roles["exhibition_dates"]["value"]
            date = period["start"] + " ~ " + period["end"]
            location = roles["venue_hall"]["value"]
            holds = ["TWTC_BILINGUAL_YEAR_CONFLICT_HOLD",
                     "EXECUTOR_EVENT_ID_EDGE_HOLD"]
        if not source_id or not date or not location:
            raise ValueError("SOURCE_FIELD_EMPTY_HOLD")
        stamp = parsed["observed_at_utc"]
        candidate = {
            "title": expected_title, "url": detail_url, "platform": platform,
            "type": event_type, "scraped_at": stamp,
            "date": date, "location": location,
            "_candidate": {
                "scope": "CANDIDATE_PREVIEW_ONLY",
                "decision": "REVIEW_WITH_HOLD",
                "published": False, "golden_accepted": False,
                "formal_field_pass": False,
                "record_id": platform_id + ":" + source_id,
                "platform_id": platform_id, "source_event_id": source_id,
                "source_class": "OFFICIAL_VENUE_NON_SESSION",
                "sources": [list_url, detail_url],
                "hold_reasons": ["CALLER_HTML_NOT_NATIVE_FRESHNESS_PROOF",
                                 "INDEPENDENT_FIELD_ACCEPTANCE_PENDING"] + holds,
                "field_evidence": {
                    "date": {"value": date, "source": detail_url,
                             "observed_at": stamp, "role": "VENUE_EVENT_DATE",
                             "decision": "REVIEW"},
                    "location": {"value": location, "source": detail_url,
                                 "observed_at": stamp, "role": "EVENT_VENUE",
                                 "decision": "REVIEW"},
                },
            },
        }
        rows, quality = build_candidate_dataset([candidate])
        if len(rows) != 1 or quality["rejectedRows"] != 0:
            raise ValueError("REVIEW_PIPELINE_REJECTED_SOURCE_CANDIDATE")
        old_ids = {(r["_candidate"]["platform_id"],
                    r["_candidate"]["source_event_id"]) for r in old_rows}
        new_ids = {(r["_candidate"]["platform_id"],
                    r["_candidate"]["source_event_id"]) for r in rows}
        if old_ids and not old_ids.issubset(new_ids):
            raise ValueError("SOURCE_ID_DISAPPEARED_NO_SILENT_REPLACE")
        return {
            "kind": "P30_L7_ISOLATED_SOURCE_ADAPTER_SNAPSHOT_V1",
            "decision": "REVIEW_ONLY_NEW_OR_UPDATED",
            "rows": rows, "quality": quality,
            "field_receipts": parsed["candidate_fields"],
            "source_receipts": parsed["source_receipts"],
            "incremental_diff": {
                "added_ids": sorted(new_ids - old_ids),
                "removed_ids": [],
                "changed": digest(rows) != digest(old_rows),
            },
            "last_known_good_sha256": digest(rows),
            "native_get_verified": False, "formal_accepted_fields": 0,
            "golden_accepted_events": 0, "published_events": 0,
            "release_state": "HARD_HOLD_NO_PUBLICATION",
        }
    except (ValueError, KeyError, TypeError) as exc:
        if previous is None:
            raise
        # Do not turn an empty, malformed or conflicting new scrape into an
        # empty publication. Keep the previously validated isolated candidate.
        return {
            **previous, "decision": "ROLLBACK_TO_ISOLATED_LAST_KNOWN_GOOD",
            "rollback_reason": type(exc).__name__ + ":" + str(exc)[:100],
            "incremental_diff": {"added_ids": [], "removed_ids": [],
                                 "changed": False},
        }


# Non-publishing durable LKG: one checksum-sealed JSON envelope, atomic replacement.
# Deliberately outside the repository, so neither Pages nor legacy publisher can
# discover it by walking docs/ or by calling save_data_and_notify().
def _isolated_lkg_digest(value):
    import hashlib
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("utf-8")).hexdigest()


def _isolated_lkg_path(destination, repo_root):
    target = Path(destination)
    root = Path(repo_root).resolve(strict=True)
    if target.name != "review_lkg_snapshot.json":
        raise ValueError("ISOLATED_LKG_EXACT_FILENAME_REQUIRED")
    # Reject symlink traversal before resolving the target. The caller creates
    # the isolated directory; this function never creates publication paths.
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError("ISOLATED_LKG_SYMLINK_HOLD")
    if not target.parent.is_dir():
        raise ValueError("ISOLATED_LKG_PARENT_MUST_EXIST")
    resolved = target.resolve(strict=False)
    if resolved == root or resolved.is_relative_to(root):
        raise ValueError("ISOLATED_LKG_MUST_BE_OUTSIDE_REPOSITORY")
    return target


def _validate_isolated_lkg_snapshot(snapshot):
    from scripts.p30_candidate_review_pipeline import build_candidate_dataset
    if (not isinstance(snapshot, dict)
            or snapshot.get("kind") != "P30_L7_ISOLATED_SOURCE_ADAPTER_SNAPSHOT_V1"
            or snapshot.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
            or snapshot.get("decision") not in (
                "REVIEW_ONLY_NEW_OR_UPDATED",
                "ROLLBACK_TO_ISOLATED_LAST_KNOWN_GOOD")
            or snapshot.get("native_get_verified") is not False
            or any(snapshot.get(k) != 0 for k in (
                "formal_accepted_fields", "golden_accepted_events",
                "published_events"))
            or not isinstance(snapshot.get("rows"), list)
            or len(snapshot["rows"]) != 1
            or snapshot.get("last_known_good_sha256") !=
               _isolated_lkg_digest(snapshot["rows"])):
        raise ValueError("ISOLATED_LKG_RELEASE_OR_INTEGRITY_HOLD")
    normalized, report = build_candidate_dataset(snapshot["rows"])
    if normalized != snapshot["rows"] or report["rejectedRows"] != 0:
        raise ValueError("ISOLATED_LKG_CANDIDATE_SCHEMA_HOLD")
    if (not isinstance(snapshot.get("quality"), dict)
            or snapshot["quality"].get("previewRows") != 1
            or snapshot["quality"].get("rejectedRows") != 0
            or snapshot["quality"].get("releaseState") !=
               "HARD_HOLD_NO_PUBLICATION"):
        raise ValueError("ISOLATED_LKG_QUALITY_HOLD")
    if (not isinstance(snapshot.get("field_receipts"), list)
            or not isinstance(snapshot.get("source_receipts"), dict)
            or not isinstance(snapshot.get("incremental_diff"), dict)):
        raise ValueError("ISOLATED_LKG_RECEIPTS_HOLD")
    # An acquisition receipt is optional for caller-HTML offline snapshots.
    # When present, seal exact source URLs, observation time, transport role
    # and both raw response hashes to the validated one-row REVIEW candidate.
    acquired = snapshot["source_receipts"].get("bounded_acquisition")
    if acquired is not None:
        import re
        row = snapshot["rows"][0]
        sources = row["_candidate"].get("sources")
        if (not isinstance(acquired, dict)
                or acquired.get("kind") != "P30_L7_BOUNDED_SOURCE_RECEIPTS_V1"
                or acquired.get("decision") != "SOURCE_BODY_REVIEW_ONLY_NOT_FORMAL"
                or acquired.get("transport") not in (
                    "BUILTIN_NATIVE_GET", "TEST_INJECTED_NOT_NATIVE")
                or acquired.get("observed_at_utc") != row["scraped_at"]
                or not isinstance(sources, list) or len(sources) != 2
                or acquired.get("list_url") != sources[0]
                or acquired.get("detail_url") != sources[1]
                or any(not isinstance(acquired.get(key), str)
                       or re.fullmatch(r"[0-9a-f]{64}", acquired[key]) is None
                       for key in ("list_body_sha256", "detail_body_sha256"))):
            raise ValueError("ISOLATED_LKG_ACQUISITION_PROVENANCE_HOLD")
    return snapshot


def load_isolated_review_lkg(destination, repo_root):
    """Verify one durable non-public REVIEW snapshot; missing file means None."""
    target = _isolated_lkg_path(destination, repo_root)
    if not target.exists():
        return None
    if not target.is_file() or target.stat().st_size > 262144:
        raise ValueError("ISOLATED_LKG_FILE_SIZE_OR_TYPE_HOLD")
    try:
        envelope = json.loads(target.read_text(encoding="utf-8"))
        if (not isinstance(envelope, dict)
                or set(envelope) != {"kind", "snapshot", "sha256"}
                or envelope["kind"] != "P30_L7_ISOLATED_DURABLE_LKG_V1"
                or envelope["sha256"] !=
                   _isolated_lkg_digest(envelope["snapshot"])):
            raise ValueError("ISOLATED_LKG_ENVELOPE_HASH_HOLD")
        return _validate_isolated_lkg_snapshot(envelope["snapshot"])
    except (UnicodeError, json.JSONDecodeError, TypeError, KeyError,
            OverflowError) as exc:
        raise ValueError("ISOLATED_LKG_UNREADABLE_HOLD") from exc


def persist_isolated_review_lkg(snapshot, destination, repo_root,
                                expected_previous_sha256=None):
    """Single-file fsync+replace with exclusive writer lock and LKG CAS guard."""
    import os
    import tempfile
    target = _isolated_lkg_path(destination, repo_root)
    _validate_isolated_lkg_snapshot(snapshot)
    if snapshot["decision"] != "REVIEW_ONLY_NEW_OR_UPDATED":
        raise ValueError("ISOLATED_LKG_ROLLBACK_MUST_NOT_OVERWRITE")
    lock = target.with_name(target.name + ".lock")
    lock_fd = None
    temp_name = None
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        prior = load_isolated_review_lkg(target, repo_root)
        actual_sha = (prior["last_known_good_sha256"]
                      if prior is not None else None)
        if actual_sha != expected_previous_sha256:
            raise ValueError("ISOLATED_LKG_COMPARE_AND_SWAP_HOLD")
        envelope = {"kind": "P30_L7_ISOLATED_DURABLE_LKG_V1",
                    "snapshot": snapshot,
                    "sha256": _isolated_lkg_digest(snapshot)}
        payload = (json.dumps(envelope, ensure_ascii=False, sort_keys=True,
                              allow_nan=False, separators=(",", ":")) +
                   "\n").encode("utf-8")
        if len(payload) > 262144:
            raise ValueError("ISOLATED_LKG_TOO_LARGE")
        fd, temp_name = tempfile.mkstemp(
            prefix=".review_lkg.", suffix=".tmp", dir=str(target.parent))
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, target)
        temp_name = None
        # Durable directory entry on POSIX. On Windows, the atomic replace
        # still applies; directory fsync is unavailable.
        if os.name == "posix":
            directory_fd = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        return {"path": str(target), "snapshot_sha256": envelope["sha256"],
                "last_known_good_sha256": snapshot["last_known_good_sha256"],
                "release_state": "HARD_HOLD_NO_PUBLICATION"}
    finally:
        if temp_name is not None:
            os.unlink(temp_name)
        if lock_fd is not None:
            os.close(lock_fd)
            os.unlink(lock)


def run_persistent_isolated_review_lkg(
        list_url, list_html, detail_url, detail_html, expected_title,
        expected_identity_id, observed_at_utc, destination, repo_root,
        now_utc=None):
    """Existing adapter + candidate pipeline + disk LKG; no HTTP or publishing."""
    prior = load_isolated_review_lkg(destination, repo_root)
    snapshot = build_source_adapter_review_snapshot(
        list_url, list_html, detail_url, detail_html, expected_title,
        expected_identity_id, observed_at_utc, now_utc, prior)
    if snapshot["decision"] == "ROLLBACK_TO_ISOLATED_LAST_KNOWN_GOOD":
        # The file remains byte-for-byte unchanged after a failed scrape.
        return {"snapshot": snapshot, "persisted": False,
                "release_state": "HARD_HOLD_NO_PUBLICATION"}
    receipt = persist_isolated_review_lkg(
        snapshot, destination, repo_root,
        expected_previous_sha256=(
            prior["last_known_good_sha256"] if prior else None))
    return {"snapshot": snapshot, "persisted": True, "receipt": receipt,
            "release_state": "HARD_HOLD_NO_PUBLICATION"}


# Explicit, bounded source acquisition into the existing REVIEW-only adapter.
# This is NOT invoked by main(), CI, scheduler, or the production scraper.
# A test-injected fetcher can validate integration but never establishes native GET.
def run_bounded_native_source_to_review_lkg(
        list_url, detail_url, expected_title, expected_identity_id,
        destination, repo_root, *, network_authorized=False,
        source_hypothesis="", fetcher=None, now_utc=None):
    """One-shot two-page official GET -> same-ID adapter -> durable REVIEW LKG.

    No checkout URL, redirect, retry, login, raw-page persistence, formal feed,
    Golden or publication. A real GET requires explicit authorization and a
    source-specific new hypothesis; synthetic fetchers are never native proof.
    """
    import hashlib
    import re
    import urllib.request
    from datetime import timezone

    pairs = {
        (PUBLIC_TMC_LIST, PUBLIC_TMC_DETAIL): ("A", "TMC_OFFICIAL"),
        (PUBLIC_TWTC_LIST, PUBLIC_TWTC_DETAIL): ("B", "16"),
    }
    if (list_url, detail_url) not in pairs or list_url == detail_url:
        raise ValueError("NATIVE_SOURCE_EXACT_ALLOWLIST_OR_PAIR_HOLD")
    if fetcher is None and (network_authorized is not True
                           or not isinstance(source_hypothesis, str)
                           or not 8 <= len(source_hypothesis.strip()) <= 200):
        raise ValueError("NATIVE_GET_REQUIRES_EXPLICIT_NEW_HYPOTHESIS")
    if fetcher is not None and not callable(fetcher):
        raise ValueError("NATIVE_FETCHER_NOT_CALLABLE_HOLD")
    if not isinstance(expected_title, str) or not expected_title.strip():
        raise ValueError("NATIVE_EXPECTED_TITLE_REQUIRED_HOLD")
    # Reject unsafe destinations BEFORE making a single network request.
    _isolated_lkg_path(destination, repo_root)
    previous = load_isolated_review_lkg(destination, repo_root)
    native = fetcher is None

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            return None

    def public_get(url):
        request = urllib.request.Request(
            url, method="GET",
            headers={"User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
                     "Accept": "text/html", "Accept-Encoding": "identity"})
        with urllib.request.build_opener(NoRedirect).open(
                request, timeout=8) as response:
            return (response.status, response.headers.get("Content-Type", ""),
                    response.read(524289), response.geturl())

    reader = public_get if native else fetcher
    receipts, pages = [], []
    try:
        for url in (list_url, detail_url):
            # Exactly one request per URL. Never follow a redirect or retry.
            status, content_type, raw, final_url = reader(url)
            if type(status) is not int or status != 200 or final_url != url:
                raise ValueError("NATIVE_HTTP_STATUS_OR_REDIRECT_HOLD")
            if not isinstance(raw, bytes) or not 0 < len(raw) <= 524288:
                raise ValueError("NATIVE_EMPTY_OR_OVERSIZE_BODY_HOLD")
            if not isinstance(content_type, str):
                raise ValueError("NATIVE_CONTENT_TYPE_HOLD")
            parts = [part.strip().lower() for part in content_type.split(";")]
            if parts[0] != "text/html":
                raise ValueError("NATIVE_NOT_HTML_HOLD")
            charset = "utf-8"
            for part in parts[1:]:
                if part.startswith("charset="):
                    charset = part.split("=", 1)[1].strip('"')
            if charset not in ("utf-8", "big5", "cp950"):
                raise ValueError("NATIVE_CHARSET_UNSUPPORTED_HOLD")
            try:
                html = raw.decode(charset, errors="strict")
            except UnicodeError as exc:
                raise ValueError("NATIVE_HTML_DECODE_HOLD") from exc
            if not html.strip():
                raise ValueError("NATIVE_EMPTY_DECODED_HTML_HOLD")
            pages.append(html)
            receipts.append({
                "url": url, "http_status": status,
                "content_type": content_type[:100],
                "bytes": len(raw), "body_sha256": hashlib.sha256(raw).hexdigest(),
                "transport": ("BUILTIN_NATIVE_GET" if native
                              else "TEST_INJECTED_NOT_NATIVE"),
                "decision": "HTTP200_BODY_RECEIPT_REVIEW_ONLY",
            })
        observed = (datetime.now(timezone.utc) if native else
                    (now_utc if now_utc is not None
                     else datetime.now(timezone.utc)))
        if not isinstance(observed, datetime) or observed.utcoffset() is None:
            raise ValueError("NATIVE_OBSERVATION_CLOCK_HOLD")
        # Keep native/raw-byte receipts in the sealed isolated REVIEW LKG.
        # The parser's caller-HTML hash alone must never be mislabeled native.
        snapshot = build_source_adapter_review_snapshot(
            list_url, pages[0], detail_url, pages[1], expected_title,
            expected_identity_id, observed.isoformat(), now_utc=observed,
            previous=previous)
        if snapshot["decision"] == "ROLLBACK_TO_ISOLATED_LAST_KNOWN_GOOD":
            result = {"snapshot": snapshot, "persisted": False}
        else:
            snapshot["source_receipts"]["bounded_acquisition"] = {
                "kind": "P30_L7_BOUNDED_SOURCE_RECEIPTS_V1",
                "observed_at_utc": observed.isoformat(),
                "transport": ("BUILTIN_NATIVE_GET" if native
                              else "TEST_INJECTED_NOT_NATIVE"),
                "list_body_sha256": receipts[0]["body_sha256"],
                "detail_body_sha256": receipts[1]["body_sha256"],
                "list_url": list_url, "detail_url": detail_url,
                "decision": "SOURCE_BODY_REVIEW_ONLY_NOT_FORMAL",
            }
            persist_isolated_review_lkg(
                snapshot, destination, repo_root,
                expected_previous_sha256=(
                    previous["last_known_good_sha256"] if previous else None))
            result = {"snapshot": snapshot, "persisted": True}
        return {
            "kind": "P30_L7_BOUNDED_NATIVE_TO_REVIEW_LKG_V1",
            "line": pairs[(list_url, detail_url)][0],
            "source_receipts": receipts,
            "observed_at_utc": observed.isoformat(),
            "native_get_verified": native,
            "source_identity": "SAME_ID_REVIEW_ONLY",
            "snapshot": result["snapshot"],
            "persisted": result["persisted"],
            "formal_accepted_fields": 0, "golden_accepted_events": 0,
            "published_events": 0, "formal_pwa_feed_events": 0,
            "release_state": "HARD_HOLD_NO_PUBLICATION",
        }
    except (ValueError, OSError, TimeoutError) as exc:
        # Acquisition failure does not modify an existing durable LKG.
        # No raw source page is returned, logged, or stored.
        return {
            "kind": "P30_L7_BOUNDED_NATIVE_TO_REVIEW_LKG_V1",
            "decision": "SOURCE_ACQUISITION_HOLD_NO_WRITE",
            "reason": type(exc).__name__ + ":" + str(exc)[:100],
            "persisted": False,
            "prior_lkg_sha256": (previous["last_known_good_sha256"]
                                 if previous is not None else None),
            "source_receipts": receipts,
            "native_get_verified": False,
            "formal_accepted_fields": 0, "golden_accepted_events": 0,
            "published_events": 0, "formal_pwa_feed_events": 0,
            "release_state": "HARD_HOLD_NO_PUBLICATION",
        }


# B rotation: reuse canonical CKSMH #17 and the existing REVIEW/LKG core.
# Strict actId ownership; no Session/price/venue inference or publication.
CKSMH_PUBLIC_LIST = "https://event.culture.tw/CKSMH"
CKSMH_PUBLIC_DETAIL = "https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId=61023"
CKSMH_ROTATION_TITLE = "「民主女路」走讀活動"


def run_cksmh_actid_review_lkg(destination, repo_root, *, fetcher=None,
                               network_authorized=False, source_hypothesis="",
                               now_utc=None):
    """One-shot public LIST/actId DETAIL -> isolated REVIEW LKG or no-write HOLD."""
    import hashlib
    import re
    import urllib.request
    from datetime import timezone, timedelta
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlsplit, parse_qs
    from scripts.p30_candidate_review_pipeline import build_candidate_dataset

    _isolated_lkg_path(destination, repo_root)
    previous = load_isolated_review_lkg(destination, repo_root)
    if fetcher is None and (network_authorized is not True or
                           not isinstance(source_hypothesis, str) or
                           not 8 <= len(source_hypothesis.strip()) <= 200):
        raise ValueError("CKSMH_NATIVE_REQUIRES_NEW_HYPOTHESIS")
    if fetcher is not None and not callable(fetcher):
        raise ValueError("CKSMH_FETCHER_NOT_CALLABLE")
    native = fetcher is None
    receipts = []

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    def public_get(url):
        req = urllib.request.Request(url, method="GET", headers={
            "User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
            "Accept": "text/html", "Accept-Encoding": "identity"})
        with urllib.request.build_opener(NoRedirect).open(req, timeout=8) as res:
            return (res.status, res.headers.get("Content-Type", ""),
                    res.read(524289), res.geturl())

    class LocalHTML(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.anchors = []
            self.headings = []
            self.anchor = None
            self.heading = None
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "a":
                self.anchor = [attrs.get("href", ""), []]
            if tag in ("h1", "h2"):
                self.heading = [tag, []]
        def handle_data(self, value):
            if self.anchor is not None:
                self.anchor[1].append(value)
            if self.heading is not None:
                self.heading[1].append(value)
        def handle_endtag(self, tag):
            if tag == "a" and self.anchor is not None:
                self.anchors.append((self.anchor[0], "".join(self.anchor[1])))
                self.anchor = None
            if tag in ("h1", "h2") and self.heading is not None:
                self.headings.append("".join(self.heading[1]))
                self.heading = None

    def norm(value):
        return re.sub(r"\s+", " ", value).strip()

    def identity(href):
        try:
            url = urlsplit(urljoin(CKSMH_PUBLIC_LIST, href))
            if (url.scheme != "https" or url.netloc != "event.culture.tw" or
                url.path not in ("/mocweb/reg/CKSMH/Detail.init.ctr",
                                 "/CKSMH/portal/Registration/C0103MAction") or
                url.fragment or url.username or url.password):
                return None
            ids = parse_qs(url.query, keep_blank_values=True).get("actId", [])
            return ids[0] if len(ids) == 1 and re.fullmatch(r"[0-9]{1,8}", ids[0]) else None
        except ValueError:
            return None

    def hold(reason):
        return {"kind": "P30_L7_CKSMH_ROTATION_REVIEW_V1",
                "decision": "SOURCE_OR_IDENTITY_HOLD_NO_WRITE",
                "reason": str(reason)[:140], "line": "B", "platform_id": "17",
                "source_event_id": "61023", "source_receipts": receipts,
                "native_get_200_count": (sum(x["http_status"] == 200 for x in receipts)
                                         if native else 0),
                "same_id_review_lkg": 0, "persisted": False,
                "prior_lkg_sha256": (previous["last_known_good_sha256"] if previous else None),
                "formal_accepted_fields": 0, "golden_accepted_events": 0,
                "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION"}

    try:
        pages = []
        for url in (CKSMH_PUBLIC_LIST, CKSMH_PUBLIC_DETAIL):
            status, content_type, raw, final_url = (public_get if native else fetcher)(url)
            if type(status) is not int or status != 200 or final_url != url:
                raise ValueError("CKSMH_HTTP_STATUS_OR_REDIRECT_HOLD")
            if not isinstance(raw, bytes) or not 0 < len(raw) <= 524288:
                raise ValueError("CKSMH_EMPTY_OR_OVERSIZE_HOLD")
            parts = [v.strip().lower() for v in content_type.split(";")]
            if parts[0] != "text/html":
                raise ValueError("CKSMH_NOT_HTML_HOLD")
            charset = next((v.split("=", 1)[1].strip('"') for v in parts[1:]
                            if v.startswith("charset=")), "utf-8")
            if charset not in ("utf-8", "big5", "cp950"):
                raise ValueError("CKSMH_CHARSET_HOLD")
            decoded = raw.decode(charset, errors="strict")
            if not decoded.strip():
                raise ValueError("CKSMH_EMPTY_HTML_HOLD")
            receipts.append({"url": url, "http_status": 200,
                             "body_sha256": hashlib.sha256(raw).hexdigest(),
                             "bytes": len(raw),
                             "transport": ("BUILTIN_NATIVE_GET" if native else
                                           "TEST_INJECTED_NOT_NATIVE")})
            pages.append(decoded)
        index, detail = LocalHTML(), LocalHTML()
        index.feed(pages[0]); detail.feed(pages[1])
        edges = [identity(href) for href, title in index.anchors
                 if norm(title) == CKSMH_ROTATION_TITLE]
        if not edges or set(edges) != {"61023"}:
            raise ValueError("CKSMH_LIST_EXACT_ACTID_EDGE_HOLD")
        headings = [norm(x) for x in detail.headings if norm(x)]
        if CKSMH_ROTATION_TITLE not in headings:
            raise ValueError("CKSMH_DETAIL_TITLE_HEADING_HOLD")
        observed = datetime.now(timezone.utc) if native else (now_utc or datetime.now(timezone.utc))
        if (not isinstance(observed, datetime) or observed.utcoffset() is None or
            abs(datetime.now(timezone.utc) - observed.astimezone(timezone.utc)) > timedelta(days=2)):
            raise ValueError("CKSMH_OBSERVATION_CLOCK_HOLD")
        if previous is not None:
            old = previous["rows"][0]["_candidate"]
            if old.get("platform_id") != "17" or old.get("source_event_id") != "61023":
                raise ValueError("CKSMH_PREVIOUS_LKG_OTHER_SOURCE_HOLD")
        stamp = observed.isoformat()
        candidate = {"title": CKSMH_ROTATION_TITLE, "url": CKSMH_PUBLIC_DETAIL,
                     "platform": "中正紀念堂", "type": "活動", "scraped_at": stamp,
                     "_candidate": {
                         "scope": "CANDIDATE_PREVIEW_ONLY", "decision": "REVIEW_WITH_HOLD",
                         "published": False, "golden_accepted": False,
                         "formal_field_pass": False, "record_id": "17:61023",
                         "platform_id": "17", "source_event_id": "61023",
                         "source_class": "OFFICIAL_VENUE_NON_SESSION",
                         "sources": [CKSMH_PUBLIC_LIST, CKSMH_PUBLIC_DETAIL],
                         "hold_reasons": ["CKSMH_MULTI_SESSION_DATE_VENUE_HOLD",
                                          "INDEPENDENT_FIELD_AUTHORITY_PENDING",
                                          "REVIEW_ONLY_NOT_FORMAL"]}}
        rows, quality = build_candidate_dataset([candidate])
        if len(rows) != 1 or quality["rejectedRows"]:
            raise ValueError("CKSMH_REVIEW_PIPELINE_REJECT_HOLD")
        digest = _isolated_lkg_digest(rows)
        snapshot = {
            "kind": "P30_L7_ISOLATED_SOURCE_ADAPTER_SNAPSHOT_V1",
            "decision": "REVIEW_ONLY_NEW_OR_UPDATED", "rows": rows,
            "quality": quality,
            "field_receipts": [{"field": "title", "value": CKSMH_ROTATION_TITLE,
                                "role": "EVENT_TITLE", "source": CKSMH_PUBLIC_DETAIL,
                                "observed_at": stamp, "decision": "REVIEW"}],
            "source_receipts": {"list_url": CKSMH_PUBLIC_LIST,
                                "detail_url": CKSMH_PUBLIC_DETAIL,
                                "bounded_acquisition": {
                                    "kind": "P30_L7_BOUNDED_SOURCE_RECEIPTS_V1",
                                    "observed_at_utc": stamp,
                                    "transport": ("BUILTIN_NATIVE_GET" if native else
                                                  "TEST_INJECTED_NOT_NATIVE"),
                                    "list_body_sha256": receipts[0]["body_sha256"],
                                    "detail_body_sha256": receipts[1]["body_sha256"],
                                    "list_url": CKSMH_PUBLIC_LIST,
                                    "detail_url": CKSMH_PUBLIC_DETAIL,
                                    "decision": "SOURCE_BODY_REVIEW_ONLY_NOT_FORMAL"}},
            "incremental_diff": {"added_ids": (["17:61023"] if previous is None else []),
                                 "removed_ids": [],
                                 "changed": previous is None or digest != previous["last_known_good_sha256"]},
            "last_known_good_sha256": digest, "native_get_verified": False,
            "formal_accepted_fields": 0, "golden_accepted_events": 0,
            "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION"}
        persist_isolated_review_lkg(snapshot, destination, repo_root,
                                    expected_previous_sha256=(
                                        previous["last_known_good_sha256"] if previous else None))
        return {"kind": "P30_L7_CKSMH_ROTATION_REVIEW_V1", "decision": "REVIEW_ONLY",
                "line": "B", "platform_id": "17", "source_event_id": "61023",
                "source_receipts": receipts, "native_get_200_count": 2 if native else 0,
                "same_id_review_lkg": 1, "persisted": True,
                "lkg_sha256": digest, "native_transport": native,
                "formal_accepted_fields": 0, "golden_accepted_events": 0,
                "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION"}
    except (ValueError, OSError, TimeoutError, UnicodeError, TypeError) as exc:
        return hold(type(exc).__name__ + ":" + str(exc))



# A: fixed automated authority/freshness adjudication; never caller-granted FIELD.
def assess_tmc_non_session_field_authority(snapshot, now_utc=None):
    from datetime import timezone
    from urllib.parse import urlsplit
    report = {"kind": "P30_L7_TMC_FIELD_AUTHORITY_CONTRACT_V1",
              "decision": "HOLD_NO_SEALED_NATIVE_AUTHORITY", "field_matrix": [],
              "first_failure": "TMC_NO_SNAPSHOT", "source_age_seconds": None,
              "requirements": ["EXACT_SOURCE_EVENT_PATH", "NATIVE_SHA256_FRESH_UTC",
                               "SHOW_NOT_SALE_OR_SESSION", "HALL_NOT_TICKET_ID",
                               "INDEPENDENT_FIELD_CONFLICT_ADJUDICATION"],
              "formal_accepted_fields": 0, "golden_accepted_events": 0,
              "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION"}
    if snapshot is None:
        return report
    _validate_isolated_lkg_snapshot(snapshot)
    row = snapshot["rows"][0]
    meta = row["_candidate"]
    src = snapshot["source_receipts"]
    fields = snapshot["field_receipts"]
    if (meta.get("platform_id") != "TMC_OFFICIAL" or
        meta.get("source_event_id") != urlsplit(PUBLIC_TMC_DETAIL).path.rsplit("/", 1)[-1] or
        meta.get("sources") != [PUBLIC_TMC_LIST, PUBLIC_TMC_DETAIL] or
        src.get("list_url") != PUBLIC_TMC_LIST or
        src.get("detail_url") != PUBLIC_TMC_DETAIL):
        raise ValueError("TMC_CONTRACT_EXACT_SOURCE_ID_HOLD")
    expected = {"venue_showtime": "VENUE_SHOW_NOT_SALE", "venue_hall": "VENUE_HALL"}
    if (len(fields) != 2 or
        {f.get("field"): f.get("role") for f in fields} != expected or
        any(f.get("source_url") != PUBLIC_TMC_DETAIL or
            f.get("observed_at_utc") != row["scraped_at"] or
            f.get("formal_accepted") is not False for f in fields)):
        raise ValueError("TMC_CONTRACT_ROLE_PROVENANCE_HOLD")
    # Fail closed on unbound acquisition clock, URL or raw-byte SHA receipts.
    _validate_nonpublishing_source_receipt(
        src.get("bounded_acquisition"), PUBLIC_TMC_LIST, PUBLIC_TMC_DETAIL,
        row["scraped_at"])
    now = now_utc or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("TMC_CONTRACT_CLOCK_HOLD")
    observed = datetime.fromisoformat(row["scraped_at"].replace("Z", "+00:00"))
    age_seconds = (now - observed).total_seconds()
    fresh = 0 <= age_seconds <= 86400
    native = src.get("bounded_acquisition", {}).get("transport") == "BUILTIN_NATIVE_GET"
    # A: deterministic first missing authority; never promotes a REVIEW field.
    report["source_age_seconds"] = int(age_seconds)
    report["first_failure"] = (
        "TMC_TEST_INJECTED_NOT_NATIVE" if not native else
        "TMC_SOURCE_RECEIPT_STALE_OR_FUTURE_24H" if not fresh else
        "TMC_INDEPENDENT_SHOW_HALL_AUTHORITY_MISSING")
    report["next_required_evidence"] = (
        "Independent same-event official SHOW/HALL observation, conflict decision, "
        "fresh UTC source-body receipt; never KHAM checkout or ticket Session")
    report["field_matrix"] = [
        {"field": f["field"], "role": f["role"], "value": f["value"],
         "source_url": PUBLIC_TMC_DETAIL, "observed_at_utc": row["scraped_at"],
         "native_body_receipt": native, "fresh_within_24h": fresh,
         "independent_authority": False,
         "decision": ("SOURCE_AUTHORITY_REVIEW_ONLY" if native and fresh
                      else "HOLD_NATIVE_FRESHNESS_OR_AUTHORITY")}
        for f in fields]
    report["decision"] = ("REVIEW_INDEPENDENT_AUTHORITY_PENDING" if native and fresh
                          else "HOLD_NATIVE_FRESHNESS_OR_AUTHORITY")
    return report


# B: canonical #13 Huashan, not a new platform. Same official detail PATH
# is independently checkable; local path hash is NOT an official numeric ID.
from urllib.parse import quote as _huashan_quote
HUASHAN_ROTATION_TITLE = "2026小黃帽交通安全童樂會《成為全家的安全小英雄》"
HUASHAN_PUBLIC_LIST = "https://www.huashan1914.com/exhibition"
HUASHAN_PUBLIC_DETAIL = HUASHAN_PUBLIC_LIST + "/" + _huashan_quote(HUASHAN_ROTATION_TITLE, safe="")


def run_huashan_exact_path_review_lkg(destination, repo_root, *, fetcher=None,
                                      network_authorized=False, source_hypothesis="",
                                      now_utc=None):
    """One-shot public LIST->same detail path->sealed REVIEW LKG; no publication."""
    import hashlib, re, urllib.request
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlsplit, unquote
    from datetime import timezone
    from scripts.p30_candidate_review_pipeline import build_candidate_dataset
    _isolated_lkg_path(destination, repo_root)
    previous = load_isolated_review_lkg(destination, repo_root)
    if fetcher is None and (network_authorized is not True or
                           not isinstance(source_hypothesis, str) or
                           not 8 <= len(source_hypothesis.strip()) <= 200):
        raise ValueError("HUASHAN_NATIVE_REQUIRES_NEW_HYPOTHESIS")
    if fetcher is not None and not callable(fetcher):
        raise ValueError("HUASHAN_FETCHER_NOT_CALLABLE")
    native, receipts = fetcher is None, []
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    def public_get(url):
        req = urllib.request.Request(url, method="GET", headers={
            "User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
            "Accept": "text/html", "Accept-Encoding": "identity"})
        with urllib.request.build_opener(NoRedirect).open(req, timeout=8) as res:
            return res.status, res.headers.get("Content-Type", ""), res.read(524289), res.geturl()
    class Page(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.anchors, self.headings, self.a, self.h, self.skip = [], [], None, None, 0
        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "noscript"): self.skip += 1
            if self.skip: return
            if tag == "a": self.a = [dict(attrs).get("href", ""), []]
            if tag == "h1": self.h = []
        def handle_data(self, s):
            if self.skip: return
            if self.a is not None: self.a[1].append(s)
            if self.h is not None: self.h.append(s)
        def handle_endtag(self, tag):
            if tag in ("script", "style", "noscript"):
                self.skip = max(0, self.skip - 1)
                return
            if tag == "a" and self.a is not None:
                self.anchors.append((self.a[0], "".join(self.a[1]))); self.a = None
            if tag == "h1" and self.h is not None:
                self.headings.append("".join(self.h)); self.h = None
    def norm(s): return re.sub(r"\s+", " ", s).strip()
    def path(href):
        try:
            u = urlsplit(urljoin(HUASHAN_PUBLIC_LIST, href))
            if (u.scheme != "https" or u.netloc != "www.huashan1914.com"
                    or u.username or u.password or u.query or u.fragment):
                return None
            return unquote(u.path)
        except ValueError:
            return None
    def hold(reason):
        return {"kind": "P30_L7_HUASHAN_ROTATION_REVIEW_V1",
                "decision": "SOURCE_OR_IDENTITY_HOLD_NO_WRITE",
                "reason": str(reason)[:140], "platform_id": "13",
                "source_receipts": receipts,
                "native_get_200_count": sum(x["http_status"] == 200 for x in receipts) if native else 0,
                "same_path_review_lkg": 0, "native_same_numeric_id": 0,
                "persisted": False, "formal_accepted_fields": 0,
                "golden_accepted_events": 0, "published_events": 0,
                "release_state": "HARD_HOLD_NO_PUBLICATION"}
    try:
        pages = []
        for url in (HUASHAN_PUBLIC_LIST, HUASHAN_PUBLIC_DETAIL):
            status, content_type, raw, final_url = (public_get if native else fetcher)(url)
            if type(status) is not int or status != 200 or final_url != url:
                raise ValueError("HUASHAN_HTTP_STATUS_OR_REDIRECT_HOLD")
            if not isinstance(raw, bytes) or not 0 < len(raw) <= 524288:
                raise ValueError("HUASHAN_EMPTY_OR_OVERSIZE_HOLD")
            if not isinstance(content_type, str):
                raise ValueError("HUASHAN_CONTENT_TYPE_HOLD")
            parts = [x.strip().lower() for x in content_type.split(";")]
            if parts[0] != "text/html": raise ValueError("HUASHAN_NOT_HTML_HOLD")
            charset = next((x.split("=", 1)[1].strip('"') for x in parts[1:]
                            if x.startswith("charset=")), "utf-8")
            if charset not in ("utf-8", "big5", "cp950"):
                raise ValueError("HUASHAN_CHARSET_HOLD")
            decoded = raw.decode(charset, errors="strict")
            if not decoded.strip(): raise ValueError("HUASHAN_EMPTY_HTML_HOLD")
            pages.append(decoded)
            receipts.append({"url": url, "http_status": 200, "bytes": len(raw),
                             "body_sha256": hashlib.sha256(raw).hexdigest(),
                             "transport": "BUILTIN_NATIVE_GET" if native else "TEST_INJECTED_NOT_NATIVE"})
        listing, detail = Page(), Page()
        listing.feed(pages[0]); detail.feed(pages[1])
        title = norm(HUASHAN_ROTATION_TITLE)
        expected_path = path(HUASHAN_PUBLIC_DETAIL)
        matches = [path(href) for href, label in listing.anchors if title in norm(label)]
        if not matches or set(matches) != {expected_path}:
            raise ValueError("HUASHAN_LIST_EXACT_TITLE_PATH_EDGE_HOLD")
        if [norm(x) for x in detail.headings].count(title) != 1:
            raise ValueError("HUASHAN_DETAIL_EXACT_H1_HOLD")
        observed = datetime.now(timezone.utc) if native else (now_utc or datetime.now(timezone.utc))
        if not isinstance(observed, datetime) or observed.utcoffset() is None:
            raise ValueError("HUASHAN_OBSERVATION_CLOCK_HOLD")
        identity = "path-sha256-" + hashlib.sha256(expected_path.encode()).hexdigest()[:24]
        if previous and (previous["rows"][0]["_candidate"].get("platform_id") != "13" or
                         previous["rows"][0]["_candidate"].get("source_event_id") != identity):
            raise ValueError("HUASHAN_PREVIOUS_LKG_OTHER_SOURCE_HOLD")
        stamp = observed.isoformat()
        candidate = {"title": HUASHAN_ROTATION_TITLE, "url": HUASHAN_PUBLIC_DETAIL,
                     "platform": "華山1914", "type": "活動", "scraped_at": stamp,
                     "_candidate": {"scope": "CANDIDATE_PREVIEW_ONLY",
                                    "decision": "REVIEW_WITH_HOLD",
                                    "published": False, "golden_accepted": False,
                                    "formal_field_pass": False,
                                    "record_id": "13:" + identity,
                                    "platform_id": "13", "source_event_id": identity,
                                    "source_identity_kind": "OFFICIAL_PATH_HASH_NOT_NUMERIC_ID",
                                    "source_class": "OFFICIAL_VENUE_NON_SESSION",
                                    "sources": [HUASHAN_PUBLIC_LIST, HUASHAN_PUBLIC_DETAIL],
                                    "hold_reasons": ["NO_INDEPENDENT_NUMERIC_EVENT_ID",
                                                     "DATE_TIME_HALL_AUTHORITY_PENDING",
                                                     "REVIEW_ONLY_NOT_FORMAL"]}}
        rows, quality = build_candidate_dataset([candidate])
        if len(rows) != 1 or quality["rejectedRows"]:
            raise ValueError("HUASHAN_REVIEW_PIPELINE_REJECT_HOLD")
        digest = _isolated_lkg_digest(rows)
        snapshot = {"kind": "P30_L7_ISOLATED_SOURCE_ADAPTER_SNAPSHOT_V1",
                    "decision": "REVIEW_ONLY_NEW_OR_UPDATED", "rows": rows,
                    "quality": quality,
                    "field_receipts": [{"field": "title", "value": HUASHAN_ROTATION_TITLE,
                                        "role": "EVENT_TITLE", "source": HUASHAN_PUBLIC_DETAIL,
                                        "observed_at": stamp, "decision": "REVIEW"}],
                    "source_receipts": {"list_url": HUASHAN_PUBLIC_LIST,
                                        "detail_url": HUASHAN_PUBLIC_DETAIL,
                                        "bounded_acquisition": {
                                            "kind": "P30_L7_BOUNDED_SOURCE_RECEIPTS_V1",
                                            "observed_at_utc": stamp,
                                            "transport": "BUILTIN_NATIVE_GET" if native else "TEST_INJECTED_NOT_NATIVE",
                                            "list_body_sha256": receipts[0]["body_sha256"],
                                            "detail_body_sha256": receipts[1]["body_sha256"],
                                            "list_url": HUASHAN_PUBLIC_LIST,
                                            "detail_url": HUASHAN_PUBLIC_DETAIL,
                                            "decision": "SOURCE_BODY_REVIEW_ONLY_NOT_FORMAL"}},
                    "incremental_diff": {"added_ids": ["13:" + identity] if not previous else [],
                                         "removed_ids": [], "changed": not previous or digest != previous["last_known_good_sha256"]},
                    "last_known_good_sha256": digest, "native_get_verified": False,
                    "formal_accepted_fields": 0, "golden_accepted_events": 0,
                    "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION"}
        persist_isolated_review_lkg(snapshot, destination, repo_root,
                                    expected_previous_sha256=previous["last_known_good_sha256"] if previous else None)
        return {"kind": "P30_L7_HUASHAN_ROTATION_REVIEW_V1", "decision": "REVIEW_ONLY",
                "platform_id": "13", "source_receipts": receipts,
                "native_get_200_count": 2 if native else 0, "same_path_review_lkg": 1,
                "native_same_numeric_id": 0, "persisted": True,
                "lkg_sha256": digest, "formal_accepted_fields": 0,
                "golden_accepted_events": 0, "published_events": 0,
                "release_state": "HARD_HOLD_NO_PUBLICATION"}
    except (ValueError, OSError, TimeoutError, UnicodeError, TypeError) as exc:
        return hold(type(exc).__name__ + ":" + str(exc))


# B #13 source-local field semantics: pure, fail-closed and non-publishing.
# Never treat multiple halls or their opening times as a ticket session.
def adjudicate_huashan_detail_field_roles(html, source_url, observed_at_utc,
                                         body_sha256, *, now_utc=None):
    import hashlib, re
    from html.parser import HTMLParser
    from datetime import timezone
    report = {"kind":"P30_L7_HUASHAN_DETAIL_FIELD_ROLE_CONTRACT_V1",
              "platform_id":"13", "source_url":source_url,
              "decision":"SOURCE_FIELD_SEMANTICS_HOLD", "first_failure":None,
              "field_matrix":[], "native_get_count":0, "same_numeric_event_id":0,
              "formal_accepted_fields":0, "golden_accepted_events":0,
              "published_events":0, "release_state":"HARD_HOLD_NO_PUBLICATION"}
    def hold(reason):
        report["first_failure"]=reason
        return report
    if source_url != HUASHAN_PUBLIC_DETAIL:
        return hold("HUASHAN_FIELD_EXACT_SOURCE_URL_HOLD")
    if not isinstance(html,str) or not html or len(html.encode("utf-8"))>524288:
        return hold("HUASHAN_FIELD_EMPTY_OR_OVERSIZE_HOLD")
    digest=hashlib.sha256(html.encode("utf-8")).hexdigest()
    if not isinstance(body_sha256,str) or body_sha256 != digest:
        return hold("HUASHAN_FIELD_RAW_BODY_SHA256_HOLD")
    try:
        observed=datetime.fromisoformat(observed_at_utc.replace("Z","+00:00"))
        now=now_utc or datetime.now(timezone.utc)
        if observed.utcoffset() is None or now.utcoffset() is None: raise ValueError()
        if not 0 <= (now-observed).total_seconds() <= 86400:
            return hold("HUASHAN_FIELD_SOURCE_FRESHNESS_HOLD")
    except (ValueError,AttributeError,TypeError):
        return hold("HUASHAN_FIELD_OBSERVATION_CLOCK_HOLD")
    class Visible(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.skip=0; self.h1=None; self.titles=[]; self.parts=[]
        def handle_starttag(self,tag,attrs):
            if tag in ("script","style","noscript"): self.skip+=1
            if not self.skip and tag=="h1": self.h1=[]
        def handle_data(self,value):
            if not self.skip:
                if value.strip(): self.parts.append(value.strip())
                if self.h1 is not None: self.h1.append(value)
        def handle_endtag(self,tag):
            if tag in ("script","style","noscript"): self.skip=max(0,self.skip-1)
            if tag=="h1" and self.h1 is not None:
                self.titles.append("".join(self.h1)); self.h1=None
    p=Visible()
    try: p.feed(html)
    except (ValueError,TypeError): return hold("HUASHAN_FIELD_HTML_PARSER_HOLD")
    norm=lambda x: re.sub(r"\s+"," ",x).strip()
    if [norm(x) for x in p.titles].count(norm(HUASHAN_ROTATION_TITLE))!=1:
        return hold("HUASHAN_FIELD_EXACT_H1_IDENTITY_HOLD")
    text=norm(" ".join(p.parts))
    # Actual first native failure: responsive HTML can split 11.07 and (六)
    # into separate text nodes. Parse within heading-bounded scopes instead
    # of requiring one contiguous date/time regex; never use footer hours.
    time_marks=list(re.finditer(r"活動時間\s*[:：]",text))
    venue_marks=list(re.finditer(r"地點\s*[:：]",text))
    organizer_marks=list(re.finditer(r"主辦單位\s*[:：]",text))
    report["structural_diagnostic"]={
        "event_time_label_count":len(time_marks),
        "venue_label_count":len(venue_marks),
        "organizer_label_count":len(organizer_marks)}
    if (len(time_marks)!=1 or len(venue_marks)!=1 or len(organizer_marks)!=1
        or not time_marks[0].end()<venue_marks[0].start()<organizer_marks[0].start()):
        return hold("HUASHAN_FIELD_EVENT_LABEL_OWNERSHIP_HOLD")
    time_scope=re.sub(r"\s+","",text[time_marks[0].end():venue_marks[0].start()])
    venue_scope=norm(text[venue_marks[0].end():organizer_marks[0].start()])
    dates=re.findall(r"\d{1,2}[./]\d{1,2}\([^)]+\)",time_scope)
    hours=re.findall(r"\d{1,2}:\d{2}",time_scope)
    report["structural_diagnostic"].update({
        "year_token_count":len(re.findall(r"20\d{2}",time_scope)),
        "date_token_count":len(dates),"clock_token_count":len(hours)})
    if (re.findall(r"20\d{2}",time_scope)!=["2026"]
        or dates!=["11.07(六)","11.07(六)"]
        or hours!=["11:00","16:30","11:30","11:00"]):
        return hold("HUASHAN_FIELD_EVENT_DATE_OR_HOURS_CONFLICT_HOLD")
    exception="西1館11:30開放/西2館、西5-1館11:00開放"
    if time_scope.count(exception)!=1:
        return hold("HUASHAN_FIELD_HALL_OPENING_EXCEPTION_HOLD")
    expected_halls=["西5-1館 壓縮兼包裝工場","西2館 第三乾餾場","西1館 第二乾餾場"]
    halls=[norm(x) for x in re.findall(
        r"西(?:5-1|2|1)館\s*(?:壓縮兼包裝工場|第三乾餾場|第二乾餾場)",
        venue_scope)]
    if halls!=expected_halls or len(re.findall(r"西(?:5-1|2|1)館",venue_scope))!=3:
        return hold("HUASHAN_FIELD_MULTI_HALL_EXACT_PARITY_HOLD")
    roles=[("event_date","VENUE_EVENT_DATE_NOT_TICKET_SESSION","2026-11-07"),
           ("event_public_hours","EVENT_OPEN_HOURS_NOT_SITE_BUSINESS_HOURS","11:00~16:30"),
           ("event_halls","MULTI_HALL_NO_SINGLE_VENUE_INFERENCE",halls),
           ("hall_opening_exceptions","PER_HALL_OPENING_NOT_SESSION",exception)]
    report["field_matrix"]=[{"field":name,"role":role,"value":value,
        "source_url":source_url,"body_sha256":digest,
        "observed_at_utc":observed_at_utc,"decision":"REVIEW_SOURCE_ROLE_ONLY",
        "formal_accepted":False,"independent_counter_source_verified":False}
        for name,role,value in roles]
    report["decision"]="REVIEW_FOUR_SOURCE_ROLES_INDEPENDENT_ACCEPTANCE_HOLD"
    return report


# B #13: a NEW, independently testable DOM hypothesis. Some official event
# pages may embed schema.org Event.identifier. It is never inferred from the
# slug, local path hash, analytics IDs, tickets or unrelated JSON-LD entities.
# Even an embedded numeric ID is REVIEW until an exact LIST->DETAIL ID edge
# and an independent authority/conflict check have both been established.
def inspect_huashan_embedded_event_identity(html, source_url):
    """Inspect bounded official JSON-LD without network, persistence or release."""
    import re
    from html.parser import HTMLParser

    report = {
        "kind": "P30_L7_HUASHAN_EMBEDDED_EVENT_IDENTITY_V1",
        "source_url": source_url,
        "decision": "HOLD_NO_OFFICIAL_EMBEDDED_NUMERIC_EVENT_ID",
        "first_failure": None,
        "embedded_numeric_id_review": None,
        "same_numeric_event_id": 0,
        "formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }

    def hold(reason):
        report["first_failure"] = reason
        return report

    if source_url != HUASHAN_PUBLIC_DETAIL:
        return hold("HUASHAN_EMBEDDED_EXACT_DETAIL_URL_HOLD")
    if not isinstance(html, str) or not 0 < len(html.encode("utf-8")) <= 524288:
        return hold("HUASHAN_EMBEDDED_EMPTY_OR_OVERSIZE_HOLD")

    class Scripts(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.current = None
            self.documents = []

        def handle_starttag(self, tag, attrs):
            if tag == "script":
                attributes = dict(attrs)
                media_type = attributes.get("type", "").split(";", 1)[0].strip().lower()
                self.current = [] if media_type == "application/ld+json" else None

        def handle_data(self, data):
            if self.current is not None:
                self.current.append(data)

        def handle_endtag(self, tag):
            if tag == "script" and self.current is not None:
                self.documents.append("".join(self.current))
                self.current = None

    parser = Scripts()
    try:
        parser.feed(html)
    except (ValueError, TypeError) as exc:
        return hold("HUASHAN_EMBEDDED_HTML_PARSER_HOLD:" + type(exc).__name__)
    if not parser.documents or len(parser.documents) > 16:
        return hold("HUASHAN_EMBEDDED_JSONLD_ABSENT_OR_EXCESS_HOLD")

    numeric_ids = []
    event_nodes = 0

    def walk(value, depth=0):
        nonlocal event_nodes
        if depth > 8:
            raise ValueError("HUASHAN_EMBEDDED_JSONLD_DEPTH_HOLD")
        if isinstance(value, list):
            if len(value) > 40:
                raise ValueError("HUASHAN_EMBEDDED_JSONLD_LIST_BOUND_HOLD")
            for child in value:
                walk(child, depth + 1)
        elif isinstance(value, dict):
            if len(value) > 80:
                raise ValueError("HUASHAN_EMBEDDED_JSONLD_OBJECT_BOUND_HOLD")
            types = value.get("@type")
            is_event = types == "Event" or (
                isinstance(types, list) and "Event" in types)
            if is_event:
                event_nodes += 1
                if event_nodes > 16:
                    raise ValueError("HUASHAN_EMBEDDED_TOO_MANY_EVENTS_HOLD")
                # The node must explicitly own THIS official detail URL.
                # A generic site-wide Event node is not an identity authority.
                if value.get("url") == HUASHAN_PUBLIC_DETAIL:
                    identifier = value.get("identifier")
                    if (type(identifier) in (str, int)
                            and re.fullmatch(r"[0-9]{1,16}", str(identifier))):
                        numeric_ids.append(str(identifier))
            for key in ("@graph", "itemListElement"):
                if key in value:
                    walk(value[key], depth + 1)

    try:
        for document in parser.documents:
            if len(document.encode("utf-8")) > 131072:
                raise ValueError("HUASHAN_EMBEDDED_JSONLD_SIZE_HOLD")
            walk(json.loads(document))
    except (ValueError, TypeError, RecursionError) as exc:
        return hold("HUASHAN_EMBEDDED_JSONLD_INVALID_OR_AMBIGUOUS_HOLD:"
                    + str(exc)[:90])

    report["event_nodes_seen"] = event_nodes
    report["matching_numeric_id_count"] = len(numeric_ids)
    if len(numeric_ids) != 1:
        return hold("HUASHAN_EMBEDDED_NUMERIC_ID_MISSING_OR_CONFLICT_HOLD")
    report["embedded_numeric_id_review"] = numeric_ids[0]
    report["decision"] = "REVIEW_EMBEDDED_ID_NOT_LIST_BOUND"
    return report


# B P0 canonical #14 Songshan: strict official UUID LIST -> DETAIL identity.
# Reuse the existing candidate quality gate and atomic/CAS sealed LKG, never
# create a second platform, infer ticket Session, or write production data.
SONGSHAN_PUBLIC_LIST = "https://www.songshanculturalpark.org/exhibition"
SONGSHAN_EVENT_UUID = "d44f6cfd-c232-41db-9124-adcc49302f2a"
SONGSHAN_PUBLIC_DETAIL = SONGSHAN_PUBLIC_LIST + "/activity/" + SONGSHAN_EVENT_UUID
SONGSHAN_EVENT_TITLE = "2026 紙上躍躍然．典美插畫大賞"


def run_songshan_uuid_review_lkg(destination, repo_root, *, fetcher=None,
                                network_authorized=False, source_hypothesis="",
                                now_utc=None):
    """Bounded official two-GET UUID edge -> existing isolated REVIEW LKG."""
    import hashlib, re, urllib.request
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlsplit
    from datetime import timezone
    from scripts.p30_candidate_review_pipeline import build_candidate_dataset

    _isolated_lkg_path(destination, repo_root)
    previous = load_isolated_review_lkg(destination, repo_root)
    if fetcher is None and (network_authorized is not True or
                            not isinstance(source_hypothesis, str) or
                            not 8 <= len(source_hypothesis.strip()) <= 200):
        raise ValueError("SONGSHAN_NATIVE_REQUIRES_NEW_HYPOTHESIS")
    if fetcher is not None and not callable(fetcher):
        raise ValueError("SONGSHAN_FETCHER_NOT_CALLABLE")
    native, receipts = fetcher is None, []

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    def public_get(url):
        request = urllib.request.Request(url, method="GET", headers={
            "User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
            "Accept": "text/html", "Accept-Encoding": "identity"})
        with urllib.request.build_opener(NoRedirect).open(request, timeout=8) as res:
            return (res.status, res.headers.get("Content-Type", ""),
                    res.read(524289), res.geturl())

    def activity_uuid(href):
        try:
            resolved = urlsplit(urljoin(SONGSHAN_PUBLIC_LIST, href))
            if (resolved.scheme != "https" or
                    resolved.netloc != "www.songshanculturalpark.org" or
                    resolved.username or resolved.password or
                    resolved.query or resolved.fragment):
                return None
            match = re.fullmatch(
                r"/exhibition/activity/([0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})",
                resolved.path)
            return match.group(1) if match else None
        except (TypeError, ValueError):
            return None

    class BoundedDOM(HTMLParser):
        """Find an event-owned title/UUID in one bounded DOM subtree."""
        VOID = frozenset(("area", "base", "br", "col", "embed", "hr",
                          "img", "input", "link", "meta", "param",
                          "source", "track", "wbr"))
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.nodes = [{"tag": "root", "parent": None, "text": "",
                           "uuid": None}]
            self.stack = [0]
            self.anchors = []
            self.headings = []
        def handle_starttag(self, tag, attrs):
            if len(self.nodes) >= 16000 or len(self.stack) > 80:
                raise ValueError("SONGSHAN_DOM_BOUNDS_HOLD")
            attributes = dict(attrs)
            idx = len(self.nodes)
            uid = activity_uuid(attributes.get("href", "")) if tag == "a" else None
            self.nodes.append({"tag": tag, "parent": self.stack[-1],
                               "text": "", "uuid": uid})
            if uid:
                self.anchors.append((idx, uid))
            if tag in ("h1", "h2", "h3"):
                self.headings.append(idx)
            if tag not in self.VOID:
                self.stack.append(idx)
        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            if tag not in self.VOID:
                self.handle_endtag(tag)
        def handle_data(self, value):
            if self.nodes[self.stack[-1]]["tag"] not in (
                    "script", "style", "noscript"):
                self.nodes[self.stack[-1]]["text"] += value
        def handle_endtag(self, tag):
            for i in range(len(self.stack)-1, 0, -1):
                if self.nodes[self.stack[i]]["tag"] == tag:
                    del self.stack[i:]
                    return
        def scopes(self):
            texts = [x["text"] for x in self.nodes]
            ids = [{x["uuid"]} if x["uuid"] else set() for x in self.nodes]
            for idx in range(len(self.nodes)-1, 0, -1):
                parent = self.nodes[idx]["parent"]
                texts[parent] += " " + texts[idx]
                ids[parent].update(ids[idx])
            return texts, ids

    def norm(s):
        return re.sub(r"\s+", " ", s).strip()

    def hold(reason):
        return {"kind": "P30_L7_SONGSHAN_CANONICAL_ROTATION_V1",
                "platform_id": "14", "decision": "SOURCE_OR_IDENTITY_HOLD_NO_WRITE",
                "reason": str(reason)[:160], "source_receipts": receipts,
                "native_get_200_count": (sum(r["http_status"] == 200 for r in receipts)
                                          if native else 0),
                "same_uuid_review_lkg": 0, "persisted": False,
                "formal_accepted_fields": 0, "golden_accepted_events": 0,
                "published_events": 0,
                "release_state": "HARD_HOLD_NO_PUBLICATION"}
    try:
        pages = []
        for url in (SONGSHAN_PUBLIC_LIST, SONGSHAN_PUBLIC_DETAIL):
            status, content_type, raw, final_url = (public_get if native else fetcher)(url)
            if type(status) is not int or status != 200 or final_url != url:
                raise ValueError("SONGSHAN_HTTP_STATUS_OR_REDIRECT_HOLD")
            if not isinstance(raw, bytes) or not 0 < len(raw) <= 524288:
                raise ValueError("SONGSHAN_EMPTY_OR_OVERSIZE_HOLD")
            if not isinstance(content_type, str):
                raise ValueError("SONGSHAN_CONTENT_TYPE_HOLD")
            parts = [part.strip().lower() for part in content_type.split(";")]
            if parts[0] != "text/html":
                raise ValueError("SONGSHAN_NOT_HTML_HOLD")
            charset = next((part.split("=", 1)[1].strip('"') for part in parts[1:]
                            if part.startswith("charset=")), "utf-8")
            if charset not in ("utf-8", "big5", "cp950"):
                raise ValueError("SONGSHAN_CHARSET_HOLD")
            pages.append(raw.decode(charset, errors="strict"))
            receipts.append({"url": url, "http_status": 200, "bytes": len(raw),
                             "body_sha256": hashlib.sha256(raw).hexdigest(),
                             "transport": ("BUILTIN_NATIVE_GET" if native
                                           else "TEST_INJECTED_NOT_NATIVE")})
        listing, detail = BoundedDOM(), BoundedDOM()
        listing.feed(pages[0])
        detail.feed(pages[1])
        list_text, list_ids = listing.scopes()
        detail_text, _ = detail.scopes()
        expected_title = norm(SONGSHAN_EVENT_TITLE)
        if not listing.anchors or not any(
                uid == SONGSHAN_EVENT_UUID and
                any(expected_title in norm(list_text[parent]) and
                    list_ids[parent] == {SONGSHAN_EVENT_UUID} and
                    len(list_text[parent]) <= 2500 and
                    listing.nodes[parent]["tag"] not in ("body", "html", "root")
                    for parent in _songshan_ancestors(listing.nodes, idx))
                for idx, uid in listing.anchors):
            raise ValueError("SONGSHAN_LIST_TITLE_UUID_LOCAL_EDGE_HOLD")
        if any(uid != SONGSHAN_EVENT_UUID and
               expected_title in norm(list_text[idx]) and
               len(list_text[idx]) <= 500
               for idx, uid in listing.anchors):
            raise ValueError("SONGSHAN_LIST_TITLE_CONFLICTING_UUID_HOLD")
        # Native 2/2 HTTP200 first failed at H1/H2-only heading ownership.
        # Test the independently observable H3 detail-title hypothesis; never
        # borrow an unscoped body/footer title or accept duplicate headings.
        heading_roles = [(detail.nodes[idx]["tag"], norm(detail_text[idx]))
                         for idx in detail.headings
                         if detail.nodes[idx]["tag"] in ("h1", "h2", "h3")]
        exact_matches = [(tag, value) for tag, value in heading_roles
                         if value == expected_title]
        if len(exact_matches) != 1:
            by_tag = {tag: sum(1 for kind, value in heading_roles
                               if kind == tag and value == expected_title)
                      for tag in ("h1", "h2", "h3")}
            raise ValueError("SONGSHAN_DETAIL_EXACT_HEADING_HOLD:" +
                             ",".join(f"{tag}={count}" for tag, count in by_tag.items()))
        if activity_uuid(SONGSHAN_PUBLIC_DETAIL) != SONGSHAN_EVENT_UUID:
            raise ValueError("SONGSHAN_DETAIL_UUID_IDENTITY_HOLD")
        observed = datetime.now(timezone.utc) if native else (
            now_utc or datetime.now(timezone.utc))
        if not isinstance(observed, datetime) or observed.utcoffset() is None:
            raise ValueError("SONGSHAN_OBSERVATION_CLOCK_HOLD")
        if previous and (previous["rows"][0]["_candidate"].get("platform_id") != "14" or
                         previous["rows"][0]["_candidate"].get("source_event_id") !=
                         SONGSHAN_EVENT_UUID):
            raise ValueError("SONGSHAN_PREVIOUS_LKG_OTHER_SOURCE_HOLD")
        stamp = observed.isoformat()
        candidate = {
            "title": SONGSHAN_EVENT_TITLE, "url": SONGSHAN_PUBLIC_DETAIL,
            "platform": "松山文創", "type": "展覽", "scraped_at": stamp,
            "_candidate": {
                "scope": "CANDIDATE_PREVIEW_ONLY", "decision": "REVIEW_WITH_HOLD",
                "published": False, "golden_accepted": False,
                "formal_field_pass": False, "record_id": "14:" + SONGSHAN_EVENT_UUID,
                "platform_id": "14", "source_event_id": SONGSHAN_EVENT_UUID,
                "source_identity_kind": "OFFICIAL_LIST_DETAIL_UUID_REVIEW",
                "source_class": "OFFICIAL_VENUE_NON_SESSION",
                "sources": [SONGSHAN_PUBLIC_LIST, SONGSHAN_PUBLIC_DETAIL],
                "hold_reasons": ["DATE_VENUE_FIELD_INDEPENDENT_AUTHORITY_PENDING",
                                 "REVIEW_ONLY_NOT_FORMAL"]}}
        rows, quality = build_candidate_dataset([candidate])
        if len(rows) != 1 or quality["rejectedRows"]:
            raise ValueError("SONGSHAN_CANDIDATE_PIPELINE_HOLD")
        digest = _isolated_lkg_digest(rows)
        snapshot = {
            "kind": "P30_L7_ISOLATED_SOURCE_ADAPTER_SNAPSHOT_V1",
            "decision": "REVIEW_ONLY_NEW_OR_UPDATED", "rows": rows,
            "quality": quality,
            "field_receipts": [{
                "field": "title", "role": "EVENT_TITLE",
                "value": SONGSHAN_EVENT_TITLE, "source": SONGSHAN_PUBLIC_DETAIL,
                "observed_at": stamp, "decision": "REVIEW"}],
            "source_receipts": {
                "list_url": SONGSHAN_PUBLIC_LIST,
                "detail_url": SONGSHAN_PUBLIC_DETAIL,
                "bounded_acquisition": {
                    "kind": "P30_L7_BOUNDED_SOURCE_RECEIPTS_V1",
                    "observed_at_utc": stamp,
                    "transport": ("BUILTIN_NATIVE_GET" if native
                                  else "TEST_INJECTED_NOT_NATIVE"),
                    "list_body_sha256": receipts[0]["body_sha256"],
                    "detail_body_sha256": receipts[1]["body_sha256"],
                    "list_url": SONGSHAN_PUBLIC_LIST,
                    "detail_url": SONGSHAN_PUBLIC_DETAIL,
                    "decision": "SOURCE_BODY_REVIEW_ONLY_NOT_FORMAL"}},
            "incremental_diff": {
                "added_ids": ["14:" + SONGSHAN_EVENT_UUID] if not previous else [],
                "removed_ids": [],
                "changed": not previous or digest != previous["last_known_good_sha256"]},
            "last_known_good_sha256": digest, "native_get_verified": False,
            "formal_accepted_fields": 0, "golden_accepted_events": 0,
            "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION"}
        persist_isolated_review_lkg(
            snapshot, destination, repo_root,
            expected_previous_sha256=(previous["last_known_good_sha256"]
                                      if previous else None))
        return {"kind": "P30_L7_SONGSHAN_CANONICAL_ROTATION_V1",
                "platform_id": "14", "decision": "REVIEW_ONLY",
                "source_receipts": receipts,
                "native_get_200_count": 2 if native else 0,
                "same_uuid_review_lkg": 1, "persisted": True,
                "official_uuid": SONGSHAN_EVENT_UUID,
                "lkg_sha256": digest, "formal_accepted_fields": 0,
                "golden_accepted_events": 0, "published_events": 0,
                "release_state": "HARD_HOLD_NO_PUBLICATION"}
    except (ValueError, OSError, TimeoutError, UnicodeError, TypeError) as exc:
        return hold(type(exc).__name__ + ":" + str(exc))


def _songshan_ancestors(nodes, idx):
    """At most six local DOM parents, never global page-title matching."""
    for _ in range(6):
        if idx is None:
            break
        yield idx
        idx = nodes[idx]["parent"]


# P30-L7 B canonical #17: reuse existing actId identity and sealed isolated LKG.
# No new platform, network access, field promotion, Golden, or publisher.
def assess_cksmh_non_session_field_authority(snapshot, now_utc=None):
    """Fail-closed independent field-readiness contract for existing CKSMH actId."""
    import re
    from datetime import timezone
    report = {
        "kind": "P30_L7_CKSMH_CANONICAL_FIELD_AUTHORITY_V1",
        "platform_id": "17", "source_event_id": "61023",
        "decision": "HOLD_NO_SEALED_NATIVE_AUTHORITY",
        "first_failure": "CKSMH_NO_SNAPSHOT",
        "field_matrix": [],
        "requirements": [
            "CANONICAL_PLATFORM_17_ONLY", "EXACT_LIST_ACTID_DETAIL_IDENTITY",
            "SEALED_NATIVE_SOURCE_BODY_SHA256_AND_UTC_FRESHNESS",
            "EVENT_LOCAL_DATE_AND_MULTI_SESSION_SCOPE",
            "VENUE_HALL_NOT_SINGLE_HALL_INFERRED",
            "INDEPENDENT_FIELD_AUTHORITY_AND_CONFLICT_DECISION",
        ],
        "new_native_get": 0, "native_same_id_review_lkg_new": 0,
        "formal_accepted_fields": 0, "golden_accepted_events": 0,
        "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION",
    }
    if snapshot is None:
        return report
    _validate_isolated_lkg_snapshot(snapshot)
    row = snapshot["rows"][0]
    meta = row["_candidate"]
    sources = snapshot["source_receipts"]
    acquisition = sources.get("bounded_acquisition")
    if (meta.get("platform_id") != "17"
            or meta.get("source_event_id") != "61023"
            or meta.get("record_id") != "17:61023"
            or meta.get("sources") != [CKSMH_PUBLIC_LIST, CKSMH_PUBLIC_DETAIL]
            or row.get("url") != CKSMH_PUBLIC_DETAIL
            or row.get("title") != CKSMH_ROTATION_TITLE
            or sources.get("list_url") != CKSMH_PUBLIC_LIST
            or sources.get("detail_url") != CKSMH_PUBLIC_DETAIL):
        raise ValueError("CKSMH_FIELD_CROSS_EVENT_OR_PLATFORM_HOLD")
    fields = snapshot["field_receipts"]
    if (len(fields) != 1
            or fields[0] != {
                "field": "title", "value": CKSMH_ROTATION_TITLE,
                "role": "EVENT_TITLE", "source": CKSMH_PUBLIC_DETAIL,
                "observed_at": row["scraped_at"], "decision": "REVIEW",
            }):
        raise ValueError("CKSMH_FIELD_UNSEALED_ROLE_OR_SOURCE_HOLD")
    if not isinstance(acquisition, dict):
        raise ValueError("CKSMH_FIELD_ACQUISITION_REQUIRED_HOLD")
    # The source hash/clock/URL contract must bind to this exact actId.
    _validate_nonpublishing_source_receipt(
        acquisition, CKSMH_PUBLIC_LIST, CKSMH_PUBLIC_DETAIL,
        row["scraped_at"])
    now = now_utc or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("CKSMH_FIELD_CLOCK_HOLD")
    try:
        observed = datetime.fromisoformat(row["scraped_at"].replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("CKSMH_FIELD_OBSERVATION_CLOCK_HOLD") from None
    if observed.utcoffset() is None:
        raise ValueError("CKSMH_FIELD_OBSERVATION_CLOCK_HOLD")
    fresh = 0 <= (now - observed).total_seconds() <= 86400
    native = acquisition.get("transport") == "BUILTIN_NATIVE_GET"
    report["field_matrix"] = [
        {
            "field": "title", "value": CKSMH_ROTATION_TITLE,
            "role": "EVENT_TITLE", "source_url": CKSMH_PUBLIC_DETAIL,
            "observed_at_utc": row["scraped_at"],
            "list_body_sha256": acquisition["list_body_sha256"],
            "detail_body_sha256": acquisition["detail_body_sha256"],
            "native_body_receipt": native, "fresh_within_24h": fresh,
            "independent_field_authority": False,
            "decision": "SOURCE_TITLE_REVIEW_ONLY" if native and fresh
                        else "HOLD_NATIVE_FRESHNESS_OR_AUTHORITY",
            "formal_accepted": False,
        },
        {
            "field": "event_date_sessions", "role": "MULTI_SESSION_UNRESOLVED",
            "value": None, "source_url": CKSMH_PUBLIC_DETAIL,
            "decision": "HOLD_INDEPENDENT_EVENT_LOCAL_DATE_AUTHORITY",
            "formal_accepted": False,
        },
        {
            "field": "venue_halls", "role": "MULTI_VENUE_UNRESOLVED",
            "value": None, "source_url": CKSMH_PUBLIC_DETAIL,
            "decision": "HOLD_INDEPENDENT_HALL_AND_SESSION_AUTHORITY",
            "formal_accepted": False,
        },
    ]
    report["decision"] = ("REVIEW_TITLE_ONLY_INDEPENDENT_FIELDS_HOLD"
                          if native and fresh
                          else "HOLD_NATIVE_FRESHNESS_OR_AUTHORITY")
    report["first_failure"] = ("CKSMH_DATE_SESSION_HALL_AUTHORITY_PENDING"
                               if native and fresh
                               else "CKSMH_NATIVE_OR_FRESHNESS_NOT_VERIFIED")
    return report


def assess_tmc_cksmh_fixed_nonpublishing_field_gate(tmc_snapshot=None,
                                                    cksmh_snapshot=None,
                                                    now_utc=None):
    """Run A and B canonical field gates without GET, persistence, or acceptance."""
    a = assess_tmc_non_session_field_authority(tmc_snapshot, now_utc)
    b = assess_cksmh_non_session_field_authority(cksmh_snapshot, now_utc)
    return {
        "kind": "P30_L7_FIXED_A_B_CANONICAL_FIELD_GATE_V1",
        "A": a, "B": b,
        "source_identity": {
            "A": "TMC_OFFICIAL:" + PUBLIC_TMC_DETAIL.rsplit("/", 1)[-1],
            "B": "17:61023",
            "cross_source_identity_merge": False,
        },
        "new_native_get": 0,
        "native_same_id_review_lkg_new": 0,
        "decision": "HOLD_INDEPENDENT_FIELD_AUTHORITY",
        "formal_accepted_fields": 0, "golden_accepted_events": 0,
        "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION",
    }


# Source-specific B canonical #17: parse four event-local session blocks.
# The official DETAIL has distinct registration periods, walking routes and
# meeting points. Neither registration dates nor meeting points are a ticket
# Session ID, a single event HALL, or a formal accepted field.
def extract_cksmh_event_local_session_roles(detail_html, source_url,
                                           observed_at_utc, body_sha256):
    """Strict bounded DETAIL role extraction; no GET, persistence or publication."""
    import re
    from html.parser import HTMLParser
    from datetime import datetime

    if source_url != CKSMH_PUBLIC_DETAIL:
        raise ValueError("CKSMH_SESSION_EXACT_DETAIL_URL_HOLD")
    if not isinstance(detail_html, str) or not detail_html.strip() or len(
            detail_html.encode("utf-8")) > 524288:
        raise ValueError("CKSMH_SESSION_BODY_BOUND_HOLD")
    if not isinstance(body_sha256, str) or not re.fullmatch(
            r"[0-9a-f]{64}", body_sha256):
        raise ValueError("CKSMH_SESSION_BODY_SHA256_HOLD")
    try:
        observed = datetime.fromisoformat(observed_at_utc.replace("Z", "+00:00"))
        if observed.utcoffset() is None:
            raise ValueError()
    except (ValueError, AttributeError, TypeError):
        raise ValueError("CKSMH_SESSION_OBSERVATION_CLOCK_HOLD") from None

    class VisibleText(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.skip = 0
            self.parts = []
        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "noscript", "template"):
                self.skip += 1
        def handle_endtag(self, tag):
            if tag in ("script", "style", "noscript", "template"):
                self.skip = max(0, self.skip - 1)
        def handle_data(self, data):
            if not self.skip and data.strip():
                self.parts.append(data)

    parser = VisibleText()
    parser.feed(detail_html)
    text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    if CKSMH_ROTATION_TITLE not in text:
        raise ValueError("CKSMH_SESSION_DETAIL_EVENT_TITLE_HOLD")
    start = re.search(r"Session Information|場次資訊|場次資料", text, re.I)
    if start is None:
        raise ValueError("CKSMH_SESSION_SECTION_START_HOLD")
    remainder = text[start.end():]
    end = re.search(
        r"Event Details|Registration Information|活動內容|活動詳情|報名資訊",
        remainder, re.I)
    if end is None:
        raise ValueError("CKSMH_SESSION_SECTION_END_HOLD")
    section = remainder[:end.start()]
    markers = list(re.finditer(r"〖\s*(\d{1,2})\s*〗", section))
    if [int(m.group(1)) for m in markers] != [1, 2, 3, 4]:
        raise ValueError("CKSMH_SESSION_FOUR_DISTINCT_ORDINALS_HOLD")
    date_pattern = re.compile(
        r"(20\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s*[~～]\s*"
        r"(20\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2})")
    rows = []
    for i, marker in enumerate(markers):
        block = section[marker.end():markers[i + 1].start()
                        if i + 1 < len(markers) else len(section)]
        registration = re.search(r"Registration Period|報名期間", block, re.I)
        if registration is None:
            raise ValueError("CKSMH_SESSION_REGISTRATION_BOUNDARY_HOLD")
        event_local = block[:registration.start()]
        dates = date_pattern.findall(event_local)
        if len(dates) != 1:
            raise ValueError("CKSMH_SESSION_EVENT_TIME_UNIQUE_HOLD")
        from datetime import datetime as DateTime
        first_date, first_time, last_date, last_time = dates[0]
        try:
            begin = DateTime.strptime(first_date + " " + first_time,
                                      "%Y/%m/%d %H:%M")
            finish = DateTime.strptime(last_date + " " + last_time,
                                       "%Y/%m/%d %H:%M")
        except ValueError:
            raise ValueError("CKSMH_SESSION_INVALID_EVENT_CLOCK_HOLD") from None
        if finish <= begin or (finish - begin).total_seconds() > 12 * 3600:
            raise ValueError("CKSMH_SESSION_EVENT_TIME_ORDER_HOLD")
        local_month_day = re.search(r"(?<!\d)(\d{1,2})/(\d{1,2})(?!\d)",
                                    event_local)
        if (local_month_day is None or
                (int(local_month_day.group(1)), int(local_month_day.group(2)))
                != (begin.month, begin.day)):
            raise ValueError("CKSMH_SESSION_HEADER_DATE_PARITY_HOLD")
        venue_labels = list(re.finditer(r"\bVenue\b|活動地點", block, re.I))
        if len(venue_labels) != 1:
            raise ValueError("CKSMH_SESSION_VENUE_LOCAL_UNIQUE_HOLD")
        after_venue = block[venue_labels[0].end():]
        venue_end = re.search(
            r"\bNote\s*:|備註|Available Slots|可報名人數|Event Details",
            after_venue, re.I)
        if venue_end is None:
            raise ValueError("CKSMH_SESSION_VENUE_BOUNDARY_HOLD")
        meeting = after_venue[:venue_end.start()].strip(" \t\r\n:：-")
        if not 8 <= len(meeting) <= 180:
            raise ValueError("CKSMH_SESSION_MEETING_POINT_BOUNDS_HOLD")
        venue_clock = re.match(r"(\d{2}:\d{2})", meeting)
        if venue_clock and venue_clock.group(1) != first_time:
            raise ValueError("CKSMH_SESSION_MEETING_CLOCK_CONFLICT_HOLD")
        rows.append({
            "local_ordinal_not_session_id": i + 1,
            "show_start": begin.strftime("%Y-%m-%dT%H:%M"),
            "show_end": finish.strftime("%Y-%m-%dT%H:%M"),
            "showtime_role": "OFFICIAL_EVENT_LOCAL_SHOWTIME_REVIEW",
            "meeting_point": meeting,
            "meeting_role": "OFFICIAL_SESSION_MEETING_POINT_NOT_HALL",
            "registration_period_is_showtime": False,
            "ticket_session_id": None, "formal_accepted": False,
        })
    if len({r["show_start"] for r in rows}) != 4:
        raise ValueError("CKSMH_SESSION_DUPLICATE_EVENT_TIME_HOLD")
    return {
        "kind": "P30_L7_CKSMH_FOUR_EVENT_LOCAL_SESSIONS_V1",
        "platform_id": "17", "source_event_id": "61023",
        "detail_url": CKSMH_PUBLIC_DETAIL,
        "observed_at_utc": observed.isoformat(),
        "detail_body_sha256": body_sha256,
        "decision": "REVIEW_FOUR_EVENT_LOCAL_SESSIONS_NOT_FORMAL",
        "session_count": 4, "sessions": rows,
        "single_event_hall": None, "native_transport_independently_verified": False,
        "list_detail_identity_this_function": "HISTORICAL_DEPENDENCY_NOT_RECHECKED",
        "formal_accepted_fields": 0, "golden_accepted_events": 0,
        "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION",
    }


def _validate_nonpublishing_source_receipt(acquisition, list_url,
                                           detail_url, observed_at):
    """Bind bounded source hashes, clock and exact URL; not native attestation."""
    import re
    if (not isinstance(acquisition, dict) or
            acquisition.get("kind") != "P30_L7_BOUNDED_SOURCE_RECEIPTS_V1" or
            acquisition.get("decision") != "SOURCE_BODY_REVIEW_ONLY_NOT_FORMAL" or
            acquisition.get("observed_at_utc") != observed_at or
            acquisition.get("list_url") != list_url or
            acquisition.get("detail_url") != detail_url or
            acquisition.get("transport") not in (
                "BUILTIN_NATIVE_GET", "TEST_INJECTED_NOT_NATIVE") or
            any(not isinstance(acquisition.get(k), str) or
                not re.fullmatch(r"[0-9a-f]{64}", acquisition[k])
                for k in ("list_body_sha256", "detail_body_sha256"))):
        raise ValueError("SOURCE_RECEIPT_UNBOUND_URL_CLOCK_OR_SHA_HOLD")
    return acquisition


def diagnose_cksmh_session_dom_boundary(detail_html, source_url, body_sha256):
    """Bounded source-owned DOM visibility diagnosis; never a parsing PASS.

    Does not persist raw HTML, fetch pages, infer a session ID or accept fields.
    A rendered public reader may expose four sessions while native HTML is a
    JS shell, has early tab boundaries, or duplicates responsive ordinal nodes.
    """
    import re
    from html.parser import HTMLParser

    if source_url != CKSMH_PUBLIC_DETAIL:
        raise ValueError("CKSMH_DOM_EXACT_DETAIL_URL_HOLD")
    if not isinstance(detail_html, str) or not detail_html.strip() or len(
            detail_html.encode("utf-8")) > 524288:
        raise ValueError("CKSMH_DOM_BODY_BOUND_HOLD")
    if not isinstance(body_sha256, str) or not re.fullmatch(
            r"[0-9a-f]{64}", body_sha256):
        raise ValueError("CKSMH_DOM_BODY_SHA256_HOLD")

    class Visible(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.skip = 0
            self.parts = []
        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "noscript", "template"):
                self.skip += 1
        def handle_endtag(self, tag):
            if tag in ("script", "style", "noscript", "template"):
                self.skip = max(0, self.skip - 1)
        def handle_data(self, value):
            if not self.skip and value.strip():
                self.parts.append(value)

    parser = Visible()
    parser.feed(detail_html)
    visible = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    marker = re.compile(r"〖\s*(\d{1,2})\s*〗")
    start_pattern = re.compile(r"Session Information|場次資訊|場次資料", re.I)
    end_pattern = re.compile(
        r"Event Details|Registration Information|活動內容|活動詳情|報名資訊",
        re.I)
    starts = list(start_pattern.finditer(visible))
    all_ordinals = [int(m.group(1)) for m in marker.finditer(visible)]
    scoped_ordinals = []
    boundary = "NONE"
    if starts:
        after = visible[starts[0].end():]
        ending = end_pattern.search(after)
        boundary = "FIRST_END_MARKER" if ending else "MISSING_END_MARKER"
        section = after[:ending.start()] if ending else after
        scoped_ordinals = [int(m.group(1)) for m in marker.finditer(section)]

    if not starts:
        diagnosis = "NO_VISIBLE_SESSION_SECTION_HOLD"
    elif not all_ordinals:
        diagnosis = "SERVER_HTML_NO_VISIBLE_ORDINALS_HOLD"
    elif scoped_ordinals == [1, 2, 3, 4]:
        diagnosis = "FOUR_SCOPED_ORDINALS_REVIEW_NOT_FIELD_PASS"
    elif all_ordinals == [1, 2, 3, 4] and scoped_ordinals != all_ordinals:
        diagnosis = "EARLY_SECTION_BOUNDARY_HOLD"
    else:
        diagnosis = "VISIBLE_ORDINAL_SCOPE_OR_DUPLICATE_CONFLICT_HOLD"

    return {
        "kind": "P30_L7_CKSMH_NATIVE_DOM_BOUNDARY_DIAGNOSTIC_V1",
        "source_url": CKSMH_PUBLIC_DETAIL,
        "detail_body_sha256": body_sha256,
        "visible_title_present": CKSMH_ROTATION_TITLE in visible,
        "session_section_heading_count": len(starts),
        "all_visible_ordinal_count": len(all_ordinals),
        "all_visible_ordinals_bounded": all_ordinals[:16],
        "first_section_ordinal_count": len(scoped_ordinals),
        "first_section_ordinals_bounded": scoped_ordinals[:16],
        "first_section_boundary": boundary,
        "diagnosis": diagnosis,
        "raw_html_saved": False,
        "native_transport_independently_verified": False,
        "formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }
