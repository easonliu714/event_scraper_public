"""Bounded native TPAC /event source receipt (NOT publication).

At most one robots.txt, one /event LIST, and two distinct /event/{id}
DETAIL requests. No redirects, login, bypass, retry, or overwrite of official
docs/data.json. Every source attempt is one-shot and must be separately
deduplicated by the invoking exact-head workflow.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
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


def bounded_fetch(url, *, opener=None, allowed_ids=SOURCE_IDS):
    allowed = {ROBOTS, ROOT, *(ROOT + "/" + sid for sid in allowed_ids)}
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




def collect_bounded_review_cycle(out, cycle_id, *, source_policy_approved=False,
                                 fetch=None, clock=None, pause=None,
                                 registry_dir=None):
    """Bounded /event native cycle for a separately approved, isolated R4 attempt.

    A fresh, exclusive output directory is a LOCAL one-shot claim, not a
    cross-run GitHub registry. Neither successful capture nor a second replay
    proves two independent source cycles or authorizes a formal Publisher.
    No automatic workflow calls this function.
    """
    if source_policy_approved is not True:
        raise ValueError("TPAC_R4_SOURCE_POLICY_AUTHORITY_HOLD")
    if not isinstance(cycle_id, str) or not re.fullmatch(r"tpac-r4-[a-z0-9-]{8,72}", cycle_id):
        raise ValueError("TPAC_R4_CYCLE_ID_HOLD")
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise ValueError("TPAC_R4_CYCLE_ALREADY_CLAIMED_HOLD")
    # Persist a one-shot claim before any HTTP request. O_EXCL serializes
    # processes on this filesystem; a crash leaves a fail-closed tombstone.
    # This is NOT a cross-host or GitHub-global source registry.
    if registry_dir is None:
        raise ValueError("TPAC_R4_DURABLE_REGISTRY_REQUIRED_HOLD")
    registry = Path(registry_dir)
    if registry.is_symlink() or not registry.is_dir():
        raise ValueError("TPAC_R4_DURABLE_REGISTRY_UNTRUSTED_HOLD")
    claim = registry / (cycle_id + ".claim.json")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(claim, flags, 0o600)
    except FileExistsError as exc:
        raise ValueError("TPAC_R4_DURABLE_CYCLE_REUSE_HOLD") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"cycle_id": cycle_id, "catalog": "event",
                   "output": str(out.resolve()), "state": "CONSUMED_BEFORE_NETWORK",
                   "global_registry_verified": False}, handle, sort_keys=True)
        handle.write(chr(10))
        handle.flush()
        os.fsync(handle.fileno())
    out.mkdir(parents=True, exist_ok=False)
    clock = clock or (lambda: datetime.now(timezone.utc))
    pause = pause or time.sleep
    selected = ()
    report = {
        "kind": "TPAC_R4_ISOLATED_BOUNDED_NATIVE_CYCLE_NOT_FORMAL",
        "cycle_id": cycle_id, "catalog": "event",
        "decision": "HOLD", "first_failure": "NOT_STARTED",
        "attempted_urls": [], "successful_get": 0,
        "source_receipts": {}, "selected_ids": [],
        "robots_allowed": False, "robots_sha256": None,
        "request_gap_seconds": None,
        "local_one_shot_claim": True, "durable_local_registry_claimed": True,
        "global_one_shot_registry_verified": False,
        "independent_cycle_verified": False, "native_official_attestation": False,
        "accepted_fields": 0, "published": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }
    blobs = {}
    manifest = None
    try:
        def observed():
            value = clock()
            if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("TPAC_R4_CLOCK_TIMEZONE_HOLD")
            return value.astimezone(timezone.utc)

        def take(url):
            allowed = {ROBOTS, ROOT, *(ROOT + "/" + sid for sid in selected)}
            if url not in allowed:
                raise ValueError("TPAC_R4_UNAPPROVED_URL_HOLD")
            report["attempted_urls"].append(url)
            raw = (fetch(url) if fetch is not None
                   else bounded_fetch(url, allowed_ids=selected))
            if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BODY:
                raise ValueError("TPAC_R4_BODY_CAP_OR_TYPE_HOLD")
            report["successful_get"] += 1
            return raw

        robots = take(ROBOTS)
        report["robots_sha256"] = hashlib.sha256(robots).hexdigest()
        if not re.search(rb"(?im)^\s*user-agent\s*:", robots):
            raise ValueError("TPAC_R4_ROBOTS_POLICY_MISSING_HOLD")
        parsed = robotparser.RobotFileParser()
        parsed.parse(robots.decode("utf-8", "strict").splitlines())
        if not parsed.can_fetch(AGENT, ROOT):
            raise ValueError("TPAC_R4_ROBOTS_LIST_DISALLOW_HOLD")
        crawl = parsed.crawl_delay(AGENT) or parsed.crawl_delay("*") or 0
        if crawl > 60:
            raise ValueError("TPAC_R4_ROBOTS_CRAWL_DELAY_OVER_BUDGET_HOLD")
        gap = max(3, crawl)
        report["request_gap_seconds"] = gap
        pause(gap)
        listing = take(ROOT)
        blobs["event_list.html"] = listing
        report["source_receipts"]["list"] = _receipt(ROOT, listing, observed())
        found = _visible_detail_ids(listing)
        report["listed_id_count"] = len(found)
        if not 2 <= len(found) <= 150:
            raise ValueError("TPAC_R4_LIST_DISTINCT_ID_COUNT_HOLD")
        selected = tuple(found[:2])
        report["selected_ids"] = list(selected)
        if not all(parsed.can_fetch(AGENT, ROOT + "/" + sid) for sid in selected):
            raise ValueError("TPAC_R4_ROBOTS_DETAIL_DISALLOW_HOLD")
        details = {}
        for sid in selected:
            pause(gap)
            url = ROOT + "/" + sid
            raw = take(url)
            blobs["event_" + sid + "_detail.html"] = raw
            receipt = _receipt(url, raw, observed())
            report["source_receipts"][sid] = receipt
            details[sid] = {
                "detail_file": str((out / ("event_" + sid + "_detail.html")).resolve()),
                "receipt": receipt,
            }
        manifest = {
            "catalog": "event", "cycle_id": cycle_id,
            "list_file": str((out / "event_list.html").resolve()),
            "list_receipt": report["source_receipts"]["list"],
            "details": details, "now": observed().isoformat(),
        }
        report["decision"] = "ISOLATED_NATIVE_BYTES_CAPTURED_REPLAY_REQUIRED"
        report["first_failure"] = "INDEPENDENT_BODY_AND_RECEIPT_READBACK_PENDING"
    except (HTTPError, URLError, OSError, UnicodeError, ValueError, TimeoutError) as exc:
        report["first_failure"] = type(exc).__name__ + ":" + str(exc)
    for name, raw in blobs.items():
        (out / name).write_bytes(raw)
    (out / "tpac_r4_cycle_receipt.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    # No consumable manifest on a partial/denied capture; keep forensic bytes.
    if manifest is not None:
        (out / "tpac_r4_refresh_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cycle-id", help="unique approved isolated TPAC-R4 cycle identifier")
    parser.add_argument("--registry-dir", type=Path,
                        help="pre-existing durable local claim directory; NOT cross-host")
    parser.add_argument("--authorize-isolated-cycle", action="store_true",
                        help="explicit operator confirmation of separately approved source policy")
    args = parser.parse_args()
    if args.cycle_id is not None or args.authorize_isolated_cycle:
        report = collect_bounded_review_cycle(
            args.output, args.cycle_id,
            source_policy_approved=args.authorize_isolated_cycle,
            registry_dir=args.registry_dir)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        raise SystemExit(0 if report["decision"] == "ISOLATED_NATIVE_BYTES_CAPTURED_REPLAY_REQUIRED" else 49)
    report = collect_once(args.output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    # Legacy one-shot is already consumed; CI never reissues that GET.
    raise SystemExit(0)
