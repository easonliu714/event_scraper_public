#!/usr/bin/env python3
"""P30-VENUE-02D: exact TMC title-bound field roles, no value acceptance/publish."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
import p30_venue02c_tmc_card_heading as prior

KIND = "EVENTRADAR_P30_VENUE02D_FIELD_PROVENANCE_REVIEW_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
LABELS = {
    "EVENT": {"活動日期", "演出日期", "演出時間", "活動時間"},
    "SALE": {"售票時間", "開賣時間", "售票期間"},
    "ADMISSION": {"入場時間", "開放入場時間"},
    "REGISTRATION": {"報名期間", "報名時間"},
    "VOUCHER": {"兌換期間", "兌換時間"},
    "VENUE": {"活動地點", "演出地點", "活動場地"},
    "PRICE": {"票價", "票券價格"},
    "SESSION": {"場次", "演出場次"},
}
MAX_HTML = 800_000
MAX_CONTAINERS = 300
MAX_PAIRS = 80

def inspect(html, title):
    base = {"decision": "HOLD_FIELD_INPUT", "assessed": False,
            "pairCount": 0, "roles": {}, "acceptedFields": 0}
    if not isinstance(html, bytes) or len(html) > MAX_HTML or not isinstance(title, str):
        return base
    try:
        soup = BeautifulSoup(html.decode("utf-8-sig"), "html.parser")
    except (UnicodeError, ValueError):
        return dict(base, decision="HOLD_FIELD_ENCODING")
    heads = soup.select("main h1,main h2,article h1,article h2,[role='main'] h1,[role='main'] h2")
    heads = list({id(h): h for h in heads}.values())
    matches = [h for h in heads if prior.prior.normalize(h.get_text(" ", strip=True)) == title
               and not prior.hidden(h, h)]
    if len(matches) != 1:
        return dict(base, decision="HOLD_FIELD_EXACT_HEADING_NOT_UNIQUE")
    region = None
    node = matches[0]
    for _ in range(8):
        node = node.parent
        if node is None or not getattr(node, "name", None):
            break
        if node.name not in ("div", "section", "article", "main"):
            continue
        if prior.hidden(node, node):
            return dict(base, decision="HOLD_FIELD_HIDDEN_REGION")
        if len(node.select("div,section,li,p")) > MAX_CONTAINERS:
            break
        if len(node.select("h1,h2")) != 1:
            continue
        if node.find(["script", "form", "iframe", "template"]):
            continue
        region = node
        break
    if region is None:
        return dict(base, decision="HOLD_FIELD_NO_BOUNDED_TITLE_REGION")
    pairs = []
    for dt in region.select("dt"):
        dd = dt.find_next_sibling("dd")
        if dd is not None:
            pairs.append((dt, dd))
    for tr in region.select("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if len(cells) == 2 and cells[0].name == "th" and cells[1].name == "td":
            pairs.append(tuple(cells))
    if len(pairs) > MAX_PAIRS:
        return dict(base, decision="HOLD_FIELD_PAIR_CAP")
    found = {key: set() for key in LABELS}
    for keynode, valnode in pairs:
        if prior.hidden(keynode, region) or prior.hidden(valnode, region):
            return dict(base, decision="HOLD_FIELD_HIDDEN_PAIR")
        label = "".join(keynode.get_text(" ", strip=True).strip("：:").split())
        roles = [role for role, names in LABELS.items() if label in names]
        if len(roles) != 1:
            continue
        value = " ".join(valnode.get_text(" ", strip=True).split())
        if 0 < len(value) <= 240:
            found[roles[0]].add(value)
    role_counts = {role: len(values) for role, values in found.items()}
    decision = ("HOLD_FIELD_CONFLICTING_VALUES" if any(n > 1 for n in role_counts.values())
                else "REVIEW_EXPLICIT_TITLE_LOCAL_ROLE_NOT_ACCEPTED" if any(role_counts.values())
                else "HOLD_NO_EXPLICIT_TITLE_LOCAL_ROLE_PAIR")
    return dict(base, decision=decision, assessed=True,
                pairCount=len(pairs), roles=role_counts)

def probe():
    captured = {"title": None, "detail": None}
    original_title = prior.candidate_card_heading
    original_get = prior.prior.prior.get_once
    def capture_title(*args):
        result = original_title(*args)
        captured["title"] = result[2]
        return result
    def capture_get(url):
        result = original_get(url)
        if (prior.prior.prior.safe_detail(url) and result[1] == 200
                and result[2] == url and not result[3]):
            captured["detail"] = result[0]
        return result
    with patch.object(prior, "candidate_card_heading", capture_title):
        with patch.object(prior.prior.prior, "get_once", capture_get):
            result = prior.probe()
    review = {"decision": "HOLD_IDENTITY_NOT_REVIEWED", "assessed": False,
              "pairCount": 0, "roles": {}, "acceptedFields": 0}
    if result["decision"].startswith("REVIEW_") and captured["detail"] and captured["title"]:
        review = inspect(captured["detail"], captured["title"])
    result["kind"] = KIND
    result["fieldTopology"] = {
        "decision": review["decision"], "assessed": review["assessed"],
        "pairCount": review["pairCount"],
        "roleEvidence": [
            {"source": "TAIPEI_MUSIC_CENTER_OFFICIAL",
             "observed_at": result["observedAt"], "role": role,
             "decision": ("REVIEW_EXPLICIT_PAIR_NOT_ACCEPTED" if n == 1
                          else "HOLD_CONFLICTING_VALUES" if n > 1
                          else "UNKNOWN_NO_EXPLICIT_PAIR"), "distinctValueCount": n}
            for role, n in review["roles"].items()
        ]
    }
    result.update(releaseState=RELEASE, acceptedFields=0, goldenAccepted=0,
                  published=False, ticketEventId=None,
                  rawHtmlPersisted=False, rawUrlsPersisted=False,
                  rawTitlesPersisted=False, rawFieldValuesPersisted=False)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.live:
        parser.error("explicit --live required")
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-venue02d-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result = probe()
    out.mkdir(exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "field_review.json").write_bytes(raw)
    (out / "manifest.json").write_text(json.dumps({
        "kind": KIND, "releaseState": RELEASE,
        "filesSHA256": {"field_review.json": hashlib.sha256(raw).hexdigest()}
    }, sort_keys=True, indent=2) + "\n")
    print("VENUE02D_IDENTITY=" + result["decision"])
    print("VENUE02D_FIELDS=" + result["fieldTopology"]["decision"])
    print("HOLD_NO_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
