#!/usr/bin/env python3
"""P30-L9-AO: fail-closed ACCUPASS role-bearing ancestor beyond title wrapper."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
import p30_l9an_accupass_matched_heading as prior

KIND = "EVENTRADAR_P30_L9AO_ROLE_BEARING_ANCESTOR_REVIEW_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
ORIGINAL_INSPECT = prior.inspect_matched_region

def inspect_role_ancestor(html, expected_title):
    first = ORIGINAL_INSPECT(html, expected_title)
    if first["decision"] != "HOLD_NO_EXPLICIT_LOCAL_ROLE_PAIR":
        return first
    if not isinstance(html, str) or not isinstance(expected_title, str):
        return first
    soup = BeautifulSoup(html, "html.parser")
    heads = soup.select("main h1,main h2,article h1,article h2,[role='main'] h1,[role='main'] h2,#event-detail h1,#event-detail h2")
    heads = list({id(h): h for h in heads}.values())
    matches = [h for h in heads if prior.ah.prior.normalized(h.get_text(" ", strip=True)) == expected_title]
    if len(matches) != 1 or prior.ak._hidden_chain(matches[0]):
        return first
    node = matches[0].parent
    candidates = []
    for _ in range(prior.ak.MAX_DEPTH):
        if node is None or not getattr(node, "name", None):
            break
        node = node.parent
        if node is None or not getattr(node, "name", None):
            break
        if node.name not in ("div", "section", "article", "main"):
            continue
        if prior.ak._hidden_chain(node):
            return dict(first, decision="HOLD_ANCESTOR_HIDDEN")
        if len(node.select("div,li,section,p")) > prior.ak.MAX_REGION_CONTAINERS:
            break
        if len(node.select("h1,h2")) != 1:
            break
        if node.find(["script", "style", "form", "iframe"]):
            break
        local = prior.ai.inspect_local_siblings("<main>" + str(node) + "</main>")
        if not local.get("assessed"):
            continue
        counts = {role: entry["localPairCount"] for role, entry in local["roles"].items()
                  if entry["localPairCount"] > 0}
        if not counts:
            continue
        if any(local["roles"][role]["decision"].startswith("HOLD_") for role in counts):
            return dict(first, decision="HOLD_ANCESTOR_ROLE_CONFLICT")
        candidates.append(counts)
    if not candidates:
        return first
    signatures = {tuple(sorted(x.items())) for x in candidates}
    if len(signatures) != 1:
        return dict(first, decision="HOLD_ANCESTOR_SCOPE_CONFLICT")
    counts = candidates[0]
    return dict(first, assessed=True, boundedRegions=1,
                decision="REVIEW_UNIQUE_ROLE_BEARING_ANCESTOR_NOT_ACCEPTED",
                observedLocalPairs=min(sum(counts.values()), prior.ai.MAX_PAIRS),
                roles=counts, regionSelection="nearest_role_bearing_ancestor",
                acceptedFields=0, rawValuesPersisted=False)

def probe():
    with patch.object(prior, "inspect_matched_region", inspect_role_ancestor):
        result = prior.probe()
    result["kind"] = KIND
    result["releaseState"] = RELEASE
    result["acceptedFields"] = result["goldenAccepted"] = 0
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    p.add_argument("--status", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    if not args.live:
        p.error("explicit --live required")
    prior.ah.prior.prior.validate_status(Path(args.status).read_bytes())
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-l9ao-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result = probe()
    result.update(kind=KIND, releaseState=RELEASE, acceptedFields=0,
                  goldenAccepted=0, published=False, rawHtmlPersisted=False,
                  rawUrlsPersisted=False, rawTitlesPersisted=False,
                  rawEventIdsPersisted=False, rawFieldValuesPersisted=False)
    out.mkdir(exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "ancestor_role_review.json").write_bytes(raw)
    (out / "manifest.json").write_text(json.dumps({
        "kind": KIND, "releaseState": RELEASE,
        "filesSHA256": {"ancestor_role_review.json": hashlib.sha256(raw).hexdigest()}
    }, sort_keys=True, indent=2) + "\n")
    print("L9AO_DECISION=" + result["decision"])
    print("L9AO_DETAILS=" + str(result["detailCount"]))
    for index, detail in enumerate(result["details"]):
        print("L9AO_DETAIL_%d=%s" % (index + 1, detail["localDecision"]))
    print("HOLD_NO_FORMAL_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
