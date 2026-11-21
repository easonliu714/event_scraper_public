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
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib import robotparser
import fcntl
import os
import secrets
import sqlite3
from pathlib import Path

from scripts.p30_tpac_catalog_topology import CATALOGS, discover_catalog

ROBOTS = "https://tpac.org.taipei/robots.txt"
AGENT = "EventRadarTaiwan-SourceAudit/1.0"
SOURCE_HOST = "tpac.org.taipei"
MIN_INTERVAL_SECONDS = 6 * 60 * 60  # Owner TPAC-R4 host-wide minimum; never hourly
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
    """Enforce Owner six-hour host-wide minimum using a durable UTC ledger."""
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
        # Fail closed BEFORE durable history or attempt write: an untrusted
        # provider lease must never consume a request budget or cross-host slot.
        if (lease.get("source_host") != source_host
                or lease.get("atomic_acquire_verified") is not True
                or lease.get("exclusive") is not True
                or type(lease.get("fencing_token")) is not str
                or not lease["fencing_token"]
                or lease.get("owner_run_id") != run_id
                or type(lease.get("acquired_at")) is not datetime):
            raise ValueError("TPAC_R4_PROVIDER_ACQUIRED_LEASE_INVALID_HOLD")
        acquired = _aware(lease["acquired_at"], "LEASE_ACQUIRED")
        if acquired > current:
            raise ValueError("TPAC_R4_LEASE_TIME_INVALID_HOLD")
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
        # A six-hour request ledger is not a durable 403/429 host barrier.
        # Read the *host-wide* response state after acquiring the same-source
        # lease and before consuming a new attempt. Both /program and /event
        # must observe the same most recent host attempt; stale/per-ID-only
        # state, missing provider support, and 403 policy HOLD fail closed.
        # This is only a review preflight; it never produces GET authority.
        if history.get("first_attempt") is not True:
            # Missing optional provider capability is a typed fail-closed HOLD,
            # not a leaked TypeError or a reason to skip host cooldown.
            read_host_cooldown = getattr(provider, "read_host_cooldown", None)
            if not callable(read_host_cooldown):
                raise ValueError("TPAC_R4_HOST_COOLDOWN_PROVIDER_MISSING_HOLD")
            host_state = read_host_cooldown(source_host=source_host)
            if (type(host_state) is not dict
                    or host_state.get("scope") != "HOST_WIDE"
                    or type(host_state.get("last_attempt_at")) is not datetime
                    or _aware(host_state["last_attempt_at"], "COOLDOWN_ATTEMPT")
                       != _aware(history["last_attempt_at"], "PREVIOUS_CLAIM")):
                raise ValueError("TPAC_R4_HOST_COOLDOWN_HISTORY_BINDING_HOLD")
            eligibility = evaluate_source_cooldown(
                now=current, state=host_state, source_host=source_host)
            # Active cooldown remains a cooldown HOLD; only an expired 429
            # advances to the separate probe-authorization HOLD. Neither
            # decision consumes an attempt or permits source network I/O.
            if (eligibility.get("decision") != "REVIEW_ONLY"
                    or eligibility.get("eligible_for_review") is not True):
                raise ValueError("TPAC_R4_HOST_COOLDOWN_ACTIVE_OR_POLICY_HOLD")
            if host_state.get("last_http_status") == 429:
                raise ValueError("TPAC_R4_429_PROBE_AUTHORIZATION_REQUIRED_HOLD")
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

