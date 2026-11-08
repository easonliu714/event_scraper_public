"""Fail-closed official activity quality gate and non-destructive snapshot planner.

The planner never performs HTTP and never writes docs/data.json. Upstream native
source receipts must come from a separately verified official acquisition Gate;
a caller-supplied positive receipt is NOT independent native attestation.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

MAX_HTML_BYTES = 2 * 1024 * 1024
MAX_ROWS = 2000
MAX_AGE_HOURS = 24
VOID = {"area", "base", "br", "col", "embed", "hr", "img",
        "input", "link", "meta", "param", "source", "track", "wbr"}
INERT = {"script", "style", "template", "noscript"}
TITLE_RE = re.compile(r"\s+")


def norm(value):
    return TITLE_RE.sub(" ", str(value)).strip()


def https_url(value):
    if not isinstance(value, str):
        return None
    p = urlparse(value)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment:
        return None
    if p.port not in (None, 443):
        return None
    return p


class OfficialDoc(HTMLParser):
    """Extract visible anchors and event-owned ARTICLE heading/time only."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.anchors = []
        self.anchor = None
        self.scopes = []
        self.active = []
        self.heading = None
        self.nodes = 0

    def handle_starttag(self, tag, attrs):
        self.nodes += 1
        if self.nodes > 10000:
            raise ValueError("HTML_NODE_CAP_HOLD")
        attrs = dict(attrs)
        if tag not in VOID:
            self.stack.append(tag)
        if any(t in INERT for t in self.stack):
            return
        if tag == "article":
            self.scopes.append({"depth": len(self.stack), "headings": [],
                                "times": []})
            self.active.append(len(self.scopes)-1)
        if tag == "a":
            self.anchor = [attrs.get("href"), []]
        if tag in ("h1", "h2"):
            self.heading = [tag, []]
        if tag == "time" and attrs.get("datetime"):
            for i in self.active:
                self.scopes[i]["times"].append(attrs["datetime"])

    def handle_data(self, data):
        if any(t in INERT for t in self.stack):
            return
        if self.anchor is not None:
            self.anchor[1].append(data)
        if self.heading is not None:
            self.heading[1].append(data)

    def handle_endtag(self, tag):
        if any(t in INERT for t in self.stack):
            if tag in self.stack:
                while self.stack:
                    if self.stack.pop() == tag:
                        break
            return
        if tag == "a" and self.anchor is not None:
            self.anchors.append((self.anchor[0], norm("".join(self.anchor[1]))))
            self.anchor = None
        if tag in ("h1", "h2") and self.heading is not None:
            for i in self.active:
                self.scopes[i]["headings"].append(norm("".join(self.heading[1])))
            self.heading = None
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break
        self.active = [i for i in self.active
                       if self.scopes[i]["depth"] <= len(self.stack)]


def _body(packet, key):
    raw = packet.get(key)
    if not isinstance(raw, str):
        raise ValueError("SOURCE_BODY_NOT_UTF8_TEXT_HOLD")
    b = raw.encode("utf-8")
    if not 0 < len(b) <= MAX_HTML_BYTES:
        raise ValueError("SOURCE_BODY_EMPTY_OR_OVERSIZE_HOLD")
    return raw, hashlib.sha256(b).hexdigest()


def _utc(value):
    if not isinstance(value, str):
        raise ValueError("OBSERVED_AT_MISSING_HOLD")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("OBSERVED_AT_TIMEZONE_HOLD")
    return dt.astimezone(timezone.utc)


