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


class OfflineFixtureTransport:
    """Deterministic in-memory bytes only; no caller-provided HTTP callbacks.

    Exact built-in types prevent arbitrary transport callbacks from bypassing
    the consumed one-shot marker or the unapproved R4 retention gate.
    """

    def __init__(self, responses):
        if type(responses) is not dict or not responses:
            raise ValueError("TPAC_OFFLINE_FIXTURE_MAP_REQUIRED_HOLD")
        self._responses = {}
        for url, value in responses.items():
            parts = urlsplit(url) if type(url) is str else None
            if (parts is None or parts.scheme != "https"
                    or parts.netloc != "tpac.org.taipei"
                    or parts.query or parts.fragment
                    or (url not in (ROOT, ROBOTS)
                        and not re.fullmatch(r"/event/[1-9]\d{0,9}", parts.path))):
                raise ValueError("TPAC_OFFLINE_FIXTURE_URL_HOLD")
            if type(value) is bytes and 0 < len(value) <= MAX_BODY:
                self._responses[url] = value
            elif type(value) is ValueError:
                self._responses[url] = value
            else:
                raise ValueError("TPAC_OFFLINE_FIXTURE_BYTES_OR_ERROR_HOLD")
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        if url not in self._responses:
            raise ValueError("TPAC_OFFLINE_FIXTURE_MISSING_URL_HOLD")
        value = self._responses[url]
        if type(value) is ValueError:
            raise value
        return value



class OfflineFixtureClock:
    """Sealed deterministic time source for fixture-only replay; never a callback."""

    def __init__(self, observed_at):
        if (type(observed_at) is not datetime or observed_at.tzinfo is None
                or observed_at.utcoffset() is None):
            raise ValueError("TPAC_R4_OFFLINE_CLOCK_AWARE_DATETIME_HOLD")
        self._observed_at = observed_at.astimezone(timezone.utc)

    def __call__(self):
        return self._observed_at


class OfflineFixturePause:
    """Record simulated gaps without executing an arbitrary sleep callback."""

    def __init__(self):
        self.calls = []

    def __call__(self, seconds):
        if type(seconds) not in (int, float) or not 0 <= seconds <= 60:
            raise ValueError("TPAC_R4_OFFLINE_GAP_BUDGET_HOLD")
        self.calls.append(seconds)


def bounded_fetch(url, *, opener=None, allowed_ids=SOURCE_IDS):
    """Retired direct native GET entrypoint: no caller can reconsume one-shot.

    The original /event source marker is already consumed. This function
    deliberately retains its old signature for fail-closed compatibility, but
    never constructs a Request or calls an opener, even when explicitly given
    a transport. A future live R4 fetch must be implemented only behind a
    separately approved immutable cross-host retention and source policy Gate.
    """
    allowed = {ROBOTS, ROOT, *(ROOT + "/" + sid for sid in allowed_ids)}
    if url not in allowed:
        raise ValueError("TPAC_EVENT_UNAPPROVED_URL_HOLD")
    # A direct Python call previously bypassed the protected CLI path.
    # Reject BEFORE any network side effect, including injected openers.
    raise ValueError("TPAC_EVENT_DIRECT_NATIVE_FETCH_DISABLED_HOLD")


