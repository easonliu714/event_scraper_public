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
import stat
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from scripts.p30_tpac_price_reconcile import extract_tpac_price_review

ROOT = "https://tpac.org.taipei/program"
KIND = "TPAC_SOURCE_OWNED_MULTI_EVENT_REVIEW_V1"
TIMEZONE = timezone(timedelta(hours=8))
DAY = "一二三四五六日"
# Reject hours 24-29 before datetime parsing so malformed source labels HOLD deterministically.
SHOW = re.compile(r"^(20\d{2}-\d{2}-\d{2})\s*\(([一二三四五六日])\)\s*((?:[01]\d|2[0-3]):[0-5]\d)$")
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
    # Hidden showtime nodes are not source-visible evidence. Reject the entire
    # ambiguous section rather than treating hidden dates as accepted events.
    if any(not _visible(node) for node in labels):
        raise ValueError("TPAC_HIDDEN_SHOWTIME_EVIDENCE_HOLD")
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
    """Compare stable REVIEW semantics, including quality HOLD transitions.

    A LIST/DETAIL period conflict can appear or resolve while the displayed
    next showtime stays identical. Dropping that change preserves stale safety
    evidence in LKG. Receipt hashes, observation timestamps, and publication
    flags are deliberately excluded from the semantic comparison.
    """
    if not isinstance(event, dict):
        raise ValueError("TPAC_SEMANTIC_EVENT_SCHEMA_HOLD")
    keys = ("source_event_id", "title", "url", "platform", "type",
            "date", "location", "price", "img_url", "description")
    candidate = event.get("_candidate") or {}
    if not isinstance(candidate, dict):
        raise ValueError("TPAC_SEMANTIC_CANDIDATE_SCHEMA_HOLD")
    roles = candidate.get("field_roles") or {}
    if not isinstance(roles, dict):
        raise ValueError("TPAC_SEMANTIC_FIELD_ROLES_SCHEMA_HOLD")
    # Compare all event-owned REVIEW roles, including /event verified core roles.
    # Previously only programme price/venue were compared, so a changed
    # /event period or show-role value could silently retain stale LKG.
    # Exclude receipt-only URL/SHA/UTC metadata from activity semantics.
    stable_roles = tuple(sorted(set(roles) | {"price", "venue_space"}))
    for role in stable_roles:
        if role in roles and not isinstance(roles[role], dict):
            raise ValueError("TPAC_SEMANTIC_FIELD_ROLE_SCHEMA_HOLD:" + role)
    role_values = tuple((role, json.dumps({
        key: roles.get(role, {}).get(key)
        for key in ("role", "value", "min_price_ntd", "max_price_ntd",
                    "start_area_note", "start_area_role", "decision")
    }, ensure_ascii=False, sort_keys=True)) for role in stable_roles)
    # Persisted HOLD authority must be an explicit list. Falsey malformed
    # values (None, "", 0, False) must not erase a prior safety decision.
    holds = candidate.get("hold_reasons", [])
    if (not isinstance(holds, list)
            or any(not isinstance(reason, str) or not reason for reason in holds)):
        raise ValueError("TPAC_SEMANTIC_HOLD_REASONS_SCHEMA_HOLD")
    # HOLD reasons are a set of stable safety decisions: order and duplicated
    # identical strings must not create false new activity.
    hold_semantics = ("quality_hold_reasons", tuple(sorted(set(holds))))
    # /event LIST and DETAIL periods are source-owned business evidence.
    # A changed period must not be hidden by identical held-field labels or
    # by unchanged next-showtime; exclude only receipt/observation metadata.
    period_semantics = tuple((key, candidate.get(key))
                             for key in ("list_period", "detail_period"))
    # Price REVIEW is not a displayed price, but its tier range and direct
    # ticket identity are business semantics. Receipt-only SHA/time changes
    # must not churn LKG; changed range or ticket event must not retain stale
    # field evidence just because the public price stays blank.
    price_review = candidate.get("price_review")
    if price_review is None:
        price_semantics = ("price_review", None)
    else:
        if not isinstance(price_review, dict):
            raise ValueError("TPAC_SEMANTIC_PRICE_REVIEW_SCHEMA_HOLD")
        linked = price_review.get("linked_ticket")
        if not isinstance(linked, dict):
            raise ValueError("TPAC_SEMANTIC_TICKET_IDENTITY_SCHEMA_HOLD")
        price_semantics = ("price_review", tuple(
            (name, price_review.get(name)) for name in
            ("decision", "role", "event_id", "min_price_ntd",
             "max_price_ntd", "raw_price_label")),
            tuple((name, linked.get(name)) for name in
                  ("platform", "ticket_event_id", "ticket_event_url",
                   "relation", "same_event_relation")))
    # Preserve cross-catalog identity and REVIEW authority transitions even
    # when display fields and source URLs happen to remain unchanged.
    identity_semantics = tuple((key, event.get(key)) for key in
                               ("source_namespace", "identity"))
    authority_semantics = tuple((key, candidate.get(key)) for key in
                                ("scope", "decision", "identity"))
    return (tuple((key, event.get(key)) for key in keys)
            + identity_semantics + authority_semantics
            + role_values + (hold_semantics,) + period_semantics
            + (price_semantics,))


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
        key = "tpac:" + sid
        if key in updated:
            # A malformed persisted LKG entry must not abort the entire batch
            # or be overwritten by an otherwise valid new observation.
            try:
                previous_semantics = _semantic_event_payload(updated[key])
                current_semantics = _semantic_event_payload(event)
            except (ValueError, TypeError, KeyError) as exc:
                report["rejected"][sid] = "TPAC_PRIOR_EVENT_SEMANTIC_HOLD:" + str(exc)
                continue
            if previous_semantics == current_semantics:
                valid += 1
                same += 1
                continue  # Preserve the prior LKG bytes and provenance unchanged.
            changes += 1
        else:
            adds += 1
        valid += 1
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
        # An invalid persisted /event LKG must isolate only its own identity.
        # Keep the previous row and continue processing unrelated valid DETAILs.
        if identity in updated:
            try:
                previous_semantics = _semantic_event_payload(updated[identity])
                current_semantics = _semantic_event_payload(event)
            except (ValueError, TypeError, KeyError) as error:
                report["rejected"][sid] = "TPAC_PRIOR_EVENT_SEMANTIC_HOLD:" + str(error)
                continue
            if previous_semantics == current_semantics:
                valid += 1
                same += 1
                continue  # Receipt-only change: retain original LKG provenance.
            changes += 1
        else:
            adds += 1
        valid += 1
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


