"""Isolated 24h Publisher preflight. NO HTTP, NO production writes, NO authority."""
import argparse, hashlib, json, re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

KIND="EVENTRADAR_DAILY_PUBLISHER_DRYRUN_V1"
DOMAINS={"臺北表演藝術中心":"tpac.org.taipei"}
HOLD="HARD_HOLD_NO_PUBLICATION"

def blob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def identity(row):
    if not isinstance(row,dict): raise ValueError("INVALID_ROW_HOLD")
    p,i=row.get("platform"),row.get("source_event_id")
    if p not in DOMAINS: raise ValueError("UNREGISTERED_ADAPTER_HOLD")
    if not isinstance(i,str) or not re.fullmatch(r"[0-9]{1,20}",i):
        raise ValueError("INVALID_SOURCE_ID_HOLD")
    return (p,i)

def verified_shape(row):
    p,i=identity(row)
    u=row.get("url")
    if not isinstance(u,str): raise ValueError("URL_HOLD")
    x=urlsplit(u)
    if (x.scheme!="https" or x.hostname!=DOMAINS[p] or x.username or x.password
            or x.port not in (None,443) or x.query or x.fragment
            or x.path not in (f"/program/{i}",f"/event/{i}")):
        raise ValueError("EXACT_OFFICIAL_ID_URL_HOLD")
    if row.get("formal_field_pass") is not True or row.get("_candidate") is not None:
        raise ValueError("REVIEW_ONLY_HOLD")
    pub=row.get("_publication")
    sha=pub.get("source_body_sha256") if isinstance(pub,dict) else None
    sha=sha.get("detail") if isinstance(sha,dict) else None
    if not isinstance(sha,str) or not re.fullmatch("[a-f0-9]{64}",sha):
        raise ValueError("NATIVE_SHA_HOLD")
    ev=row.get("_formal_field_evidence")
    if not isinstance(ev,dict): raise ValueError("FIELD_EVIDENCE_HOLD")
    for k,role in (("title","EVENT_TITLE"),("date","EVENT_SHOW_START")):
        v=row.get(k)
        r=ev.get(k)
        if not isinstance(v,str) or not v or not isinstance(r,dict):
            raise ValueError("FIELD_"+k.upper()+"_HOLD")
        stamp=r.get("observed_at")
        try:
            dt=datetime.fromisoformat(stamp.replace("Z","+00:00"))
            if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError()
        except (ValueError,TypeError,AttributeError):
            raise ValueError("FIELD_TIMEZONE_HOLD")
        if (r.get("value")!=v or r.get("role")!=role or r.get("decision")!="ACCEPTED"
                or r.get("event_id")!=i or r.get("source")!=u or r.get("source_url")!=u):
            raise ValueError("FIELD_"+k.upper()+"_AUTHORITY_HOLD")
    try: datetime.strptime(row["date"],"%Y-%m-%d %H:%M")
    except ValueError: raise ValueError("SHOW_DATE_HOLD")
    price=row.get("price","")
    if price:
        r=ev.get("price")
        if (not isinstance(r,dict) or r.get("role")!="EVENT_GENERAL_ADMISSION_MIN_PRICE"
                or r.get("decision")!="FIELD_ACCEPTED" or r.get("value")!=price
                or r.get("event_id")!=i or r.get("source_url")!=u
                or r.get("body_sha256")!=sha):
            raise ValueError("UNACCEPTED_PRICE_HOLD")
    return {k:row.get(k) for k in ("platform","source_event_id","url","title","date","price")}

def plan(formal_raw,candidates,expected_blob):
    if not isinstance(formal_raw,bytes) or not re.fullmatch("[a-f0-9]{40}",expected_blob):
        raise ValueError("CAS_INPUT_HOLD")
    actual=blob_sha(formal_raw)
    if actual!=expected_blob: raise ValueError("FORMAL_CAS_MISMATCH_HOLD")
    original=json.loads(formal_raw)
    if not isinstance(original,list) or not 0<len(original)<=2000:
        raise ValueError("FORMAL_EMPTY_OR_OVERSIZE_HOLD")
    if not isinstance(candidates,list) or len(candidates)>2000:
        raise ValueError("CANDIDATE_CAP_HOLD")
    prior={}
    for row in original:
        k=identity(row)
        if k in prior: raise ValueError("FORMAL_DUPLICATE_HOLD")
        prior[k]=row
    proposed,seen,rejected={ },set(),[]
    for n,row in enumerate(candidates):
        try:
            k=identity(row)
            if k in seen:
                proposed.pop(k,None)
                raise ValueError("DUPLICATE_CANDIDATE_HOLD")
            seen.add(k)
            proposed[k]=verified_shape(row)
        except (ValueError,TypeError,KeyError) as e:
            rejected.append({"index":n,"reason":str(e)})
    added,changed,unchanged=[],[],[]
    for k,row in proposed.items():
        label=":".join(k)
        if k not in prior: added.append(label)
        elif any(row.get(x)!=prior[k].get(x) for x in ("url","title","date","price")):
            changed.append(label)
        else: unchanged.append(label)
    return {"kind":KIND,"decision":"HOLD_INDEPENDENT_NATIVE_AND_RELEASE_AUTHORITY",
            "release_state":HOLD,"formal_blob_before":actual,"formal_blob_after":actual,
            "formal_rows_before":len(original),"formal_rows_after":len(original),
            "candidate_count":len(candidates),"shape_valid":len(proposed),
            "would_add":sorted(added),"would_change":sorted(changed),
            "unchanged":sorted(unchanged),"rejected":rejected,
            "lkg_retained":len(original),"native_get":0,"published_delta":0,
            "commit_permitted":False,"scheduler_enabled":False,
            "formal_data_mutated":False,
            "warning":"Caller-supplied ACCEPTED flags are not independent source attestation"}

def main():
    a=argparse.ArgumentParser()
    for flag in ("formal","candidates","expected-blob","output"): a.add_argument("--"+flag,required=True)
    x=a.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=Path(x.output).resolve()
    if not out.is_relative_to((root/"_isolated_review").resolve()) or out.suffix!=".json":
        raise ValueError("FORMAL_WRITE_PATH_FORBIDDEN")
    raw=Path(x.formal).read_bytes()
    result=plan(raw,json.loads(Path(x.candidates).read_text(encoding="utf-8")),x.expected_blob)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if Path(x.formal).read_bytes()!=raw: raise ValueError("FORMAL_CHANGED_HOLD")
    print(json.dumps({k:v for k,v in result.items() if k!="rejected"},ensure_ascii=False))
if __name__=="__main__": main()
