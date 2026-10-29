#!/usr/bin/env python3
"""P30-L9-AF: ACCUPASS public event-path query-key roles, no values/identity/publish."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

KIND = "EVENTRADAR_P30_L9AF_ACCUPASS_QUERY_ROLES_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "36dce126cb0e17be3a2bbb4fe385d89ce9f4f338"
SOURCE_MAIN = "fbf4ca02b91159f2423caf3d79fb0ca4bb747069"
STATUS_BLOB = "e19ca37c4c80c10b7278d0813b8ff1047535d124"
DATA_BLOB = "7fc4fe32567a57fd504483eeb9a8b9e10b568ea4"
ENTRY = "https://www.accupass.com/search?q=%E9%9F%B3%E6%A8%82"
MAX_HTML_BYTES = 1_500_000
MAX_ANCHORS = 400
MAX_QUERY_BYTES = 2048
MAX_QUERY_FIELDS = 12
MAX_TITLE = 240
OBSERVATIONS = 4
ID_RE = re.compile(r"^/event/([A-Za-z0-9_-]{8,64})/?$", re.I)
KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
TRACKING = frozenset(("utm_source", "utm_medium", "utm_campaign", "utm_term",
                      "utm_content", "gclid", "fbclid", "msclkid"))
SEMANTIC = frozenset(("eventid", "event_id", "id", "ticket", "session", "date",
                      "time", "price", "type", "product", "lang", "locale",
                      "category", "order", "sale", "start", "end"))

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

def query_roles(query):
    """Return only bounded safe-name counts; never return parameter values or unknown names."""
    if not query:
        return dict(kind="NONE", count=0, tracking={}, semantic=0, unknown=0, malformed=0)
    if len(query.encode("utf-8")) > MAX_QUERY_BYTES:
        return dict(kind="OVER_CAP", count=0, tracking={}, semantic=0, unknown=0, malformed=1)
    try:
        pairs = parse_qsl(query, keep_blank_values=True, max_num_fields=MAX_QUERY_FIELDS,
                          errors="strict")
    except (ValueError, UnicodeError):
        return dict(kind="MALFORMED", count=0, tracking={}, semantic=0, unknown=0, malformed=1)
    out = dict(kind="PARSED", count=len(pairs), tracking={}, semantic=0, unknown=0, malformed=0)
    for key, _value in pairs:
        low = key.lower()
        if not KEY_RE.fullmatch(key):
            out["unknown"] += 1
        elif low in TRACKING:
            out["tracking"][low] = out["tracking"].get(low, 0) + 1
        elif low in SEMANTIC:
            out["semantic"] += 1
        else:
            out["unknown"] += 1
    return out

def inspect(html):
    """Aggregate counts only; no raw HTML, URL, title, event ID or query values leave memory."""
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        return dict(assessed=False, hold="HTML_CAP")
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select("a[href]")
    if len(anchors) > MAX_ANCHORS:
        return dict(assessed=False, hold="ANCHOR_CAP", anchorCount=len(anchors))
    m = dict(assessed=True, hold=None, anchorCount=len(anchors), eventPathAnchors=0,
             queryEventAnchors=0, strictPathWithQuery=0, strictPathWithoutQuery=0,
             malformedQueryAnchors=0, trackingOnlyAnchors=0, semanticQueryAnchors=0,
             unknownQueryAnchors=0, localTitleOnQueryAnchors=0,
             missingLocalTitleOnQueryAnchors=0, duplicateEventPaths=0,
             uniqueEventPaths=0, uniquePathsWithLocalTitle=0,
             uniquePathsWithoutLocalTitle=0, mixedTitlePresencePaths=0,
             conflictingTitlePaths=0, nonEventAnchors=0, rejectedEventAnchors=0,
             trackingKeyCounts={})
    seen = set()
    title_states = {}  # in-memory path-to-local-title evidence; never persisted
    for a in anchors:
        try:
            url = urljoin(ENTRY, a.get("href") or "")
            p = urlsplit(url)
        except ValueError:
            m["rejectedEventAnchors"] += 1
            continue
        if not p.path.lower().startswith("/event/"):
            m["nonEventAnchors"] += 1
            continue
        if not allowed(url):
            m["rejectedEventAnchors"] += 1
            continue
        m["eventPathAnchors"] += 1
        match = ID_RE.fullmatch(p.path)
        if match:
            key = match.group(1).lower()
            title_states.setdefault(key, {"titles": set(), "missing": False})
            if key in seen:
                m["duplicateEventPaths"] += 1
            else:
                seen.add(key)
        if not p.query:
            if match:
                m["strictPathWithoutQuery"] += 1
            continue
        m["queryEventAnchors"] += 1
        if match:
            m["strictPathWithQuery"] += 1
        q = query_roles(p.query)
        if q["malformed"]:
            m["malformedQueryAnchors"] += 1
        if q["semantic"]:
            m["semanticQueryAnchors"] += 1
        if q["unknown"]:
            m["unknownQueryAnchors"] += 1
        if q["kind"] == "PARSED" and q["count"] > 0 and not (q["semantic"] or q["unknown"]):
            m["trackingOnlyAnchors"] += 1
        for name, count in q["tracking"].items():
            m["trackingKeyCounts"][name] = m["trackingKeyCounts"].get(name, 0) + count
        node = a.find(["h2", "h3", "h4"]) or a
        title = " ".join(node.get_text(" ", strip=True).split())
        if 4 <= len(title) <= MAX_TITLE:
            m["localTitleOnQueryAnchors"] += 1
            if match:
                title_states[key]["titles"].add(title)
        else:
            m["missingLocalTitleOnQueryAnchors"] += 1
            if match:
                title_states[key]["missing"] = True
    m["uniqueEventPaths"] = len(seen)
    m["uniquePathsWithLocalTitle"] = sum(bool(s["titles"]) for s in title_states.values())
    m["uniquePathsWithoutLocalTitle"] = sum(not s["titles"] for s in title_states.values())
    m["mixedTitlePresencePaths"] = sum(bool(s["titles"]) and s["missing"] for s in title_states.values())
    m["conflictingTitlePaths"] = sum(len(s["titles"]) > 1 for s in title_states.values())
    return m

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
    if last["malformedQueryAnchors"]:
        return "HOLD_QUERY_MALFORMED_OR_CAP"
    if last["semanticQueryAnchors"] or last["unknownQueryAnchors"]:
        return "HOLD_QUERY_SEMANTICS_UNKNOWN"
    if last["queryEventAnchors"] and last["strictPathWithQuery"] < last["queryEventAnchors"]:
        return "HOLD_EVENT_ID_PATH_SHAPE"
    if last["conflictingTitlePaths"]:
        return "HOLD_CONFLICTING_ANCHOR_LOCAL_TITLES"
    if last["queryEventAnchors"] and last["uniquePathsWithoutLocalTitle"]:
        return "HOLD_EVENT_PATH_WITHOUT_LOCAL_TITLE"
    if last["trackingOnlyAnchors"] and last["strictPathWithQuery"] == last["trackingOnlyAnchors"]:
        return "REVIEW_TRACKING_NAMES_AND_LOCAL_PATH_TITLES_NOT_DETAIL_IDENTITY"
    if last["eventPathAnchors"]:
        return "HOLD_EVENT_PATH_NOT_ACCEPTED"
    return "HOLD_NO_EVENT_PATH"

def validate_status(raw):
    if git_blob(raw) != STATUS_BLOB:
        raise ValueError("HOLD_STATUS_BLOB")
    obj = json.loads(raw)
    if (obj["production"]["eventFeedReleaseState"] != RELEASE
            or obj["production"]["goldenAccepted"] != 0):
        raise ValueError("HOLD_RELEASE")
    row = next((x for x in obj["platforms"] if x["platform"] == "ACCUPASS"), None)
    if not row or row["baseline"]["listCandidates"] != 25:
        raise ValueError("HOLD_BASELINE")
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
        raise ValueError("HOLD_EXPLICIT_LIVE_SCOPE")
    validate_status(Path(args.status).read_bytes())
    if Path(args.out).resolve() != (Path.cwd() / "p30-l9af-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    report = probe()
    report.update(kind=KIND, parentHead=PARENT, sourceMain=SOURCE_MAIN,
                  statusBlob=STATUS_BLOB, dataBlob=DATA_BLOB,
                  releaseState=RELEASE, formalVerifiedEventIdentity=0, acceptedFields=0,
                  goldenAccepted=0, published=False, productionModified=False,
                  writerExecuted=False, schedulerExecuted=False, notifierExecuted=False,
                  mergeExecuted=False, detailNavigated=False,
                  rawHtmlPersisted=False, rawUrlsPersisted=False,
                  rawTitlesPersisted=False, rawEventIdsPersisted=False,
                  queryValuesPersisted=False, unknownQueryNamesPersisted=False,
                  cookiesPersisted=False, screenshotsPersisted=False)
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "accupass_query_roles.json").write_bytes(raw)
    manifest = dict(kind="EVENTRADAR_P30_L9AF_SHA_MANIFEST_V1",
                    filesSHA256={"accupass_query_roles.json": hashlib.sha256(raw).hexdigest()},
                    releaseState=RELEASE, published=False)
    (out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print("L9AF_ACCUPASS", json.dumps(dict(http=report["http"], decision=report["decision"],
        initial=report["initialHtml"],
        last=(report["domObservations"][-1] if report["domObservations"] else None)),
        ensure_ascii=False))
    print("HOLD_L9AF_NO_IDENTITY_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
