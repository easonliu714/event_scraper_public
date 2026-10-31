"""P0 New Taipei venue umbrella contains performances, workshops, and a market.
Two OPENTIX shortlinks are NOT verified canonical Event IDs; ACCUPASS direct links are.
"""
import datetime
from urllib.parse import urlsplit
VENUE_URL="https://www.culture.ntpc.gov.tw/shulin_artcenter_chi/xmdoc/cont?sid=0Q273522679833703495&xsmsid=0J080506169482009359"
ROWS={
 "BEL":("PERFORMANCE","https://s.opentix.life/p/P5fece325","OPENTIX_CLAIMED",("2026-11-21 14:30",)),
 "BODY":("PERFORMANCE","https://s.opentix.life/p/P142818f5","OPENTIX_CLAIMED",("2026-11-28 13:00","2026-11-29 11:00")),
 "FAMILY":("WORKSHOP","https://www.accupass.com/event/2609151410103172453460","ACCUPASS_CANONICAL_02",("2026-11-21 10:30","2026-11-22 10:30")),
 "DANCE":("WORKSHOP","https://www.accupass.com/event/2609041147021848655729","ACCUPASS_CANONICAL_02",("2026-11-16","2026-11-27")),
 "MARKET":("MARKET",None,None,("2026-11-28 13:00","2026-11-29 11:00"))
}
def exact(url,expected):
 if expected is None:return url is None
 if not isinstance(url,str):return False
 p=urlsplit(url);e=urlsplit(expected)
 return (p.scheme,p.netloc,p.path,p.query,p.fragment)==(e.scheme,e.netloc,e.path,e.query,e.fragment)
def inspect(venue,observed_at):
 out={"gate":"P30-VENUE-02AS","acceptedFields":0,"goldenAccepted":0,"published":False,"provenance":[]}
 try:datetime.date.fromisoformat(observed_at)
 except (ValueError,TypeError):return dict(out,decision="HOLD_OBSERVED_AT")
 if not isinstance(venue,dict) or venue.get("url")!=VENUE_URL or not isinstance(venue.get("rows"),dict):
  return dict(out,decision="HOLD_OFFICIAL_VENUE_SID")
 if set(venue["rows"])!=set(ROWS):return dict(out,decision="HOLD_FESTIVAL_IS_NOT_SINGLE_EVENT")
 for key,(kind,link,platform,shows) in ROWS.items():
  r=venue["rows"][key]
  if not isinstance(r,dict) or r.get("kind")!=kind:return dict(out,decision="HOLD_CATEGORY_SCOPE")
  if not exact(r.get("ticket_url"),link):return dict(out,decision="HOLD_DIRECT_LINK_IDENTITY")
  if tuple(r.get("descriptive_times",()))!=shows:return dict(out,decision="HOLD_LOCAL_TIME_ROLE")
  if r.get("claimed_platform")!=platform:return dict(out,decision="HOLD_PLATFORM_ROLE")
  if r.get("ticket_session_id") is not None or r.get("inventory") is not None:
   return dict(out,decision="HOLD_NO_SESSION_INVENTORY")
  if key in ("BEL","BODY") and r.get("canonical_ticket_event_id") is not None:
   return dict(out,decision="HOLD_OPENTIX_SHORTLINK_UNRESOLVED")
  out["provenance"].append({"source":"SHULIN_P0_NEW_TAIPEI","source_url":VENUE_URL,"observed_at":observed_at,"role":kind+"_SOURCE_EDGE","decision":"REVIEW_NOT_FORMALLY_ACCEPTED"})
 return dict(out,decision="HOLD_MIXED_EVENT_TYPES_AND_SHORTLINK_IDENTITY")