def evaluate_source_cooldown(*, now: datetime, state: dict,
                             source_host: str = SOURCE_HOST) -> dict:
    """Pure, fail-closed durable cooldown decision; NEVER a GET authorization.

    State is a provider-verified readback, not an in-memory scheduling hint.
    A missing or malformed record is HOLD. Expiry only permits policy review.
    """
    current = _aware(now, "COOLDOWN_NOW")
    if type(state) is not dict or state.get("source_host") != source_host or source_host != SOURCE_HOST:
        raise ValueError("TPAC_R4_COOLDOWN_SOURCE_SCOPE_HOLD")
    if state.get("durable_readback_verified") is not True:
        raise ValueError("TPAC_R4_COOLDOWN_DURABLE_READBACK_HOLD")
    identity = state.get("source_identity")
    if type(identity) is not str or not re.fullmatch(r"tpac:(program|event):[0-9]+", identity):
        raise ValueError("TPAC_R4_COOLDOWN_IDENTITY_HOLD")
    last = state.get("last_attempt_at")
    if type(last) is not datetime:
        raise ValueError("TPAC_R4_COOLDOWN_ATTEMPT_MISSING_HOLD")
    last = _aware(last, "COOLDOWN_ATTEMPT")
    if last > current:
        raise ValueError("TPAC_R4_COOLDOWN_CLOCK_ROLLBACK_HOLD")
    status = state.get("last_http_status")
    failure = state.get("last_failure_class")
    count = state.get("consecutive_failures")
    if type(count) is not int or count < 0 or type(status) is not int:
        raise ValueError("TPAC_R4_COOLDOWN_SCHEMA_HOLD")
    until = state.get("cooldown_until")
    if type(until) is not datetime:
        raise ValueError("TPAC_R4_COOLDOWN_DEADLINE_MISSING_HOLD")
    until = _aware(until, "COOLDOWN_UNTIL")
    if until < last:
        raise ValueError("TPAC_R4_COOLDOWN_DEADLINE_INVALID_HOLD")
    minimum = last + timedelta(seconds=MIN_INTERVAL_SECONDS)
    if status == 429 and failure == "RATE_LIMIT":
        minimum = last + timedelta(hours=min(24 * (2 ** min(max(count - 1, 0), 3)), 168))
    elif status == 403 and failure == "ACCESS_DENIED":
        minimum = last + timedelta(hours=72)
    elif status >= 500 and status <= 599 and failure == "TRANSIENT":
        minimum = last + timedelta(hours=12)
    elif status == 200 and failure == "NONE" and count == 0:
        pass
    else:
        return {"decision": "SOURCE_ACCESS_HOLD", "eligible_for_review": False,
                "native_get_allowed": False}
    # A trusted Retry-After must extend, never shorten, the host cooldown.
    # Malformed headers fail closed rather than silently permitting an early probe.
    retry_after = state.get("retry_after_header")
    if retry_after is not None:
        if type(retry_after) is not str or not retry_after or len(retry_after) > 128:
            raise ValueError("TPAC_R4_RETRY_AFTER_INVALID_HOLD")
        if re.fullmatch(r"[0-9]+", retry_after):
            seconds = int(retry_after)
            if seconds > 365 * 86400:
                raise ValueError("TPAC_R4_RETRY_AFTER_INVALID_HOLD")
            retry_deadline = last + timedelta(seconds=seconds)
        else:
            try:
                parsed = parsedate_to_datetime(retry_after)
                retry_deadline = _aware(parsed, "RETRY_AFTER")
            except (ValueError, TypeError, OverflowError, IndexError) as exc:
                raise ValueError("TPAC_R4_RETRY_AFTER_INVALID_HOLD") from exc
        minimum = max(minimum, retry_deadline)
    if until < minimum:
        raise ValueError("TPAC_R4_COOLDOWN_MINIMUM_VIOLATION_HOLD")
    if status == 403:
        return {"decision": "SOURCE_ACCESS_HOLD_POLICY_REVIEW_REQUIRED",
                "eligible_for_review": current >= until, "native_get_allowed": False}
    return {"decision": "COOLDOWN_ACTIVE" if current < until else "REVIEW_ONLY",
            "eligible_for_review": current >= until, "native_get_allowed": False}



