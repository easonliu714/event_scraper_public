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
        if method == "GET" and "/git/matching-refs/" in path:
            return 200, [], self.server_time
        if method == "GET" and "/git/ref/" in path:
            return 404, {}, self.server_time
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
        with self.assertRaisesRegex(ValueError, "FIRST_ATTEMPT_UNATTESTED_HOLD"):
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
        self.server_time = NOW

    def __call__(self, method, path, payload):
        import base64
        import hashlib
        import json
        self.calls.append((method, path))
        if method == "POST" and path.endswith("/git/blobs"):
            raw = base64.b64decode(payload["content"], validate=True)
            sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            self.blobs[sha] = payload["content"]
            return 201, {"sha": sha}, self.server_time
        if method == "POST" and path.endswith("/git/commits"):
            sha = hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            self.commits[sha] = {
                "sha": sha, "tree": {"sha": payload["tree"]},
                "parents": [{"sha": p} for p in payload["parents"]],
                "message": payload["message"]}
            return 201, {"sha": sha}, self.server_time
        if method == "GET" and "/git/commits/" in path:
            sha = path.rsplit("/", 1)[-1]
            if sha not in self.commits:
                return 404, {}, self.server_time
            return 200, self.commits[sha].copy(), self.server_time
        if method == "POST" and path.endswith("/git/refs"):
            ref = payload["ref"]
            # GitHub must never accept a non-commit as refs/heads.
            if payload["sha"] not in self.commits:
                return 422, {"message": "branch must reference commit"}, self.server_time
            if ref in self.refs:
                return 422, {"message": "Reference already exists"}, self.server_time
            self.refs[ref] = payload["sha"]
            return 201, {"ref": ref}, self.server_time
        if method == "GET" and "/git/matching-refs/" in path:
            prefix = "refs/" + path.split("/git/matching-refs/", 1)[1]
            matches = [
                {"ref": name, "object": {"type": "commit", "sha": sha}}
                for name, sha in sorted(self.refs.items())
                if name.startswith(prefix)
            ]
            return 200, matches, self.server_time
        if method == "GET" and "/git/ref/" in path:
            ref = "refs/" + path.split("/git/ref/", 1)[1]
            if ref not in self.refs:
                return 404, {}, self.server_time
            return 200, {"object": {"sha": self.refs[ref]}}, self.server_time
        if method == "GET" and "/git/blobs/" in path:
            sha = path.rsplit("/", 1)[-1]
            if sha not in self.blobs:
                return 404, {}, self.server_time
            content = self.blobs[sha]
            if self.tamper_blob:
                content = base64.b64encode(b'{"tampered":true}').decode()
            return 200, {"encoding": "base64", "content": content}, self.server_time
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
        self.assertNotIn("/", writer._receipt_ref[len("refs/heads/source-claims/"):])
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
            {"receipt_ref": "refs/heads/source-claims/raw5-receipts/nested"},
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
        with self.assertRaisesRegex(ValueError, "FIRST_ATTEMPT_UNATTESTED_HOLD"):
            writer.read_last_attempt(source_host=HOST)
        with self.assertRaisesRegex(ValueError, "PROVIDER_ACQUIRED_LEASE_INVALID_HOLD"):
            reserve_durable_source_attempt(
                provider=GitHubRaw5AttemptProvider(SharedGitHubCommitAPI(), ANCHOR, NOW),
                now=NOW, run_id="runner-one-0001")
        self.assertFalse(writer.read_attempt(source_host=HOST,
                                             owner_run_id="runner-one-0001")["durable_provider_verified"])


