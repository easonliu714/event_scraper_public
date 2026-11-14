"""Reusable TPAC multi-event source parser and isolated refresh planner.

The source bytes/receipts are caller-supplied, not an independent native HTTP
attestation. This module performs NO GET, NO formal data/Golden write, and NO
recurring Publisher/Scheduler activation. An independent source-readback and
separate publication Gate must authorize any formal release.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from scripts.p30_tpac_price_reconcile import extract_tpac_price_review

ROOT = "https://tpac.org.taipei/program"
KIND = "TPAC_SOURCE_OWNED_MULTI_EVENT_REVIEW_V1"
TIMEZONE = timezone(timedelta(hours=8))
DAY = "一二三四五六日"
SHOW = re.compile(r"^(20\d{2}-\d{2}-\d{2})\s*\(([一二三四五六日])\)\s*([0-2]\d:[0-5]\d)$")
PERIOD = re.compile(r"^(20\d{2}-\d{2}-\d{2})\s*[-–]\s*(20\d{2}-\d{2}-\d{2})$")
PATH = re.compile(r"^/program/([1-9]\d{0,9})$")
MAX_BODY = 2 * 1024 * 1024
MAX_CARDS = 150
MAX_DETAILS = 30


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _text(node):
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def _time(value):
    if not isinstance(value, str):
        raise ValueError("TPAC_OBSERVED_TIME_MISSING_HOLD")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError("TPAC_OBSERVED_TIME_INVALID_HOLD") from e
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("TPAC_OBSERVED_TIMEZONE_HOLD")
    return stamp.astimezone(timezone.utc)


def _body(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BODY:
        raise ValueError("TPAC_BODY_CAP_OR_TYPE_HOLD")
    try:
        return BeautifulSoup(raw.decode("utf-8", "strict"), "html.parser")
    except UnicodeError as e:
        raise ValueError("TPAC_BODY_UTF8_HOLD") from e


def _visible(node):
    for parent in (node, *node.parents):
        if parent.name in ("template", "noscript", "script", "style"):
            return False
        if parent.attrs.get("hidden") is not None or parent.attrs.get("aria-hidden") == "true":
            return False
        if re.search(r"display\s*:\s*none", parent.attrs.get("style", ""), re.I):
            return False
    return True


def _receipt(raw, receipt, url, now):
    if not isinstance(receipt, dict):
        raise ValueError("TPAC_RECEIPT_MISSING_HOLD")
    # Fixture-marked receipts cannot masquerade as native source evidence.
    if receipt.get("offline_fixture_replay") is True:
        raise ValueError("TPAC_OFFLINE_FIXTURE_NOT_NATIVE_RECEIPT_HOLD")
    observed = _time(receipt.get("observed_at"))
    if now < observed - timedelta(minutes=2) or now - observed > timedelta(hours=24):
        raise ValueError("TPAC_SOURCE_STALE_OR_FUTURE_HOLD")
    if (receipt.get("http_status") != 200 or
            receipt.get("final_url") != url or
            receipt.get("robots_allowed") is not True or
            receipt.get("body_sha256") != _sha(raw) or
            receipt.get("body_bytes") != len(raw)):
        raise ValueError("TPAC_RECEIPT_STATUS_URL_ROBOTS_SHA_HOLD")
    return observed


def _period(label):
    m = PERIOD.fullmatch(label)
    if not m:
        raise ValueError("TPAC_PERIOD_LABEL_HOLD")
    from datetime import date
    start, end = date.fromisoformat(m[1]), date.fromisoformat(m[2])
    if start > end:
        raise ValueError("TPAC_PERIOD_REVERSED_HOLD")
    return start, end


def discover_list(raw, receipt, now):
    """Find all unique, visible, exact first-party TPAC programme cards."""
    now = now.astimezone(timezone.utc)
    _receipt(raw, receipt, ROOT, now)
    soup = _body(raw)
    cards = soup.select("a.card-program[href][title]")
    if not 1 <= len(cards) <= MAX_CARDS:
        raise ValueError("TPAC_EMPTY_OR_OVER_CAP_LIST_HOLD")
    results = {}
    for card in cards:
        if not _visible(card):
            continue
        href = card.get("href", "")
        full = urljoin(ROOT, href)
        url = urlsplit(full)
        m = PATH.fullmatch(url.path)
        if not m or url.scheme != "https" or url.netloc != "tpac.org.taipei" or url.query or url.fragment:
            continue
        sid = m[1]
        title = card["title"].strip()
        owned = _text(card.select_one(".card-program__text-title"))
        if not 3 <= len(title) <= 180 or title != owned:
            raise ValueError("TPAC_LIST_TITLE_OWNERSHIP_HOLD")
        if sid in results:
            raise ValueError("TPAC_LIST_DUPLICATE_SOURCE_ID_HOLD")
        results[sid] = {
            "source_event_id": sid, "title": title, "url": full,
            "period": _text(card.select_one(".card-program__text-date")),
            "list_sha256": _sha(raw),
            "observed_at": _time(receipt["observed_at"]).isoformat(),
        }
    if not results:
        raise ValueError("TPAC_NO_VALID_FIRST_PARTY_CARD_HOLD")
    return results


def _venue_role_review(soup):
    """Strict event-owned physical space + separate start-area note, REVIEW only.

    A page-wide venue mention or performance starting area is not an address,
    ticket product, showtime, or independently accepted formal location.
    """
    containers = soup.select("div.page-program__aside-place")
    blocks = soup.select("div.page-program__aside-place-venue")
    if (len(containers) != 1 or len(blocks) != 1
            or blocks[0].find_parent("div", class_="page-program__aside-place") is not containers[0]
            or not _visible(blocks[0])):
        raise ValueError("TPAC_VENUE_EXACT_EVENT_SCOPE_HOLD")
    block = blocks[0]
    headings = block.find_all("h3", recursive=False)
    spaces = block.find_all("p", recursive=False)
    notes = block.find_all("div", recursive=False)
    if (len(headings) != 1 or _text(headings[0]) != "場地"
            or len(spaces) != 1 or len(notes) > 1):
        raise ValueError("TPAC_VENUE_LABEL_OR_ROLE_HOLD")
    space = _text(spaces[0])
    note = _text(notes[0]) if notes else ""
    if (not 1 <= len(space) <= 80 or len(note) > 180
            or any(c in space + note for c in "<>\r\n")
            or "http" in (space + note).lower()):
        raise ValueError("TPAC_VENUE_VALUE_HOLD")
    return {"role": "EVENT_VENUE_SPACE", "value": space,
            "start_area_note": note,
            "start_area_role": "EVENT_START_AREA_NOTE_NOT_SHOWTIME",
            "decision": "REVIEW_REQUIRES_INDEPENDENT_ACCEPTANCE"}


def parse_detail(card, body, receipt, now):
    """Parse exact-ID DETAIL and event-owned SHOW roles; ambiguous fields HOLD."""
    url = card["url"]
    observed = _receipt(body, receipt, url, now)
    soup = _body(body)
    articles = [a for a in soup.select("article.page-program__article") if _visible(a)]
    if len(articles) != 1 or len(articles[0].select("h1")) != 1:
        raise ValueError("TPAC_DETAIL_ARTICLE_SCOPE_HOLD")
    if _text(articles[0].select_one("h1")) != card["title"]:
        raise ValueError("TPAC_EXACT_ID_TITLE_PARITY_HOLD")
    detail_period = _period(_text(articles[0].select_one(".page-program__article-top")))
    blocks = [e for e in soup.select(".page-program__aside-place-showtimes")
              if _visible(e) and len(e.select("h3")) == 1 and _text(e.select_one("h3")) == "場次"]
    if len(blocks) != 1:
        raise ValueError("TPAC_SHOW_SECTION_HOLD")
    labels = blocks[0].select("ul > li > p")
    if not 1 <= len(labels) <= 40:
        raise ValueError("TPAC_SHOW_COUNT_HOLD")
    times = []
    for node in labels:
        m = SHOW.fullmatch(_text(node))
        if not m:
            raise ValueError("TPAC_SHOW_LABEL_OR_ROLE_HOLD")
        start = datetime.fromisoformat(m[1] + "T" + m[3] + ":00+08:00")
        if DAY[start.weekday()] != m[2] or not detail_period[0] <= start.date() <= detail_period[1]:
            raise ValueError("TPAC_SHOW_WEEKDAY_OR_PERIOD_HOLD")
        times.append(start)
    if times != sorted(set(times)):
        raise ValueError("TPAC_SHOW_ORDER_OR_DUPLICATE_HOLD")
    upcoming = [t for t in times if t.astimezone(timezone.utc) > now]
    if not upcoming:
        raise ValueError("TPAC_NO_FUTURE_SHOW_HOLD")
    if upcoming[0].astimezone(timezone.utc) > now + timedelta(days=370):
        raise ValueError("TPAC_FUTURE_SHOW_OUT_OF_RANGE_HOLD")
    # Admission price is a separate source-owned field role. Do not fail
    # the accepted title/showtime just because price is unknown, conditional,
    # or needs independent field publication authority.
    admission = extract_tpac_price_review(
        body, receipt, card["source_event_id"], card["title"])
    # Independent source-owned role parsing cannot authorize formal location.
    try:
        venue_review = _venue_role_review(soup)
    except ValueError as exc:
        venue_review = None
        venue_hold = str(exc)
    else:
        venue_hold = "VENUE_SPACE_REQUIRES_INDEPENDENT_FIELD_ACCEPTANCE"
    holds = ["HALL_NOT_VERIFIED", "LOCATION_NOT_EVENT_VERIFIED", venue_hold]
    if admission.get("decision") == "SOURCE_PRICE_ROLE_REVIEW_NOT_FORMAL":
        holds.append("PRICE_REQUIRES_INDEPENDENT_FIELD_ACCEPTANCE")
    else:
        holds.append("PRICE_NOT_VERIFIED")
    try:
        if _period(card["period"]) != detail_period:
            holds.append("LIST_DETAIL_PERIOD_CONFLICT_HOLD")
    except ValueError:
        holds.append("LIST_DATE_PERIOD_UNVERIFIED_HOLD")
    event = {
        "source_event_id": card["source_event_id"],
        "title": card["title"], "url": url,
        "platform": "臺北表演藝術中心", "type": "戲劇",
        "date": upcoming[0].strftime("%Y-%m-%d %H:%M"),
        # Publisher identity does not prove the event-owned physical venue.
        # Keep location unknown until independent same-event venue evidence.
        "location": "", "price": "",
        "img_url": None,
        "scraped_at": observed.astimezone(TIMEZONE).isoformat(),
        "description": "官方場次：" + "、".join(t.strftime("%m/%d %H:%M") for t in upcoming) + "。票價與詳情以官方資訊為準。",
        "published": False, "formal_field_pass": False, "golden_accepted": False,
        "_candidate": {"scope": "REVIEW_ONLY_NOT_NATIVE_INDEPENDENTLY_ATTESTED",
                       "decision": "REVIEW", "hold_reasons": holds,
                       "sources": [ROOT, url],
                       "event_id": card["source_event_id"],
                       "source_list_sha256": card["list_sha256"],
                       "source_detail_sha256": _sha(body),
                       "observed_at": observed.isoformat(),
                       "field_roles": {
                           "title": {"role": "EVENT_TITLE", "value": card["title"], "source_url": url},
                           "date": {"role": "EVENT_SHOW_START", "value": upcoming[0].isoformat(), "source_url": url},
                       }},
    }
    if admission.get("decision") == "SOURCE_PRICE_ROLE_REVIEW_NOT_FORMAL":
        # This is useful evidence for a future governed Publisher, but it is
        # not itself authorization to display or publish a numeric price.
        event["_candidate"]["price_review"] = admission
        event["_candidate"]["field_roles"]["price"] = {
            "role": admission["role"],
            "min_price_ntd": admission["min_price_ntd"],
            "max_price_ntd": admission["max_price_ntd"],
            "source_url": admission["source_url"],
            "source_body_sha256": admission["source_body_sha256"],
            "observed_at": admission["observed_at"],
            "decision": "REVIEW_REQUIRES_INDEPENDENT_ACCEPTANCE",
        }
    if venue_review is not None:
        event["_candidate"]["venue_review"] = {
            **venue_review, "source_url": url,
            "source_body_sha256": _sha(body),
            "observed_at": observed.isoformat(),
            "formal_field_pass": False, "published": False,
        }
        event["_candidate"]["field_roles"]["venue_space"] = {
            **venue_review, "source_url": url,
            "source_body_sha256": _sha(body),
            "observed_at": observed.isoformat(),
        }
    return event



def _semantic_event_payload(event):
    """Compare display-relevant source fields, never receipt/observation metadata.

    This is REVIEW-only diff accounting, not independent field acceptance.
    Unknown fields and authority flags remain outside this comparison and
    cannot grant Publisher eligibility.
    """
    if not isinstance(event, dict):
        raise ValueError("TPAC_SEMANTIC_EVENT_SCHEMA_HOLD")
    keys = ("source_event_id", "title", "url", "platform", "type",
            "date", "location", "price", "img_url", "description")
    return tuple((key, event.get(key)) for key in keys)


def refresh_plan(list_body, list_receipt, detail_pairs, prior, now):
    """Stage multi-event source-owned candidates, with no destructive removals.

    Missing/invalid detail receipts isolate per event. A complete source error
    returns the exact prior last-known-good as a HOLD, never an empty feed.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("TPAC_CLOCK_TIMEZONE_HOLD")
    now = now.astimezone(timezone.utc)
    if not isinstance(prior, dict) or prior.get("kind") != KIND or not isinstance(prior.get("events"), dict):
        raise ValueError("TPAC_PRIOR_LKG_SCHEMA_HOLD")
    old = prior["events"]
    if not isinstance(detail_pairs, dict) or len(detail_pairs) > MAX_DETAILS:
        raise ValueError("TPAC_DETAIL_INPUT_CAP_HOLD")
    report = {"kind": KIND, "decision": "HOLD", "previous_count": len(old),
              "new_count": len(old), "added": 0, "changed": 0, "unchanged": 0,
              "retained_previous": len(old), "source_cards": 0,
              "qualified": 0, "rejected": {}, "events": dict(old),
              "release_state": "HARD_HOLD_NO_PUBLICATION",
              "published": 0, "native_attestation": "REQUIRES_INDEPENDENT_READBACK"}
    try:
        cards = discover_list(list_body, list_receipt, now)
    except (ValueError, KeyError, TypeError, OverflowError) as e:
        report["decision"] = "HOLD_LIST_" + str(e)
        return report
    report["source_cards"] = len(cards)
    updated = dict(old)
    valid = 0
    adds = changes = same = 0
    for sid, card in cards.items():
        item = detail_pairs.get(sid)
        if not isinstance(item, dict):
            report["rejected"][sid] = "DETAIL_NOT_PROVIDED_HOLD"
            continue
        try:
            event = parse_detail(card, item["body"], item["receipt"], now)
        except (ValueError, KeyError, TypeError, OverflowError) as e:
            report["rejected"][sid] = str(e)
            continue
        valid += 1
        key = "tpac:" + sid
        if key not in updated:
            adds += 1
        elif _semantic_event_payload(updated[key]) == _semantic_event_payload(event):
            # An observation-only receipt refresh must not create a content delta.
            same += 1
            continue  # Preserve the prior LKG bytes and its provenance unchanged.
        else:
            changes += 1
        updated[key] = event
    if valid == 0:
        report["decision"] = "HOLD_NO_QUALIFIED_DETAILS_PRESERVE_LKG"
        return report
    qualified_ids = {"tpac:" + sid for sid in cards if sid not in report["rejected"]}
    report.update({"decision": "REVIEW_SNAPSHOT_READY_NOT_FORMAL",
                   "events": updated, "new_count": len(updated),
                   "added": adds, "changed": changes, "unchanged": same,
                   "retained_previous": sum(k not in qualified_ids for k in old),
                   "qualified": valid,
                   "source_coverage_complete": len(report["rejected"]) == 0 and valid == len(cards)})
    # Any unobserved/failed former event is retained; a separate verified
    # expiration Gate is required to remove it. Do NOT force old=0 on failure.
    return report



