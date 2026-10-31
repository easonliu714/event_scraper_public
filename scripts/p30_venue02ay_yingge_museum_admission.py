"""P30-VENUE-02AY: museum-wide entry fee is not per-exhibition ticket price."""
from datetime import date
from urllib.parse import urlsplit
STANDARD="https://www.ceramics.ntpc.gov.tw/files/file_pool/1/0J009364880322068325/陶博館門票及場地使用收費標準.pdf"
INFO_SHEET="https://www.ceramics.ntpc.gov.tw/files/file_pool/1/0N310504807960339935/門票資訊-更新.pdf"
EXHIBITIONS=("0Q218341727998294094","0Q218346582180038351")
def inspect(x,observed_at):
    out={"gate":"P30-VENUE-02AY","acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,"published":False,"provenance":[]}
    try:date.fromisoformat(observed_at)
    except (TypeError,ValueError):return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(x,dict) or x.get("standard_url")!=STANDARD or x.get("information_sheet_url")!=INFO_SHEET:
        return dict(out,decision="HOLD_OFFICIAL_DOCUMENTS")
    if any(urlsplit(u).scheme!="https" or urlsplit(u).netloc!="www.ceramics.ntpc.gov.tw" for u in (x["standard_url"],x["information_sheet_url"])):
        return dict(out,decision="HOLD_SOURCE_HOST")
    if x.get("museum_admission_ntd")!=80 or x.get("price_role")!="GENERAL_MUSEUM_ENTRY_NOT_EXHIBITION_PRICE":
        return dict(out,decision="HOLD_MUSEUM_ADMISSION_ROLE")
    if x.get("new_taipei_resident_free") is not True or x.get("students_free") is not True or x.get("age_65_plus_free") is not True or x.get("under_12_free") is not True or x.get("proof_required") is not True:
        return dict(out,decision="HOLD_ELIGIBILITY_ROLE")
    if x.get("exhibition_sids")!=EXHIBITIONS or x.get("exhibition_price_role")!="UNKNOWN_NOT_DERIVED_FROM_MUSEUM_ADMISSION":
        return dict(out,decision="HOLD_EXHIBITION_PRICE_SCOPE")
    if x.get("information_sheet_retired_civil_servant_listed") is not True or x.get("standards_table_retired_civil_servant_listed") is not False or x.get("conflict_decision")!="HOLD_DOCUMENT_LIST_DIFFERENCE_NO_AUTOMATIC_ELIGIBILITY":
        return dict(out,decision="HOLD_DOCUMENT_VERSION_CONFLICT")
    if any(x.get(k) is not None for k in ("exhibition_ticket_price","exhibition_ticket_url","ticket_session_id","inventory","assumed_legacy_eligibility")):
        return dict(out,decision="HOLD_UNVERIFIED_EXHIBITION_TICKET")
    out["provenance"]=[{"source":"YINGGE_MUSEUM_OFFICIAL","source_url":STANDARD,"observed_at":observed_at,"role":"MUSEUM_GENERAL_ADMISSION_AND_CONDITIONAL_FREE_ENTRY","decision":"REVIEW"},
       {"source":"YINGGE_MUSEUM_OFFICIAL","source_url":INFO_SHEET,"observed_at":observed_at,"role":"OFFICIAL_INFORMATION_SHEET_FREE_ENTRY_LIST_DISCREPANCY","decision":"HOLD"}]
    return dict(out,decision="HOLD_MUSEUM_ADMISSION_NOT_EXHIBITION_TICKET")
