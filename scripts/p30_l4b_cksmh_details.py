#!/usr/bin/env python3
"""P30-L4-B: CKSMH official activity detail / sessions evidence -> isolated 44-row UAT.

Pinned parent artifact, five exact CKSMH actIds, same-host TLS-verified public HTML.
Fail closed per field: title -> session/full dates -> venues -> short summary.
No Pages write, no scheduler, no notifier, no guessed category/tickets/availability.
"""
import argparse
import hashlib
import json
import re
import time
import unicodedata
from datetime import datetime, date, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

KIND = "EVENTRADAR_P30_L4B_CKSMH_DETAIL_CANDIDATE_ONLY"
PARENT_KIND = "EVENTRADAR_P30_ANDROID_SMOKE_CANDIDATE_NOT_GOLDEN"
PARENT_RUN = "40281136558"
HOST = "event.culture.tw"
DETAIL = "/mocweb/reg/CKSMH/Detail.init.ctr"
PORTAL = "/CKSMH/portal/Registration/C0103MAction"
LIST_URL = "https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr"
UA = "EventRadar-P30-readonly/1.0 (github.com/easonliu714/event_scraper_public)"
MAX_HTML = 1_500_000
MAX_ROWS = 5
SESSION_RE = re.compile(
    r"(20\d{2}/\d{1,2}/\d{1,2})\s+(\d{2}:\d{2})\s*[~～]\s*"
    r"(20\d{2}/\d{1,2}/\d{1,2})\s+(\d{2}:\d{2})")
DAY_RANGE_RE = re.compile(
    r"(20\d{2}/\d{1,2}/\d{1,2})\s*[~～]\s*(20\d{2}/\d{1,2}/\d{1,2})")
CHINESE_RANGE_RE = re.compile(
    r"(20\d{2})年(\d{1,2})月(\d{1,2})日\s*[~～至]\s*"
    r"(20\d{2})年(\d{1,2})月(\d{1,2})日")
STOPWORDS = ("加入Google日曆","付款流程","恭喜您報名成功","隱私權及安全政策宣示",
             "最佳瀏覽狀態","活動注意事項","瀏覽人次")


def normalize(text):
    return re.sub(r"\s+","",unicodedata.normalize("NFKC",str(text))).casefold()


def short_title(text):
    """Strip a known legacy image-accessibility label, never fuzzy-match identities."""
    s=re.sub(r"\s+"," ",text).strip()
    for suffix in ("圖片說明","圖片描述","圖片資訊"):
        if s.endswith(suffix):
            s=s[:-len(suffix)].rstrip()
    return s


def exact_act_id(url):
    try:
        p=urlsplit(url)
        if (p.scheme!="https" or p.hostname!=HOST or p.username or p.password
                or p.port not in (None,443) or "\\" in p.path
                or ".." in p.path.split("/")):
            return None
        if p.path.split(";",1)[0] not in (DETAIL,PORTAL):
            return None
        values=parse_qs(p.query).get("actId",[])
        if len(values)!=1 or not re.fullmatch(r"[0-9]{3,9}",values[0]):
            return None
        return values[0]
    except ValueError:
        return None


def fetch_listing(session,timeout=12):
    """Single full official CKSMH list GET; no content from other domains."""
    try:
        with session.get(LIST_URL,allow_redirects=False,stream=True,
                         timeout=(6,timeout),headers={"User-Agent":UA,
                         "Accept-Language":"zh-TW,zh;q=0.9"}) as resp:
            meta={"state":"HTTP_OK" if resp.status_code==200 else "HTTP_ERROR",
                  "http_status":resp.status_code,"url":LIST_URL,
                  "content_type":resp.headers.get("content-type","")[:100]}
            if resp.status_code!=200:return None,meta
            if "text/html" not in meta["content_type"].lower():
                meta["state"]="NON_HTML";return None,meta
            blob=bytearray()
            for part in resp.iter_content(chunk_size=32768):
                blob.extend(part)
                if len(blob)>MAX_HTML:
                    meta["state"]="TOO_LARGE";return None,meta
            if not blob:
                meta["state"]="EMPTY_BODY";return None,meta
            meta["sha256"]=hashlib.sha256(blob).hexdigest()
            return bytes(blob),meta
    except requests.RequestException as err:
        return None,{"state":"NETWORK_ERROR","error_type":type(err).__name__,
                     "url":LIST_URL}


