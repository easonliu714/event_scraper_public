#!/usr/bin/env python3
"""P30-L9-BX: canonical #10 Event Go same-ID role ownership; no publication."""
import datetime
import hashlib
import re

INDEX = "https://eventgo.bnextmedia.com.tw/"
ID = "217fef2dc4986456b0a0da9b113f8dec"
DETAIL = "https://eventgo.bnextmedia.com.tw/event/detail/" + ID
TITLE = "〖免費報名！11/04(三)新竹場〗AI決策領導力實戰工作坊"
DATE = "2026-11-04"
VENUE = "外貿協會新竹辦事處 602會議室"
HOLD = "HARD_HOLD_NO_PUBLICATION"

def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def inspect(index, detail, observed_at):
    out = dict(gate="P30-L9-BX", source="Event Go#10",
               officialGETinCI=0, candidateProvenance=[], acceptedFields=0,
               goldenAccepted=0, published=False, releaseState=HOLD,
               verifiedInventory=False, verifiedRegistrationOpen=False)
    if not isinstance(index, dict) or not isinstance(detail, dict):
        return dict(out, decision="HOLD_UNSTRUCTURED")
    if index.get("url") != INDEX or detail.get("url") != DETAIL or index.get("detail_url") != DETAIL:
        return dict(out, decision="HOLD_SAME_ID_FIRST_PARTY_LINK")
    if index.get("title") != TITLE or detail.get("title") != TITLE:
        return dict(out, decision="HOLD_TITLE_PARITY")
    try:
        datetime.date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVED_AT")
    if detail.get("event_date") != DATE or index.get("event_date") != DATE:
        return dict(out, decision="HOLD_EVENT_DATE_PARITY")
    if detail.get("event_start") != "09:00" or detail.get("event_end") != "12:00":
        return dict(out, decision="HOLD_EVENT_TIME")
    if detail.get("venue") != VENUE or index.get("venue") != VENUE:
        return dict(out, decision="HOLD_VENUE_PARITY")
    if detail.get("ticket_class") != "FREE_REGISTRATION_NT0":
        return dict(out, decision="HOLD_PRICE_CLASS")
    if detail.get("sale_banner") != "ENDED" or detail.get("ticket_badge") != "HOT":
        return dict(out, decision="HOLD_STATUS_SOURCE_PARITY")
    if detail.get("inventory") is not None or detail.get("registration_open") is not None:
        return dict(out, decision="HOLD_DYNAMIC_INVENTORY_OR_OPEN_CLAIM")
    for role, value in (("EVENT_DATE", DATE), ("EVENT_TIME", "09:00-12:00"),
                        ("VENUE", VENUE), ("PRICE_CLASS", "FREE_REGISTRATION_NT0"),
                        ("SALE_BANNER", "ENDED"), ("TICKET_BADGE", "HOT")):
        out["candidateProvenance"].append(dict(source="Event Go#10",
            source_url=DETAIL, observed_at=observed_at, role=role,
            valueSHA256=sha(value), decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out, decision="HOLD_CONFLICTING_SALE_BANNER_AND_TICKET_BADGE")

if __name__ == "__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_NETWORK")
