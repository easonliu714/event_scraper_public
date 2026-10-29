#!/usr/bin/env python3
"""P30-L9-Z: bounded Kham list -> exact Product ID -> detail H1/H2 parity.
One public category navigation, at most two same-origin detail navigations.
Only structural counts and reason codes are retained; no activity publication.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

KIND = "EVENTRADAR_P30_L9Z_KHAM_LIST_DETAIL_IDENTITY_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "b8bd1905a875d62d131cd8db1fec814437b2fcb5"
PARENT_REPORT_SHA256 = "9104fcd2e6d5c3f78c9a7b5d86754abbfb9f5f0b0fd5462fd25e76bcdfb89e12"
SOURCE_BLOB = "98eddeafb497718c51aa81c6a150e9a5e1e687a8"
STATUS_BLOB = "e19ca37c4c80c10b7278d0813b8ff1047535d124"
MAX_BYTES = 1500000
MAX_ANCHORS = 1200
MAX_DETAILS = 2
SNAPSHOTS = 4
BASE = Path(__file__).resolve().parents[1]
Y_PATH = BASE / "scripts/p30_l9y_kham_event_object_boundary.py"
X_PATH = BASE / "scripts/p30_l9x_kham_original_parser_parity.py"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def parent_check(status_bytes, parent_bytes):
    if git_blob(status_bytes) != STATUS_BLOB:
        raise ValueError("HOLD_FORMAL_STATUS_SHA")
    if sha(parent_bytes) != PARENT_REPORT_SHA256:
        raise ValueError("HOLD_L9Y_PARENT_REPORT_SHA")
    try:
        status = json.loads(status_bytes)
        parent = json.loads(parent_bytes)
        if status["production"]["eventFeedReleaseState"] != RELEASE:
            raise ValueError("HOLD_PRODUCTION_RELEASE")
        if status["production"]["goldenAccepted"] != 0:
            raise ValueError("HOLD_PRODUCTION_GOLDEN")
        if parent["kind"] != "EVENTRADAR_P30_L9Y_KHAM_EVENT_OBJECT_BOUNDARY_V1":
            raise ValueError("HOLD_PARENT_KIND")
        if parent["releaseState"] != RELEASE or parent["published"] is not False:
            raise ValueError("HOLD_PARENT_RELEASE")
        if parent["decision"] != "REVIEW_CURRENT_PROVISIONAL_OBJECTS_HISTORIC_ZERO":
            raise ValueError("HOLD_PARENT_DECISION")
        if parent["static"]["acceptedObjects"] != 10 or parent["rendered"]["acceptedObjects"] != 10:
            raise ValueError("HOLD_PARENT_COUNT")
    except (KeyError, TypeError, IndexError, json.JSONDecodeError) as exc:
        raise ValueError("HOLD_MALFORMED_PARENT") from exc
    return True

def product_id(url, allowed):
    """Require one canonical Kham detail route and one alphanumeric Product ID."""
    try:
        if not allowed(url):
            return None
        p = urlparse(url)
        if p.path != "/application/UTK02/UTK0201_.aspx" or p.fragment:
            return None
        q = parse_qs(p.query, keep_blank_values=True)
        if set(q) != {"PRODUCT_ID"} or len(q["PRODUCT_ID"]) != 1:
            return None
        value = q["PRODUCT_ID"][0]
        return value if re.fullmatch(r"[A-Za-z0-9]{1,32}", value) else None
    except (ValueError, TypeError):
        return None

def normalize_title(text):
    """Whitespace/NFC only: never substring-match or strip event-specific text."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()

def list_candidates(html, funcs, allowed):
    """Exact frozen production selector and object filter; all strings in memory."""
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", href=True)
    if len(anchors) > MAX_ANCHORS:
        raise ValueError("HOLD_LIST_ANCHOR_CAP")
    selected = soup.select('a[href*="UTK0201_"]')
    counts = {"allAnchors": len(anchors), "selected": len(selected),
              "unsafeSelected": 0, "nonCanonical": 0, "rejectedObjects": 0,
              "duplicateProductId": 0, "provisionalObjects": 0}
    seen = set()
    candidates = []
    for a in selected:
        raw = urljoin("https://kham.com.tw", a.get("href"))
        if not allowed(raw):
            counts["unsafeSelected"] += 1
            continue
        canonical = funcs["fix_utk_url"]("kham.com.tw", raw)
        pid = product_id(canonical, allowed)
        if pid is None:
            counts["nonCanonical"] += 1
            continue
        if pid in seen:
            counts["duplicateProductId"] += 1
            continue
        title = funcs["safe_get_text"](a)
        ev = funcs["create_event_obj"](title, canonical, "寬宏", None)
        if not ev or not ev.get("title"):
            counts["rejectedObjects"] += 1
            continue
        seen.add(pid)
        counts["provisionalObjects"] += 1
        candidates.append((pid, ev["title"], canonical))
    return candidates, counts

