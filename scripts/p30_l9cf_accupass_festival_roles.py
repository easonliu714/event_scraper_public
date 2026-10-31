"""Source-observed ACCUPASS #02 direct festival links; isolated REVIEW only.
Official venue SID is an umbrella; distinct ACCUPASS Event IDs are not ticket Session IDs.
"""
import datetime
from urllib.parse import urlsplit
VENUE_URL = "https://www.culture.ntpc.gov.tw/shulin_artcenter_chi/xmdoc/cont?sid=0Q273522679833703495&xsmsid=0J080506169482009359"
EVENTS = {
 "PARENT_CHILD": ("2609151410103172453460", "跟爸爸媽媽一起用身體揉一座山", (("2026-11-21","10:30","11:30"),("2026-11-22","10:30","11:30")), 100),
 "DANCE_WORKSHOPS": ("2609041147021848655729", "身體工作坊", (), 100)
}
def exact_accupass(url, event_id):
 if not isinstance(url,str): return False
 p=urlsplit(url)
 return (p.scheme,p.netloc,p.path,p.query,p.fragment)==("https","www.accupass.com","/event/"+event_id,"","")
def inspect(venue, records, observed_at):
 out={"gate":"P30-L9-CF","acceptedFields":0,"goldenAccepted":0,"published":False,"provenance":[]}
 try: datetime.date.fromisoformat(observed_at)
 except (ValueError,TypeError): return dict(out,decision="HOLD_OBSERVED_AT")
 if not isinstance(venue,dict) or venue.get("url")!=VENUE_URL or not isinstance(records,dict):
  return dict(out,decision="HOLD_SOURCE_SHAPE")
 if set(records)!=set(EVENTS): return dict(out,decision="HOLD_DISTINCT_EVENT_SCOPE")
 for key,(eid,title,shows,price) in EVENTS.items():
  r=records[key]
  if not isinstance(r,dict) or not exact_accupass(venue.get("links",{}).get(key),eid) or not exact_accupass(r.get("url"),eid):
   return dict(out,decision="HOLD_DIRECT_SOURCE_LINK")
  if title not in r.get("title",""): return dict(out,decision="HOLD_EVENT_TITLE")
  if r.get("venue")!="樹林藝文中心3F排練室": return dict(out,decision="HOLD_VENUE")
  if key=="PARENT_CHILD":
   if tuple(map(tuple,r.get("description_sessions",[])))!=shows: return dict(out,decision="HOLD_TWO_DESCRIPTION_SESSIONS")
   if r.get("registration_unit")!="PARENT_CHILD_PAIR" or r.get("listed_fee")!=price: return dict(out,decision="HOLD_FEE_UNIT")
  else:
   if r.get("description_session_count")!=16 or r.get("range")!=["2026-11-16","2026-11-27"]:
    return dict(out,decision="HOLD_16_WORKSHOP_UMBRELLA")
   if r.get("listed_fee")!=price or r.get("registration_unit")!="PER_WORKSHOP":
    return dict(out,decision="HOLD_FEE_UNIT")
  if r.get("ticket_session_ids") is not None or r.get("inventory") is not None:
   return dict(out,decision="HOLD_NO_TICKET_SESSION_ID")
  out["provenance"].append({"source":"ACCUPASS_CANONICAL_02","source_url":r["url"],"observed_at":observed_at,"role":"DIRECT_EVENT_ID_WITH_DESCRIPTIVE_SESSIONS","decision":"REVIEW_NOT_FORMALLY_ACCEPTED"})
 return dict(out,decision="HOLD_EVENT_ID_NOT_TICKET_SESSION_ID_AND_FEE_UNIT")
