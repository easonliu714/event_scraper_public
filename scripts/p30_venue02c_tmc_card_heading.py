#!/usr/bin/env python3
"""P30-VENUE-02C: source-bound TMC card-heading title, never card-wide text."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
import p30_venue02b_tmc_title_identity as prior

KIND = "EVENTRADAR_P30_VENUE02C_CARD_HEADING_REVIEW_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
MAX_ANCHORS = 500

def hidden(node, stop):
    cur = node
    while cur is not None:
        if cur.has_attr("hidden") or str(cur.get("aria-hidden", "")).lower() == "true":
            return True
        style = str(cur.get("style", "")).replace(" ", "").lower()
        if "display:none" in style or "visibility:hidden" in style:
            return True
        if cur is stop:
            break
        cur = cur.parent
    return False

def candidate_card_heading(body, status, final_url, redirected):
    listing = prior.prior.assess_list(body, status, final_url, redirected)
    target = listing.pop("detailUrl", None)
    if not listing["decision"].startswith("REVIEW_") or not target:
        return listing, None, None
    try:
        soup = BeautifulSoup(body.decode("utf-8-sig"), "html.parser")
    except (UnicodeError, ValueError, AttributeError):
        return dict(listing, decision="HOLD_CARD_HTML_PARSE"), None, None
    anchors = soup.select("a[href]")
    if len(anchors) > MAX_ANCHORS:
        return dict(listing, decision="HOLD_CARD_ANCHOR_CAP"), None, None
    titles = set()
    matched_cards = 0
    for anchor in anchors:
        href = anchor.get("href")
        if not isinstance(href, str):
            continue
        url = prior.prior.urllib.parse.urljoin(prior.prior.LIST_URL, href)
        if url != target or not prior.prior.safe_detail(url):
            continue
        matched_cards += 1
        if hidden(anchor, anchor):
            return dict(listing, decision="HOLD_CARD_HIDDEN"), None, None
        headings = anchor.select("h2,h3,h4")
        if len(headings) != 1 or hidden(headings[0], anchor):
            return dict(listing, decision="HOLD_CARD_HEADING_ABSENT_OR_AMBIGUOUS"), None, None
        if headings[0].select("[hidden],[aria-hidden='true'],script,style,template"):
            return dict(listing, decision="HOLD_CARD_HEADING_HIDDEN_CONTENT"), None, None
        title = prior.normalize(headings[0].get_text(" ", strip=True))
        if not (3 <= len(title) <= prior.MAX_TITLE) or title.casefold() in prior.GENERIC:
            return dict(listing, decision="HOLD_CARD_TITLE_GENERIC_OR_CAP"), None, None
        titles.add(title)
    if not matched_cards or len(titles) != 1:
        return dict(listing, decision="HOLD_CARD_TITLE_CONFLICT_OR_ABSENT"), None, None
    return dict(listing, decision="REVIEW_CARD_HEADING_ONLY_NOT_FORMAL_IDENTITY",
                matchedCards=min(matched_cards, MAX_ANCHORS)), target, next(iter(titles))

def probe():
    with patch.object(prior, "candidate_title", candidate_card_heading):
        result = prior.probe()
    result["kind"] = KIND
    result["titleSource"] = "ONE_VISIBLE_H2_H3_H4_WITHIN_SAME_OFFICIAL_CARD"
    result["acceptedFields"] = result["goldenAccepted"] = 0
    result["releaseState"] = RELEASE
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.live:
        parser.error("explicit --live required")
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-venue02c-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result = probe()
    out.mkdir(exist_ok=True)
    raw = (json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()
    (out / "card_heading_review.json").write_bytes(raw)
    (out / "manifest.json").write_text(json.dumps({
        "kind": KIND, "releaseState": RELEASE,
        "filesSHA256": {"card_heading_review.json": hashlib.sha256(raw).hexdigest()}
    }, sort_keys=True, indent=2) + "\n")
    print("VENUE02C_DECISION=" + result["decision"])
    print("VENUE02C_LIST_DECISION=" + result["list"]["decision"])
    print("VENUE02C_DETAIL_DECISION=" + result["detail"]["decision"])
    print("HOLD_NO_FORMAL_FIELD_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
