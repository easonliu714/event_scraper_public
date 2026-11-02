"""Fail-closed field-level Golden-readiness contract; NEVER grants Golden acceptance."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

TICKET = "https://www.opentix.life/event/2072516129034670080"
VENUE = "https://tpac.org.taipei/program/2088"
LIST = "https://tpac.org.taipei/program"
READY = "READY_FOR_INDEPENDENT_GOLDEN_REVIEW"
HOLD = "HOLD"
READY_FIELDS = {
    ("A", "title"): ("EVENT_TITLE", TICKET),
    ("A", "ticket_event_url"): ("EVENT_URL", TICKET),
    ("A", "venue"): ("EVENT_VENUE", TICKET),
    ("B", "title"): ("EVENT_TITLE", VENUE),
    ("B", "venue_room"): ("VENUE_ROOM", VENUE),
    ("B", "showtimes"): ("VENUE_ANNOUNCED_SHOWTIME", VENUE),
    ("B", "direct_ticket_event_url"): ("VENUE_TO_TICKET_EVENT_EDGE", VENUE),
}
HOLD_FIELDS = {
    ("A", "age_min"), ("A", "sale_markers"), ("A", "ticket_session_id"),
    ("A", "admission_price"), ("A", "img_url"),
    ("B", "index_advertised_range"), ("B", "age_min"),
    ("B", "advertised_price_range"), ("B", "img_url"),
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
    if by["A","age_min"] != 7 or by["B","age_min"] != 6:
        raise ValueError("AGE_CONFLICT_NOT_PRESERVED")
    if by["A","ticket_session_id"] is not None or by["A","admission_price"] is not None:
        raise ValueError("UNVERIFIED_TICKET_FIELDS")
    if by["A","img_url"] is not None or by["B","img_url"] is not None:
        raise ValueError("UNVERIFIED_IMAGE_URL")
    if by["B","advertised_price_range"] != [1200,2200]:
        raise ValueError("VENUE_ADVERTISED_PRICE_CHANGED")
    if by["B","index_advertised_range"] != ["2026-11-04","2026-11-14"]:
        raise ValueError("INDEX_DATE_CONFLICT_NOT_PRESERVED")
    shows = by["B","showtimes"]
    if not isinstance(shows,list) or len(shows) != 12 or len(set(shows)) != 12:
        raise ValueError("VENUE_SHOWS_HOLD")
    for show in shows:
        try:
            dt=datetime.fromisoformat(show)
            if dt.utcoffset().total_seconds()!=28800: raise ValueError()
        except (ValueError,TypeError,AttributeError):
            raise ValueError("VENUE_SHOW_TIMEZONE_HOLD")
    return {"A_review_ready":3,"B_review_ready":4,"formal_accepted":0,
            "golden":0,"published":0,"native_get":0,
            "decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"}

def main():
    path = Path(__file__).resolve().parents[1] / "tests/p30/fixtures/p30_l7_prince_field_readiness.json"
    print(json.dumps(validate(json.loads(path.read_text(encoding="utf-8"))),sort_keys=True))
if __name__ == "__main__": main()
