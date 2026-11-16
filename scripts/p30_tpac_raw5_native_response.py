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
    if (receipt.get("raw_body_length") != len(body)
            or receipt.get("raw_body_sha256") != hashlib.sha256(body).hexdigest()
            or receipt.get("formal_publish_allowed") is not False):
        raise ValueError("RAW5_NATIVE_BYTES_PARITY_HOLD")
    return receipt