def parse_list_bound(page,events):
    """No global regex: each date/location must be inside one actId-bound card.

    Page 'Query.list' contains activity cards with their own '活動時間' and
    '活動地點'. We accept a card only when its sole CKSMH detail ID equals
    a frozen candidate and its linked title is identical after alt-label strip.
    """
    soup=BeautifulSoup(page,"html.parser")
    targets={exact_act_id(x["officialUrl"]):x for x in events}
    bound={}
    for a in soup.find_all("a",href=True):
        id_num=exact_act_id(urljoin(LIST_URL,a.get("href","")))
        if id_num not in targets or id_num in bound:continue
        target=targets[id_num]
        if normalize(short_title(a.get_text(" ",strip=True)))!=normalize(short_title(target["title"])):
            continue
        node=a
        for depth in range(7):
            node=node.parent
            if node is None:break
            anchors=node.find_all("a",href=True)
            ids={exact_act_id(urljoin(LIST_URL,link.get("href","")))
                 for link in anchors}
            ids.discard(None)
            if ids!={id_num}:break
            value=" ".join(node.stripped_strings)
            if len(value)>3500:break
            pattern=re.search(r"活動時間\s*(20\d{2}/\d{1,2}/\d{1,2})\s*[~～]\s*"
                              r"(20\d{2}/\d{1,2}/\d{1,2})",value)
            if not pattern:continue
            try:
                start,end=(date.fromisoformat(x.replace("/","-")) for x in pattern.groups())
            except ValueError:continue
            if start>end:continue
            vm=re.search(r"活動地點\s*(.*?)\s*活動時間",value)
            venue=re.sub(r"\s+"," ",vm.group(1)).strip() if vm else None
            if venue and (len(venue)>100 or venue=="地點詳如內頁"):
                venue=None
            bound[id_num]={"title":short_title(target["title"]),
                           "dateStart":start.isoformat(),"dateEnd":end.isoformat(),
                           "venue":venue,"actId":id_num,
                           "sourceUrl":LIST_URL,
                           "sourceRole":"OFFICIAL_LIST_ACTID_BOUND_FIELDS"}
            break
    return bound


def fetch(session,url,timeout=12):
    """Allow only redirect on same actId and same official host; no retry."""
    expected=exact_act_id(url)
    if not expected:
        return None,{"state":"UNSAFE_SOURCE_URL"}
    start=url
    trail=[]
    for _ in range(3):
        if exact_act_id(url)!=expected:
            return None,{"state":"REDIRECT_ID_OR_ORIGIN_HOLD","trail":trail}
        try:
            with session.get(url,allow_redirects=False,stream=True,timeout=(6,timeout),
                             headers={"User-Agent":UA,"Accept-Language":"zh-TW,zh;q=0.9"}) as resp:
                code=resp.status_code
                trail.append({"url":url,"http":code})
                if code in (301,302,303,307,308):
                    location=resp.headers.get("location")
                    if not location:
                        return None,{"state":"REDIRECT_LOCATION_ABSENT","trail":trail}
                    url=urljoin(url,location)
                    continue
                typ=resp.headers.get("content-type","")[:100]
                meta={"state":"HTTP_OK" if code==200 else "HTTP_ERROR",
                      "source":start,"observed_url":url,"http_status":code,
                      "content_type":typ,"trail":trail}
                if code!=200:
                    return None,meta
                if "text/html" not in typ.lower():
                    meta["state"]="NON_HTML"
                    return None,meta
                data=bytearray()
                for chunk in resp.iter_content(chunk_size=32768):
                    data.extend(chunk)
                    if len(data)>MAX_HTML:
                        meta["state"]="OVERSIZE"
                        return None,meta
                if not data:
                    meta["state"]="EMPTY_HTML"
                    return None,meta
                meta["sha256"]=hashlib.sha256(data).hexdigest()
                meta["bytes"]=len(data)
                return bytes(data),meta
        except requests.RequestException as ex:
            return None,{"state":"NETWORK_ERROR","error_type":type(ex).__name__,
                          "source":start,"trail":trail}
    return None,{"state":"REDIRECT_LIMIT","trail":trail}


