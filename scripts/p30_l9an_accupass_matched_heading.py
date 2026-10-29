#!/usr/bin/env python3
"""P30-L9-AN: bind exact source title to ONE local ACCUPASS heading region.

Reuses frozen L9-AH normal public browser navigation and title-parity checks.
At most one list and two exact same-path details. No raw page/title persistence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
import p30_l9ah_accupass_field_roles as ah
import p30_l9am_accupass_live_heading as am
import p30_l9ai_accupass_sibling_roles as ai
import p30_l9ak_accupass_heading_near as ak

KIND = "EVENTRADAR_P30_L9AN_MATCHED_HEADING_LOCAL_REVIEW_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
MAX_HTML_BYTES = 1_500_000
MAX_TITLE_CHARS = 240

def inspect_matched_region(html, expected_title):
    base = {"assessed": False, "decision": "HOLD_INVALID_INPUT",
            "headingCount": 0, "matchedHeadingCount": 0,
            "boundedRegions": 0, "observedLocalPairs": 0, "roles": {},
            "acceptedFields": 0, "rawValuesPersisted": False}
    if not isinstance(html, str) or not isinstance(expected_title, str):
        return base
    if len(html.encode("utf-8")) > MAX_HTML_BYTES or not (3 <= len(expected_title) <= MAX_TITLE_CHARS):
        return dict(base, decision="HOLD_HTML_OR_TITLE_CAP")
    soup = BeautifulSoup(html, "html.parser")
    headings = soup.select("main h1,main h2,article h1,article h2,[role='main'] h1,[role='main'] h2,#event-detail h1,#event-detail h2")
    headings = list({id(h): h for h in headings}.values())
    if not headings or len(headings) > ak.MAX_HEADINGS:
        return dict(base, decision="HOLD_HEADING_ABSENT_OR_CAP", headingCount=len(headings))
    matches = [h for h in headings if ah.prior.normalized(h.get_text(" ", strip=True)) == expected_title]
    summary = dict(base, headingCount=len(headings), matchedHeadingCount=len(matches))
    if len(matches) != 1:
        return dict(summary, decision=("HOLD_MATCHED_HEADING_AMBIGUOUS" if matches
                                       else "HOLD_NO_EXACT_SEMANTIC_HEADING"))
    heading = matches[0]
    if ak._hidden_chain(heading):
        return dict(summary, decision="HOLD_MATCHED_HEADING_HIDDEN")
    region = None
    parent = heading.parent
    for _ in range(ak.MAX_DEPTH):
        if parent is None or not getattr(parent, "name", None):
            break
        if ak._hidden_chain(parent):
            return dict(summary, decision="HOLD_REGION_HIDDEN")
        if parent.name in ("div", "section", "article", "main"):
            count = len(parent.select("div,li,section,p"))
            if count <= ak.MAX_REGION_CONTAINERS:
                if len(parent.select("h1,h2")) != 1:
                    return dict(summary, decision="HOLD_REGION_HAS_OTHER_HEADINGS")
                region = parent
                break
        parent = parent.parent
    if region is None:
        return dict(summary, decision="HOLD_NO_UNIQUE_BOUNDED_REGION")
    summary["boundedRegions"] = 1
    if region.find(["script", "style", "form", "iframe"]):
        return dict(summary, decision="HOLD_REGION_INTERACTIVE_OR_SCRIPT")
    local = ai.inspect_local_siblings("<main>" + str(region) + "</main>")
    if not local.get("assessed"):
        return dict(summary, decision=local.get("hold", "HOLD_LOCAL_INSPECTOR"))
    counts = {role: entry["localPairCount"] for role, entry in local["roles"].items()}
    total = sum(counts.values())
    if total == 0:
        return dict(summary, decision="HOLD_NO_EXPLICIT_LOCAL_ROLE_PAIR")
    return dict(summary, assessed=True,
                decision="REVIEW_MATCHED_HEADING_LOCAL_ROLES_NOT_ACCEPTED",
                observedLocalPairs=min(total, ai.MAX_PAIRS), roles=counts)

def summarize(source):
    details = source.get("details", [])
    if not isinstance(details, list) or len(details) > 2:
        return {"decision": "HOLD_DETAIL_SCOPE", "detailCount": 0, "details": []}
    safe = []
    for item in details:
        identity = item.get("identityDecision", "")
        topo = item.get("fieldTopology") or {}
        if not isinstance(identity, str) or not identity.startswith(("REVIEW_", "HOLD_")):
            identity = "HOLD_INVALID_IDENTITY"
        decision = topo.get("decision", "HOLD_UNASSESSED")
        if not isinstance(decision, str) or not decision.startswith(("REVIEW_", "HOLD_")):
            decision = "HOLD_INVALID_TOPOLOGY"
        safe.append({"http": item.get("http") if item.get("http") in (200, None) else None,
                     "identityDecision": identity, "localDecision": decision,
                     "headingCount": topo.get("headingCount", 0),
                     "matchedHeadingCount": topo.get("matchedHeadingCount", 0),
                     "observedLocalPairs": topo.get("observedLocalPairs", 0),
                     "assessed": topo.get("assessed") is True})
    review = len(safe) == 2 and all(
        x["identityDecision"].startswith("REVIEW_") and x["assessed"] for x in safe)
    return {"decision": ("REVIEW_MATCHED_HEADING_TOPOLOGY_NOT_FIELDS" if review
                         else "HOLD_MATCHED_HEADING_OR_IDENTITY"),
            "detailCount": len(safe), "details": safe,
            "listHttp": source.get("listHttp") if source.get("listHttp") in (200, None) else None,
            "acceptedFields": 0, "goldenAccepted": 0}

def probe():
    captured = {"title": None}
    original = ah.prior.detail_heading_evidence
    def capture(html, expected_title):
        captured["title"] = expected_title
        return original(html, expected_title)
    def adapter(html):
        return inspect_matched_region(html, captured["title"])
    with patch.object(ah.prior, "detail_heading_evidence", capture):
        with patch.object(ah, "scoped_pairs", adapter):
            source = ah.probe()
    return summarize(source)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    p.add_argument("--status", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    if not args.live:
        p.error("explicit --live required")
    ah.prior.prior.validate_status(Path(args.status).read_bytes())
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-l9an-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result = probe()
    result.update(kind=KIND, releaseState=RELEASE, maxDetails=2,
                  acceptedFields=0, goldenAccepted=0, published=False,
                  rawHtmlPersisted=False, rawUrlsPersisted=False,
                  rawTitlesPersisted=False, rawEventIdsPersisted=False,
                  rawFieldValuesPersisted=False)
    out.mkdir(exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "matched_heading_review.json").write_bytes(raw)
    (out / "manifest.json").write_text(json.dumps({
        "kind": KIND, "releaseState": RELEASE,
        "filesSHA256": {"matched_heading_review.json": hashlib.sha256(raw).hexdigest()}
    }, sort_keys=True, indent=2) + "\n")
    print("L9AN_DECISION=" + result["decision"])
    print("L9AN_DETAILS=" + str(result["detailCount"]))
    print("HOLD_NO_FORMAL_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
