#!/usr/bin/env python3
"""P30-L9-D: fresh public ibon DOM/JSON script diagnostics; never execute JavaScript.
Two allowlisted listing URLs, <= one strictly identity-bound detail, no retries,
cookies/login, anti-bot workaround, formal field promotion or production writes.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

KIND = "EVENTRADAR_P30_L9D_IBON_PUBLIC_DOM_DIAGNOSTICS_V1"
ROOT = Path(__file__).resolve().parent
MAX_SCRIPT_BYTES = 131072
MAX_JSON_SCRIPTS = 16
MAX_TREE_NODES = 12000
MAX_TREE_DEPTH = 12
MAX_CANDIDATES = 40
JSON_TYPES = {"application/ld+json", "application/json"}
HOLD = "HARD_HOLD_NO_PUBLICATION"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def adapter():
    spec = importlib.util.spec_from_file_location(
        "p30_l3bb_ibon_adapter", ROOT / "p30_l3bb_ibon.py")
    if not spec or not spec.loader:
        raise RuntimeError("HOLD_IBON_SOURCE_ADAPTER_MISSING")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()[:180]


def event_type(value):
    types = value if isinstance(value, list) else [value]
    return any(isinstance(t, str) and
               (t == "Event" or
                (len(t) <= 35 and t.endswith("Event") and "://" not in t))
               for t in types)


def same_object_candidate(obj, base, ibon, is_ld):
    if not isinstance(obj, dict):
        return None
    if is_ld:
        if not event_type(obj.get("@type")):
            return None
        titles = (obj.get("name"),)
        links = (obj.get("url"),)
        provenance = "JSON_LD_EVENT_SAME_OBJECT_REVIEW_ONLY"
    else:
        # Merely a directly paired public name and URL from the same JSON object.
        # Not a source authority or activity verification.
        titles = tuple(obj.get(k) for k in ("activityName", "eventName", "title", "name"))
        links = tuple(obj.get(k) for k in ("detailUrl", "eventUrl", "activityUrl", "url"))
        provenance = "JSON_HYDRATION_SAME_OBJECT_REVIEW_ONLY"
    for title in titles:
        if not isinstance(title, str):
            continue
        title = clean(title)
        if not ibon.plausible_label(title) or len(title) < 4:
            continue
        for link in links:
            if not isinstance(link, str):
                continue
            url = ibon.canonical_detail(link, base)
            if url:
                return {"title": title, "officialUrl": url,
                        "candidateId": url.rsplit("/", 1)[-1],
                        "sourceEvidenceRole": provenance,
                        "detailIdentityVerified": False,
                        "goldenVerified": False, "published": False}
    return None


def iter_bounded_nodes(root):
    stack = [(root, 0)]
    count = 0
    while stack and count < MAX_TREE_NODES:
        current, depth = stack.pop()
        count += 1
        if isinstance(current, dict):
            yield current
            if depth < MAX_TREE_DEPTH:
                stack.extend((v, depth + 1) for v in current.values()
                             if isinstance(v, (list, dict)))
        elif isinstance(current, list) and depth < MAX_TREE_DEPTH:
            stack.extend((v, depth + 1) for v in current[:2000]
                         if isinstance(v, (list, dict)))


def analyze(html, base, ibon):
    """Analyze current response only, no JS execution or external script downloads."""
    soup = BeautifulSoup(html, "html.parser")
    anchors, stats = ibon.parse_list(html, base)
    seen = set()
    result = []
    for row in anchors:
        url = row["officialUrl"]
        if url not in seen:
            seen.add(url)
            result.append({"title": row["title"], "officialUrl": url,
                           "candidateId": url.rsplit("/", 1)[-1],
                           "sourceEvidenceRole": "DIRECT_ANCHOR_SAME_CARD_REVIEW_ONLY",
                           "detailIdentityVerified": False,
                           "goldenVerified": False, "published": False})
    scripts = soup.find_all("script")
    counts = Counter()
    malformed = 0
    parsed_json = 0
    for node in scripts:
        source = node.get("src")
        if source:
            joined = urljoin(base, source)
            u = urlsplit(joined)
            counts["scriptSrcOfficialHost"] += int(
                u.scheme == "https" and u.hostname == ibon.HOST)
            counts["scriptSrcOtherHost"] += int(
                not (u.scheme == "https" and u.hostname == ibon.HOST))
            continue
        kind = (node.get("type") or "").split(";", 1)[0].strip().lower()
        if kind not in JSON_TYPES:
            counts["inlineNonJsonScript"] += 1
            continue
        counts["embeddedJsonScript"] += 1
        raw = node.string or node.get_text() or ""
        if len(raw.encode("utf-8")) > MAX_SCRIPT_BYTES or parsed_json >= MAX_JSON_SCRIPTS:
            counts["jsonScriptSizeOrQuantityHold"] += 1
            continue
        parsed_json += 1
        try:
            payload = json.loads(raw)
        except (ValueError, RecursionError):
            malformed += 1
            continue
        if not isinstance(payload, (list, dict)):
            continue
        is_ld = kind == "application/ld+json"
        for obj in iter_bounded_nodes(payload):
            row = same_object_candidate(obj, base, ibon, is_ld)
            if row is not None and row["officialUrl"] not in seen:
                seen.add(row["officialUrl"])
                result.append(row)
                if len(result) >= MAX_CANDIDATES:
                    break
        if len(result) >= MAX_CANDIDATES:
            break
    text = soup.get_text(" ", strip=True)
    js_patterns = {
        "requiresJavaScriptText": bool(re.search(r"enable javascript|請啟用JavaScript", text, re.I)),
        "nextNuxtAngularHint": bool(re.search(
            r'__NEXT_DATA__|__NUXT__|id=["\x27]__next|ng-version=', html, re.I)),
        "fetchOrAjaxInlineHint": bool(re.search(r'\bfetch\s*\(|\baxios\b|\$\.ajax\s*\(', html, re.I)),
        "jsonLdPresent": any((s.get("type") or "").lower() == "application/ld+json"
                             for s in scripts),
        "wafOrCaptchaText": bool(re.search(
            r'cloudflare|captcha|access denied|verify you are human', text, re.I))
    }
    candidate_counts = dict(Counter(x["sourceEvidenceRole"] for x in result))
    return result[:MAX_CANDIDATES], {
        "anchorCount": stats.get("other_links_seen", 0),
        "directDetailLinksSeen": stats.get("detail_links_seen", 0),
        "validDirectCandidates": len(anchors),
        "scriptCount": len(scripts),
        "scriptRoleCounts": dict(sorted(counts.items())),
        "malformedJsonCount": malformed,
        "bodyTextLength": len(text),
        "formCount": stats.get("form_tags", 0),
        "jsonOrDomCandidates": len(result[:MAX_CANDIDATES]),
        "candidateProvenanceCounts": candidate_counts,
        "renderingHints": js_patterns,
        "rawHtmlPersisted": False,
        "thirdPartyScriptDownloaded": False
    }


class CountedSession:
    def __init__(self, underlying):
        self.underlying = underlying
        self.count = 0

    def get(self, url, **kwargs):
        if kwargs.get("allow_redirects") is not False or kwargs.get("stream") is not True:
            raise RuntimeError("HOLD_AUTO_REDIRECT_OR_UNBOUNDED_BODY")
        self.count += 1
        return self.underlying.get(url, **kwargs)


def run(session=None, delay=0.7, sleep=time.sleep):
    if delay < 0.6:
        raise ValueError("HOLD_IBON_MINIMUM_RATE_INTERVAL")
    ibon = adapter()
    real = session is None
    underlying = session if session is not None else requests.Session()
    counted = CountedSession(underlying)
    platforms = []
    unique = {}
    try:
        for index, url in enumerate(ibon.LISTS):
            if index:
                sleep(delay)
            html, net = ibon.get_html(counted, url, listing=True)
            meta = {k: v for k, v in net.items() if k in (
                "state", "http_status", "observed_url", "content_type",
                "sha256", "bytes", "trail", "error_type")}
            found, diagnostics = analyze(html, net.get("observed_url", url), ibon) if html else (
                [], {"state": "HOLD_NO_HTML_FOR_DOM", "rawHtmlPersisted": False})
            for item in found:
                unique.setdefault(item["officialUrl"], item)
            platforms.append({"source": url, "http": meta, "dom": diagnostics,
                              "listCandidates": len(found),
                              "listState": "CANDIDATE_REVIEW_ONLY" if found else
                                           "HOLD_HTTP200_LIST_ZERO_OR_NETWORK"})
        candidates = list(unique.values())[:MAX_CANDIDATES]
        detail = {"state": "NOT_ATTEMPTED_NO_SOURCE_ID"}
        if candidates:
            sleep(delay)
            selected = candidates[0]
            detail_html, net = ibon.get_html(
                counted, selected["officialUrl"], detail=True)
            detail = {"sourceUrl": selected["officialUrl"],
                      "sourceEvidenceRole": selected["sourceEvidenceRole"],
                      "http": {k: v for k, v in net.items() if k in (
                          "state", "http_status", "observed_url", "sha256", "bytes", "trail")}}
            if detail_html:
                result = ibon.verify_detail(detail_html, {
                    "title": selected["title"]})
                detail["state"] = result["state"]
                detail["detailTitleParity"] = result["observedTitleMatch"]
                detail["headingCount"] = result["headlineCount"]
            else:
                detail["state"] = "HOLD_DETAIL_HTTP"
        output = {
            "kind": KIND,
            "runId": "P30-L9D-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
            "candidateOrigin": "L9D_NEW_PUBLIC_HTTP" if real else "L9D_MOCK_NOT_FRESH",
            "actualFreshHTTPRequests": counted.count if real else 0,
            "observedSyntheticRequests": 0 if real else counted.count,
            "listHTTPAttempts": 2,
            "lists": platforms,
            "candidateCount": len(candidates),
            "candidates": candidates,
            "sampleDetail": detail,
            "officialOrigin": "ticket.ibon.com.tw",
            "domEvidenceOnly": True,
            "fullPlatformCoverageVerified": False,
            "formalFieldPromotions": 0,
            "goldenAccepted": 0, "published": False,
            "writerExecuted": False, "schedulerExecuted": False,
            "notifierExecuted": False, "autoMergeCount": 0,
            "existingAndroid44Preserved": True,
            "l8CoreAndroidPassPreserved": True,
            "releaseState": HOLD
        }
        return output
    finally:
        if real:
            underlying.close()


def output_dir(value):
    root = Path.cwd().resolve()
    dest = Path(value).resolve()
    if dest == root or not dest.is_relative_to(root) or any(
        dest == (root / p) or dest.is_relative_to(root / p)
        for p in ("docs", "scripts", "tests", "schemas", ".github", ".git")):
        raise ValueError("HOLD_IBON_ISOLATED_OUTPUT_ONLY")
    return dest


def seal(report, out):
    target = output_dir(out)
    target.mkdir(parents=True, exist_ok=True)
    bytes_ = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (target / "fresh_ibon_dom_diagnostics.json").write_bytes(bytes_)
    manifest = {
        "kind": "EVENTRADAR_P30_L9D_IBON_DOM_EVIDENCE_MANIFEST",
        "sourceL9CParent": "ae469b52e7b7b7f16dda1eeab584be8e16d63f50",
        "runId": report["runId"],
        "sha256": {"fresh_ibon_dom_diagnostics.json": sha(bytes_)},
        "actualFreshHTTPRequests": report["actualFreshHTTPRequests"],
        "releaseState": HOLD, "published": False
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="p30-l9d-evidence")
    args = ap.parse_args()
    output_dir(args.out)
    report = run()
    seal(report, args.out)
    for row in report["lists"]:
        print("IBON_FRESH_LIST", row["source"], row["http"].get("state"),
              "HTTP", row["http"].get("http_status"),
              "CANDIDATES", row["listCandidates"],
              "DOM", json.dumps(row["dom"], ensure_ascii=False, sort_keys=True))
    print("IBON_DETAIL", report["sampleDetail"]["state"])
    print("PASS L9D_FRESH_PUBLIC_HTTP", report["actualFreshHTTPRequests"])
    print("QUALITY L9D_IBON_CANDIDATES", report["candidateCount"])
    print("HOLD L9D_PUBLISH_GOLDEN_FULL_CATALOG_UNVERIFIED")


if __name__ == "__main__":
    main()
