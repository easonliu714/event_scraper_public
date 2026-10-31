"""P30-L9-CL: source-local TixFun conditional youth discount vs product price; no session-price promotion."""
from datetime import date
from urllib.parse import urlsplit, parse_qs
SOURCE="https://tixfun.com/UTK0201_?PRODUCT_ID=Q023RA4H"
PRODUCT="Q023RA4H"
ROLE="CULTURE_COIN_ELIGIBLE_YOUTH_SEAT_CONDITIONAL_OFFER"
def inspect(record, observed_at):
    out={"gate":"P30-L9-CL","acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,"published":False,"provenance":[]}
    try: date.fromisoformat(observed_at)
    except (ValueError,TypeError): return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(record,dict) or record.get("source_url")!=SOURCE or record.get("product_id")!=PRODUCT:
        return dict(out,decision="HOLD_SOURCE_PRODUCT")
    u=urlsplit(record["source_url"])
    if u.scheme!="https" or u.netloc!="tixfun.com" or u.path!="/UTK0201_" or parse_qs(u.query)!={"PRODUCT_ID":[PRODUCT]}:
        return dict(out,decision="HOLD_SOURCE_URL")
    if record.get("product_price_band")!=(800,3200) or record.get("price_role")!="PRODUCT_RANGE_NOT_SESSION_PRICE":
        return dict(out,decision="HOLD_PRODUCT_BAND_ROLE")
    if record.get("eligible_face_value")!=1800 or record.get("conditional_offer")!=300 or record.get("offer_role")!=ROLE:
        return dict(out,decision="HOLD_CONDITIONAL_OFFER_ROLE")
    if record.get("eligibility")!="CULTURE_COIN_YOUTH_SEAT" or record.get("discount_88_role")!="KEELUNG_RESIDENT_OR_CITY_EMPLOYEE_CONDITIONAL":
        return dict(out,decision="HOLD_ELIGIBILITY_SCOPE")
    if any(record.get(k) is not None for k in ("ticket_session_id","ticket_inventory","ticket_session_price","universal_discount","purchase_url")):
        return dict(out,decision="HOLD_UNVERIFIED_TICKET_PROMOTION")
    out["provenance"]=[{"source":"TIXFUN_09","source_url":SOURCE,"observed_at":observed_at,"role":"PRODUCT_PRICE_RANGE","decision":"REVIEW"},
       {"source":"TIXFUN_09","source_url":SOURCE,"observed_at":observed_at,"role":ROLE,"decision":"REVIEW"},
       {"source":"TIXFUN_09","source_url":SOURCE,"observed_at":observed_at,"role":"KEELUNG_CONDITIONAL_DISCOUNT_NOT_UNIVERSAL","decision":"REVIEW"}]
    return dict(out,decision="HOLD_CONDITIONAL_DISCOUNT_NOT_TICKET_SESSION")
