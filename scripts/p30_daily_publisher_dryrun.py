"""Isolated 24h Publisher preflight. Namespace-safe identities; NO HTTP, writes or authority."""
import argparse, hashlib, json, re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

KIND="EVENTRADAR_DAILY_PUBLISHER_DRYRUN_V1"
# Only registered official event URL namespaces may enter a formal shape check.
# OPENTIX source #05 has historical same-ID REVIEW evidence, not FIELD authority.
SOURCES={
    "臺北表演藝術中心":{"host":"tpac.org.taipei","namespaces":("program","event")},
    "OPENTIX":{"host":"www.opentix.life","namespaces":("event",)},
}

HOLD="HARD_HOLD_NO_PUBLICATION"

def blob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def identity(row):
    if not isinstance(row,dict): raise ValueError("INVALID_ROW_HOLD")
    p,i=row.get("platform"),row.get("source_event_id")
    if p not in SOURCES: raise ValueError("UNREGISTERED_ADAPTER_HOLD")
    if not isinstance(i,str) or not re.fullmatch(r"[0-9]{1,20}",i):
        raise ValueError("INVALID_SOURCE_ID_HOLD")
    # TPAC /program and /event have independent numeric ID namespaces.
    # Never collapse same-number events into one formal row or LKG key.
    u=row.get("url")
    if not isinstance(u,str): raise ValueError("SOURCE_NAMESPACE_HOLD")
    try: match=re.fullmatch(r"/(program|event)/([0-9]{1,20})",urlsplit(u).path)
    except ValueError: raise ValueError("SOURCE_NAMESPACE_HOLD")
    if not match or match.group(2)!=i:
        raise ValueError("SOURCE_NAMESPACE_ID_HOLD")
    if match.group(1) not in SOURCES[p]["namespaces"]:
        raise ValueError("SOURCE_NAMESPACE_NOT_REGISTERED_HOLD")
    return (p,match.group(1),i)

def verified_shape(row):
    p,namespace,i=identity(row)
    u=row.get("url")
    if not isinstance(u,str): raise ValueError("URL_HOLD")
    x=urlsplit(u)
    if (x.scheme!="https" or x.hostname!=SOURCES[p]["host"] or x.username or x.password
            or x.port not in (None,443) or x.query or x.fragment
            or x.path!=f"/{namespace}/{i}"):
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
        m=re.fullmatch(r"NT\$\s*(\d{1,3}(?:,\d{3})*|\d{3,6})\s*起",price)
        amount=int(m.group(1).replace(",","")) if m else None
        try:
            stamp=r.get("observed_at") if isinstance(r,dict) else None
            dt=datetime.fromisoformat(stamp.replace("Z","+00:00"))
            aware=dt.tzinfo is not None and dt.utcoffset() is not None
        except (ValueError,TypeError,AttributeError):
            aware=False
        if (not isinstance(r,dict) or not aware or amount is None
                or not 100<=amount<=100000 or r.get("accepted") is not True
                or r.get("role")!="EVENT_GENERAL_ADMISSION_MIN_PRICE"
                or r.get("decision")!="FIELD_ACCEPTED"
                or r.get("price_kind")!="GENERAL_NON_DISCOUNTED"
                or r.get("value")!=price or r.get("event_id")!=i
                or r.get("source")!=u or r.get("source_url")!=u
                or r.get("source_body_sha256")!=sha
                or r.get("min_price_ntd")!=amount
                or type(r.get("max_price_ntd")) is not int
                or not amount<=r["max_price_ntd"]<=100000):
            raise ValueError("UNACCEPTED_PRICE_HOLD")
    return {k:row.get(k) for k in ("platform","source_event_id","url","title","date","price")}


def review_bridge_only(row):
    """Consume an existing A_OPENTIX REVIEW envelope without accepting any field.

    This path intentionally never interprets caller-supplied body digests as
    independently verified native receipts or publisher authority.
    """
    if (row.get("kind")!="EVENTRADAR_AB_ISOLATED_REVIEW_BRIDGE_V1"
            or row.get("adapter_key")!="A_OPENTIX" or row.get("line")!="A"
            or row.get("source_id")!="05"
            or row.get("list_url")!="https://www.opentix.life/"
            or row.get("source_attestation")!="CALLER_SUPPLIED_NOT_NATIVE"
            or row.get("decision") not in ("HOLD","REVIEW_ONLY_NOT_NATIVE")
            or row.get("release_state")!=HOLD
            or any(row.get(k)!=0 for k in ("native_get","native_body_lkg",
                                           "formal_accepted_fields","golden","published"))):
        raise ValueError("REVIEW_BRIDGE_ATTESTATION_HOLD")
    event_id=row.get("source_event_id")
    if not isinstance(event_id,str) or not re.fullmatch(r"[0-9]{1,20}",event_id):
        raise ValueError("REVIEW_BRIDGE_EVENT_ID_HOLD")
    url="https://www.opentix.life/event/"+event_id
    if row.get("detail_url")!=url:
        raise ValueError("REVIEW_BRIDGE_OFFICIAL_URL_HOLD")
    stamp=row.get("observed_at_utc")
    try:
        dt=datetime.fromisoformat(stamp.replace("Z","+00:00"))
        if dt.tzinfo is None or dt.utcoffset() is None or dt.utcoffset().total_seconds()!=0:
            raise ValueError("not UTC")
    except (ValueError,TypeError,AttributeError):
        raise ValueError("REVIEW_BRIDGE_UTC_HOLD")
    digests=row.get("body_digests")
    if (not isinstance(digests,dict)
            or any(not isinstance(digests.get(k),str)
                   or not re.fullmatch(r"[a-f0-9]{64}",digests[k])
                   for k in ("list_sha256","detail_sha256"))):
        raise ValueError("REVIEW_BRIDGE_DIGEST_SHAPE_HOLD")
    if isinstance(row.get("candidate"),dict) and (
            row["candidate"].get("formal_field_pass") is True
            or row["candidate"].get("published") is True):
        raise ValueError("REVIEW_BRIDGE_FORGED_FORMAL_HOLD")
    return {"source":"OPENTIX","source_event_id":event_id,
            "url":url,"observed_at_utc":stamp,
            "detail_sha256_unattested":digests["detail_sha256"],
            "decision":"REVIEW_ONLY_NOT_NATIVE",
            "first_failure":"INDEPENDENT_NATIVE_AND_FIELD_AUTHORITY_HOLD"}

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
    review_only=[]
    for n,row in enumerate(candidates):
        try:
            if isinstance(row,dict) and row.get("kind")=="EVENTRADAR_AB_ISOLATED_REVIEW_BRIDGE_V1":
                review_only.append(review_bridge_only(row))
                continue
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
            "review_only_count":len(review_only),"review_only":review_only,
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
