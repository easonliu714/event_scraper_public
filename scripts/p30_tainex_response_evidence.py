"""Isolated HTTP response evidence ingestion; NEVER performs a network request.

Only accepts externally captured response bytes and operator-supplied metadata.
The resulting evidence is explicitly UNATTESTED until the capturing host's
independent native HTTP journal is verified. No publisher integration.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED_HOSTS = frozenset(("www.tainex.com.tw", "tainex.com.tw"))
MAX_BYTES = 2_000_000


def ingest_response(*, raw_path, output_dir, source_url, final_url,
                    http_status, observed_at):
    """Persist a bounded immutable-by-name isolated response and metadata."""
    if type(http_status) is not int or http_status not in (200, 301, 302, 403, 429):
        raise ValueError("HTTP_STATUS_UNSUPPORTED_HOLD")
    for url in (source_url, final_url):
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS
                or parsed.username or parsed.password or parsed.fragment
                or parsed.port is not None):
            raise ValueError("SOURCE_URL_SCOPE_HOLD")
    if final_url != source_url:
        raise ValueError("REDIRECT_UNVERIFIED_HOLD")
    timestamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("UTC_REQUIRED_HOLD")
    if timestamp.utcoffset().total_seconds() != 0:
        raise ValueError("UTC_REQUIRED_HOLD")
    raw = Path(raw_path).read_bytes()
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("BODY_SIZE_HOLD")
    digest = hashlib.sha256(raw).hexdigest()
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink():
        raise ValueError("OUTPUT_SYMLINK_HOLD")
    name = "tainex-" + digest
    evidence = {"source": "tainex", "requested_url": source_url,
                "final_url": final_url, "http_status": http_status,
                "observed_at_utc": timestamp.isoformat(),
                "raw_sha256": digest, "raw_bytes": len(raw),
                "native_http_attested": False,
                "decision": "ISOLATED_UNATTESTED_NO_PUBLICATION"}
    # Exclusive creation: never replace previous evidence.
    for suffix, content in ((".bin", raw),
                            (".json", (json.dumps(evidence, sort_keys=True,
                                                  ensure_ascii=False) + "\n").encode("utf-8"))):
        fd = os.open(str(directory / (name + suffix)),
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    return evidence


def main():
    parser = argparse.ArgumentParser()
    for key in ("raw-path", "output-dir", "source-url", "final-url", "observed-at"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--http-status", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(ingest_response(raw_path=args.raw_path,
                                     output_dir=args.output_dir,
                                     source_url=args.source_url,
                                     final_url=args.final_url,
                                     http_status=args.http_status,
                                     observed_at=args.observed_at),
                     sort_keys=True))


if __name__ == "__main__":
    main()
