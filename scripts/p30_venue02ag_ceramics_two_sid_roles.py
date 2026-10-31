#!/usr/bin/env python3
"""VENUE-02AG: two distinct official Ceramics SID role-layout candidates.

Source-specific REVIEW only. Never merge adjacent official SID identities,
infer ticket Event IDs, or publish field candidates. No network or raw HTML
retention; independent public reader observations are external evidence.
"""
import hashlib
import re
from datetime import date
from bs4 import BeautifulSoup
from p30_venue02ac_ceramics_sid_title import OBSERVED, audit_sid_title
from p30_venue02z_ceramics_fields import DATE, VENUE, norm

HOLD = "HARD_HOLD_NO_PUBLICATION"
SOURCE = "CERAMICS_P0_NEW_TAIPEI"
LABEL = re.compile(r"^展覽(日期|地點)\s*[:：]")
SKIP = {"script", "style", "noscript", "title"}

def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def inspect_one(url, html, sid, title, observed_at):
    out = {"gate": "P30-VENUE-02AG", "source": SOURCE, "sid": sid,
           "sidBound": False, "titleBound": False, "roleNodes": 0,
           "dateCandidates": 0, "venueCandidates": 0, "candidateProvenance": [],
           "acceptedFields": 0, "goldenAccepted": 0, "published": False,
           "ticketEventId": None, "releaseState": HOLD}
    if not isinstance(observed_at, str) or not re.fullmatch(
            r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ", observed_at):
        return dict(out, decision="HOLD_MISSING_OBSERVATION_PROVENANCE")
    if OBSERVED.get(sid) != title:
        return dict(out, decision="HOLD_CROSS_SID_TITLE")
    prior = audit_sid_title(url, html, sid, title)
    out["sidBound"] = prior["sidBound"]
    out["titleBound"] = prior["detailHeadingMatches"] == 1
    if not out["sidBound"] or not out["titleBound"]:
        return dict(out, decision="HOLD_SID_OR_HEADING_IDENTITY")
    soup = BeautifulSoup(html, "html.parser")
    fragments = []
    for node in soup.find_all(string=True, limit=5000):
        if node.parent.name in SKIP:
            continue
        value = norm(str(node))
        if "展覽日期" not in value and "展覽地點" not in value:
            continue
        out["roleNodes"] += 1
        if len(value) > 220 or node.parent.name not in ("p", "li", "div", "span", "td", "dd"):
            return dict(out, decision="HOLD_OVERSIZED_OR_UNBOUND_ROLE_NODE")
        fragments.extend(re.split(r"/(?=\s*展覽地點\s*[:：])", value))
    if not fragments:
        return dict(out, decision="HOLD_NO_ROLE_TEXT")
    dates, places = [], []
    for raw in fragments:
        value = norm(raw)
        if not LABEL.match(value) or any(x in value for x in ("售票日期", "報名日期", "售票期間", "報名期間")):
            return dict(out, decision="HOLD_MIXED_OR_UNLABELED_ROLE_TEXT")
        if value.startswith("展覽日期"):
            match = DATE.fullmatch(value)
            if not match:
                return dict(out, decision="HOLD_DATE_LABEL_VALUE_NOT_EXACT")
            y, mo, d, ey, em, ed = match.groups()
            try:
                first = date(int(y), int(mo), int(d))
                last = date(int(ey or y), int(em), int(ed))
            except ValueError:
                return dict(out, decision="HOLD_INVALID_DATE")
            if first > last:
                return dict(out, decision="HOLD_REVERSED_DATE_RANGE")
            dates.append(first.isoformat() + "/" + last.isoformat())
        elif value.startswith("展覽地點"):
            match = VENUE.fullmatch(value)
            if not match:
                return dict(out, decision="HOLD_VENUE_LABEL_VALUE_NOT_EXACT")
            room = norm(match.group(1))
            if not 2 <= len(room) <= 80 or any(x in room for x in ("日期", "時間", "售票", "報名")):
                return dict(out, decision="HOLD_VENUE_MIXED_ROLE")
            places.append(room)
    out["dateCandidates"], out["venueCandidates"] = len(dates), len(places)
    if len(dates) != 1 or len(places) != 1:
        return dict(out, decision="HOLD_DUPLICATE_OR_MISSING_ROLE")
    for role, value in (("EXHIBITION_DATE_RANGE", dates[0]), ("EXHIBITION_VENUE", places[0])):
        out["candidateProvenance"].append({
            "source": SOURCE, "source_sid": sid, "observed_at": observed_at,
            "role": role, "decision": "REVIEW_CANDIDATE_NOT_ACCEPTED",
            "valueSHA256": digest(value)})
    return dict(out, decision="REVIEW_EXACT_SID_DATE_AND_VENUE_CANDIDATES")

def inspect_two(records):
    out = {"gate": "P30-VENUE-02AG", "source": SOURCE,
           "distinctSIDs": 0, "records": [], "candidateFieldCount": 0,
           "acceptedFields": 0, "goldenAccepted": 0, "published": False,
           "ticketEventId": None, "releaseState": HOLD}
    if len(records) != 2:
        return dict(out, decision="HOLD_NOT_TWO_BOUNDED_RECORDS")
    sids = [r.get("sid") for r in records]
    if len(set(sids)) != 2 or any(sid not in OBSERVED for sid in sids):
        return dict(out, decision="HOLD_DUPLICATE_OR_UNBOUNDED_SID")
    out["distinctSIDs"] = 2
    for r in records:
        x = inspect_one(r.get("url"), r.get("html", ""), r["sid"],
                        r.get("title"), r.get("observed_at"))
        out["records"].append({k:v for k,v in x.items() if k not in ("sid", "gate", "source")})
        out["candidateFieldCount"] += len(x["candidateProvenance"])
        if not x["decision"].startswith("REVIEW_"):
            return dict(out, decision="HOLD_ONE_OR_MORE_SID_FIELD_ROLES")
    return dict(out, decision="REVIEW_TWO_DISTINCT_EXHIBITION_SIDS_NO_FIELD_ACCEPTANCE")

if __name__ == "__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_IMPLICIT_NETWORK")
