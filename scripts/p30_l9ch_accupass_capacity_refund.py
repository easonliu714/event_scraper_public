"""ACCUPASS #02 public organizer terms: capacity is NOT live inventory.
The refund window is relative to a ticket start not independently exposed here.
Official source https://www.accupass.com/event/2609041147021848655729
"""
import datetime
from urllib.parse import urlsplit

SOURCE = "https://www.accupass.com/event/2609041147021848655729"
EVENT_ID = "2609041147021848655729"

def exact_source(value):
    if not isinstance(value, str):
        return False
    x = urlsplit(value)
    return (x.scheme, x.netloc, x.path, x.query, x.fragment) == ("https", "www.accupass.com", "/event/" + EVENT_ID, "", "")

def inspect(record, observed_at):
    result = {"gate": "P30-L9-CH", "acceptedFields": 0, "goldenAccepted": 0,
              "published": False, "provenance": []}
    try:
        datetime.date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(result, decision="HOLD_OBSERVED_AT")
    if not isinstance(record, dict) or not exact_source(record.get("url")) or record.get("event_id") != EVENT_ID:
        return dict(result, decision="HOLD_SAME_EVENT_ID")
    if record.get("ticket_session_ids") is not None or record.get("inventory") is not None or record.get("remaining_seats") is not None:
        return dict(result, decision="HOLD_NO_PUBLIC_SESSION_OR_INVENTORY")
    if record.get("capacity_role") != "PER_WORKSHOP_LIMIT" or type(record.get("capacity")) is not int or record["capacity"] != 20:
        return dict(result, decision="HOLD_CAPACITY_NOT_LIVE_INVENTORY")
    if record.get("fee_role") != "PER_WORKSHOP_FEE" or type(record.get("fee_ntd")) is not int or record["fee_ntd"] != 100:
        return dict(result, decision="HOLD_WORKSHOP_FEE_ROLE")
    if record.get("refund_role") != "RELATIVE_TO_PURCHASE_AND_TICKET_START":
        return dict(result, decision="HOLD_REFUND_ROLE")
    if record.get("refund_after_purchase_hours") != 24 or record.get("refund_before_ticket_start_days") != 8 or record.get("refund_fee_percent") != 10:
        return dict(result, decision="HOLD_REFUND_CONDITION")
    if record.get("absolute_refund_deadline") is not None:
        return dict(result, decision="HOLD_NO_VERIFIED_TICKET_START_FOR_DEADLINE")
    if record.get("walkin_role") != "NO_SHOW_WAITLIST_ONLY" or record.get("walkin_guaranteed") is not False:
        return dict(result, decision="HOLD_WAITLIST_NOT_AVAILABILITY")
    for role, value in (
        ("PER_WORKSHOP_LIMIT_NOT_INVENTORY", 20),
        ("PER_WORKSHOP_FEE_NOT_SESSION_PRICE", 100),
        ("RELATIVE_REFUND_AFTER_PURCHASE_HOURS", 24),
        ("RELATIVE_REFUND_BEFORE_TICKET_START_DAYS", 8),
        ("REFUND_FEE_PERCENT", 10),
        ("NO_SHOW_WAITLIST_NOT_TICKET_AVAILABILITY", True),
    ):
        result["provenance"].append({"source": "ACCUPASS_CANONICAL_02", "source_url": SOURCE,
                                     "observed_at": observed_at, "role": role, "value": value,
                                     "decision": "REVIEW_NOT_FORMALLY_ACCEPTED"})
    return dict(result, decision="HOLD_RELATIVE_TERMS_NO_TICKET_SESSION_ID")
