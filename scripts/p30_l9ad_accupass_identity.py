#!/usr/bin/env python3
"""P30-L9-AD: one bounded public ACCUPASS list/detail identity review; NO PUBLISH."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

KIND = "EVENTRADAR_P30_L9AD_ACCUPASS_IDENTITY_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
STATUS_BLOB = "e19ca37c4c80c10b7278d0813b8ff1047535d124"
SOURCE_MAIN = "fbf4ca02b91159f2423caf3d79fb0ca4bb747069"
PARENT_HEAD = "3b6b64ff4803a1a156e5774a23850f756d31e799"
ENTRY = "https://www.accupass.com/search?q=%E9%9F%B3%E6%A8%82"
MAX_HTML = 1_500_000
MAX_LINKS = 300
MAX_CANDIDATES = 30
MAX_HEADINGS = 40
MAX_TITLE = 240
OBSERVATIONS = 4
ID_RE = re.compile(r"^/event/([A-Za-z0-9_-]{8,64})/?$", re.I)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def allowed(url):
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and p.hostname in ("www.accupass.com", "accupass.com")
                and not p.username and not p.password and p.port in (None, 443)
                and not any(ord(c) < 33 for c in url) and not p.fragment)
    except ValueError:
        return False

def event_id(url):
    if not allowed(url):
        return None
    p = urlsplit(url)
    m = ID_RE.fullmatch(p.path)
    return m.group(1).lower() if m and not p.query else None

def clean(value):
    return " ".join(str(value).split()).strip()

def title_equal(a, b):
    import unicodedata
    x, y = (unicodedata.normalize("NFC", clean(s)) for s in (a, b))
    return len(x) >= 4 and len(x) <= MAX_TITLE and x == y

def list_candidates(html):
    if len(html.encode("utf-8")) > MAX_HTML:
        return [], "HOLD_LIST_HTML_CAP", 0
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select("a[href]")
    if len(anchors) > MAX_LINKS:
        return [], "HOLD_LIST_ANCHOR_CAP", len(anchors)
    found, seen = [], set()
    for a in anchors:
        from urllib.parse import urljoin
        url = urljoin(ENTRY, a.get("href", ""))
        key = event_id(url)
        if not key or key in seen:
            continue
        # The title must belong to the same event anchor, not a global document text.
        node = a.find(["h2", "h3", "h4"]) or a
        label = clean(node.get_text(" ", strip=True))
        if not (4 <= len(label) <= MAX_TITLE):
            continue
        seen.add(key)
        found.append((key, label, url))
        if len(found) > MAX_CANDIDATES:
            return [], "HOLD_LIST_CANDIDATE_CAP", len(anchors)
    return found, "REVIEW_LIST_CANDIDATES_ONLY", len(anchors)

def detail_snapshot(html, expected):
    if len(html.encode("utf-8")) > MAX_HTML:
        return dict(headingCount=None, exactHeadings=None, metadataExact=None, hold="HTML_CAP")
    soup = BeautifulSoup(html, "html.parser")
    headings = soup.select("h1,h2")
    if len(headings) > MAX_HEADINGS:
        return dict(headingCount=None, exactHeadings=None, metadataExact=None, hold="HEADING_CAP")
    hits = sum(title_equal(h.get_text(" ", strip=True), expected) for h in headings)
    og = soup.select_one('meta[property="og:title"]')
    meta = bool(og and title_equal(og.get("content", ""), expected))
    return dict(headingCount=len(headings), exactHeadings=hits, metadataExact=meta, hold=None)

def classify(sample):
    if sample.get("error"):
        return "HOLD_DETAIL_" + sample["error"]
    if sample.get("http") != 200 or not sample.get("sameId") or not sample.get("allowed"):
        return "HOLD_DETAIL_HTTP_OR_ID"
    frames = sample.get("observations", [])
    if len(frames) != OBSERVATIONS:
        return "HOLD_INCOMPLETE_OBSERVATIONS"
    if any(f["hold"] for f in frames[-2:]):
        return "HOLD_DETAIL_UNASSESSED"
    if all(f["exactHeadings"] > 0 for f in frames[-2:]):
        return "REVIEW_STABLE_HEADING_EXACT_NOT_GOLDEN"
    if any(f["exactHeadings"] > 0 for f in frames[-2:]):
        return "HOLD_TRANSIENT_HEADING"
    if any(f["metadataExact"] for f in frames[-2:]):
        return "HOLD_METADATA_ONLY_NOT_IDENTITY"
    return "HOLD_NO_SOURCE_BOUND_HEADING"

def validate_status(raw):
    if git_blob(raw) != STATUS_BLOB:
        raise ValueError("HOLD_STATUS_BLOB")
    s = json.loads(raw)
    if s["production"]["eventFeedReleaseState"] != RELEASE or s["production"]["goldenAccepted"] != 0:
        raise ValueError("HOLD_PRODUCTION")
    row = next((x for x in s["platforms"] if x["platform"] == "ACCUPASS"), None)
    if not row or row["baseline"]["listCandidates"] != 25 or row["baseline"]["detailTitleMatches"] != 0:
        raise ValueError("HOLD_BASELINE")
    return True

def probe():
    result = dict(listHttp=None, listAllowed=False, listAnchors=0, listCandidates=0,
                  listState="HOLD_NOT_STARTED", detail=None, navigationCount=0,
                  sourceError=None)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=False, service_workers="block")
        def guard(route):
            if route.request.is_navigation_request() and not allowed(route.request.url):
                route.abort("blockedbyclient")
            else:
                route.continue_()
        page = context.new_page()
        page.route("**/*", guard)
        candidates = []
        try:
            result["navigationCount"] += 1
            response = page.goto(ENTRY, wait_until="domcontentloaded", timeout=18000)
            result["listHttp"] = response.status if response else None
            result["listAllowed"] = allowed(page.url)
            if result["listHttp"] == 200 and result["listAllowed"]:
                page.wait_for_timeout(1500)
                candidates, state, count = list_candidates(page.content())
                result.update(listState=state, listAnchors=count, listCandidates=len(candidates))
        except Exception as exc:
            result["sourceError"] = type(exc).__name__
        finally:
            page.close()
        if candidates:
            key, title, url = candidates[0]
            detail = dict(http=None, allowed=False, sameId=False, observations=[], error=None)
            page = context.new_page()
            page.route("**/*", guard)
            try:
                result["navigationCount"] += 1
                response = page.goto(url, wait_until="domcontentloaded", timeout=18000)
                detail["http"] = response.status if response else None
                detail["allowed"] = allowed(page.url)
                detail["sameId"] = event_id(page.url) == key
                if detail["http"] == 200 and detail["allowed"] and detail["sameId"]:
                    for n in range(OBSERVATIONS):
                        if n:
                            page.wait_for_timeout(650)
                        detail["observations"].append(detail_snapshot(page.content(), title))
            except Exception as exc:
                detail["error"] = type(exc).__name__
            finally:
                page.close()
            detail["decision"] = classify(detail)
            result["detail"] = detail
        context.close()
        browser.close()
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--live-accupass", action="store_true")
    args = ap.parse_args()
    if not args.live_accupass:
        raise ValueError("HOLD_EXPLICIT_LIVE_SCOPE")
    validate_status(Path(args.status).read_bytes())
    out = Path(args.out).resolve()
    if out != (Path.cwd() / "p30-l9ad-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result = probe()
    result.update(kind=KIND, parentHead=PARENT_HEAD, formalStatusBlob=STATUS_BLOB,
                  sourceMain=SOURCE_MAIN, releaseState=RELEASE,
                  decision="HOLD_ACCUPASS_IDENTITY_REVIEW_ONLY",
                  formalVerifiedEventIdentity=0, acceptedFields=0, goldenAccepted=0,
                  published=False, productionModified=False, writerExecuted=False,
                  schedulerExecuted=False, notifierExecuted=False, mergeExecuted=False,
                  rawHtmlPersisted=False, rawUrlsPersisted=False, rawTitlesPersisted=False,
                  rawEventIdsPersisted=False, cookiesPersisted=False, screenshotsPersisted=False)
    out.mkdir(exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    (out / "accupass_identity.json").write_bytes(raw)
    manifest = dict(kind="EVENTRADAR_P30_L9AD_SHA_MANIFEST_V1",
                    filesSHA256={"accupass_identity.json": digest(raw)},
                    releaseState=RELEASE, published=False)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("L9AD_ACCUPASS", json.dumps(dict(http=result["listHttp"],
          listCandidates=result["listCandidates"],
          detail=(result["detail"] or {}).get("decision"), decision=result["decision"])))
    print("HOLD_L9AD_NO_IDENTITY_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
