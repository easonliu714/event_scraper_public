#!/usr/bin/env python3
"""P30-L4-D1 FamiTicket official-detail evidence: label role and stability.

READ ONLY. Official title identity must match per response. A date in a sales,
registration, voucher-validity, or page-copy block is NOT an event time.
Two separated observations of the same public activity detail are evidence
of reliability, not retry/availability polling. NEVER write docs/ nor Golden.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

from bs4 import BeautifulSoup
import requests

SRC = Path(__file__).with_name("p30_l3b_a_famiticket.py")
_spec=importlib.util.spec_from_file_location("p30_l3ba_pinned",SRC)
fami=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fami)

KIND="EVENTRADAR_P30_L4D1_FAMITICKET_DETAIL_ROLE_AND_STABILITY_ONLY"
TARGET_TITLE="2026 ITF 台灣國際旅展"
# These are grammatical roles, not enough by themselves to accept actual
# show dates: field promotion needs a separate source-bound full QA gate.
ROLES={
    "演出日期":"EVENT_OCCURRENCE_EVIDENCE",
    "活動日期":"EVENT_OCCURRENCE_EVIDENCE",
    "展覽日期":"EVENT_OCCURRENCE_EVIDENCE",
    "展出日期":"EVENT_OCCURRENCE_EVIDENCE",
    "比賽日期":"EVENT_OCCURRENCE_EVIDENCE",
    "活動時間":"EVENT_OCCURRENCE_EVIDENCE",
    "展出時間":"EVENT_OCCURRENCE_EVIDENCE",
    "售票時間":"SALE_WINDOW_NOT_EVENT",
    "售票期間":"SALE_WINDOW_NOT_EVENT",
    "開賣時間":"SALE_WINDOW_NOT_EVENT",
    "售票日期":"SALE_WINDOW_NOT_EVENT",
    "報名期間":"REGISTRATION_WINDOW_NOT_EVENT",
    "報名時間":"REGISTRATION_WINDOW_NOT_EVENT",
    "票券使用期限":"VOUCHER_VALIDITY_NOT_EVENT",
    "票券使用期間":"VOUCHER_VALIDITY_NOT_EVENT",
    "使用期限":"VOUCHER_VALIDITY_NOT_EVENT",
    "兌換期限":"VOUCHER_VALIDITY_NOT_EVENT",
}
LABEL=re.compile(r"^("+ "|".join(map(re.escape,sorted(ROLES,key=len,reverse=True)))+ r")[ 　\t]*[:：][ 　\t]*(.*)$")
# Full year only. No title-year, mm/dd-year inference, venue-date inference.
DATE=re.compile(r"(?<!\d)(20\d{2})[./-](0?[1-9]|1[0-2])[./-](0?[1-9]|[12]\d|3[01])(?!\d)")
MAX_ROLES=32

def iso_dates(fragment):
    out=[]
    for match in DATE.finditer(fragment):
        y,m,d=map(int,match.groups())
        try: dt=datetime(y,m,d)
        except ValueError: continue
        value=dt.strftime("%Y-%m-%d")
        if value not in out:out.append(value)
    return out[:4]

def labeled_date_roles(html):
    soup=BeautifulSoup(html,"html.parser")
    for tag in soup(["script","style","noscript"]):tag.decompose()
    lines=[re.sub(r"\s+"," ",x).strip()
           for x in soup.get_text("\n",strip=True).split("\n")]
    out=[]
    for line in lines:
        x=LABEL.fullmatch(line[:360])
        if not x:continue
        label,raw=x.groups()
        dates=iso_dates(raw)
        if not dates:continue
        out.append({"roleLabel":label,"role":ROLES[label],
                    "observedFullYearDates":dates,
                    "evidenceExcerpt":raw[:180],
                    "evidenceStatus":"UNPROMOTED_ROLE_ONLY"})
        if len(out)>=MAX_ROLES:break
    return out

def assess_detail(row,html,net):
    data={"url":row["official_url"],"listTitle":row["title"],
          "http":net,"identity":"NOT_VERIFIED","headingCount":0,
          "roles":[],"dateStart":None,"dateEnd":None,
          "eventTimeVerified":False,"saleStatus":"UNKNOWN",
          "price":None,"goldenVerified":False}
    if html is None:
        data["identity"]="HTTP_OR_CONTENT_HOLD"
        return data
    match=fami.sample_detail(html,row)
    data["headingCount"]=match["heading_count"]
    if match["state"]!="DETAIL_TITLE_VERIFIED":
        data["identity"]="DETAIL_TITLE_IDENTITY_HOLD"
        return data
    data["identity"]="EXACT_LIST_DETAIL_TITLE_MATCH"
    data["roles"]=labeled_date_roles(html)
    # Even a labeled event interval can be cancellation/old date; no
    # accepted schedule without reconciling against official session state.
    return data

def repeat_stability(results):
    if len(results)!=2:raise ValueError("MUST_HAVE_EXACT_TWO_OBSERVATIONS")
    states=[r["identity"] for r in results]
    if all(x=="EXACT_LIST_DETAIL_TITLE_MATCH" for x in states):
        return "SAMPLED_TWICE_IDENTITY_MATCH_NOT_EVENT_GOLDEN"
    if any(x=="EXACT_LIST_DETAIL_TITLE_MATCH" for x in states):
        return "INTERMITTENT_TITLE_MATCH_HOLD"
    return "TWO_RESPONSES_WITHOUT_TITLE_HOLD"

def build(session,sleep=time.sleep):
    list_html,list_meta=fami.fetch(session,fami.LIST)
    candidates,parse=fami.parse_list(list_html) if list_html else ([],{"candidate_count":0})
    same=[r for r in candidates if r["title"]==TARGET_TITLE]
    if len(same)!=1:
        return [],{"kind":KIND,"listHttp":list_meta,"listParse":parse,
                   "state":"TARGET_TITLE_UNIQUE_IDENTITY_HOLD",
                   "sampleCount":0,"goldenAccepted":False}
    row=same[0]
    samples=[]
    for i in range(2):
        sleep(1.2)
        page,network=fami.fetch(session,row["official_url"],detail=True)
        samples.append(assess_detail(row,page,network))
    result={"kind":KIND,"source":"FamiTicket",
            "sourceListUrl":fami.LIST,
            "targetListTitle":TARGET_TITLE,"targetOfficialUrl":row["official_url"],
            "observedAtUTC":datetime.now(timezone.utc).isoformat(),
            "listHttp":list_meta,"listParse":parse,
            "sourceRole":"OFFICIAL_TICKET_PLATFORM_NOT_ORGANISER",
            "observations":samples,
            "state":repeat_stability(samples),"sampleCount":2,
            "maxListGET":1,"maxDetailGET":2,"intentionalSeparatedObservations":True,
            "noRetries":True,"noLogin":True,"noCheckout":True,
            "eventDateStart":None,"eventDateEnd":None,
            "ticketStatus":"UNKNOWN","price":None,"goldenAccepted":False,
            "published":False,"writerExecuted":False,"notifierExecuted":False,
            "autoHidden":0,"sourceRuntime":"DORMANT",
            "completeCatalogProven":False}
    return candidates,result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    target=Path(a.out_dir).resolve()
    docs=Path("docs").resolve()
    if target==docs or docs in target.parents:
        ap.error("HOLD_OFFICIAL_WRITER_PATH")
    with requests.Session() as sess:
        candidates,report=build(sess)
    target.mkdir(parents=True,exist_ok=True)
    (target/"diagnostics.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Only the target detail evidence is exported; no output full HTML or
    # unreviewed old JSON snapshots / stale long-term catalog.
    sample={"platform":"FamiTicket","title":report.get("targetListTitle"),
            "officialUrl":report.get("targetOfficialUrl"),
            "dateStart":None,"dateEnd":None,"ticketStatus":"UNKNOWN",
            "price":None,"dataCompleteness":"DETAIL_ROLE_OBSERVED_NOT_PROMOTED",
            "eventTimeVerified":False,"goldenVerified":False,"published":False}
    (target/"sample_candidate.json").write_text(json.dumps(sample,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FAMITICKET_L4D_LIST",report["listHttp"].get("http_status"),report["listParse"].get("candidate_count"))
    print("FAMITICKET_L4D_STABILITY",report["state"],
          "IDENTITIES",*[x["identity"] for x in report.get("observations",[])])
    print("FAMITICKET_L4D_ROLE_LABELS",*[r["roleLabel"]+":"+r["role"] for d in report.get("observations",[]) for r in d["roles"]])
    if len(candidates)==0 or report.get("sampleCount")!=2:
        print("HOLD P30_L4D_FAMITICKET_LIST_OR_SAMPLE")
        sys.exit(2)
    print("PASS P30_L4D1_TWO_OFFICIAL_RESPONSES_AUDITED")
    if report["state"]!="SAMPLED_TWICE_IDENTITY_MATCH_NOT_EVENT_GOLDEN":
        print("HOLD P30_L4D1_DETAIL_IDENTITY_NOT_STABLE")
    print("GOLDEN=0, DATE_PROMOTED=0, TICKET_STATUS=UNKNOWN")

if __name__=="__main__":main()
