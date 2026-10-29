#!/usr/bin/env python3
"""P30-L9-AA: bounded Kham non-H1/H2 title-region topology; review only.
One public list and <=2 same-Product-ID detail navigations. Persist counts,
reason codes and booleans only; never persist titles, URLs, HTML or IDs.
"""
import argparse
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import p30_l9z_kham_list_detail_identity as z
from scripts import p30_l9y_kham_event_object_boundary as y
from scripts import p30_l9x_kham_original_parser_parity as x

KIND = "EVENTRADAR_P30_L9AA_KHAM_TITLE_TOPOLOGY_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "18d9a28c4b3235a5aa7b722b447f7588a707911d"
PARENT_SHA = "d1858976888b257af0642a9832651218ca3b7d29c8099df6c753f099c28f5125"
SOURCE_BLOB = "98eddeafb497718c51aa81c6a150e9a5e1e687a8"
STATUS_BLOB = "e19ca37c4c80c10b7278d0813b8ff1047535d124"
MAX_BYTES = 1500000
MAX_ZONE_NODES = 250
MAX_DETAILS = 2
SNAPSHOTS = 6
OUT = "p30-l9aa-evidence"
ZONES = (
    ("headTitle", "head > title", "text", False),
    ("openGraph", "head meta[property='og:title']", "content", False),
    ("twitter", "head meta[name='twitter:title']", "content", False),
    ("h3h6", "h3,h4,h5,h6", "text", True),
    ("semanticName", "main [itemprop='name'],article [itemprop='name'],[role='main'] [itemprop='name']", "text", True),
    ("scopedTitle", "main [class*='title'],article [class*='title'],#content [class*='title'],.detail [class*='title'],[role='main'] [class*='title'],main [id*='title'],article [id*='title']", "text", True),
    ("scopedText", "main p,main span,article p,article span,#content p,#content span,.detail p,.detail span", "text", True),
    ("scopedImageAlt", "main img[alt],article img[alt],#content img[alt],.detail img[alt]", "alt", False),
)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify_parent(status_bytes, parent_bytes, scraper_bytes):
    if z.git_blob(status_bytes) != STATUS_BLOB:
        raise ValueError("HOLD_FORMAL_STATUS_SHA")
    if z.git_blob(scraper_bytes) != SOURCE_BLOB:
        raise ValueError("HOLD_FROZEN_SOURCE_SHA")
    if sha(parent_bytes) != PARENT_SHA:
        raise ValueError("HOLD_L9Z_PARENT_REPORT_SHA")
    try:
        status, parent = json.loads(status_bytes), json.loads(parent_bytes)
        if status["production"]["eventFeedReleaseState"] != RELEASE or status["production"]["goldenAccepted"] != 0:
            raise ValueError("HOLD_FORMAL_RELEASE")
        if parent["kind"] != z.KIND or parent["releaseState"] != RELEASE:
            raise ValueError("HOLD_L9Z_PARENT_KIND")
        if parent["decision"] != "HOLD_DETAIL_IDENTITY_OR_TITLE_PARITY":
            raise ValueError("HOLD_L9Z_PARENT_DECISION")
        if len(parent["samples"]) != 2 or any(s["decision"] != "HOLD_NO_H1H2_CANDIDATE" for s in parent["samples"]):
            raise ValueError("HOLD_L9Z_PARENT_SAMPLES")
        if parent["formalVerifiedEventIdentity"] != 0 or parent["acceptedFields"] != 0 or parent["published"] is not False:
            raise ValueError("HOLD_L9Z_PARENT_PUBLICATION")
    except (KeyError, TypeError, IndexError, json.JSONDecodeError) as exc:
        raise ValueError("HOLD_MALFORMED_PARENT") from exc
    return True

