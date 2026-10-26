#!/usr/bin/env python3
"""P30-L7-C: independent POSTPONED schedule roles for a single bound TWTC event.

Exactly one GET to TWTC detail and one GET to the official event organizer's
public announcement; strict origin/path and redirect guards, no retries.
Original and tentative dates MUST NOT be published as confirmed event dates.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

KIND = "EVENTRADAR_P30_L7C_POSTPONEMENT_CANDIDATE_NOT_GOLDEN"
PARENT_KIND = "EVENTRADAR_P30_ANDROID_SMOKE_CANDIDATE_NOT_GOLDEN"
TWTC_URL = "https://twtc.com.tw/exhibition_more.aspx?id=28255&p=home"
ANNOUNCEMENT_URL = "https://www.fintechtaipei.tw/Announcement/19"
MAX_BODY = 800_000
UA = "EventRadar-P30-readonly/1.0 (github.com/easonliu714/event_scraper_public)"
DATE_RE = re.compile(r"展出日期\s*[:：]\s*(20\d{2}/\d{1,2}/\d{1,2})\s*[~～-]\s*(20\d{2}/\d{1,2}/\d{1,2})")


def allowed(url):
    try:
        u = urlsplit(url)
        if (u.scheme != "https" or u.username or u.password
                or u.port not in (None, 443)
                or "\\" in u.path or ".." in u.path.split("/")):
            return False
        if u.hostname == "twtc.com.tw" and u.path == "/exhibition_more.aspx":
            return parse_qs(u.query).get("id", []) == ["28255"]
        if u.hostname == "www.fintechtaipei.tw" and u.path == "/Announcement/19":
            return not u.query
        return False
    except ValueError:
        return False


def get_html(session, url, timeout=12):
    """Bound redirects to the two exact public pages; never change content source."""
    original_host = urlsplit(url).hostname
    trail = []
    for _ in range(3):
        if not allowed(url) or urlsplit(url).hostname != original_host:
            return None, {"state": "UNAPPROVED_URL_OR_REDIRECT", "trail": trail}
        try:
            with session.get(url, allow_redirects=False, stream=True,
                             timeout=(6, timeout), headers={"User-Agent": UA}) as resp:
                code = resp.status_code
                trail.append({"url": url, "http_status": code})
                if code in (301, 302, 303, 307, 308):
                    loc = resp.headers.get("location")
                    if not loc:
                        return None, {"state": "REDIRECT_NO_LOCATION", "trail": trail}
                    url = urljoin(url, loc)
                    continue
                meta = {"state": "HTTP_OK" if code == 200 else "HTTP_ERROR",
                        "http_status": code, "observed_url": url, "trail": trail,
                        "content_type": resp.headers.get("content-type", "")[:100]}
                if code != 200:
                    return None, meta
                if "text/html" not in meta["content_type"].lower():
                    meta["state"] = "NON_HTML"
                    return None, meta
                raw = bytearray()
                for part in resp.iter_content(chunk_size=32768):
                    raw.extend(part)
                    if len(raw) > MAX_BODY:
                        meta["state"] = "OVERSIZE"
                        return None, meta
                if not raw:
                    meta["state"] = "EMPTY_BODY"
                    return None, meta
                meta["sha256"] = hashlib.sha256(raw).hexdigest()
                return bytes(raw), meta
        except requests.RequestException as exc:
            return None, {"state": "NETWORK_ERROR", "error_type": type(exc).__name__,
                          "trail": trail}
    return None, {"state": "REDIRECT_LIMIT", "trail": trail}


def date_range(year, mon1, day1, mon2, day2):
    start = date(year, mon1, day1)
    end = date(year + (1 if (mon2, day2) < (mon1, day1) else 0), mon2, day2)
    return start.isoformat(), end.isoformat()


def parse_original(detail):
    soup = BeautifulSoup(detail, "html.parser")
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
    if not any("2026" in h and "台北金融科技展" in h and "延期" in h for h in headings):
        raise ValueError("HOLD_TWTC_TITLE_OR_STATUS_MISMATCH")
    raw = " ".join(soup.stripped_strings)
    matches = DATE_RE.findall(raw)
    if len(matches) != 1:
        raise ValueError("HOLD_ORIGINAL_DATE_SHAPE")
    try:
        a, b = (date.fromisoformat(text.replace("/", "-")) for text in matches[0])
    except ValueError:
        raise ValueError("HOLD_INVALID_ORIGINAL_DATE")
    if a > b or a.year != 2026 or b.year != 2026:
        raise ValueError("HOLD_ORIGINAL_DATE_RANGE")
    return a.isoformat(), b.isoformat()


def parse_tentative(announcement):
    soup = BeautifulSoup(announcement, "html.parser")
    body = " ".join(soup.stripped_strings)
    compact = re.sub(r"\s+", "", body).replace("－", "-").replace("–", "-")
    if "FinTechTaipei2026" not in compact.replace(" ", "") and "台北金融科技展" not in compact:
        raise ValueError("HOLD_ANNOUNCEMENT_EVENT_IDENTITY")
    if "預定延期至12/18-12/19" not in compact:
        raise ValueError("HOLD_TENTATIVE_DATE_NOT_CONFIRMED_FROM_SOURCE")
    if "確切調整時間將於10月底前公告" not in compact:
        raise ValueError("HOLD_NOT_EXPLICITLY_TENTATIVE")
    return date_range(2026, 12, 18, 12, 19)


def select_postponed(payload):
    if not isinstance(payload, dict) or payload.get("kind") != PARENT_KIND:
        raise ValueError("HOLD_PARENT_CONTRACT")
    if payload.get("count") != 44 or len(payload.get("items", [])) != 44:
        raise ValueError("HOLD_PARENT_44")
    for field, accepted in (("published", False), ("goldenAccepted", False),
                            ("writerExecuted", False), ("notificationExecuted", False),
                            ("autoHidden", 0), ("sourceRuntime", "DORMANT")):
        if payload.get(field) != accepted:
            raise ValueError("HOLD_PARENT_FLAG_" + field)
    hits = [e for e in payload["items"]
            if e.get("platform") == "台北世貿"
            and e.get("rawPeriod") == "延期未定"
            and "台北金融科技展" in e.get("title", "")]
    if len(hits) != 1:
        raise ValueError("HOLD_POSTPONED_IDENTITY_COUNT")
    target = hits[0]
    if (target.get("officialUrl") != TWTC_URL
            or target.get("dateEvidenceStatus") != "LIST_DETAIL_PERIOD_CONFLICT"
            or target.get("dateStart") is not None or target.get("dateEnd") is not None):
        raise ValueError("HOLD_WRONG_DETAIL_BINDING")
    if payload.get("dateVerifiedCount") != 38 or payload.get("dateUnverifiedCount") != 1:
        raise ValueError("HOLD_PARENT_DATE_METRICS")
    return target


def build(payload, detail_html, announcement_html, detail_meta, announce_meta):
    target = select_postponed(payload)
    original = parse_original(detail_html)
    tentative = parse_tentative(announcement_html)
    if (detail_meta.get("state") != "HTTP_OK" or detail_meta.get("observed_url") != TWTC_URL
            or announce_meta.get("state") != "HTTP_OK"
            or announce_meta.get("observed_url") != ANNOUNCEMENT_URL
            or len(detail_meta.get("sha256", "")) != 64
            or len(announce_meta.get("sha256", "")) != 64):
        raise ValueError("HOLD_MISSING_LIVE_HTTP_EVIDENCE")
    result = json.loads(json.dumps(payload, ensure_ascii=False))
    record = next(x for x in result["items"] if x["id"] == target["id"])
    # Old dates remain unavailable: never conflate original/tentative with actual.
    record.update({
        "scheduleStatus": "POSTPONED_TENTATIVE_UNCONFIRMED",
        "originalDateStart": original[0], "originalDateEnd": original[1],
        "tentativeDateStart": tentative[0], "tentativeDateEnd": tentative[1],
        "confirmedDateStart": None, "confirmedDateEnd": None,
        "dateStart": None, "dateEnd": None,
        "dateEvidenceStatus": "ORIGINAL_AND_TENTATIVE_ROLES_SEPARATED",
        "detailAnnouncementUrl": ANNOUNCEMENT_URL,
        "originalDateSourceUrl": TWTC_URL,
        "originalDateHTMLSHA256": detail_meta["sha256"],
        "tentativeDateHTMLSHA256": announce_meta["sha256"],
        "scheduleLastObservedAtUTC": datetime.now(timezone.utc).isoformat(),
    })
    result["postponementRoleCaseCount"] = 1
    result["postponementEvidenceKind"] = KIND
    result["dateVerifiedCount"] = 38
    result["dateUnverifiedCount"] = 1
    result["published"] = False
    return result, {
        "kind": KIND, "eventId": target["id"],
        "twtcDetailUrl": TWTC_URL, "organizerAnnouncementUrl": ANNOUNCEMENT_URL,
        "original": original, "tentative": tentative, "confirmed": None,
        "twtcHttp": detail_meta, "organizerHttp": announce_meta,
        "noticeStatus": "TENTATIVE_DATE_SUBJECT_TO_OFFICIAL_CONFIRMATION",
        "published": False, "goldenAccepted": False, "autoHidden": 0,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    dest = Path(args.out_dir).resolve()
    if dest == Path("docs").resolve() or Path("docs").resolve() in dest.parents:
        parser.error("HOLD_FORBIDDEN_PAGES_OUTPUT")
    original = json.loads(Path(args.parent).read_text(encoding="utf-8"))
    select_postponed(original)
    with requests.Session() as session:
        detail_html, detail_meta = get_html(session, TWTC_URL)
        time.sleep(1.5)
        notice_html, notice_meta = get_html(session, ANNOUNCEMENT_URL)
    if detail_html is None or notice_html is None:
        print("HOLD P30_L7C_OFFICIAL_HTTP_NOT_PROVEN", detail_meta["state"], notice_meta["state"])
        raise SystemExit(2)
    data, evidence = build(original, detail_html, notice_html, detail_meta, notice_meta)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    (dest / "schedule_roles.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print("PASS P30_L7C_TWO_LIVE_OFFICIAL_SOURCES_ORIGINAL_VS_TENTATIVE")
    print("ORIGINAL", *evidence["original"], "TENTATIVE", *evidence["tentative"], "CONFIRMED_NONE")
    print("PASS P30_L7C_44_IDS_38_VERIFIED_1_POSTPONED_NO_PUBLISH")


if __name__ == "__main__":
    main()