def parse_dates(values):
    """Validate full-year, chronological instants; never infer year or timezone."""
    a,at,b,bt=values
    start=datetime.fromisoformat(a.replace("/","-")+"T"+at)
    end=datetime.fromisoformat(b.replace("/","-")+"T"+bt)
    if start>end:
        raise ValueError("INVERTED_SESSION_TIME")
    if (end-start).days>365*3:
        raise ValueError("SESSION_TOO_LONG")
    return {"start":start.isoformat(timespec="minutes"),"end":end.isoformat(timespec="minutes"),
            "startDate":start.date().isoformat(),"endDate":end.date().isoformat(),
            "timeZone":"Asia/Taipei","role":"OFFICIAL_SESSION_TIME"}


def extract(page,event):
    """Evidence bound by exact top-page title + source actId; fields independent."""
    soup=BeautifulSoup(page,"html.parser")
    candidate=short_title(event["title"])
    ckey=normalize(candidate)
    strings=[s.strip() for s in soup.stripped_strings if s.strip()]
    # The official detail shows title at the beginning; no similarity threshold.
    top=[normalize(s) for s in strings[:65]]
    if ckey not in top:
        return {"state":"TITLE_IDENTITY_HOLD","candidateTitle":event["title"],
                "topTitleSample":strings[:5], "dateStart":None,"dateEnd":None,
                "venue":None,"summary":None,"sessions":[]}
    text=" ".join(strings)
    section=text
    for mark in ("場次資料","Session Information"):
        pos=text.find(mark)
        if pos>=0:
            section=text[pos:]
            break
    for terminator in ("活動內容介紹","Event Details","主辦單位"):
        pos=section.find(terminator)
        if pos>=0 and pos>0:
            section=section[:pos]
            break
    matches=[]
    seen=set()
    for m in SESSION_RE.findall(section):
        try:
            s=parse_dates(m)
        except (ValueError,TypeError):
            continue
        key=(s["start"],s["end"])
        if key not in seen:
            seen.add(key)
            matches.append(s)
        if len(matches)>=20:break
    matches.sort(key=lambda s:s["start"])
    result={"state":"DETAIL_TITLE_VERIFIED","candidateTitle":event["title"],
            "officialTitle":candidate,"dateStart":None,"dateEnd":None,
            "timeRole":"UNKNOWN","sessions":matches,"venue":None,"summary":None,
            "summaryRole":"NONE","venueRole":"NONE","sessionCount":len(matches)}
    if matches:
        result.update({"dateStart":matches[0]["startDate"],"dateEnd":max(x["endDate"] for x in matches),
                       "timeRole":"OFFICIAL_SINGLE_SESSION" if len(matches)==1
                                  else "OFFICIAL_MULTIPLE_SESSIONS_BOUNDS"})
    else:
        # Separate full-year date span in event summary; don't search entire description.
        snippet=" ".join(strings[:55])
        spans=DAY_RANGE_RE.findall(snippet)
        if len(spans)==1:
            a,b=(date.fromisoformat(v.replace("/","-")) for v in spans[0])
            if a<=b:
                result.update({"dateStart":a.isoformat(),"dateEnd":b.isoformat(),
                               "timeRole":"OFFICIAL_DETAIL_DATE_RANGE"})
        if result["dateStart"] is None:
            ranges=CHINESE_RANGE_RE.findall(snippet)
            if len(ranges)==1:
                yr,mo,dy,yr2,mo2,dy2=map(int,ranges[0])
                a,b=date(yr,mo,dy),date(yr2,mo2,dy2)
                if a<=b:
                    result.update({"dateStart":a.isoformat(),"dateEnd":b.isoformat(),
                                   "timeRole":"OFFICIAL_DETAIL_DATE_RANGE"})
    # Prefer a map-backed visible venue name. Multiple distinct venues => preserve candidates only.
    venues=[]
    for a in soup.find_all("a",href=True):
        href=a.get("href","")
        label=" ".join(a.stripped_strings).strip()
        if ("google.com/maps" in href or "maps.google.com" in href) and 2<=len(label)<=120:
            if label not in venues:venues.append(label)
    result["venueCandidates"]=venues[:12]
    if len(venues)==1:
        result["venue"]=venues[0]
        result["venueRole"]="OFFICIAL_DETAIL_MAP_LINK"
    # Short summary only inside the content-introduction section; never scrape entire page.
    for marker in ("活動內容介紹","Event Details"):
        idx=text.find(marker)
        if idx>=0:
            section=text[idx+len(marker):]
            for stop in STOPWORDS+("地址：","地址:","隱私權"):
                loc=section.find(stop)
                if loc>=0: section=section[:loc]
            section=re.sub(r"\s+"," ",section).strip()
            section=re.sub(r"^(Image\s*)+","",section,flags=re.IGNORECASE).strip()
            if 25<=len(section):
                result["summary"]=section[:360]
                result["summaryRole"]="OFFICIAL_DETAIL_INTRO_EXCERPT"
            break
    return result


