"""SHA-pinned historical TaiNEX official HTTP audit receipts -> isolated REVIEW.

#98 archived same-run LIST+DETAIL /event/689; #100 archived DETAIL-only
/event/690. Original HTML was not retained; no new GET or FIELD acceptance.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HOLD = "HARD_HOLD_NO_PUBLICATION"
LIST = "https://www.tainex.com.tw/event"
SOURCE_CLASS = "HISTORICAL_NATIVE_AUDIT_REPLAY"
HOLDS = ["HISTORICAL_NATIVE_RECEIPT_NOT_CURRENT_SOURCE",
         "ARCHIVED_AUDIT_ONLY_RAW_HTML_NOT_AVAILABLE",
         "FIELD_VALUE_NOT_INDEPENDENTLY_ACCEPTED",
         "TICKET_SESSION_AND_GENERAL_MIN_PRICE_NOT_ACCEPTED"]
SPECS = {
    "689": dict(title="2026臺灣國際咖啡展", gate="P30-VENUE-02H",
                run=40969673735, artifact=12939228326,
                zip_sha="7de0da813036bd826edead7f9205202900fd56c09fdf60743160390b16b62242",
                audit_sha="4ff3db387f481aae1db8b197e17a4e1cdfd21d59676829807c340950c8a3d2cb",
                stamp="2026-10-29T22:57:20.076592+00:00",
                body_shas=["68480cc1076f8c78d431ff0ef1d57050a4285b1d59af5b968012a802676512cb",
                           "b5bfaf3c9c87b89d319d227478df88629c1c1332ca325fd50107c9af5d749912"],
                sources=[LIST, "https://www.tainex.com.tw/event/689"]),
    "690": dict(title="2026臺灣茶業博覽會", gate="P30-VENUE-02I",
                run=40976369881, artifact=12941823947,
                zip_sha="bcf43ac34816df2f3324cf9fecbe3a2b3cce3fdffa1e7a5b8cd9cec628ce0baa",
                audit_sha="5419196807c6a7965333809ad19148803815bb692c6142df68d349d9661cbe89",
                stamp="2026-10-29T23:55:51.744805+00:00",
                body_shas=["67b1584bd00fed3eff13df8ef0fb4a7ac43886609e649e1606d8fd317ce49fa0"],
                sources=["https://www.tainex.com.tw/event/690"]),
}


def _http(r, sha, role):
    return (isinstance(r, dict) and r.get("urlRole") == role
            and r.get("httpStatus") == 200
            and r.get("decision") == "REVIEW_HTTP_200_HTML"
            and type(r.get("bodyBytes")) is int and 0 < r["bodyBytes"] <= 180000
            and r.get("bodySHA256") == sha)


def inspect_archived_native(event_id, raw, as_of):
    """Only exact audited bytes qualify; the unavailable HTML is not reattested."""
    if event_id not in SPECS or not isinstance(raw, bytes):
        raise ValueError("ARCHIVED_NATIVE_SOURCE_ID_HOLD")
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("CLOCK_TIMEZONE_HOLD")
    s = SPECS[event_id]
    if hashlib.sha256(raw).hexdigest() != s["audit_sha"]:
        raise ValueError("ARCHIVED_NATIVE_AUDIT_SHA_HOLD")
    a = json.loads(raw)
    if (a.get("observedAtUTC") != s["stamp"]
            or datetime.fromisoformat(s["stamp"]).astimezone(timezone.utc)
               > as_of.astimezone(timezone.utc)
            or a.get("source") != "TAINEX_OFFICIAL_VENUE"
            or a.get("venueLocalIdReview") != event_id
            or a.get("acceptedFields") != 0 or a.get("goldenAccepted") != 0
            or a.get("published") is not False or a.get("ticketEventId") is not None
            or a.get("releaseState") != HOLD):
        raise ValueError("ARCHIVED_NATIVE_IDENTITY_OR_ROLE_HOLD")
    if event_id == "689":
        rr = a.get("receipts")
        if (a.get("decision") != "REVIEW_LIVE_LIST_DETAIL_IDENTITY_NO_PROMOTION"
                or a.get("identity") != "REVIEW_SAME_ORIGIN_PATH_AND_EXACT_TITLE"
                or a.get("listExactAnchors") != 1 or a.get("detailExactHeadings") != 1
                or a.get("requestCount") != 2 or a.get("requestBudget") != 2
                or a.get("roleLabelPresence") != {
                    "exhibitionPeriod": True, "organizer": True, "venue": True}
                or not isinstance(rr, list) or len(rr) != 2
                or not _http(rr[0], s["body_shas"][0], "LIST")
                or not _http(rr[1], s["body_shas"][1], "DETAIL")):
            raise ValueError("ARCHIVED_NATIVE_LIST_DETAIL_HOLD")
    else:
        fp = a.get("fieldProvenance")
        roles = {"exhibitionPeriod": "EXHIBITION_RANGE_NOT_SESSION_START",
                 "organizer": "ORGANIZER_NOT_TICKET_EVENT_ID",
                 "venue": "VENUE_ROLE_NOT_TICKET_URL"}
        if (a.get("decision") != "REVIEW_ONE_OFFICIAL_DETAIL_ROLE_PROVENANCE_NO_PROMOTION"
                or a.get("sourceURL") != s["sources"][0]
                or a.get("distinctFrom689") != "REVIEW_DISTINCT_SOURCE_LOCAL_IDS_NO_MERGE"
                or a.get("requestCount") != 1 or a.get("requestBudget") != 1
                or a.get("roleLabelCounts") != {k: 1 for k in roles}
                or not _http(a.get("receipt"), s["body_shas"][0], "DETAIL")
                or not isinstance(fp, dict) or set(fp) != set(roles)
                or any(fp[k] != {
                    "source": s["sources"][0], "observed_at": s["stamp"],
                    "role": role, "decision": "REVIEW_LABEL_PRESENCE_NO_VALUE_ACCEPTANCE"}
                    for k, role in roles.items())):
            raise ValueError("ARCHIVED_NATIVE_DETAIL_ONLY_HOLD")
    url = "https://www.tainex.com.tw/event/" + event_id
    holds = HOLDS + (["LIST_EDGE_NOT_ATTESTED_IN_SAME_NATIVE_RUN"] if event_id == "690" else [])
    candidate = {
        "title": s["title"], "url": url, "platform": "台北南港展覽館",
        "type": "展覽", "scraped_at": s["stamp"],
        "date": "未確認", "location": "未確認", "price": "未確認",
        "_candidate": {
            "scope": "CANDIDATE_PREVIEW_ONLY", "decision": "REVIEW_WITH_HOLD",
            "platform_id": "TAINEX", "source_event_id": event_id,
            "record_id": "TAINEX:event:" + event_id, "source_class": SOURCE_CLASS,
            "sources": list(s["sources"]), "hold_reasons": holds,
            "field_evidence": {}, "formal_field_pass": False,
            "golden_accepted": False, "published": False,
            "ticket_session_id": None, "inventory": None}}
    return {"candidate": candidate, "gate": s["gate"], "native_run_id": s["run"],
            "artifact_id": s["artifact"], "artifact_zip_sha256": s["zip_sha"],
            "audit_sha256": s["audit_sha"], "body_sha256": list(s["body_shas"]),
            "same_run_list_detail": event_id == "689",
            "raw_html_available": False, "native_get_this_run": 0,
            "accepted_fields": 0}


def validate_archived_prior(row, as_of):
    """Reject foreign identity, stale/forged fields and false promotion."""
    m = row["_candidate"]
    eid = m.get("source_event_id")
    s = SPECS.get(eid)
    if not s:
        raise ValueError("PRIOR_NATIVE_SOURCE_BINDING_HOLD")
    holds = HOLDS + (["LIST_EDGE_NOT_ATTESTED_IN_SAME_NATIVE_RUN"] if eid == "690" else [])
    if (row.get("title") != s["title"]
            or row.get("url") != "https://www.tainex.com.tw/event/" + eid
            or row.get("platform") != "台北南港展覽館"
            or row.get("type") != "展覽" or row.get("scraped_at") != s["stamp"]
            or any(row.get(k) != "未確認" for k in ("date", "location", "price"))
            or m.get("platform_id") != "TAINEX"
            or m.get("record_id") != "TAINEX:event:" + eid
            or m.get("source_class") != SOURCE_CLASS
            or m.get("sources") != s["sources"] or m.get("hold_reasons") != holds
            or m.get("field_evidence") != {}
            or any(m.get(k) is not False for k in
                   ("published", "golden_accepted", "formal_field_pass"))
            or datetime.fromisoformat(s["stamp"]).astimezone(timezone.utc)
               > as_of.astimezone(timezone.utc)):
        raise ValueError("PRIOR_NATIVE_SOURCE_BINDING_HOLD")


def archived_inputs(directory):
    """Read exact pinned audit JSON files locally; never make network requests."""
    root = Path(directory)
    return [{"id": eid, "audit_bytes": (root / ("tainex_" + eid + "_native_audit.json")).read_bytes()}
            for eid in ("689", "690")]
