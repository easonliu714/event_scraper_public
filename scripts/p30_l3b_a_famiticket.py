#!/usr/bin/env python3
"""EventRadar P30-L3-B-A FamiTicket read-only official list -> detail probe.

One homepage GET + at most one bounded detail GET. Candidate evidence, NOT
an activity calendar, ticket availability, official Golden, or a Pages writer.
Old 2026 L1 /Home/Activity/Search/242 had HTTP 200 yet list empty.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote

import requests
from bs4 import BeautifulSoup

LIST="https://www.famiticket.com.tw/Home"
BASE_HOST="www.famiticket.com.tw"
DETAIL_PREFIX="/Home/Activity/Info/"
MAX_HTML=2_000_000
MAX_LIST=120
KIND="EVENTRADAR_P30_L3B_A_FAMITICKET_CANDIDATES_ONLY"
UA="EventRadar-Taiwan-P30-L3B-official-list-readonly/1.0"
STOPWORDS={"購票","立即購票","即將開賣","活動詳情","查看詳情","更多","詳情"}
CATEGORY={"展覽","文化幣(限線上)","表演&劇場","演唱會","音樂會",
          "運動賽事","TPBL","TPVL","F1賽車","樂園","景點門票","住宿",
          "農遊超市","電影","特映會","國旅限定優惠","戶外觀光","交通"}
DATE_TOKEN=re.compile(r"(?:(?:20\d{2}|11[456])[/.\-]\d{1,2}[/.\-]\d{1,2}|\d{1,2}/\d{1,2})(?:\s*[（(][一二三四五六日天][)）])?")
PERIOD_TOKEN=re.compile(r"(?:20\d{2}[/.]\d{1,2}[/.]\d{1,2}|自購買日起|即日起|使用期限至|2026/12/31)")

def allowed(url,detail=False):
    try:
        u=urlsplit(url)
        if (u.scheme!="https" or u.hostname!=BASE_HOST or u.username is not None
            or u.password is not None or u.port not in (None,443)
            or u.fragment or "\\" in u.path or ".." in u.path.split("/")):
            return False
        path=unquote(u.path)
        if detail:
            ident=path[len(DETAIL_PREFIX):] if path.startswith(DETAIL_PREFIX) else ""
            return bool(re.fullmatch(r"[A-Za-z0-9_\-+=]{20,500}",ident))
        return path in ("/Home","/Home/")
    except ValueError:
        return False


def canonical(url,detail=False):
    if not allowed(url,detail=detail):return None
    u=urlsplit(url)
    # query-free detail IDs; reject invented tracking values and duplicate query.
    if u.query:return None
    return urlunsplit(("https",BASE_HOST,u.path,"",""))


def fetch(session,url,detail=False,timeout=12):
    """No login, WAF evasion or retries. Redirect only allowlisted list/detail role."""
    trail=[]
    start=url
    for _ in range(3):
        if not allowed(url,detail=detail):
            return None,{"state":"URL_NOT_ALLOWLISTED","trail":trail}
        try:
            with session.get(url,timeout=(6,timeout),stream=True,allow_redirects=False,
                             headers={"User-Agent":UA,"Accept-Language":"zh-TW,zh;q=0.9"}) as rsp:
                code=rsp.status_code
                trail.append({"url":url,"status":code})
                if code in (301,302,303,307,308):
                    new=rsp.headers.get("location","")
                    if not new:return None,{"state":"MISSING_LOCATION","trail":trail}
                    url=urljoin(url,new)
                    continue
                typ=rsp.headers.get("content-type","")[:100]
                meta={"state":"HTTP_OK" if code==200 else "HTTP_ERROR",
                      "http_status":code,"start_url":start,"observed_url":url,
                      "content_type":typ,"trail":trail}
                if code!=200:return None,meta
                if "text/html" not in typ.lower():
                    meta["state"]="NON_HTML";return None,meta
                data=bytearray()
                for chunk in rsp.iter_content(chunk_size=32768):
                    data.extend(chunk)
                    if len(data)>MAX_HTML:
                        meta["state"]="OVERSIZE_HTML";return None,meta
                if not data:
                    meta["state"]="EMPTY_HTML";return None,meta
                meta["bytes"]=len(data)
                meta["sha256"]=hashlib.sha256(data).hexdigest()
                return bytes(data),meta
        except requests.RequestException as ex:
            return None,{"state":"NETWORK_ERROR","error_type":type(ex).__name__,
                         "trail":trail,"start_url":start}
    return None,{"state":"REDIRECT_LIMIT","trail":trail}


def norm(s):
    return re.sub(r"\s+"," ",s).strip()


def extract_card_label(anchor):
    """Reject purchase CTAs and category-only text. One anchor -> one candidate."""
    t=norm(anchor.get_text(" ",strip=True))
    if not t:
        for node in anchor.find_all(["img"],alt=True):
            t=norm(node.get("alt",""))
            if t:break
    if not t:return None
    # Official card often contains category, schedule and CTA around event title.
    for tok in ("購票","即將開賣","立即購買"):
        t=re.sub(r"\s*"+re.escape(tok)+r"\s*$","",t).strip()
    # If the title is a dedicated heading, prefer that over promotional card metadata.
    heads=anchor.find_all(["h2","h3","h4","h5"])
    for h in heads:
        value=norm(h.get_text(" ",strip=True))
        if len(value)>=4 and value not in STOPWORDS:
            return value[:180]
    if t in STOPWORDS or len(t)<4:return None
    # Strip opening badges + a complete date range; leave underlying title.
    tokens=t.split()
    while tokens and tokens[0] in CATEGORY:tokens.pop(0)
    remaining=norm(" ".join(tokens))
    prefix=re.match(
        r"^(?:20\d{2}|11[456])[/.\-]\d{1,2}[/.\-]\d{1,2}"
        r"(?:\s*[（(][一二三四五六日天][)）])?"
        r"(?:\s*[~～\-]\s*(?:(?:20\d{2}|11[456])[/.\-])?\d{1,2}[/.\-]\d{1,2}"
        r"(?:\s*[（(][一二三四五六日天][)）])?)?\s*",
        remaining)
    if prefix:remaining=remaining[prefix.end():]
    remaining=norm(remaining)
    if len(remaining)<4 or remaining in STOPWORDS:return None
    return remaining[:180]


def parse_list(html):
    soup=BeautifulSoup(html,"html.parser")
    out=[]
    seen=set()
    anchors_seen=0
    for a in soup.find_all("a",href=True):
        href=a.get("href","")
        url=canonical(urljoin(LIST,href),detail=True)
        if not url:continue
        anchors_seen+=1
        if url in seen:continue
        label=extract_card_label(a)
        if not label:continue
        # Some templates place title outside anchor, in same card container.
        if label in STOPWORDS:continue
        seen.add(url)
        # Date tokens are captured as raw evidence only, NEVER assumed show dates.
        raw=norm(a.get_text(" ",strip=True))
        date_text=" ".join(DATE_TOKEN.findall(raw))[:120] or None
        out.append({"platform":"FamiTicket","title":label,"official_url":url,
                    "list_url":LIST,"dateStart":None,"dateEnd":None,
                    "rawScheduleText":date_text,"rawScheduleRole":"UNCLASSIFIED_LISTING_TEXT",
                    "venue":None,"price":None,"ticketStatus":"UNKNOWN",
                    "scheduleStatus":"UNKNOWN","detailStatus":"NOT_CHECKED",
                    "dataCompleteness":"LIST_IDENTITY_ONLY",
                    "category":"待分類","classificationEvidence":"UNVERIFIED",
                    "goldenVerified":False,"published":False})
        if len(out)>=MAX_LIST:break
    return out,{"detail_anchors":anchors_seen,"candidate_count":len(out),
                "bounded_limit":MAX_LIST}


def sample_detail(html,row):
    soup=BeautifulSoup(html,"html.parser")
    headings=[norm(x.get_text(" ",strip=True))
              for x in soup.find_all(["h1","h2","h3","h4"])]
    title=row["title"]
    matched=title in headings
    result={"state":"DETAIL_TITLE_VERIFIED" if matched else "TITLE_IDENTITY_HOLD",
            "official_title":title if matched else None,"heading_count":len(headings),
            "dateStart":None,"dateEnd":None,"price":None,"ticketStatus":"UNKNOWN"}
    if matched:
        # Optional bounded description for QA, not official calendar or ticket truth.
        for h in soup.find_all(["h1","h2","h3","h4"]):
            if norm(h.get_text(" ",strip=True))==title:
                parent=h.parent
                snippet=norm(parent.get_text(" ",strip=True))[:360] if parent else ""
                if len(snippet)>len(title)+20:
                    result["short_excerpt"]=snippet
                break
    return result


def run(session,delay=1.0):
    if delay<0.6:raise ValueError("HOLD_RATE_LIMIT")
    page,meta=fetch(session,LIST)
    rows,summary=parse_list(page) if page is not None else ([],{"candidate_count":0})
    sample={"state":"NOT_ATTEMPTED"}
    if rows:
        time.sleep(delay)
        sample_page,detail_meta=fetch(session,rows[0]["official_url"],detail=True)
        sample={"id":rows[0]["official_url"],"http":detail_meta}
        if sample_page is not None:
            sample.update(sample_detail(sample_page,rows[0]))
            rows[0]["detailStatus"]=sample["state"]
            print("SAMPLE_LIST_TITLE",repr(rows[0]["title"][:130]))
            print("SAMPLE_DETAIL_HEADINGS",repr([x.get_text(" ",strip=True)[:130] for x in BeautifulSoup(sample_page,"html.parser").find_all(["h1","h2","h3","h4"])][:6]))
        else:sample["state"]="DETAIL_HTTP_HOLD"
    report={"kind":KIND,"generatedAtUTC":datetime.now(timezone.utc).isoformat(),
            "priorFailure":"P30_L1_HTTP200_LIST0_STALE_SEARCH_ENTRY",
            "list":{"requested":LIST,"http":meta,"parse":summary},
            "sample":sample,"maxListGET":1,"maxDetailGET":1,"retries":0,
            "goldenAccepted":False,"published":False,"writerExecuted":False,
            "notificationExecuted":False,"autoHidden":0,
            "sourceRuntime":"DORMANT","completeCatalogProven":False}
    return rows,report


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",required=True)
    args=ap.parse_args(argv)
    target=Path(args.out_dir).resolve()
    docs=Path("docs").resolve()
    if target==docs or docs in target.parents:
        ap.error("HOLD_OFFICIAL_PAGES_WRITER")
    with requests.Session() as session:
        rows,report=run(session)
    target.mkdir(parents=True,exist_ok=True)
    (target/"candidate.json").write_text(
        json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (target/"diagnostics.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("L3B_FAMITICKET HTTP",report["list"]["http"].get("http_status"),
          "LIST",len(rows),"DETAIL",report["sample"]["state"])
    if report["list"]["http"]["state"]!="HTTP_OK" or len(rows)==0:
        print("HOLD L3B_FAMITICKET_HTTP_OR_LIST")
        raise SystemExit(2)
    print("PASS P30_L3B_A_FAMITICKET_LIST_EVIDENCE_ONLY")
    print("GOLDEN=0 PUBLISHED=false AUTOHIDE=0 NOTIFIER=0")


if __name__=="__main__":
    main()
