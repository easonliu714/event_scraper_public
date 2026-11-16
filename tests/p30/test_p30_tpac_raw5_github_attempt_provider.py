"""RAW5 transport regression: no credentials, no source network, no LIVE grant."""
import unittest
from datetime import datetime, timedelta, timezone

from scripts.p30_tpac_raw5_github_attempt_provider import (
    GitHubRaw5AttemptProvider, HOST, REF_PREFIX,
)
from scripts.p30_tpac_r4_source_policy import reserve_durable_source_attempt

NOW = datetime(2026, 11, 16, 5, 55, tzinfo=timezone.utc)
ANCHOR = "a" * 40


class FakeGitHub:
    def __init__(self):
        self.refs = set()
        self.calls = []
        self.status = None
        self.server_time = NOW

    def __call__(self, method, path, payload):
        self.calls.append((method, path, payload))
        if method != "POST" or not path.endswith("/git/refs"):
            raise AssertionError("unexpected GitHub API")
        ref = payload["ref"]
        status = self.status if self.status is not None else (422 if ref in self.refs else 201)
        if status == 201:
            self.refs.add(ref)
        return status, {}, self.server_time


class Raw5ProviderTests(unittest.TestCase):
    def provider(self, transport):
        return GitHubRaw5AttemptProvider(transport, ANCHOR, NOW)

    def test_one_slot_one_winner_second_executor_denied(self):
        api = FakeGitHub()
        first = self.provider(api)
        lease = first.acquire_atomic(source_host=HOST, owner_run_id="runner-one-0001")
        self.assertFalse(lease["exclusive"])
        self.assertFalse(lease["atomic_acquire_verified"])
        self.assertEqual(len(api.refs), 1)
        self.assertTrue(next(iter(api.refs)).startswith(REF_PREFIX))
        second = self.provider(api)
        with self.assertRaisesRegex(ValueError, "ATOMIC_SLOT_NOT_ACQUIRED_HOLD"):
            second.acquire_atomic(source_host=HOST, owner_run_id="runner-two-0002")
        self.assertEqual(len(api.calls), 2)

    def test_reserve_never_reads_history_or_writes_unverified_lease(self):
        api = FakeGitHub()
        with self.assertRaisesRegex(ValueError, "PROVIDER_ACQUIRED_LEASE_INVALID_HOLD"):
            reserve_durable_source_attempt(
                provider=self.provider(api), now=NOW, run_id="runner-one-0001")
        self.assertEqual(len(api.calls), 1)

    def test_crash_restart_same_slot_does_not_retry_or_get(self):
        api = FakeGitHub()
        self.provider(api).acquire_atomic(source_host=HOST, owner_run_id="runner-one-0001")
        with self.assertRaisesRegex(ValueError, "ATOMIC_SLOT_NOT_ACQUIRED_HOLD"):
            self.provider(api).acquire_atomic(source_host=HOST, owner_run_id="runner-one-0001")
        self.assertEqual(len(api.refs), 1)

    def test_invalid_host_run_anchor_and_server_clock_hold(self):
        api = FakeGitHub()
        with self.assertRaisesRegex(ValueError, "TRANSPORT_OR_ANCHOR_HOLD"):
            GitHubRaw5AttemptProvider(api, "not-a-sha", NOW)
        p = self.provider(api)
        with self.assertRaisesRegex(ValueError, "SCOPE_OR_RUN_HOLD"):
            p.acquire_atomic(source_host="wrong.example", owner_run_id="runner-one-0001")
        with self.assertRaisesRegex(ValueError, "SCOPE_OR_RUN_HOLD"):
            p.acquire_atomic(source_host=HOST, owner_run_id="../bad")
        self.assertEqual(api.calls, [])
        api.server_time = NOW + timedelta(minutes=3)
        with self.assertRaisesRegex(ValueError, "REST_SERVER_CLOCK_HOLD"):
            p.acquire_atomic(source_host=HOST, owner_run_id="runner-one-0001")

    def test_durable_history_and_receipt_never_fabricated(self):
        api = FakeGitHub()
        p = self.provider(api)
        p.acquire_atomic(source_host=HOST, owner_run_id="runner-one-0001")
        with self.assertRaisesRegex(ValueError, "DURABLE_LAST_ATTEMPT_UNAVAILABLE_HOLD"):
            p.read_last_attempt(source_host=HOST)
        with self.assertRaisesRegex(ValueError, "WRITE_AHEAD_RECEIPT_NOT_IMPLEMENTED_HOLD"):
            p.write_attempt(source_host=HOST)
        with self.assertRaisesRegex(ValueError, "INDEPENDENT_RECEIPT_UNAVAILABLE_HOLD"):
            p.read_attempt(source_host=HOST)


if __name__ == "__main__":
    unittest.main()
