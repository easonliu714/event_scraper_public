#!/usr/bin/env python3
"""VENUE-02AH: exhibit range vs article/site update dates, strict role isolation.

Two independent first-party SID receipts. Source-rendered text is not a
verified DOM leaf; no session, ticket, formal field, Golden or publication.
"""
import hashlib
import re
from datetime import date
from p30_venue02ag_ceramics_two_sid_roles import inspect_one, SOURCE, HOLD
from p30_venue02ac_ceramics_sid_title import OBSERVED

ARTICLE=re.compile(r"^更新日期：(\d{4}-\d{2}-\d{2})\s+瀏覽人次：(\d{1,10})$")
SITE=re.compile(r"^內容更新\s*：(\d{4}-\d{2}-\d{2})$")
STAMP=re.compile(r"^20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
def inspect_metadata(record,article_text,site_text):
    out={"gate":"P30-VENUE-02AH","source":SOURCE,"sid":record.get("sid"),
         "candidateProvenance":[],"acceptedFields":0,"goldenAccepted":0,
         "published":False,"ticketEventId":None,"sessionAccepted":False,
         "releaseState":HOLD}
    if record.get("sid") not in OBSERVED:
        return dict(out,decision="HOLD_UNBOUNDED_SID")
    prior=inspect_one(record.get("url"),record.get("html",""),
                      record["sid"],record.get("title"),record.get("observed_at"))
    out["priorFieldDecision"]=prior["decision"]
    if not prior["decision"].startswith("REVIEW_") or len(prior["candidateProvenance"])!=2:
        return dict(out,decision="HOLD_EXHIBITION_ROLE_OR_IDENTITY")
    if not isinstance(article_text,str) or not isinstance(site_text,str):
        return dict(out,decision="HOLD_METADATA_NOT_TEXT")
    a=ARTICLE.fullmatch(article_text.strip())
    s=SITE.fullmatch(site_text.strip())
    if not a or not s:
        return dict(out,decision="HOLD_METADATA_ROLE_LABEL_OR_AMBIGUITY")
    if not isinstance(record.get("observed_at"),str) or not STAMP.fullmatch(record["observed_at"]):
        return dict(out,decision="HOLD_METADATA_OBSERVATION_PROVENANCE")
    try:
        article_day=date.fromisoformat(a.group(1))
        site_day=date.fromisoformat(s.group(1))
        observed_day=date.fromisoformat(record["observed_at"][:10])
    except ValueError:
        return dict(out,decision="HOLD_METADATA_INVALID_DATE")
    if article_day>observed_day or site_day>observed_day:
        return dict(out,decision="HOLD_METADATA_AFTER_OBSERVATION")
    out["candidateProvenance"].extend(prior["candidateProvenance"])
    for role,value in (("ARTICLE_UPDATED_AT",article_day.isoformat()),
                       ("SITE_CONTENT_UPDATED_AT",site_day.isoformat())):
        out["candidateProvenance"].append({
            "source":SOURCE,"source_sid":record["sid"],
            "observed_at":record["observed_at"],"role":role,
            "decision":"REVIEW_METADATA_NOT_EXHIBITION_OR_SESSION",
            "valueSHA256":digest(value)})
    out["candidateRoleCount"]=4
    return dict(out,decision="REVIEW_DISTINCT_EXHIBITION_VS_UPDATE_ROLES_NO_FORMAL_FIELDS")
def inspect_pair(records):
    out={"gate":"P30-VENUE-02AH","source":SOURCE,"records":[],
         "acceptedFields":0,"goldenAccepted":0,"published":False,
         "releaseState":HOLD}
    if not isinstance(records,list) or len(records)!=2:
        return dict(out,decision="HOLD_NOT_TWO_SIDS")
    sids=[x.get("sid") for x in records]
    if len(set(sids))!=2 or any(x not in OBSERVED for x in sids):
        return dict(out,decision="HOLD_CROSS_SID_OR_DUPLICATE")
    for record in records:
        result=inspect_metadata(record,record.get("articleUpdatedText"),
                                record.get("siteUpdatedText"))
        out["records"].append({"sid":record["sid"],"decision":result["decision"],
                               "candidateRoleCount":len(result["candidateProvenance"])})
        if not result["decision"].startswith("REVIEW_"):
            return dict(out,decision="HOLD_ONE_OR_MORE_SOURCE_DATE_ROLES")
    return dict(out,decision="REVIEW_TWO_SIDS_UPDATE_DATES_NOT_EVENT_SESSIONS")
if __name__=="__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_IMPLICIT_NETWORK")