class IsolatedSingleExecutorLedger:
    """Local POSIX single-actor, crash-durable SOURCE health prototype.

    This is an OFFLINE candidate, not a cross-host provider or HTTP executor.
    A held kernel file lock is mandatory in addition to SQLite transactions.
    PENDING survives process death and is never inferred to mean HTTP success.
    No method issues requests or returns live/source-publication authorization.
    """

    def __init__(self, database_path):
        path = Path(database_path).absolute()
        if (os.name != "posix" or path.parent.is_symlink()
                or path.is_symlink() or Path(str(path) + ".lock").is_symlink()
                or not path.parent.is_dir()):
            raise ValueError("TPAC_LEDGER_UNSAFE_LOCAL_PATH_HOLD")
        self._lock_fd = None
        self._conn = None
        try:
            self._lock_fd = os.open(str(path) + ".lock",
                                    os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("TPAC_LEDGER_SECOND_EXECUTOR_HOLD") from exc
            self._conn = sqlite3.connect(str(path), timeout=0,
                                         isolation_level=None)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=FULL")
            self._conn.execute("PRAGMA busy_timeout=0")
            self._conn.execute("""CREATE TABLE IF NOT EXISTS source_attempts (
                id INTEGER PRIMARY KEY,
                source_host TEXT NOT NULL,
                source_identity TEXT NOT NULL,
                owner_run_id TEXT NOT NULL UNIQUE,
                fencing_token TEXT NOT NULL,
                attempted_at TEXT NOT NULL,
                response_at TEXT,
                outcome TEXT NOT NULL CHECK(outcome IN ('PENDING','COMMITTED')),
                last_http_status INTEGER,
                failure_class TEXT,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                retry_after_header TEXT,
                cooldown_until TEXT,
                body_sha256 TEXT,
                source_url TEXT,
                source_receipt_sha256 TEXT,
                source_observed_at TEXT
            )""")
            # Migrate isolated local ledgers; preexisting unbound 200s HOLD.
            columns = {entry[1] for entry in self._conn.execute(
                "PRAGMA table_info(source_attempts)")}
            for column in ("source_url", "source_receipt_sha256", "source_observed_at"):
                if column not in columns:
                    self._conn.execute("ALTER TABLE source_attempts ADD COLUMN " + column + " TEXT")
            if self._conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("TPAC_LEDGER_SQLITE_INTEGRITY_HOLD")
        except BaseException:
            self.close()
            raise

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        if self._lock_fd is not None:
            fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            os.close(self._lock_fd)
            self._lock_fd = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _latest(self, source_host):
        return self._conn.execute(
            """SELECT owner_run_id,fencing_token,attempted_at,outcome,
                      last_http_status,failure_class,consecutive_failures,
                      retry_after_header,cooldown_until,source_identity,
                       source_url,source_receipt_sha256,source_observed_at,body_sha256
               FROM source_attempts WHERE source_host=?
               ORDER BY id DESC LIMIT 1""", (source_host,)).fetchone()

    @staticmethod
    def _identity(source_host, source_identity):
        if (type(source_host) is not str
                or re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,120}", source_host) is None
                or type(source_identity) is not str
                or re.fullmatch(r"[a-z][a-z0-9_-]{1,30}:(?:program|event):(?:list|[1-9][0-9]{0,9})",
                                source_identity) is None):
            raise ValueError("TPAC_LEDGER_IDENTITY_SCHEMA_HOLD")
        if (source_host == SOURCE_HOST) != source_identity.startswith("tpac:"):
            raise ValueError("TPAC_LEDGER_IDENTITY_HOST_MISMATCH_HOLD")

    def begin_attempt(self, *, source_host, source_identity, owner_run_id, now):
        """Atomically reserve OFFLINE attempt; never grants native GET."""
        self._identity(source_host, source_identity)
        if (type(owner_run_id) is not str
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{7,127}",
                                owner_run_id) is None):
            raise ValueError("TPAC_LEDGER_RUN_ID_HOLD")
        current = _aware(now, "LEDGER_BEGIN")
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            last = self._latest(source_host)
            if last is not None:
                previous = _aware(datetime.fromisoformat(last[2]), "LEDGER_PREVIOUS")
                if current < previous:
                    raise ValueError("TPAC_LEDGER_CLOCK_ROLLBACK_HOLD")
                if last[3] == "PENDING":
                    raise ValueError("TPAC_LEDGER_UNCERTAIN_CRASH_OUTCOME_HOLD")
                if last[4] == 200 and not all(last[i] for i in (10, 11, 12, 13)):
                    raise ValueError("TPAC_LEDGER_LEGACY_UNBOUND_200_HOLD")
                if current - previous < timedelta(seconds=MIN_INTERVAL_SECONDS):
                    raise ValueError("TPAC_LEDGER_SIX_HOUR_HOST_HOLD")
                if last[4] in (403, 429):
                    raise ValueError("TPAC_LEDGER_POLICY_OR_PROBE_REVIEW_HOLD")
                until = _aware(datetime.fromisoformat(last[8]), "LEDGER_COOLDOWN")
                if current < until:
                    raise ValueError("TPAC_LEDGER_HOST_COOLDOWN_ACTIVE_HOLD")
            fence = secrets.token_hex(32)
            self._conn.execute(
                """INSERT INTO source_attempts
                   (source_host,source_identity,owner_run_id,fencing_token,
                    attempted_at,outcome)
                   VALUES(?,?,?,?,?,'PENDING')""",
                (source_host, source_identity, owner_run_id, fence,
                 current.isoformat()))
            self._conn.commit()
        except BaseException:
            self._conn.rollback()
            raise
        return {"owner_run_id": owner_run_id, "fencing_token": fence,
                "source_host": source_host, "decision": "ISOLATED_PENDING_ONLY",
                "native_get_allowed": False}

    def commit_response(self, *, source_host, owner_run_id, fencing_token,
                        status, observed_at, retry_after_header=None,
                        raw_body=None, source_receipt=None):
        """Fenced response write; a bare HTTP-200/boolean cannot mark success."""
        observed = _aware(observed_at, "LEDGER_RESPONSE")
        if type(status) is not int or not 100 <= status <= 599:
            raise ValueError("TPAC_LEDGER_HTTP_STATUS_HOLD")
        if retry_after_header is not None:
            if (type(retry_after_header) is not str
                    or not 1 <= len(retry_after_header) <= 128):
                raise ValueError("TPAC_LEDGER_RETRY_AFTER_HOLD")
            if re.fullmatch(r"[0-9]+", retry_after_header):
                delta = int(retry_after_header)
                if delta > 365 * 86400:
                    raise ValueError("TPAC_LEDGER_RETRY_AFTER_HOLD")
                retry_deadline = observed + timedelta(seconds=delta)
            else:
                try:
                    retry_deadline = _aware(parsedate_to_datetime(retry_after_header),
                                            "LEDGER_RETRY_AFTER")
                except (ValueError, TypeError, OverflowError, IndexError) as exc:
                    raise ValueError("TPAC_LEDGER_RETRY_AFTER_HOLD") from exc
        else:
            retry_deadline = observed
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            last = self._latest(source_host)
            if (last is None or last[0] != owner_run_id
                    or type(fencing_token) is not str
                    or last[1] != fencing_token or last[3] != "PENDING"):
                raise ValueError("TPAC_LEDGER_FENCING_OR_PENDING_HOLD")
            begun = _aware(datetime.fromisoformat(last[2]), "LEDGER_BEGIN")
            if observed < begun:
                raise ValueError("TPAC_LEDGER_RESPONSE_BEFORE_ATTEMPT_HOLD")
            count = 0
            digest = None
            source_url = None
            source_receipt_sha256 = None
            source_observed_at = None
            if status == 200:
                if (source_host != SOURCE_HOST or raw_body is None
                        or type(source_receipt) is not dict
                        or last[9] not in ("tpac:program:list", "tpac:event:list")):
                    raise ValueError("TPAC_LEDGER_200_TRUSTED_PARSER_RECEIPT_HOLD")
                # Bind parser evidence to this exact attempt/host/namespace,
                # URL, response time and fencing generation. These fields
                # are local provenance only, never LIVE GET authorization.
                kind = last[9].split(":")[1]
                from scripts.p30_tpac_catalog_topology import CATALOGS, discover_catalog
                expected_url = CATALOGS[kind]["list_url"]
                evidence_fields = {
                    "ledger_evidence_class": "ISOLATED_OFFLINE_SOURCE_RECEIPT",
                    "ledger_owner_run_id": owner_run_id,
                    "ledger_fencing_token": fencing_token,
                    "ledger_source_host": source_host,
                    "ledger_source_identity": last[9],
                    "ledger_source_url": expected_url,
                    "ledger_observed_at": observed.isoformat(),
                }
                if (type(raw_body) is not bytes
                        or any(source_receipt.get(k) != v for k, v in evidence_fields.items())
                        or source_receipt.get("final_url") != expected_url
                        or source_receipt.get("observed_at") != observed.isoformat()):
                    raise ValueError("TPAC_LEDGER_PARSER_RECEIPT_BINDING_HOLD")
                discover_catalog(kind, raw_body, source_receipt, observed)
                digest = hashlib.sha256(raw_body).hexdigest()
                source_url = expected_url
                source_receipt_sha256 = hashlib.sha256(json.dumps(
                    source_receipt, sort_keys=True, ensure_ascii=False,
                    separators=(",", ":")).encode("utf-8")).hexdigest()
                source_observed_at = observed.isoformat()
                minimum = observed + timedelta(seconds=MIN_INTERVAL_SECONDS)
                failure = "NONE"
            elif status == 429:
                earlier = self._conn.execute(
                    """SELECT last_http_status,consecutive_failures
                       FROM source_attempts WHERE source_host=? AND outcome='COMMITTED'
                       ORDER BY id DESC LIMIT 1""", (source_host,)).fetchone()
                count = (earlier[1] + 1) if earlier and earlier[0] == 429 else 1
                minimum = observed + timedelta(hours=min(24 * (2 ** min(count-1, 3)), 168))
                failure = "RATE_LIMIT"
            elif status == 403:
                minimum = observed + timedelta(hours=72)
                failure = "ACCESS_DENIED"
            elif 500 <= status <= 599:
                minimum = observed + timedelta(hours=12)
                failure = "TRANSIENT"
            else:
                minimum = observed + timedelta(days=7)
                failure = "PERMANENT"
            deadline = max(minimum, retry_deadline)
            self._conn.execute(
                """UPDATE source_attempts SET outcome='COMMITTED',
                   response_at=?,last_http_status=?,failure_class=?,
                   consecutive_failures=?,retry_after_header=?,
                   cooldown_until=?,body_sha256=?,source_url=?,
                   source_receipt_sha256=?,source_observed_at=?
                   WHERE owner_run_id=? AND fencing_token=? AND outcome='PENDING'""",
                (observed.isoformat(), status, failure, count,
                 retry_after_header, deadline.isoformat(), digest,
                 source_url, source_receipt_sha256, source_observed_at,
                 owner_run_id, fencing_token))
            self._conn.commit()
        except BaseException:
            self._conn.rollback()
            raise
        return {"source_host": source_host, "decision": "ISOLATED_RESPONSE_COMMITTED",
                "last_http_status": status, "cooldown_until": deadline,
                "native_get_allowed": False}

    def read_host_cooldown(self, *, source_host):
        """Durable readback; PENDING is an irreversible unknown-outcome HOLD."""
        last = self._latest(source_host)
        if last is None or last[3] == "PENDING":
            raise ValueError("TPAC_LEDGER_MISSING_OR_PENDING_RESPONSE_HOLD")
        return {"scope": "HOST_WIDE", "source_host": source_host,
                "source_identity": last[9],
                "durable_readback_verified": True,
                "evidence_class": "ISOLATED_LOCAL_PROCESS_ONLY",
                "last_attempt_at": datetime.fromisoformat(last[2]),
                "last_http_status": last[4], "last_failure_class": last[5],
                "consecutive_failures": last[6], "retry_after_header": last[7],
                "cooldown_until": datetime.fromisoformat(last[8]),
                "native_get_allowed": False}

    def read_last_bound_source(self, *, source_host):
        """Independent local SQLite provenance readback; never GET authority."""
        last = self._latest(source_host)
        if (last is None or last[3] != "COMMITTED" or last[4] != 200
                or not all(last[i] for i in (10, 11, 12, 13))):
            raise ValueError("TPAC_LEDGER_BOUND_SOURCE_NOT_AVAILABLE_HOLD")
        return {"source_host": source_host, "source_identity": last[9],
                "source_url": last[10], "source_receipt_sha256": last[11],
                "source_observed_at": datetime.fromisoformat(last[12]),
                "body_sha256": last[13],
                "evidence_class": "ISOLATED_LOCAL_PROVENANCE_ONLY",
                "native_get_allowed": False}