@contextmanager
def _isolated_writer_lock(lock, hold):
    """Persistent POSIX lock inode; legacy/unknown sentinels remain HOLD.

    Publish the protocol marker atomically before locking. Never unlink a
    protocol inode: another process may already have opened it. Old writers
    using O_EXCL will also fail closed against this persistent sentinel.
    """
    try:
        import fcntl
    except ImportError as error:
        # No crash-safe ownership proof is available without an OS-backed lock.
        # Never create/unlink a sentinel that could be stolen after a crash or
        # unlink another writer's inode. Fail closed without touching the LKG.
        raise ValueError(hold) from error

    marker = b"TPAC_ISOLATED_FLOCK_V1\n"
    if not lock.exists() and not lock.is_symlink():
        staged = None
        try:
            with tempfile.NamedTemporaryFile(dir=lock.parent, prefix=".lock-stage-",
                                             delete=False) as stream:
                staged = Path(stream.name)
                stream.write(marker)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(staged, lock)
            except FileExistsError:
                pass
        finally:
            if staged is not None:
                staged.unlink(missing_ok=True)
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError(hold)
    try:
        fd = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        raise ValueError(hold) from error
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or os.read(fd, len(marker) + 1) != marker:
            raise ValueError(hold)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError(hold) from error
        if not os.path.samestat(info, os.stat(lock, follow_symlinks=False)):
            raise ValueError(hold)
        yield
    finally:
        os.close(fd)


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
                or (program_match and (event.get("source_namespace") not in (None, "program")
                                       or event.get("identity") not in (None, key)))
                or (event["_candidate"].get("identity") not in (None, key))
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
    with _isolated_writer_lock(lock, "TPAC_CONCURRENT_WRITER_HOLD"):
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
                # Reject malformed prior bytes before archiving them during recovery.
                if set(old_doc) != {"kind", "events"} or _canonical(old_doc) != prior:
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
    ap.add_argument("--diff-prior-archive-sha", help="Read-only previous inventory version for candidate field delta")
    # Explicit opt-in: persist REVIEW-only field candidates under isolated CAS.
    ap.add_argument("--commit-archive-field-candidates", action="store_true",
                    help="Commit archived FIELD candidate delta to isolated LKG, never formal data")
    ap.add_argument("--candidate-expected-sha",
                    help="Expected current isolated candidate snapshot SHA for compare-and-swap")
    ap.add_argument("--read-archive-field-candidates", action="store_true",
                    help="Read exact isolated candidate LKG after restart; never publish")
    ap.add_argument("--export-archive-fields", action="store_true",
                    help="Read-only normalized FIELD REVIEW ledger from isolated archive CAS")
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--expected-sha")
    ap.add_argument("--restore-archive-version", help="SHA256 of a prior isolated archive inventory")
    ap.add_argument("--restore-identity", help="One exact tpac:program/event:ID to recover as historical REVIEW")
    ap.add_argument("--prior-from-lkg", action="store_true",
                    help="CAS-load the current isolated LKG instead of a manifest prior")
    args = ap.parse_args(argv)
    if args.read_archive_field_candidates:
        if (args.export_archive_fields or args.commit_archive_field_candidates
                or args.diff_prior_archive_sha is not None
                or args.candidate_expected_sha is not None
                or args.input is not None or args.inventory_input is not None
                or args.restore_archive_version is not None
                or args.restore_identity is not None or args.prior_from_lkg):
            raise ValueError("TPAC_CANDIDATE_READ_MODE_HOLD")
        snapshot = load_archived_field_candidate_snapshot(args.repo_root, args.expected_sha)
        print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True))
        return 0
    if args.export_archive_fields:
        if args.diff_prior_archive_sha is not None and (type(args.diff_prior_archive_sha) is not str or re.fullmatch(r"[0-9a-f]{64}", args.diff_prior_archive_sha) is None):
            raise ValueError("TPAC_FIELD_DELTA_PRIOR_SHA_HOLD")
        # Export stays read-only unless explicitly opted into isolated candidate CAS.
        if args.commit_archive_field_candidates:
            if args.diff_prior_archive_sha is None:
                raise ValueError("TPAC_CANDIDATE_COMMIT_REQUIRES_PRIOR_VERSION_HOLD")
            if (args.candidate_expected_sha is not None and
                    re.fullmatch(r"[0-9a-f]{64}", args.candidate_expected_sha) is None):
                raise ValueError("TPAC_CANDIDATE_COMMIT_EXPECTED_SHA_HOLD")
        elif args.candidate_expected_sha is not None:
            raise ValueError("TPAC_CANDIDATE_COMMIT_MODE_HOLD")
        # A strict, archive-only output mode, never a publication or GET path.
        if (args.input is not None or args.inventory_input is not None
                or args.restore_archive_version is not None
                or args.restore_identity is not None or args.prior_from_lkg
                or type(args.expected_sha) is not str
                or re.fullmatch(r"[0-9a-f]{64}", args.expected_sha) is None):
            raise ValueError("TPAC_ARCHIVE_FIELD_EXPORT_MODE_HOLD")
        archive_root = Path(args.repo_root).resolve() / "_isolated_archive_replay"
        if archive_root.is_symlink():
            raise ValueError("TPAC_ARCHIVE_ROOT_SYMLINK_HOLD")
        inventory, actual_sha = load_detail_inventory(archive_root)
        if actual_sha is None or actual_sha != args.expected_sha:
            raise ValueError("TPAC_ARCHIVE_FIELD_EXPORT_CAS_HOLD")
        report = build_archived_field_review_export(inventory, actual_sha)
        if args.diff_prior_archive_sha is not None:
            prior_inventory, prior_sha = read_detail_inventory_version(archive_root, args.diff_prior_archive_sha)
            prior_ledger = build_archived_field_review_export(prior_inventory, prior_sha)
            report = build_archived_field_candidate_delta(prior_ledger, report)
        if args.commit_archive_field_candidates:
            # The existing isolated writer lock and CAS are the sole writer path.
            committed = write_archived_field_candidate_snapshot(
                report, args.repo_root, args.candidate_expected_sha)
            print(json.dumps({"result": committed, "delta": report},
                             ensure_ascii=False, sort_keys=True))
            return 0
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    if (args.diff_prior_archive_sha is not None or args.commit_archive_field_candidates
            or args.candidate_expected_sha is not None):
        raise ValueError("TPAC_FIELD_DELTA_MODE_HOLD")
    if args.restore_archive_version is not None or args.restore_identity is not None:
        # Archive recovery is a separate mode; never touch LIVE inventory/LKG.
        if (args.input is not None or args.inventory_input is not None
                or args.prior_from_lkg or args.restore_archive_version is None
                or args.restore_identity is None or args.expected_sha is None
                or re.fullmatch(r"[0-9a-f]{64}", args.expected_sha) is None):
            raise ValueError("TPAC_ARCHIVE_RECOVERY_CLI_MODE_HOLD")
        archive_root = Path(args.repo_root).resolve() / "_isolated_archive_replay"
        if archive_root.is_symlink():
            raise ValueError("TPAC_ARCHIVE_ROOT_SYMLINK_HOLD")
        result = restore_detail_inventory_row(
            archive_root, args.restore_archive_version, args.restore_identity,
            args.expected_sha)
        print(json.dumps({**result, "accepted_fields": 0, "published": 0},
                         ensure_ascii=False, sort_keys=True))
        return 0
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
    # An unreadable DETAIL is per-event HOLD, not a reason to discard valid
    # siblings or their existing LKG. Invalid manifest schemas still fail closed.
    details = data.get("details")
    if not isinstance(details, dict) or len(details) > MAX_DETAILS:
        raise ValueError("TPAC_DETAIL_MANIFEST_SCHEMA_OR_CAP_HOLD")
    pairs = {}
    for sid, row in details.items():
        if (type(sid) is not str or re.fullmatch(r"[1-9][0-9]{0,9}", sid) is None
                or not isinstance(row, dict)
                or set(row) != {"detail_file", "receipt"}
                or type(row["detail_file"]) is not str
                or not isinstance(row["receipt"], dict)):
            raise ValueError("TPAC_DETAIL_MANIFEST_ROW_SCHEMA_HOLD")
        try:
            detail_path = Path(row["detail_file"])
            if not detail_path.is_file():
                raise OSError("DETAIL_NOT_REGULAR_FILE")
            body = detail_path.read_bytes()
        except OSError:
            # Planner emits DETAIL_NOT_PROVIDED_HOLD for this exact ID.
            # No filesystem paths or failed bytes may enter a REVIEW candidate.
            continue
        pairs[sid] = {"body": body, "receipt": row["receipt"]}
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
        # A LIST body hash alone causes false churn when an unrelated card
        # changes. Track the source-owned title/period/category per identity;
        # if one event's semantics drift, its previous DETAIL status is stale.
        # Legacy rows without this fingerprint fail closed into the backlog.
        card_sha = _sha(_canonical({
            "title": card["title_candidate"],
            "title_owned": card["list_title_owned"],
            "period": card["list_date_label"],
            "category": card["list_event_category"],
        }))
        reappeared = old.get("status") == "NOT_IN_LATEST_LIST_REVIEW"
        card_changed = bool(old and old.get("list_card_sha256") != card_sha)
        needs_recheck = reappeared or card_changed
        reason = ("REAPPEARED_DETAIL_RECHECK_REQUIRED" if reappeared else
                  "LIST_CARD_SEMANTIC_DRIFT_RECHECK_REQUIRED" if card_changed else
                  old.get("reason", "DETAIL_BYTES_NOT_CAPTURED"))
        current[key] = {
            "source_namespace": catalog, "source_event_id": sid,
            "list_url": card["list_url"], "detail_url": card["detail_url"],
            "list_sha": list_sha, "list_card_sha256": card_sha,
            "last_observed": observed,
            "status": ("PENDING_DETAIL_BUDGET" if needs_recheck else
                       old.get("status", "PENDING_DETAIL_BUDGET")),
            "attempts": old.get("attempts", 0),
            "last_attempt": old.get("last_attempt"),
            "reason": reason,
        }
    # Unobserved historical IDs are retained, but cannot be scheduled.
    for key in (set(prior_items) - {c["identity"] for c in cards.values()}):
        if prior_items[key].get("source_namespace") != catalog:
            continue
        current[key] = dict(prior_items[key], status="NOT_IN_LATEST_LIST_REVIEW")
    return {"kind": INVENTORY_KIND, "items": current}



