"""VENUE-01 Taipei Arena public OpenData, fail-closed read-only review adapter.

Never writes formal event data. DataSN is an arena announcement ID, NOT a
ticket-platform Event ID. '日期時間' is an announcement timestamp, NOT an event date.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

ENDPOINT = "https://www.arena.taipei/OpenData.aspx?SN=DDA0CF2A5B65EBFE"
MAX_BYTES = 2_000_000
MAX_ITEMS = 40
MAX_CONTENT_CHARS = 100_000
PLATFORM_PATTERN = re.compile(
    r"售\s*票\s*系\s*統\s*[:：]\s*"
    r"(Ticket\s*Plus|遠大售票系統|ibon|拓元售票系統|拓元售票|KKTIX)",
    re.IGNORECASE,
)


class SourceHold(ValueError):
    """Reject unverifiable source structure without fallback inference."""


def _source_url_ok(url: object) -> bool:
    if not isinstance(url, str) or len(url) > 500:
        return False
    try:
        u = urllib.parse.urlsplit(url)
        if (u.scheme, u.netloc, u.path) != (
            "https", "www.arena.taipei", "/News_Content.aspx"
        ) or u.username or u.password or u.fragment:
            return False
        params = urllib.parse.parse_qs(u.query, keep_blank_values=True)
        return (
            set(params) == {"n", "s"}
            and all(len(values) == 1 for values in params.values())
            and bool(re.fullmatch(r"[A-F0-9]{16}", params["n"][0]))
            and bool(re.fullmatch(r"[A-F0-9]{16}", params["s"][0]))
        )
    except (ValueError, TypeError):
        return False


def _platform_claim(content: str) -> str | None:
    # Only the source's explicit '售票系統：' label qualifies.
    # Contact numbers, article text, or other mentions cannot infer platform.
    text = html.unescape(re.sub(r"<[^>]{0,200}>", " ", content))
    found = set()
    for match in PLATFORM_PATTERN.finditer(text):
        value = re.sub(r"\s+", "", match.group(1)).lower()
        if value in ("ticketplus", "遠大售票系統"):
            found.add("Ticket Plus/遠大")
        elif value in ("拓元售票系統", "拓元售票"):
            found.add("拓元")
        elif value == "ibon":
            found.add("ibon")
        elif value == "kktix":
            found.add("KKTIX")
    return next(iter(found)) if len(found) == 1 else None


def inspect_payload(payload: object) -> dict:
    if not isinstance(payload, list) or len(payload) > MAX_ITEMS:
        raise SourceHold("HOLD_JSON_ARRAY_OR_ITEM_CAP")
    seen: set[str] = set()
    rows = []
    for entry in payload:
        if not isinstance(entry, dict):
            raise SourceHold("HOLD_ITEM_SHAPE")
        sn, title, source, body = (
            entry.get("DataSN"), entry.get("title"),
            entry.get("Source"), entry.get("內容"),
        )
        if not isinstance(sn, str) or not re.fullmatch(r"[0-9]{1,12}", sn):
            raise SourceHold("HOLD_DATASN")
        if sn in seen:
            raise SourceHold("HOLD_DUPLICATE_DATASN")
        seen.add(sn)
        if not isinstance(title, str) or not title.strip() or len(title) > 250:
            raise SourceHold("HOLD_TITLE")
        if not _source_url_ok(source):
            raise SourceHold("HOLD_OFFICIAL_SOURCE_URL")
        if not isinstance(body, str) or len(body) > MAX_CONTENT_CHARS:
            raise SourceHold("HOLD_CONTENT")
        platform = _platform_claim(body)
        rows.append({
            "venue_source_key_hash": hashlib.sha256(
                (sn + "\n" + source).encode("utf-8")
            ).hexdigest()[:20],
            "venue_source_id_kind": "TAIPEI_ARENA_DATASN",
            "ticket_event_id": None,
            "ticket_event_url": None,
            "ticket_platform_claim": platform,
            "ticket_platform_evidence": (
                "EXPLICIT_VENUE_LABEL_REVIEW" if platform
                else "HOLD_NO_UNIQUE_EXPLICIT_LABEL"
            ),
            "event_date": None,
            "sale_date": None,
            "admission_date": None,
            "registration_date": None,
            "voucher_date": None,
            "price": None,
            "session": None,
            "field_status": "HOLD_SEMANTIC_ROLES_NOT_VERIFIED",
            "identity_status": "REVIEW_VENUE_ANNOUNCEMENT_ONLY",
        })
    counts = Counter(r["ticket_platform_claim"] or "UNKNOWN" for r in rows)
    return {
        "gate": "P30-VENUE-01",
        "source": "TAIPEI_ARENA_OFFICIAL_OPENDATA",
        "decision": "REVIEW_SOURCE_ANNOUNCEMENTS_ONLY_NO_TICKET_IDENTITY",
        "announcement_count": len(rows),
        "platform_claim_counts": dict(sorted(counts.items())),
        "records": rows,
        "golden_accepted": 0,
        "published": False,
        "hard_hold_no_publication": True,
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_once() -> dict:
    # Exactly one explicit HTTPS GET. No redirects, retry, cookies, login or JS.
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(
        ENDPOINT,
        headers={"User-Agent": "EventRadarVenueReadOnly/1.0", "Accept": "application/json"},
        method="GET",
    )
    try:
        with opener.open(request, timeout=12) as response:
            if response.status != 200 or response.geturl() != ENDPOINT:
                raise SourceHold("HOLD_HTTP_STATUS_OR_REDIRECT")
            media_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if media_type != "application/json":
                raise SourceHold("HOLD_CONTENT_TYPE")
            raw = response.read(MAX_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise SourceHold("HOLD_HTTP_OR_NETWORK") from exc
    if len(raw) > MAX_BYTES:
        raise SourceHold("HOLD_BODY_CAP")
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SourceHold("HOLD_JSON_DECODE") from exc
    return inspect_payload(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="one explicit public GET; never CI")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline-only by default; use --live explicitly for one bounded GET")
    try:
        result = fetch_once()
    except SourceHold as exc:
        print(str(exc), file=sys.stderr)
        return 2
    # No raw HTML, title, source URL, query values, cookies or announcement timestamp.
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