def validate_parent(parent):
    if not isinstance(parent,dict) or parent.get("kind")!=PARENT_KIND:
        raise ValueError("HOLD_PARENT_SCHEMA")
    if parent.get("count")!=44 or len(parent.get("items",[]))!=44:
        raise ValueError("HOLD_PARENT_COUNT")
    for k,v in (("published",False),("goldenAccepted",False),
                ("writerExecuted",False),("notificationExecuted",False),
                ("autoHidden",0),("sourceRuntime","DORMANT")):
        if parent.get(k)!=v:
            raise ValueError("HOLD_PARENT_FLAG_"+k)
    rows=[r for r in parent["items"] if r.get("platform")=="中正紀念堂"]
    if len(rows)!=MAX_ROWS:
        raise ValueError("HOLD_CKSMH_FIVE")
    acts=[]
    for r in rows:
        act=exact_act_id(r.get("officialUrl"))
        if not act or not isinstance(r.get("title"),str) or len(r["title"])<4:
            raise ValueError("HOLD_CKSMH_OFFICIAL_ID_TITLE")
        if r.get("dateStart") is not None or r.get("dateEnd") is not None:
            raise ValueError("HOLD_CKSMH_BASE_HAS_UNVERIFIED_DATE")
        acts.append(act)
    if len(set(acts))!=MAX_ROWS:
        raise ValueError("HOLD_DUPLICATE_CKSMH_ID")
    return rows