def _validate_archived_review_row(row):
    """Fail closed on corrupted archived FIELD evidence before CAS/readback.

    This is a local integrity/authority schema, not independent HTTP proof.
    Legacy inventory rows without this optional archive extension are kept.
    """
    evidence_keys = ("archive_field_evidence", "archive_field_evidence_current",
                     "archive_field_hold_reason")
    if "archive_field_evidence" not in row:
        if any(key in row for key in evidence_keys[1:]):
            raise ValueError("TPAC_ARCHIVE_FIELD_ORPHAN_FLAG_HOLD")
        return
    ev = row["archive_field_evidence"]
    if (type(ev) is not dict or
            set(ev) != {"detail_body_sha256", "field_roles", "field_holds",
                        "observed_at", "capture_started_at", "decision",
                        "accepted_fields", "published"} or
            ev["decision"] != "ARCHIVED_LIST_DETAIL_IDENTITY_REVIEW_ONLY" or
            type(ev["accepted_fields"]) is not int or ev["accepted_fields"] != 0 or
            ev["published"] is not False or
            type(ev["detail_body_sha256"]) is not str or
            re.fullmatch(r"[0-9a-f]{64}", ev["detail_body_sha256"]) is None or
            type(row.get("archive_field_evidence_current")) is not bool):
        raise ValueError("TPAC_ARCHIVE_FIELD_AUTHORITY_SCHEMA_HOLD")
    current = row["archive_field_evidence_current"]
    if current:
        if (row.get("status") != "ARCHIVED_DETAIL_VERIFIED_ONLY"
                or row.get("reason") != "PARSER_NOT_ACCEPTED_ARCHIVE_ONLY"
                or "archive_field_hold_reason" in row):
            raise ValueError("TPAC_ARCHIVE_FIELD_CURRENTNESS_HOLD")
    elif (row.get("status") != "PENDING_DETAIL_BUDGET" or
          row.get("archive_field_hold_reason") not in ("DETAIL_BYTES_NOT_REPLAYED_HOLD",
              "DETAIL_VALIDATION_FAILED_HOLD", "RESTORED_HISTORICAL_REVIEW_HOLD")):
        raise ValueError("TPAC_ARCHIVE_FIELD_CURRENTNESS_HOLD")
    stamped = ev["observed_at"] or ev["capture_started_at"]
    if ((ev["observed_at"] is not None and ev["capture_started_at"] is not None)
            or type(stamped) is not str or not stamped):
        raise ValueError("TPAC_ARCHIVE_FIELD_TIMESTAMP_HOLD")
    try:
        _time(stamped)
    except (ValueError, TypeError) as exc:
        raise ValueError("TPAC_ARCHIVE_FIELD_TIMESTAMP_HOLD") from exc
    roles = ev["field_roles"]
    holds = ev["field_holds"]
    allowed = {"title": ("EVENT_TITLE",),
               "show_start": ("EVENT_SHOW_START",),
               "show_count": ("SOURCE_SHOW_COUNT",),
               "activity_period": ("ACTIVITY_PERIOD", "EXHIBITION_PERIOD")}
    if (type(roles) is not dict or "title" not in roles
            or set(roles) - set(allowed) or type(holds) is not dict
            or set(holds) != {"date", "price", "venue", "description", "image"}):
        raise ValueError("TPAC_ARCHIVE_FIELD_ROLES_SCHEMA_HOLD")
    sha = ev["detail_body_sha256"]
    url = row["detail_url"]
    for key, candidate in roles.items():
        if (type(candidate) is not dict or
                candidate.get("role") not in allowed[key] or
                candidate.get("source_url") != url or
                candidate.get("source_body_sha256") != sha):
            raise ValueError("TPAC_ARCHIVE_FIELD_ROLE_SOURCE_HOLD")
        if key == "title":
            if (set(candidate) != {"role", "value", "source_url",
                                  "source_body_sha256", "decision"} or
                    candidate.get("decision") != "ARCHIVED_IDENTITY_PARITY_REVIEW_ONLY" or
                    type(candidate.get("value")) is not str or
                    not candidate["value"].strip()):
                raise ValueError("TPAC_ARCHIVE_FIELD_TITLE_HOLD")
            continue
        if (set(candidate) != {"role", "value", "source_url",
                              "source_body_sha256", "observed_at", "decision"} or
                candidate.get("decision") != "ARCHIVED_SEMANTIC_REVIEW_NOT_FIELD_ACCEPTED" or
                candidate.get("observed_at") != stamped):
            raise ValueError("TPAC_ARCHIVE_FIELD_ROLE_AUTHORITY_HOLD")
        value = candidate["value"]
        if key == "show_count":
            if type(value) is not int or not 1 <= value <= 40:
                raise ValueError("TPAC_ARCHIVE_FIELD_SHOW_COUNT_HOLD")
        elif key == "show_start":
            if type(value) is not str:
                raise ValueError("TPAC_ARCHIVE_FIELD_SHOW_START_HOLD")
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("TPAC_ARCHIVE_FIELD_SHOW_START_HOLD") from exc
            if parsed.utcoffset() != timedelta(hours=8):
                raise ValueError("TPAC_ARCHIVE_FIELD_SHOW_START_HOLD")
        elif (type(value) is not list or len(value) != 2
              or any(type(item) is not str for item in value)
              or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", value[0])
              or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", value[1])
              or value[0] > value[1]):
            raise ValueError("TPAC_ARCHIVE_FIELD_PERIOD_HOLD")
    expected_reason = ("ARCHIVED_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE"
                       if len(roles) > 1 else
                       "ARCHIVED_FIELD_SEMANTICS_NOT_VERIFIED")
    for key, field in holds.items():
        if (type(field) is not dict or
                set(field) != {"decision", "value", "hold_reason",
                               "source_url", "source_body_sha256"} or
                field["decision"] != "HOLD" or field["value"] is not None or
                field["source_url"] != url or
                field["source_body_sha256"] != sha or
                field["hold_reason"] != (expected_reason if key == "date" else
                                         "ARCHIVED_FIELD_SEMANTICS_NOT_VERIFIED")):
            raise ValueError("TPAC_ARCHIVE_FIELD_HOLD_AUTHORITY_HOLD")


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
        # Persisted archive-only field receipts must not claim LIVE authority,
        # override a source URL/SHA, or masquerade as a current replay.
        _validate_archived_review_row(row)
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
    with _isolated_writer_lock(lock, "TPAC_INVENTORY_CONCURRENT_WRITER_HOLD"):
        prior = target.read_bytes() if target.exists() else None
        if (None if prior is None else _sha(prior)) != expected_sha:
            raise ValueError("TPAC_INVENTORY_CAS_HOLD")
        payload = _canonical(inventory)
        # Preserve the last complete, validated CAS version before replacement.
        # This is an isolated local recovery journal, never a LIVE/Publisher LKG.
        # A failed archive write must leave the current inventory untouched.
        if prior is not None and prior != payload:
            if not 0 < len(prior) <= 16 * 1024 * 1024:
                raise ValueError("TPAC_INVENTORY_PRIOR_SIZE_HOLD")
            previous_document = json.loads(prior)
            if _canonical(previous_document) != prior:
                raise ValueError("TPAC_INVENTORY_PRIOR_NONCANONICAL_HOLD")
            select_pending_details(previous_document, 0)
            history = folder / "inventory_versions"
            if history.is_symlink():
                raise ValueError("TPAC_INVENTORY_HISTORY_SYMLINK_HOLD")
            history.mkdir(exist_ok=True)
            archived = history / (_sha(prior) + ".json")
            if archived.is_symlink():
                raise ValueError("TPAC_INVENTORY_HISTORY_SYMLINK_HOLD")
            if archived.exists():
                if archived.read_bytes() != prior:
                    raise ValueError("TPAC_INVENTORY_HISTORY_CORRUPT_HOLD")
            else:
                # A killed writer must never expose a partially written SHA-named
                # predecessor. Stage and fsync first, then publish by atomic
                # no-clobber hard link. A restart may safely discard temp files.
                staged = None
                try:
                    with tempfile.NamedTemporaryFile(
                            dir=history, prefix=".history-", delete=False) as saved:
                        staged = Path(saved.name)
                        saved.write(prior)
                        saved.flush()
                        os.fsync(saved.fileno())
                    try:
                        os.link(staged, archived)
                    except FileExistsError as error:
                        raise ValueError("TPAC_INVENTORY_HISTORY_RACE_HOLD") from error
                    # Persist the directory entry before replacing current CAS.
                    if hasattr(os, "O_DIRECTORY"):
                        dir_fd = os.open(history, os.O_RDONLY | os.O_DIRECTORY)
                        try:
                            os.fsync(dir_fd)
                        finally:
                            os.close(dir_fd)
                finally:
                    if staged is not None:
                        staged.unlink(missing_ok=True)
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



