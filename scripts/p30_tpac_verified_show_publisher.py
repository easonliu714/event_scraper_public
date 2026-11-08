"""Reusable strict TPAC official program LIST -> exact ID DETAIL field parser.

Accepts bounded native-body receipts only; never GETs, writes docs/data.json,
updates Golden, schedules work or sends notifications. A source-qualified
candidate still needs independently approved one-shot release Gate.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

SHOW = re.compile(r"^(20\d{2}-\d{2}-\d{2})\s*\(([一二三四五六日])\)\s*([0-2]\d:[0-5]\d)$")
PERIOD = re.compile(r"^(20\d{2}-\d{2}-\d{2})\s*[-–]\s*(20\d{2}-\d{2}-\d{2})$")
WEEK = "一二三四五六日"
TPE = timezone(timedelta(hours=8))
MAX_HTML = 2*1024*1024


def text(node):
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def _utc(value):
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("TPAC_OBSERVED_AT_TZ_HOLD")
    return dt.astimezone(timezone.utc)


def _period(value):
    m=PERIOD.fullmatch(value)
    if not m:
        raise ValueError("TPAC_PERIOD_LABEL_HOLD")
    a,b=date.fromisoformat(m.group(1)),date.fromisoformat(m.group(2))
    if a>b:
        raise ValueError("TPAC_PERIOD_REVERSED_HOLD")
    return a,b


def parse_verified_program(list_bytes, detail_bytes, receipt, now):
    """Return independently checkable qualified core fields or fail closed.

    The LIST date range is recorded as a conflict if it differs from the
    DETAIL date range; only exact DETAIL '場次' values are eligible for SHOW.
    """
    try:
        if not isinstance(receipt,dict) or receipt.get("kind")!="EVENTRADAR_TPAC_2040_FIRST_PARTY_ONE_SHOT":
            raise ValueError("TPAC_NATIVE_RECEIPT_KIND_HOLD")
        lu,du=receipt.get("list_url"),receipt.get("detail_url")
        if lu!="https://tpac.org.taipei/program" or not isinstance(du,str):
            raise ValueError("TPAC_LIST_URL_HOLD")
        p=urlparse(du)
        if p.scheme!="https" or p.netloc!="tpac.org.taipei" or not re.fullmatch(r"/program/[1-9][0-9]*",p.path) or p.query or p.fragment:
            raise ValueError("TPAC_CANONICAL_ID_HOLD")
        sid=p.path.rsplit("/",1)[-1]
        if receipt.get("source_native_get")!=3 or receipt.get("decision")!="RAW_SOURCE_SAVED_FOR_INDEPENDENT_REPLAY_ONLY":
            raise ValueError("TPAC_NATIVE_STATUS_ROBOTS_HOLD")
        if not all(isinstance(b,bytes) and 0<len(b)<=MAX_HTML for b in (list_bytes,detail_bytes)):
            raise ValueError("TPAC_NATIVE_BODY_CAP_HOLD")
        lsha=hashlib.sha256(list_bytes).hexdigest()
        dsha=hashlib.sha256(detail_bytes).hexdigest()
        if (lsha!=receipt.get("list_sha256") or dsha!=receipt.get("detail_sha256")
            or len(list_bytes)!=receipt.get("list_bytes") or len(detail_bytes)!=receipt.get("detail_bytes")):
            raise ValueError("TPAC_NATIVE_SOURCE_SHA_HOLD")
        observed=_utc(receipt["started_at"])
        now=now.astimezone(timezone.utc)
        if now<observed or now-observed>timedelta(hours=24):
            raise ValueError("TPAC_NATIVE_FRESHNESS_HOLD")
        listing=BeautifulSoup(list_bytes.decode("utf-8"),"html.parser")
        detail=BeautifulSoup(detail_bytes.decode("utf-8"),"html.parser")
        links=[a for a in listing.select("a.card-program[href][title]")
               if urljoin(lu,a["href"])==du]
        if len(links)!=1:
            raise ValueError("TPAC_EXACT_LIST_ID_EDGE_HOLD")
        a=links[0]
        title=a["title"].strip()
        if not title or len(title)>180 or title!=text(a.select_one(".card-program__text-title")):
            raise ValueError("TPAC_LIST_TITLE_OWNERSHIP_HOLD")
        articles=detail.select("article.page-program__article")
        if len(articles)!=1 or len(articles[0].select("h1"))!=1 or text(articles[0].select_one("h1"))!=title:
            raise ValueError("TPAC_EXACT_DETAIL_ARTICLE_TITLE_HOLD")
        lp=_period(text(a.select_one(".card-program__text-date")))
        dp=_period(text(articles[0].select_one(".page-program__article-top")))
        boxes=[e for e in detail.select(".page-program__aside-place-showtimes")
               if len(e.select("h3"))==1 and text(e.select_one("h3"))=="場次"]
        if len(boxes)!=1:
            raise ValueError("TPAC_EVENT_SHOW_SECTION_HOLD")
        items=boxes[0].select("ul > li > p")
        if not 1<=len(items)<=40:
            raise ValueError("TPAC_SHOW_COUNT_HOLD")
        starts=[]
        for item in items:
            m=SHOW.fullmatch(text(item))
            if not m:
                raise ValueError("TPAC_SHOW_ROLE_LABEL_HOLD")
            start=datetime.fromisoformat(m.group(1)+"T"+m.group(3)+":00+08:00")
            if WEEK[start.weekday()]!=m.group(2) or not dp[0]<=start.date()<=dp[1]:
                raise ValueError("TPAC_SHOW_WEEKDAY_OR_DETAIL_PERIOD_HOLD")
            starts.append(start)
        if starts!=sorted(set(starts)):
            raise ValueError("TPAC_SHOW_DUPLICATE_ORDER_HOLD")
        future=[s for s in starts if s.astimezone(timezone.utc)>now]
        if not future:
            raise ValueError("TPAC_NO_FUTURE_SHOW_HOLD")
        if future[0].astimezone(timezone.utc)>now+timedelta(days=370):
            raise ValueError("TPAC_SHOW_IMPLAUSIBLY_FAR_HOLD")
        banner=a.select_one("img[alt][src]")
        image=None
        if banner and title in banner["alt"]:
            image_url=banner["src"]
            if urlparse(image_url).scheme=="https" and urlparse(image_url).netloc=="backstage.tpac-taipei.org":
                image=image_url
        venue=detail.select(".page-program__aside-place-venue")
        # Mixed local rooms are NOT a safely accepted room-specific venue.
        location="臺北表演藝術中心" if len(venue)==1 and text(venue[0].select_one("h3"))=="場地" else ""
        holds=["PRICE_NOT_INDEPENDENTLY_ACCEPTED","HALL_SPECIFIC_ROOM_NOT_ACCEPTED"]
        if lp!=dp:
            holds.append("LIST_DETAIL_EVENT_PERIOD_RANGE_CONFLICT_HOLD")
        event={
            "title":title, "url":du, "platform":"臺北表演藝術中心",
            "date":future[0].strftime("%Y-%m-%d %H:%M"),
            "location":location, "type":"戲劇",
            "price":"", "img_url":image, "scraped_at":observed.astimezone(TPE).isoformat(),
            "description":"官方已列出場次："+ "、".join(s.strftime("%m/%d %H:%M") for s in future)
                         +"。詳細演出與票價以官方網站為準。",
            "source_event_id":sid,
            "published":False, "formal_field_pass":False,"golden_accepted":False
        }
        return {
            "decision":"SOURCE_QUALIFIED_CORE_REQUIRES_INDEPENDENT_RELEASE",
            "record":event, "accepted_roles":["EVENT_TITLE","NEXT_EVENT_SHOW_START"],
            "same_source_identity":True,"future_showtimes":len(future),
            "all_showtimes":len(starts),"hold_fields":holds,
            "list_period":[x.isoformat() for x in lp],
            "detail_period":[x.isoformat() for x in dp],
            "receipts":{"list_url":lu,"detail_url":du,"source_event_id":sid,
                        "observed_at":observed.isoformat(),
                        "list_sha256":lsha,"detail_sha256":dsha,
                        "source_role":"FIRST_PARTY_TPAC_PROGRAM"}
        }
    except (ValueError,TypeError,KeyError,OverflowError,UnicodeError) as exc:
        return {"decision":"HOLD","first_failure":str(exc) or type(exc).__name__}


def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-dir",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    source=args.source_dir
    receipt=json.loads((source/"tpac_2040_source_receipt.json").read_text(encoding="utf-8"))
    result=parse_verified_program((source/"tpac_2040_list.html").read_bytes(),
                                  (source/"tpac_2040_detail.html").read_bytes(),
                                  receipt, datetime.now(timezone.utc))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="record"},ensure_ascii=False))
    return 0 if result["decision"]=="SOURCE_QUALIFIED_CORE_REQUIRES_INDEPENDENT_RELEASE" else 49


if __name__=="__main__":
    raise SystemExit(main())
