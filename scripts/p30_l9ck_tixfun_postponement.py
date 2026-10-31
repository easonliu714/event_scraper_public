"""P30-L9-CK: source-bound TixFun #09 list/detail product and postponed show; no sale/session promotion."""
from datetime import date
from urllib.parse import urlsplit,parse_qs
LIST_URL="https://tixfun.com/UTK0102_?TYPE=0"
DETAIL_URL="https://tixfun.com/UTK0201_?PRODUCT_ID=Q023RA4H"
PRODUCT_ID="Q023RA4H"
TITLE="故事工廠 第24回作品《婚禮上的小抄》"
ORIGINAL=("2026-09-05","14:30","嘉義縣表演藝術中心 演藝廳")
POSTPONED=("2027-03-06","14:30","嘉義縣表演藝術中心 演藝廳")
HEADER=("2026-11-06","2027-03-06")
def inspect(x,observed_at):
    out={"gate":"P30-L9-CK","acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,"published":False,"provenance":[]}
    try: date.fromisoformat(observed_at)
    except (ValueError,TypeError): return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(x,dict) or x.get("list_url")!=LIST_URL or x.get("list_title")!=TITLE:
        return dict(out,decision="HOLD_LIST_IDENTITY")
    u=urlsplit(x.get("detail_url",""))
    if x.get("detail_url")!=DETAIL_URL or u.netloc!="tixfun.com" or u.path!="/UTK0201_" or parse_qs(u.query)!={"PRODUCT_ID":[PRODUCT_ID]} or x.get("product_id")!=PRODUCT_ID:
        return dict(out,decision="HOLD_PRODUCT_ID")
    if x.get("detail_title")!=TITLE or x.get("header_range")!=HEADER or x.get("price_band")!=(800,3200):
        return dict(out,decision="HOLD_DETAIL_PARITY")
    if x.get("original")!=ORIGINAL or x.get("postponed")!=POSTPONED or x.get("change_role")!="ONE_CHIAYI_SHOW_RESCHEDULE_NOT_ALL_SHOWS":
        return dict(out,decision="HOLD_POSTPONEMENT_SCOPE")
    if x.get("refund_exception_cutoff")!="2026-09-05" or x.get("refund_exception_role")!="PAST_RESCHEDULE_EXCEPTION_NOT_CURRENT_POLICY":
        return dict(out,decision="HOLD_REFUND_EXCEPTION_ROLE")
    if x.get("general_refund_days")!=10 or x.get("general_refund_fee_percent")!=10 or x.get("general_refund_role")!="RELATIVE_POLICY_NOT_ABSOLUTE":
        return dict(out,decision="HOLD_GENERAL_REFUND_ROLE")
    if x.get("show_duration_minutes")!=160 or x.get("intermission_minutes")!=15 or x.get("duration_role")!="DESCRIPTION_NOT_TICKET_SESSION":
        return dict(out,decision="HOLD_DURATION_ROLE")
    if any(x.get(k) is not None for k in ("ticket_session_id","inventory","session_price","computed_refund_deadline")):
        return dict(out,decision="HOLD_UNVERIFIED_SESSION_FIELDS")
    out["provenance"]=[
      {"source":"TIXFUN_09","source_url":LIST_URL,"observed_at":observed_at,"role":"LIST_PRODUCT_TITLE","decision":"REVIEW"},
      {"source":"TIXFUN_09","source_url":DETAIL_URL,"observed_at":observed_at,"role":"DETAIL_PRODUCT_ID_HEADER_PRICE_BAND","decision":"REVIEW"},
      {"source":"TIXFUN_09","source_url":DETAIL_URL,"observed_at":observed_at,"role":"SINGLE_CHIAYI_RESCHEDULE_AND_REFUND_EXCEPTION","decision":"REVIEW"}]
    return dict(out,decision="HOLD_PRODUCT_DETAIL_SOURCE_BOUND_NO_SESSION_ID")
