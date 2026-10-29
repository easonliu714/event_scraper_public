#!/usr/bin/env python3
"""P30-L9-AJ: apply frozen L9-AI sibling topology to at most two source-matched ACCUPASS details.

Read-only REVIEW/HOLD. The existing L9-AH browser/identity Gate is reused unchanged;
no event fields, raw page content, query values or identifiers are persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import p30_l9ah_accupass_field_roles as ah
import p30_l9ai_accupass_sibling_roles as ai

KIND = "EVENTRADAR_P30_L9AJ_LIVE_SIBLING_ROLE_REVIEW_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "ed7e3d15a2fb76161ec95bad460d0003f46c8b19"
MAX_DETAILS = 2


def summarize(source: dict) -> dict:
    """Whitelist aggregate-only evidence and refuse every non-reviewed identity."""
    details = source.get("details", [])
    if not isinstance(details, list) or len(details) > MAX_DETAILS:
        return {"decision": "HOLD_DETAIL_SCOPE", "detailCount": 0, "details": []}
    output = []
    for item in details:
        topology = item.get("fieldTopology") or {}
        roles = topology.get("roles") or {}
        if not isinstance(roles, dict):
            roles = {}
        safe_roles = {}
        for role in sorted(ai.ROLE_LABELS):
            r = roles.get(role) or {}
            count = r.get("localPairCount", 0)
            distinct = r.get("distinctValueCount", 0)
            decision = r.get("decision", "HOLD_NO_EXPLICIT_LOCAL_SIBLING")
            if type(count) is not int or type(distinct) is not int or count < 0 or distinct < 0 or distinct > count:
                count, distinct, decision = 0, 0, "HOLD_INVALID_ROLE_METRIC"
            if decision not in ("HOLD_NO_EXPLICIT_LOCAL_SIBLING",
                                "HOLD_CONFLICTING_LOCAL_VALUES",
                                "REVIEW_ONE_LOCAL_SIBLING_NOT_ACCEPTED",
                                "HOLD_INVALID_ROLE_METRIC"):
                count, distinct, decision = 0, 0, "HOLD_INVALID_ROLE_METRIC"
            safe_roles[role] = {"localPairCount": count, "distinctValueCount": distinct,
                                "decision": decision, "accepted": False}
        identity = item.get("identityDecision", "")
        if not isinstance(identity, str) or not (
            identity.startswith("REVIEW_") or identity.startswith("HOLD_")
        ):
            identity = "HOLD_UNRECOGNIZED_IDENTITY_DECISION"
        output.append({
            "http": item.get("http") if item.get("http") in (200, None) else None,
            "identityDecision": identity,
            "topologyAssessed": topology.get("assessed") is True,
            "topologyHold": topology.get("hold") if topology.get("hold") in (
                None, "HOLD_HTML_CAP_OR_TYPE", "HOLD_NO_SEMANTIC_ROOT",
                "HOLD_ROOT_CAP", "HOLD_CONTAINER_CAP", "HOLD_PAIR_CAP") else "HOLD_UNKNOWN_TOPOLOGY",
            "roles": safe_roles,
        })
    identity_ok = (len(output) == MAX_DETAILS and
                   all(d["identityDecision"].startswith("REVIEW_") for d in output))
    assessed = identity_ok and all(d["topologyAssessed"] for d in output)
    observed = sum(v["localPairCount"] for d in output for v in d["roles"].values())
    decision = ("HOLD_DETAIL_IDENTITY_OR_COUNT" if not identity_ok else
                "HOLD_LOCAL_TOPOLOGY_UNASSESSED" if not assessed else
                "HOLD_NO_LOCAL_SIBLING_EVIDENCE" if observed == 0 else
                "REVIEW_LOCAL_SIBLING_ROLE_EVIDENCE_NOT_ACCEPTED")
    return {"decision": decision, "detailCount": len(output),
            "listHttp": source.get("listHttp") if source.get("listHttp") in (200, None) else None,
            "listDecision": source.get("listDecision") if source.get("listDecision") in (
                "REVIEW_SOURCE_BOUND_CANDIDATES", "HOLD_LIST_STABILITY_OR_SCOPE",
                "HOLD_LIST_HTTP_OR_URL") else "HOLD_UNCLASSIFIED_LIST",
            "observedLocalPairs": observed, "details": output}


def probe() -> dict:
    # Reuse the previously reviewed one-list/two-detail navigation and exact
    # same-event-path title gate; only replace its local topology inspector.
    with patch.object(ah, "scoped_pairs", ai.inspect_local_siblings):
        source = ah.probe()
    return summarize(source)


def offline_contract() -> dict:
    return {"kind": KIND, "parentHead": PARENT, "releaseState": RELEASE,
            "maxDetails": MAX_DETAILS, "roleNames": sorted(ai.ROLE_LABELS),
            "httpRequests": 0, "acceptedFields": 0, "goldenAccepted": 0,
            "published": False, "productionModified": False,
            "rawHtmlPersisted": False, "rawUrlsPersisted": False,
            "rawTitlesPersisted": False, "rawEventIdsPersisted": False,
            "rawFieldValuesPersisted": False, "queryValuesPersisted": False}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    p.add_argument("--status", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    if not args.live:
        p.error("explicit --live required")
    ah.prior.prior.validate_status(Path(args.status).read_bytes())
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-l9aj-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result = offline_contract()
    result.update(probe())
    result["httpRequests"] = "ONE_LIST_MAX_TWO_DETAILS"
    out.mkdir(exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "accupass_sibling_roles.json").write_bytes(raw)
    manifest = {"kind": KIND, "releaseState": RELEASE,
                "filesSHA256": {"accupass_sibling_roles.json": hashlib.sha256(raw).hexdigest()}}
    (out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print("L9AJ_DECISION=" + result["decision"])
    print("L9AJ_DETAILS=" + str(result["detailCount"]))
    print("HOLD_NO_FORMAL_FIELDS_GOLDEN_PUBLICATION")


if __name__ == "__main__":
    main()