def read_detail_inventory_version(repo_root, version_sha):
    """Read a validated immutable local CAS predecessor, never publish/auto-restore."""
    if type(version_sha) is not str or re.fullmatch(r"[0-9a-f]{64}", version_sha) is None:
        raise ValueError("TPAC_INVENTORY_VERSION_SHA_HOLD")
    root = Path(repo_root).resolve()
    folder = root / "_isolated_review" / "tpac"
    history = folder / "inventory_versions"
    archived = history / (version_sha + ".json")
    if any(path.is_symlink() for path in
           (root / "_isolated_review", folder, history, archived)):
        raise ValueError("TPAC_INVENTORY_HISTORY_SYMLINK_HOLD")
    if not archived.is_file():
        raise ValueError("TPAC_INVENTORY_VERSION_MISSING_HOLD")
    raw = archived.read_bytes()
    if not 0 < len(raw) <= 16 * 1024 * 1024 or _sha(raw) != version_sha:
        raise ValueError("TPAC_INVENTORY_HISTORY_CORRUPT_HOLD")
    document = json.loads(raw)
    if _canonical(document) != raw:
        raise ValueError("TPAC_INVENTORY_HISTORY_NONCANONICAL_HOLD")
    select_pending_details(document, 0)
    return document, version_sha



def restore_detail_inventory_row(repo_root, version_sha, identity, expected_current_sha):
    """Recover one archived REVIEW row by CAS; never restore an entire stale snapshot.

    The current document and immutable predecessor must both validate. Other
    identities remain byte-for-byte equivalent at the canonical row level.
    This is isolated inventory recovery, never LIVE field acceptance or publish.
    """
    if type(identity) is not str or re.fullmatch(r"tpac:(program|event):[0-9]+", identity) is None:
        raise ValueError("TPAC_INVENTORY_RECOVERY_IDENTITY_HOLD")
    archived, _ = read_detail_inventory_version(repo_root, version_sha)
    old_row = archived["items"].get(identity)
    if old_row is None:
        raise ValueError("TPAC_INVENTORY_RECOVERY_ROW_MISSING_HOLD")
    current, current_sha = load_detail_inventory(repo_root)
    if current_sha != expected_current_sha:
        raise ValueError("TPAC_INVENTORY_RECOVERY_CAS_HOLD")
    current_row = current["items"].get(identity)
    if current_row is None:
        raise ValueError("TPAC_INVENTORY_RECOVERY_CURRENT_ROW_MISSING_HOLD")
    # A row recovery cannot silently change an event's source identity or URL.
    for field in ("source_namespace", "source_event_id", "detail_url", "list_url", "list_sha"):
        if old_row.get(field) != current_row.get(field):
            raise ValueError("TPAC_INVENTORY_RECOVERY_SOURCE_DRIFT_HOLD")
    # Do not silently promote archived evidence to currentness on rollback.
    recovered = dict(old_row)
    if "archive_field_evidence" in recovered:
        # Historical bytes are not a current replay. Requeue the restored ID
        # explicitly, preserving the evidence but not its previous authority.
        recovered["status"] = "PENDING_DETAIL_BUDGET"
        recovered["reason"] = "RESTORED_HISTORICAL_REVIEW_HOLD"
        recovered["archive_field_evidence_current"] = False
        recovered["archive_field_hold_reason"] = "RESTORED_HISTORICAL_REVIEW_HOLD"
    updated = {"kind": INVENTORY_KIND, "items": dict(current["items"])}
    updated["items"][identity] = recovered
    # Validate the entire merged document before committing.
    select_pending_details(updated, 0)
    result = write_detail_inventory(updated, repo_root, current_sha)
    return {"sha256": result["sha256"], "recovered_identity": identity,
            "decision": "ISOLATED_HISTORICAL_ROW_REVIEW_HOLD_NO_PUBLICATION"}


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
    if any(receipt.get(k) is not None for k in ("http_status", "robots_allowed")):
        raise ValueError("TPAC_ARCHIVE_AUTHORITY_ESCALATION_HOLD")
    # Historical /program has capture_started_at but no per-body observation.
    # Historical /event has original per-body observed_at but no capture_started_at.
    # These are mutually exclusive, independently sourced archive evidence variants.
    # Neither variant supplies native LIVE status/robots or publication authority.
    stamp = receipt.get("capture_started_at")
    observed = receipt.get("observed_at")
    if stamp is not None:
        if not isinstance(stamp, str) or not stamp.strip() or observed is not None:
            raise ValueError("TPAC_ARCHIVE_AUTHORITY_ESCALATION_HOLD")
        _time(stamp)
    elif catalog == "event" and isinstance(observed, str) and observed.strip():
        _time(observed)
    else:
        raise ValueError("TPAC_ARCHIVE_CAPTURE_TIMESTAMP_MISSING_HOLD")
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
        # Mirror the LIVE catalog title contract: official /event link title
        # attributes begin with "連結到", while the event-owned visible title
        # does not. Reject unowned/conflicting titles instead of stripping blindly.
        from scripts.p30_tpac_catalog_topology import _title
        title, title_owned = _title(card, catalog)
        if not title_owned:
            raise ValueError("TPAC_ARCHIVE_CARD_TITLE_HOLD")
        results[sid] = {"identity": "tpac:" + catalog + ":" + sid,
                        "source_event_id": sid, "source_namespace": catalog,
                        "list_url": "https://tpac.org.taipei/" + catalog,
                        "detail_url": url, "title_candidate": title}
    if not results:
        raise ValueError("TPAC_ARCHIVE_NO_VISIBLE_CARDS_HOLD")
    return results