def region_snapshot(html, expected, ready):
    """Strict full-title NFC equality in named semantic DOM regions, never regex.
    Metadata/image alt are hints only. No candidate text is returned or logged.
    """
    if not isinstance(html, (str, bytes)) or len(html.encode("utf-8") if isinstance(html, str) else html) > MAX_BYTES:
        raise ValueError("HOLD_HTML_SIZE")
    expected = z.normalize_title(expected)
    if not expected:
        raise ValueError("HOLD_EMPTY_EXPECTED_TITLE")
    soup = BeautifulSoup(html, "html.parser")
    counts, matches = {}, {}
    overflow = False
    for name, selector, attr, _visible in ZONES:
        nodes = soup.select(selector)
        counts[name] = min(len(nodes), MAX_ZONE_NODES + 1)
        if len(nodes) > MAX_ZONE_NODES:
            overflow = True
            matches[name] = 0
            continue
        texts = [n.get(attr, "") if attr != "text" else n.get_text(" ", strip=True) for n in nodes]
        matches[name] = sum(z.normalize_title(str(v)) == expected for v in texts)
    return {"ready": ready, "candidateCounts": counts, "exactMatches": matches,
            "zoneOverflow": overflow, "iframeCount": min(len(soup.select("iframe")), 20),
            "h1h2Count": min(len(soup.select("h1,h2")), 81),
            "mainScopeCount": min(len(soup.select("main,article,[role='main'],#content,.detail")), 81)}

def classify(sample):
    if sample.get("sourceException"):
        return "HOLD_DETAIL_SOURCE_" + sample.get("sourceErrorKind", "OTHER")
    if not sample.get("finalAllowed"):
        return "HOLD_UNSAFE_DETAIL_FINAL"
    if not sample.get("sameProductId"):
        return "HOLD_DETAIL_PRODUCT_ID_DRIFT"
    if sample.get("http") != 200:
        return "HOLD_DETAIL_HTTP_NOT_200"
    frames = sample.get("frames") or []
    if len(frames) != SNAPSHOTS:
        return "HOLD_INCOMPLETE_SNAPSHOTS"
    if any(f["zoneOverflow"] for f in frames):
        return "HOLD_REGION_CAP"
    tail = frames[-3:]
    if any(f["ready"] != "complete" for f in tail):
        return "HOLD_RENDER_NOT_COMPLETE"
    visible = ("h3h6", "semanticName", "scopedTitle", "scopedText")
    if all(sum(f["exactMatches"][k] for k in visible) == 1 for f in tail):
        return "REVIEW_ONE_EXACT_VISIBLE_REGION_NO_IDENTITY_PROMOTION"
    if any(sum(f["exactMatches"][k] for k in visible) > 1 for f in tail):
        return "HOLD_MULTIPLE_EXACT_VISIBLE_REGIONS"
    if any(sum(f["exactMatches"][k] for k in ("headTitle", "openGraph", "twitter", "scopedImageAlt")) for f in tail):
        return "HOLD_METADATA_OR_IMAGE_ONLY"
    if any(f["iframeCount"] for f in tail):
        return "HOLD_NO_EXACT_REGION_IFRAME_PRESENT"
    return "HOLD_NO_EXACT_TITLE_REGION"

def decide(probe):
    if probe.get("sourceException"):
        return "HOLD_LIST_SOURCE_" + probe.get("sourceErrorKind", "OTHER")
    if not probe.get("listFinalAllowed"):
        return "HOLD_UNSAFE_LIST_FINAL"
    if probe.get("listHttp") != 200:
        return "HOLD_LIST_HTTP_NOT_200"
    counts = probe.get("listCounts")
    if not counts or counts["unsafeSelected"] or counts["nonCanonical"] or counts["provisionalObjects"] < 2:
        return "HOLD_LIST_IDENTITY_OR_COUNT"
    if len(probe["samples"]) != MAX_DETAILS:
        return "HOLD_DETAIL_SAMPLE_COUNT"
    if all(s["decision"] == "REVIEW_ONE_EXACT_VISIBLE_REGION_NO_IDENTITY_PROMOTION" for s in probe["samples"]):
        return "REVIEW_TWO_REGION_MATCHES_NO_FORMAL_PROMOTION"
    return "HOLD_TITLE_REGION_TOPOLOGY_UNRESOLVED"

