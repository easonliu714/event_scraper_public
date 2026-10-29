#!/usr/bin/env python3
"""P30-L9-AP: diagnose ACCUPASS zero-detail cause without an extra source request."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from unittest.mock import patch
import p30_l9ao_accupass_role_ancestor as prior

KIND = "EVENTRADAR_P30_L9AP_LIST_CAUSE_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"

def classify(decision):
    if decision == "REVIEW_SOURCE_BOUND_CANDIDATES":
        return "REVIEW_LIST_CANDIDATES"
    if decision == "HOLD_LIST_HTTP_OR_URL":
        return "HOLD_HTTP_OR_FINAL_URL"
    if decision == "HOLD_LIST_STABILITY_OR_SCOPE":
        return "HOLD_STATIC_DOM_PARITY_OR_SCOPE"
    if decision == "HOLD_LIST_TimeoutError":
        return "HOLD_NAVIGATION_TIMEOUT"
    if isinstance(decision, str) and re.fullmatch(r"HOLD_LIST_[A-Za-z]{1,48}Error", decision):
        return "HOLD_NAVIGATION_EXCEPTION_CLASS"
    return "HOLD_UNCLASSIFIED_LIST_CAUSE"

def probe():
    captured = {}
    original = prior.prior.ah.probe
    def intercept():
        source = original()
        captured["listDecision"] = source.get("listDecision")
        captured["listHttp"] = source.get("listHttp")
        return source
    with patch.object(prior.prior.ah, "probe", intercept):
        result = prior.probe()
    decision = captured.get("listDecision")
    result.update(kind=KIND, releaseState=RELEASE,
                  listCause=classify(decision),
                  listHttp=captured.get("listHttp") if captured.get("listHttp") in (200, None) else None,
                  listAttemptMax=1, detailAttemptMax=2,
                  acceptedFields=0, goldenAccepted=0, published=False,
                  rawHtmlPersisted=False, rawUrlsPersisted=False,
                  rawTitlesPersisted=False, rawEventIdsPersisted=False,
                  rawFieldValuesPersisted=False)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--status", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.live:
        parser.error("explicit --live required")
    prior.prior.ah.prior.prior.validate_status(Path(args.status).read_bytes())
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-l9ap-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result = probe()
    out.mkdir(exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "list_cause.json").write_bytes(raw)
    (out / "manifest.json").write_text(json.dumps({
        "kind": KIND, "releaseState": RELEASE,
        "filesSHA256": {"list_cause.json": hashlib.sha256(raw).hexdigest()}
    }, sort_keys=True, indent=2) + "\n")
    print("L9AP_LIST_CAUSE=" + result["listCause"])
    print("L9AP_DETAILS=" + str(result["detailCount"]))
    print("HOLD_NO_FIELDS_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