def _receipt(url, raw, now):
    return {
        "http_status": 200, "final_url": url,
        "robots_allowed": True,
        "observed_at": now.isoformat(),
        "body_sha256": hashlib.sha256(raw).hexdigest(),
        "body_bytes": len(raw),
        "offline_fixture_replay": True,
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


def collect_once(out, *, fetch=None):
    """Offline replay of consumed legacy one-shot; never initiate native GET.

    Only exact OfflineFixtureTransport byte maps are permitted for replay.
    No arbitrary callback, opener, or native HTTP path can be injected.
    """
    # The original first-party one-shot marker was consumed in run 42491637804.
    # Neither default CLI invocation nor passing the native fetcher may re-GET.
    if fetch is None or fetch is bounded_fetch:
        raise ValueError("TPAC_EVENT_LEGACY_NATIVE_FETCH_DISABLED_HOLD")
    if type(fetch) is not OfflineFixtureTransport:
        raise ValueError("TPAC_EVENT_UNTRUSTED_FETCH_CALLBACK_HOLD")
    out = Path(out)
    report = {
        "kind": "EVENTRADAR_TPAC_EVENT_TWO_DETAILS_SINGLE_AUDIT",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "requested_ids": list(SOURCE_IDS),
        "robots_url": ROBOTS, "list_url": ROOT,
        "successful_get": 0, "attempted_urls": [],
        "new_native_http_get": 0, "offline_fixture_replay": True,
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
        report["decision"] = "OFFLINE_FIXTURE_REPLAY_ONLY"
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





class GitHubAtomicClaimRegistry:
    """Cross-host atomic one-shot source claim via unique GitHub Git tag refs.

    A tag creation is an atomic uniqueness check across runners. A tag can be
    deleted by a privileged actor: this is NOT immutable retention authority.
    Requires separate Owner source-frequency approval; it never publishes data.
    No automatic CI execution, no retries, and no HTTP source GET on failure.
    """

    API = "https://api.github.com/repos/easonliu714/event_scraper_public"

    def __init__(self, token, expected_main_sha, *, opener=None):
        if not isinstance(token, str) or not token.strip():
            raise ValueError("TPAC_R4_GLOBAL_CLAIM_TOKEN_REQUIRED_HOLD")
        if not isinstance(expected_main_sha, str) or not re.fullmatch(
                r"[0-9a-f]{40}", expected_main_sha):
            raise ValueError("TPAC_R4_GLOBAL_CLAIM_MAIN_SHA_HOLD")
        self._token = token
        self.expected_main_sha = expected_main_sha
        self._opener = opener or build_opener(NoRedirect())

    def _request(self, method, url, *, payload=None, status=200):
        raw_payload = (json.dumps(payload, sort_keys=True).encode("utf-8")
                       if payload is not None else None)
        request = Request(
            url, data=raw_payload, method=method,
            headers={
                "Authorization": "Bearer " + self._token,
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": AGENT,
            })
        try:
            with self._opener.open(request, timeout=15) as response:
                if response.status != status or response.geturl() != url:
                    raise ValueError("TPAC_R4_GLOBAL_CLAIM_REDIRECT_OR_STATUS_HOLD")
                raw = response.read(65537)
                if not 0 < len(raw) <= 65536:
                    raise ValueError("TPAC_R4_GLOBAL_CLAIM_RESPONSE_CAP_HOLD")
                value = json.loads(raw.decode("utf-8", "strict"))
                if not isinstance(value, dict):
                    raise ValueError("TPAC_R4_GLOBAL_CLAIM_JSON_OBJECT_HOLD")
                return value
        except HTTPError as exc:
            if exc.code == 422:
                raise ValueError("TPAC_R4_GLOBAL_CYCLE_ALREADY_CLAIMED_OR_REJECTED_HOLD") from exc
            raise ValueError("TPAC_R4_GLOBAL_CLAIM_HTTP_HOLD") from exc
        except (URLError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("TPAC_R4_GLOBAL_CLAIM_HTTP_OR_JSON_HOLD") from exc

    def claim(self, cycle_id):
        if not isinstance(cycle_id, str) or not re.fullmatch(
                r"tpac-r4-[a-z0-9-]{8,72}", cycle_id):
            raise ValueError("TPAC_R4_GLOBAL_CLAIM_CYCLE_ID_HOLD")
        main = self._request("GET", self.API + "/git/ref/heads/main")
        if (main.get("ref") != "refs/heads/main"
                or not isinstance(main.get("object"), dict)
                or main["object"].get("sha") != self.expected_main_sha):
            raise ValueError("TPAC_R4_GLOBAL_CLAIM_MAIN_HEAD_DRIFT_HOLD")
        ref = "refs/tags/eventradar-tpac-r4-claims/" + cycle_id
        url = self.API + "/git/ref/tags/eventradar-tpac-r4-claims/" + cycle_id
        created = self._request(
            "POST", self.API + "/git/refs",
            payload={"ref": ref, "sha": self.expected_main_sha}, status=201)
        if (created.get("ref") != ref
                or not isinstance(created.get("object"), dict)
                or created["object"].get("sha") != self.expected_main_sha):
            raise ValueError("TPAC_R4_GLOBAL_CLAIM_CREATE_PARITY_HOLD")
        readback = self._request("GET", url)
        if (readback.get("ref") != ref
                or not isinstance(readback.get("object"), dict)
                or readback["object"].get("sha") != self.expected_main_sha):
            raise ValueError("TPAC_R4_GLOBAL_CLAIM_READBACK_PARITY_HOLD")
        return {
            "ref": ref, "main_sha": self.expected_main_sha,
            "global_atomic_claim_created": True,
            "global_immutable_registry_verified": False,
        }



def collect_bounded_review_cycle(out, cycle_id, *, source_policy_approved=False,
                                 fetch=None, clock=None, pause=None,
                                 registry_dir=None, global_registry=None):
    """Bounded /event native cycle for a separately approved, isolated R4 attempt.

    Requires both a local crash-persistent tombstone and a GitHub atomic tag
    claim, created/read back before source GET. Tags can be deleted by admins,
    so this does not prove immutable global registry retention. No automatic
    Publisher or two-independent-native-cycle attestation.
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
    if claim.exists() or claim.is_symlink():
        raise ValueError("TPAC_R4_DURABLE_CYCLE_REUSE_HOLD")
    # Never trust a caller-provided boolean or dict as a global claim. Only
    # This concrete client can create and independently read back an atomic ref.
    if type(global_registry) is not GitHubAtomicClaimRegistry:
        raise ValueError("TPAC_R4_GLOBAL_ATOMIC_REGISTRY_REQUIRED_HOLD")
    # Production CLI supplies no injected fetch. A GitHub tag is deletable and
    # therefore cannot authorize live HTTP until independently governed,
    # immutable cross-host retention is implemented and verified. Preserve
    # mock-only offline contract tests without creating a real source request.
    if fetch is None:
        raise ValueError("TPAC_R4_GLOBAL_RETENTION_AUTHORITY_UNVERIFIED_HOLD")
    if type(fetch) is not OfflineFixtureTransport:
        raise ValueError("TPAC_R4_UNTRUSTED_FETCH_CALLBACK_HOLD")
    # Test clocks and delays are also executable injection surfaces. Only
    # exact sealed offline fixtures are allowed before any global claim.
    if clock is not None and type(clock) is not OfflineFixtureClock:
        raise ValueError("TPAC_R4_UNTRUSTED_CLOCK_CALLBACK_HOLD")
    if pause is not None and type(pause) is not OfflineFixturePause:
        raise ValueError("TPAC_R4_UNTRUSTED_PAUSE_CALLBACK_HOLD")
    global_claim = global_registry.claim(cycle_id)
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
                   "global_registry_verified": False,
                   "global_claim_ref": global_claim["ref"],
                   "global_atomic_claim_created": True}, handle, sort_keys=True)
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
        "new_native_http_get": 0, "offline_fixture_replay": True,
        "source_receipts": {}, "selected_ids": [],
        "robots_allowed": False, "robots_sha256": None,
        "request_gap_seconds": None,
        "local_one_shot_claim": True, "durable_local_registry_claimed": True,
        "global_one_shot_registry_verified": False,
        "global_atomic_claim_created": True,
        "global_claim_ref": global_claim["ref"],
        "global_claim_main_sha": global_claim["main_sha"],
        "global_immutable_registry_verified": False,
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
        report["decision"] = "ISOLATED_OFFLINE_FIXTURE_REPLAY_ONLY"
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
    parser.add_argument("--global-github-ref-claim", action="store_true",
                        help="create a unique GitHub tag ref before source GET; needs dedicated token")
    parser.add_argument("--global-expected-main-sha",
                        help="fresh exact main SHA to compare before atomic tag creation")
    parser.add_argument("--authorize-isolated-cycle", action="store_true",
                        help="explicit operator confirmation of separately approved source policy")
    args = parser.parse_args()
    if args.cycle_id is not None or args.authorize_isolated_cycle:
        global_registry = None
        if args.global_github_ref_claim:
            global_registry = GitHubAtomicClaimRegistry(
                os.environ.get("EVENTRADAR_SOURCE_CLAIM_GITHUB_TOKEN"),
                args.global_expected_main_sha)
        report = collect_bounded_review_cycle(
            args.output, args.cycle_id,
            source_policy_approved=args.authorize_isolated_cycle,
            registry_dir=args.registry_dir, global_registry=global_registry)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        raise SystemExit(0 if report["decision"] == "ISOLATED_OFFLINE_FIXTURE_REPLAY_ONLY" else 49)
    # The legacy source marker is consumed. An unqualified CLI invocation
    # must never become a second network path around TPAC-R4 retention HOLD.
    print(json.dumps({
        "kind": "TPAC_EVENT_LEGACY_ONESHOT_CONSUMED",
        "decision": "HOLD",
        "first_failure": "TPAC_EVENT_LEGACY_NATIVE_GET_DISABLED_HOLD",
        "published": 0,
    }, ensure_ascii=False, sort_keys=True))
    raise SystemExit(49)
