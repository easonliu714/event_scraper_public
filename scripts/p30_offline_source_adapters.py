"""Fixed KKTIX / ACCUPASS offline LIST->same-ID DETAIL review adapters.

Consumes only supplied, SHA-pinned local fixture bytes. Never requests a
website, accepts a formal field, writes a snapshot, or publishes activities.
Each adapter can be reused by the shared field evidence / isolated LKG Core.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

SOURCES = {
    "kktix": ("kktix.com", "events"),
    "accupass": ("www.accupass.com", "event"),
}
LIMIT = 2_000_000
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")


def _canonical_event_url(provider, href):
    """Keep only exact provider event IDs; reject redirects and cross-host aliases."""
    host, prefix = SOURCES[provider]
    if not isinstance(href, str):
        return None
    url = urlsplit(urljoin("https://" + host + "/", href))
    if (url.scheme != "https" or url.hostname != host or url.port is not None
            or url.username is not None or url.password is not None
            or url.query or url.fragment):
        return None
    path = url.path.split("/")
    if len(path) != 3 or path[0] != "" or path[1] != prefix:
        return None
    sid = path[2]
    if not IDENTIFIER.fullmatch(sid):
        return None
    return sid, "https://" + host + "/" + prefix + "/" + sid


def _read_fixture(root, relative):
    """Fail closed on path traversal, symlinks, directories and oversized files."""
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("SOURCE_FIXTURE_PATH_HOLD")
    base = Path(root).resolve(strict=True)
    candidate = base / relative
    if not candidate.resolve().is_relative_to(base):
        raise ValueError("SOURCE_FIXTURE_PATH_HOLD")
    segment = base
    for part in Path(relative).parts:
        if part in (".", "..") or segment.joinpath(part).is_symlink():
            raise ValueError("SOURCE_FIXTURE_PATH_HOLD")
        segment = segment / part
    if not candidate.is_file() or candidate.stat().st_size > LIMIT:
        raise ValueError("SOURCE_FIXTURE_IO_HOLD")
    return candidate.read_bytes()


def _receipt(body, receipt, url):
    if (not isinstance(receipt, dict)
            or receipt.get("evidence_class") != "SEALED_OFFLINE_FIXTURE_ONLY"
            or receipt.get("source_url") != url
            or receipt.get("body_sha256") != hashlib.sha256(body).hexdigest()):
        raise ValueError("SOURCE_RECEIPT_PROVENANCE_HOLD")
    stamp = receipt.get("observed_at")
    try:
        observed = datetime.fromisoformat(stamp)
    except (ValueError, TypeError):
        raise ValueError("SOURCE_RECEIPT_TIME_HOLD") from None
    if observed.utcoffset() is None:
        raise ValueError("SOURCE_RECEIPT_TIME_HOLD")
    return stamp


def _owned_list(provider, body):
    soup = BeautifulSoup(body, "html.parser")
    found = {}
    for link in soup.select("a[href]"):
        parsed = _canonical_event_url(provider, link.get("href"))
        if parsed is None:
            continue
        sid, detail_url = parsed
        if provider == "kktix":
            name_node = link.select_one(".name")
        else:
            name_node = link.select_one("h3")
        name = (link.get("title") or
                (name_node.get_text(" ", strip=True) if name_node else "") or
                link.get_text(" ", strip=True)).strip()
        name = " ".join(name.split())
        if not name or len(name) > 300:
            continue
        # Duplicate event IDs with conflicting titles must not override the
        # earlier source-owned identity.
        if sid in found and found[sid]["title"] != name:
            raise ValueError("SOURCE_LIST_DUPLICATE_IDENTITY_HOLD")
        found[sid] = {"id": sid, "title": name, "url": detail_url}
    return found


def _field(value, role, sid, url, stamp, sha, decision, reason):
    return {"value": value, "role": role, "event_id": sid,
            "source_url": url, "observed_at": stamp,
            "source_body_sha256": sha, "decision": decision,
            "hold_reason": reason}


def replay_offline_sources(manifest, fixture_root):
    """Build a non-publishing two-provider review ledger from sealed fixtures."""
    if (not isinstance(manifest, dict) or set(manifest) != {"mode", "sources"}
            or manifest["mode"] != "SEALED_OFFLINE_REPLAY_ONLY"
            or not isinstance(manifest["sources"], dict)
            or set(manifest["sources"]) != set(SOURCES)):
        raise ValueError("SOURCE_DUAL_ADAPTER_MANIFEST_HOLD")
    rows, holds, states = {}, {}, {}
    for provider in SOURCES:
        entry = manifest["sources"][provider]
        if (not isinstance(entry, dict)
                or set(entry) != {"list_file", "list_receipt", "details"}
                or not isinstance(entry["details"], dict)
                or len(entry["details"]) > 20):
            raise ValueError("SOURCE_ADAPTER_INPUT_SCHEMA_HOLD")
        list_url = "https://" + SOURCES[provider][0] + "/"
        try:
            raw = _read_fixture(fixture_root, entry["list_file"])
            _receipt(raw, entry["list_receipt"], list_url)
            cards = _owned_list(provider, raw)
        except (ValueError, OSError) as exc:
            holds[provider] = str(exc)
            states[provider] = "HOLD_LIST"
            continue
        if not cards:
            holds[provider] = "SOURCE_EMPTY_LIST_HOLD"
            states[provider] = "HOLD_EMPTY_LIST"
            continue
        states[provider] = "REVIEW_IDENTITY_ONLY"
        for sid in entry["details"]:
            if sid not in cards:
                raise ValueError("SOURCE_DETAIL_ID_NOT_IN_LIST_HOLD")
        for sid, card in cards.items():
            identity = provider + ":" + sid
            record = entry["details"].get(sid)
            if record is None:
                holds[identity] = "SOURCE_DETAIL_NOT_PROVIDED_HOLD"
                continue
            if (not isinstance(record, dict)
                    or set(record) != {"detail_file", "receipt"}):
                raise ValueError("SOURCE_DETAIL_SCHEMA_HOLD")
            try:
                detail = _read_fixture(fixture_root, record["detail_file"])
                stamp = _receipt(detail, record["receipt"], card["url"])
                article = BeautifulSoup(detail, "html.parser")
                heads = [node for node in article.select("h1")
                         if node.get_text(" ", strip=True)]
                if len(heads) != 1:
                    raise ValueError("SOURCE_DETAIL_TITLE_AMBIGUOUS_HOLD")
                actual = " ".join(heads[0].get_text(" ", strip=True).split())
                if actual != card["title"]:
                    raise ValueError("SOURCE_LIST_DETAIL_TITLE_PARITY_HOLD")
            except (ValueError, OSError) as exc:
                holds[identity] = str(exc)
                continue
            sha = hashlib.sha256(detail).hexdigest()
            fields = {"title": _field(
                actual, "EVENT_TITLE", sid, card["url"], stamp, sha,
                "REVIEW", "SOURCE_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE")}
            for name in ("date", "show_start", "price", "venue", "image"):
                fields[name] = _field(
                    None, "UNKNOWN", sid, card["url"], stamp, sha,
                    "HOLD", "SOURCE_FIELD_ROLE_NOT_VERIFIED")
            rows[identity] = {
                "identity": identity, "source_namespace": provider,
                "event_id": sid, "detail_source_url": card["url"],
                "archive_evidence_current": False,
                "fields": fields, "decision": "REVIEW_ONLY_NO_FIELD_ACCEPTANCE",
            }
    return {
        "kind": "MULTI_SOURCE_OFFLINE_FIELD_EVIDENCE_V1",
        "scope": "SEALED_OFFLINE_REPLAY_ONLY",
        "records": rows, "holds": holds, "source_states": states,
        "counts": {"review_identities": len(rows), "sources": len(SOURCES)},
        "new_official_get": 0, "accepted_fields": 0, "published": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline two-source LIST+DETAIL; no GET/publish")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--fixture-root", required=True, type=Path)
    args = parser.parse_args(argv)
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = replay_offline_sources(data, args.fixture_root)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
