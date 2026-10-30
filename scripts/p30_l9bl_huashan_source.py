#!/usr/bin/env python3
"""P30-L9-BL: rotate from Songshan title HOLD to existing Huashan #13, no publication."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

HOME = "https://www.huashan1914.com/exhibition"
HOST = "www.huashan1914.com"
HOLD = "HARD_HOLD_NO_PUBLICATION"

def norm(s):
    return " ".join(str(s).split())

def safe_detail(raw):
    if not raw or raw.startswith("//"):
        return None
    u = urlsplit(urljoin(HOME, raw))
    if u.scheme != "https" or u.hostname != HOST or u.username or u.password or u.port or u.query or u.fragment:
        return None
    if not re.fullmatch(r"/exhibition/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)?/?", u.path):
        return None
    return u.geturl()

def edges(html):
    soup = BeautifulSoup(html, "html.parser")
    found, conflicts = {}, 0
    for a in soup.find_all("a", href=True, limit=1200):
        u = safe_detail(a["href"])
        if not u:
            continue
        title = norm(a.get_text(" ", strip=True))
        if not title:
            imgs = a.find_all("img", alt=True, limit=2)
            title = norm(imgs[0].get("alt", "")) if len(imgs) == 1 else ""
        title = re.sub(r"\s*(?:20\d{2}[/-]\d{1,2}[/-]\d{1,2}).*$", "", title)
        if not 4 <= len(title) <= 180 or any(w in title for w in ("活動總覽", "展覽總覽", "展演攻略")):
            continue
        if u in found and found[u] != title:
            conflicts += 1
        found.setdefault(u, title)
    return list(found.items())[:50], conflicts

def inspect(index_html, detail_html):
    found, conflicts = edges(index_html)
    out = {"sourceDerivedEdges":len(found), "titleConflicts":conflicts, "exactTitleMatches":0,
           "detailDateLabelCount":0, "acceptedFields":0, "ticketEventId":None}
    if not found or conflicts:
        return dict(out, decision="HOLD_LIST_ZERO_OR_TITLE_CONFLICT")
    title = found[0][1]
    soup = BeautifulSoup(detail_html, "html.parser")
    headings = [norm(x.get_text(" ", strip=True)) for x in soup.find_all(["h1","h2","h3","h4"], limit=80)]
    out["exactTitleMatches"] = headings.count(title)
    text = norm(soup.get_text(" ", strip=True))
    out["detailDateLabelCount"] = len(re.findall(r"(?:展覽|活動)日期\s*[：:]", text))
    if out["exactTitleMatches"] != 1:
        return dict(out, decision="HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    if out["detailDateLabelCount"] > 1:
        return dict(out, decision="HOLD_DATE_ROLE_AMBIGUITY")
    return dict(out, decision="REVIEW_HUASHAN_EXACT_TITLE_NO_FIELDS")

def get_one(url):
    receipt = {"urlSHA256":hashlib.sha256(url.encode()).hexdigest(),"httpStatus":None,"bodyBytes":0}
    try:
        r = requests.get(url, timeout=15, allow_redirects=False,
                         headers={"User-Agent":"EventRadar-SourceQuality/1.0"})
        receipt.update(httpStatus=r.status_code, bodyBytes=len(r.content))
        if r.status_code != 200 or len(r.content) > 1500000 or "text/html" not in r.headers.get("Content-Type","").lower():
            return receipt, None
        return receipt, r.text
    except requests.RequestException as e:
        receipt["errorType"] = type(e).__name__
        return receipt, None

def live():
    a = {"gate":"P30-L9-BL","source":"HUASHAN_PLATFORM_13",
         "observed_at":datetime.now(timezone.utc).isoformat(),"requestBudget":2,
         "requestCount":1,"acceptedFields":0,"goldenAccepted":0,
         "published":False,"releaseState":HOLD}
    a["indexReceipt"], html = get_one(HOME)
    if html is None:
        return dict(a, decision="HOLD_INDEX_HTTP_OR_BODY")
    found, conflicts = edges(html)
    a.update(sourceDerivedEdges=len(found),titleConflicts=conflicts)
    if not found or conflicts:
        return dict(a, decision="HOLD_LIST_ZERO_OR_TITLE_CONFLICT")
    url = found[0][0]
    a["selectedURLSHA256"] = hashlib.sha256(url.encode()).hexdigest()
    a["requestCount"] = 2
    a["detailReceipt"], detail = get_one(url)
    if detail is None:
        return dict(a, decision="HOLD_DETAIL_HTTP_OR_BODY")
    a.update(inspect(html, detail))
    return a

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--live-one", action="store_true")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(live(), f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
