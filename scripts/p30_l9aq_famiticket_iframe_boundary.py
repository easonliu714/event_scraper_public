#!/usr/bin/env python3
"""P30-L9-AQ: FamiTicket iframe-only detail boundary, REVIEW/HOLD, no publication.

Source-first observation: official /Home list has /Home/Activity/Info/ cards,
but a sampled detail exposes an iframe shell rather than a matching H1/H2.
Never follow the iframe, infer ticket identity, or accept a date/price.
"""
from __future__ import annotations
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit
import p30_l3b_a_famiticket as frozen

MAX_BYTES = 800_000
MAX_FRAMES = 3
RELEASE = "HARD_HOLD_NO_PUBLICATION"

def classify_detail(html: bytes, expected_title: str, detail_url: str) -> dict:
    """Inspect one bounded official detail HTML; fail closed on iframe shells."""
    base = dict(decision="HOLD_INPUT", headingMatches=0, iframeCount=0,
                iframeSameOriginCount=0, iframeFollowed=False, acceptedFields=0,
                goldenAccepted=0, published=False, releaseState=RELEASE)
    if (not isinstance(html, bytes) or not html or len(html) > MAX_BYTES
            or not isinstance(expected_title, str) or not expected_title.strip()
            or len(expected_title) > 180
            or not frozen.allowed(detail_url, detail=True)):
        return base
    try:
        soup = BeautifulSoup(html.decode("utf-8-sig"), "html.parser")
    except UnicodeError:
        return dict(base, decision="HOLD_ENCODING")
    for n in soup(["script", "style", "template"]):
        n.decompose()
    headings = [frozen.norm(h.get_text(" ", strip=True))
                for h in soup.find_all(["h1", "h2", "h3", "h4"])]
    matches = sum(x == frozen.norm(expected_title) for x in headings)
    frames = soup.find_all("iframe")
    if len(frames) > MAX_FRAMES:
        return dict(base, decision="HOLD_IFRAME_CAP", iframeCount=len(frames))
    same = 0
    for frame in frames:
        src = frame.get("src", "")
        if not isinstance(src, str) or not src:
            continue
        target = urlsplit(urljoin(detail_url, src))
        if (target.scheme == "https" and target.hostname == frozen.BASE_HOST
                and target.username is None and target.password is None
                and target.port in (None, 443)):
            same += 1
    if matches != 1:
        decision = ("HOLD_IFRAME_ONLY_NO_TITLE_IDENTITY" if frames and matches == 0
                    else "HOLD_TITLE_MISMATCH_OR_AMBIGUITY")
    elif frames:
        decision = "HOLD_IFRAME_PRESENT_EVEN_WITH_HEADING"
    else:
        decision = "REVIEW_EXACT_HEADING_ONLY_NO_FIELDS"
    return dict(base, decision=decision, headingMatches=matches,
                iframeCount=len(frames), iframeSameOriginCount=same)

if __name__ == "__main__":
    raise SystemExit("HOLD_NO_DIRECT_EXECUTION: import and test only; no official GET")
