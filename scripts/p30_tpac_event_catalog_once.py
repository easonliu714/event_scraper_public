"""Bounded native TPAC /event source receipt (NOT publication).

At most one robots.txt, one /event LIST, and two distinct /event/{id}
DETAIL requests. No redirects, login, bypass, retry, or overwrite of official
docs/data.json. Every source attempt is one-shot and must be separately
deduplicated by the invoking exact-head workflow.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib import robotparser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from bs4 import BeautifulSoup

ROOT = "https://tpac.org.taipei/event"
ROBOTS = "https://tpac.org.taipei/robots.txt"
SOURCE_IDS = ("1301", "2072")
AGENT = "EventRadarTaiwan-SourceAudit/1.0"
MAX_BODY = 2 * 1024 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def bounded_fetch(url, *, opener=None):
    allowed = {ROBOTS, ROOT, *(ROOT + "/" + sid for sid in SOURCE_IDS)}
    if url not in allowed:
        raise ValueError("TPAC_EVENT_UNAPPROVED_URL_HOLD")
    req = Request(url, headers={"User-Agent": AGENT, "Accept": "text/html,text/plain"})
    with (opener or build_opener(NoRedirect())).open(req, timeout=15) as res:
        content_type = res.headers.get("Content-Type", "").lower()
        data = res.read(MAX_BODY + 1)
        if res.status != 200 or res.geturl() != url:
            raise ValueError("TPAC_EVENT_HTTP_OR_REDIRECT_HOLD")
        if len(data) == 0 or len(data) > MAX_BODY:
            raise ValueError("TPAC_EVENT_EMPTY_OR_OVERSIZE_HOLD")
        if ("text/" not in content_type if url == ROBOTS else
                "text/html" not in content_type):
            raise ValueError("TPAC_EVENT_UNEXPECTED_MIME_HOLD")
        return data


def _receipt(url, raw, now):
    return {
        "http_status": 200, "final_url": url,
        "robots_allowed": True,
        "observed_at": now.isoformat(),
        "body_sha256": hashlib.sha256(raw).hexdigest(),
        "body_bytes": len(raw),
    }


def _visible_detail_ids(raw):
    soup = BeautifulSoup(raw.decode("utf-8"), "html.parser")
    found = set()
    for a in soup.select("a[href]"):
        if a.find_parent(["template", "noscript", "script", "style"]):
            continue
        if a.attrs.get("hidden") is not None or a.attrs.get("aria-hidden") == "true":
            continue
        href = a.get("href", "")
        dest = urlsplit(urljoin(ROOT, href))
        if (dest.scheme == "https" and dest.netloc == "tpac.org.taipei"
                and not dest.query and not dest.fragment
                and re.fullmatch(r"/event/[1-9]\d{0,9}", dest.path)):
            found.add(dest.path.rsplit("/", 1)[-1])
    return sorted(found)


def collect_once(out, *, fetch=bounded_fetch):
    """Save original official bytes for independent replay, never infer field PASS."""
    out = Path(out)
    report = {
        "kind": "EVENTRADAR_TPAC_EVENT_TWO_DETAILS_SINGLE_AUDIT",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "requested_ids": list(SOURCE_IDS),
        "robots_url": ROBOTS, "list_url": ROOT,
        "successful_get": 0, "attempted_urls": [],
        "decision": "HOLD", "first_failure": "NOT_STARTED",
        "published": 0, "accepted_fields": 0, "native_official_attestation": False,
        "source_receipts": {},
    }
    blobs = {}
    try:
        def take(url):
            report["attempted_urls"].append(url)
            raw = fetch(url)
            report["successful_get"] += 1
            return raw

        robots = take(ROBOTS)
        parsed = robotparser.RobotFileParser()
        parsed.parse(robots.decode("utf-8").splitlines())
        urls = [ROOT] + [ROOT + "/" + x for x in SOURCE_IDS]
        if not all(parsed.can_fetch(AGENT, u) for u in urls):
            raise ValueError("TPAC_EVENT_ROBOTS_DISALLOW_HOLD")
        listing = take(ROOT)
        report["source_receipts"]["list"] = _receipt(ROOT, listing, datetime.now(timezone.utc))
        blobs["event_list.html"] = listing
        found = _visible_detail_ids(listing)
        report["listed_id_count"] = len(found)
        report["ids_present_on_list"] = [x for x in SOURCE_IDS if x in found]
        if len(report["ids_present_on_list"]) != len(SOURCE_IDS):
            raise ValueError("TPAC_EVENT_TWO_DISTINCT_LIST_EDGES_MISSING_HOLD")
        for ident in SOURCE_IDS:
            url = ROOT + "/" + ident
            body = take(url)
            blobs["event_" + ident + "_detail.html"] = body
            report["source_receipts"][ident] = _receipt(url, body, datetime.now(timezone.utc))
        report["decision"] = "NATIVE_BODY_CAPTURED_FOR_INDEPENDENT_REPLAY_ONLY"
        report["first_failure"] = "TPAC_EVENT_ROLE_AND_IDENTITY_FIELD_REPLAY_PENDING"
    except (HTTPError, URLError, OSError, UnicodeError, ValueError, TimeoutError) as exc:
        report["first_failure"] = type(exc).__name__ + ":" + str(exc)
    out.mkdir(parents=True, exist_ok=True)
    for name, raw in blobs.items():
        (out / name).write_bytes(raw)
    (out / "tpac_event_catalog_receipt.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = collect_once(args.output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    # Site HOLD is recorded in the artifact; this workflow is diagnostic only.
    raise SystemExit(0)
