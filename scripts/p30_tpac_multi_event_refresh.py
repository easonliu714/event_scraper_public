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
    holds = ["HALL_NOT_VERIFIED"]
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
        "location": "臺北表演藝術中心", "price": "",
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
    return event


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
        elif updated[key] == event:
            same += 1
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
        elif updated[identity] == event:
            same += 1
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


def write_isolated_plan(plan, repo_root, expected_sha=None):
    """Atomic/CAS isolated REVIEW snapshot; no formal output paths."""
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
        payload = _canonical({"kind": KIND, "events": plan["events"]})
        new_sha = _sha(payload)
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
                    "sha256": new_sha, "rows": len(plan["events"])}
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
    finally:
        lock.unlink(missing_ok=True)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="TPAC multi-event offline REVIEW refresh; no GET or PUBLISH")
    # Explicit namespace prevents a /event archive from silently entering the
    # legacy /program planner; the default preserves existing program callers.
    ap.add_argument("--catalog", choices=("program", "event"), default="program")
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--expected-sha")
    args = ap.parse_args(argv)
    data = json.loads(args.input.read_text(encoding="utf-8"))
    if data.get("catalog", "program") != args.catalog:
        raise ValueError("TPAC_MANIFEST_CATALOG_MISMATCH_HOLD")
    pairs = {sid: {"body": Path(row["detail_file"]).read_bytes(), "receipt": row["receipt"]}
             for sid, row in data["details"].items()}
    planner = refresh_event_plan if args.catalog == "event" else refresh_plan
    plan = planner(Path(data["list_file"]).read_bytes(), data["list_receipt"],
                   pairs, data["prior"], _time(data["now"]))
    if plan["decision"] == "REVIEW_SNAPSHOT_READY_NOT_FORMAL":
        result = write_isolated_plan(plan, args.repo_root, args.expected_sha)
    else:
        result = {"decision": plan["decision"], "sha256": None, "rows": plan["new_count"]}
    print(json.dumps({"result": result,
                      "counts": {k: plan[k] for k in ("source_cards", "qualified", "added", "changed",
                                                    "unchanged", "retained_previous")},
                      "rejected": plan["rejected"],
                      "published": 0}, ensure_ascii=False, sort_keys=True))
    return 0 if result["decision"] == "ISOLATED_REVIEW_LKG_COMMITTED_NOT_FORMAL" else 49


if __name__ == "__main__":
    raise SystemExit(main())