class HostHistoryRecoveryTests(unittest.TestCase):
    """Host-wide elapsed recovery from actual remote ref/commit/blob records."""

    def _previous_and_current(self, age_minutes=61):
        prior = NOW - timedelta(minutes=age_minutes)
        assert int(prior.timestamp()) // 3600 == int(NOW.timestamp()) // 3600 - 1
        api = SharedGitHubCommitAPI()
        api.server_time = prior
        writer = GitHubRaw5AttemptProvider(api, ANCHOR, prior)
        old = writer.acquire_atomic(source_host=HOST, owner_run_id="prior-run-0001")
        writer.write_attempt(source_host=HOST, owner_run_id="prior-run-0001",
                             fencing_token=old["fencing_token"], attempted_at=prior)
        api.server_time = NOW
        reader = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        current = reader.acquire_atomic(source_host=HOST, owner_run_id="new-run-0002")
        self.assertFalse(current["exclusive"])
        return api, writer, reader, prior

    def test_previous_protected_receipt_recovers_real_utc_for_next_runner(self):
        from scripts.p30_tpac_r4_source_policy import enforce_elapsed
        api, writer, reader, prior = self._previous_and_current(age_minutes=61)
        history = reader.read_last_attempt(source_host=HOST)
        self.assertFalse(history["first_attempt"])
        self.assertEqual(history["last_attempt_at"], prior)
        self.assertTrue(history["history_record_independently_verified"])
        self.assertFalse(history["native_get_allowed"])
        self.assertEqual(history["history_receipt_ref"], writer._receipt_ref)
        self.assertEqual(history["history_receipt_commit_sha"], writer._receipt_commit_sha)
        self.assertEqual(history["history_receipt_blob_sha"], writer._receipt_sha)
        enforce_elapsed(NOW, history["last_attempt_at"])

    def test_actual_utc_spacing_blocks_even_when_hour_slot_changes(self):
        from scripts.p30_tpac_r4_source_policy import enforce_elapsed
        api, writer, reader, prior = self._previous_and_current(age_minutes=56)
        history = reader.read_last_attempt(source_host=HOST)
        self.assertEqual(history["last_attempt_at"], prior)
        with self.assertRaisesRegex(ValueError, "ENGINEERING_MIN_INTERVAL_HOLD"):
            enforce_elapsed(NOW, history["last_attempt_at"])

    def test_prior_claim_without_receipt_is_not_clean_history(self):
        api = SharedGitHubCommitAPI()
        past = NOW - timedelta(minutes=61)
        api.server_time = past
        orphan = GitHubRaw5AttemptProvider(api, ANCHOR, past)
        orphan.acquire_atomic(source_host=HOST, owner_run_id="prior-run-0001")
        api.server_time = NOW
        current = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        current.acquire_atomic(source_host=HOST, owner_run_id="new-run-0002")
        with self.assertRaisesRegex(ValueError, "PREVIOUS_LEASE_WITHOUT_RECEIPT_HOLD"):
            current.read_last_attempt(source_host=HOST)
        self.assertEqual(len(api.refs), 2)

    def test_no_prior_history_never_claims_first_attempt(self):
        api = SharedGitHubCommitAPI()
        current = GitHubRaw5AttemptProvider(api, ANCHOR, NOW)
        current.acquire_atomic(source_host=HOST, owner_run_id="new-run-0002")
        with self.assertRaisesRegex(ValueError, "FIRST_ATTEMPT_UNATTESTED_HOLD"):
            current.read_last_attempt(source_host=HOST)

    def test_previous_receipt_ref_replacement_denied(self):
        api, writer, reader, _ = self._previous_and_current()
        api.refs[writer._receipt_ref] = ANCHOR
        with self.assertRaisesRegex(ValueError, "HISTORY_COMMIT_INVALID_HOLD"):
            reader.read_last_attempt(source_host=HOST)

    def test_previous_body_sha_tamper_denied(self):
        api, writer, reader, _ = self._previous_and_current()
        api.tamper_blob = True
        with self.assertRaisesRegex(ValueError, "GIT_BLOB_SHA_MISMATCH_HOLD"):
            reader.read_last_attempt(source_host=HOST)

    def test_duplicate_prior_slot_receipts_fail_closed(self):
        api, writer, reader, _ = self._previous_and_current()
        alias = writer._receipt_ref + "-duplicate"
        api.refs[alias] = writer._receipt_commit_sha
        with self.assertRaisesRegex(ValueError, "MULTIPLE_HOST_ATTEMPTS_IN_SLOT_HOLD"):
            reader.read_last_attempt(source_host=HOST)

    def test_wrong_namespace_and_network_error_not_treated_as_no_history(self):
        api, writer, reader, _ = self._previous_and_current()
        original = api.__call__
        class BadStatusTransport:
            def __call__(self, method, path, payload):
                if "/git/matching-refs/" in path:
                    return 206, [], NOW
                return original(method, path, payload)
        reader._request = BadStatusTransport()
        with self.assertRaisesRegex(ValueError, "HISTORY_ENUMERATION_UNVERIFIED_HOLD"):
            reader.read_last_attempt(source_host=HOST)
        with self.assertRaisesRegex(ValueError, "NO_LEASE_HOLD"):
            GitHubRaw5AttemptProvider(api, ANCHOR, NOW).read_last_attempt(source_host=HOST)




if __name__ == "__main__":
    unittest.main()
