#!/usr/bin/env python3
"""P30-L9-AI: fail-closed bounded sibling label/value topology (offline, no publication).

Only identifies explicit role-label relationships in small local containers.
Does not accept dates, identities or formal event fields and makes no HTTP calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup

KIND = "EVENTRADAR_P30_L9AI_BOUNDED_SIBLING_TOPOLOGY_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "1a64ae6e258367c89856d5cd2b3cf558cc14ac00"
MAX_HTML_BYTES = 1_500_000
MAX_ROOTS = 8
MAX_CONTAINERS = 400
MAX_PAIRS = 80
MAX_VALUE_CHARS = 240
ROLE_LABELS = {
    "EVENT": {"活動日期", "演出日期", "活動時間", "演出時間"},
    "SALE": {"售票時間", "開賣時間", "售票期間"},
    "ADMISSION": {"入場時間", "開放入場時間"},
    "REGISTRATION": {"報名時間", "報名期間", "登記時間"},
    "VOUCHER": {"兌換時間", "兌換期間"},
    "VENUE": {"活動地點", "演出地點", "活動場地"},
    "PRICE": {"票價", "票券價格"},
    "SESSION": {"場次", "演出場次"},
}
LABEL_TO_ROLE = {label: role for role, labels in ROLE_LABELS.items() for label in labels}
BLOCKED_TAGS = ("a", "button", "input", "select", "textarea", "script", "style")


def compact(text: str) -> str:
    return "".join(text.strip().strip("：:").split())


def hidden(node) -> bool:
    return (
        node.has_attr("hidden")
        or str(node.get("aria-hidden", "")).lower() == "true"
        or "display:none" in str(node.get("style", "")).lower().replace(" ", "")
    )


def inspect_local_siblings(html: str) -> dict:
    if not isinstance(html, str) or len(html.encode("utf-8")) > MAX_HTML_BYTES:
        return {"assessed": False, "hold": "HOLD_HTML_CAP_OR_TYPE", "roles": {}}
    soup = BeautifulSoup(html, "html.parser")
    roots = soup.select("main, article, [role='main'], #event-detail")
    if not roots:
        return {"assessed": False, "hold": "HOLD_NO_SEMANTIC_ROOT", "roles": {}}
    if len(roots) > MAX_ROOTS:
        return {"assessed": False, "hold": "HOLD_ROOT_CAP", "roles": {}}
    containers = []
    seen = set()
    for root in roots:
        for container in root.select("div, li, section, p"):
            key = id(container)
            if key not in seen:
                seen.add(key)
                containers.append(container)
            if len(containers) > MAX_CONTAINERS:
                return {"assessed": False, "hold": "HOLD_CONTAINER_CAP", "roles": {}}
    values = {role: set() for role in ROLE_LABELS}
    counts = {role: 0 for role in ROLE_LABELS}
    blocked = 0
    for container in containers:
        if hidden(container):
            continue
        children = container.find_all(recursive=False)
        if len(children) != 2 or any(hidden(child) for child in children):
            continue
        label_node, value_node = children
        if label_node.find(BLOCKED_TAGS) or value_node.find(BLOCKED_TAGS):
            blocked += 1
            continue
        role = LABEL_TO_ROLE.get(compact(label_node.get_text(" ", strip=True)))
        if role is None:
            continue
        value = " ".join(value_node.get_text(" ", strip=True).split())
        if not value or len(value) > MAX_VALUE_CHARS:
            blocked += 1
            continue
        if compact(value) in LABEL_TO_ROLE:
            blocked += 1
            continue
        counts[role] += 1
        if sum(counts.values()) > MAX_PAIRS:
            return {"assessed": False, "hold": "HOLD_PAIR_CAP", "roles": {}}
        values[role].add(value)
    roles = {}
    for role in ROLE_LABELS:
        distinct = len(values[role])
        decision = (
            "HOLD_NO_EXPLICIT_LOCAL_SIBLING" if counts[role] == 0
            else "HOLD_CONFLICTING_LOCAL_VALUES" if distinct > 1
            else "REVIEW_ONE_LOCAL_SIBLING_NOT_ACCEPTED"
        )
        roles[role] = {
            "localPairCount": counts[role],
            "distinctValueCount": distinct,
            "decision": decision,
            "accepted": False,
        }
    return {
        "assessed": True, "hold": None, "semanticRootCount": len(roots),
        "containerCount": len(containers), "blockedPairs": blocked,
        "roles": roles, "acceptedFields": 0, "rawValuesPersisted": False,
    }


def offline_contract_report() -> dict:
    """No live source inference; report only the synthetic contract's scope."""
    return {
        "kind": KIND, "parentHead": PARENT, "releaseState": RELEASE,
        "sourceStatus": "NOT_PROBED_THIS_GATE",
        "diagnosticScope": "LOCAL_TWO_DIRECT_CHILDREN_IN_SEMANTIC_ROOT",
        "roleNames": sorted(ROLE_LABELS), "roleCount": len(ROLE_LABELS),
        "maxRoots": MAX_ROOTS, "maxContainers": MAX_CONTAINERS,
        "maxPairs": MAX_PAIRS, "acceptedFields": 0, "goldenAccepted": 0,
        "published": False, "productionModified": False,
        "httpRequests": 0, "rawHtmlPersisted": False,
        "rawUrlsPersisted": False, "rawTitlesPersisted": False,
        "rawEventIdsPersisted": False, "rawFieldValuesPersisted": False,
        "decision": "REVIEW_OFFLINE_TOPOLOGY_CONTRACT_ONLY",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-contract", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.offline_contract:
        parser.error("explicit --offline-contract required; no live mode")
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-l9ai-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    out.mkdir(exist_ok=True)
    report = (json.dumps(offline_contract_report(), sort_keys=True, indent=2) + "\n").encode()
    (out / "local_sibling_contract.json").write_bytes(report)
    (out / "manifest.json").write_text(json.dumps({
        "kind": KIND, "releaseState": RELEASE,
        "filesSHA256": {"local_sibling_contract.json": hashlib.sha256(report).hexdigest()},
    }, sort_keys=True, indent=2) + "\n")
    print("PASS_L9AI_OFFLINE_ONLY_NO_PUBLICATION")


if __name__ == "__main__":
    main()
