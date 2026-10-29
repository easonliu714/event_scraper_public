#!/usr/bin/env python3
"""P30-L9-AG: at most two public ACCUPASS same-path list/detail title reviews. NO PUBLISH."""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import p30_l9af_accupass_query_roles as prior

KIND = "EVENTRADAR_P30_L9AG_ACCUPASS_DETAIL_PARITY_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "ae54d7687893e4f0960fc7d3926c7a376798d386"
SOURCE_MAIN = prior.SOURCE_MAIN
STATUS_BLOB = prior.STATUS_BLOB
DATA_BLOB = prior.DATA_BLOB
ENTRY = prior.ENTRY
MAX_HTML_BYTES = 1_500_000
MAX_ANCHORS = 400
MAX_HEADINGS = 60
MAX_TITLE = 240
MAX_DETAILS = 2
OBSERVATIONS = 4
ID_RE = re.compile(r"^/event/([A-Za-z0-9_-]{8,64})/?$", re.I)

def normalized(value):
    return " ".join(unicodedata.normalize("NFC", value).split())

def safe_event(url):
    if not prior.allowed(url):
        return False
    p = urlsplit(url)
    q = prior.query_roles(p.query)
    return bool(ID_RE.fullmatch(p.path) and p.query and q["kind"] == "PARSED"
                and q["count"] > 0 and not (q["semantic"] or q["unknown"] or q["malformed"])
                and sum(q["tracking"].values()) == q["count"])

def list_candidates(html):
    """Return private in-memory candidates and aggregate-only public metrics."""
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        return {"assessed": False, "hold": "HTML_CAP"}, []
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select("a[href]")
    if len(anchors) > MAX_ANCHORS:
        return {"assessed": False, "hold": "ANCHOR_CAP", "anchorCount": len(anchors)}, []
    metrics = dict(assessed=True, hold=None, anchorCount=len(anchors), eventAnchors=0,
                   eligibleAnchors=0, rejectedEventAnchors=0, uniquePaths=0,
                   titledPaths=0, conflictingTitlePaths=0, candidateCount=0)
    groups = {}
    for a in anchors:
        try:
            url = urljoin(ENTRY, a.get("href") or "")
            p = urlsplit(url)
        except ValueError:
            metrics["rejectedEventAnchors"] += 1
            continue
        if not p.path.lower().startswith("/event/"):
            continue
        metrics["eventAnchors"] += 1
        if not safe_event(url):
            metrics["rejectedEventAnchors"] += 1
            continue
        metrics["eligibleAnchors"] += 1
        event_id = ID_RE.fullmatch(p.path).group(1).lower()
        group = groups.setdefault(event_id, {"titles": set(), "candidate": None})
        title_node = a.find(["h2", "h3", "h4"]) or a
        title = normalized(title_node.get_text(" ", strip=True))
        if 4 <= len(title) <= MAX_TITLE:
            group["titles"].add(title)
            if group["candidate"] is None:
                group["candidate"] = (event_id, title, url)
    metrics["uniquePaths"] = len(groups)
    metrics["titledPaths"] = sum(bool(g["titles"]) for g in groups.values())
    metrics["conflictingTitlePaths"] = sum(len(g["titles"]) > 1 for g in groups.values())
    candidates = [g["candidate"] for g in groups.values()
                  if len(g["titles"]) == 1 and g["candidate"] is not None]
    metrics["candidateCount"] = len(candidates)
    if metrics["rejectedEventAnchors"]:
        metrics["hold"] = "UNSAFE_OR_UNCLASSIFIED_EVENT_LINK"
    elif metrics["conflictingTitlePaths"]:
        metrics["hold"] = "CONFLICTING_LOCAL_TITLES"
    elif metrics["candidateCount"] < MAX_DETAILS:
        metrics["hold"] = "INSUFFICIENT_UNIQUE_TITLED_PATHS"
    return metrics, candidates

def detail_heading_evidence(html, expected_title):
    """Only exact NFC/whitespace H1/H2 equality; never return heading text."""
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        return dict(assessed=False, hold="HTML_CAP", headingCount=None, exactMatches=None)
    headings = BeautifulSoup(html, "html.parser").select("h1, h2")
    if len(headings) > MAX_HEADINGS:
        return dict(assessed=False, hold="HEADING_CAP", headingCount=len(headings), exactMatches=None)
    return dict(assessed=True, hold=None, headingCount=len(headings),
                exactMatches=sum(normalized(h.get_text(" ", strip=True)) == expected_title
                                 for h in headings))

def detail_decision(candidate, final_url, http, redirected, states, observations, error):
    if error:
        return "HOLD_DETAIL_NAVIGATION_ERROR"
    if http != 200:
        return "HOLD_DETAIL_HTTP"
    if not safe_event(final_url) or final_url != candidate[2] or redirected:
        return "HOLD_REDIRECT_OR_ID_QUERY_CHANGED"
    if len(observations) != OBSERVATIONS or len(states) != OBSERVATIONS:
        return "HOLD_INCOMPLETE_OBSERVATIONS"
    if any(not x["assessed"] for x in observations):
        return "HOLD_DETAIL_UNASSESSED_CAP"
    last = observations[-1]
    if last["headingCount"] == 0:
        return "HOLD_NO_H1_H2"
    if last["exactMatches"] == 0:
        return "HOLD_H1_H2_TITLE_MISMATCH"
    if states[-1] != "complete":
        return "HOLD_DETAIL_INTERACTIVE"
    return "REVIEW_EXACT_SAME_PATH_H1_H2_TITLE_NOT_FORMAL_IDENTITY"

