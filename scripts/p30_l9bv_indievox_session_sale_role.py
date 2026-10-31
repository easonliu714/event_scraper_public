#!/usr/bin/env python3
"""P30-L9-BV: iNDIEVOX #18 first-party LIST -> same activity ID DETAIL -> GAME.

Source-observed 2026-10-31. Distinguish six performance sessions from
advance-sale windows and general price classes; no live ticket inventory,
per-session price, formal FIELD or publication is inferred.
"""
import hashlib
import re
from urllib.parse import urlsplit

SOURCE = "iNDIEVOX#18"
EVENT_ID = "26_iv04280c7"
HOME = "https://www.indievox.com/"
TITLE = "【美秀集團《等無》巡迴 2026】"
HOLD = "HARD_HOLD_NO_PUBLICATION"
SESSIONS = (
    ("2026-12-05", "20:00", "LIVE WAREHOUSE", "高雄一"),
    ("2026-12-06", "20:00", "LIVE WAREHOUSE", "高雄二"),
    ("2026-12-12", "20:00", "Legacy Taichung", "台中一"),
    ("2026-12-13", "20:00", "Legacy Taichung", "台中二"),
    ("2026-12-19", "20:00", "Legacy TERA", "台北一"),
    ("2026-12-20", "20:00", "Legacy TERA", "台北二"),
)
PRICES = ("預售票1500元", "現場票1800元", "身心票750元")
SALE = ("2026/10/29 12:00", "2026/10/30 12:00")

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def first_party(url, kind):
    if not isinstance(url, str):
        return False
    try:
        p = urlsplit(url)
    except ValueError:
        return False
    return (p.scheme == "https" and p.netloc == "www.indievox.com"
            and not p.username and not p.password and not p.query
            and not p.fragment and p.path == "/activity/" + kind + "/" + EVENT_ID)

def inspect(index, detail, game):
    out = dict(gate="P30-L9-BV", canonicalPlatform=SOURCE, officialGETinCI=0,
               candidateProvenance=[], acceptedFields=0, goldenAccepted=0,
               published=False, releaseState=HOLD, ticketInventoryVerified=False)
    if not all(isinstance(x, dict) for x in (index, detail, game)):
        return dict(out, decision="HOLD_UNSTRUCTURED_EVIDENCE")
    if (index.get("url") != HOME or not first_party(index.get("detail_url"), "detail")
            or not first_party(detail.get("url"), "detail")
            or not first_party(game.get("url"), "game")
            or index["detail_url"] != detail["url"]):
        return dict(out, decision="HOLD_FIRST_PARTY_SAME_ID_EDGE")
    if (index.get("title") != TITLE or detail.get("title") != TITLE
            or game.get("title") != TITLE):
        return dict(out, decision="HOLD_LIST_DETAIL_GAME_TITLE_PARITY")
    if (detail.get("sessions") != list(SESSIONS)
            or game.get("sessions") != list(SESSIONS)):
        return dict(out, decision="HOLD_SIX_ROW_SESSION_IDENTITY")
    if detail.get("prices") != list(PRICES) or detail.get("sale_windows") != list(SALE):
        return dict(out, decision="HOLD_PRICE_OR_SALE_ROLE_SOURCE_PARITY")
    if game.get("per_session_price_verified") is not False:
        return dict(out, decision="HOLD_PER_SESSION_PRICE_MAPPING_UNKNOWN")
    if game.get("inventory_verified") is not False:
        return dict(out, decision="HOLD_LIVE_INVENTORY_UNKNOWN")
    stamp = index.get("observed_at")
    if not isinstance(stamp, str) or not re.fullmatch(r"20\d\d-\d\d-\d\d", stamp):
        return dict(out, decision="HOLD_PROVENANCE_DATE")
    values = [("EVENT_TITLE", TITLE, detail["url"])]
    values += [("EVENT_SESSION_" + str(i+1), "|".join(row), game["url"])
               for i, row in enumerate(SESSIONS)]
    values += [("EVENT_PRICE_CLASS_UNMAPPED", price, detail["url"]) for price in PRICES]
    values += [("SALE_START_NOT_EVENT_TIME", sale, detail["url"]) for sale in SALE]
    for role, value, url in values:
        out["candidateProvenance"].append(dict(source=SOURCE, source_url=url,
            observed_at=stamp, role=role, valueSHA256=sha(value),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    out["sameIdDetailAndGame"] = True
    out["distinctSessionCandidates"] = len(SESSIONS)
    return dict(out, decision="HOLD_PER_SESSION_PRICE_AND_INDEPENDENT_ACCEPTANCE")

if __name__ == "__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_NETWORK")
