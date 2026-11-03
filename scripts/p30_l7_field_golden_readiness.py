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
                                    observed_at_utc, now_utc=None):
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


def main():
    path = Path(__file__).resolve().parents[1] / "tests/p30/fixtures/p30_l7_prince_field_readiness.json"
    print(json.dumps(validate(json.loads(path.read_text(encoding="utf-8"))),sort_keys=True))
if __name__ == "__main__": main()
