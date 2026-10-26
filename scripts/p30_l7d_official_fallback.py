#!/usr/bin/env python3
"""P30-L7-D official-institution fallback for postponed FinTech Taipei 2026.

Read-only: three EXACT public HTTPS URLs; 3 GET maximum, 0 retries, bounded bytes.
Separates original, referenced tentative, and confirmed dates. No bypass of
TLS, no automatic writer/publisher, and no inference of final event dates.
"""
import argparse
import hashlib
import json
import re
import time
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs

import requests
from bs4 import BeautifulSoup

BASE_KIND = "EVENTRADAR_P30_ANDROID_SMOKE_CANDIDATE_NOT_GOLDEN"
EVIDENCE_KIND = "EVENTRADAR_P30_L7D_OFFICIAL_INSTITUTION_ROLE_EVIDENCE"
EVENT_ID = "28255"
ORIGINAL_URL = f"https://twtc.com.tw/exhibition_more.aspx?id={EVENT_ID}&p=home"
CO_ORGANIZER_URL = "https://www.tfsr.org.tw/information/187"
FINANCIAL_INSTITUTION_URL = "https://www.nccc.com.tw/wps/wcm/connect/zh/home/AboutNCCC/News/200261021-1"
SOURCE_URLS = (ORIGINAL_URL, CO_ORGANIZER_URL, FINANCIAL_INSTITUTION_URL)
USER_AGENT = "EventRadar-P30-readonly/1.0 (github.com/easonliu714/event_scraper_public)"
MAX_BYTES = 800_000
MAX_REDIRECTS = 2
MAX_INPUT_ROWS = 44


def ntext(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value))).casefold()


def allow(url, source):
    """Every request/redirect must stay HTTPS on its own exact source document."""
    try:
        p, fixed = urlsplit(url), urlsplit(source)
        if (p.scheme != "https" or p.username or p.password
                or p.port not in (None, 443) or p.hostname != fixed.hostname
                or p.path != fixed.path or "\\" in p.path or ".." in p.path.split("/")):
            return False
        if source == ORIGINAL_URL:
            return parse_qs(p.query).get("id", []) == [EVENT_ID]
        return not p.query
    except ValueError:
        return False


def get_one(session, source, timeout=12):
    url, redirects = source, []
    for _ in range(MAX_REDIRECTS + 1):
        if not allow(url, source):
            return None, {"state": "UNAPPROVED_REDIRECT", "trail": redirects}
        try:
            with session.get(url, timeout=(6, timeout), stream=True,
                             allow_redirects=False,
                             headers={"User-Agent": USER_AGENT}) as response:
                status = response.status_code
                redirects.append({"url": url, "status": status})
                if status in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        return None, {"state": "REDIRECT_NO_LOCATION", "trail": redirects}
                    url = urljoin(url, location)
                    continue
                content_type = response.headers.get("content-type", "")[:100]
                meta = {"state": "HTTP_OK" if status == 200 else "HTTP_ERROR",
                        "http_status": status, "source_url": source,
                        "observed_url": url, "trail": redirects, "content_type": content_type}
                if status != 200:
                    return None, meta
                if "text/html" not in content_type.lower():
                    meta["state"] = "NON_HTML"
                    return None, meta
                data = bytearray()
                for part in response.iter_content(chunk_size=16384):
                    data.extend(part)
                    if len(data) > MAX_BYTES:
                        meta["state"] = "HTML_SIZE_LIMIT"
                        return None, meta
                if not data:
                    meta["state"] = "EMPTY_BODY"
                    return None, meta
                meta["sha256"] = hashlib.sha256(data).hexdigest()
                meta["bytes"] = len(data)
                return bytes(data), meta
        except requests.RequestException as err:
            return None, {"state": "NETWORK_ERROR", "error_type": type(err).__name__,
                          "source_url": source, "trail": redirects}
    return None, {"state": "REDIRECT_LIMIT", "trail": redirects}


