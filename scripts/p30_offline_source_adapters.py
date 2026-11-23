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



def _structured_event_fields(article, provider, sid, title, detail_url, stamp, sha):
    """Extract only unambiguous same-event JSON-LD startDate and venue as REVIEW.

    JSON-LD is untrusted archived HTML: no cross-event, timezone-naive,
    multiple Event, or incomplete venue inference is allowed.
    """
    # Keep each Event bound to its own JSON-LD document. An @id from a
    # different script is not evidence that the Event owns that Place.
    matches = []
    for node in article.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.string or node.get_text())
        except (ValueError, TypeError):
            continue
        # Archived schema.org pages commonly wrap Event nodes in @graph.
        # Inspect only the top-level graph (never arbitrary nested objects),
        # and require a single exact same-ID event before admitting fields.
        roots = data if isinstance(data, list) else [data]
        objects = []
        for root in roots:
            if not isinstance(root, dict):
                continue
            objects.append(root)
            graph = root.get("@graph")
            if isinstance(graph, list):
                objects.extend(node for node in graph if isinstance(node, dict))
        for obj in objects:
            kinds = obj.get("@type")
            if not (kinds == "Event" or
                    isinstance(kinds, list) and kinds.count("Event") == 1):
                continue
            parsed = _canonical_event_url(provider, obj.get("url"))
            if (parsed != (sid, detail_url)
                    or " ".join(str(obj.get("name", "")).split()) != title):
                continue
            matches.append((obj, objects))
    if len(matches) != 1:
        return {}
    obj, same_document_objects = matches[0]
    # A structurally invalid Event startDate invalidates this JSON-LD event
    # as a field-evidence source; do not retain a venue REVIEW from the same
    # malformed event while show_start is HOLD.
    start = obj.get("startDate")
    if not isinstance(start, str):
        return {}
    try:
        dt = datetime.fromisoformat(start)
    except ValueError:
        return {}
    if dt.utcoffset() is None:
        return {}
    fields = {"show_start": _field(
        start, "EVENT_SHOW_START", sid, detail_url, stamp, sha,
        "REVIEW", "SOURCE_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE")}
    # JSON-LD may reference a Place by @id in the same local @graph.
    # Resolve only one exact graph-local Place; never dereference remote URLs
    # or infer a venue from a different event or an ambiguous graph node.
    location = obj.get("location")
    if isinstance(location, dict) and set(location) == {"@id"}:
        reference = location.get("@id")
        places = []
        if isinstance(reference, str) and reference:
            for candidate in same_document_objects:
                kinds = candidate.get("@type")
                is_place = (kinds == "Place" or
                            isinstance(kinds, list) and kinds.count("Place") == 1)
                if (candidate is not obj and candidate.get("@id") == reference
                        and is_place):
                    places.append(candidate)
        if len(places) == 1:
            location = places[0]
        else:
            location = None
    if isinstance(location, dict) and location.get("@type") == "Place":
        name = location.get("name")
        if isinstance(name, str) and 0 < len(name.strip()) <= 200:
            fields["venue"] = _field(
                " ".join(name.split()), "EVENT_VENUE", sid, detail_url,
                stamp, sha, "REVIEW", "SOURCE_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE")
    return fields


def replay_offline_sources(manifest, fixture_root):
    """Build a non-publishing two-provider review ledger from sealed fixtures."""
    if (not isinstance(manifest, dict) or set(manifest) != {"mode", "sources"}
            or manifest["mode"] != "SEALED_OFFLINE_REPLAY_ONLY"
            or not isinstance(manifest["sources"], dict)
            or set(manifest["sources"]) != set(SOURCES)):
        raise ValueError("SOURCE_DUAL_ADAPTER_MANIFEST_HOLD")
    rows, holds, states, listed = {}, {}, {}, {provider: [] for provider in SOURCES}
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
        # A DETAIL HOLD may preserve an existing identity only if the latest
        # verified LIST still explicitly contains its provider-owned ID.
        listed[provider] = [provider + ":" + sid for sid in sorted(cards)]
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
            fields.update(_structured_event_fields(article, provider, sid, actual, card["url"], stamp, sha))
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
        "listed_identities": listed,
        "counts": {"review_identities": len(rows), "sources": len(SOURCES)},
        "new_official_get": 0, "accepted_fields": 0, "published": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }


