"""TPAC /event DETAIL role-specific review for official original native bodies.

Activity /event is separate from performance /program:
- exhibitions: EXHIBITION_PERIOD, never EVENT_SHOW_START from date range;
- guided tours: exact detail-owned session times may be EVENT_SHOW_START;
- LIST/DETAIL range contradictions HOLD only the range, not trustworthy
  same-ID DETAIL-labelled event/session fields.
No new network, formal JSON write, Golden update or recurring publisher.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.p30_tpac_catalog_topology import discover_catalog
from scripts.p30_tpac_multi_event_refresh import (
    _body, _period, _receipt, _text, _visible, SHOW, DAY,
)

MAX_SHOWS = 40
TPE = timezone(timedelta(hours=8))


def inspect_event_detail(card, raw, receipt, now):
    """Return source-owned partial candidate; unsupported semantics remain HOLD."""
    if card.get("kind") != "event":
        raise ValueError("TPAC_ACTIVITY_WRONG_CATALOG_HOLD")
    url = card["detail_url"]
    _receipt(raw, receipt, url, now)
    soup = _body(raw)
    article = [x for x in soup.select("article.page-event__article") if _visible(x)]
    if len(article) != 1 or len(article[0].select("h1")) != 1:
        raise ValueError("TPAC_ACTIVITY_DETAIL_SCOPE_HOLD")
    name = _text(article[0].select_one("h1"))
    if name != card["title_candidate"]:
        raise ValueError("TPAC_ACTIVITY_DETAIL_TITLE_IDENTITY_HOLD")
    parts = [n for n in article[0].select(".page-event__article-top-text")
             if _visible(n)]
    if len(parts) != 1:
        raise ValueError("TPAC_ACTIVITY_DETAIL_PERIOD_OWNERSHIP_HOLD")
    children = parts[0].find_all("div", recursive=False)
    if len(children) != 2:
        raise ValueError("TPAC_ACTIVITY_DETAIL_PERIOD_CATEGORY_SCOPE_HOLD")
    category = _text(children[0])
    period = _period(_text(children[1]))
    if not category or category != card["list_event_category"]:
        raise ValueError("TPAC_ACTIVITY_LIST_DETAIL_CATEGORY_PARITY_HOLD")
    hold_fields = ["PRICE_NOT_INDEPENDENTLY_ACCEPTED", "HALL_SPECIFIC_NOT_ACCEPTED"]
    try:
        if _period(card["list_date_label"]) != period:
            hold_fields.append("LIST_DETAIL_ACTIVITY_PERIOD_CONFLICT_HOLD")
    except ValueError:
        hold_fields.append("LIST_ACTIVITY_PERIOD_UNVERIFIED_HOLD")
    now = now.astimezone(timezone.utc)
    if period[1] < now.astimezone(TPE).date():
        raise ValueError("TPAC_ACTIVITY_ALREADY_ENDED_HOLD")
    roles = {"EVENT_TITLE": name}
    showtimes = []
    if category == "展覽":
        roles["EXHIBITION_PERIOD"] = [x.isoformat() for x in period]
        # '每日晚上8:00至凌晨01:00' is not an event performance start.
        hold_fields.append("EXHIBITION_OPEN_HOURS_NOT_MACHINE_ACCEPTED")
    else:
        sections = [x for x in soup.select(".page-event__aside-place-showtimes")
                    if _visible(x) and len(x.select("h3")) == 1
                    and _text(x.select_one("h3")) == "場次"]
        if len(sections) == 1:
            labels = sections[0].select("ul > li > p")
            if not 1 <= len(labels) <= MAX_SHOWS:
                raise ValueError("TPAC_ACTIVITY_SHOW_COUNT_HOLD")
            for node in labels:
                m = SHOW.fullmatch(_text(node))
                if not m:
                    raise ValueError("TPAC_ACTIVITY_SHOW_ROLE_HOLD")
                at = datetime.fromisoformat(m[1] + "T" + m[3] + ":00+08:00")
                if DAY[at.weekday()] != m[2] or not period[0] <= at.date() <= period[1]:
                    raise ValueError("TPAC_ACTIVITY_SHOW_WEEKDAY_OR_PERIOD_HOLD")
                showtimes.append(at)
            if showtimes != sorted(set(showtimes)):
                raise ValueError("TPAC_ACTIVITY_SHOW_DUPLICATE_OR_ORDER_HOLD")
            future = [d for d in showtimes if d.astimezone(timezone.utc) > now]
            if not future:
                raise ValueError("TPAC_ACTIVITY_NO_FUTURE_SHOW_HOLD")
            roles["NEXT_EVENT_SHOW_START"] = future[0].isoformat()
            roles["EXACT_EVENT_SHOW_COUNT"] = len(future)
        else:
            hold_fields.append("ACTIVITY_SHOW_START_NOT_VERIFIED")
    return {
        "decision": "SOURCE_OWNED_PARTIAL_FIELDS_REQUIRE_INDEPENDENT_ACCEPTANCE",
        "identity": card["identity"],
        "source_event_id": card["source_event_id"],
        "url": url, "title": name, "activity_kind": category,
        "verified_core_roles": roles,
        "source_show_count": len(showtimes),
        "held_fields": hold_fields,
        "list_period": card["list_date_label"],
        "detail_period": [x.isoformat() for x in period],
        "detail_body_sha256": receipt["body_sha256"],
        "list_body_sha256": card.get("list_sha256"),
        "observed_at": receipt["observed_at"],
        "published": False,
        "formal_field_pass": False, "golden_accepted": False,
    }


def review_pinned_native(source_dir, now):
    """Replay exact already captured official source bytes without GET."""
    source_dir = Path(source_dir)
    native = json.loads((source_dir / "tpac_event_catalog_receipt.json").read_text())
    if (native.get("kind") != "EVENTRADAR_TPAC_EVENT_TWO_DETAILS_SINGLE_AUDIT"
            or native.get("decision") != "NATIVE_BODY_CAPTURED_FOR_INDEPENDENT_REPLAY_ONLY"
            or native.get("successful_get") != 4
            or native.get("requested_ids") != ["1301", "2072"]):
        raise ValueError("TPAC_ACTIVITY_NATIVE_SOURCE_INCOMPLETE_HOLD")
    raw = (source_dir / "event_list.html").read_bytes()
    cards = discover_catalog("event", raw, native["source_receipts"]["list"], now)
    rows = {}
    for event_id in native["requested_ids"]:
        card = cards.get(event_id)
        if not card:
            raise ValueError("TPAC_ACTIVITY_EVENT_ID_NOT_IN_LIST_HOLD")
        data = (source_dir / ("event_" + event_id + "_detail.html")).read_bytes()
        receipt = native["source_receipts"][event_id]
        rows[event_id] = inspect_event_detail(card, data, receipt, now)
    return {"kind": "TPAC_EVENT_TWO_NATIVE_REPLAY_REVIEW_NOT_PUBLICATION",
            "checked_at": now.isoformat(), "source_list_count": len(cards),
            "detail_count": len(rows), "records": rows,
            "native_again": 0, "published": 0,
            "release_state": "HARD_HOLD_NO_PUBLICATION"}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = review_pinned_native(args.source_dir, datetime.now(timezone.utc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "records"},
                     ensure_ascii=False, sort_keys=True))
