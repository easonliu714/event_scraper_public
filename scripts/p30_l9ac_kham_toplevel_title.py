#!/usr/bin/env python3
"""P30-L9-AC: bounded top-level table/component title topology; review-only."""
import argparse
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import p30_l9ab_kham_iframe_narrow as ab

KIND = "EVENTRADAR_P30_L9AC_KHAM_TOPLEVEL_TITLE_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT_HEAD = "f657555b16f41d4d24e4b67205c0c0019d0b12fe"
PARENT_ARTIFACT_SHA = "18da27a1ceec328af40ae5f2ca3eb59665bbd82e6d4258355de71cfb39458b21"
MAX_TABLES = 12
MAX_ROWS = 160
MAX_COMPONENTS = 64
MAX_TEXT_CHARS = 240
MAX_DETAILS = 2
SNAPSHOTS = 4
LABELS = frozenset(("活動名稱", "節目名稱", "演出名稱", "商品名稱", "活動", "節目"))
TABLE_SELECTOR = "main table,#content table,.detail table,table[class*='event'],table[class*='product']"
COMPONENT_SELECTOR = (
    "main [class*='event-name'],#content [class*='event-name'],"
    "main [class*='product-name'],#content [class*='product-name'],"
    "main [class*='show-name'],#content [class*='show-name'],"
    "main [class*='event-title'],#content [class*='event-title'],"
    "main [class*='product-title'],#content [class*='product-title'],"
    "main [class*='show-title'],#content [class*='show-title']"
)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify_parent(status_raw, parent_raw, scraper_raw):
    if ab.aa.z.git_blob(status_raw) != ab.aa.STATUS_BLOB:
        raise ValueError("HOLD_STATUS_BLOB")
    if ab.aa.z.git_blob(scraper_raw) != ab.aa.SOURCE_BLOB:
        raise ValueError("HOLD_SCRAPER_BLOB")
    try:
        status, parent = json.loads(status_raw), json.loads(parent_raw)
        assert status["production"]["eventFeedReleaseState"] == RELEASE
        assert status["production"]["goldenAccepted"] == 0
        assert parent["kind"] == ab.KIND and parent["releaseState"] == RELEASE
        assert parent["decision"] == "HOLD_IFRAME_AND_NARROW_TITLE_NOT_FORMALLY_VERIFIED"
        assert len(parent["samples"]) == 2
        assert parent["formalVerifiedEventIdentity"] == parent["acceptedFields"] == parent["goldenAccepted"] == 0
        assert parent["published"] is False
    except (AssertionError, ValueError, KeyError, TypeError, IndexError) as exc:
        raise ValueError("HOLD_PARENT_CONTRACT") from exc
    return True

def exact(text, expected):
    return ab.aa.z.normalize_title(text) == ab.aa.z.normalize_title(expected)

def bounded_text(node):
    text = node.get_text(" ", strip=True)
    return text if len(text) <= MAX_TEXT_CHARS else None

def top_level_snapshot(html, expected):
    """Only top-level source-bound tables and named components; never global text/regex."""
    if len(html.encode("utf-8")) > ab.aa.MAX_BYTES:
        return dict(tableRows=None, labeledPairs=None, tableExact=None,
                    components=None, componentExact=None, overflow="HTML_BYTES")
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.select(TABLE_SELECTOR)
    if len(tables) > MAX_TABLES:
        return dict(tableRows=None, labeledPairs=None, tableExact=None,
                    components=None, componentExact=None, overflow="TABLE_COUNT")
    table_rows = labeled_pairs = table_exact = 0
    for table in tables:
        rows = table.select("tr")
        table_rows += len(rows)
        if table_rows > MAX_ROWS:
            return dict(tableRows=None, labeledPairs=None, tableExact=None,
                        components=None, componentExact=None, overflow="TABLE_ROWS")
        for row in rows:
            cells = row.find_all(["th", "td"], recursive=False)
            if not (2 <= len(cells) <= 4):
                continue
            label = bounded_text(cells[0])
            value = bounded_text(cells[1])
            if label is None or value is None:
                continue
            if ab.aa.z.normalize_title(label).rstrip("：: ") in LABELS:
                labeled_pairs += 1
                if exact(value, expected):
                    table_exact += 1
    components = soup.select(COMPONENT_SELECTOR)
    if len(components) > MAX_COMPONENTS:
        return dict(tableRows=table_rows, labeledPairs=labeled_pairs,
                    tableExact=table_exact, components=None,
                    componentExact=None, overflow="COMPONENT_COUNT")
    component_exact = 0
    for node in components:
        value = bounded_text(node)
        if value is not None and exact(value, expected):
            component_exact += 1
    return dict(tableRows=table_rows, labeledPairs=labeled_pairs,
                tableExact=table_exact, components=len(components),
                componentExact=component_exact, overflow=None)

