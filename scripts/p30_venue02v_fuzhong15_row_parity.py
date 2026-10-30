#!/usr/bin/env python3
"""P30-VENUE-02V: Fuzhong15 row-local screening vs film-detail dates; NO PUBLISH."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from p30_venue02u_fuzhong15_sessions import HOME, HOLD, norm, safe_detail, get_one

DATE = re.compile(r"^(\d{1,2})/(\d{1,2})\(([一二三四五六日天])\)$")
TIME = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
FULL = re.compile(r"(?<!\d)(20\d{2})/(\d{2})/(\d{2})\s+([01]\d|2[0-3]):([0-5]\d)(?!\d)")

def year_hint(html):
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    values = set(re.findall(r"(20\d{2})年(\d{1,2})月放映場次表", text))
    return values.pop() if len(values) == 1 else None

def index_rows(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr", limit=800):
        cells = tr.find_all("td", recursive=False)
        if len(cells) != 5:
            continue
        date = DATE.fullmatch(norm(cells[0].get_text(" ", strip=True)))
        time = TIME.fullmatch(norm(cells[1].get_text(" ", strip=True)))
        anchors = cells[2].find_all("a", href=True)
        if not date or not time or len(anchors) != 1:
            continue
        url = safe_detail(anchors[0]["href"])
        title = norm(anchors[0].get_text(" ", strip=True))
        if not url or not 2 <= len(title) <= 160:
            continue
        month, day = int(date.group(1)), int(date.group(2))
        if not 1 <= month <= 12 or not 1 <= day <= 31:
            continue
        rows.append({"url": url, "title": title, "month": month, "day": day,
                     "time": time.group(0), "admissionMarker": norm(cells[2].get_text(" ", strip=True)).replace(title, "").strip()})
    return rows

def detail_screening_dates(html):
    soup = BeautifulSoup(html, "html.parser")
    labels = [node for node in soup.find_all(string=True, limit=8000)
              if norm(node).rstrip("：:") == "放映日期"]
    if len(labels) != 1:
        return [], len(labels)
    parent = labels[0].parent
    scopes = [parent]
    if parent.parent is not None:
        scopes.append(parent.parent)
    for scope in scopes:
        local = norm(scope.get_text(" ", strip=True))
        if len(local) > 550:
            continue
        tokens = [f"{y}/{m}/{d} {h}:{mi}" for y, m, d, h, mi in FULL.findall(local)]
        if tokens:
            return tokens, len(labels)
    return [], len(labels)

def inspect_pair(index_html, detail_html, selected):
    hint = year_hint(index_html)
    headings = [norm(h.get_text(" ", strip=True)) for h in BeautifulSoup(detail_html, "html.parser").find_all(["h1", "h2", "h3", "h4"], limit=100)]
    exact = sum(h == selected["title"] for h in headings)
    dates, labels = detail_screening_dates(detail_html)
    result = {"exactTitleMatches": exact, "screeningDateLabelCount": labels,
              "detailLocalDateCandidateCount": len(dates), "matchingRowDateTimeCount": 0,
              "acceptedFields": 0, "venueScreeningId": None, "ticketEventId": None}
    if hint is None or int(hint[1]) != selected["month"]:
        result["decision"] = "HOLD_INDEX_YEAR_MONTH_SCOPE_AMBIGUOUS"
        return result
    target = f"{hint[0]}/{selected['month']:02}/{selected['day']:02} {selected['time']}"
    matches = dates.count(target)
    result["matchingRowDateTimeCount"] = matches
    if exact != 1 or labels != 1 or matches != 1 or len(dates) > 12:
        result["decision"] = "HOLD_TITLE_OR_ROW_DETAIL_DATETIME_PARITY"
    elif len(dates) > 1:
        result["decision"] = "REVIEW_FILM_MULTI_SCREENING_DATES_NO_FIELDS"
    else:
        result["decision"] = "REVIEW_EXACT_ROW_DETAIL_SCREENING_NO_FIELDS"
    return result

def live():
    audit = {"gate": "P30-VENUE-02V", "source": "FUZHONG15_P0_NEW_TAIPEI",
             "observed_at": datetime.now(timezone.utc).isoformat(), "requestBudget": 2,
             "requestCount": 1, "acceptedFields": 0, "goldenAccepted": 0,
             "published": False, "releaseState": HOLD, "venueScreeningId": None, "ticketEventId": None}
    receipt, index = get_one(HOME)
    audit["indexReceipt"] = receipt
    if index is None:
        return dict(audit, decision="HOLD_INDEX_HTTP_OR_BODY")
    rows = index_rows(index)
    audit["rowLocalScreeningCandidates"] = len(rows)
    hint = year_hint(index)
    audit["uniqueIndexYearMonthScope"] = hint is not None
    if not rows or hint is None:
        return dict(audit, decision="HOLD_INDEX_ROW_OR_YEAR_SCOPE")
    eligible = [r for r in rows if r["month"] == int(hint[1])]
    if not eligible:
        return dict(audit, decision="HOLD_NO_SAME_MONTH_ROW")
    selected = eligible[-1]
    audit["sameFilmIndexRowCount"] = sum(r["url"] == selected["url"] for r in eligible)
    audit["rowAdmissionMarkerRoleOnly"] = selected["admissionMarker"] in {"售", "報", "索", ""}
    audit["selectedDetailURLSHA256"] = hashlib.sha256(selected["url"].encode()).hexdigest()
    audit["selectedRowIdentitySHA256"] = hashlib.sha256((selected["url"] + "|" + selected["title"] + "|" +
                                                           str(selected["month"]) + "/" + str(selected["day"]) + "|" +
                                                           selected["time"]).encode()).hexdigest()
    audit["requestCount"] = 2
    receipt, detail = get_one(selected["url"])
    audit["detailReceipt"] = receipt
    if detail is None:
        return dict(audit, decision="HOLD_DETAIL_HTTP_OR_BODY")
    audit.update(inspect_pair(index, detail, selected))
    return audit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-one", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(live(), handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
