#!/usr/bin/env python3
"""P30-L9-AE: one public ACCUPASS navigation, same-response HTML/DOM list topology; NO PUBLISH."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

KIND = "EVENTRADAR_P30_L9AE_ACCUPASS_LIST_TOPOLOGY_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "7c0668443df2d540ca00e773b4028e7b93434e45"
SOURCE_MAIN = "fbf4ca02b91159f2423caf3d79fb0ca4bb747069"
STATUS_BLOB = "e19ca37c4c80c10b7278d0813b8ff1047535d124"
ENTRY = "https://www.accupass.com/search?q=%E9%9F%B3%E6%A8%82"
MAX_HTML_BYTES = 1_500_000
MAX_ANCHORS = 400
MAX_TITLE = 240
OBSERVATIONS = 4
ID_RE = re.compile(r"^/event/([A-Za-z0-9_-]{8,64})/?$", re.I)

def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def allowed(url):
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and p.hostname in ("accupass.com", "www.accupass.com")
                and p.username is None and p.password is None and p.port in (None, 443)
                and not p.fragment and not any(ord(c) < 33 for c in url))
    except ValueError:
        return False

def text_of(node):
    return " ".join(node.get_text(" ", strip=True).split())

def inspect(html):
    """Aggregate only; never return title, URL, event ID, HTML, or any personal data."""
    size = len(html.encode("utf-8"))
    if size > MAX_HTML_BYTES:
        return dict(assessed=False, hold="HTML_CAP", bytesBand="OVER_CAP")
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select("a[href]")
    if len(anchors) > MAX_ANCHORS:
        return dict(assessed=False, hold="ANCHOR_CAP", anchorCount=len(anchors))
    metrics = dict(assessed=True, hold=None, anchorCount=len(anchors), eventPathAnchors=0,
                   strictEventIdAnchors=0, uniqueStrictIds=0, strictWithLocalTitle=0,
                   strictMissingLocalTitle=0, eventPathNonStrict=0, eventQueryAnchors=0,
                   externalEventLinks=0, headingAnchors=0, nonEventAnchors=0,
                   duplicateStrictAnchors=0, cardTitleHints=0)
    seen = set()
    for a in anchors:
        href = a.get("href") or ""
        try:
            url = urljoin(ENTRY, href)
            p = urlsplit(url)
        except ValueError:
            metrics["nonEventAnchors"] += 1
            continue
        if not p.path.lower().startswith("/event/"):
            metrics["nonEventAnchors"] += 1
            continue
        if not allowed(url):
            metrics["externalEventLinks"] += 1
            continue
        metrics["eventPathAnchors"] += 1
        if p.query:
            metrics["eventQueryAnchors"] += 1
        m = ID_RE.fullmatch(p.path) if not p.query else None
        if not m:
            metrics["eventPathNonStrict"] += 1
            continue
        metrics["strictEventIdAnchors"] += 1
        key = m.group(1).lower()
        if key in seen:
            metrics["duplicateStrictAnchors"] += 1
            continue
        seen.add(key)
        label_node = a.find(["h2", "h3", "h4"]) or a
        title = text_of(label_node)
        if a.find(["h2", "h3", "h4"]):
            metrics["headingAnchors"] += 1
        if 4 <= len(title) <= MAX_TITLE:
            metrics["strictWithLocalTitle"] += 1
        else:
            metrics["strictMissingLocalTitle"] += 1
    metrics["uniqueStrictIds"] = len(seen)
    # Local card/heading hints are diagnostic counts, never a substitute for event identity.
    metrics["cardTitleHints"] = min(len(soup.select("article h2, article h3, [class*=card] h2, [class*=card] h3")), MAX_ANCHORS + 1)
    return metrics

def classify(raw, frames, http, allowed_final, source_error):
    if source_error:
        return "HOLD_NAVIGATION_ERROR"
    if http != 200 or not allowed_final:
        return "HOLD_HTTP_OR_REDIRECT"
    if not raw["assessed"] or any(not f["assessed"] for f in frames):
        return "HOLD_UNASSESSED_CAP"
    if len(frames) != OBSERVATIONS:
        return "HOLD_OBSERVATION_INCOMPLETE"
    last = frames[-1]
    if last["strictWithLocalTitle"] > 0:
        return "REVIEW_SAME_NAVIGATION_CANDIDATES_NOT_IDENTITY"
    if last["strictEventIdAnchors"] > 0:
        return "HOLD_STRICT_ID_LOCAL_TITLE_MISSING"
    if last["eventPathAnchors"] > 0:
        return "HOLD_EVENT_PATH_FORMAT_OR_QUERY"
    if last["externalEventLinks"] > 0:
        return "HOLD_EXTERNAL_EVENT_LINKS_NOT_FOLLOWED"
    if last["cardTitleHints"] > 0:
        return "HOLD_CARD_HINTS_WITHOUT_EVENT_URL"
    return "HOLD_NO_EVENT_SHAPED_ANCHORS"

def validate_status(raw):
    if git_blob(raw) != STATUS_BLOB:
        raise ValueError("HOLD_STATUS_BLOB")
    s = json.loads(raw)
    if s["production"]["eventFeedReleaseState"] != RELEASE or s["production"]["goldenAccepted"] != 0:
        raise ValueError("HOLD_RELEASE")
    row = next((x for x in s["platforms"] if x["platform"] == "ACCUPASS"), None)
    if not row or row["baseline"]["listCandidates"] != 25:
        raise ValueError("HOLD_HISTORICAL_BASELINE")
    return True

def probe():
    result = dict(http=None, allowedFinal=False, navigationCount=0, sourceError=None,
                  initialHtml=None, domObservations=[], documentStates=[], decision="HOLD_NOT_STARTED")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=False, service_workers="block")
        page = context.new_page()
        def guard(route):
            if route.request.is_navigation_request() and not allowed(route.request.url):
                route.abort("blockedbyclient")
            else:
                route.continue_()
        page.route("**/*", guard)
        try:
            result["navigationCount"] = 1
            response = page.goto(ENTRY, wait_until="domcontentloaded", timeout=18000)
            result["http"] = response.status if response else None
            result["allowedFinal"] = allowed(page.url)
            if result["http"] == 200 and result["allowedFinal"]:
                result["initialHtml"] = inspect(response.text())
                for i in range(OBSERVATIONS):
                    if i:
                        page.wait_for_timeout(650)
                    result["documentStates"].append(page.evaluate("document.readyState"))
                    result["domObservations"].append(inspect(page.content()))
        except Exception as exc:
            result["sourceError"] = type(exc).__name__
        finally:
            page.close()
            context.close()
            browser.close()
    if result["initialHtml"] is not None:
        result["decision"] = classify(result["initialHtml"], result["domObservations"],
                                      result["http"], result["allowedFinal"], result["sourceError"])
    else:
        result["decision"] = "HOLD_NO_ASSESSABLE_HTML"
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    if not args.live:
        raise ValueError("HOLD_LIVE_SCOPE_REQUIRED")
    validate_status(Path(args.status).read_bytes())
    if Path(args.out).resolve() != (Path.cwd() / "p30-l9ae-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    report = probe()
    report.update(kind=KIND, parentHead=PARENT, sourceMain=SOURCE_MAIN, statusBlob=STATUS_BLOB,
                  releaseState=RELEASE, formalVerifiedEventIdentity=0, acceptedFields=0,
                  goldenAccepted=0, published=False, productionModified=False,
                  writerExecuted=False, schedulerExecuted=False, notifierExecuted=False,
                  mergeExecuted=False, rawHtmlPersisted=False, rawUrlsPersisted=False,
                  rawTitlesPersisted=False, rawEventIdsPersisted=False,
                  cookiesPersisted=False, screenshotsPersisted=False)
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "accupass_list_topology.json").write_bytes(raw)
    manifest = dict(kind="EVENTRADAR_P30_L9AE_SHA_MANIFEST_V1",
                    filesSHA256={"accupass_list_topology.json": hashlib.sha256(raw).hexdigest()},
                    releaseState=RELEASE, published=False)
    (out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print("L9AE_ACCUPASS", json.dumps(dict(http=report["http"], decision=report["decision"],
        initial=report["initialHtml"], last=(report["domObservations"][-1] if report["domObservations"] else None)),
        ensure_ascii=False))
    print("HOLD_L9AE_NO_IDENTITY_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
