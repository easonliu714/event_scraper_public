#!/usr/bin/env python3
"""P30-L3-B-B: ibon public entertainment cards, read-only/one-shot Gate.

A recovered listing is not a verified show schedule, price, sale state or Golden.
Never touch checkout, login, published Pages, scheduler, or notification functions.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

import requests
from bs4 import BeautifulSoup, UnicodeDammit

KIND="EVENTRADAR_P30_L3BB_IBON_PUBLIC_EVENT_CANDIDATE_ONLY"
HOST="ticket.ibon.com.tw"
LISTS=(
    "https://ticket.ibon.com.tw/Index/entertainment",
    "https://ticket.ibon.com.tw/Home/MoreResult?inATAPID=105&inATAPWebType=entertainment",
)
DETAIL_RE=re.compile(r"^/(?:Web/|WebV3/)?ActivityInfo/Details/([0-9]{3,8})/?$")
USER_AGENT="EventRadar-P30-L3BB-readonly/1.0 (public event pages; github.com/easonliu714/event_scraper_public)"
MAX_BYTES=2_000_000
MAX_ROWS=120
SKIP={
    "購票","立即購票","查看活動","活動詳情","查看詳情","更多","查看更多",
    "詳細資料","熱賣中","售票中","即將開賣","立即預訂","報名","了解更多",
    "img","image","熱門","活動","娛樂","最新開賣","已售完",
}
def origin_ok(url):
    try:
        v=urlsplit(url)
        return v.scheme=="https" and v.hostname==HOST and v.username is None \
            and v.password is None and v.port in (None,443) and not v.fragment \
            and "\\" not in unquote(v.path) and ".." not in unquote(v.path).split("/")
    except ValueError:
        return False

def role(url,listing=False,detail=False):
    if not origin_ok(url):return False
    u=urlsplit(url)
    if detail:
        return not u.query and bool(DETAIL_RE.fullmatch(u.path))
    if listing:
        return url in LISTS or (not u.query and u.path in ("/Index/entertainment","/"))
    return False

def canonical_detail(href,base):
    url=urljoin(base,href)
    if not role(url,detail=True):return None
    u=urlsplit(url)
    m=DETAIL_RE.fullmatch(u.path)
    return f"https://{HOST}/ActivityInfo/Details/{m.group(1)}"

def get_html(session,url,listing=False,detail=False,timeout=12):
    hops=[]
    if not role(url,listing=listing,detail=detail):
        return None,{"state":"URL_REJECTED","trail":hops,"request_url":url}
    for _ in range(3):
        if not role(url,listing=listing,detail=detail):
            return None,{"state":"REDIRECT_REJECTED","trail":hops,"request_url":url}
        try:
            with session.get(url,timeout=(6,timeout),stream=True,allow_redirects=False,
                             headers={"User-Agent":USER_AGENT,"Accept":"text/html"}) as response:
                code=response.status_code
                hops.append({"url":url,"status":code})
                if code in (301,302,303,307,308):
                    loc=response.headers.get("location","")
                    if not loc:
                        return None,{"state":"REDIRECT_WITHOUT_LOCATION","trail":hops}
                    url=urljoin(url,loc)
                    continue
                ct=response.headers.get("content-type","")[:120]
                info={"state":"HTTP_OK" if code==200 else "HTTP_ERROR",
                      "http_status":code,"observed_url":url,"trail":hops,"content_type":ct}
                if code!=200:return None,info
                if "text/html" not in ct.casefold():
                    info["state"]="NON_HTML";return None,info
                body=bytearray()
                for chunk in response.iter_content(chunk_size=32768):
                    body.extend(chunk)
                    if len(body)>MAX_BYTES:
                        info["state"]="OVERSIZE_HTML";return None,info
                if not body:
                    info["state"]="EMPTY_HTML";return None,info
                info["bytes"]=len(body)
                info["sha256"]=hashlib.sha256(body).hexdigest()
                decoded=UnicodeDammit(bytes(body),is_html=True).unicode_markup
                return (decoded or bytes(body).decode("utf-8",errors="replace")),info
        except requests.RequestException as ex:
            return None,{"state":"NETWORK_ERROR","error_type":type(ex).__name__,
                         "trail":hops,"request_url":url}
    return None,{"state":"REDIRECT_LIMIT","trail":hops}

def clean(s):
    return re.sub(r"\s+"," ",s or "").strip()

def plausible_label(label):
    if not label or len(label)<4 or len(label)>260:return False
    if label.casefold() in SKIP:return False
    if re.fullmatch(r"20\d{2}[-/\.]\d{1,2}[-/\.]\d{1,2}",label):return False
    if label.startswith(("http://","https://","javascript:")):return False
    return True

def official_label(a):
    # Prioritize same-card title; keep identity close to the outbound event link.
    scope=[a]
    if a.parent and a.parent.name not in ("body","html"):scope.append(a.parent)
    for item in scope:
        for node in item.find_all(["h2","h3","h4","h5"],recursive=True):
            title=clean(node.get_text(" ",strip=True))
            if plausible_label(title):return title[:180]
    for v in (a.get("title"),a.get("aria-label"),
              a.get_text(" ",strip=True)):
        label=clean(v)
        if plausible_label(label):return label[:180]
    img=a.find("img",alt=True)
    if img:
        label=clean(img.get("alt"))
        if plausible_label(label):return label[:180]
    return None

def parse_list(html,base):
    soup=BeautifulSoup(html,"html.parser")
    out=[]
    seen=set()
    links=0
    for a in soup.select("a[href]"):
        url=canonical_detail(a.get("href",""),base)
        if url is None:continue
        links+=1
        if url in seen:continue
        title=official_label(a)
        if not title:continue
        seen.add(url)
        out.append({"platform":"ibon","title":title,"officialUrl":url,
                    "observedListUrl":base,"dateStart":None,"dateEnd":None,
                    "dateRole":"UNKNOWN","location":None,"price":None,
                    "ticketStatus":"UNKNOWN","category":"待分類",
                    "categoryBasis":"UNVERIFIED","dataCompleteness":"OFFICIAL_LIST_LINK_ONLY",
                    "detailState":"NOT_CHECKED","candidateOnly":True,"goldenVerified":False})
        if len(out)>=MAX_ROWS:break
    return out,{"detail_links_seen":links,"candidates":len(out),
                "boundedLimit":MAX_ROWS,"other_links_seen":len(soup.select("a[href]"))}

def verify_detail(html,row):
    soup=BeautifulSoup(html,"html.parser")
    headings=[clean(n.get_text(" ",strip=True)) for n in soup.find_all(["h1","h2","h3","h4"])]
    title=row["title"]
    matched=any(h==title for h in headings)
    return {"state":"TITLE_MATCH" if matched else "TITLE_MISMATCH_OR_HTML_SHELL_HOLD",
            "headlineCount":len(headings),"observedTitleMatch":matched,
            "dateStart":None,"dateEnd":None,"ticketStatus":"UNKNOWN"}

def run(session,delay=1.0):
    if delay<0.6:raise ValueError("HOLD_DELAY")
    found={}
    observations=[]
    for i,url in enumerate(LISTS):
        if i:time.sleep(delay)
        html,net=get_html(session,url,listing=True)
        rows,stats=parse_list(html,net.get("observed_url",url)) if html is not None else ([],{"candidates":0})
        observations.append({"url":url,"net":net,"parse":stats})
        for r in rows:
            found.setdefault(r["officialUrl"],r)
    rows=list(found.values())[:MAX_ROWS]
    detail={"state":"NOT_ATTEMPTED"}
    if rows:
        time.sleep(delay)
        # Choose the first identity-bound anchor, never fetch a foreign host or checkout.
        page,net=get_html(session,rows[0]["officialUrl"],detail=True)
        detail={"officialUrl":rows[0]["officialUrl"],"http":net}
        if page is not None:
            result=verify_detail(page,rows[0])
            detail.update(result)
            rows[0]["detailState"]=result["state"]
        else:detail["state"]="DETAIL_HTTP_HOLD"
    report={"kind":KIND,"generatedAtUTC":datetime.now(timezone.utc).isoformat(),
            "formerL1":"ticket.ibon.com.tw/Activity/Index HTTP200 list=0",
            "lists":observations,"detail":detail,
            "counts":{"listHTTP200":sum(x["net"]["state"]=="HTTP_OK" for x in observations),
                      "listNonempty":sum(x["parse"]["candidates"]>0 for x in observations),
                      "uniqueCandidates":len(rows)},
            "maxListGET":2,"maxDetailGET":1,"retryCount":0,
            "goldenAccepted":False,"appDataPublished":False,"writerExecuted":False,
            "notifierExecuted":False,"sourceRuntime":"DORMANT","autoHidden":0,
            "fullCatalogProven":False}
    return rows,report

def main(argv=None):
    arg=argparse.ArgumentParser()
    arg.add_argument("--out-dir",required=True)
    a=arg.parse_args(argv)
    out=Path(a.out_dir).resolve()
    docs=Path("docs").resolve()
    if out==docs or docs in out.parents:arg.error("HOLD_PRODUCTION_DOCS")
    with requests.Session() as s: rows,report=run(s)
    out.mkdir(parents=True,exist_ok=True)
    (out/"candidate.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"diagnostics.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for r in report["lists"]:
        print("IBON_LIST",r["url"],r["net"]["state"],r["net"].get("http_status"),
              "CANDIDATES",r["parse"].get("candidates",0),
              "LINKS",r["parse"].get("detail_links_seen",0),
              "ANCHORS",r["parse"].get("other_links_seen",0))
    print("IBON_DETAIL",report["detail"]["state"],report["detail"].get("http",{}).get("http_status"))
    print("IBON_TOTAL",len(rows),"CANDIDATE_ONLY")
    if not rows:
        print("HOLD P30_L3BB_IBON_EMPTY_LIST_HTML_SHELL_OR_ENTRY")
        raise SystemExit(2)
    print("PASS P30_L3BB_IBON_OFFICIAL_LIST_CANDIDATES_NO_PUBLISH")

if __name__=="__main__":main()
