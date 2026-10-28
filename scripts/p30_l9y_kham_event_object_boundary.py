#!/usr/bin/env python3
"""P30-L9-Y: exact frozen Kham event-object boundary, one public navigation.
Only structural counts leave memory. Never persist raw HTML, URLs, titles or cookies.
"""
import argparse
import ast
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import importlib.util

KIND = "EVENTRADAR_P30_L9Y_KHAM_EVENT_OBJECT_BOUNDARY_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "b90a6af4f6bb2bab4a6570a025e7068cd1c69093"
SOURCE_BLOB = "98eddeafb497718c51aa81c6a150e9a5e1e687a8"
STATUS_BLOB = "e19ca37c4c80c10b7278d0813b8ff1047535d124"
MAX_BYTES = 1500000
MAX_ANCHORS = 1200
BASE = Path(__file__).resolve().parents[1]
L9X = BASE / "scripts/p30_l9x_kham_original_parser_parity.py"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def frozen_functions(source):
    """Compile only exact top-level production functions, not scraper.py imports/main."""
    if git_blob(source) != SOURCE_BLOB:
        raise ValueError("HOLD_FROZEN_SCRAPER_SHA")
    tree = ast.parse(source.decode("utf-8-sig"))
    names = ("fix_utk_url", "safe_get_text", "get_event_category_from_title", "create_event_obj")
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in selected} != set(names):
        raise ValueError("HOLD_MISSING_FROZEN_FUNCTION")
    namespace = {"re": re, "datetime": datetime, "timedelta": timedelta, "timezone": timezone}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "frozen_scraper_functions", "exec"), namespace)
    return namespace

def parent_check(status_bytes, parent_bytes):
    if git_blob(status_bytes) != STATUS_BLOB:
        raise ValueError("HOLD_FORMAL_STATUS_SHA")
    status = json.loads(status_bytes)
    if status["production"]["eventFeedReleaseState"] != RELEASE or status["production"]["goldenAccepted"] != 0:
        raise ValueError("HOLD_PRODUCTION_RELEASE")
    p = json.loads(parent_bytes)
    if p.get("kind") != "EVENTRADAR_P30_L9X_KHAM_ORIGINAL_PARSER_PARITY_V1":
        raise ValueError("HOLD_PARENT_KIND")
    if p["releaseState"] != RELEASE or p["decision"] != "REVIEW_CURRENT_PRE_EVENT_CANDIDATES_HISTORIC_ZERO":
        raise ValueError("HOLD_PARENT_DECISION")
    if p["static"]["passedProductIdGate"] != 10 or p["static"]["titleTextNonempty"] != 10:
        raise ValueError("HOLD_PARENT_COUNT")
    return True

def stages(html, funcs, allowed):
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", href=True)
    if len(anchors) > MAX_ANCHORS:
        raise ValueError("HOLD_ANCHOR_CAP")
    selected = soup.select('a[href*="UTK0201_"]')
    d = dict(allAnchors=len(anchors), selected=len(selected), productGate=0,
             unsafeLinks=0, duplicateAfterAccepted=0, emptyRawTitle=0,
             preObject=0, acceptedObjects=0, rejectedObjects=0,
             exactNoiseRejected=0, normalizedTitle=0, shortOrNumericRejected=0,
             otherRejected=0)
    seen = set()
    for a in selected:
        raw = urljoin("https://kham.com.tw", a.get("href"))
        if not allowed(raw):
            d["unsafeLinks"] += 1
            continue
        full = funcs["fix_utk_url"]("kham.com.tw", raw)
        if not allowed(full):
            d["unsafeLinks"] += 1
            continue
        if full in seen:
            d["duplicateAfterAccepted"] += 1
            continue
        if "PRODUCT_ID" not in full:
            continue
        d["productGate"] += 1
        title = funcs["safe_get_text"](a)
        if not title:
            d["emptyRawTitle"] += 1
        d["preObject"] += 1
        ev = funcs["create_event_obj"](title, full, "寬宏", None)
        if ev:
            if ev["title"] != title:
                d["normalizedTitle"] += 1
            d["acceptedObjects"] += 1
            seen.add(full)
        else:
            d["rejectedObjects"] += 1
            if title and len(title.strip()) >= 2 and not title.strip().isdigit():
                # Includes exact-noise and normalization-to-empty; no title persisted.
                d["exactNoiseRejected"] += 1 if title.strip() in NOISE_EXACT else 0
                d["otherRejected"] += 0 if title.strip() in NOISE_EXACT else 1
            else:
                d["shortOrNumericRejected"] += 1
    if d["preObject"] != d["acceptedObjects"] + d["rejectedObjects"]:
        raise ValueError("HOLD_OBJECT_ACCOUNTING")
    return d