def probe(funcs):
    from playwright.sync_api import sync_playwright
    out = dict(listHttp=None, listFinalAllowed=False, listCounts=None, samples=[],
               navigationCount=0, sourceException=False, sourceErrorKind="NONE")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=False, service_workers="block")
        def guard(route):
            if route.request.is_navigation_request() and not x.allowed(route.request.url):
                route.abort("blockedbyclient")
            else:
                route.continue_()
        page = context.new_page()
        page.route("**/*", guard)
        candidates = []
        try:
            out["navigationCount"] += 1
            response = page.goto(x.ENTRY, wait_until="domcontentloaded", timeout=18000)
            out["listHttp"] = response.status if response else None
            out["listFinalAllowed"] = x.allowed(page.url)
            if response and out["listHttp"] == 200 and out["listFinalAllowed"]:
                body = response.body()
                if len(body) <= MAX_BYTES:
                    candidates, out["listCounts"] = z.list_candidates(body, funcs, x.allowed)
        except Exception as exc:
            out["sourceException"], out["sourceErrorKind"] = True, z.error_kind(exc)
        finally:
            page.close()
        if out["listCounts"] and not out["listCounts"]["unsafeSelected"] and not out["listCounts"]["nonCanonical"]:
            for index, (pid, title, url) in enumerate(candidates[:MAX_DETAILS]):
                d = dict(sampleIndex=index, http=None, finalAllowed=False, sameProductId=False,
                         frames=[], redirects=0, sourceException=False, sourceErrorKind="NONE")
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
                    d["finalAllowed"] = x.allowed(detail.url) and d["redirects"] <= 2
                    d["sameProductId"] = z.product_id(detail.url, x.allowed) == pid
                    if d["http"] == 200 and d["finalAllowed"] and d["sameProductId"]:
                        for n in range(SNAPSHOTS):
                            if n:
                                detail.wait_for_timeout(650)
                            html = detail.content()
                            d["frames"].append(region_snapshot(html, title, detail.evaluate("document.readyState")))
                except Exception as exc:
                    d["sourceException"], d["sourceErrorKind"] = True, z.error_kind(exc)
                finally:
                    detail.close()
                d["decision"] = classify(d)
                out["samples"].append(d)
        context.close()
        browser.close()
    return out

def main():
    ap = argparse.ArgumentParser()
    for name in ("status", "parent", "scraper", "out"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--live-kham", action="store_true")
    args = ap.parse_args()
    if not args.live_kham:
        raise ValueError("HOLD_EXPLICIT_LIVE_SCOPE")
    status, parent, scraper = (Path(getattr(args, k)).read_bytes() for k in ("status", "parent", "scraper"))
    verify_parent(status, parent, scraper)
    result = probe(y.frozen_functions(scraper))
    result.update(kind=KIND, parentHead=PARENT, parentReportSHA256=sha(parent),
                  formalStatusBlob=STATUS_BLOB, frozenScraperBlob=SOURCE_BLOB,
                  decision=decide(result), formalVerifiedEventIdentity=0,
                  acceptedFields=0, goldenAccepted=0, published=False,
                  productionModified=False, writerExecuted=False, schedulerExecuted=False,
                  notifierExecuted=False, mergeExecuted=False, rawHtmlPersisted=False,
                  rawUrlsPersisted=False, rawTitlesPersisted=False, rawProductIdsPersisted=False,
                  cookiesPersisted=False, screenshotsPersisted=False, releaseState=RELEASE)
    out = Path(args.out).resolve()
    if out != (Path.cwd() / OUT).resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    out.mkdir(exist_ok=True)
    data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    (out / "kham_title_topology.json").write_bytes(data)
    manifest = {"kind": "EVENTRADAR_P30_L9AA_SHA_MANIFEST_V1",
                "filesSHA256": {"kham_title_topology.json": sha(data)},
                "releaseState": RELEASE, "published": False}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("L9AA_KHAM", json.dumps({
        "listHttp": result["listHttp"], "candidateCount": (result["listCounts"] or {}).get("provisionalObjects", 0),
        "samples": [{"http": s["http"], "decision": s["decision"],
                     "tailMatches": s["frames"][-1]["exactMatches"] if s["frames"] else {}}
                    for s in result["samples"]], "decision": result["decision"]}, ensure_ascii=False))
    print("HOLD_L9AA_NO_FORMAL_IDENTITY_NO_FIELDS_NO_PUBLICATION")

if __name__ == "__main__":
    main()
