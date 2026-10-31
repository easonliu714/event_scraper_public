"""P30-L9-BZ: distinct Xinzhuang row #1 → OPENTIX #05 de-listed title boundary; source REVIEW only."""
import datetime
import hashlib
import re

BULLETIN = "https://www.xzcac.ntpc.gov.tw/xmdoc/cont?sid=0Q252550255605202263&xsmsid=0G286655201682579075"
TICKET = "https://www.opentix.life/event/2071939794940801025"
VENUE_TITLE = "2026新莊有好戲-《隋唐風雲—江山換美人》/一心戲劇團"
TICKET_TITLE = "2026新莊有好戲 ~ 一心戲劇團《隋唐風雲—江山換美人》"
DATE = "2026-10-03"
TIME = "19:30"

def inspect(row, ticket, observed_at):
    out = dict(gate="P30-L9-BZ", source="OPENTIX#05", acceptedFields=0,
               goldenAccepted=0, published=False, candidateProvenance=[],
               ticketSessionVerified=False, availabilityVerified=False)
    try:
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", observed_at or ""):
            raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVED_AT")
    if row.get("bulletin_url") != BULLETIN or row.get("row_number") != 1:
        return dict(out, decision="HOLD_ROW_LOCAL_SOURCE")
    if row.get("ticket_url") != TICKET or ticket.get("url") != TICKET:
        return dict(out, decision="HOLD_DIRECT_EVENT_URL")
    if row.get("title") != VENUE_TITLE or ticket.get("title") != TICKET_TITLE:
        return dict(out, decision="HOLD_SOURCE_TITLE_CHANGED")
    if row.get("event_date") != DATE or row.get("event_time") != TIME:
        return dict(out, decision="HOLD_VENUE_DATE_ROLE")
    if ticket.get("status_text") != "本節目已下架":
        return dict(out, decision="HOLD_TICKET_STATUS_NOT_OBSERVED")
    if ticket.get("session_date") is not None or ticket.get("inventory") is not None:
        return dict(out, decision="HOLD_UNVERIFIED_SESSION_OR_INVENTORY")
    if ticket.get("title") != row.get("title"):
        decision = "HOLD_DIRECT_LINK_BUT_NONEXACT_TITLE_AND_DELISTED"
    else:
        decision = "HOLD_TITLE_PARITY_REQUIRES_INDEPENDENT_SESSION"
    for source, url, role, value in (
        ("XINZHUANG_VENUE", BULLETIN, "ROW1_VENUE_TITLE", VENUE_TITLE),
        ("XINZHUANG_VENUE", BULLETIN, "ROW1_EVENT_DATE", DATE),
        ("XINZHUANG_VENUE", BULLETIN, "ROW1_EVENT_TIME", TIME),
        ("XINZHUANG_VENUE", BULLETIN, "ROW1_DIRECT_TICKET_URL", TICKET),
        ("OPENTIX#05", TICKET, "TICKET_EVENT_TITLE", TICKET_TITLE),
        ("OPENTIX#05", TICKET, "TICKET_DELISTED_NOT_SOLD_OUT", "本節目已下架"),
    ):
        out["candidateProvenance"].append(dict(source=source, source_url=url,
            observed_at=observed_at, role=role,
            valueSHA256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out, decision=decision)
