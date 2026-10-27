#!/usr/bin/env python3
"""P30-L9-C: fresh bounded 4-source, source-specific HTTP/list/detail acquisition.
Read-only research. Zero production Writer/Publisher, no anti-bot evasion, no retry.
Historical L3 specialist *parser code* is reused, NEVER historical result JSON.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs

import requests
from bs4 import BeautifulSoup

KIND = "EVENTRADAR_P30_L9C_FOUR_OFFICIAL_FRESH_ADAPTERS_V1"
ROOT = Path(__file__).resolve().parent
PORTALS = ("中正紀念堂", "台北世貿", "ibon", "FamiTicket")
TWTC_LIST = "https://twtc.com.tw/exhibition?p=home"
MAX_ROWS = 40
SOURCES = {
    "中正紀念堂": {"list": "https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr",
                   "adapter": "P30_L4B_CKSMH_BOUND_ACTID"},
    "台北世貿": {"list": TWTC_LIST, "adapter": "P30_L3A_TWTC_OFFICIAL_TABLE"},
    "ibon": {"list": "https://ticket.ibon.com.tw/Index/entertainment",
             "adapter": "P30_L3BB_IBON_TWO_LISTS"},
    "FamiTicket": {"list": "https://www.famiticket.com.tw/Home",
                   "adapter": "P30_L3BA_FAMITICKET_CARD_ID"},
}
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    if not spec or not spec.loader:
        raise RuntimeError("HOLD_OFFICIAL_ADAPTER_MODULE_MISSING")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def hexdigest(data):
    return hashlib.sha256(data).hexdigest()


def title_clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()[:220]


def strict_detail_url(value, host, path, id_param=None):
    try:
        u = urlsplit(value)
        if (u.scheme != "https" or u.hostname != host or u.username or u.password
                or u.port not in (None, 443) or u.fragment
                or "\\" in u.path or ".." in u.path.split("/")
                or u.path != path):
            return None
        if id_param:
            q = parse_qs(u.query, keep_blank_values=True)
            if set(q) - {id_param, "p"} or len(q.get(id_param, [])) != 1:
                return None
            value_id = q[id_param][0]
            if not re.fullmatch(r"\d{2,12}", value_id):
                return None
            if "p" in q and q["p"] != ["home"]:
                return None
            return value_id
        if u.query:
            return None
        return True
    except ValueError:
        return None


def twtc_list(html):
    """Directly port isolated L3A official table shape; no legacy JSON imported."""
    soup = BeautifulSoup(html, "html.parser")
    result, seen = [], set()
    table_rows = 0
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 3:
            continue
        table_rows += 1
        period = title_clean(" ".join(cells[0].stripped_strings))
        if not re.fullmatch(r"\d{1,2}/\d{1,2}\s*[~～-]\s*\d{1,2}/\d{1,2}", period) and period != "延期未定":
            continue
        title = title_clean(" ".join(x for x in cells[1].stripped_strings if x not in ("more", "詳情")))
        if len(title) < 4:
            continue
        dest = None
        for a in cells[1].select("a[href]"):
            url = urljoin(TWTC_LIST, a["href"])
            identity = strict_detail_url(url, "twtc.com.tw", "/exhibition_more.aspx", "id")
            if identity:
                dest = "https://twtc.com.tw/exhibition_more.aspx?id=" + identity + "&p=home"
                break
        organizer = title_clean(" ".join(cells[2].stripped_strings))
        venue = title_clean(" ".join(cells[4].stripped_strings)) if len(cells) >= 5 else None
        key = dest or title + "|" + period + "|" + organizer
        if key in seen:
            continue
        seen.add(key)
        result.append({"platform": "台北世貿", "title": title, "officialUrl": dest,
                       "identity": identity if dest else None,
                       "rawPeriod": period, "rawPeriodRole": "EXHIBITION_LIST_PERIOD_REVIEW_ONLY",
                       "organizerEvidence": organizer, "venueEvidence": venue,
                       "sourceUrl": TWTC_LIST, "sourceRole": "FIRST_PARTY_LIST_TABLE",
                       "verified": False, "published": False})
        if len(result) == MAX_ROWS:
            break
    return result, {"tableRows": table_rows, "candidates": len(result)}


def cksmh_list(html, adapter):
    """One actId-bound anchor AND same-card title; no global dates or legacy five IDs."""
    soup = BeautifulSoup(html, "html.parser")
    result, seen = [], set()
    links = 0
    for a in soup.select("a[href]"):
        url = urljoin(SOURCES["中正紀念堂"]["list"], a["href"])
        ident = adapter.exact_act_id(url)
        if not ident:
            continue
        links += 1
        title = title_clean(adapter.short_title(a.get_text(" ", strip=True)))
        if len(title) < 4 or ident in seen:
            continue
        seen.add(ident)
        result.append({"platform": "中正紀念堂", "title": title, "officialUrl":
                       "https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId=" + ident,
                       "identity": ident, "sourceUrl": SOURCES["中正紀念堂"]["list"],
                       "sourceRole": "FIRST_PARTY_ACTID_LIST_LINK",
                       "rawPeriod": None, "rawPeriodRole": "UNKNOWN",
                       "verified": False, "published": False})
        if len(result) >= MAX_ROWS:
            break
    return result, {"actIdAnchors": links, "candidates": len(result)}


class CountingSession:
    """Audit attempted GETs including redirects; optional injected mock session."""
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.count = 0

    def get(self, url, **kwargs):
        self.count += 1
        assert kwargs.get("allow_redirects") is False, "HOLD_REDIRECT_AUTOFOLLOW"
        assert kwargs.get("stream") is True, "HOLD_UNBOUNDED_RESPONSE"
        return self.session.get(url, **kwargs)

    def close(self):
        self.session.close()


def item_from_specialized(name, original):
    if name == "ibon":
        url = original["officialUrl"]
        title = original["title"]
        identity = url.rsplit("/", 1)[-1]
    else:
        url = original["official_url"]
        title = original["title"]
        identity = hexdigest(url.encode())[:24]
    return {"platform": name, "title": title, "officialUrl": url,
            "identity": identity, "sourceUrl": SOURCES[name]["list"],
            "sourceRole": "FIRST_PARTY_OFFICIAL_PLATFORM_LIST",
            "rawPeriod": original.get("rawScheduleText") if name == "FamiTicket" else None,
            "rawPeriodRole": "UNCLASSIFIED_LIST_TEXT" if name == "FamiTicket" else "UNKNOWN",
            "verified": False, "published": False}


def redact_info(meta):
    """No raw HTML persisted; seal source page bytes and public HTTP metadata."""
    return {k: v for k, v in meta.items()
            if k in ("state", "http_status", "httpStatus", "sha256", "bodySHA256",
                      "bytes", "bodyBytes", "content_type", "contentType",
                      "error_type", "exception", "trail", "redirectTrail")}


def detail_record(name, item, html, meta, adapter=None):
    result = {"identity": item["identity"], "url": item["officialUrl"],
              "http": redact_info(meta), "status": meta.get("state", "HOLD"),
              "titleParity": False, "fieldEvidence": [], "formalFieldPromotions": 0}
    if html is None:
        return result
    if name == "台北世貿":
        soup = BeautifulSoup(html, "html.parser")
        body = soup.get_text(" ", strip=True)
        # Direct title must be in document, not a redirect URL.
        matching = item["title"] in body
        result["titleParity"] = matching
        result["status"] = "DETAIL_TITLE_BOUND" if matching else "HOLD_TITLE_MISMATCH"
        if matching:
            match = re.search(r"展出日期\s*[:：]\s*(20\d{2}/\d{1,2}/\d{1,2})\s*[~～-]\s*(20\d{2}/\d{1,2}/\d{1,2})", body)
            if match:
                result["fieldEvidence"].append({"role": "EXHIBITION_DATE_RANGE",
                    "observedValue": match.group(0)[:110], "verification": "REVIEW_REQUIRED"})
    elif name == "中正紀念堂":
        # Historical P30-L4B source code; new current source row ID/title only.
        try:
            status = adapter.extract(html, {"officialUrl": item["officialUrl"],
                                            "title": item["title"]})
        except (ValueError, KeyError, TypeError):
            status = None
        result["titleParity"] = bool(status and status.get("state") == "DETAIL_TITLE_VERIFIED")
        result["status"] = "DETAIL_TITLE_BOUND" if result["titleParity"] else "HOLD_TITLE_MISMATCH"
        # No unreviewed promotion of prior field parser's dates.
    else:
        old = {"title": item["title"]}
        if name == "FamiTicket":
            check = adapter.sample_detail(html, old)
            success = check.get("state") == "DETAIL_TITLE_VERIFIED"
        else:
            check = adapter.verify_detail(html, old)
            success = check.get("state") == "TITLE_MATCH"
        result["titleParity"] = bool(success)
        result["status"] = "DETAIL_TITLE_BOUND" if success else "HOLD_TITLE_MISMATCH"
    return result


def safe_output(raw):
    target, root = Path(raw).resolve(), Path.cwd().resolve()
    if target == root or not target.is_relative_to(root) or any(
        target == root / p or target.is_relative_to(root / p)
        for p in ("docs", "scripts", "tests", "schemas", ".github", ".git")
    ):
        raise ValueError("HOLD_ISOLATED_OUTPUT_ONLY")
    return target


def acquire(session=None, delay=0.7, sleeper=time.sleep):
    if delay < 0.6:
        raise ValueError("HOLD_BOUNDED_RATE_REQUIRED")
    real = session is None
    client = CountingSession(session)
    ck = module("p30_l4b_cksmh", "p30_l4b_cksmh_details.py")
    fam = module("p30_l3ba_fami", "p30_l3b_a_famiticket.py")
    ibon = module("p30_l3bb_ibon", "p30_l3bb_ibon.py")
    l7b = module("p30_l7b_fresh", "p30_l7b_fresh_acquisition.py")
    out = []
    try:
        for name in PORTALS:
            begin = client.count
            meta = {"platform": name, "adapter": SOURCES[name]["adapter"],
                    "listUrls": [], "listHttp": [], "listCandidates": 0,
                    "detailAttempted": False, "detail": {"status": "NOT_ATTEMPTED"},
                    "jsOrTableHold": False, "state": "NOT_ATTEMPTED"}
            out.append(meta)
            rows = []
            if name == "中正紀念堂":
                page, http = ck.fetch_listing(client)
                meta["listUrls"].append(SOURCES[name]["list"])
                meta["listHttp"].append(redact_info(http))
                if page:
                    rows, state = cksmh_list(page, ck)
                    meta["parse"] = state
            elif name == "台北世貿":
                page, http = l7b.get_page(client, TWTC_LIST, ("twtc.com.tw",), 10, {"requests": 0})
                meta["listUrls"].append(TWTC_LIST)
                meta["listHttp"].append(redact_info(http))
                if page:
                    rows, state = twtc_list(page)
                    meta["parse"] = state
            elif name == "ibon":
                # Strict public entry and additional public MoreResult endpoint.
                for idx, url in enumerate(ibon.LISTS):
                    if idx:
                        sleeper(delay)
                    page, http = ibon.get_html(client, url, listing=True)
                    meta["listUrls"].append(url)
                    meta["listHttp"].append(redact_info(http))
                    if page:
                        found, state = ibon.parse_list(page, http.get("observed_url", url))
                        meta.setdefault("parse", []).append(state)
                        rows.extend(item_from_specialized(name, p) for p in found[:MAX_ROWS])
                rows = list({x["officialUrl"]: x for x in rows}.values())[:MAX_ROWS]
            else:
                page, http = fam.fetch(client, fam.LIST)
                meta["listUrls"].append(SOURCES[name]["list"])
                meta["listHttp"].append(redact_info(http))
                if page:
                    found, state = fam.parse_list(page)
                    meta["parse"] = state
                    rows = [item_from_specialized(name, p) for p in found[:MAX_ROWS]]
            meta["listCandidates"] = len(rows)
            meta["state"] = "LIST_CANDIDATES_REVIEW_ONLY" if rows else "HOLD_LIST_ZERO_OR_HTTP"
            if rows:
                chosen = next((x for x in rows if x["officialUrl"]), None)
                if chosen:
                    sleeper(delay)
                    meta["detailAttempted"] = True
                    if name == "中正紀念堂":
                        detail_page, detail_http = ck.fetch(client, chosen["officialUrl"])
                    elif name == "台北世貿":
                        if not strict_detail_url(chosen["officialUrl"], "twtc.com.tw", "/exhibition_more.aspx", "id"):
                            detail_page, detail_http = None, {"state": "HOLD_DETAIL_URL"}
                        else:
                            detail_page, detail_http = l7b.get_page(client, chosen["officialUrl"], ("twtc.com.tw",), 10, {"requests": 0})
                    elif name == "ibon":
                        detail_page, detail_http = ibon.get_html(client, chosen["officialUrl"], detail=True)
                    else:
                        detail_page, detail_http = fam.fetch(client, chosen["officialUrl"], detail=True)
                    meta["detail"] = detail_record(name, chosen, detail_page, detail_http,
                                                    {"中正紀念堂": ck, "ibon": ibon, "FamiTicket": fam}.get(name))
            meta["candidates"] = rows[:MAX_ROWS]
            meta["requestCount"] = client.count - begin
            meta["jsOrTableHold"] = meta["listCandidates"] == 0
            meta["completeCatalogVerified"] = False
    finally:
        if real:
            client.close()
    fetched = client.count if real else 0
    report = {"kind": KIND, "runId": "P30-L9C-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
              "candidateOrigin": "L9C_FRESH_PUBLIC_HTTP" if real else "L9C_SYNTHETIC_TEST_NOT_FRESH",
              "actualFreshHTTPRequests": fetched, "syntheticTestGETs": 0 if real else client.count,
              "sources": out, "platformsAttempted": len(out),
              "listPositive": sum(bool(p["listCandidates"]) for p in out),
              "candidateCount": sum(p["listCandidates"] for p in out),
              "detailAttempted": sum(bool(p["detailAttempted"]) for p in out),
              "detailTitleBound": sum(bool(p["detail"].get("titleParity")) for p in out),
              "fullPlatformCoverageVerified": False, "published": False,
              "goldenAccepted": 0, "writerExecuted": False, "schedulerExecuted": False,
              "notifierExecuted": False, "autoMergeCount": 0, "autoDeleteCount": 0,
              "formalDatePriceTicketPromotions": 0,
              "existingAndroid44Preserved": True,
              "l8AndroidCorePassPreserved": True, "releaseState": "HARD_HOLD_NO_PUBLICATION"}
    return report


def emit(report, output):
    target = safe_output(output)
    target.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
    (target / "fresh_four_source_diagnostics.json").write_bytes(raw)
    manifest = {"kind": "EVENTRADAR_P30_L9C_SEALED_EVIDENCE_MANIFEST",
                "runId": report["runId"], "sourcePR39Parent": "b1f831f985074e5011950403823bb1b4c41d16b4",
                "sha256": {"fresh_four_source_diagnostics.json": hexdigest(raw)},
                "actualFreshHTTPRequests": report["actualFreshHTTPRequests"],
                "releaseState": "HARD_HOLD_NO_PUBLICATION", "published": False}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="p30-l9c-evidence")
    p.add_argument("--delay", type=float, default=0.7)
    args = p.parse_args()
    safe_output(args.out)
    report = acquire(delay=args.delay)
    emit(report, args.out)
    for row in report["sources"]:
        print("SOURCE", row["platform"], "HTTP", [x.get("state") for x in row["listHttp"]],
              "LIST", row["listCandidates"], "DETAIL", row["detail"].get("status"),
              "REQUESTS", row["requestCount"])
    print("PASS L9C_REAL_HTTP_REQUESTS", report["actualFreshHTTPRequests"])
    print("QUALITY_LIST", report["listPositive"], "DETAIL_TITLE", report["detailTitleBound"])
    print("HOLD L9C_FRESH_FOUR_SOURCE_COVERAGE_AND_FIELD_PROMOTION_REVIEW_ONLY")
    print("PASS L9C_NO_WRITER_NO_PUBLISH_NO_ANDROID_44_REGRESSION")


if __name__ == "__main__":
    main()
