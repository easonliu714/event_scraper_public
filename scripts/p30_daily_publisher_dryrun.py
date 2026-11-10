"""Isolated 24h Publisher preflight. Namespace-safe identities; NO HTTP, writes or authority."""
import argparse, hashlib, json, re, io, zipfile, html
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


# Versioned rollback manifests pin the original Git blob and per-event bytes.
# They do NOT confer release authority or guarantee Git object retention.
def _json_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()

def rollback_manifest(formal_raw, expected_blob):
    if not isinstance(formal_raw, bytes) or blob_sha(formal_raw) != expected_blob:
        raise ValueError("ROLLBACK_BASE_CAS_HOLD")
    try:
        rows=json.loads(formal_raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("ROLLBACK_BASE_JSON_HOLD") from exc
    if not isinstance(rows, list) or not 0 < len(rows) <= 2000:
        raise ValueError("ROLLBACK_BASE_ROWS_HOLD")
    entries={}
    for row in rows:
        k=":".join(identity(row))
        if k in entries:
            raise ValueError("ROLLBACK_DUPLICATE_ID_HOLD")
        entries[k]=_json_sha(row)
    return {"kind":"EVENTRADAR_FORMAL_ROLLBACK_MANIFEST_V1",
            "release_state":HOLD,"base_git_blob":expected_blob,
            "base_raw_sha256":hashlib.sha256(formal_raw).hexdigest(),
            "row_count":len(rows),"event_row_sha256":dict(sorted(entries.items())),
            "storage_retention_attested":False,
            "restore_requires_separate_owner_authority":True,
            "commit_permitted":False}

def verify_rollback_manifest(formal_raw, manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("base_git_blob"), str):
        raise ValueError("ROLLBACK_MANIFEST_SHAPE_HOLD")
    actual=rollback_manifest(formal_raw, manifest["base_git_blob"])
    if actual != manifest:
        raise ValueError("ROLLBACK_MANIFEST_MISMATCH_HOLD")
    return True

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


# Sealed TPAC original native bytes, run 42491637804; NEVER a new GET or FIELD acceptance.
TPAC_ARCHIVE_SHA256="87fd004eb1a3b3019620a2ae93f2e991b1669caa9ab17c3938479eda295c0acd"

def replay_tpac_event_archive(raw,expected_sha):
    if not isinstance(raw,bytes) or expected_sha!=TPAC_ARCHIVE_SHA256:
        raise ValueError("ARCHIVE_PROVENANCE_PIN_HOLD")
    if hashlib.sha256(raw).hexdigest()!=expected_sha:
        raise ValueError("ARCHIVE_ZIP_SHA256_HOLD")
    names={"SHA256SUMS.txt","native_event/event_list.html",
           "native_event/event_1301_detail.html","native_event/event_2072_detail.html",
           "native_event/tpac_event_catalog_receipt.json",
           "tpac_catalog_topology_fixture.json","tpac_multi_event_offline_demo.json"}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if set(z.namelist())!=names or len(z.namelist())!=len(names) or z.testzip():
                raise ValueError("ARCHIVE_MEMBERS_CRC_HOLD")
            sums={}
            for line in z.read("SHA256SUMS.txt").decode().splitlines():
                m=re.fullmatch(r"([a-f0-9]{64})  \./([A-Za-z0-9_./-]+)",line)
                if not m or m.group(2) in sums: raise ValueError("ARCHIVE_MANIFEST_HOLD")
                sums[m.group(2)]=m.group(1)
            if set(sums)!=names-{"SHA256SUMS.txt"}:
                raise ValueError("ARCHIVE_MANIFEST_SCOPE_HOLD")
            if any(hashlib.sha256(z.read(n)).hexdigest()!=h for n,h in sums.items()):
                raise ValueError("ARCHIVE_MEMBER_SHA256_HOLD")
            r=json.loads(z.read("native_event/tpac_event_catalog_receipt.json"))
            if (r.get("kind")!="EVENTRADAR_TPAC_EVENT_TWO_DETAILS_SINGLE_AUDIT"
                or r.get("decision")!="NATIVE_BODY_CAPTURED_FOR_INDEPENDENT_REPLAY_ONLY"
                or r.get("native_official_attestation") is not False
                or r.get("accepted_fields")!=0 or r.get("published")!=0
                or r.get("list_url")!="https://tpac.org.taipei/event"
                or r.get("listed_id_count")!=18
                or set(r.get("ids_present_on_list",[]))!={"1301","2072"}
                or set(r.get("source_receipts",{}))!={"list","1301","2072"}):
                raise ValueError("ARCHIVE_RECEIPT_AUTHORITY_HOLD")
            ids=re.findall(r'href="/event/([0-9]+)"',
                           z.read("native_event/event_list.html").decode())
            if len(ids)!=18 or len(set(ids))!=18:
                raise ValueError("ARCHIVE_LIST_TOPOLOGY_HOLD")
            reviews=[]
            for i in ("list","1301","2072"):
                receipt=r["source_receipts"][i]
                name=("native_event/event_list.html" if i=="list"
                      else "native_event/event_"+i+"_detail.html")
                url=("https://tpac.org.taipei/event" if i=="list"
                     else "https://tpac.org.taipei/event/"+i)
                stamp=receipt.get("observed_at")
                try:
                    dt=datetime.fromisoformat(stamp.replace("Z","+00:00"))
                    if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError()
                except (ValueError,TypeError,AttributeError):
                    raise ValueError("ARCHIVE_OBSERVED_AT_HOLD")
                body=z.read(name)
                if (receipt.get("final_url")!=url or receipt.get("http_status")!=200
                    or receipt.get("robots_allowed") is not True
                    or receipt.get("body_bytes")!=len(body)
                    or receipt.get("body_sha256")!=hashlib.sha256(body).hexdigest()):
                    raise ValueError("ARCHIVE_RECEIPT_BODY_HOLD")
                if i=="list": continue
                if i not in ids: raise ValueError("ARCHIVE_LIST_DETAIL_ID_HOLD")
                m=re.search(r"<h1\b[^>]*>(.*?)</h1>",body.decode(),re.S|re.I)
                if not m: raise ValueError("ARCHIVE_TITLE_HOLD")
                title=html.unescape(re.sub(r"<[^>]+>","",m.group(1))).strip()
                if not title or len(title)>180: raise ValueError("ARCHIVE_TITLE_HOLD")
                reviews.append({"source":"臺北表演藝術中心","namespace":"event",
                    "source_event_id":i,"url":url,"title_review":title,
                    "title_role":"EVENT_TITLE_REVIEW_NOT_ACCEPTED",
                    "observed_at":stamp,"detail_body_sha256":receipt["body_sha256"],
                    "archive_run_id":42491637804,"archive_zip_sha256":expected_sha,
                    "decision":"ARCHIVED_NATIVE_REPLAY_REVIEW_ONLY",
                    "first_failure":"INDEPENDENT_FIELD_ACCEPTANCE_AND_FRESHNESS_HOLD"})
            return reviews
    except (zipfile.BadZipFile,UnicodeError,KeyError,TypeError,json.JSONDecodeError) as e:
        raise ValueError("ARCHIVE_STRUCTURE_HOLD") from e

def plan(formal_raw,candidates,expected_blob,archive_zip=None,archive_sha=None):
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
    if (archive_zip is None)!=(archive_sha is None):
        raise ValueError("ARCHIVE_PAIR_REQUIRED_HOLD")
    archived_reviews=(replay_tpac_event_archive(archive_zip,archive_sha)
                      if archive_zip is not None else [])
    review_only.extend(archived_reviews)
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
    diff_entries=[]
    for k,row in proposed.items():
        label=":".join(k)
        if k not in prior:
            added.append(label)
            change="ADD"
        elif any(row.get(x)!=prior[k].get(x) for x in ("url","title","date","price")):
            changed.append(label)
            change="CHANGE"
        else:
            unchanged.append(label)
            change="UNCHANGED"
        fields=("platform","source_event_id","url","title","date","price")
        before={x:prior[k].get(x) for x in fields} if k in prior else None
        diff_entries.append({"event_key":label,"change":change,
            "before_fields_sha256":_json_sha(before) if before is not None else None,
            "candidate_fields_sha256":_json_sha(row),
            "authority":"SHAPE_ONLY_NOT_INDEPENDENTLY_ACCEPTED"})
    return {"kind":KIND,"decision":"HOLD_INDEPENDENT_NATIVE_AND_RELEASE_AUTHORITY",
            "release_state":HOLD,"formal_blob_before":actual,"formal_blob_after":actual,
            "formal_rows_before":len(original),"formal_rows_after":len(original),
            "candidate_count":len(candidates),"shape_valid":len(proposed),
            "review_only_count":len(review_only),
            "archived_native_review_count":len(archived_reviews),
            "archived_native_list_rows":18 if archived_reviews else 0,"review_only":review_only,
            "would_add":sorted(added),"would_change":sorted(changed),
            "unchanged":sorted(unchanged),"rejected":rejected,
            "versioned_diff":sorted(diff_entries,key=lambda x:x["event_key"]),
            "rollback_manifest":rollback_manifest(formal_raw,expected_blob),
            "lkg_retained":len(original),"native_get":0,"published_delta":0,
            "commit_permitted":False,"scheduler_enabled":False,
            "formal_data_mutated":False,
            "warning":"Caller-supplied ACCEPTED flags are not independent source attestation"}


# [P30-PUB-OD-01] Deterministic, read-only gate for an authenticated server.
# Public PWA refresh may only read these results. Browser inputs, this function,
# and the existing PR workflow have ZERO GitHub dispatch or publication power.
# A trusted gateway must re-read server-side receipts, obtain a durable global
# claim, enforce per-source rate limits, and separately attest release authority.
def assess_refresh_request(status, now, *, gateway_attested=False,
                           claim_attested=False, release_authorized=False,
                           ttl_seconds=86400, retry_cooldown_seconds=3600):
    """Return refresh REQUEST eligibility, never execute a request or publish.

    All timestamps must be checked server-side; browser-supplied status and
    clock are untrusted. Per-source robots/6h limits are independent gates.
    """
    if not isinstance(status, dict) or not isinstance(now, datetime):
        raise ValueError("REFRESH_TRUSTED_INPUT_HOLD")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("REFRESH_SERVER_TIMEZONE_HOLD")
    if (type(ttl_seconds) is not int or not 3600 <= ttl_seconds <= 604800
            or type(retry_cooldown_seconds) is not int
            or not 300 <= retry_cooldown_seconds <= ttl_seconds):
        raise ValueError("REFRESH_BOUND_POLICY_HOLD")
    if type(status.get("running", False)) is not bool:
        raise ValueError("REFRESH_RUNNING_SHAPE_HOLD")
    if any(type(v) is not bool for v in
           (gateway_attested, claim_attested, release_authorized)):
        raise ValueError("REFRESH_AUTHORITY_SHAPE_HOLD")
    def parse_timestamp(key):
        value = status.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("REFRESH_RECEIPT_SHAPE_HOLD")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError()
        except ValueError as exc:
            raise ValueError("REFRESH_RECEIPT_TIMEZONE_HOLD") from exc
        if parsed > now:
            raise ValueError("REFRESH_FUTURE_RECEIPT_HOLD")
        return parsed
    last_success = parse_timestamp("last_success_at")
    last_attempt = parse_timestamp("last_attempt_at")
    decision = "REQUEST_ELIGIBLE_NOT_DISPATCHED"
    if status.get("running", False):
        decision = "SKIP_ALREADY_RUNNING"
    elif last_success is not None and (
            now - last_success).total_seconds() < ttl_seconds:
        decision = "SKIP_DATA_FRESH"
    elif last_attempt is not None and (
            now - last_attempt).total_seconds() < retry_cooldown_seconds:
        decision = "SKIP_RETRY_COOLDOWN"
    elif not gateway_attested:
        decision = "HOLD_TRUSTED_GATEWAY_NOT_ATTESTED"
    elif not claim_attested:
        decision = "HOLD_GLOBAL_CLAIM_NOT_ATTESTED"
    elif not release_authorized:
        decision = "HOLD_PUBLICATION_AUTHORITY"
    return {
        "kind": "EVENTRADAR_ONDEMAND_REFRESH_ELIGIBILITY_V1",
        "decision": decision,
        "request_eligible": decision == "REQUEST_ELIGIBLE_NOT_DISPATCHED",
        "dispatch_performed": False,
        "publisher_executed": False,
        "formal_write_performed": False,
        "source_get_performed": False,
        "schedule_enabled": False,
        "source_rate_limits_checked": False,
        "warning": "Server-only preflight; official source limits and publisher checks remain separate",
    }

def main():
    a=argparse.ArgumentParser()
    for flag in ("formal","candidates","expected-blob","output"): a.add_argument("--"+flag,required=True)
    a.add_argument("--archived-tpac-zip")
    a.add_argument("--archived-tpac-sha256")
    x=a.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=Path(x.output).resolve()
    if not out.is_relative_to((root/"_isolated_review").resolve()) or out.suffix!=".json":
        raise ValueError("FORMAL_WRITE_PATH_FORBIDDEN")
    raw=Path(x.formal).read_bytes()
    archived=Path(x.archived_tpac_zip).read_bytes() if x.archived_tpac_zip else None
    result=plan(raw,json.loads(Path(x.candidates).read_text(encoding="utf-8")),
                x.expected_blob,archived,x.archived_tpac_sha256)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if Path(x.formal).read_bytes()!=raw: raise ValueError("FORMAL_CHANGED_HOLD")
    print(json.dumps({k:v for k,v in result.items() if k!="rejected"},ensure_ascii=False))
if __name__=="__main__": main()
