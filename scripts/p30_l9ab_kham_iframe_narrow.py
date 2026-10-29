#!/usr/bin/env python3
"""P30-L9-AB: read-only, bounded Kham iframe origin and narrow-title diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import p30_l9aa_kham_title_topology as aa

KIND = "EVENTRADAR_P30_L9AB_KHAM_IFRAME_NARROW_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT_HEAD = "86ef4fffb67824f9981bba984ecadb62eca93631"
PARENT_ARTIFACT_SHA = "4b1b9d830cf947202798f9c601d9c69c194af35c4b64c3320dbe5fd04d4a9075"
MAX_IFRAMES = 6
MAX_DETAILS = 2
SNAPSHOTS = 4
NARROW_SELECTOR = ("#content h3,#content h4,#content h5,#content h6,"
                   ".detail h3,.detail h4,.detail h5,main h3,main h4,main h5,"
                   "#content [itemprop='name'],main [itemprop='name'],"
                   "#content [class*='title'],.detail [class*='title']")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify_parent(status_raw, parent_raw, scraper_raw):
    if aa.z.git_blob(status_raw) != aa.STATUS_BLOB:
        raise ValueError("HOLD_STATUS_BLOB")
    if aa.z.git_blob(scraper_raw) != aa.SOURCE_BLOB:
        raise ValueError("HOLD_SCRAPER_BLOB")
    try:
        status, parent = json.loads(status_raw), json.loads(parent_raw)
        assert status["production"]["eventFeedReleaseState"] == RELEASE
        assert status["production"]["goldenAccepted"] == 0
        assert parent["kind"] == aa.KIND and parent["releaseState"] == RELEASE
        assert parent["decision"] == "HOLD_TITLE_REGION_TOPOLOGY_UNRESOLVED"
        assert len(parent["samples"]) == 2
        assert parent["formalVerifiedEventIdentity"] == parent["acceptedFields"] == 0
        assert parent["published"] is False
    except (AssertionError, ValueError, KeyError, TypeError, IndexError) as exc:
        raise ValueError("HOLD_PARENT_CONTRACT") from exc
    return True

def narrow_snapshot(html, expected):
    if len(html.encode("utf-8")) > aa.MAX_BYTES:
        return {"count": None, "matches": None, "overflow": True}
    nodes = BeautifulSoup(html, "html.parser").select(NARROW_SELECTOR)
    if len(nodes) > aa.MAX_ZONE_NODES:
        return {"count": aa.MAX_ZONE_NODES + 1, "matches": None, "overflow": True}
    expected = aa.z.normalize_title(expected)
    return {"count": len(nodes),
            "matches": sum(aa.z.normalize_title(n.get_text(" ", strip=True)) == expected for n in nodes),
            "overflow": False}

def iframe_topology(page, expected):
    """Never inspect unrelated/cross-origin frames, navigate frames, or persist URLs."""
    origin = urlsplit(page.url)
    frames = page.frames[1:]
    out = dict(total=min(len(frames), MAX_IFRAMES + 1),
               capped=len(frames) > MAX_IFRAMES, opaque=0, unrelated=0,
               sameOrigin=0, sameOriginAllowed=0, readable=0,
               unreadable=0, overCap=0, exactBounded=0)
    for child in frames[:MAX_IFRAMES]:
        url = child.url
        if not url or url.startswith(("about:", "data:", "blob:")):
            out["opaque"] += 1
            continue
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != origin.hostname:
            out["unrelated"] += 1
            continue
        out["sameOrigin"] += 1
        if not aa.x.allowed(url):
            continue
        out["sameOriginAllowed"] += 1
        try:
            html = child.content()
            if len(html.encode("utf-8")) > aa.MAX_BYTES:
                out["overCap"] += 1
                continue
            snap = aa.region_snapshot(html, expected, child.evaluate("document.readyState"))
            out["readable"] += 1
            if snap["zoneOverflow"]:
                out["overCap"] += 1
                continue
            out["exactBounded"] += sum(snap["exactMatches"][k] for k in
                                       ("h3h6", "semanticName", "scopedTitle", "scopedText"))
        except Exception:
            out["unreadable"] += 1
    return out

def classify(sample):
    if sample["sourceException"]:
        return "HOLD_DETAIL_SOURCE_" + sample["sourceErrorKind"]
    if not sample["finalAllowed"] or not sample["sameProductId"] or sample["http"] != 200:
        return "HOLD_DETAIL_IDENTITY_OR_HTTP"
    frames = sample["frames"]
    if len(frames) != SNAPSHOTS:
        return "HOLD_INCOMPLETE_FRAMES"
    tail = frames[-2:]
    if any(f["iframeTopology"]["exactBounded"] for f in tail):
        return "REVIEW_SAME_ORIGIN_IFRAME_EXACT_NOT_IDENTITY"
    if any(f["broad"]["zoneOverflow"] for f in tail):
        if any(f["narrow"]["overflow"] for f in tail):
            return "HOLD_NARROW_UNASSESSED"
        if any(f["narrow"]["matches"] for f in tail):
            return "REVIEW_NARROW_EXACT_BROAD_UNASSESSED"
        return "HOLD_BROAD_OVERFLOW_NARROW_ZERO_NOT_IDENTITY"
    if any(f["iframeTopology"]["sameOriginAllowed"] for f in tail):
        return "HOLD_SAME_ORIGIN_IFRAME_NO_EXACT"
    return "HOLD_NO_SOURCE_BOUND_IFRAME_TITLE"

def probe(scraper_raw):
    funcs = aa.y.frozen_functions(scraper_raw)
    out = dict(listHttp=None, listFinalAllowed=False, listCounts=None,
               samples=[], navigationCount=0, sourceException=False, sourceErrorKind="NONE")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=False, service_workers="block")
        def guard(route):
            if route.request.is_navigation_request() and not aa.x.allowed(route.request.url):
                route.abort("blockedbyclient")
            else:
                route.continue_()
        page = context.new_page()
        page.route("**/*", guard)
        candidates = []
        try:
            out["navigationCount"] += 1
            response = page.goto(aa.x.ENTRY, wait_until="domcontentloaded", timeout=18000)
            out["listHttp"] = response.status if response else None
            out["listFinalAllowed"] = aa.x.allowed(page.url)
            if response and out["listHttp"] == 200 and out["listFinalAllowed"]:
                body = response.body()
                if len(body) <= aa.MAX_BYTES:
                    candidates, out["listCounts"] = aa.z.list_candidates(body, funcs, aa.x.allowed)
        except Exception as exc:
            out["sourceException"], out["sourceErrorKind"] = True, aa.z.error_kind(exc)
        finally:
            page.close()
        if out["listCounts"] and not out["listCounts"]["unsafeSelected"] and not out["listCounts"]["nonCanonical"]:
            for index, (pid, title, url) in enumerate(candidates[:MAX_DETAILS]):
                d = dict(sampleIndex=index, http=None, finalAllowed=False,
                         sameProductId=False, redirects=0, frames=[],
                         sourceException=False, sourceErrorKind="NONE")
                detail = context.new_page()
                detail.route("**/*", guard)
                try:
                    out["navigationCount"] += 1
                    response = detail.goto(url, wait_until="domcontentloaded", timeout=18000)
                    d["http"] = response.status if response else None
                    prev = response.request.redirected_from if response else None
                    while prev and d["redirects"] <= 3:
                        d["redirects"] += 1
                        prev = prev.redirected_from
                    d["finalAllowed"] = aa.x.allowed(detail.url) and d["redirects"] <= 2
                    d["sameProductId"] = aa.z.product_id(detail.url, aa.x.allowed) == pid
                    if d["http"] == 200 and d["finalAllowed"] and d["sameProductId"]:
                        for n in range(SNAPSHOTS):
                            if n:
                                detail.wait_for_timeout(650)
                            html = detail.content()
                            d["frames"].append({
                                "ready": detail.evaluate("document.readyState"),
                                "broad": aa.region_snapshot(html, title, detail.evaluate("document.readyState")),
                                "narrow": narrow_snapshot(html, title),
                                "iframeTopology": iframe_topology(detail, title)})
                except Exception as exc:
                    d["sourceException"], d["sourceErrorKind"] = True, aa.z.error_kind(exc)
                finally:
                    detail.close()
                d["decision"] = classify(d)
                out["samples"].append(d)
        context.close()
        browser.close()
    return out

def decide(out):
    if out["sourceException"]:
        return "HOLD_LIST_SOURCE_" + out["sourceErrorKind"]
    if not out["listFinalAllowed"] or out["listHttp"] != 200:
        return "HOLD_LIST_ACCESS"
    counts = out["listCounts"]
    if not counts or counts["unsafeSelected"] or counts["nonCanonical"] or counts["provisionalObjects"] < 2:
        return "HOLD_LIST_CANDIDATES"
    if len(out["samples"]) != MAX_DETAILS:
        return "HOLD_SAMPLE_COUNT"
    return "HOLD_IFRAME_AND_NARROW_TITLE_NOT_FORMALLY_VERIFIED"

def main():
    p = argparse.ArgumentParser()
    for key in ("status", "parent", "scraper", "out"):
        p.add_argument("--" + key, required=True)
    p.add_argument("--live-kham", action="store_true")
    args = p.parse_args()
    if not args.live_kham:
        raise ValueError("HOLD_EXPLICIT_LIVE_SCOPE")
    status_raw, parent_raw, scraper_raw = (Path(getattr(args, k)).read_bytes()
                                           for k in ("status", "parent", "scraper"))
    verify_parent(status_raw, parent_raw, scraper_raw)
    out = Path(args.out).resolve()
    if out != (Path.cwd() / "p30-l9ab-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result = probe(scraper_raw)
    result.update(kind=KIND, parentHead=PARENT_HEAD, parentArtifactSHA256=PARENT_ARTIFACT_SHA,
                  parentReportSHA256=sha(parent_raw), formalStatusBlob=aa.STATUS_BLOB,
                  frozenScraperBlob=aa.SOURCE_BLOB, decision=decide(result),
                  formalVerifiedEventIdentity=0, acceptedFields=0, goldenAccepted=0,
                  published=False, productionModified=False, writerExecuted=False,
                  schedulerExecuted=False, notifierExecuted=False, mergeExecuted=False,
                  rawHtmlPersisted=False, rawUrlsPersisted=False, rawTitlesPersisted=False,
                  rawProductIdsPersisted=False, cookiesPersisted=False,
                  screenshotsPersisted=False, releaseState=RELEASE)
    out.mkdir(exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    (out / "kham_iframe_narrow.json").write_bytes(raw)
    manifest = {"kind": "EVENTRADAR_P30_L9AB_SHA_MANIFEST_V1",
                "filesSHA256": {"kham_iframe_narrow.json": sha(raw)},
                "releaseState": RELEASE, "published": False}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("L9AB_KHAM", json.dumps({"listHttp": result["listHttp"],
          "candidates": (result["listCounts"] or {}).get("provisionalObjects", 0),
          "samples": [{"http": s["http"], "decision": s["decision"],
                       "tail": s["frames"][-1]["iframeTopology"] if s["frames"] else None}
                      for s in result["samples"]], "decision": result["decision"]}))
    print("HOLD_L9AB_NO_IDENTITY_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