# Shared Candidate/Core integration: the existing provenance validator is reused
# rather than introducing a second, weaker field admission contract.
def _candidate_rows(report):
    from scripts.p30_tpac_multi_event_refresh import _validate_archived_candidate_snapshot_row
    if (not isinstance(report, dict)
            or report.get("kind") != "MULTI_SOURCE_OFFLINE_FIELD_EVIDENCE_V1"
            or report.get("scope") != "SEALED_OFFLINE_REPLAY_ONLY"
            or report.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
            or report.get("new_official_get") != 0
            or report.get("accepted_fields") != 0 or report.get("published") != 0
            or not isinstance(report.get("records"), dict)
            or not isinstance(report.get("holds"), dict)
            or not isinstance(report.get("source_states"), dict)
            or set(report["source_states"]) != set(SOURCES)
            or not isinstance(report.get("listed_identities"), dict)
            or set(report["listed_identities"]) != set(SOURCES)
            or any(not isinstance(report["listed_identities"][provider], list)
                   or len(set(report["listed_identities"][provider])) !=
                       len(report["listed_identities"][provider])
                   or any(not isinstance(identity, str)
                          or not identity.startswith(provider + ":")
                          or not IDENTIFIER.fullmatch(identity[len(provider) + 1:])
                          for identity in report["listed_identities"][provider])
                   for provider in SOURCES)):
        raise ValueError("SOURCE_CANDIDATE_AUTHORITY_HOLD")
    rows = {}
    for identity, record in sorted(report["records"].items()):
        if (not isinstance(record, dict)
                or identity != record.get("identity")
                or record.get("source_namespace") not in SOURCES
                or identity != record["source_namespace"] + ":" + str(record.get("event_id"))
                or record.get("archive_evidence_current") is not False
                or record.get("decision") != "REVIEW_ONLY_NO_FIELD_ACCEPTANCE"
                or not isinstance(record.get("fields"), dict)):
            raise ValueError("SOURCE_CANDIDATE_IDENTITY_HOLD")
        url = _canonical_event_url(record["source_namespace"], record.get("detail_source_url"))
        if url is None or url[0] != record["event_id"] or url[1] != record["detail_source_url"]:
            raise ValueError("SOURCE_CANDIDATE_SOURCE_URL_HOLD")
        accepted, held = {}, {}
        for name, field in sorted(record["fields"].items()):
            if (not isinstance(field, dict) or field.get("event_id") != record["event_id"]
                    or field.get("source_url") != url[1]
                    or not isinstance(field.get("observed_at"), str)
                    or not isinstance(field.get("source_body_sha256"), str)
                    or re.fullmatch(r"[0-9a-f]{64}", field["source_body_sha256"]) is None
                    or not isinstance(field.get("hold_reason"), str)
                    or not field["hold_reason"]):
                raise ValueError("SOURCE_CANDIDATE_FIELD_PROVENANCE_HOLD")
            if field.get("decision") == "REVIEW" and field.get("value") is not None:
                accepted[name] = dict(field, decision="REVIEW_ONLY_NOT_ACCEPTED")
            elif field.get("decision") == "HOLD" and field.get("value") is None:
                held[name] = dict(field)
            else:
                raise ValueError("SOURCE_CANDIDATE_FIELD_AUTHORITY_HOLD")
        row = {"identity": identity, "source_namespace": record["source_namespace"],
               "event_id": record["event_id"], "detail_source_url": url[1],
               "fields": accepted, "held_fields": held, "source_current": False,
               "decision": "ISOLATED_REVIEW_CANDIDATE_ONLY"}
        _validate_archived_candidate_snapshot_row(identity, row, "SOURCE_CANDIDATE_CORE_HOLD")
        rows[identity] = row
    return rows


