"""RAW5 isolated native-response evidence writer. No network, no GET authority.

Only the caller's real HTTPS response bytes and transport metadata may enter
this recorder. A WebReader text page or reconstructed receipt is not accepted.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

HOST = "tpac.org.taipei"
DETAIL = re.compile(r"^/(program|event)/([1-9][0-9]*)/?$")
MAX_BODY = 2 * 1024 * 1024


def seal_native_detail_response(*, requested_url: str, final_url: str,
                                status: int, content_type: str, body: bytes,
                                observed_at: datetime, executor_id: str,
                                claim_id: str, run_id: str) -> tuple[bytes, bytes]:
    """Return canonical manifest bytes and original body; never grant source GET."""
    if any(type(x) is not str or not x or len(x) > 256
           for x in (requested_url, final_url, content_type, executor_id, claim_id, run_id)):
        raise ValueError("RAW5_NATIVE_METADATA_MISSING_HOLD")
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}", x)
           for x in (executor_id, claim_id, run_id)):
        raise ValueError("RAW5_NATIVE_IDENTITY_INVALID_HOLD")
    paths = []
    for url in (requested_url, final_url):
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.netloc != HOST or parsed.username
                or parsed.password or parsed.query or parsed.fragment):
            raise ValueError("RAW5_NATIVE_ORIGIN_OR_REDIRECT_HOLD")
        match = DETAIL.fullmatch(parsed.path)
        if match is None:
            raise ValueError("RAW5_NATIVE_DETAIL_PATH_HOLD")
        paths.append(match.groups())
    if paths[0] != paths[1]:
        raise ValueError("RAW5_NATIVE_DETAIL_ID_REDIRECT_HOLD")
    if type(status) is not int or status != 200:
        raise ValueError("RAW5_NATIVE_HTTP_NOT_200_HOLD")
    if not content_type.lower().split(";", 1)[0].strip() in ("text/html", "application/xhtml+xml"):
        raise ValueError("RAW5_NATIVE_NOT_HTML_HOLD")
    if type(body) is not bytes or not 0 < len(body) <= MAX_BODY:
        raise ValueError("RAW5_NATIVE_BYTES_MISSING_OR_OVERSIZE_HOLD")
    if (type(observed_at) is not datetime or observed_at.tzinfo is None
            or observed_at.utcoffset() is None):
        raise ValueError("RAW5_NATIVE_UTC_UNATTESTED_HOLD")
    if observed_at.utcoffset().total_seconds() != 0:
        raise ValueError("RAW5_NATIVE_UTC_REQUIRED_HOLD")
    receipt = {
        "schema": "RAW5_NATIVE_DETAIL_V1", "method": "GET",
        "requested_url": requested_url, "final_url": final_url,
        "http_status": status, "content_type": content_type,
        "observed_at_utc": observed_at.isoformat(),
        "namespace": paths[0][0], "event_id": paths[0][1],
        "executor_id": executor_id, "claim_id": claim_id, "run_id": run_id,
        "raw_body_length": len(body), "raw_body_sha256": hashlib.sha256(body).hexdigest(),
        "formal_publish_allowed": False,
    }
    return json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8"), body


def verify_native_detail_receipt(manifest: bytes, body: bytes) -> dict:
    """Independently verify exact raw bytes; never infer HTTP provenance."""
    if type(manifest) is not bytes or type(body) is not bytes:
        raise ValueError("RAW5_NATIVE_RECEIPT_SCHEMA_HOLD")
    try:
        receipt = json.loads(manifest.decode("utf-8", "strict"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("RAW5_NATIVE_RECEIPT_PARSE_HOLD") from exc
    if type(receipt) is not dict or receipt.get("schema") != "RAW5_NATIVE_DETAIL_V1":
        raise ValueError("RAW5_NATIVE_RECEIPT_SCHEMA_HOLD")
    # Revalidate the complete untrusted manifest, not only its body hash.
    expected_keys = {
        "schema", "method", "requested_url", "final_url", "http_status",
        "content_type", "observed_at_utc", "namespace", "event_id",
        "executor_id", "claim_id", "run_id", "raw_body_length",
        "raw_body_sha256", "formal_publish_allowed",
    }
    if set(receipt) != expected_keys or receipt.get("formal_publish_allowed") is not False:
        raise ValueError("RAW5_NATIVE_BYTES_PARITY_HOLD")
    if (type(receipt["raw_body_length"]) is not int
            or receipt["raw_body_length"] != len(body)
            or receipt["raw_body_sha256"] != hashlib.sha256(body).hexdigest()):
        raise ValueError("RAW5_NATIVE_BYTES_PARITY_HOLD")
    try:
        timestamp = datetime.fromisoformat(receipt["observed_at_utc"])
        expected, _ = seal_native_detail_response(
            requested_url=receipt["requested_url"], final_url=receipt["final_url"],
            status=receipt["http_status"], content_type=receipt["content_type"],
            body=body, observed_at=timestamp, executor_id=receipt["executor_id"],
            claim_id=receipt["claim_id"], run_id=receipt["run_id"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError("RAW5_NATIVE_MANIFEST_FIELDS_HOLD") from exc
    if (receipt["method"] != "GET" or expected != manifest
            or json.loads(expected)["namespace"] != receipt["namespace"]
            or json.loads(expected)["event_id"] != receipt["event_id"]):
        raise ValueError("RAW5_NATIVE_MANIFEST_FIELDS_HOLD")
    return receipt


# Isolated artifact transport: consumes already captured native response bytes.
# Never initiates a request, creates a claim, or grants publication.
def build_isolated_native_zip(records: list[tuple[bytes, bytes]]) -> bytes:
    """Package 1-5 independently valid DETAIL responses without fabricating provenance."""
    import io
    import zipfile
    if type(records) is not list or not 1 <= len(records) <= 5:
        raise ValueError("RAW5_ZIP_RECORD_COUNT_HOLD")
    index = []
    payloads = []
    identities = set()
    for manifest, body in records:
        receipt = verify_native_detail_receipt(manifest, body)
        identity = (receipt["namespace"], receipt["event_id"])
        if identity in identities:
            raise ValueError("RAW5_ZIP_DUPLICATE_ID_HOLD")
        identities.add(identity)
        stem = f'{receipt["namespace"]}-{receipt["event_id"]}'
        payloads.extend([(f"responses/{stem}.json", manifest),
                         (f"responses/{stem}.html", body)])
        index.append({"namespace": identity[0], "event_id": identity[1],
                      "manifest": f"responses/{stem}.json",
                      "body": f"responses/{stem}.html",
                      "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
                      "body_sha256": hashlib.sha256(body).hexdigest()})
    index_bytes = json.dumps({"schema": "RAW5_ISOLATED_ZIP_V1",
                              "formal_publish_allowed": False,
                              "records": index}, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in [("index.json", index_bytes), *payloads]:
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_STORED
            archive.writestr(entry, data)
    return output.getvalue()


def verify_isolated_native_zip(archive_bytes: bytes) -> list[dict]:
    """Independently check ZIP member allowlist, CRC, SHA and native receipt parity."""
    import io
    import zipfile
    if type(archive_bytes) is not bytes or not archive_bytes:
        raise ValueError("RAW5_ZIP_BYTES_HOLD")
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if (len(names) != len(set(names)) or "index.json" not in names
                    or len(names) > 11 or any(info.file_size > MAX_BODY for info in infos)
                    or any(info.compress_type != zipfile.ZIP_STORED for info in infos)
                    or archive.testzip() is not None):
                raise ValueError("RAW5_ZIP_STRUCTURE_OR_CRC_HOLD")
            index_bytes = archive.read("index.json")
            index = json.loads(index_bytes.decode("utf-8", "strict"))
            if (type(index) is not dict or set(index) !=
                    {"schema", "formal_publish_allowed", "records"}
                    or index["schema"] != "RAW5_ISOLATED_ZIP_V1"
                    or index["formal_publish_allowed"] is not False
                    or type(index["records"]) is not list
                    or not 1 <= len(index["records"]) <= 5):
                raise ValueError("RAW5_ZIP_INDEX_HOLD")
            expected = {"index.json"}
            seen = set()
            verified = []
            for item in index["records"]:
                if type(item) is not dict or set(item) != {
                    "namespace", "event_id", "manifest", "body",
                    "manifest_sha256", "body_sha256"}:
                    raise ValueError("RAW5_ZIP_INDEX_ENTRY_HOLD")
                namespace, event_id = item["namespace"], item["event_id"]
                if (namespace not in ("program", "event")
                        or type(event_id) is not str or not re.fullmatch(r"[1-9][0-9]*", event_id)
                        or (namespace, event_id) in seen):
                    raise ValueError("RAW5_ZIP_IDENTITY_HOLD")
                seen.add((namespace, event_id))
                stem = f"{namespace}-{event_id}"
                if (item["manifest"] != f"responses/{stem}.json"
                        or item["body"] != f"responses/{stem}.html"):
                    raise ValueError("RAW5_ZIP_PATH_HOLD")
                expected.update((item["manifest"], item["body"]))
                manifest = archive.read(item["manifest"])
                body = archive.read(item["body"])
                if (hashlib.sha256(manifest).hexdigest() != item["manifest_sha256"]
                        or hashlib.sha256(body).hexdigest() != item["body_sha256"]):
                    raise ValueError("RAW5_ZIP_SHA256_HOLD")
                receipt = verify_native_detail_receipt(manifest, body)
                if (receipt["namespace"], receipt["event_id"]) != (namespace, event_id):
                    raise ValueError("RAW5_ZIP_RECEIPT_IDENTITY_HOLD")
                verified.append(receipt)
            if set(names) != expected or len(names) != len(expected):
                raise ValueError("RAW5_ZIP_MEMBER_ALLOWLIST_HOLD")
            return verified
    except (zipfile.BadZipFile, KeyError, UnicodeError, TypeError, OverflowError) as exc:
        raise ValueError("RAW5_ZIP_INVALID_HOLD") from exc
