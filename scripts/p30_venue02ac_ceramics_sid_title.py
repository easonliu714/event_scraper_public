#!/usr/bin/env python3
"""P30-VENUE-02AC: prevent Ceramics exhibit SID/title/date cross-record bleed.

Official 2026-10-31 readback: sid=0Q218... is Shan Cai Die Die (Oct16-Nov15),
whereas sid=0Q238... is Shell Nest (Oct13-Nov10). Prior AB sample TITLE
named Shell Nest while the previously selected URL pointed at Shan Cai.
Never attach a date/location to a different official SID, even if DOM passes.
Diagnostic only, no formal field acceptance.
"""
import hashlib
from urllib.parse import parse_qsl, urlsplit
from bs4 import BeautifulSoup
from p30_venue02z_ceramics_fields import norm
from p30_venue02ab_ceramics_role_ownership import classify_field_ownership

OBSERVED = {
    "0Q218338899799849722": "山彩疊疊-唐榕個展",
    "0Q238554544743104681": "殼之巢 — 情景之階：佐藤雅之個展",
}
CATEGORY = "0J148497613881029302"
HOLD = "HARD_HOLD_NO_PUBLICATION"

def audit_sid_title(detail_url, detail_html, expected_sid, expected_title):
    out = {"gate": "P30-VENUE-02AC", "source": "CERAMICS_P0_NEW_TAIPEI",
           "sourceRole": "OFFICIAL_VENUE", "sidBound": False,
           "detailHeadingMatches": 0, "fieldRoleDecision": None,
           "acceptedFields": 0, "goldenAccepted": 0, "published": False,
           "ticketEventId": None, "releaseState": HOLD}
    try:
        u = urlsplit(detail_url)
        qs = parse_qsl(u.query, keep_blank_values=True, strict_parsing=True)
        safe = (u.scheme == "https" and u.hostname == "www.ceramics.ntpc.gov.tw"
                and not u.username and not u.password and u.port is None
                and u.path == "/xmdoc/cont" and not u.fragment
                and len(qs) == 2 and {k for k,v in qs} == {"sid","xsmsid"}
                and len({k for k,v in qs}) == 2)
        values = dict(qs)
    except (ValueError, TypeError):
        safe = False
        values = {}
    if not safe or values.get("xsmsid") != CATEGORY or values.get("sid") != expected_sid:
        return dict(out, decision="HOLD_UNSAFE_OR_UNBOUND_DETAIL_SID")
    if expected_sid not in OBSERVED:
        return dict(out, decision="HOLD_SID_NOT_IN_BOUNDED_OFFICIAL_SAMPLE")
    if norm(expected_title) != norm(OBSERVED[expected_sid]):
        return dict(out, decision="HOLD_SOURCE_SID_TITLE_PAIR_CONFLICT")
    soup = BeautifulSoup(detail_html, "html.parser")
    headings = [norm(x.get_text(" ", strip=True)) for x in soup.find_all("h3", limit=30)]
    out["detailHeadingMatches"] = headings.count(norm(expected_title))
    out["sidBound"] = True
    out["sidSHA256"] = hashlib.sha256(expected_sid.encode()).hexdigest()
    if len(headings) != 1 or out["detailHeadingMatches"] != 1:
        return dict(out, decision="HOLD_DETAIL_TITLE_NOT_BOUND_TO_SID")
    field = classify_field_ownership(detail_html, expected_title)
    out["fieldRoleDecision"] = field["decision"]
    if not field["decision"].startswith("REVIEW_"):
        return dict(out, decision="HOLD_FIELD_ROLE_" + field["decision"])
    return dict(out, decision="REVIEW_SAME_SID_TITLE_FIELD_ROLES_NOT_ACCEPTED")