def heading_state(html, ready, expected):
    """Exact H1/H2 text only; a page title/substring is never sufficient."""
    soup = BeautifulSoup(html, "html.parser")
    headings = [normalize_title(h.get_text(" ", strip=True))
                for h in soup.select("h1,h2")]
    expected = normalize_title(expected)
    matches = sum(bool(expected) and h == expected for h in headings)
    return {"ready": ready, "headingCandidates": len(headings),
            "exactHeadingMatches": matches}

def classify_detail(detail):
    if not detail["finalAllowed"]:
        return "HOLD_UNSAFE_DETAIL_FINAL"
    if not detail["sameProductId"]:
        return "HOLD_DETAIL_PRODUCT_ID_DRIFT"
    if detail["http"] != 200:
        return "HOLD_DETAIL_HTTP_NOT_200"
    frames = detail["frames"]
    if len(frames) != SNAPSHOTS:
        return "HOLD_INCOMPLETE_DETAIL_SNAPSHOTS"
    if any(f["headingCandidates"] > 80 or f["exactHeadingMatches"] > 1 for f in frames):
        return "HOLD_AMBIGUOUS_HEADING"
    if all(f["ready"] == "complete" and f["exactHeadingMatches"] == 1 for f in frames[-2:]):
        return "REVIEW_EXACT_SAME_ID_STABLE_H1H2"
    if not any(f["exactHeadingMatches"] for f in frames):
        return ("HOLD_NO_H1H2_CANDIDATE" if not any(f["headingCandidates"] for f in frames)
                else "HOLD_H1H2_TITLE_NONMATCH")
    return "HOLD_H1H2_NOT_STABLE"

def decision(report):
    if not report["listFinalAllowed"]:
        return "HOLD_UNSAFE_LIST_FINAL"
    if report["listHttp"] != 200:
        return "HOLD_LIST_HTTP_NOT_200"
    if report["listCounts"] is None:
        return "HOLD_LIST_PARSE_MISSING"
    if report["listCounts"]["unsafeSelected"] or report["listCounts"]["nonCanonical"]:
        return "HOLD_LIST_UNSAFE_OR_NONCANONICAL"
    if report["listCounts"]["provisionalObjects"] < MAX_DETAILS:
        return "HOLD_INSUFFICIENT_LIST_CANDIDATES"
    if len(report["samples"]) != MAX_DETAILS:
        return "HOLD_DETAIL_SAMPLING_INCOMPLETE"
    if any(s["decision"] != "REVIEW_EXACT_SAME_ID_STABLE_H1H2" for s in report["samples"]):
        return "HOLD_DETAIL_IDENTITY_OR_TITLE_PARITY"
    return "REVIEW_TWO_CURRENT_SAME_ID_TITLE_MATCHES_NO_FIELD_PROMOTION"