# Frozen exact-match noise tokens for aggregate reason attribution only; not a substitute parser.
NOISE_EXACT = {"立即購票", "詳細內容", "Read More", "活動詳情", "查看更多", "已結束", "報名",
               "詳細資訊", "購票", "More", "None", "活動介紹", "Traffic", "更多詳情",
               "其他活動", "開放時間", "交通資訊", "當前頁面", "Current Page",
               "Go to page", "看更多", "查看全部", "FamiTicket全網購票網", "首頁",
               "找活動", "下一頁", "廣告版位出租", "隱私權政策", "較舊的文章",
               "詳細介紹", "回首頁", "網站導覽", "兩側門廳", "中央通廊",
               "服務台", "堂景介紹", "租借", "全票", "優待票", "建立活動",
               "Facebook", "Instagram", "聯絡我們", "關於我們", "全台週末活動",
               "VIVE EAGLE", "Uncategorized", "親子運動", "展覽活動",
               "科學益智", "藝術創作", "5-6歲", "7-8歲", "9-10歲",
               "11-12歲", "兒童營隊"}

def decide(probe):
    if not probe["finalAllowed"]:
        return "HOLD_UNSAFE_FINAL"
    if probe["http"] != 200:
        return "HOLD_HTTP_NOT_200"
    if probe["static"] is None or probe["rendered"] is None:
        return "HOLD_INCOMPLETE_SOURCE"
    if probe["static"]["unsafeLinks"] or probe["rendered"]["unsafeLinks"]:
        return "HOLD_UNSAFE_LINKS"
    if probe["static"]["acceptedObjects"] == 0:
        return "REVIEW_CURRENT_POST_OBJECT_ZERO"
    if probe["static"]["rejectedObjects"] > 0:
        return "REVIEW_CURRENT_MIXED_OBJECT_FILTERING"
    return "REVIEW_CURRENT_PROVISIONAL_OBJECTS_HISTORIC_ZERO"

def one_navigation(funcs, allowed, entry):
    from playwright.sync_api import sync_playwright
    probe = dict(http=None, redirects=0, finalAllowed=False, static=None, rendered=None,
                 navigationCount=1)
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
            response = page.goto(entry, wait_until="domcontentloaded", timeout=18000)
            if response:
                probe["http"] = response.status
                prev = response.request.redirected_from
                while prev and probe["redirects"] <= 3:
                    probe["redirects"] += 1
                    prev = prev.redirected_from
            probe["finalAllowed"] = allowed(page.url) and probe["redirects"] <= 2
            if response and probe["http"] == 200 and probe["finalAllowed"]:
                raw = response.body()
                if len(raw) <= MAX_BYTES:
                    probe["static"] = stages(raw, funcs, allowed)
                try:
                    page.wait_for_load_state("load", timeout=10000)
                except Exception:
                    pass
                rendered = page.content()
                if len(rendered.encode("utf-8")) <= MAX_BYTES:
                    probe["rendered"] = stages(rendered, funcs, allowed)
        except Exception:
            pass
        finally:
            context.close()
            browser.close()
    return probe

def main():
    ap = argparse.ArgumentParser()
    for key in ("status", "parent", "scraper", "out"):
        ap.add_argument("--" + key, required=True)
    ap.add_argument("--live-kham", action="store_true")
    args = ap.parse_args()
    if not args.live_kham:
        raise ValueError("HOLD_EXPLICIT_LIVE_SCOPE")
    status = Path(args.status).read_bytes()
    previous = Path(args.parent).read_bytes()
    parent_check(status, previous)
    funcs = frozen_functions(Path(args.scraper).read_bytes())
    spec = importlib.util.spec_from_file_location("l9x", L9X)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    probe = one_navigation(funcs, module.allowed, module.ENTRY)
    decision = decide(probe)
    result = dict(kind=KIND, platform="寬宏", parentHead=PARENT,
                  frozenScraperBlob=SOURCE_BLOB, formalStatusBlob=STATUS_BLOB,
                  parentReportSHA256=sha(previous), **probe, decision=decision,
                  provisionalNotVerified=True, historicRootCauseUnproven=True,
                  verifiedEventIdentity=0, acceptedFields=0, goldenAccepted=0,
                  published=False, writerExecuted=False, schedulerExecuted=False,
                  notifierExecuted=False, mergeExecuted=False, productionModified=False,
                  rawHtmlPersisted=False, rawUrlsPersisted=False, rawTitlesPersisted=False,
                  cookiesPersisted=False, screenshotsPersisted=False, releaseState=RELEASE)
    out = Path(args.out).resolve()
    if out != (Path.cwd() / "p30-l9y-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    out.mkdir(exist_ok=True)
    payload = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    (out / "kham_event_object_boundary.json").write_bytes(payload)
    manifest = {"kind": "EVENTRADAR_P30_L9Y_SHA_MANIFEST_V1",
                "filesSHA256": {"kham_event_object_boundary.json": sha(payload)},
                "releaseState": RELEASE, "published": False}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("L9Y_KHAM", json.dumps({"http": probe["http"], "decision": decision,
                                 "static": probe["static"], "rendered": probe["rendered"]},
                                ensure_ascii=False))
    print("HOLD_L9Y_NO_IDENTITY_NO_FIELDS_NO_PUBLICATION")

if __name__ == "__main__":
    main()