def _archived_detail_date_roles(catalog, article, soup, detail_url, body_sha, stamped):
    """Parse source-owned date semantics without fabricating LIVE field acceptance.

    Exact detail DOM scopes only. A listing/activity date range is never a
    performance start or ticket-sale time. Invalid/ambiguous nodes remain HOLD.
    """
    roles = {}
    def evidence(role, value):
        return {"role": role, "value": value, "source_url": detail_url,
                "source_body_sha256": body_sha, "observed_at": stamped,
                "decision": "ARCHIVED_SEMANTIC_REVIEW_NOT_FIELD_ACCEPTED"}
    try:
        if catalog == "program":
            nodes = [x for x in article.select(".page-program__article-top") if _visible(x)]
            if len(nodes) != 1:
                return roles
            dates = _period(_text(nodes[0]))
            # Performance dates are evidence only when sourced from an exact
            # owned showtime block; the programme period alone is not a show.
            blocks = [x for x in soup.select(".page-program__aside-place-showtimes")
                      if _visible(x) and len(x.select("h3")) == 1
                      and _text(x.select_one("h3")) == "場次"]
        else:
            nodes = [x for x in article.select(".page-event__article-top-text")
                     if _visible(x)]
            if len(nodes) != 1:
                return roles
            children = nodes[0].find_all("div", recursive=False)
            if len(children) != 2:
                return roles
            category = _text(children[0])
            dates = _period(_text(children[1]))
            if not category:
                return roles
            period_role = ("EXHIBITION_PERIOD" if category == "展覽"
                           else "ACTIVITY_PERIOD")
            roles["activity_period"] = evidence(period_role,
                [dates[0].isoformat(), dates[1].isoformat()])
            if category == "展覽":
                # Exhibition range must NOT become show start or opening hours.
                return roles
            blocks = [x for x in soup.select(".page-event__aside-place-showtimes")
                      if _visible(x) and len(x.select("h3")) == 1
                      and _text(x.select_one("h3")) == "場次"]
        if len(blocks) != 1:
            return roles
        labels = blocks[0].select("ul > li > p")
        if not 1 <= len(labels) <= 40 or any(not _visible(x) for x in labels):
            return roles
        times = []
        for node in labels:
            match = SHOW.fullmatch(_text(node))
            if match is None:
                return roles
            moment = datetime.fromisoformat(
                match[1] + "T" + match[3] + ":00+08:00")
            if (DAY[moment.weekday()] != match[2]
                    or not dates[0] <= moment.date() <= dates[1]):
                return roles
            times.append(moment)
        if times != sorted(set(times)):
            return roles
        # The date may now be historical; never filter it by current time or
        # claim a future event, price or availability.
        roles["show_start"] = evidence("EVENT_SHOW_START", times[0].isoformat())
        roles["show_count"] = evidence("SOURCE_SHOW_COUNT", len(times))
    except (ValueError, TypeError, KeyError, IndexError, OverflowError):
        # Bad dates or unexpected DOM can only remove REVIEW candidates.
        return {}
    return roles