def refresh_event_plan(list_body, list_receipt, detail_pairs, prior, now):
    """Replay TPAC /event LIST + exact-ID DETAIL into nonpublication CAS LKG.

    /event activities have a separate identity namespace from /program shows.
    A missing DETAIL, conflicting period, or exhibition hours cannot create a
    fabricated performance date. Archived source receipts are not fresh GETs.
    """
    from scripts.p30_tpac_catalog_topology import discover_catalog
    from scripts.p30_tpac_event_detail_review import inspect_event_detail

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("TPAC_EVENT_CLOCK_TIMEZONE_HOLD")
    now = now.astimezone(timezone.utc)
    if (not isinstance(prior, dict) or prior.get("kind") != KIND
            or not isinstance(prior.get("events"), dict)):
        raise ValueError("TPAC_EVENT_PRIOR_LKG_SCHEMA_HOLD")
    if not isinstance(detail_pairs, dict) or len(detail_pairs) > MAX_DETAILS:
        raise ValueError("TPAC_EVENT_DETAIL_INPUT_CAP_HOLD")
    old = prior["events"]
    report = {"kind": KIND, "decision": "HOLD", "previous_count": len(old),
              "new_count": len(old), "added": 0, "changed": 0, "unchanged": 0,
              "retained_previous": len(old), "source_cards": 0,
              "qualified": 0, "rejected": {}, "events": dict(old),
              "release_state": "HARD_HOLD_NO_PUBLICATION",
              "published": 0, "native_attestation": "REQUIRES_INDEPENDENT_READBACK"}
    try:
        cards = discover_catalog("event", list_body, list_receipt, now)
    except (ValueError, KeyError, TypeError, OverflowError) as error:
        report["decision"] = "HOLD_EVENT_LIST_" + str(error)
        return report
    report["source_cards"] = len(cards)
    updated = dict(old)
    adds = changes = same = valid = 0
    for sid, card in cards.items():
        item = detail_pairs.get(sid)
        if not isinstance(item, dict):
            report["rejected"][sid] = "DETAIL_NOT_PROVIDED_HOLD"
            continue
        try:
            owned = dict(card)
            owned["list_sha256"] = _sha(list_body)
            review = inspect_event_detail(owned, item["body"], item["receipt"], now)
            identity = "tpac:event:" + sid
            if (review["identity"] != identity
                    or review["source_event_id"] != sid
                    or review["url"] != "https://tpac.org.taipei/event/" + sid
                    or review["detail_body_sha256"] != _sha(item["body"])
                    or review["decision"] != "SOURCE_OWNED_PARTIAL_FIELDS_REQUIRE_INDEPENDENT_ACCEPTANCE"):
                raise ValueError("TPAC_EVENT_ROLE_IDENTITY_PROVENANCE_HOLD")
            roles = {}
            for role, value in review["verified_core_roles"].items():
                roles[role] = {"role": role, "value": value,
                               "source_url": review["url"],
                               "source_body_sha256": review["detail_body_sha256"],
                               "observed_at": review["observed_at"],
                               "decision": "REVIEW_NOT_FORMAL"}
            start = review["verified_core_roles"].get("NEXT_EVENT_SHOW_START")
            event = {
                "source_namespace": "event", "identity": identity,
                "source_event_id": sid, "url": review["url"],
                "title": review["title"], "platform": "臺北表演藝術中心",
                "type": review["activity_kind"],
                "date": datetime.fromisoformat(start).strftime("%Y-%m-%d %H:%M") if start else "",
                "location": "", "price": "", "img_url": None,
                "scraped_at": _time(review["observed_at"]).astimezone(TIMEZONE).isoformat(),
                "description": "官方活動詳情與場次請參閱來源；尚未正式接受欄位。",
                "published": False, "formal_field_pass": False, "golden_accepted": False,
                "_candidate": {
                    "scope": "ARCHIVED_SOURCE_REPLAY_REVIEW_ONLY",
                    "decision": "REVIEW",
                    "event_id": sid, "identity": identity,
                    "hold_reasons": list(review["held_fields"]),
                    "source_list_sha256": _sha(list_body),
                    "source_detail_sha256": review["detail_body_sha256"],
                    "observed_at": review["observed_at"],
                    "list_period": review["list_period"],
                    "detail_period": review["detail_period"],
                    "field_roles": roles,
                },
            }
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as error:
            report["rejected"][sid] = str(error)
            continue
        valid += 1
        if identity not in updated:
            adds += 1
        elif _semantic_event_payload(updated[identity]) == _semantic_event_payload(event):
            # Preserve REVIEW LKG provenance on observation-only receipt changes.
            same += 1
            continue
        else:
            changes += 1
        updated[identity] = event
    if valid == 0:
        report["decision"] = "HOLD_NO_QUALIFIED_EVENT_DETAILS_PRESERVE_LKG"
        return report
    qualified = {"tpac:event:" + sid for sid in cards if sid not in report["rejected"]}
    report.update({"decision": "REVIEW_SNAPSHOT_READY_NOT_FORMAL",
                   "events": updated, "new_count": len(updated),
                   "added": adds, "changed": changes, "unchanged": same,
                   "retained_previous": sum(k not in qualified for k in old),
                   "qualified": valid,
                   "source_coverage_complete": valid == len(cards) and not report["rejected"]})
    return report