def assess_packet(packet, now):
    """Only validate materialized evidence; never claim its native authenticity."""
    try:
        if not isinstance(packet, dict):
            raise ValueError("PACKET_SCHEMA_HOLD")
        source_id = packet.get("source_event_id")
        if not isinstance(source_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,80}", source_id):
            raise ValueError("SOURCE_EVENT_ID_HOLD")
        lu, du = packet.get("list_url"), packet.get("detail_url")
        lp, dp = https_url(lu), https_url(du)
        if not lp or not dp or lp.hostname != dp.hostname:
            raise ValueError("FIRST_PARTY_HTTPS_HOLD")
        if dp.path.rstrip("/").split("/")[-1] != source_id:
            raise ValueError("SOURCE_ID_DETAIL_PATH_HOLD")
        receipt = packet.get("receipt")
        if not isinstance(receipt, dict) or receipt.get("attestation") != "NATIVE_SOURCE_REQUIRES_INDEPENDENT_READBACK":
            raise ValueError("SOURCE_ATTESTATION_HOLD")
        if (receipt.get("robots_allowed") is not True or
            receipt.get("list_status") != 200 or receipt.get("detail_status") != 200 or
            receipt.get("list_final_url") != lu or receipt.get("detail_final_url") != du):
            raise ValueError("NATIVE_HTTP_ROBOTS_OR_REDIRECT_HOLD")
        observed = _utc(receipt.get("observed_at"))
        if observed > now + timedelta(minutes=2) or now-observed > timedelta(hours=MAX_AGE_HOURS):
            raise ValueError("SOURCE_STALE_OR_FUTURE_HOLD")
        li, lsha = _body(packet, "list_html")
        de, dsha = _body(packet, "detail_html")
        if lsha != receipt.get("list_sha256") or dsha != receipt.get("detail_sha256"):
            raise ValueError("SOURCE_BODY_SHA_HOLD")
        list_doc, detail_doc = OfficialDoc(), OfficialDoc()
        list_doc.feed(li)
        detail_doc.feed(de)
        list_edges = [(urljoin(lu, href), title) for href,title in list_doc.anchors
                      if isinstance(href,str) and urljoin(lu,href)==du]
        if len(list_edges) != 1 or not list_edges[0][1]:
            raise ValueError("EXACT_LIST_DETAIL_EDGE_HOLD")
        title = list_edges[0][1]
        owned = [s for s in detail_doc.scopes if s["headings"].count(title)==1]
        if len(owned) != 1:
            raise ValueError("EXACT_ARTICLE_TITLE_IDENTITY_HOLD")
        times = list(dict.fromkeys(owned[0]["times"]))
        if len(times) != 1:
            raise ValueError("EVENT_LOCAL_TIME_ROLE_HOLD")
        event_time = _utc(times[0])
        if event_time < now or event_time > now + timedelta(days=370):
            raise ValueError("PAST_OR_IMPLAUSIBLE_EVENT_HOLD")
        platform = packet.get("platform")
        if not isinstance(platform,str) or not platform.strip():
            raise ValueError("PLATFORM_NAME_HOLD")
        # This is an evidence-validated *candidate*, not an independently
        # released event. Formal publication requires an independent trust gate.
        return {"decision":"QUALIFIED_PACKET_REQUIRES_INDEPENDENT_NATIVE_ATTESTATION",
                "id":platform+":"+source_id,
                "event":{"title":title, "url":du, "platform":platform, "date":event_time.astimezone(timezone(timedelta(hours=8))).isoformat(),
                         "type":"其他活動", "location":"", "price":"", "img_url":None,
                         "scraped_at":observed.isoformat()},
                "provenance":{"source_event_id":source_id, "list_url":lu, "detail_url":du,
                              "observed_at":observed.isoformat(), "list_sha256":lsha,
                              "detail_sha256":dsha,
                              "date_role":"EVENT_START_NOT_SALE_OR_SESSION"}}
    except (ValueError, KeyError, TypeError, OverflowError, UnicodeError) as e:
        return {"decision":"HOLD", "reason":str(e) or type(e).__name__}


def plan_replacement(packets, *, now, legacy_count, source_collection_ok,
                     owner_allows_legacy_retirement):
    """Select genuine qualified packets and reject unsafe or empty replacement.

    Even qualified packet evidence cannot independently attest source authority.
    Actual writer is a *separate*, exact-head approved transaction, not this
    planner. Legacy removal is allowed only after nonempty attested coverage.
    """
    if not isinstance(packets,list) or len(packets)>MAX_ROWS:
        raise ValueError("INPUT_ROW_CAP_HOLD")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("CLOCK_TIMEZONE_HOLD")
    now=now.astimezone(timezone.utc)
    decisions=[assess_packet(item,now) for item in packets]
    qualified=[d for d in decisions if d["decision"].startswith("QUALIFIED_")]
    duplicates={d["id"] for d in qualified if sum(v["id"]==d["id"] for v in qualified)>1}
    qualified=[d for d in qualified if d["id"] not in duplicates]
    holds=[{"index":i,"reason":d.get("reason","DUPLICATE_IDENTITY_HOLD")}
           for i,d in enumerate(decisions)
           if d["decision"]=="HOLD" or d.get("id") in duplicates]
    # Only an independently attested native source can enter formal publication;
    # caller-supplied receipts cannot independently create an ACCEPTED_FIELD.
    decision=("HOLD_SOURCE_COLLECTION" if not source_collection_ok else
              "HOLD_NO_QUALIFIED_EVENTS" if not qualified else
              "HOLD_INDEPENDENT_FIELD_AUTHORITY_AND_RELEASE" )
    if not owner_allows_legacy_retirement:
        decision="HOLD_NO_LEGACY_RETIREMENT_AUTHORIZATION"
    return {"kind":"EVENTRADAR_P30_QUALITY_SNAPSHOT_PLAN_V1",
            "decision":decision, "legacy_rows":legacy_count,
            "owner_allows_legacy_retirement":bool(owner_allows_legacy_retirement),
            "source_collection_ok":bool(source_collection_ok),
            "packet_count":len(packets),"qualified_packet_count":len(qualified),
            "independently_accepted_events":0,"published_events":0,
            "qualified_candidates":[{"id":d["id"],"event":d["event"],
                                     "provenance":d["provenance"]} for d in qualified],
            "quarantined":holds,"formal_feed_mutated":False,
            "release_state":"HARD_HOLD_NO_PUBLICATION"}


def main():
    import argparse
    from pathlib import Path
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--legacy-count",type=int,required=True)
    ap.add_argument("--owner-allows-legacy-retirement",action="store_true")
    args=ap.parse_args()
    payload=json.loads(args.input.read_text(encoding="utf-8"))
    result=plan_replacement(payload["packets"],now=_utc(payload["now"]),
                            legacy_count=args.legacy_count,
                            source_collection_ok=payload.get("source_collection_ok") is True,
                            owner_allows_legacy_retirement=args.owner_allows_legacy_retirement)
    target=args.output.resolve()
    if "docs/data.json" in str(target).replace("\\","/"):
        raise ValueError("FORMAL_DATA_PATH_FORBIDDEN")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("qualified_candidates","quarantined")},ensure_ascii=False))
    return 0 if result["qualified_packet_count"] else 49


if __name__=="__main__":
    raise SystemExit(main())
