#!/usr/bin/env python3
"""P30-L4-C: CKSMH semantic date roles. Separate EVENT SESSION and REGISTRATION.

Strict event/title/actId and single bounded HTTPS detail GET per frozen source.
Never use a registration window as an event date. No official Pages/writer/GOLDEN.
"""
import argparse
import hashlib
import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from p30_l4b_cksmh_details import exact_act_id, fetch, short_title, normalize

KIND = "EVENTRADAR_P30_L4C_CKSMH_DATE_ROLE_EVIDENCE_NOT_GOLDEN"
PARENT_KIND = "EVENTRADAR_P30_ANDROID_SMOKE_CANDIDATE_NOT_GOLDEN"
PARENT_RUN = "40285154986"
CKSMH_COUNT = 5
MAX_SESSION = 20

SECTION_START = re.compile(r"場\s*次\s*資\s*料")
SESSION_MARK = re.compile(r"場\s*次\s*[:：]")
REG_MARK = re.compile(r"報\s*名\s*期\s*間")
INTRO_MARK = re.compile(r"活動\s*內\s*容\s*介\s*紹")
VENUE_MARK = re.compile(r"場\s*地\s*[:：]?")
NEXT_INFO = re.compile(r"(?:名\s*額|講\s*師|名額剩|正取剩|報\s*名\s*期\s*間|場\s*次\s*介\s*紹)")
FULL_RANGE = re.compile(
    r"(?P<d1>20\d{2}/\d{1,2}/\d{1,2})\s+"
    r"(?P<t1>\d{2}:\d{2})\s*[～~\-]\s*"
    r"(?P<d2>20\d{2}/\d{1,2}/\d{1,2})\s+"
    r"(?P<t2>\d{2}:\d{2})")
HEADING_RANGE = re.compile(
    r"(?P<d>20\d{2}/\d{1,2}/\d{1,2})\s*"
    r"(?:[\(（]\s*[一二三四五六日天]\s*[\)）])?\s*"
    r"(?P<t1>\d{2}:?\d{2})\s*[～~\-]\s*(?P<t2>\d{2}:?\d{2})(?![/\d:])")
DATEISH = re.compile(r"20\d{2}/\d{1,2}/\d{1,2}")


def iso_time(s):
    if re.fullmatch(r"\d{4}",s):return s[:2]+":"+s[2:]
    if re.fullmatch(r"\d{2}:\d{2}",s):return s
    raise ValueError("INVALID_CLOCK")


def date_pair(d1,t1,d2,t2):
    a=datetime.fromisoformat(d1.replace("/","-")+"T"+iso_time(t1))
    b=datetime.fromisoformat(d2.replace("/","-")+"T"+iso_time(t2))
    if b<a or (b-a).days>370:
        raise ValueError("TIME_REVERSED_OR_TOO_LONG")
    return {"start":a.isoformat(timespec="minutes"),"end":b.isoformat(timespec="minutes"),
            "timeZone":"Asia/Taipei"}


def exact_one(values):
    """Require exactly one unique occurrence, not one arbitrary date from prose."""
    seen={(x["start"],x["end"]) for x in values}
    return values[0] if len(seen)==1 else None


def occurrence(section):
    values=[]
    for m in FULL_RANGE.finditer(section):
        try:values.append(date_pair(m["d1"],m["t1"],m["d2"],m["t2"]))
        except ValueError:pass
    for m in HEADING_RANGE.finditer(section):
        try:values.append(date_pair(m["d"],m["t1"],m["d"],m["t2"]))
        except ValueError:pass
    return exact_one(values)


def paragraphs(page):
    soup=BeautifulSoup(page,"html.parser")
    # NFKC normalizes fullwidth digits/whitespace while keeping content literal.
    return unicodedata.normalize("NFKC"," ".join(soup.stripped_strings))


