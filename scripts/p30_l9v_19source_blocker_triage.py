#!/usr/bin/env python3
"""P30-L9-V: SHA-pinned 19-source HTTP/list blocker triage and ONE BeClass public GET.

Diagnostic only. Does not fetch other 18 sources, follow redirects, bypass access
controls, parse global dates, store source HTML/URLs, or publish event data.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

KIND = "EVENTRADAR_P30_L9V_19SOURCE_BLOCKER_MATRIX_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
STATUS_BLOB = "e19ca37c4c80c10b7278d0813b8ff1047535d124"
STATUS_MAIN = "fbf4ca02b91159f2423caf3d79fb0ca4bb747069"
L7B_REPORT_SHA256 = "e07c01a5d36ab0c950c45fb26e5fdd270103b4013bbf62a00c48291fee5f595a"
L7B_ARTIFACT_SHA256 = "8ad3a6c8d0b3259ef9187830a33455365a8ff4c7bc30061653345d74cef758c6"
L7B_RUN = 40353636708
L7B_ARTIFACT = 12665097220
BECLASS_URL = "https://www.beclass.com/default.php?name=ShowList&op=recent"
UA = "EventRadar-P30-L9V/1.0 (single bounded public-source diagnostic)"
BUCKETS = (
    "HTTP403_ACCESS_HOLD",
    "HTTP200_ZERO_GENERIC_LIST",
    "HTTP200_ZERO_WITH_INDEPENDENT_SOURCE",
    "LIST_POSITIVE_DETAIL_IDENTITY_HOLD",
    "LIST_POSITIVE_FIELD_ROLE_HOLD",
)

def sha256(raw):
    return hashlib.sha256(raw).hexdigest()

def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def read_json(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), raw

def validate(status, status_bytes, diag, diag_bytes, manifest):
    if git_blob(status_bytes) != STATUS_BLOB:
        raise ValueError("HOLD_L9V_PUBLIC_STATUS_BLOB")
    if sha256(diag_bytes) != L7B_REPORT_SHA256:
        raise ValueError("HOLD_L9V_L7B_REPORT_SHA")
    if manifest.get("filesSHA256", {}).get("platform_diagnostics.json") != L7B_REPORT_SHA256:
        raise ValueError("HOLD_L9V_L7B_MANIFEST")
    if manifest.get("sourceMainSHA") != "fc4f963247d68eed29425808cc14e7250f312d05":
        raise ValueError("HOLD_L9V_L7B_SOURCE_PIN")
    if status.get("kind") != "EVENTRADAR_PUBLIC_PLATFORM_ENGINEERING_STATUS_V1":
        raise ValueError("HOLD_L9V_STATUS_KIND")
    if diag.get("kind") != "EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1":
        raise ValueError("HOLD_L9V_L7B_KIND")
    if status.get("production", {}).get("eventFeedReleaseState") != RELEASE:
        raise ValueError("HOLD_L9V_RELEASE")
    if status["production"].get("goldenAccepted") != 0 or status["production"].get("eventDataModifiedByThisReport"):
        raise ValueError("HOLD_L9V_PRODUCTION")
    if diag.get("published") or diag.get("goldenAccepted") or diag.get("writerExecuted"):
        raise ValueError("HOLD_L9V_SOURCE_PRODUCTION")
    if not diag.get("all19PlatformsAttempted") or diag.get("fullPlatformCoverageVerified"):
        raise ValueError("HOLD_L9V_COVERAGE_CLAIM")
    rows = status.get("platforms", [])
    source_rows = diag.get("platforms", [])
    if len(rows) != 19 or len(source_rows) != 19:
        raise ValueError("HOLD_L9V_PLATFORM_COUNT")
    if len({r.get("platform") for r in rows}) != 19:
        raise ValueError("HOLD_L9V_PLATFORM_DUPLICATE")
    for a, b in zip(rows, source_rows):
        if a["platform"] != b.get("platform"):
            raise ValueError("HOLD_L9V_PLATFORM_ORDER")
        base = a["baseline"]
        http = b.get("http") or {}
        if base["httpStatus"] != http.get("httpStatus"):
            raise ValueError("HOLD_L9V_HTTP_PARITY_" + a["id"])
        if base["listCandidates"] != b.get("listCandidateCount"):
            raise ValueError("HOLD_L9V_LIST_PARITY_" + a["id"])
        if base["detailAttempted"] != b.get("detailAttempted"):
            raise ValueError("HOLD_L9V_DETAIL_PARITY_" + a["id"])
        if base["detailTitleMatches"] != b.get("detailIdentityVerified"):
            raise ValueError("HOLD_L9V_TITLE_PARITY_" + a["id"])
    sums = status["baselineSummary"]
    if (sums["platformsChecked"], sums["http200Platforms"],
        sums["blocked403Platforms"], sums["positiveListPlatforms"],
        sums["listCandidates"], sums["detailAttempts"],
        sums["detailTitleMatches"]) != (19, 16, 3, 12, 264, 12, 5):
        raise ValueError("HOLD_L9V_BASELINE_COUNTS")
    if (diag["counts"]["httpOK"], diag["counts"]["listPositive"],
        diag["counts"]["listCandidates"], diag["counts"]["detailAttempts"],
        diag["counts"]["detailIdentityVerified"]) != (16, 12, 264, 12, 5):
        raise ValueError("HOLD_L9V_DIAG_COUNTS")
    return rows, source_rows

def classify(row, original):
    b = row["baseline"]
    code, count, matched = b["httpStatus"], b["listCandidates"], b["detailTitleMatches"]
    trail = (original.get("http") or {}).get("redirectTrail") or []
    redirect_codes = sorted({x.get("httpStatus") for x in trail
                             if x.get("httpStatus") in (301, 302, 303, 307, 308)})
    independent = row.get("independentGate")
    if code == 403:
        bucket = BUCKETS[0]
        next_action = "SINGLE_PUBLIC_ACCESS_OR_REDIRECT_DIAGNOSTIC_ONLY"
    elif code == 200 and count == 0:
        bucket = BUCKETS[2] if independent else BUCKETS[1]
        next_action = ("COMPARE_INDEPENDENT_LIST_ADAPTER" if independent
                       else "INSPECT_PUBLIC_HTML_VS_JS_LIST_STRUCTURE")
    elif code == 200 and count > 0 and matched == 0:
        bucket = BUCKETS[3]
        next_action = "EXACT_EVENT_ID_AND_DETAIL_TITLE_PARITY"
    elif code == 200 and count > 0 and matched > 0:
        bucket = BUCKETS[4]
        next_action = "SOURCE_BOUND_FIELD_ROLE_REVIEW"
    else:
        raise ValueError("HOLD_L9V_UNEXPECTED_HTTP_LIST_TIER")
    return {
        "id": row["id"], "platform": row["platform"],
        "baselineHTTP": code, "baselineListCandidates": count,
        "baselineDetailAttempts": b["detailAttempted"],
        "baselineDetailTitleMatches": matched,
        "originalRedirectCodes": redirect_codes,
        "bucket": bucket, "nextAction": next_action,
        "independentGateExists": independent is not None,
        "sourceCauseProven": False,
        "freshSourceReverified": False,
        "formallyAcceptedFields": 0,
    }

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

def redirect_class(location):
    if not location:
        return "MISSING_LOCATION"
    try:
        target = urlsplit(urljoin(BECLASS_URL, location))
        if target.scheme != "https":
            return "NON_HTTPS_HOLD"
        if target.username or target.password or target.port not in (None, 443):
            return "UNSAFE_TARGET_HOLD"
        host = (target.hostname or "").lower().rstrip(".")
        if host == "beclass.com" or host.endswith(".beclass.com"):
            return "SAME_SITE_HTTPS_NOT_FOLLOWED"
        return "OFFSITE_NOT_FOLLOWED"
    except ValueError:
        return "INVALID_TARGET_HOLD"

def probe_beclass(opener=None):
    """Exactly one public GET; no redirect follow, no retries, no response-body read."""
    opener = opener if opener is not None else build_opener(NoRedirect())
    request = Request(BECLASS_URL, headers={
        "User-Agent": UA, "Accept": "text/html",
    }, method="GET")
    result = {"platform": "BeClass", "requested": 1, "followedRedirects": 0,
              "responseHTTP": None, "state": "HOLD_NETWORK_ERROR",
              "redirectClass": "NONE", "observedAtUTC": utc_now(),
              "rawBodySaved": False, "rawUrlSaved": False}
    try:
        with opener.open(request, timeout=9) as response:
            result["responseHTTP"] = response.status
            result["state"] = ("HTTP200_REACHABLE_LIST_UNVERIFIED"
                               if response.status == 200 else "HOLD_HTTP_OTHER")
            if response.status in (301, 302, 303, 307, 308):
                result["state"] = "HOLD_REDIRECT_NOT_FOLLOWED"
                result["redirectClass"] = redirect_class(response.headers.get("Location"))
    except HTTPError as error:
        result["responseHTTP"] = error.code
        if error.code in (301, 302, 303, 307, 308):
            result["state"] = "HOLD_REDIRECT_NOT_FOLLOWED"
            result["redirectClass"] = redirect_class(error.headers.get("Location"))
        elif error.code == 403:
            result["state"] = "HOLD_HTTP403"
        elif error.code == 429:
            result["state"] = "HOLD_HTTP429_NO_RETRY"
        else:
            result["state"] = "HOLD_HTTP_OTHER"
        error.close()
    except (URLError, TimeoutError, OSError):
        result["state"] = "HOLD_NETWORK_ERROR"
    return result

def build_report(rows, original, probe):
    matrix = [classify(a, b) for a, b in zip(rows, original)]
    counts = {bucket: sum(x["bucket"] == bucket for x in matrix) for bucket in BUCKETS}
    if sum(counts.values()) != 19 or counts[BUCKETS[0]] != 3:
        raise ValueError("HOLD_L9V_MATRIX_SUM")
    if {x["platform"] for x in matrix if x["bucket"] == BUCKETS[0]} != {"KKTIX", "拓元售票", "BeClass"}:
        raise ValueError("HOLD_L9V_BLOCKED_IDENTITY")
    if probe["requested"] != 1 or probe["followedRedirects"] != 0:
        raise ValueError("HOLD_L9V_PROBE_SCOPE")
    return {
        "kind": KIND, "sourceStatusMain": STATUS_MAIN, "sourceStatusBlob": STATUS_BLOB,
        "sourceL7BRun": L7B_RUN, "sourceL7BArtifact": L7B_ARTIFACT,
        "sourceL7BArtifactSHA256": L7B_ARTIFACT_SHA256,
        "sourceL7BReportSHA256": L7B_REPORT_SHA256,
        "baselineAtUTC": "2026-10-26T15:53:41Z",
        "historicalEvidenceNotCurrent": True,
        "matrix": matrix, "counts": counts, "beclassOneShot": probe,
        "freshSourcesProbed": 1, "otherSourcesReprobed": 0,
        "formalFieldPromotions": 0, "goldenAccepted": 0,
        "published": False, "writerExecuted": False,
        "schedulerExecuted": False, "notifierExecuted": False,
        "mergeExecuted": False, "productionModified": False,
        "releaseState": RELEASE,
    }

def emit(report, out):
    path = Path(out).resolve()
    root = Path.cwd().resolve()
    if not path.is_relative_to(root) or path == root or path.parts[len(root.parts)] in (
        ".git", ".github", "docs", "scripts", "tests", "schemas"
    ):
        raise ValueError("HOLD_L9V_ISOLATED_OUTPUT_ONLY")
    path.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
    (path / "blocker_matrix.json").write_bytes(data)
    manifest = {"kind": "EVENTRADAR_P30_L9V_SHA_MANIFEST_V1",
                "sourceStatusBlob": STATUS_BLOB,
                "sourceL7BReportSHA256": L7B_REPORT_SHA256,
                "filesSHA256": {"blocker_matrix.json": sha256(data)},
                "releaseState": RELEASE, "published": False}
    (path / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", required=True)
    parser.add_argument("--l7b", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", default="p30-l9v-evidence")
    parser.add_argument("--live-beclass", action="store_true")
    args = parser.parse_args()
    status, status_raw = read_json(args.status)
    diag, diag_raw = read_json(args.l7b)
    manifest, _ = read_json(args.manifest)
    rows, original = validate(status, status_raw, diag, diag_raw, manifest)
    if not args.live_beclass:
        raise ValueError("HOLD_L9V_ONE_SHOT_NOT_REQUESTED")
    report = build_report(rows, original, probe_beclass())
    emit(report, args.out)
    print("PASS_L9V_SHA_PINNED_19_SOURCE_MATRIX",
          json.dumps(report["counts"], ensure_ascii=False, sort_keys=True))
    print("L9V_BECLASS_ONE_SHOT", json.dumps(report["beclassOneShot"], sort_keys=True))
    print("HOLD_L9V_NO_FIELD_PROMOTION_NO_PUBLICATION")

if __name__ == "__main__":
    main()