def probe():
    result = dict(listHttp=None, listFinalAllowed=False, listNavigationCount=0,
                  listSourceError=None, rawList=None, finalList=None,
                  listStates=[], detailNavigationCount=0, details=[],
                  decision="HOLD_NOT_STARTED")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=False, service_workers="block")
        def guard(route):
            if route.request.is_navigation_request() and not prior.allowed(route.request.url):
                route.abort("blockedbyclient")
            else:
                route.continue_()
        page = context.new_page()
        page.route("**/*", guard)
        selected = []
        try:
            result["listNavigationCount"] = 1
            response = page.goto(ENTRY, wait_until="domcontentloaded", timeout=18000)
            result["listHttp"] = response.status if response else None
            result["listFinalAllowed"] = prior.allowed(page.url) and page.url == ENTRY
            if result["listHttp"] == 200 and result["listFinalAllowed"]:
                raw_metrics, raw_candidates = list_candidates(response.text())
                result["rawList"] = raw_metrics
                dom_metrics, dom_candidates = None, []
                for i in range(OBSERVATIONS):
                    if i:
                        page.wait_for_timeout(650)
                    result["listStates"].append(page.evaluate("document.readyState"))
                    dom_metrics, dom_candidates = list_candidates(page.content())
                result["finalList"] = dom_metrics
                if (raw_metrics["assessed"] and dom_metrics["assessed"]
                        and not raw_metrics["hold"] and not dom_metrics["hold"]
                        and {c[0] for c in raw_candidates} == {c[0] for c in dom_candidates}):
                    selected = dom_candidates[:MAX_DETAILS]
        except Exception as exc:
            result["listSourceError"] = type(exc).__name__
        finally:
            page.close()
        for candidate in selected:
            item = dict(http=None, allowedFinal=False, redirected=None,
                        states=[], observations=[], sourceError=None,
                        decision="HOLD_NOT_STARTED")
            detail = context.new_page()
            detail.route("**/*", guard)
            try:
                result["detailNavigationCount"] += 1
                response = detail.goto(candidate[2], wait_until="domcontentloaded", timeout=18000)
                item["http"] = response.status if response else None
                item["allowedFinal"] = safe_event(detail.url)
                item["redirected"] = bool(response and response.request.redirected_from)
                if item["http"] == 200 and item["allowedFinal"]:
                    for i in range(OBSERVATIONS):
                        if i:
                            detail.wait_for_timeout(650)
                        item["states"].append(detail.evaluate("document.readyState"))
                        item["observations"].append(detail_heading_evidence(detail.content(), candidate[1]))
            except Exception as exc:
                item["sourceError"] = type(exc).__name__
            finally:
                final_url = detail.url
                detail.close()
            item["decision"] = detail_decision(candidate, final_url, item["http"],
                                               item["redirected"], item["states"],
                                               item["observations"], item["sourceError"])
            result["details"].append(item)
        context.close()
        browser.close()
    if result["listSourceError"]:
        result["decision"] = "HOLD_LIST_NAVIGATION_ERROR"
    elif result["listHttp"] != 200 or not result["listFinalAllowed"]:
        result["decision"] = "HOLD_LIST_HTTP_OR_REDIRECT"
    elif not selected:
        result["decision"] = "HOLD_LIST_CANDIDATES_OR_STABILITY"
    elif len(result["details"]) != MAX_DETAILS:
        result["decision"] = "HOLD_DETAIL_SAMPLE_INCOMPLETE"
    elif all(x["decision"].startswith("REVIEW_") for x in result["details"]):
        result["decision"] = "REVIEW_TWO_SOURCE_BOUND_TITLE_MATCHES_NOT_FORMAL_IDENTITY"
    else:
        result["decision"] = "HOLD_ONE_OR_MORE_DETAIL_IDENTITY_CHECKS"
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    if not args.live:
        raise ValueError("HOLD_EXPLICIT_LIVE_SCOPE")
    prior.validate_status(Path(args.status).read_bytes())
    if Path(args.out).resolve() != (Path.cwd() / "p30-l9ag-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    report = probe()
    report.update(kind=KIND, parentHead=PARENT, sourceMain=SOURCE_MAIN,
                  statusBlob=STATUS_BLOB, dataBlob=DATA_BLOB,
                  releaseState=RELEASE, formalVerifiedEventIdentity=0, acceptedFields=0,
                  goldenAccepted=0, published=False, productionModified=False,
                  writerExecuted=False, schedulerExecuted=False, notifierExecuted=False,
                  mergeExecuted=False, rawHtmlPersisted=False, rawUrlsPersisted=False,
                  rawTitlesPersisted=False, rawEventIdsPersisted=False,
                  queryValuesPersisted=False, cookiesPersisted=False,
                  screenshotsPersisted=False)
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "accupass_detail_parity.json").write_bytes(raw)
    manifest = dict(kind="EVENTRADAR_P30_L9AG_SHA_MANIFEST_V1",
                    filesSHA256={"accupass_detail_parity.json": hashlib.sha256(raw).hexdigest()},
                    releaseState=RELEASE, published=False)
    (out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print("L9AG_ACCUPASS", json.dumps(dict(listHttp=report["listHttp"],
          rawList=report["rawList"], finalList=report["finalList"],
          details=[dict(http=x["http"], decision=x["decision"],
                        last=(x["observations"][-1] if x["observations"] else None))
                   for x in report["details"]], decision=report["decision"])))
    print("HOLD_L9AG_NO_IDENTITY_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