def parse_twtc_original(page):
    soup = BeautifulSoup(page, "html.parser")
    heads = [ntext(h.get_text(" ", strip=True)) for h in soup.select("h1,h2,h3")]
    if not any("2026" in h and "台北金融科技展" in h and "延期" in h for h in heads):
        raise ValueError("HOLD_ORIGINAL_HEADING_IDENTITY")
    raw = " ".join(soup.stripped_strings)
    matches = re.findall(
        r"展出日期\s*[:：]\s*(20\d{2}/\d{1,2}/\d{1,2})\s*[～~-]\s*(20\d{2}/\d{1,2}/\d{1,2})",
        raw)
    if len(matches) != 1:
        raise ValueError("HOLD_ORIGINAL_DATE_SHAPE")
    a,b=(date.fromisoformat(v.replace("/","-")) for v in matches[0])
    if a>b or a.year!=2026 or b.year!=2026:
        raise ValueError("HOLD_ORIGINAL_YEAR")
    return a.isoformat(), b.isoformat()


def parse_co_organizer(page):
    soup = BeautifulSoup(page, "html.parser")
    body = ntext(" ".join(soup.stripped_strings))
    if not ("台北金融科技展" in body and "延期" in body and "10/23" in body):
        raise ValueError("HOLD_ORGANIZER_POSTPONEMENT_IDENTITY")
    # Even when a new date appears elsewhere, co-organizer says confirmation pending.
    if "10月底前公告" not in body:
        raise ValueError("HOLD_ORGANIZER_CONFIRMATION_TEXT_CHANGED")
    return "POSTPONED_PENDING_FINAL_CONFIRMATION"


def parse_financial_notice(page):
    soup = BeautifulSoup(page, "html.parser")
    body = ntext(" ".join(soup.stripped_strings))
    if "台北金融科技展" not in body or "延期" not in body:
        raise ValueError("HOLD_FINANCIAL_INSTITUTION_IDENTITY")
    # Notice dated Oct 21 says rescheduled Dec 18-19. We still classify as
    # REPORTED_TENTATIVE because the co-organizer says final dates pending.
    if not re.search(r"12月18日.{0,30}12月19日", body):
        raise ValueError("HOLD_FINANCIAL_INSTITUTION_DATE_TEXT_CHANGED")
    return "2026-12-18", "2026-12-19"


def select_one(parent):
    if not isinstance(parent,dict) or parent.get("kind")!=BASE_KIND:
        raise ValueError("HOLD_PARENT_KIND")
    if parent.get("count")!=MAX_INPUT_ROWS or len(parent.get("items",[]))!=MAX_INPUT_ROWS:
        raise ValueError("HOLD_PARENT_ROWS")
    for name,expected in (("goldenAccepted",False),("published",False),
                          ("writerExecuted",False),("notificationExecuted",False),
                          ("autoHidden",0),("sourceRuntime","DORMANT"),
                          ("dateVerifiedCount",38),("dateUnverifiedCount",1)):
        if parent.get(name)!=expected:
            raise ValueError("HOLD_PARENT_FLAG_"+name)
    rows=[r for r in parent["items"] if r.get("platform")=="台北世貿"
          and r.get("rawPeriod")=="延期未定" and "台北金融科技展" in r.get("title","")]
    if len(rows)!=1:
        raise ValueError("HOLD_EXACT_POSTPONED_ROW")
    event=rows[0]
    if (event.get("officialUrl")!=ORIGINAL_URL
            or event.get("dateEvidenceStatus")!="LIST_DETAIL_PERIOD_CONFLICT"
            or event.get("dateStart") is not None or event.get("dateEnd") is not None):
        raise ValueError("HOLD_DETAIL_BINDING")
    return event