def _canonical(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_isolated_plan(plan, repo_root, expected_sha=None, allow_archived_rollback=False,
                        rollback_archive_sha=None):
    """Atomic/CAS isolated REVIEW snapshot; archived rollback is byte-bound.

    A legacy boolean is never authority to remove LKG rows. Removal requires
    a pre-existing, exact canonical archived snapshot, rechecked under CAS lock.
    """
    if plan.get("decision") != "REVIEW_SNAPSHOT_READY_NOT_FORMAL":
        raise ValueError("TPAC_UNQUALIFIED_PLAN_WRITE_HOLD")
    if (plan.get("release_state") != "HARD_HOLD_NO_PUBLICATION" or
            plan.get("published") != 0 or
            plan.get("native_attestation") != "REQUIRES_INDEPENDENT_READBACK"):
        raise ValueError("TPAC_UNAUTHORIZED_PUBLICATION_CLAIM_HOLD")
    rows = plan.get("events")
    if not isinstance(rows, dict) or not rows:
        raise ValueError("TPAC_EMPTY_REVIEW_SNAPSHOT_HOLD")
    for key, event in rows.items():
        if not isinstance(key, str) or not isinstance(event, dict):
            raise ValueError("TPAC_REVIEW_ROW_AUTHORITY_HOLD")
        event_match = re.fullmatch(r"tpac:event:([1-9]\d{0,9})", key)
        program_match = re.fullmatch(r"tpac:([1-9]\d{0,9})", key)
        if not event_match and not program_match:
            raise ValueError("TPAC_REVIEW_NAMESPACE_IDENTITY_HOLD")
        sid = (event_match or program_match)[1]
        url = ("https://tpac.org.taipei/event/" if event_match else ROOT + "/") + sid
        if (event.get("source_event_id") != sid
                or event.get("url") != url
                or (event_match and (event.get("source_namespace") != "event"
                                     or event.get("identity") != key))
                or (program_match and event.get("source_namespace") == "event")
                or event.get("published") is not False
                or event.get("golden_accepted") is not False
                or event.get("formal_field_pass") is not False
                or not isinstance(event.get("_candidate"), dict)
                or event["_candidate"].get("decision") != "REVIEW"):
            raise ValueError("TPAC_REVIEW_ROW_AUTHORITY_HOLD")
    root = Path(repo_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    isolation_root = root / "_isolated_review"
    if isolation_root.exists() and isolation_root.is_symlink():
        raise ValueError("TPAC_ISOLATION_ROOT_SYMLINK_HOLD")
    dest_dir = isolation_root / "tpac"
    if dest_dir.exists() and dest_dir.is_symlink():
        raise ValueError("TPAC_ISOLATED_SYMLINK_HOLD")
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / "tpac_multi_event_lkg.json"
    if target.is_symlink():
        raise ValueError("TPAC_LKG_SYMLINK_HOLD")
    lock = dest_dir / ".write.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as e:
        raise ValueError("TPAC_CONCURRENT_WRITER_HOLD") from e
    try:
        os.close(fd)
        prior = target.read_bytes() if target.exists() else None
        actual = _sha(prior) if prior is not None else None
        if actual != expected_sha:
            raise ValueError("TPAC_LKG_EXPECTED_SHA_CAS_HOLD")
        old_rows = {}
        if prior is not None:
            try:
                old_doc = json.loads(prior)
                if old_doc.get("kind") != KIND or not isinstance(old_doc.get("events"), dict):
                    raise ValueError("TPAC_PRIOR_SCHEMA_HOLD")
                old_rows = old_doc["events"]
            except (TypeError, json.JSONDecodeError) as error:
                raise ValueError("TPAC_PRIOR_SCHEMA_HOLD") from error
        removed = sorted(set(old_rows) - set(rows))
        # The previous allow_archived_rollback=True flag was an unbound
        # deletion bypass. A caller cannot claim rollback authority by boolean.
        if allow_archived_rollback is not False:
            raise ValueError("TPAC_ROLLBACK_BOOLEAN_BYPASS_HOLD")
        if removed and rollback_archive_sha is None:
            raise ValueError("TPAC_UNAUTHORIZED_REMOVAL_EXPIRY_GATE_HOLD")
        if rollback_archive_sha is not None:
            if (not isinstance(rollback_archive_sha, str)
                    or not re.fullmatch(r"[0-9a-f]{64}", rollback_archive_sha)):
                raise ValueError("TPAC_ROLLBACK_ARCHIVE_AUTHORITY_HOLD")
            archived_payload = _canonical({"kind": KIND, "events": rows})
            versions_for_rollback = dest_dir / "versions"
            archived_path = versions_for_rollback / (rollback_archive_sha + ".json")
            if (versions_for_rollback.is_symlink() or archived_path.is_symlink()
                    or not archived_path.is_file()
                    or _sha(archived_payload) != rollback_archive_sha
                    or archived_path.read_bytes() != archived_payload):
                raise ValueError("TPAC_ROLLBACK_ARCHIVE_AUTHORITY_HOLD")
        diff = {"added": sorted(set(rows) - set(old_rows)),
                "changed": sorted(k for k in set(rows) & set(old_rows)
                                  if rows[k] != old_rows[k]),
                "unchanged": sorted(k for k in set(rows) & set(old_rows)
                                    if rows[k] == old_rows[k]),
                "removed": removed}
        payload = _canonical({"kind": KIND, "events": plan["events"]})
        new_sha = _sha(payload)
        # Archive the prior exact bytes under CAS lock BEFORE replacing LKG.
        # This version is a REVIEW-only rollback source, never formal data.
        if prior is not None:
            versions = dest_dir / "versions"
            if versions.is_symlink():
                raise ValueError("TPAC_VERSION_DIRECTORY_SYMLINK_HOLD")
            versions.mkdir(exist_ok=True)
            archive = versions / (actual + ".json")
            if archive.is_symlink():
                raise ValueError("TPAC_VERSION_SYMLINK_HOLD")
            if archive.exists():
                if archive.read_bytes() != prior:
                    raise ValueError("TPAC_VERSION_COLLISION_HOLD")
            else:
                version_temp = None
                try:
                    with tempfile.NamedTemporaryFile(mode="wb", dir=versions,
                                                     prefix=".tpac-version-", delete=False) as v:
                        version_temp = Path(v.name)
                        v.write(prior)
                        v.flush()
                        os.fsync(v.fileno())
                    os.replace(version_temp, archive)
                    version_temp = None
                    if _sha(archive.read_bytes()) != actual:
                        raise ValueError("TPAC_VERSION_READBACK_HOLD")
                finally:
                    if version_temp is not None:
                        version_temp.unlink(missing_ok=True)
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=dest_dir, prefix=".tpac-stage-",
                                             delete=False) as f:
                tmp = Path(f.name)
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            if target.exists() and _sha(target.read_bytes()) != actual:
                raise ValueError("TPAC_LKG_POST_PREFLIGHT_RACE_HOLD")
            os.replace(tmp, target)
            tmp = None
            if _sha(target.read_bytes()) != new_sha:
                raise ValueError("TPAC_LKG_ATOMIC_READBACK_HOLD")
            return {"decision": "ISOLATED_REVIEW_LKG_COMMITTED_NOT_FORMAL",
                    "sha256": new_sha, "rows": len(plan["events"]),
                    "previous_sha256": actual, "diff": diff,
                    "rollback_available": prior is not None}
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
    finally:
        lock.unlink(missing_ok=True)


def restore_isolated_version(repo_root, archived_sha, expected_current_sha):
    """Restore a sealed REVIEW version by CAS; never touch formal data/Golden."""
    if (not isinstance(archived_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", archived_sha)
            or not isinstance(expected_current_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_current_sha)):
        raise ValueError("TPAC_ROLLBACK_SHA_ARGUMENT_HOLD")
    root = Path(repo_root).resolve()
    isolation = root / "_isolated_review"
    folder = isolation / "tpac"
    versions = folder / "versions"
    archive = versions / (archived_sha + ".json")
    if any(p.is_symlink() for p in (isolation, folder, versions, archive)):
        raise ValueError("TPAC_ROLLBACK_SYMLINK_HOLD")
    if not archive.is_file():
        raise ValueError("TPAC_ROLLBACK_ARCHIVE_MISSING_HOLD")
    raw = archive.read_bytes()
    if _sha(raw) != archived_sha:
        raise ValueError("TPAC_ROLLBACK_ARCHIVE_SHA_HOLD")
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("TPAC_ROLLBACK_ARCHIVE_JSON_HOLD") from error
    if document.get("kind") != KIND or not isinstance(document.get("events"), dict):
        raise ValueError("TPAC_ROLLBACK_ARCHIVE_SCHEMA_HOLD")
    # Check canonical bytes BEFORE calling the writer: a noncanonical but
    # self-consistently hashed archive must never mutate LKG then raise HOLD.
    if _canonical(document) != raw:
        raise ValueError("TPAC_ROLLBACK_NONCANONICAL_ARCHIVE_HOLD")
    plan = {"decision": "REVIEW_SNAPSHOT_READY_NOT_FORMAL",
            "release_state": "HARD_HOLD_NO_PUBLICATION",
            "native_attestation": "REQUIRES_INDEPENDENT_READBACK",
            "published": 0, "events": document["events"]}
    result = write_isolated_plan(plan, root, expected_current_sha,
                                 rollback_archive_sha=archived_sha)
    if result["sha256"] != archived_sha:
        raise ValueError("TPAC_ROLLBACK_NONCANONICAL_ARCHIVE_HOLD")
    return dict(result, decision="ISOLATED_REVIEW_ROLLBACK_NOT_FORMAL")



def load_isolated_prior(repo_root):
    """Read exact current isolated LKG and its CAS SHA for repeatable refresh.

    Never trust a manifest-supplied prior in this mode. A later concurrent
    writer is caught by write_isolated_plan's expected-SHA lock check.
    Historical receipts remain historical; this helper does not attest GET.
    """
    root = Path(repo_root).resolve()
    isolation = root / "_isolated_review"
    folder = isolation / "tpac"
    target = folder / "tpac_multi_event_lkg.json"
    if any(p.is_symlink() for p in (isolation, folder, target)):
        raise ValueError("TPAC_AUTO_PRIOR_SYMLINK_HOLD")
    if not target.exists():
        return {"kind": KIND, "events": {}}, None
    if not target.is_file() or not 0 < target.stat().st_size <= 16 * 1024 * 1024:
        raise ValueError("TPAC_AUTO_PRIOR_SIZE_OR_TYPE_HOLD")
    raw = target.read_bytes()
    try:
        document = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("TPAC_AUTO_PRIOR_JSON_HOLD") from error
    if (not isinstance(document, dict)
            or set(document) != {"kind", "events"}
            or document["kind"] != KIND
            or not isinstance(document["events"], dict)):
        raise ValueError("TPAC_AUTO_PRIOR_SCHEMA_HOLD")
    if _canonical(document) != raw:
        raise ValueError("TPAC_AUTO_PRIOR_NONCANONICAL_HOLD")
    return document, _sha(raw)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="TPAC multi-event offline REVIEW refresh; no GET or PUBLISH")
    # Explicit namespace prevents a /event archive from silently entering the
    # legacy /program planner; the default preserves existing program callers.
    ap.add_argument("--catalog", choices=("program", "event"), default="program")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--inventory-input", type=Path,
                    help="Offline two-catalog LIST/DETAIL receipt manifest; no network")
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--expected-sha")
    ap.add_argument("--prior-from-lkg", action="store_true",
                    help="CAS-load the current isolated LKG instead of a manifest prior")
    args = ap.parse_args(argv)
    if args.inventory_input is not None:
        if args.input is not None or args.prior_from_lkg or args.expected_sha is not None:
            raise ValueError("TPAC_INVENTORY_CLI_MODE_CONFLICT_HOLD")
        result = offline_inventory_cli(args.inventory_input, args.repo_root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.input is None:
        raise ValueError("TPAC_INPUT_REQUIRED_HOLD")
    data = json.loads(args.input.read_text(encoding="utf-8"))
    if data.get("catalog", "program") != args.catalog:
        raise ValueError("TPAC_MANIFEST_CATALOG_MISMATCH_HOLD")
    if args.prior_from_lkg:
        if "prior" in data or args.expected_sha is not None:
            raise ValueError("TPAC_AUTO_PRIOR_AMBIGUOUS_HOLD")
        prior, expected_sha = load_isolated_prior(args.repo_root)
    else:
        prior, expected_sha = data["prior"], args.expected_sha
    pairs = {sid: {"body": Path(row["detail_file"]).read_bytes(), "receipt": row["receipt"]}
             for sid, row in data["details"].items()}
    planner = refresh_event_plan if args.catalog == "event" else refresh_plan
    plan = planner(Path(data["list_file"]).read_bytes(), data["list_receipt"],
                   pairs, prior, _time(data["now"]))
    if plan["decision"] == "REVIEW_SNAPSHOT_READY_NOT_FORMAL":
        result = write_isolated_plan(plan, args.repo_root, expected_sha)
    else:
        result = {"decision": plan["decision"], "sha256": None, "rows": plan["new_count"]}
    print(json.dumps({"result": result,
                      "counts": {k: plan[k] for k in ("source_cards", "qualified", "added", "changed",
                                                    "unchanged", "retained_previous")},
                      "rejected": plan["rejected"],
                      "published": 0}, ensure_ascii=False, sort_keys=True))
    return 0 if result["decision"] == "ISOLATED_REVIEW_LKG_COMMITTED_NOT_FORMAL" else 49


# Persistent LIST inventory is separate from REVIEW event LKG. It never grants
# DETAIL network permission or formal field acceptance.
INVENTORY_KIND = "TPAC_DUAL_CATALOG_PENDING_DETAIL_V1"


def build_detail_inventory(catalog, raw, receipt, now, previous=None):
    """Reconcile every visible LIST ID without discarding prior attempt history."""
    from scripts.p30_tpac_catalog_topology import discover_catalog
    if catalog not in ("program", "event"):
        raise ValueError("TPAC_INVENTORY_CATALOG_HOLD")
    if previous is not None and (not isinstance(previous, dict)
            or previous.get("kind") != INVENTORY_KIND
            or not isinstance(previous.get("items"), dict)):
        raise ValueError("TPAC_INVENTORY_PRIOR_SCHEMA_HOLD")
    cards = discover_catalog(catalog, raw, receipt, now)
    prior_items = previous["items"] if previous else {}
    current = dict(prior_items)
    list_sha = _sha(raw)
    observed = _time(receipt["observed_at"]).isoformat()
    for sid, card in cards.items():
        key = card["identity"]
        old = prior_items.get(key, {})
        if old and (old.get("detail_url") != card["detail_url"]
                    or old.get("source_namespace") != catalog
                    or old.get("source_event_id") != sid):
            raise ValueError("TPAC_INVENTORY_IDENTITY_DRIFT_HOLD")
        current[key] = {
            "source_namespace": catalog, "source_event_id": sid,
            "list_url": card["list_url"], "detail_url": card["detail_url"],
            "list_sha": list_sha, "last_observed": observed,
            "status": old.get("status", "PENDING_DETAIL_BUDGET"),
            "attempts": old.get("attempts", 0),
            "last_attempt": old.get("last_attempt"),
            "reason": old.get("reason", "DETAIL_BYTES_NOT_CAPTURED"),
        }
    # Unobserved historical IDs are retained, but cannot be scheduled.
    for key in (set(prior_items) - {c["identity"] for c in cards.values()}):
        if prior_items[key].get("source_namespace") != catalog:
            continue
        current[key] = dict(prior_items[key], status="NOT_IN_LATEST_LIST_REVIEW")
    return {"kind": INVENTORY_KIND, "items": current}


def select_pending_details(inventory, limit=2):
    """Fair, deterministic per-catalog round-robin; selection is not GET authority."""
    if (not isinstance(inventory, dict) or inventory.get("kind") != INVENTORY_KIND
            or not isinstance(inventory.get("items"), dict)
            or not isinstance(limit, int) or isinstance(limit, bool)
            or not 0 <= limit <= 2):
        raise ValueError("TPAC_INVENTORY_SELECTION_SCHEMA_HOLD")
    buckets = {}
    for key, row in inventory["items"].items():
        if (not isinstance(row, dict)
                or row.get("source_namespace") not in ("program", "event")
                or key != "tpac:" + row["source_namespace"] + ":" + str(row.get("source_event_id"))
                or row.get("detail_url") != "https://tpac.org.taipei/" +
                   row["source_namespace"] + "/" + str(row["source_event_id"])):
            raise ValueError("TPAC_INVENTORY_ROW_IDENTITY_HOLD")
        if row.get("status") == "PENDING_DETAIL_BUDGET":
            buckets.setdefault(row["source_namespace"], []).append((key, row))
    for entries in buckets.values():
        entries.sort(key=lambda item: (item[1].get("attempts", 0),
                                       item[1].get("last_attempt") or "", item[0]))
    chosen = []
    while len(chosen) < limit and any(buckets.values()):
        for kind in ("program", "event"):
            if len(chosen) < limit and buckets.get(kind):
                chosen.append(buckets[kind].pop(0)[0])
    return chosen


def write_detail_inventory(inventory, repo_root, expected_sha=None):
    """Local atomic CAS of inventory only; never touch the separate event LKG."""
    if not isinstance(inventory, dict) or inventory.get("kind") != INVENTORY_KIND:
        raise ValueError("TPAC_INVENTORY_WRITE_SCHEMA_HOLD")
    select_pending_details(inventory, 0)  # Validate every row before any write.
    root = Path(repo_root).resolve()
    folder = root / "_isolated_review" / "tpac"
    if any(p.is_symlink() for p in (root / "_isolated_review", folder)):
        raise ValueError("TPAC_INVENTORY_SYMLINK_HOLD")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "tpac_detail_inventory.json"
    lock = folder / ".inventory.lock"
    if target.is_symlink() or lock.is_symlink():
        raise ValueError("TPAC_INVENTORY_SYMLINK_HOLD")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError("TPAC_INVENTORY_CONCURRENT_WRITER_HOLD") from error
    try:
        os.close(fd)
        prior = target.read_bytes() if target.exists() else None
        if (None if prior is None else _sha(prior)) != expected_sha:
            raise ValueError("TPAC_INVENTORY_CAS_HOLD")
        payload = _canonical(inventory)
        with tempfile.NamedTemporaryFile(dir=folder, prefix=".inventory-", delete=False) as tmp:
            temp_name = tmp.name
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        try:
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return {"sha256": _sha(payload), "items": len(inventory["items"])}
    finally:
        os.unlink(lock)


def load_detail_inventory(repo_root):
    """Read canonical persisted inventory and its CAS version."""
    target = Path(repo_root).resolve() / "_isolated_review" / "tpac" / "tpac_detail_inventory.json"
    if target.is_symlink() or target.parent.is_symlink():
        raise ValueError("TPAC_INVENTORY_SYMLINK_HOLD")
    if not target.exists():
        return {"kind": INVENTORY_KIND, "items": {}}, None
    raw = target.read_bytes()
    if not 0 < len(raw) <= 16 * 1024 * 1024:
        raise ValueError("TPAC_INVENTORY_SIZE_HOLD")
    document = json.loads(raw)
    if _canonical(document) != raw:
        raise ValueError("TPAC_INVENTORY_NONCANONICAL_HOLD")
    select_pending_details(document, 0)
    return document, _sha(raw)



def _archived_body(raw, receipt, url, catalog, event_id=None):
    """Offline provenance only. Never converts an archive into a LIVE receipt."""
    if not isinstance(receipt, dict) or receipt.get("evidence_class") != "VERIFIED_ARCHIVED_BODY_ONLY":
        raise ValueError("TPAC_ARCHIVE_EVIDENCE_CLASS_HOLD")
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BODY:
        raise ValueError("TPAC_ARCHIVE_BODY_HOLD")
    expected = "https://tpac.org.taipei/" + catalog
    if event_id is not None:
        expected += "/" + str(event_id)
    if url != expected or receipt.get("source_url") != expected:
        raise ValueError("TPAC_ARCHIVE_IDENTITY_URL_HOLD")
    if receipt.get("body_sha256") != _sha(raw) or receipt.get("body_bytes") != len(raw):
        raise ValueError("TPAC_ARCHIVE_BYTES_SHA_HOLD")
    # The one-shot /program receipt has no per-body observation, status or robots.
    # Unknown fields must remain absent/null, not fabricated by a replay.
    if any(receipt.get(k) is not None for k in ("observed_at", "http_status", "robots_allowed")):
        raise ValueError("TPAC_ARCHIVE_AUTHORITY_ESCALATION_HOLD")
    stamp = receipt.get("capture_started_at")
    if stamp is not None:
        _time(stamp)  # validate provenance metadata, never treat as observed_at
    return _body(raw)


def _archived_cards(catalog, raw, receipt):
    """Visible, exact first-party card inventory; no LIVE discovery or parser acceptance."""
    soup = _archived_body(raw, receipt, "https://tpac.org.taipei/" + catalog, catalog)
    selector = "a.card-program[href][title]" if catalog == "program" else "a.card-event[href][title]"
    cards = soup.select(selector)
    if not 1 <= len(cards) <= MAX_CARDS:
        raise ValueError("TPAC_ARCHIVE_LIST_COUNT_HOLD")
    results = {}
    for card in cards:
        if not _visible(card):
            continue
        href = card.get("href", "")
        url = urljoin("https://tpac.org.taipei/" + catalog, href)
        parts = urlsplit(url)
        match = re.fullmatch("/" + catalog + r"/([1-9]\d{0,9})", parts.path)
        if (parts.scheme != "https" or parts.netloc != "tpac.org.taipei"
                or parts.query or parts.fragment or match is None):
            raise ValueError("TPAC_ARCHIVE_CARD_URL_HOLD")
        sid = match.group(1)
        if sid in results:
            raise ValueError("TPAC_ARCHIVE_DUPLICATE_ID_HOLD")
        title = card["title"].strip()
        owned_selector = ".card-program__text-title" if catalog == "program" else ".card-event__text-title"
        if not 3 <= len(title) <= 180 or title != _text(card.select_one(owned_selector)):
            raise ValueError("TPAC_ARCHIVE_CARD_TITLE_HOLD")
        results[sid] = {"identity": "tpac:" + catalog + ":" + sid,
                        "source_event_id": sid, "source_namespace": catalog,
                        "list_url": "https://tpac.org.taipei/" + catalog,
                        "detail_url": url}
    if not results:
        raise ValueError("TPAC_ARCHIVE_NO_VISIBLE_CARDS_HOLD")
    return results


def archived_inventory_cli(manifest_path, repo_root):
    """Separate archived-only CLI; never calls LIVE _receipt or creates accepted events."""
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"mode", "catalogs"} or data["mode"] != "archived":
        raise ValueError("TPAC_ARCHIVE_MANIFEST_HOLD")
    if not isinstance(data["catalogs"], dict) or set(data["catalogs"]) != {"program", "event"}:
        raise ValueError("TPAC_ARCHIVE_TWO_CATALOG_HOLD")
    # Archive replay has its own CAS domain; never downgrade a LIVE inventory row.
    # Archive replay must not follow a pre-existing symlink outside the caller root.
    # Check before load/write: their internal resolve() would otherwise escape.
    base_root = Path(repo_root).resolve()
    archive_root = base_root / "_isolated_archive_replay"
    if archive_root.is_symlink():
        raise ValueError("TPAC_ARCHIVE_ROOT_SYMLINK_HOLD")
    previous, expected = load_detail_inventory(archive_root)
    rows = dict(previous["items"]) if previous else {}
    counts = {"source_cards": 0, "detail_available": 0, "pending_detail_budget": 0,
              "archive_identity_hold": 0}
    diagnostics = {}
    for catalog in ("program", "event"):
        entry = data["catalogs"][catalog]
        if not isinstance(entry, dict) or set(entry) != {"list_file", "list_receipt", "details"}:
            raise ValueError("TPAC_ARCHIVE_CATALOG_SCHEMA_HOLD")
        raw = Path(entry["list_file"]).read_bytes()
        receipt = entry["list_receipt"]
        cards = _archived_cards(catalog, raw, receipt)
        details = entry["details"]
        if not isinstance(details, dict) or set(details) - set(cards):
            raise ValueError("TPAC_ARCHIVE_DETAIL_ID_HOLD")
        counts["source_cards"] += len(cards)
        for sid, card in cards.items():
            key = card["identity"]
            old = rows.get(key, {})
            if old and (old.get("detail_url") != card["detail_url"]
                        or old.get("source_namespace") != catalog):
                raise ValueError("TPAC_ARCHIVE_IDENTITY_DRIFT_HOLD")
            status, reason = "PENDING_DETAIL_BUDGET", "DETAIL_BYTES_NOT_CAPTURED"
            if sid in details:
                record = details[sid]
                if not isinstance(record, dict) or set(record) != {"detail_file", "receipt"}:
                    raise ValueError("TPAC_ARCHIVE_DETAIL_SCHEMA_HOLD")
                body = Path(record["detail_file"]).read_bytes()
                _archived_body(body, record["receipt"], card["detail_url"], catalog, sid)
                # Only source-body identity is verified; semantic fields remain unaccepted.
                status, reason = "ARCHIVED_DETAIL_VERIFIED_ONLY", "PARSER_NOT_ACCEPTED_ARCHIVE_ONLY"
                counts["detail_available"] += 1
            else:
                counts["pending_detail_budget"] += 1
            rows[key] = {"source_namespace": catalog, "source_event_id": sid,
                         "list_url": card["list_url"], "detail_url": card["detail_url"],
                         "list_sha": _sha(raw), "last_observed": None,
                         "status": status, "attempts": old.get("attempts", 0),
                         "last_attempt": old.get("last_attempt"), "reason": reason}
            diagnostics[key] = {"status": status, "reason": reason}
    # Do not erase rows from other snapshots; archive replay is not LIVE reconciliation.
    inventory = {"kind": INVENTORY_KIND, "items": rows}
    result = write_detail_inventory(inventory, archive_root, expected)
    return {"decision": "ARCHIVED_SOURCE_VERIFIED_BODY_ONLY_NO_PUBLICATION",
            "inventory": result, "counts": counts, "diagnostics": diagnostics,
            "next_detail_ids": select_pending_details(inventory),
            "published": 0, "accepted_fields": 0}