def bind_archived_detail_identity(catalog, list_raw, list_receipt,
                                  event_id, detail_raw, detail_receipt):
    """Compare sealed LIST and same-ID DETAIL bytes/identity (OFFLINE only).

    Archive receipt provenance does not prove fresh HTTP, robots or live access.
    Only the source-owned DETAIL article H1 is reviewed, never published.
    """
    if (catalog not in ("program", "event")
            or type(event_id) is not str
            or re.fullmatch(r"[1-9][0-9]{0,9}", event_id) is None):
        raise ValueError("TPAC_ARCHIVE_DETAIL_ID_SCOPE_HOLD")
    cards = _archived_cards(catalog, list_raw, list_receipt)
    card = cards.get(event_id)
    if card is None or card["identity"] != "tpac:" + catalog + ":" + event_id:
        raise ValueError("TPAC_ARCHIVE_DETAIL_NOT_IN_SAME_LIST_HOLD")
    soup = _archived_body(detail_raw, detail_receipt, card["detail_url"],
                          catalog, event_id)
    selector = ("article.page-program__article" if catalog == "program"
                else "article.page-event__article")
    articles = [node for node in soup.select(selector) if _visible(node)]
    if len(articles) != 1:
        raise ValueError("TPAC_ARCHIVE_DETAIL_OWNED_ARTICLE_HOLD")
    titles = [node for node in articles[0].select("h1") if _visible(node)]
    if len(titles) != 1:
        raise ValueError("TPAC_ARCHIVE_DETAIL_OWNED_H1_HOLD")
    name = _text(titles[0])
    if name != card["title_candidate"]:
        raise ValueError("TPAC_ARCHIVE_LIST_DETAIL_TITLE_PARITY_HOLD")
    stamped = (detail_receipt.get("observed_at")
               or detail_receipt.get("capture_started_at"))
    date_roles = _archived_detail_date_roles(
        catalog, articles[0], soup, card["detail_url"],
        detail_receipt["body_sha256"], stamped)
    return {
        "kind": "TPAC_ARCHIVED_SAME_ID_DETAIL_REVIEW_V1",
        "identity": card["identity"], "source_namespace": catalog,
        "source_event_id": event_id,
        "list_url": card["list_url"], "detail_url": card["detail_url"],
        "list_body_sha256": list_receipt["body_sha256"],
        "detail_body_sha256": detail_receipt["body_sha256"],
        "capture_started_at": detail_receipt.get("capture_started_at"),
        "observed_at": detail_receipt.get("observed_at"),
        "field_roles": {
            "title": {"role": "EVENT_TITLE", "value": name,
                      "source_url": card["detail_url"],
                      "source_body_sha256": detail_receipt["body_sha256"],
                      "decision": "ARCHIVED_IDENTITY_PARITY_REVIEW_ONLY"},
            **date_roles
        },
        # The archived H1 proves identity only. These field roles are explicit
        # UNKNOWNs, not values inferred from the card, surrounding text, or
        # unverified historical HTML. This makes partial replay safe for LKG.
        "field_holds": {
            role: {"decision": "HOLD", "value": None,
                   "hold_reason": ("ARCHIVED_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE"
                                    if role == "date" and date_roles else
                                    "ARCHIVED_FIELD_SEMANTICS_NOT_VERIFIED"),
                   "source_url": card["detail_url"],
                   "source_body_sha256": detail_receipt["body_sha256"]}
            for role in ("date", "price", "venue", "description", "image")
        },
        "decision": "ARCHIVED_LIST_DETAIL_IDENTITY_REVIEW_ONLY",
        "historical_replay_only": True, "native_get_allowed": False,
        "source_requests_performed": 0, "accepted_fields": 0,
        "formal_field_pass": False, "published": False,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }


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
            # A frozen archive CAS must not silently rebind an existing ID to
            # another LIST body. New captures require a separate snapshot root.
            if old and old.get("list_sha") != _sha(raw):
                raise ValueError("TPAC_ARCHIVE_SNAPSHOT_DRIFT_HOLD")
            status, reason = "PENDING_DETAIL_BUDGET", "DETAIL_BYTES_NOT_CAPTURED"
            if sid in details:
                record = details[sid]
                if not isinstance(record, dict) or set(record) != {"detail_file", "receipt"}:
                    raise ValueError("TPAC_ARCHIVE_DETAIL_SCHEMA_HOLD")
                # Require the source-owned article H1 to match the exact LIST card
                # before counting this archived DETAIL as identity-verified.
                # An invalid individual DETAIL must not erase unrelated, already
                # validated archived rows. Keep the failed identity in backlog;
                # never accept its stale evidence as current.
                try:
                    # Missing/unreadable bytes are per-event failures, not LIST
                    # authority failures. Reject non-regular files before reading.
                    detail_path = Path(record["detail_file"])
                    if not detail_path.is_file():
                        raise OSError("DETAIL_NOT_REGULAR_FILE")
                    body = detail_path.read_bytes()
                    bound = bind_archived_detail_identity(catalog, raw, receipt, sid,
                                                         body, record["receipt"])
                except (OSError, ValueError) as error:
                    is_io = isinstance(error, OSError)
                    status = "PENDING_DETAIL_BUDGET"
                    reason = ("ARCHIVED_DETAIL_IO_HOLD" if is_io
                              else "ARCHIVED_DETAIL_VALIDATION_HOLD")
                    counts["archive_identity_hold"] += 1
                    counts["pending_detail_budget"] += 1
                    rows[key] = {"source_namespace": catalog, "source_event_id": sid,
                                 "list_url": card["list_url"], "detail_url": card["detail_url"],
                                 "list_sha": _sha(raw), "last_observed": None,
                                 "status": status, "attempts": old.get("attempts", 0),
                                 "last_attempt": old.get("last_attempt"), "reason": reason}
                    if "archive_field_evidence" in old:
                        rows[key]["archive_field_evidence"] = old["archive_field_evidence"]
                        rows[key]["archive_field_evidence_current"] = False
                        rows[key]["archive_field_hold_reason"] = "DETAIL_VALIDATION_FAILED_HOLD"
                    diagnostics[key] = {"status": status, "reason": reason,
                                        # Avoid exposing the caller's local filesystem path.
                                        "detail_error": ("DETAIL_FILE_UNREADABLE" if is_io
                                                         else str(error))}
                    continue
                # Persist exact body-bound FIELD REVIEW evidence in archive-only
                # CAS inventory. Never promote archived fields to LIVE/accepted.
                archive_evidence = {
                    "detail_body_sha256": bound["detail_body_sha256"],
                    "field_roles": bound["field_roles"],
                    "field_holds": bound["field_holds"],
                    "observed_at": bound["observed_at"],
                    "capture_started_at": bound["capture_started_at"],
                    "decision": bound["decision"],
                    "accepted_fields": 0, "published": False,
                }
                status, reason = "ARCHIVED_DETAIL_VERIFIED_ONLY", "PARSER_NOT_ACCEPTED_ARCHIVE_ONLY"
                counts["detail_available"] += 1
            else:
                # A previous inventory status is only historical metadata; it
                # does NOT retain the DETAIL bytes or original receipt. A partial
                # manifest cannot prove the old body is still replayable. Keep
                # history in prior CAS versions, and requeue this ID until the
                # caller supplies exact raw bytes + receipt for fresh validation.
                # Never inflate C20 capture coverage from metadata alone.
                if (old.get("status") == "ARCHIVED_DETAIL_VERIFIED_ONLY"
                        and old.get("list_sha") == _sha(raw)
                        and old.get("reason") == "PARSER_NOT_ACCEPTED_ARCHIVE_ONLY"):
                    reason = "PRIOR_ARCHIVED_DETAIL_BYTES_NOT_REPLAYED_HOLD"
                counts["pending_detail_budget"] += 1
            rows[key] = {"source_namespace": catalog, "source_event_id": sid,
                         "list_url": card["list_url"], "detail_url": card["detail_url"],
                         "list_sha": _sha(raw), "last_observed": None,
                         "status": status, "attempts": old.get("attempts", 0),
                         "last_attempt": old.get("last_attempt"), "reason": reason}
            if sid in details:
                rows[key]["archive_field_evidence"] = archive_evidence
                rows[key]["archive_field_evidence_current"] = True
            elif "archive_field_evidence" in old:
                # Missing replay cannot revalidate old bytes. Keep prior LKG
                # evidence intact but explicitly mark it historical and held.
                rows[key]["archive_field_evidence"] = old["archive_field_evidence"]
                rows[key]["archive_field_evidence_current"] = False
                rows[key]["archive_field_hold_reason"] = "DETAIL_BYTES_NOT_REPLAYED_HOLD"
            diagnostics[key] = {"status": status, "reason": reason}
    # Do not erase rows from other snapshots; archive replay is not LIVE reconciliation.
    inventory = {"kind": INVENTORY_KIND, "items": rows}
    result = write_detail_inventory(inventory, archive_root, expected)
    return {"decision": "ARCHIVED_SOURCE_VERIFIED_BODY_ONLY_NO_PUBLICATION",
            "inventory": result, "counts": counts, "diagnostics": diagnostics,
            "next_detail_ids": select_pending_details(inventory),
            "published": 0, "accepted_fields": 0}


def build_archived_field_review_export(inventory, inventory_sha):
    """Normalize archived LIST->DETAIL->FIELD evidence into a read-only ledger.

    A complete current archived replay supplies REVIEW candidates, never an
    accepted field. Missing, stale or quarantined DETAIL rows supply HOLD/UNKNOWN
    without leaking historical values as current. Neither reads native HTTP nor
    mutates the isolated CAS, Golden or formal PWA data.
    """
    if (type(inventory_sha) is not str
            or re.fullmatch(r"[0-9a-f]{64}", inventory_sha) is None):
        raise ValueError("TPAC_ARCHIVE_FIELD_EXPORT_SHA_HOLD")
    select_pending_details(inventory, 0)  # Reuse persistent evidence authority validation.
    field_names = ("title", "date", "show_start", "show_count", "activity_period",
                   "price", "venue", "description", "image")
    items = {}
    current_count = 0
    for identity, row in sorted(inventory["items"].items()):
        evidence = row.get("archive_field_evidence")
        current = row.get("archive_field_evidence_current") is True
        if current:
            current_count += 1
        observed = ((evidence.get("observed_at") or evidence.get("capture_started_at"))
                    if evidence is not None else None)
        historical_sha = (evidence["detail_body_sha256"]
                          if evidence is not None else None)
        roles = evidence["field_roles"] if evidence is not None and current else {}
        holds = evidence["field_holds"] if evidence is not None and current else {}
        fields = {}
        for name in field_names:
            role = roles.get(name)
            held = holds.get(name)
            if role is not None:
                # A source-owned role is only REVIEW, including verified H1.
                value, field_role, decision = role["value"], role["role"], "REVIEW"
                hold_reason = "ARCHIVED_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE"
            else:
                value, field_role, decision = None, "UNKNOWN", "HOLD"
                hold_reason = (
                    row.get("archive_field_hold_reason")
                    if evidence is not None and not current else
                    (held["hold_reason"] if held is not None else
                     "ARCHIVED_FIELD_ROLE_NOT_VERIFIED_HOLD"))
            fields[name] = {
                "value": value, "role": field_role,
                "event_id": row["source_event_id"],
                "source_url": row["detail_url"], "observed_at": observed,
                "source_body_sha256": historical_sha,
                "decision": decision, "hold_reason": hold_reason,
            }
        items[identity] = {
            "identity": identity, "source_namespace": row["source_namespace"],
            "event_id": row["source_event_id"],
            "list_source_url": row.get("list_url"),
            "list_body_sha256": row.get("list_sha"),
            "detail_source_url": row["detail_url"],
            "historical_detail_body_sha256": historical_sha,
            "archive_evidence_current": current,
            "status": row.get("status"),
            "fields": fields,
        }
    return {
        "kind": "TPAC_ISOLATED_FIELD_EVIDENCE_LEDGER_V1",
        "source_scope": "ARCHIVED_OFFLINE_REVIEW_ONLY",
        "inventory_sha256": inventory_sha,
        "records": items,
        "counts": {"events": len(items), "archived_detail_current": current_count,
                   "pending_or_held": len(items) - current_count},
        "new_official_get": 0, "accepted_fields": 0, "published": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }



