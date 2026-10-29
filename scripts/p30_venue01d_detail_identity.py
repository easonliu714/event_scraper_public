"""P30-VENUE-01D: fail-closed official announcement/detail identity, offline only.
DataSN and official URL tokens are NOT ticket-platform Event IDs.
"""
from __future__ import annotations
import hashlib
import p30_venue01_taipei_arena_readonly as arena
import p30_venue01c_date_conflict as date_role

RELEASE = "HARD_HOLD_NO_PUBLICATION"

def assess(data_sn, source_url, list_title, detail_url, detail_title, detail_body):
    base = dict(decision="HOLD_INVALID_INPUT", sourceIdentity="UNKNOWN",
                ticketEventId=None, acceptedFields=0, goldenAccepted=0,
                published=False, rawContentPersisted=False, dateRole="UNKNOWN")
    if not isinstance(data_sn, str) or not data_sn.isascii() or not data_sn.isdigit() or not (1 <= len(data_sn) <= 12):
        return base
    if not arena._source_url_ok(source_url) or not arena._source_url_ok(detail_url):
        return dict(base, decision="HOLD_UNVERIFIED_OFFICIAL_URL")
    if source_url != detail_url:
        return dict(base, decision="HOLD_SOURCE_URL_DRIFT")
    if not all(isinstance(x, str) for x in (list_title, detail_title, detail_body)):
        return base
    if not (0 < len(list_title.strip()) <= 250 and 0 < len(detail_title.strip()) <= 250):
        return dict(base, decision="HOLD_TITLE_SHAPE")
    if list_title.strip() != detail_title.strip():
        return dict(base, decision="HOLD_TITLE_MISMATCH")
    if len(detail_body) > date_role.MAX_TEXT:
        return dict(base, decision="HOLD_BODY_CAP")
    role = date_role.inspect_date_role(list_title, detail_body)
    fingerprint = hashlib.sha256((data_sn + "\n" + source_url).encode()).hexdigest()[:20]
    return dict(base, decision="REVIEW_OFFICIAL_DETAIL_TITLE_ONLY",
                sourceIdentity="REVIEW_DATASN_OFFICIAL_URL_TITLE",
                sourceKeyDigest=fingerprint, dateRole=role["decision"],
                titleMatch=True, ticketPlatformClaimIsIdentity=False)

def offline_contract():
    return dict(kind="EVENTRADAR_P30_VENUE01D_DETAIL_IDENTITY_V1",
                releaseState=RELEASE, httpRequests=0, acceptedFields=0,
                goldenAccepted=0, published=False, dataSNIsTicketEventId=False,
                sourceUrlTokenIsTicketEventId=False, rawHtmlPersisted=False,
                decision="REVIEW_OFFLINE_SOURCE_IDENTITY_CONTRACT_ONLY")