def parse_event(page,row):
    soup=BeautifulSoup(page,"html.parser")
    title=short_title(row["title"])
    exact=[normalize(x) for x in list(soup.stripped_strings)[:65]]
    if normalize(title) not in exact:
        return {"state":"HOLD_EVENT_TITLE_IDENTITY","sessions":[],"registrationWindows":[],
                "eventDateStart":None,"eventDateEnd":None}
    whole=paragraphs(page)
    begin=SECTION_START.search(whole)
    if not begin:
        # No sessions: retain L4B date only if the role was a separate
        # uniquely actId-bound official listing PERIOD; it is not a session.
        return {"state":"NO_SESSION_SECTION","sessions":[],"registrationWindows":[],
                "eventDateStart":None,"eventDateEnd":None}
    segment=whole[begin.end():]
    stop=INTRO_MARK.search(segment)
    if stop:segment=segment[:stop.start()]
    chunks=SESSION_MARK.split(segment)[1:]
    sessions=[]
    registrations=[]
    warnings=[]
    for index,chunk in enumerate(chunks):
        mark=REG_MARK.search(chunk)
        header=chunk[:mark.start()] if mark else chunk
        # A bare '2026/10/16 ~ ...' after '報名期間' must never be used as EVENT.
        event=occurrence(header)
        if not event:
            warnings.append({"block":index+1,"reason":"EVENT_TIME_UNPROVEN"})
            continue
        # One session per explicit '場次:' block. No duplicate acts or borrowed dates.
        label=header[:240]
        if len(label)>180:label=label[:180]
        v=VENUE_MARK.search(chunk)
        venue=None
        if v:
            next_marker=NEXT_INFO.search(chunk,v.end())
            raw=chunk[v.end():next_marker.start() if next_marker else len(chunk)]
            raw=re.sub(r"\s+"," ",raw).strip()
            raw=re.sub(r"(?:名額剩|正取剩|名單|報名|登入).*$","",raw).strip()
            if 2<=len(raw)<=160:venue=raw
        entry={"ordinal":index+1,"title":label.strip(),"start":event["start"],
               "end":event["end"],"timeZone":"Asia/Taipei",
               "role":"OFFICIAL_EVENT_SESSION_TIME","venue":venue}
        if mark:
            # Registration window is captured separately and only after the
            # explicit label, in this SAME session block.
            regpart=chunk[mark.end():]
            rm=FULL_RANGE.search(regpart)
            if rm:
                try:
                    r=date_pair(rm["d1"],rm["t1"],rm["d2"],rm["t2"])
                    entry["registration"]={**r,"role":"OFFICIAL_REGISTRATION_WINDOW"}
                    registrations.append({**r,"sessionOrdinal":index+1,
                                          "role":"OFFICIAL_REGISTRATION_WINDOW"})
                except ValueError:
                    warnings.append({"block":index+1,"reason":"REG_WINDOW_INVALID"})
        sessions.append(entry)
    # Extra date-like values in blocks lacking an event are not proof.
    if not sessions:
        return {"state":"HOLD_NO_OFFICIAL_EVENT_SESSION","sessions":[],
                "registrationWindows":registrations,
                "eventDateStart":None,"eventDateEnd":None,"warnings":warnings,
                "sessionBlocks":len(chunks)}
    dates=sorted(x["start"][:10] for x in sessions)
    ends=sorted(x["end"][:10] for x in sessions)
    return {"state":"OFFICIAL_EVENT_SESSIONS_VERIFIED",
            "sessions":sessions,"registrationWindows":registrations,
            "eventDateStart":dates[0],"eventDateEnd":ends[-1],
            "eventTimeRole":"OFFICIAL_EVENT_SESSION_BOUNDS",
            "sessionBlocks":len(chunks),"warnings":warnings}


def verify_parent(obj):
    if not isinstance(obj,dict) or obj.get("kind")!=PARENT_KIND:
        raise ValueError("HOLD_PARENT_KIND")
    if obj.get("count")!=44 or len(obj.get("items",[]))!=44:
        raise ValueError("HOLD_PARENT_44")
    for k,v in (("sourceRuntime","DORMANT"),("published",False),
                ("goldenAccepted",False),("autoHidden",0),
                ("writerExecuted",False),("notificationExecuted",False)):
        if obj.get(k)!=v:raise ValueError("HOLD_PARENT_FLAG_"+k)
    rows=[r for r in obj["items"] if r.get("platform")=="中正紀念堂"]
    if len(rows)!=5 or len({exact_act_id(r.get("officialUrl")) for r in rows})!=5:
        raise ValueError("HOLD_CKSMH_SOURCE_ID")
    for r in rows:
        if not exact_act_id(r["officialUrl"]) or r.get("ticketStatus")!="UNKNOWN":
            raise ValueError("HOLD_CKSMH_INVALID")
    return rows


