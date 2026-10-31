#!/usr/bin/env python3
"""P30-L9-BW: iNDIEVOX same-ID game rows; dynamic status is not inventory PASS."""
import hashlib
import re
from urllib.parse import urlsplit

EVENT_ID = "26_iv04280c7"
DETAIL = "https://www.indievox.com/activity/detail/" + EVENT_ID
GAME = "https://www.indievox.com/activity/game/" + EVENT_ID
TITLE = "〖美秀集團《等無》巡迴 2026〗"
EXPECTED = (
    ("2026-12-05", "20:00", "LIVE WAREHOUSE", "高雄一"),
    ("2026-12-06", "20:00", "LIVE WAREHOUSE", "高雄二"),
    ("2026-12-12", "20:00", "Legacy Taichung", "台中一"),
    ("2026-12-13", "20:00", "Legacy Taichung", "台中二"),
    ("2026-12-19", "20:00", "Legacy TERA", "台北一"),
    ("2026-12-20", "20:00", "Legacy TERA", "台北二"),
)
HOLD = "HARD_HOLD_NO_PUBLICATION"

def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def inspect(detail, game, observed_at):
    out = dict(gate="P30-L9-BW", source="iNDIEVOX#18", officialGETinCI=0,
               acceptedFields=0, goldenAccepted=0, published=False,
               releaseState=HOLD, candidateProvenance=[],
               inventoryVerified=False, perSessionPriceVerified=False)
    if not isinstance(detail, dict) or not isinstance(game, dict):
        return dict(out, decision="HOLD_UNSTRUCTURED")
    if detail.get("url") != DETAIL or game.get("url") != GAME:
        return dict(out, decision="HOLD_SAME_EVENT_ID_URL")
    if detail.get("title") != TITLE or game.get("title") != TITLE:
        return dict(out, decision="HOLD_TITLE_PARITY")
    if not isinstance(observed_at, str) or not re.fullmatch(r"20\d\d-\d\d-\d\d", observed_at):
        return dict(out, decision="HOLD_OBSERVATION_DATE")
    rows = game.get("rows")
    if not isinstance(rows, list) or len(rows) != 6:
        return dict(out, decision="HOLD_GAME_ROW_COUNT")
    if detail.get("sessions") != list(EXPECTED):
        return dict(out, decision="HOLD_DETAIL_SESSION_PARITY")
    statuses = []
    for i, (row, expected) in enumerate(zip(rows, EXPECTED)):
        if not isinstance(row, dict) or row.get("session") != expected:
            return dict(out, decision="HOLD_GAME_ROW_IDENTITY")
        if row.get("status") not in ("NO_TICKETS_AVAILABLE_TEXT", "NO_EXPLICIT_STATUS"):
            return dict(out, decision="HOLD_DYNAMIC_STATUS_UNRECOGNIZED")
        statuses.append(row["status"])
    if game.get("per_session_price") is not None or game.get("live_inventory_confirmed") is not False:
        return dict(out, decision="HOLD_PRICE_OR_LIVE_INVENTORY_ASSERTION")
    for i, (row, status) in enumerate(zip(EXPECTED, statuses)):
        out["candidateProvenance"].append(dict(source="iNDIEVOX#18", source_url=GAME,
            observed_at=observed_at, role="EVENT_SESSION_ROW", row=i + 1,
            valueSHA256=sha("|".join(row)), decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
        if status == "NO_TICKETS_AVAILABLE_TEXT":
            out["candidateProvenance"].append(dict(source="iNDIEVOX#18", source_url=GAME,
                observed_at=observed_at, role="DYNAMIC_UI_STATUS_TEXT_NOT_INVENTORY",
                row=i + 1, valueSHA256=sha(status),
                decision="REVIEW_SNAPSHOT_ONLY_NOT_TICKET_AVAILABILITY"))
    out["statusTextRows"] = statuses.count("NO_TICKETS_AVAILABLE_TEXT")
    return dict(out, decision="HOLD_DYNAMIC_STATUS_AND_PER_SESSION_PRICE_NOT_VERIFIED")

if __name__ == "__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_NETWORK")
