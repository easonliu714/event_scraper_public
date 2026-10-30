#!/usr/bin/env python3
"""P30-VENUE-02X: all same-film showings must match detail dates; NO PUBLISH."""
import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from p30_venue02u_fuzhong15_sessions import HOME, HOLD, get_one, norm, safe_detail
from p30_venue02v_fuzhong15_row_parity import index_rows, year_hint, detail_screening_dates
from p30_venue02w_fuzhong15_multishow import showing_groups

WEEKDAYS = "一二三四五六日"

def inspect_all_showings(index_html, detail_html):
    evidence, selected, error = showing_groups(index_html)
    result = dict(evidence, exactTitleMatches=0, screeningDateLabelCount=0,
                  detailLocalDateCandidateCount=0, matchedShowingCount=0,
                  missingShowingCount=0, extraDetailDateCount=0,
                  invalidWeekdayCount=0, acceptedFields=0,
                  venueScreeningId=None, ticketEventId=None)
    if error:
        return dict(result, decision=error)
    hint = year_hint(index_html)
    if hint is None:
        return dict(result, decision="HOLD_INDEX_YEAR_MONTH_AMBIGUOUS")
    year, month = int(hint[0]), int(hint[1])
    group = [row for row in index_rows(index_html)
             if row["url"] == selected["url"] and row["month"] == month]
    if len(group) < 2:
        return dict(result, decision="HOLD_NO_MULTISHOWING_GROUP")
    if len(group) > 12:
        return dict(result, decision="HOLD_SHOWING_GROUP_CAP")
    expected = []
    for row in group:
        try:
            stamp = datetime.strptime(
                f"{year}/{row['month']:02d}/{row['day']:02d} {row['time']}",
                "%Y/%m/%d %H:%M")
            expected.append(stamp.strftime("%Y/%m/%d %H:%M"))
        except ValueError:
            return dict(result, decision="HOLD_INVALID_INDEX_CALENDAR_DATE")
    # The displayed weekday is a source-local claim, not an inferred session ID.
    raw_weekdays = []
    for tr in BeautifulSoup(index_html, "html.parser").find_all("tr", limit=800):
        cells = tr.find_all("td", recursive=False)
        if len(cells) != 5:
            continue
        anchors = cells[2].find_all("a", href=True)
        if len(anchors) != 1 or safe_detail(anchors[0]["href"]) != selected["url"]:
            continue
        match = re.fullmatch(r"(\d{1,2})/(\d{1,2})\(([一二三四五六日天])\)",
                             norm(cells[0].get_text(" ", strip=True)))
        if match and int(match.group(1)) == month:
            raw_weekdays.append((int(match.group(1)), int(match.group(2)),
                                 norm(cells[1].get_text(" ", strip=True)), match.group(3)))
    if len(raw_weekdays) != len(group):
        return dict(result, decision="HOLD_WEEKDAY_SCOPE_AMBIGUOUS")
    invalid = 0
    for m, day, clock, weekday in raw_weekdays:
        try:
            actual = WEEKDAYS[datetime.strptime(
                f"{year}/{m:02d}/{day:02d} {clock}", "%Y/%m/%d %H:%M").weekday()]
            invalid += (actual != ("日" if weekday == "天" else weekday))
        except ValueError:
            return dict(result, decision="HOLD_INVALID_INDEX_CALENDAR_DATE")
    result["invalidWeekdayCount"] = invalid
    if invalid:
        return dict(result, decision="HOLD_WEEKDAY_DATE_MISMATCH")
    titles = {row["title"] for row in group}
    if len(titles) != 1:
        return dict(result, decision="HOLD_SAME_FILM_TITLE_CONFLICT")
    soup = BeautifulSoup(detail_html, "html.parser")
    headings = [norm(h.get_text(" ", strip=True))
                for h in soup.find_all(["h1", "h2", "h3", "h4"], limit=100)]
    result["exactTitleMatches"] = headings.count(selected["title"])
    dates, labels = detail_screening_dates(detail_html)
    result["screeningDateLabelCount"] = labels
    result["detailLocalDateCandidateCount"] = len(dates)
    left, right = Counter(expected), Counter(dates)
    result["matchedShowingCount"] = sum((left & right).values())
    result["missingShowingCount"] = sum((left - right).values())
    result["extraDetailDateCount"] = sum((right - left).values())
    if result["exactTitleMatches"] != 1 or labels != 1 or len(dates) > 12:
        result["decision"] = "HOLD_DETAIL_TITLE_LABEL_OR_CAP"
    elif len(expected) != len(set(expected)) or len(dates) != len(set(dates)):
        result["decision"] = "HOLD_DUPLICATE_INDEX_OR_DETAIL_DATETIME"
    elif result["missingShowingCount"] or result["extraDetailDateCount"]:
        result["decision"] = "HOLD_INCOMPLETE_ALL_SHOWING_PARITY"
    else:
        result["decision"] = "REVIEW_ALL_SHOWINGS_EXACT_PARITY_NO_SESSION_ID"
    return result

def live():
    audit={"gate":"P30-VENUE-02X","source":"FUZHONG15_P0_NEW_TAIPEI",
           "observed_at":datetime.now(timezone.utc).isoformat(),
           "requestBudget":2,"requestCount":1,"acceptedFields":0,
           "goldenAccepted":0,"published":False,"releaseState":HOLD}
    receipt,index=get_one(HOME)
    audit["indexReceipt"]=receipt
    if index is None:
        return dict(audit,decision="HOLD_INDEX_HTTP_OR_BODY")
    groups,selected,error=showing_groups(index)
    audit.update(groups)
    if error:
        return dict(audit,decision=error)
    audit["selectedDetailURLSHA256"]=hashlib.sha256(selected["url"].encode()).hexdigest()
    audit["requestCount"]=2
    receipt,detail=get_one(selected["url"])
    audit["detailReceipt"]=receipt
    if detail is None:
        return dict(audit,decision="HOLD_DETAIL_HTTP_OR_BODY")
    audit.update(inspect_all_showings(index,detail))
    return audit

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
