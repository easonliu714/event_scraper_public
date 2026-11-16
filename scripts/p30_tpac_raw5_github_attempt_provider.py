"""RAW5 isolated GitHub-backed attempt provider candidate. NO source GET authority.

This adapter intentionally does not claim that GitHub refs are immutable, nor
that a single collision proves cross-runner exclusivity. It stores immutable-
intent receipts for independent review and always fails closed for LIVE GET.
Transport is injected to permit exact HTTP response tests without credentials.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

REPO = "easonliu714/event_scraper_public"
HOST = "tpac.org.taipei"
PREFIX = "/repos/" + REPO
REF_PREFIX = "refs/heads/source-claims/raw5-tpac-"
RUN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{7,127}\Z")


def _utc(value):
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("RAW5_UTC_REQUIRED_HOLD")
    return value.astimezone(timezone.utc)


class GitHubRaw5AttemptProvider:
    """Candidate transport for #243 reservation interface; never LIVE authority.

    GitHub refs are mutable/deletable unless a verified external Ruleset
    prevents it. This class deliberately cannot attest that protection.
    """

    def __init__(self, transport, anchor_sha, observed_at):
        if not callable(transport) or not re.fullmatch(r"[0-9a-f]{40}", anchor_sha):
            raise ValueError("RAW5_TRANSPORT_OR_ANCHOR_HOLD")
        self._request = transport
        self._anchor = anchor_sha
        self._now = _utc(observed_at)
        self._run = None
        self._ref = None

    def _call(self, method, path, payload=None):
        status, body, server_at = self._request(method, PREFIX + path, payload)
        if type(status) is not int or type(body) is not dict:
            raise ValueError("RAW5_REST_RESPONSE_SCHEMA_HOLD")
        if abs((_utc(server_at) - self._now).total_seconds()) > 120:
            raise ValueError("RAW5_REST_SERVER_CLOCK_HOLD")
        return status, body

    def acquire_atomic(self, *, source_host, owner_run_id):
        if source_host != HOST or type(owner_run_id) is not str or not RUN_RE.fullmatch(owner_run_id):
            raise ValueError("RAW5_SCOPE_OR_RUN_HOLD")
        # The slot is deterministic across executors. A collision is a HOLD,
        # not proof of permanent exclusivity or a grant of network authority.
        slot = int(self._now.timestamp()) // 3600
        ref = REF_PREFIX + str(slot)
        status, _ = self._call("POST", "/git/refs", {"ref": ref, "sha": self._anchor})
        if status != 201:
            raise ValueError("RAW5_ATOMIC_SLOT_NOT_ACQUIRED_HOLD")
        self._run, self._ref = owner_run_id, ref
        # No 'atomic_acquire_verified=True': actual protection has not been
        # proven on two independent runners, and refs may be deleted.
        return {"source_host": HOST, "owner_run_id": owner_run_id,
                "exclusive": False, "atomic_acquire_verified": False,
                "fencing_token": hashlib.sha256(ref.encode()).hexdigest(),
                "acquired_at": self._now}

    def read_last_attempt(self, *, source_host):
        if source_host != HOST or self._ref is None:
            raise ValueError("RAW5_NO_LEASE_HOLD")
        # A ref collision alone cannot provide durable history, so fail
        # closed rather than inventing a first-attempt assertion.
        raise ValueError("RAW5_DURABLE_LAST_ATTEMPT_UNAVAILABLE_HOLD")

    def write_attempt(self, **kwargs):
        raise ValueError("RAW5_WRITE_AHEAD_RECEIPT_NOT_IMPLEMENTED_HOLD")

    def read_attempt(self, **kwargs):
        raise ValueError("RAW5_INDEPENDENT_RECEIPT_UNAVAILABLE_HOLD")
