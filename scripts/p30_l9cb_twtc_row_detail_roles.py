"""P30-L9-CB: official TWTC #16 same-list/detail event roles; admission stays unknown."""
import datetime
import hashlib
import re

LIST = "https://twtc.com.tw/exhibition?p=home"
DETAIL = "https://twtc.com.tw/exhibition_more.aspx?id=29251&p=home"
TITLE = "2026台北Meng萌寵物用品展/2026台北國際玩轉文具禮品暨手作創意展"
VENUE = "世貿一館"
ORGANIZER = "生動國際展覽事業股份有限公司"

def inspect(index_row, detail, observed_at):
    """Only record exact source-bound candidate roles; never publish or infer tickets."""
    out = dict(gate="P30-L9-CB", source="TWTC#16", candidateProvenance=[],
               acceptedFields=0, goldenAccepted=0, published=False,
               ticketEventIdVerified=False, admissionVerified=False)
    try:
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", observed_at or ""):
            raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVED_AT")
    if index_row.get("url") != LIST or index_row.get("detail_url") != DETAIL:
        return dict(out, decision="HOLD_INDEX_DETAIL_LINK")
    if detail.get("url") != DETAIL or detail.get("detail_id") != "29251":
        return dict(out, decision="HOLD_DETAIL_ID_URL")
    if index_row.get("title") != TITLE or detail.get("title") != TITLE:
        return dict(out, decision="HOLD_SAME_ID_EXACT_TITLE")
    if index_row.get("start") != "2026-11-06" or index_row.get("end") != "2026-11-09":
        return dict(out, decision="HOLD_LIST_DATE_RANGE")
    if detail.get("start") != "2026-11-06" or detail.get("end") != "2026-11-09":
        return dict(out, decision="HOLD_DETAIL_DATE_RANGE")
    if index_row.get("venue") != VENUE or detail.get("venue") != VENUE:
        return dict(out, decision="HOLD_VENUE_IDENTITY")
    if detail.get("hours") != "10:00 ~ 18:00" or detail.get("organizer") != ORGANIZER:
        return dict(out, decision="HOLD_DETAIL_HOURS_OR_ORGANIZER")
    if detail.get("admission") != "請逕洽主辦單位":
        return dict(out, decision="HOLD_ADMISSION_UNKNOWN_ROLE")
    if any(detail.get(k) is not None for k in ("ticket_url", "ticket_event_id", "session_id", "price", "inventory")):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_FIELDS")
    for source, url, role, value in (
        ("TWTC#16", LIST, "LIST_TITLE", TITLE),
        ("TWTC#16", LIST, "LIST_DATE_START", "2026-11-06"),
        ("TWTC#16", LIST, "LIST_DATE_END", "2026-11-09"),
        ("TWTC#16", LIST, "LIST_VENUE", VENUE),
        ("TWTC#16", DETAIL, "DETAIL_ID_NOT_TICKET_ID", "29251"),
        ("TWTC#16", DETAIL, "DETAIL_TITLE", TITLE),
        ("TWTC#16", DETAIL, "DETAIL_SHOW_HOURS_NOT_SESSIONS", "10:00 ~ 18:00"),
        ("TWTC#16", DETAIL, "DETAIL_ORGANIZER", ORGANIZER),
        ("TWTC#16", DETAIL, "ADMISSION_UNKNOWN_CONTACT_ORGANIZER", "請逕洽主辦單位"),
    ):
        out["candidateProvenance"].append(dict(
            source=source, source_url=url, observed_at=observed_at,
            role=role, valueSHA256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out, decision="HOLD_ADMISSION_PRICE_TICKET_SESSION_UNVERIFIED")