def build_archived_field_candidate_delta(previous, current):
    """Diff two validated isolated FIELD ledgers; never promote REVIEW to accepted.

    Candidate rows are scoped to current REVIEW evidence. HOLD transitions
    explicitly invalidate the affected field, not the unaffected siblings.
    Receipt-only observations do not change semantic candidate values.
    """
    if (not isinstance(previous, dict) or not isinstance(current, dict)
            or previous.get("kind") != "TPAC_ISOLATED_FIELD_EVIDENCE_LEDGER_V1"
            or current.get("kind") != "TPAC_ISOLATED_FIELD_EVIDENCE_LEDGER_V1"
            or previous.get("source_scope") != "ARCHIVED_OFFLINE_REVIEW_ONLY"
            or current.get("source_scope") != "ARCHIVED_OFFLINE_REVIEW_ONLY"
            or previous.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
            or current.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
            or any(doc.get("accepted_fields") != 0 or doc.get("published") != 0
                   for doc in (previous, current))):
        raise ValueError("TPAC_FIELD_DELTA_AUTHORITY_HOLD")
    before, after = previous.get("records"), current.get("records")
    if not isinstance(before, dict) or not isinstance(after, dict) or not after:
        raise ValueError("TPAC_FIELD_DELTA_EMPTY_OR_SCHEMA_HOLD")
    if set(before) - set(after):
        raise ValueError("TPAC_FIELD_DELTA_DESTRUCTIVE_REMOVAL_HOLD")
    changed, candidates = {}, {}
    for identity, row in sorted(after.items()):
        if not isinstance(row, dict) or row.get("identity") != identity:
            raise ValueError("TPAC_FIELD_DELTA_IDENTITY_HOLD")
        old = before.get(identity)
        if old is not None and (not isinstance(old, dict)
                                or old.get("identity") != identity
                                or any(old.get(key) != row.get(key) for key in
                                       ("source_namespace", "event_id", "detail_source_url"))):
            raise ValueError("TPAC_FIELD_DELTA_SOURCE_IDENTITY_HOLD")
        fields = row.get("fields")
        old_fields = old.get("fields", {}) if old is not None else {}
        if not isinstance(fields, dict) or not fields or not isinstance(old_fields, dict):
            raise ValueError("TPAC_FIELD_DELTA_FIELDS_HOLD")
        event_changes, candidate_fields = {}, {}
        # Source currentness is a semantic authority transition, unlike a
        # receipt/body SHA-only observation. Keep it separate from FIELD names.
        if old is not None:
            old_current = old.get("archive_evidence_current")
            new_current = row.get("archive_evidence_current")
            if not isinstance(old_current, bool) or not isinstance(new_current, bool):
                raise ValueError("TPAC_FIELD_DELTA_CURRENTNESS_SCHEMA_HOLD")
            if old_current != new_current:
                event_changes["__source_currentness__"] = {
                    "transition": ("CURRENT_TO_STALE" if old_current
                                   else "STALE_TO_CURRENT"),
                    "current_decision": "REVIEW" if new_current else "HOLD",
                    "current_role": "SOURCE_CURRENTNESS",
                    "current_value": new_current,
                    "hold_reason": (None if new_current
                                    else "ARCHIVED_SOURCE_NOT_CURRENT_HOLD"),
                }
        for name, field in sorted(fields.items()):
            if not isinstance(field, dict) or field.get("decision") not in ("REVIEW", "HOLD"):
                raise ValueError("TPAC_FIELD_DELTA_FIELD_AUTHORITY_HOLD")
            if field.get("event_id") != row["event_id"] or field.get("source_url") != row["detail_source_url"]:
                raise ValueError("TPAC_FIELD_DELTA_PROVENANCE_HOLD")
            if field["decision"] == "REVIEW":
                if not row.get("archive_evidence_current") or field.get("value") is None:
                    raise ValueError("TPAC_FIELD_DELTA_STALE_REVIEW_HOLD")
                candidate_fields[name] = {"value": field["value"], "role": field["role"],
                                          "decision": "REVIEW_ONLY_NOT_ACCEPTED"}
            elif field.get("value") is not None:
                raise ValueError("TPAC_FIELD_DELTA_HELD_VALUE_HOLD")
            prior = old_fields.get(name)
            if prior is not None and not isinstance(prior, dict):
                raise ValueError("TPAC_FIELD_DELTA_PRIOR_FIELD_HOLD")
            semantic = lambda item: None if item is None else (
                item.get("decision"), item.get("role"), item.get("value"),
                item.get("hold_reason"))
            if semantic(field) != semantic(prior):
                event_changes[name] = {
                    "transition": ((prior.get("decision") if prior else "ABSENT")
                                   + "_TO_" + field["decision"]),
                    "current_decision": field["decision"],
                    "current_role": field["role"],
                    "current_value": field["value"] if field["decision"] == "REVIEW" else None,
                    "hold_reason": field.get("hold_reason"),
                }
        # A disappeared field is an explicit candidate withdrawal, not an
        # unchanged value. Preserve siblings while preventing stale REVIEW reuse.
        for name in sorted(set(old_fields) - set(fields)):
            prior = old_fields[name]
            if not isinstance(prior, dict) or prior.get("decision") not in ("REVIEW", "HOLD"):
                raise ValueError("TPAC_FIELD_DELTA_PRIOR_FIELD_HOLD")
            event_changes[name] = {
                "transition": prior["decision"] + "_TO_ABSENT",
                "current_decision": "HOLD",
                "current_role": "UNKNOWN",
                "current_value": None,
                "hold_reason": "FIELD_REMOVED_FROM_CURRENT_EVIDENCE_HOLD",
            }
        # Persist source-currentness with the candidate, not only the transient
        # delta. Consumers must not infer freshness from a previous REVIEW value.
        source_current = row.get("archive_evidence_current")
        if not isinstance(source_current, bool):
            raise ValueError("TPAC_FIELD_DELTA_CURRENTNESS_SCHEMA_HOLD")
        candidates[identity] = {"identity": identity, "source_namespace": row["source_namespace"],
                                "event_id": row["event_id"], "fields": candidate_fields,
                                "source_current": source_current,
                                "decision": "ISOLATED_REVIEW_CANDIDATE_ONLY"}
        if event_changes:
            changed[identity] = event_changes
    return {"kind": "TPAC_ISOLATED_FIELD_CANDIDATE_DELTA_V1",
            "previous_inventory_sha256": previous.get("inventory_sha256"),
            "current_inventory_sha256": current.get("inventory_sha256"),
            "changed": changed, "candidates": candidates,
            "counts": {"events": len(after), "changed_events": len(changed)},
            "accepted_fields": 0, "published": 0,
            "release_state": "HARD_HOLD_NO_PUBLICATION"}



