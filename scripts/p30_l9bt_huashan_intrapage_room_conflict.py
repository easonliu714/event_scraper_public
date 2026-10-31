#!/usr/bin/env python3
"""P30-L9-BT: strict same-page room-role conflict diagnostic, never publish."""
import hashlib
import re
from p30_l9bs_huashan_accupass_direct_edge import audit, VENUE_SOURCE, TICKET_SOURCE, HOLD
ROLES={"HEADER_VENUE_ROOM":"地點","BODY_VENUE_ROOM":"►活動地點"}
STAMP=re.compile(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ")
def digest(v):
    return hashlib.sha256(v.encode("utf-8")).hexdigest()
def inspect(venue,ticket,room_evidence):
    out={"gate":"P30-L9-BT","source":VENUE_SOURCE,"ticketSource":TICKET_SOURCE,
         "roomClaims":0,"candidateProvenance":[],"acceptedFields":0,
         "goldenAccepted":0,"published":False,"releaseState":HOLD,"ticketEventId":None}
    prior=audit(venue,ticket)
    out["priorIdentityDecision"]=prior["decision"]
    if not (prior["directLinkBound"] and prior["sameCoreTitle"] and prior["sameSession"]):
        return dict(out,decision="HOLD_PRIOR_SOURCE_IDENTITY_OR_SESSION")
    if not isinstance(room_evidence,list) or len(room_evidence)!=2:
        return dict(out,decision="HOLD_NOT_EXACT_TWO_ROOM_CLAIMS")
    found={}
    for entry in room_evidence:
        if not isinstance(entry,dict):
            return dict(out,decision="HOLD_UNBOUND_ROOM_EVIDENCE")
        role,value=entry.get("role"),entry.get("value")
        if role not in ROLES or role in found:
            return dict(out,decision="HOLD_DUPLICATE_OR_UNKNOWN_ROOM_ROLE")
        if (entry.get("label")!=ROLES[role] or entry.get("source")!=VENUE_SOURCE
                or entry.get("source_url")!=venue.get("url")
                or not isinstance(entry.get("observed_at"),str)
                or not STAMP.fullmatch(entry["observed_at"])):
            return dict(out,decision="HOLD_ROOM_LABEL_SOURCE_PROVENANCE")
        if (not isinstance(value,str) or value!=value.strip() or not 2<=len(value)<=160
                or any(ch in value for ch in "\r\n<>")):
            return dict(out,decision="HOLD_ROOM_VALUE_INVALID")
        found[role]=value
    if set(found)!=set(ROLES) or found["HEADER_VENUE_ROOM"]!=venue.get("room"):
        return dict(out,decision="HOLD_HEADER_ROOM_NOT_SAME_SOURCE_BOUND")
    out["roomClaims"]=2
    for entry in room_evidence:
        out["candidateProvenance"].append({
            "source":VENUE_SOURCE,"source_url":venue["url"],
            "observed_at":entry["observed_at"],"role":entry["role"],
            "decision":"REVIEW_NOT_ACCEPTED","valueSHA256":digest(entry["value"])})
    out["candidateProvenance"].append({
        "source":TICKET_SOURCE,"source_url":ticket["url"],
        "observed_at":ticket["observed_at"],"role":"TICKET_VENUE_ROOM",
        "decision":"REVIEW_NOT_ACCEPTED","valueSHA256":digest(ticket["room"])})
    out["sameSourceConflict"]=found["HEADER_VENUE_ROOM"]!=found["BODY_VENUE_ROOM"]
    out["ticketMatchesBodyExactly"]=ticket["room"]==found["BODY_VENUE_ROOM"]
    out["ticketMatchesHeaderExactly"]=ticket["room"]==found["HEADER_VENUE_ROOM"]
    if out["sameSourceConflict"]:
        return dict(out,decision="HOLD_SAME_SOURCE_HEADER_BODY_ROOM_CONFLICT")
    if not out["ticketMatchesHeaderExactly"]:
        return dict(out,decision="HOLD_CROSS_SOURCE_ROOM_CONFLICT")
    return dict(out,decision="REVIEW_ROOM_PARITY_NOT_FORMALLY_ACCEPTED")
if __name__=="__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_IMPLICIT_NETWORK")
