"""One bounded, robots-compliant TPAC program LIST -> exact DETAIL source audit.

No login, cookies, redirects, retries, checkout, or formal publication.
At most 1 robots + 1 index + 1 new event detail GET per first attempt.
Outputs raw public HTML only to isolated CI evidence for offline replay.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib import robotparser
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.parse import urljoin

from scripts.p30_quality_snapshot_publisher import OfficialDoc, https_url, norm

AGENT = "EventRadarTaiwan-SourceAudit/1.0"
LIST_URL = "https://tpac.org.taipei/program"
DETAIL_URL = "https://tpac.org.taipei/program/2040"
ROBOTS_URL = "https://tpac.org.taipei/robots.txt"
MAX_BYTES = 2 * 1024 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def bounded_fetch(url, *, opener=None):
    """One official URL GET, fail closed on redirect, status, size, or MIME."""
    if url not in (LIST_URL, DETAIL_URL, ROBOTS_URL):
        raise ValueError("TPAC_UNEXPECTED_SOURCE_URL_HOLD")
    client=opener or build_opener(NoRedirect())
    request=Request(url,headers={"User-Agent":AGENT,"Accept":"text/html,text/plain"})
    with client.open(request,timeout=15) as response:
        status=response.status
        final_url=response.geturl()
        media=response.headers.get("Content-Type","").lower()
        raw=response.read(MAX_BYTES+1)
    if status!=200 or final_url!=url or not raw or len(raw)>MAX_BYTES:
        raise ValueError("TPAC_STATUS_REDIRECT_OR_BODY_HOLD")
    if not (("text/html" in media) if url!=ROBOTS_URL else ("text/" in media)):
        raise ValueError("TPAC_CONTENT_TYPE_HOLD")
    return raw


def acquire_once(output_dir, *, fetch=bounded_fetch):
    """Acquire source once only after explicit robots authorization."""
    output_dir=Path(output_dir)
    report={"kind":"EVENTRADAR_TPAC_2040_FIRST_PARTY_ONE_SHOT",
            "started_at":datetime.now(timezone.utc).isoformat(),
            "list_url":LIST_URL,"detail_url":DETAIL_URL,
            "robots_url":ROBOTS_URL,"decision":"HOLD",
            "source_native_get":0,"published":0,
            "first_failure":"NOT_ATTEMPTED"}
    files={}
    try:
        robots=fetch(ROBOTS_URL)
        report["source_native_get"]+=1
        policy=robotparser.RobotFileParser()
        policy.parse(robots.decode("utf-8").splitlines())
        if not policy.can_fetch(AGENT,LIST_URL) or not policy.can_fetch(AGENT,DETAIL_URL):
            raise ValueError("TPAC_ROBOTS_DISALLOW_HOLD")
        listing=fetch(LIST_URL)
        report["source_native_get"]+=1
        detail=fetch(DETAIL_URL)
        report["source_native_get"]+=1
        list_body=listing.decode("utf-8")
        detail_body=detail.decode("utf-8")
        ldoc,ddoc=OfficialDoc(),OfficialDoc()
        ldoc.feed(list_body);ddoc.feed(detail_body)
        edges=[(href,title) for href,title in ldoc.anchors
               if isinstance(href,str) and urljoin(LIST_URL,href)==DETAIL_URL]
        report["exact_list_edges"]=len(edges)
        report["detail_articles"]=len(ddoc.scopes)
        report["first_party_same_id_url"]=bool(edges)
        report["detail_exact_label_owned_article_count"]=(sum(
            s["headings"].count(edges[0][1])==1 for s in ddoc.scopes)
            if len(edges)==1 else 0)
        report["list_sha256"]=hashlib.sha256(listing).hexdigest()
        report["detail_sha256"]=hashlib.sha256(detail).hexdigest()
        report["list_bytes"]=len(listing)
        report["detail_bytes"]=len(detail)
        files={"tpac_2040_list.html":listing,"tpac_2040_detail.html":detail}
        report["decision"]="RAW_SOURCE_SAVED_FOR_INDEPENDENT_REPLAY_ONLY"
        report["first_failure"]=("TPAC_EVENT_LOCAL_ATTESTATION_PENDING"
                  if report["detail_exact_label_owned_article_count"]!=1
                  else "INDEPENDENT_FIELD_AND_RELEASE_PENDING")
    except (HTTPError, URLError, OSError, UnicodeError, ValueError, TimeoutError) as exc:
        report["decision"]="HOLD"
        report["first_failure"]=type(exc).__name__+":"+str(exc)
    output_dir.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        (output_dir/name).write_bytes(raw)
    (output_dir/"tpac_2040_source_receipt.json").write_text(
        json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return report


if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    result=acquire_once(args.out)
    print(json.dumps({k:v for k,v in result.items()
                      if k not in ("started_at",)},ensure_ascii=False))
    # A lawful native source diagnostic may HOLD; never claim publication success.
    raise SystemExit(0)
