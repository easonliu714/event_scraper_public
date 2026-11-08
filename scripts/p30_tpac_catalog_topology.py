"""TPAC dual-list official catalog topology and fail-closed identity discovery.

Two official first-party LIST namespaces exist:
  /program -> /program/{id}  PERFORMANCE; showtimes are DETAIL-only.
  /event   -> /event/{id}    ACTIVITY; lectures, tours, workshops, exhibitions.
Their numeric IDs are *not* interchangeable and neither listing range is
evidence for an EVENT_SHOW_START. No GET, formal Publisher or data mutation.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit

from scripts.p30_tpac_multi_event_refresh import (
    _body, _receipt, _text, _visible,
)

BASE = "https://tpac.org.taipei"
CATALOGS = {
    "program": {"list_url": BASE + "/program", "path": "/program/",
                "identity_prefix": "tpac:program:",
                "role": "PERFORMANCE_LIST_PERIOD_NOT_SHOW_START"},
    "event": {"list_url": BASE + "/event", "path": "/event/",
              "identity_prefix": "tpac:event:",
              "role": "ACTIVITY_LIST_PERIOD_NOT_SHOW_START"},
}
ID = re.compile(r"^[1-9][0-9]{0,9}$")
MAX_LINKS = 300
MAX_TITLE = 180


def _title(anchor, kind):
    """Require event-owned title evidence, never take whole card or date blob."""
    raw = anchor.get("title") or anchor.get("data-title")
    labels = [
        node for selector in (
            ".card-" + kind + "__text-title",
            ".card-program__text-title",
            ".card-event__text-title",
            ".card__text-title",
            "[data-event-title]",
        ) for node in anchor.select(selector) if _visible(node)
    ]
    names = [_text(n) for n in labels if _text(n)]
    if not isinstance(raw, str) or not 3 <= len(raw.strip()) <= MAX_TITLE:
        raise ValueError("TPAC_CATALOG_TITLE_ATTRIBUTE_HOLD")
    title = " ".join(raw.split())
    if names and any(n != title for n in names):
        raise ValueError("TPAC_CATALOG_TITLE_CONFLICT_HOLD")
    # A title attribute alone is an inventory-level candidate, not accepted
    # event identity. Exact matching official DETAIL H1 is required later.
    return title, bool(names)


def discover_catalog(kind, body, receipt, now):
    """Bounded same-host exact LIST links; evidence is not DETAIL acceptance."""
    if kind not in CATALOGS:
        raise ValueError("TPAC_CATALOG_KIND_HOLD")
    catalog = CATALOGS[kind]
    source = catalog["list_url"]
    _receipt(body, receipt, source, now)
    soup = _body(body)
    anchors = soup.select("a[href]")
    if not 1 <= len(anchors) <= MAX_LINKS:
        raise ValueError("TPAC_CATALOG_LINK_CAP_HOLD")
    records = {}
    for anchor in anchors:
        if not _visible(anchor):
            continue
        href = anchor.get("href", "")
        if not isinstance(href, str) or not href:
            continue
        target = urlsplit(urljoin(source, href))
        if (target.scheme != "https" or target.netloc != "tpac.org.taipei"
                or target.query or target.fragment):
            continue
        prefix = catalog["path"]
        if not target.path.startswith(prefix):
            continue
        number = target.path[len(prefix):]
        if not ID.fullmatch(number):
            continue
        if number in records:
            raise ValueError("TPAC_CATALOG_DUPLICATE_ID_HOLD")
        title, title_owned = _title(anchor, kind)
        date_nodes = [
            n for sel in (".card-" + kind + "__text-date",
                          ".card-program__text-date",
                          ".card-event__text-date")
            for n in anchor.select(sel) if _visible(n)
        ]
        period = _text(date_nodes[0]) if len(date_nodes) == 1 else ""
        records[number] = {
            "source": "TPAC",
            "kind": kind,
            "source_event_id": number,
            "identity": catalog["identity_prefix"] + number,
            "detail_url": target.geturl(),
            "list_url": source,
            "title_candidate": title,
            "list_title_owned": title_owned,
            "list_date_label": period,
            "list_date_role": catalog["role"],
            "decision": "REVIEW_DETAIL_ID_AND_FIELDS_REQUIRED",
            "accepted_show_start": None,
            "accepted_exhibition_hours": None,
            "accepted_sale_start": None,
        }
    if not records:
        raise ValueError("TPAC_CATALOG_NO_VALID_EVENT_LINK_HOLD")
    return records


def safe_union(programs, events):
    """Combine separate catalog identities without guessing equivalence."""
    if not isinstance(programs, dict) or not isinstance(events, dict):
        raise ValueError("TPAC_CATALOG_UNION_SCHEMA_HOLD")
    out = {}
    for kind, source in (("program", programs), ("event", events)):
        expected = CATALOGS[kind]["identity_prefix"]
        for number, entry in source.items():
            if (not isinstance(entry, dict) or entry.get("kind") != kind
                    or entry.get("source_event_id") != number
                    or entry.get("identity") != expected + number):
                raise ValueError("TPAC_CATALOG_UNION_IDENTITY_HOLD")
            key = entry["identity"]
            if key in out:
                raise ValueError("TPAC_CATALOG_UNION_DUPLICATE_HOLD")
            out[key] = entry
    return out