def _candidate_canonical(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def commit_offline_candidate_lkg(report, root, expected_sha=None):
    """Non-destructive, locked CAS of two provider-namespaced Candidate ledgers.

    Failed source replays retain their prior candidate, never replace it with
    an empty source result. Historical versions remain available for rollback.
    """
    import os
    import tempfile
    from scripts.p30_tpac_multi_event_refresh import (
        _isolated_writer_lock, _validate_archived_candidate_snapshot_row)
    rows = _candidate_rows(report)
    if expected_sha is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ValueError("SOURCE_CANDIDATE_EXPECTED_SHA_HOLD")
    root = Path(root).resolve()
    directory = root / "_isolated_multi_source_candidates"
    if directory.is_symlink():
        raise ValueError("SOURCE_CANDIDATE_SYMLINK_HOLD")
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "candidate_lkg.json"
    if target.is_symlink():
        raise ValueError("SOURCE_CANDIDATE_SYMLINK_HOLD")
    with _isolated_writer_lock(directory / ".candidate.lock", "SOURCE_CANDIDATE_WRITER_HOLD"):
        prior = target.read_bytes() if target.exists() else None
        actual = hashlib.sha256(prior).hexdigest() if prior is not None else None
        if actual != expected_sha:
            raise ValueError("SOURCE_CANDIDATE_CAS_HOLD")
        if prior is not None:
            try:
                old = json.loads(prior)
                if (_candidate_canonical(old) != prior
                        or old.get("kind") != "MULTI_SOURCE_ISOLATED_CANDIDATE_LKG_V1"
                        or old.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
                        or old.get("accepted_fields") != 0 or old.get("published") != 0
                        or not isinstance(old.get("candidates"), dict)):
                    raise ValueError("SOURCE_CANDIDATE_PRIOR_CORRUPT_HOLD")
                for identity, row in old["candidates"].items():
                    _validate_archived_candidate_snapshot_row(
                        identity, row, "SOURCE_CANDIDATE_PRIOR_FIELD_HOLD")
                    provider = row["source_namespace"]
                    if identity in rows:
                        if any(row.get(k) != rows[identity].get(k) for k in
                               ("source_namespace", "event_id", "detail_source_url")):
                            raise ValueError("SOURCE_CANDIDATE_IDENTITY_SWAP_HOLD")
                    elif report["source_states"][provider] == "REVIEW_IDENTITY_ONLY":
                        # A healthy LIST may include a known ID whose DETAIL
                        # is absent/invalid. It is not a deletion: retain the
                        # identity and immutable historical provenance, but
                        # withdraw *all* old REVIEW values from current use.
                        # A missing ID from the verified LIST still fails closed.
                        held_reason = report["holds"].get(identity)
                        allowed = {
                            "SOURCE_DETAIL_NOT_PROVIDED_HOLD",
                            "SOURCE_FIXTURE_IO_HOLD",
                            "SOURCE_FIXTURE_PATH_HOLD",
                            "SOURCE_RECEIPT_PROVENANCE_HOLD",
                            "SOURCE_RECEIPT_TIME_HOLD",
                            "SOURCE_DETAIL_TITLE_AMBIGUOUS_HOLD",
                            "SOURCE_LIST_DETAIL_TITLE_PARITY_HOLD",
                        }
                        if (identity not in report["listed_identities"][provider]
                                or held_reason not in allowed):
                            raise ValueError("SOURCE_CANDIDATE_DESTRUCTIVE_REMOVAL_HOLD")
                        pending = dict(row)
                        pending["fields"] = {}
                        pending["held_fields"] = {
                            name: {**field, "value": None,
                                   "role": "UNKNOWN", "decision": "HOLD",
                                   "hold_reason": held_reason}
                            for name, field in {**row["held_fields"], **row["fields"]}.items()
                        }
                        pending["detail_replay_hold_reason"] = held_reason
                        _validate_archived_candidate_snapshot_row(
                            identity, pending, "SOURCE_CANDIDATE_DETAIL_HOLD")
                        rows[identity] = pending
                    else:
                        rows[identity] = row
            except (TypeError, UnicodeError, json.JSONDecodeError) as exc:
                raise ValueError("SOURCE_CANDIDATE_PRIOR_CORRUPT_HOLD") from exc
        if not rows:
            raise ValueError("SOURCE_CANDIDATE_EMPTY_HOLD")
        snapshot = {"kind": "MULTI_SOURCE_ISOLATED_CANDIDATE_LKG_V1",
                    "candidates": rows, "release_state": "HARD_HOLD_NO_PUBLICATION",
                    "accepted_fields": 0, "published": 0}
        payload = _candidate_canonical(snapshot)
        digest = hashlib.sha256(payload).hexdigest()
        versions = directory / "versions"
        if versions.is_symlink():
            raise ValueError("SOURCE_CANDIDATE_SYMLINK_HOLD")
        versions.mkdir(exist_ok=True)
        # Keep immutable version files for an explicit CAS-controlled rollback.
        version = versions / (digest + ".json")
        if version.is_symlink():
            raise ValueError("SOURCE_CANDIDATE_SYMLINK_HOLD")
        if version.exists():
            if version.read_bytes() != payload:
                raise ValueError("SOURCE_CANDIDATE_VERSION_COLLISION_HOLD")
        else:
            with version.open("xb") as out:
                out.write(payload)
                out.flush()
                os.fsync(out.fileno())
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=directory, prefix=".candidate-",
                                             delete=False) as out:
                temp = Path(out.name)
                out.write(payload)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, target)
            temp = None
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        return {"sha256": digest, "events": len(rows),
                "decision": "ISOLATED_MULTI_SOURCE_CANDIDATE_COMMITTED_NOT_FORMAL",
                "accepted_fields": 0, "published": 0}