def classify(sample):
    if sample["sourceException"]:
        return "HOLD_DETAIL_SOURCE_" + sample["sourceErrorKind"]
    if sample["http"] != 200 or not sample["finalAllowed"] or not sample["sameProductId"]:
        return "HOLD_DETAIL_IDENTITY_OR_HTTP"
    frames = sample["frames"]
    if len(frames) != SNAPSHOTS:
        return "HOLD_INCOMPLETE_SNAPSHOTS"
    tail = [f["topLevel"] for f in frames[-2:]]
    if any(f["overflow"] for f in tail):
        return "HOLD_TOPLEVEL_UNASSESSED"
    if all(f["tableExact"] or f["componentExact"] for f in tail):
        return "REVIEW_STABLE_TOPLEVEL_EXACT_NOT_FORMAL_IDENTITY"
    if any(f["tableExact"] or f["componentExact"] for f in tail):
        return "HOLD_TRANSIENT_TOPLEVEL_EXACT"
    return "HOLD_NO_BOUND_TOPLEVEL_TITLE"

def probe(scraper_raw):
    funcs = ab.aa.y.frozen_functions(scraper_raw)
    result = dict(listHttp=None, listFinalAllowed=False, listCounts=None,
                  samples=[], navigationCount=0, sourceException=False, sourceErrorKind="NONE")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=False, service_workers="block")
        def guard(route):
            if route.request.is_navigation_request() and not ab.aa.x.allowed(route.request.url):
                route.abort("blockedbyclient")
            else:
                route.continue_()
        list_page = context.new_page()
        list_page.route("**/*", guard)
        candidates = []
        try:
            result["navigationCount"] += 1
            response = list_page.goto(ab.aa.x.ENTRY, wait_until="domcontentloaded", timeout=18000)
            result["listHttp"] = response.status if response else None
            result["listFinalAllowed"] = ab.aa.x.allowed(list_page.url)
            if response and result["listHttp"] == 200 and result["listFinalAllowed"]:
                body = response.body()
                if len(body) <= ab.aa.MAX_BYTES:
                    candidates, result["listCounts"] = ab.aa.z.list_candidates(body, funcs, ab.aa.x.allowed)
        except Exception as exc:
            result["sourceException"], result["sourceErrorKind"] = True, ab.aa.z.error_kind(exc)
        finally:
            list_page.close()
        counts = result["listCounts"]
        if counts and not counts["unsafeSelected"] and not counts["nonCanonical"]:
            for index, (pid, title, url) in enumerate(candidates[:MAX_DETAILS]):
                sample = dict(sampleIndex=index, http=None, finalAllowed=False,
                              sameProductId=False, redirects=0, frames=[],
                              sourceException=False, sourceErrorKind="NONE")
                detail = context.new_page()
                detail.route("**/*", guard)
                try:
                    result["navigationCount"] += 1
                    response = detail.goto(url, wait_until="domcontentloaded", timeout=18000)
                    sample["http"] = response.status if response else None
                    prev = response.request.redirected_from if response else None
                    while prev and sample["redirects"] <= 3:
                        sample["redirects"] += 1
                        prev = prev.redirected_from
                    sample["finalAllowed"] = ab.aa.x.allowed(detail.url) and sample["redirects"] <= 2
                    sample["sameProductId"] = ab.aa.z.product_id(detail.url, ab.aa.x.allowed) == pid
                    if sample["http"] == 200 and sample["finalAllowed"] and sample["sameProductId"]:
                        for n in range(SNAPSHOTS):
                            if n:
                                detail.wait_for_timeout(650)
                            html = detail.content()
                            sample["frames"].append(dict(
                                ready=detail.evaluate("document.readyState"),
                                topLevel=top_level_snapshot(html, title)))
                except Exception as exc:
                    sample["sourceException"], sample["sourceErrorKind"] = True, ab.aa.z.error_kind(exc)
                finally:
                    detail.close()
                sample["decision"] = classify(sample)
                result["samples"].append(sample)
        context.close()
        browser.close()
    return result

