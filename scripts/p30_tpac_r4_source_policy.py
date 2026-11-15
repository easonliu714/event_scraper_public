"""Owner-approved TPAC-R4 two-catalog source budget, OFFLINE REVIEW ONLY.

This module is a pure preflight. It makes zero network requests, claims no
real retention authority and cannot enable the live Collector/Publisher.
First-party TPAC /program and /event share ONE host-wide request budget:
one robots GET, one LIST per catalog, and at most TWO DETAIL GETs *total*.
A real live executor must independently prove a shared cross-host atomic
source lease and durable last-attempt record before any request. The former
six-hour owner interval was superseded on 2026-11-15; 3600s is only a
conservative engineering throttle, NOT a verified official source limit.

Existing GitHub lightweight tags are deletable. Github Actions artifacts,
local tombstones and CI fixtures are not authority for source GET.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from urllib import robotparser

from scripts.p30_tpac_catalog_topology import CATALOGS, discover_catalog

ROBOTS = "https://tpac.org.taipei/robots.txt"
AGENT = "EventRadarTaiwan-SourceAudit/1.0"
SOURCE_HOST = "tpac.org.taipei"
MIN_INTERVAL_SECONDS = 60 * 60
MAX_REQUESTS = 5
MAX_DETAIL_REQUESTS = 2
MAX_CONCURRENT = 1
MIN_REQUEST_GAP_SECONDS = 3
MAX_CRAWL_DELAY_SECONDS = 60
STOP_HTTP = (403, 429)
KIND = "TPAC_R4_OWNER_APPROVED_SOURCE_POLICY_REVIEW_V1"
CLAIM_HOLD = "HOLD_CROSS_HOST_IMMUTABLE_CLAIM_UNVERIFIED_NO_GET"
_CYCLE = re.compile(r"^tpac-r4-[a-z0-9-]{8,72}$")


@dataclass(frozen=True)
class RequestBudget:
    robots: int = 1
    program_list: int = 1
    event_list: int = 1
    detail_total: int = 2
    concurrency: int = 1
    interval_seconds: int = MIN_INTERVAL_SECONDS
    stop_http: tuple[int, ...] = STOP_HTTP

    def __post_init__(self):
        if type(self) is not RequestBudget or asdict(self) != {
            "robots": 1, "program_list": 1, "event_list": 1,
            "detail_total": 2, "concurrency": 1,
            "interval_seconds": MIN_INTERVAL_SECONDS, "stop_http": STOP_HTTP,
        }:
            raise ValueError("TPAC_R4_OWNER_BUDGET_IMMUTABLE_HOLD")


def _aware(value: datetime, label: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("TPAC_R4_" + label + "_AWARE_UTC_REQUIRED_HOLD")
    return value.astimezone(timezone.utc)


def _verify_robots(raw: bytes, urls: tuple[str, ...]) -> tuple[str, int]:
    if type(raw) is not bytes or not 0 < len(raw) <= 65536:
        raise ValueError("TPAC_R4_ROBOTS_MISSING_OR_TOO_LARGE_HOLD")
    if not re.search(rb"(?im)^\s*user-agent\s*:", raw):
        raise ValueError("TPAC_R4_ROBOTS_DIRECTIVES_MISSING_HOLD")
    try:
        lines = raw.decode("utf-8", "strict").splitlines()
    except UnicodeError as exc:
        raise ValueError("TPAC_R4_ROBOTS_INVALID_UTF8_HOLD") from exc
    policy = robotparser.RobotFileParser()
    policy.parse(lines)
    if not all(policy.can_fetch(AGENT, url) for url in urls):
        raise ValueError("TPAC_R4_ROBOTS_DENIED_AT_LEAST_ONE_URL_HOLD")
    wait = policy.crawl_delay(AGENT)
    if wait is None:
        wait = policy.crawl_delay("*")
    if wait is None:
        wait = 0
    if type(wait) not in (int, float) or not 0 <= wait <= MAX_CRAWL_DELAY_SECONDS:
        raise ValueError("TPAC_R4_ROBOTS_CRAWL_DELAY_EXCEEDS_BUDGET_HOLD")
    # robotparser exposes Request-rate separately from Crawl-delay. Ignoring it
    # can violate an official host-wide policy despite a valid Crawl-delay.
    rates = [policy.request_rate(AGENT), policy.request_rate("*")]
    intervals = [MIN_REQUEST_GAP_SECONDS, int(wait)]
    for rate in rates:
        if rate is not None:
            if (type(rate.requests) is not int or type(rate.seconds) is not int
                    or rate.requests <= 0 or rate.seconds <= 0):
                raise ValueError("TPAC_R4_ROBOTS_REQUEST_RATE_INVALID_HOLD")
            intervals.append((rate.seconds + rate.requests - 1) // rate.requests)
    # An explicitly present but unsupported directive must not silently
    # downgrade to the minimum spacing.
    if any(re.match(r"(?i)^\s*request-rate\s*:", line)
           for line in lines) and not any(rate is not None for rate in rates):
        raise ValueError("TPAC_R4_ROBOTS_REQUEST_RATE_UNSUPPORTED_HOLD")
    gap = max(intervals)
    if gap > MAX_CRAWL_DELAY_SECONDS:
        raise ValueError("TPAC_R4_ROBOTS_REQUEST_RATE_EXCEEDS_BUDGET_HOLD")
    return hashlib.sha256(raw).hexdigest(), gap


def enforce_elapsed(start_at: datetime, previous_claim_at: datetime | None) -> None:
    """Offline policy check; timestamp MUST come from a shared durable attempt ledger."""
    start = _aware(start_at, "START")
    if previous_claim_at is not None:
        previous = _aware(previous_claim_at, "PREVIOUS_CLAIM")
        if start < previous:
            raise ValueError("TPAC_R4_CLOCK_ROLLBACK_HOLD")
        if start - previous < timedelta(seconds=MIN_INTERVAL_SECONDS):
            raise ValueError("TPAC_R4_ENGINEERING_MIN_INTERVAL_HOLD")



def validate_durable_source_attempt(*, now: datetime, ledger: dict,
                                    lease: dict, source_host: str = SOURCE_HOST) -> None:
    """Fail-closed LIVE preflight over independently fetched durable records.

    This function does not fetch/claim a lease, authenticate a provider or
    authorize GET. The executor must atomically acquire the host-wide lease
    and persist a new attempt BEFORE any network I/O. An empty history is
    valid only when a trusted ledger explicitly attests first_attempt=True.
    """
    current = _aware(now, "START")
    if type(source_host) is not str or source_host != SOURCE_HOST:
        raise ValueError("TPAC_R4_SOURCE_HOST_MISMATCH_HOLD")
    if type(ledger) is not dict or type(lease) is not dict:
        raise ValueError("TPAC_R4_DURABLE_AUTHORITY_MISSING_HOLD")
    if ledger.get("source_host") != source_host or lease.get("source_host") != source_host:
        raise ValueError("TPAC_R4_CROSS_HOST_LEDGER_SCOPE_HOLD")
    if ledger.get("durable_provider_verified") is not True or lease.get("atomic_acquire_verified") is not True:
        raise ValueError("TPAC_R4_DURABLE_AUTHORITY_UNVERIFIED_HOLD")
    if lease.get("exclusive") is not True or lease.get("fencing_token") in (None, ""):
        raise ValueError("TPAC_R4_LEASE_NOT_EXCLUSIVE_HOLD")
    if lease.get("owner_run_id") in (None, "") or lease.get("owner_run_id") != ledger.get("owner_run_id"):
        raise ValueError("TPAC_R4_LEASE_OWNER_MISMATCH_HOLD")
    # The durable write-ahead request receipt must be bound to the exact
    # atomic lease generation; a prior runner's ledger is never authority.
    if (type(lease.get("fencing_token")) is not str
            or type(ledger.get("fencing_token")) is not str
            or ledger["fencing_token"] != lease["fencing_token"]):
        raise ValueError("TPAC_R4_LEDGER_LEASE_FENCING_MISMATCH_HOLD")
    written = ledger.get("attempt_written_at")
    if type(written) is not datetime or _aware(written, "ATTEMPT_WRITTEN") > current:
        raise ValueError("TPAC_R4_ATTEMPT_WRITE_AHEAD_MISSING_HOLD")
    acquired = lease.get("acquired_at")
    if type(acquired) is not datetime or _aware(acquired, "LEASE_ACQUIRED") > current:
        raise ValueError("TPAC_R4_LEASE_TIME_INVALID_HOLD")
    if _aware(acquired, "LEASE_ACQUIRED") > written:
        raise ValueError("TPAC_R4_ATTEMPT_PRECEDES_LEASE_HOLD")
    if ledger.get("first_attempt") is True:
        if ledger.get("last_attempt_at") is not None:
            raise ValueError("TPAC_R4_FIRST_ATTEMPT_CONFLICT_HOLD")
    else:
        previous = ledger.get("last_attempt_at")
        if type(previous) is not datetime:
            raise ValueError("TPAC_R4_LAST_ATTEMPT_MISSING_HOLD")
        enforce_elapsed(current, previous)
    # Never return a live permission token: this is a structural preflight.
    return None



def reserve_durable_source_attempt(*, provider, now: datetime,
                                   run_id: str, source_host: str = SOURCE_HOST) -> dict:
    """Reserve a real source attempt before any GET; never grant live authority.

    The provider must independently implement cross-runner atomic acquisition,
    read-after-write durable receipts, and fencing. Any missing method, partial
    write, stale readback or provider failure is a hard HOLD. A consumed attempt
    is NEVER rolled back or retried automatically, including on crash.
    """
    current = _aware(now, "START")
    if source_host != SOURCE_HOST or type(run_id) is not str or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]{7,127}", run_id):
        raise ValueError("TPAC_R4_SOURCE_RUN_ID_HOLD")
    try:
        lease = provider.acquire_atomic(source_host=source_host, owner_run_id=run_id)
        if type(lease) is not dict:
            raise ValueError("TPAC_R4_PROVIDER_LEASE_SCHEMA_HOLD")
        history = provider.read_last_attempt(source_host=source_host)
        if type(history) is not dict or history.get("source_host") != source_host:
            raise ValueError("TPAC_R4_PROVIDER_HISTORY_UNVERIFIED_HOLD")
        if history.get("first_attempt") is True:
            if history.get("last_attempt_at") is not None:
                raise ValueError("TPAC_R4_FIRST_ATTEMPT_CONFLICT_HOLD")
        else:
            if type(history.get("last_attempt_at")) is not datetime:
                raise ValueError("TPAC_R4_LAST_ATTEMPT_MISSING_HOLD")
            enforce_elapsed(current, history["last_attempt_at"])
        # Persist before a single network request. Provider must implement
        # immutable fencing-bound write and independently verified readback.
        provider.write_attempt(source_host=source_host, owner_run_id=run_id,
                               fencing_token=lease["fencing_token"], attempted_at=current)
        ledger = provider.read_attempt(source_host=source_host, owner_run_id=run_id)
        if type(ledger) is not dict:
            raise ValueError("TPAC_R4_PROVIDER_WRITE_READBACK_MISSING_HOLD")
        if ledger.get("attempt_written_at") != current:
            raise ValueError("TPAC_R4_PROVIDER_WRITE_READBACK_MISMATCH_HOLD")
        validate_durable_source_attempt(now=current, ledger=ledger, lease=lease,
                                        source_host=source_host)
    except (ValueError, KeyError, TypeError):
        raise
    except Exception as exc:
        raise ValueError("TPAC_R4_PROVIDER_OPERATION_FAILED_HOLD") from exc
    # Deliberately NO live permission token. Executor remains fail-closed.
    return {"source_host": source_host, "owner_run_id": run_id,
            "attempt_reserved": True, "native_get_allowed": False,
            "decision": CLAIM_HOLD}


def stop_on_response(status: int) -> None:
    """No retry path exists. Codes other than HTTP 200 are fatal."""
    if type(status) is not int or status != 200:
        if status in STOP_HTTP:
            raise ValueError("TPAC_R4_HTTP_403_429_STOP_NO_RETRY_HOLD")
        raise ValueError("TPAC_R4_HTTP_NON_200_STOP_NO_RETRY_HOLD")


def review_two_catalog_plan(*, cycle_id: str, start_at: datetime,
                            previous_claim_at: datetime | None,
                            robots: bytes,
                            program_body: bytes, program_receipt: dict,
                            event_body: bytes, event_receipt: dict,
                            attempts: tuple[str, ...] = ()) -> dict:
    """Evaluate two source LISTs already supplied by a sealed OFFLINE fixture.

    A successful schema/robots/budget check is *not* a live fetch permit. The
    returned plan always carries immutable-Claim HOLD, not a source credential.
    """
    if type(cycle_id) is not str or not _CYCLE.fullmatch(cycle_id):
        raise ValueError("TPAC_R4_CYCLE_ID_HOLD")
    enforce_elapsed(start_at, previous_claim_at)
    if type(attempts) is not tuple or any(type(a) is not str for a in attempts):
        raise ValueError("TPAC_R4_ATTEMPT_LOG_SCHEMA_HOLD")
    if attempts:
        # No GET, regardless of error family; this pure function does not retry.
        raise ValueError("TPAC_R4_PRECONSUMED_REQUEST_BUDGET_HOLD")
    listed = {}
    for name, body, receipt in (
        ("program", program_body, program_receipt),
        ("event", event_body, event_receipt),
    ):
        listed[name] = discover_catalog(name, body, receipt, start_at)
    # Deterministic, bounded two-ID fairness: one from each catalog when both
    # supply at least one visible exact-origin official link; NEVER merge IDs.
    chosen = (
        listed["program"][sorted(listed["program"])[0]],
        listed["event"][sorted(listed["event"])[0]],
    )
    allowed = (CATALOGS["program"]["list_url"], CATALOGS["event"]["list_url"],
               chosen[0]["detail_url"], chosen[1]["detail_url"])
    robots_sha, gap = _verify_robots(robots, allowed)
    request_urls = (ROBOTS,) + allowed
    if len(request_urls) != MAX_REQUESTS or len(set(request_urls)) != MAX_REQUESTS:
        raise ValueError("TPAC_R4_TOTAL_REQUEST_BUDGET_OR_DUPLICATE_URL_HOLD")
    if tuple(x["identity"] for x in chosen)[0] == chosen[1]["identity"]:
        raise ValueError("TPAC_R4_CROSS_CATALOG_IDENTITY_COLLISION_HOLD")
    return {
        "kind": KIND,
        "cycle_id": cycle_id,
        "decision": CLAIM_HOLD,
        "authorization": "OWNER_LIMITED_ISOLATED_SOURCE_ONLY",
        "immutable_cross_host_claim_verified": False,
        "native_get_allowed": False,
        "new_native_http_get": 0,
        "published": 0,
        "budget": asdict(RequestBudget()),
        "minimum_request_gap_seconds": gap,
        "robots_sha256": robots_sha,
        "source_lists": {k: len(v) for k, v in listed.items()},
        "request_urls_for_future_authorized_cycle": list(request_urls),
        "detail_source_identities": [x["identity"] for x in chosen],
        "detail_count": len(chosen),
        "first_failure": CLAIM_HOLD,
        "next_gate": "shared cross-host atomic source lease and durable last-attempt readback",
    }


def assert_no_untrusted_live_authority(result: dict) -> None:
    """Never interpret an offline plan as permission for native HTTP."""
    if type(result) is not dict or result.get("native_get_allowed") is not False:
        raise ValueError("TPAC_R4_UNVERIFIED_LIVE_AUTHORITY_HOLD")
    if result.get("immutable_cross_host_claim_verified") is not False:
        raise ValueError("TPAC_R4_UNVERIFIED_LIVE_AUTHORITY_HOLD")
    raise ValueError("TPAC_R4_IMMUTABLE_CLAIM_PROVIDER_MISSING_HOLD")