def offline_inventory_cli(manifest_path, repo_root):
    """Replay sealed two-catalog LIST bytes, persist backlog CAS; never GET/publish."""
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and data.get("mode") == "archived":
        return archived_inventory_cli(manifest_path, repo_root)
    if not isinstance(data, dict) or set(data) != {"now", "catalogs"}:
        raise ValueError("TPAC_INVENTORY_CLI_MANIFEST_HOLD")
    catalogs = data["catalogs"]
    if not isinstance(catalogs, dict) or set(catalogs) != {"program", "event"}:
        raise ValueError("TPAC_INVENTORY_CLI_TWO_CATALOGS_HOLD")
    now = _time(data["now"])
    prior, expected = load_detail_inventory(repo_root)
    # Use the actual isolated REVIEW LKG as parser prior; inventory is a separate CAS domain.
    # Never persist a newly parsed event from this diagnostic-only CLI.
    review_prior, review_sha = load_isolated_prior(repo_root)
    staged = prior
    counts = {"source_cards": 0, "detail_available": 0,
              "pending_detail_budget": 0, "parse_hold": 0, "review": 0}
    diagnostics = {}
    for catalog in ("program", "event"):
        entry = catalogs[catalog]
        if not isinstance(entry, dict) or set(entry) != {"list_file", "list_receipt", "details"}:
            raise ValueError("TPAC_INVENTORY_CLI_CATALOG_SCHEMA_HOLD")
        raw = Path(entry["list_file"]).read_bytes()
        staged = build_detail_inventory(catalog, raw, entry["list_receipt"], now, staged)
        from scripts.p30_tpac_catalog_topology import discover_catalog
        cards = discover_catalog(catalog, raw, entry["list_receipt"], now)
        details = entry["details"]
        if not isinstance(details, dict) or set(details) - set(cards):
            raise ValueError("TPAC_INVENTORY_CLI_DETAIL_ID_HOLD")
        counts["source_cards"] += len(cards)
        pairs = {}
        for sid, record in details.items():
            if not isinstance(record, dict) or set(record) != {"detail_file", "receipt"}:
                raise ValueError("TPAC_INVENTORY_CLI_DETAIL_SCHEMA_HOLD")
            pairs[sid] = {"body": Path(record["detail_file"]).read_bytes(),
                          "receipt": record["receipt"]}
        plan = None
        if pairs:
            planner = refresh_event_plan if catalog == "event" else refresh_plan
            plan = planner(raw, entry["list_receipt"], pairs,
                           review_prior, now)
        for sid, card in cards.items():
            key = card["identity"]
            row = staged["items"][key]
            if sid not in pairs:
                if row["status"] != "REVIEW_DETAIL_PARSED":
                    row["status"] = "PENDING_DETAIL_BUDGET"
                    row["reason"] = "DETAIL_BYTES_NOT_CAPTURED"
                    counts["pending_detail_budget"] += 1
                diagnostics[key] = {"status": row["status"], "reason": row["reason"]}
                continue
            counts["detail_available"] += 1
            event_key = "tpac:event:" + sid if catalog == "event" else "tpac:" + sid
            # A retained LKG entry is NOT evidence that this DETAIL parsed successfully.
            accepted = (plan is not None and event_key in plan["events"]
                        and sid not in plan.get("rejected", {})
                        and plan.get("decision") == "REVIEW_SNAPSHOT_READY_NOT_FORMAL")
            row["status"] = "REVIEW_DETAIL_PARSED" if accepted else "PARSE_HOLD"
            reason = "REVIEW_FIELDS_NOT_FORMALLY_ACCEPTED" if accepted else "DETAIL_PARSER_REJECTED"
            if not accepted and plan is not None:
                reason = str(plan.get("rejected", {}).get(sid, reason))
            row["reason"] = reason
            counts["review" if accepted else "parse_hold"] += 1
            diagnostics[key] = {"status": row["status"], "reason": reason}
    result = write_detail_inventory(staged, repo_root, expected)
    return {"decision": "ISOLATED_INVENTORY_ONLY_NO_PUBLICATION",
            "inventory": result, "counts": counts,
            "next_detail_ids": select_pending_details(staged),
            "diagnostics": diagnostics, "published": 0}


if __name__ == "__main__":
    raise SystemExit(main())
