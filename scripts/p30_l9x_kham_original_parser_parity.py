#!/usr/bin/env python3
"""P30-L9-X: one normal public Kham navigation, exact original selector/filter
stage parity in static and rendered HTML. Structural counts only; NO PUBLISH.
Never persist raw HTML, hrefs, titles, cookies, response bodies or screenshots.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

KIND = "EVENTRADAR_P30_L9X_KHAM_ORIGINAL_PARSER_PARITY_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
ENTRY = "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=205"
PARENT = "9bc37d326ee6e1b698e36061f8323e0894c98ad6"
STATUS_BLOB = "e19ca37c4c80c10b7278d0813b8ff1047535d124"
L7B_SHA = "e07c01a5d36ab0c950c45fb26e5fdd270103b4013bbf62a00c48291fee5f595a"
W_SHA = "2ba90bf6d5e080443b5e01309ae877f3057f9915082b9c3b303c130f0051fa61"
MAX_BYTES = 1500000
MAX_ANCHORS = 1200


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def allowed(url):
    try:
        p = urlparse(url)
        return (p.scheme == "https" and p.hostname in ("kham.com.tw", "www.kham.com.tw")
                and not p.username and not p.password and p.port in (None, 443))
    except ValueError:
        return False


def fix_utk_url(domain, raw_url):
    """Frozen scraper.py:fix_utk_url logic for Kham, source blob pinned by CI."""
    match = re.search(r"PRODUCT_ID=([A-Za-z0-9]+)", raw_url, re.I)
    if match:
        return f"https://{domain}/application/UTK02/UTK0201_.aspx?PRODUCT_ID={match.group(1)}"
    return raw_url


def stages(html):
    """Exact BeautifulSoup selector and PRODUCT_ID gate of frozen fetch_kham.
    This is pre-create_event_obj diagnostic, NOT full production parser execution.
    """
    soup = BeautifulSoup(html, "html.parser")
    all_links = soup.find_all("a", href=True)
    if len(all_links) > MAX_ANCHORS:
        raise ValueError("HOLD_ANCHOR_CAP")
    broad = [a for a in all_links if "UTK0201" in (a.get("href") or "").upper()]
    selected = soup.select('a[href*="UTK0201_"]')
    stats = dict(allAnchors=len(all_links), broadUtkLinks=len(broad),
                 originalSelector=len(selected), missingProductId=0,
                 passedProductIdGate=0, uniqueAfterGate=0,
                 titleTextNonempty=0, titleTextEmpty=0,
                 titleAttributePresent=0, imageAltPresent=0,
                 offsiteSelected=0, duplicateAfterGate=0)
    seen = set()
    for link in selected:
        raw_url = urljoin("https://kham.com.tw", link.get("href"))
        if not allowed(raw_url):
            stats["offsiteSelected"] += 1
            continue
        full_url = fix_utk_url("kham.com.tw", raw_url)
        # Original fetch_kham checks seen, then this exact uppercase gate.
        if full_url in seen:
            stats["duplicateAfterGate"] += 1
            continue
        if "PRODUCT_ID" not in full_url:
            stats["missingProductId"] += 1
            continue
        stats["passedProductIdGate"] += 1
        seen.add(full_url)
        if link.get_text(strip=True):
            stats["titleTextNonempty"] += 1
        else:
            stats["titleTextEmpty"] += 1
        if link.get("title"):
            stats["titleAttributePresent"] += 1
        if link.find("img", alt=True):
            stats["imageAltPresent"] += 1
    stats["uniqueAfterGate"] = len(seen)
    return stats


def decide(http, final_allowed, static, frames):
    if not final_allowed:
        return "HOLD_UNSAFE_FINAL"
    if http != 200:
        return "HOLD_HTTP_NOT_200"
    if static is None or len(frames) != 3:
        return "HOLD_INCOMPLETE_SOURCE"
    if frames[-1]["ready"] != "complete":
        return "HOLD_RENDER_NOT_COMPLETE"
    last = frames[-1]["stages"]
    if frames[-2]["stages"]["originalSelector"] != last["originalSelector"]:
        return "HOLD_RENDER_SELECTOR_UNSTABLE"
    if static["broadUtkLinks"] and not static["originalSelector"]:
        return "REVIEW_CURRENT_ORIGINAL_SELECTOR_ZERO"
    if static["originalSelector"] and not static["passedProductIdGate"]:
        return "REVIEW_CURRENT_ORIGINAL_PRODUCT_ID_GATE_ZERO"
    if static["passedProductIdGate"] and not static["titleTextNonempty"]:
        return "REVIEW_CURRENT_ORIGINAL_ANCHOR_TEXT_ZERO"
    if static["titleTextNonempty"]:
        return "REVIEW_CURRENT_PRE_EVENT_CANDIDATES_HISTORIC_ZERO"
    return "HOLD_NO_CURRENT_SOURCE_CANDIDATES"


def verify_parents(status_bytes, l7b_bytes, w_bytes):
    if git_blob(status_bytes) != STATUS_BLOB:
        raise ValueError("HOLD_STATUS_BLOB")
    if sha(l7b_bytes) != L7B_SHA:
        raise ValueError("HOLD_L7B_SHA")
    status, old, w = map(json.loads, (status_bytes, l7b_bytes, w_bytes))
    if status["production"]["eventFeedReleaseState"] != RELEASE or status["production"]["goldenAccepted"] != 0:
        raise ValueError("HOLD_PRODUCTION_RELEASE")
    old_rows = [x for x in old["platforms"] if x["platform"] == "寬宏"]
    if len(old_rows) != 1 or old_rows[0]["listCandidateCount"] != 0:
        raise ValueError("HOLD_HISTORIC_BASELINE")
    if w["kind"] != "EVENTRADAR_P30_L9W_KHAM_LIST_BOUNDARY_V1" or w["decision"] != "REVIEW_CURRENT_STATIC_DETAIL_LINKS_HISTORIC_ZERO":
        raise ValueError("HOLD_L9W_REPORT")
    if w["staticLinks"]["detailUnique"] != 10 or w["releaseState"] != RELEASE:
        raise ValueError("HOLD_L9W_COUNT")
    return {"historicList": 0, "l9wStaticUrlPattern": 10}


def one_navigation():
    from playwright.sync_api import sync_playwright
    frames = []
    http = None
    redirect_count = 0
    final_allowed = False
    static = None
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
            response = page.goto(ENTRY, wait_until="domcontentloaded", timeout=18000)
            if response:
                http = response.status
                prev = response.request.redirected_from
                while prev and redirect_count <= 4:
                    redirect_count += 1
                    prev = prev.redirected_from
            final_allowed = allowed(page.url) and redirect_count <= 2
            if final_allowed and http == 200 and response:
                length = int(response.headers.get("content-length", "0") or "0")
                if length <= MAX_BYTES:
                    body = response.body()
                    if len(body) <= MAX_BYTES:
                        static = stages(body)
            for i in range(3):
                if i:
                    page.wait_for_timeout(750)
                if final_allowed:
                    # HTML is ephemeral memory only; never written to evidence.
                    frames.append({"ready": page.evaluate("document.readyState"),
                                   "stages": stages(page.content())})
        except Exception:
            pass
        finally:
            context.close()
            browser.close()
    return {"http": http, "redirects": redirect_count,
            "finalAllowed": final_allowed, "static": static, "frames": frames}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-kham", action="store_true")
    for name in ("status", "l7b", "w", "out"):
        ap.add_argument("--" + name, required=True)
    a = ap.parse_args()
    if not a.live_kham:
        raise ValueError("HOLD_EXPLICIT_LIVE_SCOPE")
    history = verify_parents(Path(a.status).read_bytes(), Path(a.l7b).read_bytes(), Path(a.w).read_bytes())
    probe = one_navigation()
    decision = decide(probe["http"], probe["finalAllowed"], probe["static"], probe["frames"])
    result = dict(kind=KIND, platform="寬宏", parentHead=PARENT, sourceEntryId="KHAM_CATEGORY_205",
                  statusBlob=STATUS_BLOB, l7bSHA256=L7B_SHA, l9wZipSHA256=W_SHA,
                  historical=history, navigationCount=1, **probe, decision=decision,
                  sourceTimeDifferenceNotRootCauseProof=True, fullCreateEventObjNotExecuted=True,
                  verifiedEventIdentity=0, acceptedFields=0, goldenAccepted=0,
                  published=False, writerExecuted=False, schedulerExecuted=False,
                  notifierExecuted=False, mergeExecuted=False, productionModified=False,
                  rawHtmlPersisted=False, rawUrlsPersisted=False, rawTitlesPersisted=False,
                  cookiesPersisted=False, screenshotsPersisted=False, releaseState=RELEASE)
    out = Path(a.out).resolve()
    cwd = Path.cwd().resolve()
    if out.parent != cwd or out.name != "p30-l9x-evidence":
        raise ValueError("HOLD_ISOLATED_OUTPUT")
    out.mkdir(exist_ok=True)
    payload = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    (out / "kham_original_parser_parity.json").write_bytes(payload)
    manifest = dict(kind="EVENTRADAR_P30_L9X_SHA_MANIFEST_V1",
                    filesSHA256={"kham_original_parser_parity.json": sha(payload)},
                    releaseState=RELEASE, published=False)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("L9X_KHAM", json.dumps({"http": probe["http"], "decision": decision,
        "static": probe["static"], "rendered": [f["stages"] for f in probe["frames"]]}, ensure_ascii=False))
    print("HOLD_L9X_NO_EVENT_PROMOTION_NO_PUBLICATION")


if __name__ == "__main__":
    main()