def load_offline_candidate_lkg(root, expected_sha):
    """Restart readback validates both canonical bytes and shared Core fields."""
    from scripts.p30_tpac_multi_event_refresh import _validate_archived_candidate_snapshot_row
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ValueError("SOURCE_CANDIDATE_READ_SHA_HOLD")
    directory = Path(root).resolve() / "_isolated_multi_source_candidates"
    target = directory / "candidate_lkg.json"
    if directory.is_symlink() or target.is_symlink() or not target.is_file():
        raise ValueError("SOURCE_CANDIDATE_READ_PATH_HOLD")
    raw = target.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("SOURCE_CANDIDATE_READ_CAS_HOLD")
    try:
        snapshot = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("SOURCE_CANDIDATE_READ_SCHEMA_HOLD") from exc
    if (_candidate_canonical(snapshot) != raw
            or set(snapshot) != {"kind", "candidates", "release_state",
                                 "accepted_fields", "published"}
            or snapshot["kind"] != "MULTI_SOURCE_ISOLATED_CANDIDATE_LKG_V1"
            or snapshot["release_state"] != "HARD_HOLD_NO_PUBLICATION"
            or snapshot["accepted_fields"] != 0 or snapshot["published"] != 0
            or not isinstance(snapshot["candidates"], dict)):
        raise ValueError("SOURCE_CANDIDATE_READ_SCHEMA_HOLD")
    for identity, row in snapshot["candidates"].items():
        _validate_archived_candidate_snapshot_row(identity, row, "SOURCE_CANDIDATE_READ_FIELD_HOLD")
    return snapshot


def rollback_offline_candidate_lkg(root, archived_sha, expected_current_sha):
    """Restore an archived version only after exact current-state CAS."""
    directory = Path(root).resolve() / "_isolated_multi_source_candidates"
    version = directory / "versions" / (archived_sha + ".json")
    if (not isinstance(archived_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", archived_sha)
            or directory.is_symlink() or version.is_symlink() or not version.is_file()):
        raise ValueError("SOURCE_CANDIDATE_ROLLBACK_VERSION_HOLD")
    raw = version.read_bytes()
    if hashlib.sha256(raw).hexdigest() != archived_sha:
        raise ValueError("SOURCE_CANDIDATE_ROLLBACK_HASH_HOLD")
    historical = json.loads(raw)
    # Reuse the normal admission path, without trusting historical filenames.
    report = {"kind": "MULTI_SOURCE_OFFLINE_FIELD_EVIDENCE_V1",
              "scope": "SEALED_OFFLINE_REPLAY_ONLY",
              "records": {}, "source_states": {p: "HOLD_LIST" for p in SOURCES},
              "new_official_get": 0, "accepted_fields": 0, "published": 0,
              "release_state": "HARD_HOLD_NO_PUBLICATION"}
    from scripts.p30_tpac_multi_event_refresh import _isolated_writer_lock
    import os
    import tempfile
    with _isolated_writer_lock(directory / ".candidate.lock", "SOURCE_CANDIDATE_WRITER_HOLD"):
        target = directory / "candidate_lkg.json"
        if target.is_symlink() or not target.is_file():
            raise ValueError("SOURCE_CANDIDATE_ROLLBACK_PATH_HOLD")
        current = target.read_bytes()
        if hashlib.sha256(current).hexdigest() != expected_current_sha:
            raise ValueError("SOURCE_CANDIDATE_ROLLBACK_CAS_HOLD")
        load_offline_candidate_lkg(root, expected_current_sha)
        if (_candidate_canonical(historical) != raw
                or historical.get("kind") != "MULTI_SOURCE_ISOLATED_CANDIDATE_LKG_V1"
                or historical.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
                or historical.get("accepted_fields") != 0 or historical.get("published") != 0):
            raise ValueError("SOURCE_CANDIDATE_ROLLBACK_SCHEMA_HOLD")
        from scripts.p30_tpac_multi_event_refresh import _validate_archived_candidate_snapshot_row
        for identity, row in historical["candidates"].items():
            _validate_archived_candidate_snapshot_row(identity, row, "SOURCE_CANDIDATE_ROLLBACK_FIELD_HOLD")
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=directory, prefix=".rollback-", delete=False) as out:
                temp = Path(out.name)
                out.write(raw)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, target)
            temp = None
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
    return {"sha256": archived_sha, "decision": "ISOLATED_ROLLBACK_NOT_FORMAL"}

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
