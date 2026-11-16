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
        with self.assertRaisesRegex(ValueError, "RECEIPT_SCOPE_OR_FENCE_HOLD"):
            p.write_attempt(source_host=HOST, owner_run_id="runner-one-0001", fencing_token="wrong", attempted_at=NOW)
        with self.assertRaisesRegex(ValueError, "RECEIPT_READ_SCOPE_HOLD"):
            p.read_attempt(source_host=HOST, owner_run_id="runner-one-0001")


class ReceiptRoundTripTests(unittest.TestCase):
    def test_write_ahead_independent_ref_blob_readback_and_tamper_hold(self):
        import base64
        import hashlib
        import json
        class ReceiptAPI:
            def __init__(self):
                self.refs = {}
                self.blobs = {}
                self.tamper = False
            def __call__(self, method, path, payload):
                if method == "POST" and path.endswith("/git/blobs"):
                    raw = base64.b64decode(payload["content"])
                    sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
                    self.blobs[sha] = payload["content"]
                    return 201, {"sha": sha}, NOW
                if method == "POST" and path.endswith("/git/refs"):
                    ref = payload["ref"]
                    if ref in self.refs:
                        return 422, {}, NOW
                    self.refs[ref] = payload["sha"]
                    return 201, {}, NOW
                if method == "GET" and "/git/ref/" in path:
                    ref = "refs/" + path.split("/git/ref/", 1)[1]
                    return 200, {"object": {"sha": self.refs[ref]}}, NOW
                if method == "GET" and "/git/blobs/" in path:
                    sha = path.rsplit("/", 1)[-1]
                    content = self.blobs[sha]
                    if self.tamper:
                        content = base64.b64encode(b'{"tampered":true}').decode()
                    return 200, {"encoding": "base64", "content": content}, NOW
                raise AssertionError((method, path))
        api = ReceiptAPI()
        p = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        lease = p.acquire_atomic(source_host=HOST, owner_run_id="runner-one-0001")
        p.write_attempt(source_host=HOST, owner_run_id="runner-one-0001",
                        fencing_token=lease["fencing_token"], attempted_at=NOW)
        record = p.read_attempt(source_host=HOST, owner_run_id="runner-one-0001")
        self.assertEqual(record["attempt_written_at"], NOW)
        self.assertFalse(record["durable_provider_verified"])
        api.tamper = True
        with self.assertRaisesRegex(ValueError, "RECEIPT_GIT_BLOB_SHA_MISMATCH_HOLD"):
            p.read_attempt(source_host=HOST, owner_run_id="runner-one-0001")

    def test_receipt_rejects_wrong_fence_before_write(self):
        api = FakeGitHub()
        p = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        p.acquire_atomic(source_host=HOST, owner_run_id="runner-one-0001")
        with self.assertRaisesRegex(ValueError, "RECEIPT_SCOPE_OR_FENCE_HOLD"):
            p.write_attempt(source_host=HOST, owner_run_id="runner-one-0001",
                            fencing_token="wrong", attempted_at=NOW)
        self.assertEqual(len(api.calls), 1)


if __name__ == "__main__":
    unittest.main()