def one_bounded_probe(funcs, allowed, entry):
    """Normal Chromium JS, no clicks, no login, no retry, at most 3 navigations."""
    from playwright.sync_api import sync_playwright
    out = {"listHttp": None, "listFinalAllowed": False, "listCounts": None,
           "samples": [], "navigationCount": 0, "sourceException": False}
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
            out["navigationCount"] += 1
            response = page.goto(entry, wait_until="domcontentloaded", timeout=18000)
            out["listHttp"] = response.status if response else None
            out["listFinalAllowed"] = allowed(page.url)
            if response and out["listHttp"] == 200 and out["listFinalAllowed"]:
                raw = response.body()
                if len(raw) <= MAX_BYTES:
                    candidates, out["listCounts"] = list_candidates(raw, funcs, allowed)
        except Exception:
            out["sourceException"] = True
        finally:
            page.close()
        if out["listCounts"] and not out["listCounts"]["unsafeSelected"] and not out["listCounts"]["nonCanonical"]:
            for i, (expected_id, expected_title, detail_url) in enumerate(candidates[:MAX_DETAILS]):
                d = {"sampleIndex": i, "http": None, "finalAllowed": False,
                     "sameProductId": False, "frames": [], "redirects": 0,
                     "sourceException": False}
                detail = context.new_page()
                detail.route("**/*", guard)
                try:
                    out["navigationCount"] += 1
                    response = detail.goto(detail_url, wait_until="domcontentloaded", timeout=18000)
                    d["http"] = response.status if response else None
                    prev = response.request.redirected_from if response else None
                    while prev and d["redirects"] <= 3:
                        d["redirects"] += 1
                        prev = prev.redirected_from
                    d["finalAllowed"] = allowed(detail.url) and d["redirects"] <= 2
                    d["sameProductId"] = product_id(detail.url, allowed) == expected_id
                    if d["http"] == 200 and d["finalAllowed"] and d["sameProductId"]:
                        for k in range(SNAPSHOTS):
                            if k:
                                detail.wait_for_timeout(600)
                            rendered = detail.content()
                            if len(rendered.encode("utf-8")) > MAX_BYTES:
                                break
                            d["frames"].append(heading_state(
                                rendered, detail.evaluate("document.readyState"), expected_title))
                except Exception:
                    d["sourceException"] = True
                finally:
                    detail.close()
                d["decision"] = classify_detail(d)
                out["samples"].append(d)
        context.close()
        browser.close()
    return out

def main():
    ap = argparse.ArgumentParser()
    for name in ("status", "parent", "scraper", "out"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--live-kham", action="store_true")
    a = ap.parse_args()
    if not a.live_kham:
        raise ValueError("HOLD_EXPLICIT_LIVE_SCOPE")
    parent_bytes = Path(a.parent).read_bytes()
    parent_check(Path(a.status).read_bytes(), parent_bytes)
    y = load(Y_PATH, "p30_l9y_frozen")
    x = load(X_PATH, "p30_l9x_source")
    funcs = y.frozen_functions(Path(a.scraper).read_bytes())
    probe = one_bounded_probe(funcs, x.allowed, x.ENTRY)
    result = dict(kind=KIND, platform="寬宏", parentHead=PARENT,
                  parentReportSHA256=sha(parent_bytes), frozenScraperBlob=SOURCE_BLOB,
                  formalStatusBlob=STATUS_BLOB, **probe, decision=decision(probe),
                  sampledCurrentTitleMatches=sum(
                      s["decision"] == "REVIEW_EXACT_SAME_ID_STABLE_H1H2"
                      for s in probe["samples"]),
                  formalVerifiedEventIdentity=0, acceptedFields=0, goldenAccepted=0,
                  published=False, productionModified=False, mergeExecuted=False,
                  writerExecuted=False, schedulerExecuted=False, notifierExecuted=False,
                  rawHtmlPersisted=False, rawUrlsPersisted=False, rawTitlesPersisted=False,
                  rawProductIdsPersisted=False, cookiesPersisted=False,
                  screenshotsPersisted=False, releaseState=RELEASE)
    out = Path(a.out).resolve()
    if out != (Path.cwd() / "p30-l9z-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    out.mkdir(exist_ok=True)
    data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    (out / "kham_list_detail_identity.json").write_bytes(data)
    manifest = {"kind": "EVENTRADAR_P30_L9Z_SHA_MANIFEST_V1",
                "filesSHA256": {"kham_list_detail_identity.json": sha(data)},
                "releaseState": RELEASE, "published": False}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("L9Z_KHAM", json.dumps({
        "listHttp": result["listHttp"], "listCounts": result["listCounts"],
        "samples": [{"http": s["http"], "decision": s["decision"],
                     "sameProductId": s["sameProductId"]} for s in result["samples"]],
        "decision": result["decision"]}, ensure_ascii=False))
    print("HOLD_L9Z_NO_FORMAL_IDENTITY_NO_FIELDS_NO_PUBLICATION")

if __name__ == "__main__":
    main()
