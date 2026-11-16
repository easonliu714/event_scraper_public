"""RAW5 transport regression: no credentials, no source network, no LIVE grant."""
import unittest
from datetime import datetime, timedelta, timezone

from scripts.p30_tpac_raw5_github_attempt_provider import (
    GitHubRaw5AttemptProvider, HOST, REF_PREFIX, RECEIPT_REF_PREFIX,
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


class SharedGitHubCommitAPI:
    """Realistic Git REST object-type model: branch refs point to commits."""
    TREE = "c" * 40

    def __init__(self):
        import copy
        self.refs = {}
        self.blobs = {}
        self.commits = {ANCHOR: {
            "sha": ANCHOR, "tree": {"sha": self.TREE},
            "parents": [], "message": "main"}}
        self.calls = []
        self.tamper_blob = False

    def __call__(self, method, path, payload):
        import base64
        import hashlib
        import json
        self.calls.append((method, path))
        if method == "POST" and path.endswith("/git/blobs"):
            raw = base64.b64decode(payload["content"], validate=True)
            sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            self.blobs[sha] = payload["content"]
            return 201, {"sha": sha}, NOW
        if method == "POST" and path.endswith("/git/commits"):
            sha = hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            self.commits[sha] = {
                "sha": sha, "tree": {"sha": payload["tree"]},
                "parents": [{"sha": p} for p in payload["parents"]],
                "message": payload["message"]}
            return 201, {"sha": sha}, NOW
        if method == "GET" and "/git/commits/" in path:
            sha = path.rsplit("/", 1)[-1]
            if sha not in self.commits:
                return 404, {}, NOW
            return 200, self.commits[sha].copy(), NOW
        if method == "POST" and path.endswith("/git/refs"):
            ref = payload["ref"]
            # GitHub must never accept a non-commit as refs/heads.
            if payload["sha"] not in self.commits:
                return 422, {"message": "branch must reference commit"}, NOW
            if ref in self.refs:
                return 422, {"message": "Reference already exists"}, NOW
            self.refs[ref] = payload["sha"]
            return 201, {"ref": ref}, NOW
        if method == "GET" and "/git/ref/" in path:
            ref = "refs/" + path.split("/git/ref/", 1)[1]
            if ref not in self.refs:
                return 404, {}, NOW
            return 200, {"object": {"sha": self.refs[ref]}}, NOW
        if method == "GET" and "/git/blobs/" in path:
            sha = path.rsplit("/", 1)[-1]
            if sha not in self.blobs:
                return 404, {}, NOW
            content = self.blobs[sha]
            if self.tamper_blob:
                content = base64.b64encode(b'{"tampered":true}').decode()
            return 200, {"encoding": "base64", "content": content}, NOW
        raise AssertionError((method, path))


class ReceiptRoundTripTests(unittest.TestCase):
    def _written(self):
        api = SharedGitHubCommitAPI()
        writer = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        lease = writer.acquire_atomic(source_host=HOST, owner_run_id="runner-one-0001")
        writer.write_attempt(source_host=HOST, owner_run_id="runner-one-0001",
                             fencing_token=lease["fencing_token"], attempted_at=NOW)
        return api, writer

    def _fresh(self, writer):
        return dict(source_host=HOST, owner_run_id="runner-one-0001",
                    receipt_ref=writer._receipt_ref,
                    expected_sha=writer._receipt_sha,
                    expected_commit_sha=writer._receipt_commit_sha,
                    slot_ref=writer._ref, expected_at=NOW)

    def test_protected_commit_ref_and_full_byte_roundtrip(self):
        api, writer = self._written()
        self.assertTrue(writer._receipt_ref.startswith(RECEIPT_REF_PREFIX))
        self.assertNotEqual(writer._receipt_commit_sha, writer._receipt_sha)
        self.assertEqual(api.refs[writer._receipt_ref], writer._receipt_commit_sha)
        record = writer.read_attempt(source_host=HOST, owner_run_id="runner-one-0001")
        self.assertEqual(record["attempt_written_at"], NOW)
        self.assertFalse(record["durable_provider_verified"])
        reader = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        audit = reader.verify_receipt_from_fresh_executor(**self._fresh(writer))
        self.assertTrue(audit["receipt_verified"])
        self.assertFalse(audit["native_get_allowed"])
        # The transport explicitly forbids non-commit branch refs.
        self.assertTrue(all(sha in api.commits for sha in api.refs.values()))

    def test_ref_retarget_to_another_valid_commit_rejected(self):
        api, writer = self._written()
        ref = writer._receipt_ref
        api.refs[ref] = ANCHOR
        with self.assertRaisesRegex(ValueError, "RECEIPT_REF_READBACK_HOLD"):
            writer.read_attempt(source_host=HOST, owner_run_id="runner-one-0001")
        reader = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        with self.assertRaisesRegex(ValueError, "FRESH_RECEIPT_REF_HOLD"):
            reader.verify_receipt_from_fresh_executor(**self._fresh(writer))

    def test_commit_parent_tree_and_message_tamper_rejected(self):
        api, writer = self._written()
        commit = api.commits[writer._receipt_commit_sha]
        saved = dict(commit)
        for replacement in (
            {"parents": [{"sha": "f" * 40}]},
            {"tree": {"sha": "f" * 40}},
            {"message": "RAW5_ATTEMPT_V1_BLOB " + "f" * 40},
        ):
            commit.update(replacement)
            with self.subTest(replacement=replacement), self.assertRaisesRegex(
                    ValueError, "RECEIPT_COMMIT_BINDING_HOLD|RECEIPT_ANCHOR_TREE_HOLD"):
                writer.read_attempt(source_host=HOST, owner_run_id="runner-one-0001")
            commit.clear()
            commit.update(saved)

    def test_blob_bytes_substitution_is_detected(self):
        api, writer = self._written()
        api.tamper_blob = True
        with self.assertRaisesRegex(ValueError, "RECEIPT_GIT_BLOB_SHA_MISMATCH_HOLD"):
            writer.read_attempt(source_host=HOST, owner_run_id="runner-one-0001")

    def test_foreign_or_unprotected_receipt_ref_rejected_before_rest(self):
        api, writer = self._written()
        reader = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        before = len(api.calls)
        for change in (
            {"receipt_ref": "refs/heads/raw5-receipts/" + writer._ref.split("/")[-1]},
            {"receipt_ref": "refs/heads/other"},
            {"receipt_ref": writer._receipt_ref + "-foreign"},
            {"slot_ref": REF_PREFIX + "../bad"},
            {"owner_run_id": "runner-two-0002"},
        ):
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "FRESH_RECEIPT_SCOPE_HOLD|RECEIPT_REF_SCOPE_HOLD"):
                reader.verify_receipt_from_fresh_executor(**{**self._fresh(writer), **change})
        self.assertEqual(len(api.calls), before)

    def test_no_claim_is_not_a_live_authority(self):
        api = SharedGitHubCommitAPI()
        reader = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        with self.assertRaisesRegex(ValueError, "NO_LEASE_HOLD"):
            reader.read_last_attempt(source_host=HOST)
        api, writer = self._written()
        with self.assertRaisesRegex(ValueError, "DURABLE_LAST_ATTEMPT_UNAVAILABLE_HOLD"):
            writer.read_last_attempt(source_host=HOST)
        with self.assertRaisesRegex(ValueError, "PROVIDER_ACQUIRED_LEASE_INVALID_HOLD"):
            reserve_durable_source_attempt(
                provider=GitHubRaw5AttemptProvider(SharedGitHubCommitAPI(), ANCHOR, NOW),
                now=NOW, run_id="runner-one-0001")
        self.assertFalse(writer.read_attempt(source_host=HOST,
                                             owner_run_id="runner-one-0001")["durable_provider_verified"])


if __name__ == "__main__":
    unittest.main()
