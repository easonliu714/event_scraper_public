#!/usr/bin/env python3
"""P30-VENUE-01F: one official detail GET, aggregate-only identity/label topology.
DataSN is an announcement identifier; no title parity without same-source list.
No redirects, retries, cookies, JS, ticket access, raw HTML or field values stored.
"""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.request, urllib.error
from html.parser import HTMLParser
from pathlib import Path
import p30_venue01_taipei_arena_readonly as arena

KIND = "EVENTRADAR_P30_VENUE01F_LIVE_DETAIL_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
DETAIL = "https://www.arena.taipei/News_Content.aspx?n=2E1489AFE4B1BEA1&s=44EFCD82A9D43986"
MAX_BYTES = 1_000_000
LABELS = ("活動日期/時間", "活動日期", "演出日期", "入場時間", "售票系統", "日期時間")

class DetailHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.headings = []
        self.parts = []
        self.in_script = 0
    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)
        if tag in ("script", "style"):
            self.in_script += 1
        if tag in ("h1", "h2"):
            self.headings.append([])
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.in_script:
            self.in_script -= 1
        if tag in ("h1", "h2") and self.headings:
            self.headings[-1].append(" ")
        if self.stack:
            self.stack.pop()
    def handle_data(self, data):
        if self.in_script:
            return
        if self.stack and self.stack[-1] in ("h1", "h2") and self.headings:
            self.headings[-1].append(data)
        if any(x in self.stack for x in ("main", "article", "section")):
            self.parts.append(data[:300])

def assess_html(body: object, status: int, final_url: str, redirected: bool) -> dict:
    base = dict(kind=KIND, releaseState=RELEASE, decision="HOLD_INPUT",
        source="TAIPEI_ARENA_OFFICIAL_DETAIL", sourceDataSN="REVIEW_PRIOR_OPENDATA_ONLY",
        detailUrlValid=False, http=status if type(status) is int else None,
        headingCount=0, explicitLabelCounts={}, titleParity="UNVERIFIED_NO_SAME_SESSION_LIST",
        ticketEventId=None, acceptedFields=0, goldenAccepted=0, published=False,
        rawHtmlPersisted=False, rawTitlesPersisted=False, rawDatesPersisted=False,
        rawUrlsPersisted=False, announcementTimeIsEventTime=False)
    if not arena._source_url_ok(final_url) or final_url != DETAIL or redirected:
        return dict(base, decision="HOLD_URL_OR_REDIRECT")
    if status != 200 or not isinstance(body, bytes) or len(body) > MAX_BYTES:
        return dict(base, decision="HOLD_HTTP_OR_BODY_CAP")
    try:
        decoded = body.decode("utf-8-sig")
    except UnicodeError:
        return dict(base, decision="HOLD_ENCODING")
    parser = DetailHTML()
    try:
        parser.feed(decoded)
    except Exception:
        return dict(base, decision="HOLD_HTML_PARSER")
    headings = [" ".join("".join(h).split()) for h in parser.headings]
    headings = [h for h in headings if h]
    local = " ".join(parser.parts)
    counts = {k: len(re.findall(re.escape(k) + r"\s*[:：]", local)) for k in LABELS}
    # No date extraction or role promotion; labels are not enough to prove values.
    decision = "REVIEW_HTTP200_DETAIL_STRUCTURE_NOT_IDENTITY" if headings else "HOLD_NO_DETAIL_HEADING"
    return dict(base, decision=decision, detailUrlValid=True, headingCount=len(headings),
                explicitLabelCounts=counts)

def fetch_once() -> dict:
    opener = urllib.request.build_opener(arena.NoRedirect)
    req = urllib.request.Request(DETAIL, headers={"User-Agent":"EventRadarVenueReadOnly/1.0",
                                                  "Accept":"text/html"}, method="GET")
    try:
        with opener.open(req, timeout=12) as response:
            status = response.status
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "").lower()
            body = response.read(MAX_BYTES+1)
        if not content_type.startswith("text/html"):
            return assess_html(None, status, final_url, False)
        return assess_html(body, status, final_url, False)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return dict(kind=KIND, releaseState=RELEASE, decision="HOLD_HTTP_OR_NETWORK",
                    http=None, acceptedFields=0, goldenAccepted=0, published=False)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    p.add_argument("--out", required=True)
    args=p.parse_args()
    if not args.live:
        p.error("explicit --live required")
    out=Path(args.out)
    if out.resolve() != (Path.cwd()/"p30-venue01f-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    report=fetch_once()
    out.mkdir(exist_ok=True)
    raw=(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2)+"\n").encode()
    (out/"detail_review.json").write_bytes(raw)
    (out/"manifest.json").write_text(json.dumps({"kind":KIND,"releaseState":RELEASE,
        "filesSHA256":{"detail_review.json":hashlib.sha256(raw).hexdigest()}},
        sort_keys=True, indent=2)+"\n")
    print("VENUE01F_DECISION="+report["decision"])
    print("VENUE01F_HTTP="+str(report.get("http")))
    print("HOLD_NO_FORMAL_FIELD_GOLDEN_PUBLICATION")
if __name__=="__main__":
    main()