def enrich(parent,records,listing=None):
    src=validate_parent(parent)
    ids={x["id"]:x for x in src}
    if len(records)!=MAX_ROWS or {x["id"] for x in records}!=set(ids):
        raise ValueError("HOLD_EVIDENCE_ID_SET")
    result=json.loads(json.dumps(parent,ensure_ascii=False))
    target={x["id"]:x for x in result["items"]}
    counters={"http_ok":0,"title_verified":0,"date_bound":0,"venue_bound":0,
              "summary_bound":0,"multi_session":0}
    for rec in records:
        row=target[rec["id"]]
        original=ids[rec["id"]]
        if rec["officialUrl"]!=original["officialUrl"] or rec["title"]!=original["title"]:
            raise ValueError("HOLD_EVIDENCE_TITLE_URL_MISMATCH")
        if rec.get("http",{}).get("state")=="HTTP_OK":
            counters["http_ok"]+=1
        fields=rec.get("fields")
        if not fields or fields["state"]!="DETAIL_TITLE_VERIFIED":
            continue
        counters["title_verified"]+=1
        row["title"]=fields["officialTitle"]  # Removes only the verified image-alt suffix.
        row["cksmhDetailStatus"]="OFFICIAL_TITLE_VERIFIED"
        row["detailEvidenceSHA256"]=rec["http"]["sha256"]
        row["detailEvidenceRole"]="P30_L4B_CKSMH_OFFICIAL_DETAIL"
        detail_id=exact_act_id(rec["officialUrl"])
        if rec.get("actId",detail_id)!=detail_id:
            raise ValueError("HOLD_EVIDENCE_ACTID_MISMATCH")
        list_fields=(listing or {}).get(detail_id)
        if list_fields and (list_fields["title"]!=fields["officialTitle"]
                            or list_fields["actId"]!=exact_act_id(row["officialUrl"])):
            raise ValueError("HOLD_LIST_DETAIL_IDENTITY_MISMATCH")
        if fields["dateStart"] and fields["dateEnd"]:
            row["dateStart"],row["dateEnd"]=fields["dateStart"],fields["dateEnd"]
            row["timeRole"]=fields["timeRole"]
            row["sourceLevel"]="CKSMH_DETAIL_DATE_CANDIDATE"
            counters["date_bound"]+=1
        if list_fields and not fields["dateStart"]:
            row["dateStart"]=list_fields["dateStart"]
            row["dateEnd"]=list_fields["dateEnd"]
            row["timeRole"]="OFFICIAL_LIST_ACTID_BOUND_DATE_RANGE"
            row["sourceLevel"]="CKSMH_LIST_DATE_WITH_DETAIL_TITLE_CONFIRMED"
            row["dateEvidenceSourceUrl"]=LIST_URL
            counters["date_bound"]+=1
        if fields["sessions"]:
            row["sessions"]=fields["sessions"]
            if len(fields["sessions"])>1:counters["multi_session"]+=1
        if list_fields and fields.get("dateStart"):
            # Cross-check the list by actual days when detail sessions are available.
            if list_fields["dateStart"]!=fields["dateStart"] or list_fields["dateEnd"]!=fields["dateEnd"]:
                row["listDetailDateComparison"]="MISMATCH_REVIEW_NOT_AUTOCORRECTED"
        if fields.get("venue"):
            row["venue"]=fields["venue"]
            row["venueRole"]=fields["venueRole"]
            counters["venue_bound"]+=1
        elif list_fields and list_fields.get("venue"):
            row["venue"]=list_fields["venue"]
            row["venueRole"]="OFFICIAL_LIST_ACTID_BOUND_VENUE"
            counters["venue_bound"]+=1
        if fields.get("summary"):
            row["summary"]=fields["summary"]
            row["summaryRole"]=fields["summaryRole"]
            counters["summary_bound"]+=1
    if counters["date_bound"]==0:
        raise ValueError("HOLD_NO_CKSMH_DATE_BOUND")
    result["cksmhDetailEvidenceKind"]=KIND
    result["cksmhDetailCounts"]=counters
    result["cksmhDetailSourceRun"]="P30_L4B_ONE_SHOT"
    result["published"]=False
    return result,counters


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--parent",required=True)
    ap.add_argument("--out-dir",required=True)
    args=ap.parse_args(argv)
    out=Path(args.out_dir).resolve()
    formal=Path("docs").resolve()
    if out==formal or formal in out.parents:ap.error("HOLD_PAGES_WRITER")
    parent_blob=Path(args.parent).read_bytes()
    parent=json.loads(parent_blob.decode("utf-8"))
    rows=validate_parent(parent)
    evidence=[]
    listing_fields={}
    listing_meta={"state":"NOT_ATTEMPTED"}
    with requests.Session() as sess:
        for i,item in enumerate(rows):
            if i: time.sleep(1.2)
            html,http=fetch(sess,item["officialUrl"])
            fields=extract(html,item) if html is not None else None
            record={"id":item["id"],"title":item["title"],
                    "officialUrl":item["officialUrl"],"actId":exact_act_id(item["officialUrl"]),
                    "http":http,"fields":fields}
            evidence.append(record)
            print("DETAIL",record["actId"],http["state"],http.get("http_status"),
                  "TITLE",fields["state"] if fields else "HTTP_HOLD",
                  "DATE",fields.get("dateStart") if fields else None,
                  "VENUE",fields.get("venue") if fields else None,
                  "SESSIONS",fields.get("sessionCount") if fields else None)
        time.sleep(1.2)
        listing_html,listing_meta=fetch_listing(sess)
        if listing_html is not None:
            listing_fields=parse_list_bound(listing_html,rows)
        print("OFFICIAL_LIST",listing_meta["state"],listing_meta.get("http_status"),
              "ACTID_BOUND",len(listing_fields))
    output={"kind":KIND,"generatedAtUTC":datetime.now(timezone.utc).isoformat(),
            "parentRun":PARENT_RUN,"parentSHA256":hashlib.sha256(parent_blob).hexdigest(),
            "records":evidence,"listingBound":listing_fields,"listingHTTP":listing_meta,
            "fetchMax":MAX_ROWS+1,"noRetries":True,
            "sourceRuntime":"DORMANT","published":False,"goldenAccepted":False,
            "writerExecuted":False,"notificationExecuted":False,"autoHidden":0}
    out.mkdir(parents=True,exist_ok=True)
    (out/"detail_evidence.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    try:
        new,counts=enrich(parent,evidence,listing_fields)
    except ValueError as e:
        (out/"hold_diagnostics.json").write_text(
            json.dumps({"state":str(e),"records":len(evidence)},ensure_ascii=False,indent=2)+"\n",
            encoding="utf-8")
        print("HOLD P30_L4B_ENRICHMENT",str(e))
        raise SystemExit(2)
    (out/"data.json").write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS P30_L4B_CKSMH_DETAIL_EVIDENCE",counts)
    print("PASS P30_L4B_44_IDENTITY_AND_NO_PUBLISH")


if __name__=="__main__":
    main()
