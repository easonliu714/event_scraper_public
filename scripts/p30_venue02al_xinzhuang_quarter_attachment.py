#!/usr/bin/env python3
"""P30-VENUE-02AL: Xinzhuang official quarter bulletin != event detail."""
import datetime
import hashlib

INDEX = "https://www.xzcac.ntpc.gov.tw/xmdoc?XsmSId=0O093511499740188930"
SID = "0Q292597022385142603"
DETAIL = "https://www.xzcac.ntpc.gov.tw/xmdoc/cont?sid=" + SID + "&xsmsid=0O093511499740188930"
TITLE = "2026年10至12月新北市各藝文中心聯合季節目單"
UPDATED = "2026-10-19"
HOLD = "HARD_HOLD_NO_PUBLICATION"

def inspect(index, detail, observed_at):
    out = dict(gate="P30-VENUE-02AL", source="Xinzhuang Cultural Arts Center P0",
               officialGETinCI=0, candidateProvenance=[], acceptedFields=0,
               goldenAccepted=0, published=False, releaseState=HOLD,
               individualEventIdsVerified=0, attachmentParsed=False)
    if not isinstance(index, dict) or not isinstance(detail, dict):
        return dict(out, decision="HOLD_UNSTRUCTURED")
    if index.get("url") != INDEX or index.get("detail_url") != DETAIL or detail.get("url") != DETAIL:
        return dict(out, decision="HOLD_FIRST_PARTY_DETAIL_LINK")
    if index.get("title") != TITLE or detail.get("title") != TITLE or detail.get("sid") != SID:
        return dict(out, decision="HOLD_QUARTER_SID_TITLE_PARITY")
    try:
        datetime.date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVED_AT")
    if detail.get("updated_at") != UPDATED:
        return dict(out, decision="HOLD_ARTICLE_UPDATED_AT")
    if detail.get("attachment_label") != TITLE:
        return dict(out, decision="HOLD_ATTACHMENT_LABEL")
    if detail.get("attachment_type") != "PDF_LINK_UNPARSED":
        return dict(out, decision="HOLD_ATTACHMENT_NOT_INDEPENDENTLY_PARSED")
    if detail.get("event_ids") or detail.get("event_dates") or detail.get("ticket_event_ids"):
        return dict(out, decision="HOLD_UNVERIFIED_EVENT_FIELDS")
    for role, value in (("QUARTERLY_BULLETIN_TITLE", TITLE),
                        ("ARTICLE_UPDATED_AT_NOT_EVENT_DATE", UPDATED),
                        ("ATTACHMENT_LINK_LABEL_NOT_EVENT_DETAIL", TITLE)):
        out["candidateProvenance"].append(dict(source=out["source"], source_url=DETAIL,
            observed_at=observed_at, role=role,
            valueSHA256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out, decision="HOLD_PDF_ATTACHMENT_NO_EVENT_LEVEL_IDENTITY")

if __name__ == "__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_NETWORK")