def decide(result):
    if result["sourceException"]:
        return "HOLD_LIST_SOURCE_" + result["sourceErrorKind"]
    if result["listHttp"] != 200 or not result["listFinalAllowed"]:
        return "HOLD_LIST_ACCESS"
    counts = result["listCounts"]
    if not counts or counts["unsafeSelected"] or counts["nonCanonical"] or counts["provisionalObjects"] < 2:
        return "HOLD_LIST_CANDIDATES"
    if len(result["samples"]) != MAX_DETAILS:
        return "HOLD_SAMPLE_COUNT"
    return "HOLD_TOPLEVEL_TITLE_NOT_FORMALLY_VERIFIED"

def main():
    parser = argparse.ArgumentParser()
    for key in ("status", "parent", "scraper", "out"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--live-kham", action="store_true")
    args = parser.parse_args()
    if not args.live_kham:
        raise ValueError("HOLD_EXPLICIT_LIVE_SCOPE")
    status_raw, parent_raw, scraper_raw = (
        Path(getattr(args, key)).read_bytes() for key in ("status", "parent", "scraper"))
    verify_parent(status_raw, parent_raw, scraper_raw)
    out = Path(args.out).resolve()
    if out != (Path.cwd() / "p30-l9ac-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result = probe(scraper_raw)
    result.update(kind=KIND, parentHead=PARENT_HEAD, parentArtifactSHA256=PARENT_ARTIFACT_SHA,
                  parentReportSHA256=sha(parent_raw), formalStatusBlob=ab.aa.STATUS_BLOB,
                  frozenScraperBlob=ab.aa.SOURCE_BLOB, decision=decide(result),
                  formalVerifiedEventIdentity=0, acceptedFields=0, goldenAccepted=0,
                  published=False, productionModified=False, writerExecuted=False,
                  schedulerExecuted=False, notifierExecuted=False, mergeExecuted=False,
                  rawHtmlPersisted=False, rawUrlsPersisted=False, rawTitlesPersisted=False,
                  rawProductIdsPersisted=False, cookiesPersisted=False,
                  screenshotsPersisted=False, releaseState=RELEASE)
    out.mkdir(exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    (out / "kham_toplevel_title.json").write_bytes(raw)
    manifest = dict(kind="EVENTRADAR_P30_L9AC_SHA_MANIFEST_V1",
                    filesSHA256={"kham_toplevel_title.json": sha(raw)},
                    releaseState=RELEASE, published=False)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("L9AC_KHAM", json.dumps(dict(listHttp=result["listHttp"],
          candidates=(result["listCounts"] or {}).get("provisionalObjects", 0),
          samples=[dict(http=s["http"], decision=s["decision"],
                        tail=s["frames"][-1]["topLevel"] if s["frames"] else None)
                   for s in result["samples"]], decision=result["decision"])))
    print("HOLD_L9AC_NO_IDENTITY_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
