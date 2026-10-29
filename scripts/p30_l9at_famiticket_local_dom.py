#!/usr/bin/env python3
"""L9-AT: FamiTicket title/marker locality; one bounded live probe, never publish.

The predecessor L9-AS independently counted a heading and marker but did not
require them to belong to the same event section. This Gate refuses that gap.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import p30_l9as_famiticket_live_dom as prior

RELEASE = "HARD_HOLD_NO_PUBLICATION"
LABELS = ("活動時間", "活動地點", "活動票價")

def inspect_local(html):
    base = dict(source="FAMITICKET_07", decision="HOLD_INPUT",
                sourceQuality="UNKNOWN", semanticSection="UNKNOWN",
                roleLabelCounts={}, identity="UNKNOWN",
                acceptedFields=0, goldenAccepted=0, published=False,
                ticketEventId=None, releaseState=RELEASE)
    old = prior.inspect_html(html, prior.URL, prior.TITLE)
    base["priorIdentityDecision"] = old["decision"]
    if not old["decision"].startswith("REVIEW_"):
        return dict(base, decision="HOLD_PRIOR_IDENTITY")
    soup = BeautifulSoup(html, "html.parser")
    headings = [x for x in soup.find_all(["h1","h2","h3","h4"])
                if prior.norm(x.get_text(" ",strip=True)) == prior.TITLE and not prior.hidden(x)]
    markers = [x for x in soup.find_all("img")
               if prior.norm(x.get("alt","")) == "《活動資訊》" and not prior.hidden(x)]
    markers += [x.parent for x in soup.find_all(string=True)
                if x.parent is not None and prior.norm(x) == "《活動資訊》"
                and not prior.hidden(x.parent)]
    if len(headings) != 1 or len(markers) != 1:
        return dict(base, decision="HOLD_NONUNIQUE_LOCAL_ANCHORS")
    heading, marker = headings[0], markers[0]
    base["headingParentTag"] = heading.parent.name
    base["markerParentTag"] = marker.parent.name
    sections = [x for x in marker.parents if getattr(x,"name",None) in ("section","article")
                and heading in x.descendants and not prior.hidden(x)]
    if not sections:
        return dict(base, decision="HOLD_NO_SHARED_SEMANTIC_EVENT_SECTION",
                    sourceQuality="REVIEW_STRUCTURE_NO_SHARED_SECTION")
    section = sections[0]
    text = prior.norm(section.get_text(" ",strip=True))
    base["semanticSection"] = section.name
    base["sectionTextChars"] = len(text)
    if len(text) > 6000 or len(text) < 15:
        return dict(base, decision="HOLD_SECTION_TEXT_BOUNDS")
    counts = {label: text.count(label) for label in LABELS}
    base["roleLabelCounts"] = counts
    base["identity"] = "REVIEW_SHARED_SEMANTIC_SECTION_EXACT_TITLE"
    if any(v != 1 for v in counts.values()):
        return dict(base, decision="HOLD_NONUNIQUE_LOCAL_ROLE_LABELS",
                    sourceQuality="REVIEW_LOCAL_LABEL_COUNTS")
    if "退票" in text:
        return dict(base, decision="HOLD_REFUND_WITHIN_EVENT_SECTION",
                    sourceQuality="REVIEW_REFUND_AMBIGUITY")
    return dict(base, decision="REVIEW_LOCAL_ROLE_TOPOLOGY_NO_FIELD_ACCEPTANCE",
                sourceQuality="REVIEW_LOCAL_SECTION")

def fetch_one():
    import requests
    audit = dict(observedAtUTC=datetime.now(timezone.utc).isoformat(),
                 requestCount=1, httpStatus=None, bodyBytes=0,
                 bodySHA256=None, decision="HOLD_NETWORK",
                 sourceQuality="HOLD_NETWORK", acceptedFields=0,
                 goldenAccepted=0, published=False, releaseState=RELEASE)
    try:
        with requests.get(prior.URL, headers={"User-Agent":"EventRadar-ReadOnly/1.0"},
                          timeout=(6,12), allow_redirects=False, stream=True) as response:
            audit["httpStatus"] = response.status_code
            if response.status_code != 200:
                return dict(audit, decision="HOLD_HTTP_STATUS")
            if response.headers.get("Content-Type","").split(";")[0].lower() not in ("text/html","application/xhtml+xml"):
                return dict(audit, decision="HOLD_CONTENT_TYPE")
            parts, size = [], 0
            for chunk in response.iter_content(32768):
                size += len(chunk)
                if size > prior.MAX_HTML_BYTES:
                    return dict(audit, decision="HOLD_BODY_CAP", bodyBytes=size)
                parts.append(chunk)
            raw = b"".join(parts)
            audit.update(bodyBytes=len(raw),bodySHA256=hashlib.sha256(raw).hexdigest())
            audit.update(inspect_local(raw.decode(response.encoding or "utf-8",errors="replace")))
    except Exception as exc:
        audit["networkErrorClass"] = type(exc).__name__
    return audit

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f:
        json.dump(fetch_one(),f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