def build(parent,evidences):
    src=verify_parent(parent)
    if len(evidences)!=5 or {e["id"] for e in evidences}!={r["id"] for r in src}:
        raise ValueError("HOLD_EVIDENCE_EXACT_FIVE")
    result=json.loads(json.dumps(parent,ensure_ascii=False))
    byid={x["id"]:x for x in result["items"]}
    source={x["id"]:x for x in src}
    counts={"httpOK":0,"eventSessionsBound":0,"registrationWindowsBound":0,
            "eventsWithSessionTime":0,"noSessionExhibitions":0,
            "unverifiedSessionEvents":0}
    for evidence in evidences:
        old=source[evidence["id"]]
        row=byid[old["id"]]
        if evidence["title"]!=old["title"] or evidence["officialUrl"]!=old["officialUrl"]:
            raise ValueError("HOLD_IDENTITY_URL_MISMATCH")
        if evidence["actId"]!=exact_act_id(old["officialUrl"]):
            raise ValueError("HOLD_ACTID_MISMATCH")
        if evidence["http"].get("state")=="HTTP_OK":counts["httpOK"]+=1
        role=evidence["roles"]
        row["semanticDateEvidenceKind"]=KIND
        row["semanticDateEvidenceState"]=role["state"]
        row["semanticDateEvidenceSHA256"]=evidence["http"].get("sha256")
        if role["state"]=="OFFICIAL_EVENT_SESSIONS_VERIFIED":
            # Discard incorrect L4B registration windows masquerading as sessions.
            row["sessions"]=role["sessions"]
            row["registrationWindows"]=role["registrationWindows"]
            row["dateStart"]=role["eventDateStart"]
            row["dateEnd"]=role["eventDateEnd"]
            row["timeRole"]=role["eventTimeRole"]
            row["sourceLevel"]="CKSMH_SESSIONS_AND_REGISTRATION_DISTINCT_CANDIDATE"
            venues=[s["venue"] for s in role["sessions"]]
            if venues and all(venues) and len(set(venues))==1:
                row["venue"]=venues[0]
                row.pop("venueNote",None)
            elif len(venues)>1:
                row["venue"]=None
                row["venueNote"]="多場次：場地可能不同，詳見各場次"
            counts["eventsWithSessionTime"]+=1
            counts["eventSessionsBound"]+=len(role["sessions"])
            counts["registrationWindowsBound"]+=len(role["registrationWindows"])
        elif old.get("timeRole")=="OFFICIAL_LIST_ACTID_BOUND_DATE_RANGE":
            # This is official list period, not enrollment and not daily open.
            row["timeRole"]="OFFICIAL_LIST_PERIOD_UNCLASSIFIED"
            row["listPeriodStart"]=old.get("dateStart")
            row["listPeriodEnd"]=old.get("dateEnd")
            row["dateStart"]=None
            row["dateEnd"]=None
            row["sourceLevel"]="CKSMH_LIST_PERIOD_WITH_DETAIL_TITLE_CONFIRMED"
            counts["noSessionExhibitions"]+=1
        elif old.get("timeRole","").startswith("OFFICIAL_"):
            # NO verified event sessions: fail closed and clear potentially
            # mislabelled registration spans inherited from L4B.
            row["dateStart"]=None
            row["dateEnd"]=None
            row["sessions"]=[]
            row["timeRole"]="UNKNOWN_SESSION_DATE_NOT_VERIFIED"
            counts["unverifiedSessionEvents"]+=1
    result["cksmhSemanticRolesKind"]=KIND
    result["cksmhSemanticCounts"]=counts
    return result,counts


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--parent",required=True)
    ap.add_argument("--out-dir",required=True)
    arg=ap.parse_args(argv)
    out=Path(arg.out_dir).resolve()
    docs=Path("docs").resolve()
    if out==docs or docs in out.parents:
        ap.error("HOLD_PRODUCTION_OUTPUT")
    raw=Path(arg.parent).read_bytes()
    parent=json.loads(raw.decode("utf-8"))
    rows=verify_parent(parent)
    records=[]
    with requests.Session() as session:
        for i,row in enumerate(rows):
            if i:time.sleep(1.2)
            page,http=fetch(session,row["officialUrl"])
            roles=parse_event(page,row) if page is not None else {"state":"HTTP_HOLD",
                  "sessions":[],"registrationWindows":[],"eventDateStart":None,"eventDateEnd":None}
            records.append({"id":row["id"],"title":row["title"],"officialUrl":row["officialUrl"],
                            "actId":exact_act_id(row["officialUrl"]),
                            "http":http,"roles":roles})
            print("SEMANTIC",exact_act_id(row["officialUrl"]),http["state"],http.get("http_status"),
                  roles["state"],"EVENT_SESSIONS",len(roles["sessions"]),
                  "REGISTRATION_WINDOWS",len(roles["registrationWindows"]))
    out.mkdir(parents=True,exist_ok=True)
    report={"kind":KIND,"parentRun":PARENT_RUN,
            "parentSHA256":hashlib.sha256(raw).hexdigest(),
            "observedAtUTC":datetime.now(timezone.utc).isoformat(),
            "records":records,"maxGET":5,"retries":0,"tlsValidation":True,
            "sourceRuntime":"DORMANT","goldenAccepted":False,"published":False,
            "writerExecuted":False,"notificationExecuted":False,"autoHidden":0}
    (out/"semantic_evidence.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    out_data,counts=build(parent,records)
    (out/"data.json").write_text(json.dumps(out_data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("P30_L4C_COUNTS",counts)
    if counts["httpOK"]!=5 or counts["eventsWithSessionTime"]<3 or counts["noSessionExhibitions"]!=1:
        print("HOLD P30_L4C_EVENT_DATE_ROLES_NOT_FULLY_PROVEN")
        raise SystemExit(2)
    print("PASS P30_L4C_CKSMH_EVENT_VS_REGISTRATION_ROLES")
    print("PASS P30_L4C_44_IDS_NO_PUBLISH")


if __name__=="__main__":
    main()