def enrich(parent, original, inst_note, organizer_status, http):
    target=select_one(parent)
    if original is None:
        raise ValueError("HOLD_ORIGINAL_UNVERIFIED")
    if inst_note is None and organizer_status is None:
        raise ValueError("HOLD_POSTPONEMENT_NOTICE_UNVERIFIED")
    data=json.loads(json.dumps(parent,ensure_ascii=False))
    row=next(x for x in data["items"] if x["id"]==target["id"])
    row.update({
        "scheduleStatus":"POSTPONED_PENDING_FINAL_CONFIRMATION",
        "originalDateStart":original[0],"originalDateEnd":original[1],
        "tentativeDateStart":inst_note[0] if inst_note else None,
        "tentativeDateEnd":inst_note[1] if inst_note else None,
        "tentativeSourceRole":"OFFICIAL_INSTITUTION_REPORTED_UNCONFIRMED"
                              if inst_note else "NOT_CONFIRMED",
        "tentativeSourceUrl":FINANCIAL_INSTITUTION_URL if inst_note else None,
        "organizerStatusSourceUrl":CO_ORGANIZER_URL if organizer_status else None,
        "originalDateSourceUrl":ORIGINAL_URL,
        "confirmedDateStart":None,"confirmedDateEnd":None,
        "dateStart":None,"dateEnd":None,
        "dateEvidenceStatus":"POSTPONED_ORIGINAL_AND_UNCONFIRMED_ROLES",
        "dateSourceRole":"ORIGINAL_NOT_CURRENT",
        "scheduleObservedAtUTC":datetime.now(timezone.utc).isoformat(),
    })
    data["postponementRoleCaseCount"]=1
    data["postponementEvidenceKind"]=EVIDENCE_KIND
    data["published"]=False
    evidence={"kind":EVIDENCE_KIND,"eventId":target["id"],"sourceRunId":"40273949404",
              "original":original,"tentative":inst_note,"organizerState":organizer_status,
              "confirmed":None,"http":http,
              "sourceRuntime":"DORMANT","goldenAccepted":False,"published":False,
              "autoHidden":0,"writerExecuted":False,"notificationExecuted":False}
    return data,evidence


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--parent",required=True)
    parser.add_argument("--out-dir",required=True)
    args=parser.parse_args(argv)
    out=Path(args.out_dir).resolve()
    docs=Path("docs").resolve()
    if out==docs or docs in out.parents:
        parser.error("HOLD_FORMAL_PAGES_PATH")
    blob=Path(args.parent).read_bytes()
    parent=json.loads(blob.decode("utf-8"))
    select_one(parent)
    http={}
    results={}
    with requests.Session() as session:
        for idx,source in enumerate(SOURCE_URLS):
            if idx: time.sleep(1.5)
            body,meta=get_one(session,source)
            http[source]=meta
            results[source]=body
    original,co,inst=None,None,None
    parse_errors={}
    for url,parser_fn in ((ORIGINAL_URL,parse_twtc_original),
                          (CO_ORGANIZER_URL,parse_co_organizer),
                          (FINANCIAL_INSTITUTION_URL,parse_financial_notice)):
        if results[url] is None: continue
        try:
            parsed=parser_fn(results[url])
            if url==ORIGINAL_URL: original=parsed
            elif url==CO_ORGANIZER_URL: co=parsed
            else: inst=parsed
        except (ValueError,TypeError) as exc:
            parse_errors[url]=str(exc)
    out.mkdir(parents=True,exist_ok=True)
    diagnosis={"kind":EVIDENCE_KIND,"state":"EVALUATED",
               "source_sha256":hashlib.sha256(blob).hexdigest(),
               "http":http,"parse_errors":parse_errors,
               "original":original,"tentative":inst,"organizerState":co,
               "candidateCreated":False}
    if original is None or (co is None and inst is None):
        diagnosis["state"]="OFFICIAL_EVIDENCE_INCOMPLETE_HOLD"
        (out/"hold_diagnostics.json").write_text(
            json.dumps(diagnosis,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("HOLD P30_L7D_OFFICIAL_SOURCES_INCOMPLETE", [(u,m["state"]) for u,m in http.items()],parse_errors)
        raise SystemExit(2)
    data,evidence=enrich(parent,original,inst,co,http)
    diagnosis["candidateCreated"]=True
    (out/"data.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"schedule_roles.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"diagnostics.json").write_text(json.dumps(diagnosis,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS P30_L7D_OFFICIAL_INSTITUTION_POSTPONEMENT_EVIDENCE")
    print("SOURCE_HTTP",[(u,m["state"],m.get("http_status")) for u,m in http.items()])
    print("ORIGINAL",original,"TENTATIVE",inst,"CONFIRMED",None)
    print("PASS P30_L7D_44_IDENTITIES_38_DATE_CANDIDATES_1_POSTPONED_NO_PUBLISH")


if __name__=="__main__":
    main()