def write_archived_field_candidate_snapshot(delta, repo_root, expected_sha=None):
    """Persist a REVIEW-only candidate snapshot with CAS and sibling preservation.

    The snapshot is deliberately separate from the event LKG and formal data.
    A failed compare-and-swap cannot replace another process's candidate state.
    """
    if (not isinstance(delta, dict)
            or delta.get("kind") != "TPAC_ISOLATED_FIELD_CANDIDATE_DELTA_V1"
            or delta.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
            or delta.get("accepted_fields") != 0 or delta.get("published") != 0
            or not isinstance(delta.get("candidates"), dict)
            or not delta["candidates"]
            or not isinstance(delta.get("changed"), dict)):
        raise ValueError("TPAC_CANDIDATE_SNAPSHOT_AUTHORITY_HOLD")
    for identity, row in delta["candidates"].items():
        if (not isinstance(row, dict) or row.get("identity") != identity
                or row.get("decision") != "ISOLATED_REVIEW_CANDIDATE_ONLY"
                or not isinstance(row.get("fields"), dict)):
            raise ValueError("TPAC_CANDIDATE_SNAPSHOT_IDENTITY_HOLD")
        for field in row["fields"].values():
            if not isinstance(field, dict) or field.get("decision") != "REVIEW_ONLY_NOT_ACCEPTED":
                raise ValueError("TPAC_CANDIDATE_SNAPSHOT_FIELD_HOLD")
    if expected_sha is not None and (not isinstance(expected_sha, str)
                                     or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None):
        raise ValueError("TPAC_CANDIDATE_SNAPSHOT_EXPECTED_SHA_HOLD")
    root = Path(repo_root).resolve() / "_isolated_archive_replay"
    if root.is_symlink():
        raise ValueError("TPAC_CANDIDATE_SNAPSHOT_SYMLINK_HOLD")
    root.mkdir(parents=True, exist_ok=True)
    target = root / "field_candidate_lkg.json"
    if target.is_symlink():
        raise ValueError("TPAC_CANDIDATE_SNAPSHOT_SYMLINK_HOLD")
    with _isolated_writer_lock(root / ".field_candidate.lock", "TPAC_CANDIDATE_CONCURRENT_WRITER_HOLD"):
        prior = target.read_bytes() if target.exists() else None
        actual = _sha(prior) if prior is not None else None
        if actual != expected_sha:
            raise ValueError("TPAC_CANDIDATE_SNAPSHOT_CAS_HOLD")
        if prior is not None:
            try:
                old = json.loads(prior)
                if (_canonical(old) != prior
                        or old.get("kind") != "TPAC_ISOLATED_FIELD_CANDIDATE_SNAPSHOT_V1"
                        or old.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
                        or old.get("accepted_fields") != 0 or old.get("published") != 0
                        or not isinstance(old.get("candidates"), dict)
                        or set(old["candidates"]) - set(delta["candidates"])):
                    raise ValueError("TPAC_CANDIDATE_PRIOR_CORRUPT_OR_REMOVAL_HOLD")
            except (TypeError, json.JSONDecodeError) as exc:
                raise ValueError("TPAC_CANDIDATE_PRIOR_CORRUPT_OR_REMOVAL_HOLD") from exc
        snapshot = {"kind": "TPAC_ISOLATED_FIELD_CANDIDATE_SNAPSHOT_V1",
                    "inventory_sha256": delta.get("current_inventory_sha256"),
                    "candidates": delta["candidates"],
                    "release_state": "HARD_HOLD_NO_PUBLICATION",
                    "accepted_fields": 0, "published": 0}
        payload = _canonical(snapshot)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=root, prefix=".candidate-",
                                             delete=False) as out:
                temp_path = Path(out.name)
                out.write(payload)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp_path, target)
            temp_path = None
            if hasattr(os, "O_DIRECTORY"):
                fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        return {"decision": "ISOLATED_FIELD_CANDIDATE_SNAPSHOT_COMMITTED_NOT_FORMAL",
                "sha256": _sha(payload), "events": len(snapshot["candidates"]),
                "accepted_fields": 0, "published": 0}



def load_archived_field_candidate_snapshot(repo_root, expected_sha):
    """Read back the exact isolated candidate LKG after restart; no GET or publication."""
    if not isinstance(expected_sha, str) or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None:
        raise ValueError("TPAC_CANDIDATE_READ_EXPECTED_SHA_HOLD")
    root = Path(repo_root).resolve() / "_isolated_archive_replay"
    target = root / "field_candidate_lkg.json"
    if root.is_symlink() or target.is_symlink() or not target.is_file():
        raise ValueError("TPAC_CANDIDATE_READ_MISSING_OR_SYMLINK_HOLD")
    raw = target.read_bytes()
    if _sha(raw) != expected_sha:
        raise ValueError("TPAC_CANDIDATE_READ_CAS_HOLD")
    try:
        snapshot = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("TPAC_CANDIDATE_READ_SCHEMA_HOLD") from exc
    if (not isinstance(snapshot, dict) or _canonical(snapshot) != raw
            or set(snapshot) != {"kind", "inventory_sha256", "candidates",
                                 "release_state", "accepted_fields", "published"}
            or snapshot["kind"] != "TPAC_ISOLATED_FIELD_CANDIDATE_SNAPSHOT_V1"
            or snapshot["release_state"] != "HARD_HOLD_NO_PUBLICATION"
            or snapshot["accepted_fields"] != 0 or snapshot["published"] != 0
            or not isinstance(snapshot["candidates"], dict) or not snapshot["candidates"]):
        raise ValueError("TPAC_CANDIDATE_READ_SCHEMA_HOLD")
    for identity, row in snapshot["candidates"].items():
        if (not isinstance(row, dict) or row.get("identity") != identity
                or row.get("decision") != "ISOLATED_REVIEW_CANDIDATE_ONLY"
                or not isinstance(row.get("fields"), dict)):
            raise ValueError("TPAC_CANDIDATE_READ_IDENTITY_HOLD")
        for field in row["fields"].values():
            if not isinstance(field, dict) or field.get("decision") != "REVIEW_ONLY_NOT_ACCEPTED":
                raise ValueError("TPAC_CANDIDATE_READ_FIELD_HOLD")
    return snapshot


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
        unreadable = set()
        for sid, record in details.items():
            if not isinstance(record, dict) or set(record) != {"detail_file", "receipt"}:
                raise ValueError("TPAC_INVENTORY_CLI_DETAIL_SCHEMA_HOLD")
            # Isolate an unavailable DETAIL to its identity; LIST failures remain fatal.
            try:
                detail_path = Path(record["detail_file"])
                if not detail_path.is_file():
                    raise OSError("DETAIL_NOT_REGULAR_FILE")
                body = detail_path.read_bytes()
            except (OSError, TypeError, ValueError):
                unreadable.add(sid)
                continue
            pairs[sid] = {"body": body, "receipt": record["receipt"]}
        plan = None
        if pairs:
            planner = refresh_event_plan if catalog == "event" else refresh_plan
            plan = planner(raw, entry["list_receipt"], pairs,
                           review_prior, now)
        for sid, card in cards.items():
            key = card["identity"]
            row = staged["items"][key]
            if sid not in pairs:
                if sid in unreadable:
                    row["status"] = "PENDING_DETAIL_BUDGET"
                    row["reason"] = "DETAIL_IO_HOLD"
                    counts["pending_detail_budget"] += 1
                    diagnostics[key] = {"status": row["status"], "reason": row["reason"]}
                    continue
                # A prior REVIEW status is not proof of replayable DETAIL bytes
                # in this manifest. Preserve the separate REVIEW LKG, but
                # restore this identity to the capture backlog (no LIVE GET).
                row["status"] = "PENDING_DETAIL_BUDGET"
                row["reason"] = "DETAIL_BYTES_NOT_REPLAYED_HOLD"
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
