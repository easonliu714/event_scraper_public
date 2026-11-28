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
RECEIPT_REF_PREFIX = "refs/heads/source-claims/raw5-receipt-"
RECEIPT_MSG_PREFIX = "RAW5_ATTEMPT_V1_BLOB "
RECEIPT_TREE_PATH = "raw5_attempt.json"
RUN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{7,127}\Z")


def _owner_fence(slot_ref, owner_run_id):
    """Bind fencing to the winning owner as well as the host-wide slot."""
    if (type(slot_ref) is not str or not re.fullmatch(re.escape(REF_PREFIX) + r"[0-9]{1,12}", slot_ref)
            or type(owner_run_id) is not str or not RUN_RE.fullmatch(owner_run_id)):
        raise ValueError("RAW5_FENCE_SCOPE_HOLD")
    return hashlib.sha256((slot_ref + "\\n" + owner_run_id).encode()).hexdigest()


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
        # Bind the unique source-host slot to the winning run, not a generic
        # anchor SHA. Still fail closed until Ruleset and two-runner attestation.
        status, anchor = self._call("GET", "/git/commits/" + self._anchor)
        tree = anchor.get("tree") if type(anchor) is dict else None
        tree_sha = tree.get("sha") if type(tree) is dict else None
        if (status != 200 or type(tree_sha) is not str
                or not re.fullmatch(r"[0-9a-f]{40}", tree_sha)):
            raise ValueError("RAW5_LEASE_ANCHOR_TREE_HOLD")
        message = "RAW5_HOST_LEASE_V1 " + HOST + " " + str(slot) + " " + owner_run_id
        status, commit = self._call("POST", "/git/commits", {
            "message": message, "tree": tree_sha, "parents": [self._anchor]})
        lease_sha = commit.get("sha") if type(commit) is dict else None
        if (status != 201 or type(lease_sha) is not str
                or not re.fullmatch(r"[0-9a-f]{40}", lease_sha)):
            raise ValueError("RAW5_LEASE_COMMIT_CREATE_HOLD")
        status, _ = self._call("POST", "/git/refs", {"ref": ref, "sha": lease_sha})
        if status != 201:
            raise ValueError("RAW5_ATOMIC_SLOT_NOT_ACQUIRED_HOLD")
        status, readback = self._call("GET", "/git/ref/" + ref.removeprefix("refs/"))
        pointed = readback.get("object") if type(readback) is dict else None
        if (status != 200 or type(pointed) is not dict
                or pointed.get("sha") != lease_sha
                or pointed.get("type") not in (None, "commit")):
            raise ValueError("RAW5_LEASE_REF_READBACK_HOLD")
        status, bound = self._call("GET", "/git/commits/" + lease_sha)
        parents = bound.get("parents") if type(bound) is dict else None
        bound_tree = bound.get("tree") if type(bound) is dict else None
        if (status != 200 or bound.get("sha") != lease_sha
                or bound.get("message") != message
                or type(parents) is not list or len(parents) != 1
                or type(parents[0]) is not dict or parents[0].get("sha") != self._anchor
                or type(bound_tree) is not dict or bound_tree.get("sha") != tree_sha):
            raise ValueError("RAW5_LEASE_OWNER_COMMIT_BINDING_HOLD")
        self._run, self._ref = owner_run_id, ref
        self._lease_commit_sha = lease_sha
        # No 'atomic_acquire_verified=True': actual protection has not been
        # proven on two independent runners, and refs may be deleted.
        return {"source_host": HOST, "owner_run_id": owner_run_id,
                "exclusive": False, "atomic_acquire_verified": False,
                "fencing_token": _owner_fence(ref, owner_run_id),
                "acquired_at": self._now}

    def read_last_attempt(self, *, source_host):
        """Recover the latest PREVIOUS attempt across all visible UTC slots.

        A previous-hour-only lookup misses durable receipts two or more
        hours old. Reuse the complete forensic lease/receipt scan so missing
        older receipts or crashes cannot be ignored. Neither an empty scan
        nor this result attests immutable history or authorizes source GET.
        """
        if source_host != HOST or self._ref is None or self._run is None:
            raise ValueError("RAW5_NO_LEASE_HOLD")
        current = int(self._now.timestamp()) // 3600
        if self._ref != REF_PREFIX + str(current):
            raise ValueError("RAW5_CURRENT_SLOT_SCOPE_HOLD")
        history = self.audit_host_wide_attempts(source_host=source_host)
        previous = history["last_attempt_at"]
        if int(previous.timestamp()) // 3600 >= current:
            raise ValueError("RAW5_CURRENT_SLOT_RECEIPT_NOT_PREVIOUS_HOLD")
        return {
            "source_host": HOST,
            "first_attempt": False,
            "last_attempt_at": previous,
            "history_receipt_ref": history["last_receipt_ref"],
            "history_receipt_commit_sha": history["last_receipt_commit_sha"],
            "history_receipt_blob_sha": history["last_receipt_blob_sha"],
            "history_record_independently_verified": True,
            "host_wide_receipts_verified": True,
            "history_complete_attested": False,
            "native_get_allowed": False,
        }

    def audit_host_wide_attempts(self, *, source_host):
        """Audit every visible protected host lease and receipt across UTC slots.

        This is forensic evidence only. A missing first-attempt anchor, a
        partial listing, or any lease without a receipt must never grant GET.
        """
        if source_host != HOST or self._ref is None or self._run is None:
            raise ValueError("RAW5_NO_LEASE_HOLD")

        def listing(prefix):
            status, refs, server_at = self._request(
                "GET", PREFIX + "/git/matching-refs/heads/source-claims/" + prefix, None)
            if (type(status) is not int or status != 200 or type(refs) is not list
                    or abs((_utc(server_at) - self._now).total_seconds()) > 120):
                raise ValueError("RAW5_HOST_WIDE_ENUMERATION_HOLD")
            return refs

        leases = {}
        receipts = {}
        for entry in listing("raw5-tpac-"):
            name = entry.get("ref") if type(entry) is dict else None
            obj = entry.get("object") if type(entry) is dict else None
            if (type(name) is not str or not name.startswith(REF_PREFIX)
                    or not re.fullmatch(r"[0-9]{1,12}", name[len(REF_PREFIX):])
                    or type(obj) is not dict or obj.get("type") != "commit"
                    or not re.fullmatch(r"[0-9a-f]{40}", str(obj.get("sha")))):
                raise ValueError("RAW5_HOST_WIDE_LEASE_SCHEMA_HOLD")
            slot = int(name[len(REF_PREFIX):])
            if slot in leases or slot > int(self._now.timestamp()) // 3600:
                raise ValueError("RAW5_HOST_WIDE_LEASE_SLOT_HOLD")
            leases[slot] = obj["sha"]
        for entry in listing("raw5-receipt-"):
            name = entry.get("ref") if type(entry) is dict else None
            obj = entry.get("object") if type(entry) is dict else None
            match = (re.fullmatch(re.escape(RECEIPT_REF_PREFIX)
                                  + r"([0-9]{1,12})-([A-Za-z0-9][A-Za-z0-9_.-]{7,127})",
                                  name) if type(name) is str else None)
            if (match is None or type(obj) is not dict
                    or obj.get("type") != "commit"
                    or not re.fullmatch(r"[0-9a-f]{40}", str(obj.get("sha")))):
                raise ValueError("RAW5_HOST_WIDE_RECEIPT_SCHEMA_HOLD")
            slot = int(match.group(1))
            if slot in receipts:
                raise ValueError("RAW5_MULTIPLE_HOST_ATTEMPTS_IN_SLOT_HOLD")
            receipts[slot] = (name, match.group(2), obj["sha"])
        if not leases or self._ref not in [REF_PREFIX + str(s) for s in leases]:
            raise ValueError("RAW5_HOST_WIDE_CURRENT_LEASE_HOLD")
        # A matching ref name is not proof of an owner-bound lease.
        # Verify every historical lease commit, parent, tree, slot and owner.
        status, anchor = self._call("GET", "/git/commits/" + self._anchor)
        anchor_tree = anchor.get("tree") if type(anchor) is dict else None
        tree_sha = anchor_tree.get("sha") if type(anchor_tree) is dict else None
        if (status != 200 or type(tree_sha) is not str
                or not re.fullmatch(r"[0-9a-f]{40}", tree_sha)):
            raise ValueError("RAW5_HOST_WIDE_ANCHOR_HOLD")
        for slot, lease_sha in sorted(leases.items()):
            status, lease = self._call("GET", "/git/commits/" + lease_sha)
            parents = lease.get("parents") if type(lease) is dict else None
            tree = lease.get("tree") if type(lease) is dict else None
            message = lease.get("message") if type(lease) is dict else None
            prefix = "RAW5_HOST_LEASE_V1 " + HOST + " " + str(slot) + " "
            owner = message[len(prefix):] if type(message) is str and message.startswith(prefix) else None
            if (status != 200 or lease.get("sha") != lease_sha
                    or type(owner) is not str or not RUN_RE.fullmatch(owner)
                    or type(parents) is not list or len(parents) != 1
                    or type(parents[0]) is not dict or parents[0].get("sha") != self._anchor
                    or type(tree) is not dict or tree.get("sha") != tree_sha):
                raise ValueError("RAW5_HOST_WIDE_LEASE_BINDING_HOLD")
            if slot in receipts and receipts[slot][1] != owner:
                raise ValueError("RAW5_HOST_WIDE_OWNER_MISMATCH_HOLD")
        if set(receipts) - set(leases):
            raise ValueError("RAW5_HOST_WIDE_ORPHAN_RECEIPT_HOLD")
        # A previous lease without a durable receipt may represent a crash.
        current = int(self._now.timestamp()) // 3600
        if any(slot != current and slot not in receipts for slot in leases):
            raise ValueError("RAW5_HOST_WIDE_CRASH_GAP_HOLD")
        latest = None
        latest_record = None
        for slot, (ref, run_id, sha) in sorted(receipts.items()):
            status, commit = self._call("GET", "/git/commits/" + sha)
            if status != 200 or commit.get("sha") != sha:
                raise ValueError("RAW5_HOST_WIDE_COMMIT_HOLD")
            message = commit.get("message")
            if type(message) is not str or not message.startswith(RECEIPT_MSG_PREFIX):
                raise ValueError("RAW5_HOST_WIDE_COMMIT_HOLD")
            blob_sha = message[len(RECEIPT_MSG_PREFIX):]
            self._read_commit_binding(sha, blob_sha)
            record = self._read_verified_blob(blob_sha)
            try:
                attempted = _utc(datetime.fromisoformat(record["attempted_at"]))
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                raise ValueError("RAW5_HOST_WIDE_TIME_HOLD") from exc
            expected = {"schema": "RAW5_ATTEMPT_V1", "source_host": HOST,
                        "owner_run_id": run_id,
                        "fencing_token": _owner_fence(REF_PREFIX + str(slot), run_id),
                        "attempted_at": attempted.isoformat(),
                        "slot_ref": REF_PREFIX + str(slot),
                        "native_get_allowed": False}
            if (record != expected or int(attempted.timestamp()) // 3600 != slot
                    or attempted > self._now):
                raise ValueError("RAW5_HOST_WIDE_BINDING_HOLD")
            if latest is None or attempted > latest:
                latest = attempted
                latest_record = (ref, sha, blob_sha)
        if latest is None:
            raise ValueError("RAW5_FIRST_ATTEMPT_UNATTESTED_HOLD")
        return {"source_host": HOST, "last_attempt_at": latest,
                "last_receipt_ref": latest_record[0],
                "last_receipt_commit_sha": latest_record[1],
                "last_receipt_blob_sha": latest_record[2],
                "first_attempt": False, "native_get_allowed": False,
                "host_wide_receipts_verified": True,
                "history_complete_attested": False}

    @staticmethod
    def _receipt_branch(slot_ref, run_id):
        """Protected branch scope; a raw Git blob cannot be a branch tip."""
        if (type(slot_ref) is not str
                or not re.fullmatch(re.escape(REF_PREFIX) + r"[0-9]{1,12}", slot_ref)
                or type(run_id) is not str or not RUN_RE.fullmatch(run_id)):
            raise ValueError("RAW5_RECEIPT_REF_SCOPE_HOLD")
        return RECEIPT_REF_PREFIX + slot_ref[len(REF_PREFIX):] + "-" + run_id

    @staticmethod
    def _receipt_tree_sha(blob_sha):
        """Compute the exact single-file Git tree identity from the blob SHA."""
        if type(blob_sha) is not str or not re.fullmatch(r"[0-9a-f]{40}", blob_sha):
            raise ValueError("RAW5_RECEIPT_COMMIT_SHA_HOLD")
        raw = (b"100644 " + RECEIPT_TREE_PATH.encode("ascii") + bytes([0])
               + bytes.fromhex(blob_sha))
        return hashlib.sha1(b"tree " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()

    def _read_receipt_tree(self, tree_sha, blob_sha):
        # A SHA written only in a commit message is not a Git object edge.
        # Legacy anchor-tree receipts may be readable but are not durable proof.
        if tree_sha != self._receipt_tree_sha(blob_sha):
            raise ValueError("RAW5_RECEIPT_TREE_LINK_HOLD")
        status, tree = self._call("GET", "/git/trees/" + tree_sha)
        entries = tree.get("tree")
        if (status != 200 or tree.get("sha") != tree_sha
                or tree.get("truncated") is not False or type(entries) is not list
                or len(entries) != 1 or type(entries[0]) is not dict
                or entries[0].get("path") != RECEIPT_TREE_PATH
                or entries[0].get("mode") != "100644"
                or entries[0].get("type") != "blob"
                or entries[0].get("sha") != blob_sha):
            raise ValueError("RAW5_RECEIPT_TREE_READBACK_HOLD")

    def _read_commit_binding(self, commit_sha, blob_sha):
        """Require a real Git commit with pinned parent and reachable blob."""
        if (type(commit_sha) is not str or not re.fullmatch(r"[0-9a-f]{40}", commit_sha)
                or type(blob_sha) is not str or not re.fullmatch(r"[0-9a-f]{40}", blob_sha)):
            raise ValueError("RAW5_RECEIPT_COMMIT_SHA_HOLD")
        status, obj = self._call("GET", "/git/commits/" + commit_sha)
        if status != 200 or obj.get("sha") != commit_sha:
            raise ValueError("RAW5_RECEIPT_COMMIT_MISSING_HOLD")
        tree = obj.get("tree")
        parents = obj.get("parents")
        if (type(tree) is not dict or type(tree.get("sha")) is not str
                or not re.fullmatch(r"[0-9a-f]{40}", tree["sha"])
                or type(parents) is not list or len(parents) != 1
                or type(parents[0]) is not dict or parents[0].get("sha") != self._anchor
                or obj.get("message") != RECEIPT_MSG_PREFIX + blob_sha):
            raise ValueError("RAW5_RECEIPT_COMMIT_BINDING_HOLD")
        self._read_receipt_tree(tree["sha"], blob_sha)

    def _read_verified_blob(self, blob_sha):
        import base64
        status, blob = self._call("GET", "/git/blobs/" + blob_sha)
        if status != 200 or blob.get("encoding") != "base64":
            raise ValueError("RAW5_RECEIPT_BLOB_READBACK_HOLD")
        try:
            raw = base64.b64decode(blob["content"], validate=True)
            record = json.loads(raw)
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("RAW5_RECEIPT_BYTES_INVALID_HOLD") from exc
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        if actual != blob_sha:
            raise ValueError("RAW5_RECEIPT_GIT_BLOB_SHA_MISMATCH_HOLD")
        if type(record) is not dict:
            raise ValueError("RAW5_RECEIPT_SCHEMA_HOLD")
        return record

    def verify_receipt_from_fresh_executor(self, *, source_host, owner_run_id,
                                           receipt_ref, expected_sha, expected_commit_sha,
                                           slot_ref, expected_at):
        """Verify protected receipt commit and raw blob from a separate executor.

        This does NOT attest real branch protection or grant LIVE HTTP authority.
        """
        if (source_host != HOST or type(owner_run_id) is not str
                or not RUN_RE.fullmatch(owner_run_id)
                or type(receipt_ref) is not str
                or receipt_ref != self._receipt_branch(slot_ref, owner_run_id)
                or type(expected_sha) is not str
                or not re.fullmatch(r"[0-9a-f]{40}", expected_sha)
                or type(expected_commit_sha) is not str
                or not re.fullmatch(r"[0-9a-f]{40}", expected_commit_sha)):
            raise ValueError("RAW5_FRESH_RECEIPT_SCOPE_HOLD")
        when = _utc(expected_at)
        status, ref = self._call("GET", "/git/ref/" + receipt_ref.removeprefix("refs/"))
        actual = ref.get("object", {}).get("sha") if type(ref.get("object")) is dict else None
        if status != 200 or actual != expected_commit_sha:
            raise ValueError("RAW5_FRESH_RECEIPT_REF_HOLD")
        self._read_commit_binding(expected_commit_sha, expected_sha)
        record = self._read_verified_blob(expected_sha)
        if record != {
                "schema": "RAW5_ATTEMPT_V1", "source_host": HOST,
                "owner_run_id": owner_run_id,
                "fencing_token": _owner_fence(slot_ref, owner_run_id),
                "attempted_at": when.isoformat(), "slot_ref": slot_ref,
                "native_get_allowed": False}:
            raise ValueError("RAW5_FRESH_RECEIPT_PARITY_HOLD")
        return {"receipt_verified": True, "native_get_allowed": False,
                "durable_provider_verified": False, "attempt_written_at": when}

    def write_attempt(self, *, source_host, owner_run_id, fencing_token, attempted_at):
        """Store canonical JSON blob behind a real protected-scope Git commit.

        A branch must point at a commit. Its tree must actually contain the
        receipt blob, not merely mention its SHA in the commit message.
        """
        import base64
        if (source_host != HOST or owner_run_id != self._run
                or self._ref is None or type(fencing_token) is not str
                or fencing_token != _owner_fence(self._ref, self._run)
                or _utc(attempted_at) != self._now):
            raise ValueError("RAW5_RECEIPT_SCOPE_OR_FENCE_HOLD")
        receipt = {"schema": "RAW5_ATTEMPT_V1", "source_host": HOST,
                   "owner_run_id": self._run, "fencing_token": fencing_token,
                   "attempted_at": self._now.isoformat(),
                   "slot_ref": self._ref, "native_get_allowed": False}
        raw = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
        encoded = base64.b64encode(raw).decode()
        expected_blob_sha = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        status, blob = self._call("POST", "/git/blobs",
                                  {"content": encoded, "encoding": "base64"})
        if status != 201 or blob.get("sha") != expected_blob_sha:
            raise ValueError("RAW5_RECEIPT_BLOB_NOT_DURABLE_HOLD")
        status, anchor = self._call("GET", "/git/commits/" + self._anchor)
        tree = anchor.get("tree") if type(anchor) is dict else None
        tree_sha = tree.get("sha") if type(tree) is dict else None
        if status != 200 or type(tree_sha) is not str or not re.fullmatch(
                r"[0-9a-f]{40}", tree_sha):
            raise ValueError("RAW5_RECEIPT_ANCHOR_TREE_HOLD")
        expected_tree_sha = self._receipt_tree_sha(expected_blob_sha)
        status, receipt_tree = self._call("POST", "/git/trees", {"tree": [{
            "path": RECEIPT_TREE_PATH, "mode": "100644", "type": "blob",
            "sha": expected_blob_sha}]})
        if status != 201 or receipt_tree.get("sha") != expected_tree_sha:
            raise ValueError("RAW5_RECEIPT_TREE_CREATE_HOLD")
        self._read_receipt_tree(expected_tree_sha, expected_blob_sha)
        status, commit = self._call("POST", "/git/commits", {
            "message": RECEIPT_MSG_PREFIX + expected_blob_sha,
            "tree": expected_tree_sha, "parents": [self._anchor]})
        commit_sha = commit.get("sha")
        if status != 201 or type(commit_sha) is not str or not re.fullmatch(
                r"[0-9a-f]{40}", commit_sha):
            raise ValueError("RAW5_RECEIPT_COMMIT_CREATE_HOLD")
        self._read_commit_binding(commit_sha, expected_blob_sha)
        ref = self._receipt_branch(self._ref, self._run)
        status, _ = self._call("POST", "/git/refs", {"ref": ref, "sha": commit_sha})
        if status != 201:
            raise ValueError("RAW5_RECEIPT_REF_NOT_ATOMIC_HOLD")
        self._receipt_ref = ref
        self._receipt_sha = expected_blob_sha
        self._receipt_commit_sha = commit_sha

    def read_attempt(self, *, source_host, owner_run_id):
        """Re-fetch protected receipt branch -> commit -> blob, not cached bytes."""
        if (source_host != HOST or owner_run_id != self._run
                or not getattr(self, "_receipt_ref", None)):
            raise ValueError("RAW5_RECEIPT_READ_SCOPE_HOLD")
        if self._receipt_ref != self._receipt_branch(self._ref, self._run):
            raise ValueError("RAW5_RECEIPT_REF_SCOPE_HOLD")
        path = "/git/ref/" + self._receipt_ref.removeprefix("refs/")
        status, ref = self._call("GET", path)
        sha = ref.get("object", {}).get("sha") if type(ref.get("object")) is dict else None
        if status != 200 or sha != getattr(self, "_receipt_commit_sha", None):
            raise ValueError("RAW5_RECEIPT_REF_READBACK_HOLD")
        self._read_commit_binding(sha, self._receipt_sha)
        record = self._read_verified_blob(self._receipt_sha)
        if record != {
                "schema": "RAW5_ATTEMPT_V1", "source_host": HOST,
                "owner_run_id": self._run,
                "fencing_token": _owner_fence(self._ref, self._run),
                "attempted_at": self._now.isoformat(), "slot_ref": self._ref,
                "native_get_allowed": False}:
            raise ValueError("RAW5_RECEIPT_INDEPENDENT_PARITY_HOLD")
        # Still not attested: two-runner lease / durable LAST_ATTEMPT not ready.
        return {"source_host": HOST, "owner_run_id": self._run,
                "fencing_token": record["fencing_token"],
                "attempt_written_at": self._now,
                "durable_provider_verified": False, "first_attempt": False}
