"""Single-use TPAC /event/2072 native LIST->DETAIL receipt, NO PUBLISH.

Robots policy must explicitly permit both paths. One bounded GET per path,
no redirects/retries/checkout. Raw HTML is never saved; dates stay HOLD.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from urllib.parse import urlsplit
from scripts import p30_tpac_event_source as tpac

USER_AGENT = "EventRadarPublicResearch"
ROBOTS_URL = "https://tpac.org.taipei/robots.txt"
MAX_HTML = 4 * 1024 * 1024
MAX_ROBOTS = 256 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_public(url, mime, cap):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "tpac.org.taipei"
            or parsed.port is not None or parsed.username or parsed.password
            or parsed.fragment):
        raise ValueError("TPAC_NATIVE_ORIGIN_HOLD")
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": mime,
                      "Cache-Control": "no-cache"})
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=12) as resp:
        status, final = resp.status, resp.geturl()
        content_type = resp.headers.get_content_type()
        body = resp.read(cap + 1)
    if final != url or status != 200:
        raise ValueError("TPAC_NATIVE_HTTP_OR_REDIRECT_HOLD")
    if content_type != mime or not 0 < len(body) <= cap:
        raise ValueError("TPAC_NATIVE_MIME_OR_BODY_CAP_HOLD")
    return body, {"url": url, "http_status": status,
                  "content_type": content_type, "body_bytes": len(body),
                  "body_sha256": hashlib.sha256(body).hexdigest(),
                  "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                  "transport": "NATIVE_NO_REDIRECT_NO_RETRY"}


def explicit_robots_allow(body):
    try:
        value = body.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("TPAC_ROBOTS_UTF8_HOLD") from exc
    groups = re.findall(r"(?im)^\s*user-agent\s*:\s*([^#\r\n]+)", value)
    if not any(g.strip().lower() in ("*", USER_AGENT.lower()) for g in groups):
        raise ValueError("TPAC_ROBOTS_APPLICABLE_GROUP_MISSING_HOLD")
    policy = urllib.robotparser.RobotFileParser()
    policy.parse(value.splitlines())
    if not all(policy.can_fetch(USER_AGENT, url) for url in
               (tpac.LIST_URL, tpac.DETAIL_URL)):
        raise ValueError("TPAC_ROBOTS_EVENT_PATH_DENIED_HOLD")


def run_native_once():
    out = {"kind": "P30_TPAC_EVENT2072_NATIVE_ONESHOT_V1",
           "source_id": tpac.SOURCE_ID, "source_event_id": tpac.EVENT_ID,
           "list_url": tpac.LIST_URL, "detail_url": tpac.DETAIL_URL,
           "decision": "HOLD", "first_failure": "TPAC_ROBOTS_NOT_CHECKED_HOLD",
           "robots_get_attempted": 0, "native_event_get_attempted": 0,
           "native_list": 0, "native_detail": 0, "native_same_id_review": 0,
           "native_role_review": 0, "date_conflict": False,
           "formal_accepted_fields": 0, "native_body_lkg": 0,
           "receipt_only_lkg": 0, "golden": 0, "published": 0,
           "raw_html_saved": False, "release_state": "HARD_HOLD_NO_PUBLICATION",
           "receipts": []}
    try:
        out["robots_get_attempted"] = 1
        robots, receipt = read_public(ROBOTS_URL, "text/plain", MAX_ROBOTS)
        out["receipts"].append(receipt)
        explicit_robots_allow(robots)
        out["native_event_get_attempted"] = 1
        listing, receipt = read_public(tpac.LIST_URL, "text/html", MAX_HTML)
        out["receipts"].append(receipt)
        out["native_list"] = 1
        parser = tpac.EventScopes()
        parser.feed(listing.decode("utf-8"))
        if tpac._unique_owner(parser, "list") is None:
            raise ValueError("TPAC_NATIVE_LIST_EXACT_EVENT_LOCAL_EDGE_HOLD")
        out["native_event_get_attempted"] = 2
        detail, receipt = read_public(tpac.DETAIL_URL, "text/html", MAX_HTML)
        out["receipts"].append(receipt)
        out["native_detail"] = 1
        verdict = tpac.inspect_caller_html(
            listing.decode("utf-8"), detail.decode("utf-8"))
        if verdict["same_id_review"] != 1:
            raise ValueError(verdict["first_failure"])
        out["native_same_id_review"] = 1
        out["native_role_review"] = len(verdict["field_roles"])
        out["date_conflict"] = verdict["date_conflict"]
        out["decision"] = "NATIVE_IDENTITY_REVIEW_WITH_FIELD_HOLD"
        out["first_failure"] = verdict["first_failure"]
    except Exception as exc:
        out["first_failure"] = type(exc).__name__ + ":" + str(exc)[:180]
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="TPAC native one-shot; NO PUBLISH")
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args(argv)
    out = run_native_once()
    with open(args.evidence, "w", encoding="utf-8") as stream:
        json.dump(out, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(out, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
