"""Opt-in TaiNEX source gateway: robots -> LIST -> same-ID DETAIL, isolated only.

No scheduler, publisher, or Claim release. Network requests require --execute and
the operator's independently confirmed source-specific authorization.
"""
import argparse
import hashlib
import json
import time
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser

from scripts.p30_tainex_response_evidence import ingest_response

ORIGIN = "https://www.tainex.com.tw"
ROBOTS = ORIGIN + "/robots.txt"
LIST = ORIGIN + "/event"
USER_AGENT = "EventRadarTaiwanSourceResearch/1.0"
MAX_BYTES = 2_000_000
MIN_DELAY = 10.0


class ListLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def fetch_bounded(url, opener, *, agent=USER_AGENT):
    """One HTTPS GET, no redirects or off-host hops; preserve raw bytes."""
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "www.tainex.com.tw"
            or parsed.username or parsed.password or parsed.query
            or parsed.fragment or parsed.port is not None):
        raise ValueError("SOURCE_SCOPE_HOLD")
    request = Request(url, headers={"User-Agent": agent, "Accept": "text/html,*/*"})
    try:
        response = opener.open(request, timeout=15)
    except HTTPError as exc:
        if exc.code in (403, 429):
            raise ValueError("SOURCE_403_429_STOP") from exc
        raise ValueError("SOURCE_HTTP_ERROR_HOLD_" + str(exc.code)) from exc
    with response:
        status = response.status
        final = response.geturl()
        if final != url:
            raise ValueError("SOURCE_REDIRECT_HOLD")
        if status != 200:
            raise ValueError("SOURCE_HTTP_STATUS_HOLD_" + str(status))
        data = response.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise ValueError("SOURCE_BODY_SIZE_HOLD")
    return data


def capture(*, output_dir, detail_id=None, execute=False, opener=None,
            sleeper=time.sleep, clock=None):
    """Fail closed; only an explicit event ID permits same-ID DETAIL."""
    if not execute:
        raise ValueError("EXPLICIT_EXECUTE_REQUIRED")
    if detail_id is not None and (not isinstance(detail_id, str)
            or not detail_id.isascii() or not detail_id.isdecimal()
            or not 1 <= len(detail_id) <= 8):
        raise ValueError("DETAIL_ID_SCOPE_HOLD")
    opener = opener or build_opener(NoRedirect())
    clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
    # Robots must be fetched and parsed before any event request.
    robots_raw = fetch_bounded(ROBOTS, opener)
    robots = RobotFileParser()
    # A malformed or non-robots HTML response must never authorize LIST.
    # RobotFileParser defaults to permissive behavior without valid groups.
    robots_text = robots_raw.decode("utf-8", "strict")
    robots_lines = robots_text.splitlines()
    if not any(line.strip().lower().startswith("user-agent:") for line in robots_lines):
        raise ValueError("ROBOTS_INVALID_RESPONSE_HOLD")
    robots.parse(robots_lines)
    if not robots.can_fetch(USER_AGENT, LIST):
        raise ValueError("ROBOTS_LIST_DENIED_HOLD")
    detail_url = ORIGIN + "/event/" + detail_id if detail_id else None
    if detail_url and not robots.can_fetch(USER_AGENT, detail_url):
        raise ValueError("ROBOTS_DETAIL_DENIED_HOLD")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    receipts = []
    # robots.txt is itself a network request: enforce the source-wide delay
    # before LIST as well as between LIST and DETAIL, not only for DETAIL.
    delay = max(MIN_DELAY, float(robots.crawl_delay(USER_AGENT) or 0))
    for role, url in (("LIST", LIST), ("DETAIL", detail_url)):
        if url is None:
            continue
        sleeper(delay)
        raw = fetch_bounded(url, opener)
        if role == "LIST" and detail_url:
            links = ListLinks()
            links.feed(raw.decode("utf-8", "strict"))
            if sum(urljoin(LIST, href) == detail_url for href in links.hrefs) != 1:
                raise ValueError("DETAIL_ID_NOT_IN_CURRENT_LIST_HOLD")
        observed_at = clock()
        # Store in isolated location only; never claim native HTTP attestation.
        # A fixed incoming-ROLE.tmp blocks recovery after an interrupted run.
        # Use a unique private staging file and always remove it after ingestion.
        if output_dir.is_symlink():
            raise ValueError("OUTPUT_SYMLINK_HOLD")
        with tempfile.NamedTemporaryFile(mode="wb", prefix="incoming-" + role.lower() + "-",
                                         suffix=".tmp", dir=output_dir, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
        try:
            receipt = ingest_response(raw_path=temporary, output_dir=output_dir,
                                      source_url=url, final_url=url,
                                      http_status=200, observed_at=observed_at)
        finally:
            temporary.unlink(missing_ok=True)
        receipt["role"] = role
        receipts.append(receipt)
    return {"decision": "ISOLATED_CAPTURE_NO_PUBLICATION",
            "native_http_attested": False, "receipts": receipts,
            "robots_sha256": hashlib.sha256(robots_raw).hexdigest(),
            "robots_bytes": len(robots_raw)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--detail-id")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    print(json.dumps(capture(output_dir=args.output_dir,
                             detail_id=args.detail_id,
                             execute=args.execute), sort_keys=True))


if __name__ == "__main__":
    main()
