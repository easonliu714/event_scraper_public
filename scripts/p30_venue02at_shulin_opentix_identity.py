"""Shulin official venue descriptive performances vs independent OPENTIX #05 pages.
Canonical event candidates are first-party OPENTIX pages; venue shortlink redirects
are NOT resolved, so shortlink->event edge remains HOLD. No ticket-session promotion.
"""
import datetime
from urllib.parse import urlsplit
VENUE="https://www.culture.ntpc.gov.tw/shulin_artcenter_chi/xmdoc/cont?sid=0Q273522679833703495&xsmsid=0J080506169482009359"
EVENTS={
 "BEL":{"event_id":"2099700588990402561","title":"傑宏・貝爾","shortlink":"https://s.opentix.life/p/P5fece325","shows":(("2026-11-21","14:30"),),"face_price":700},
 "BODY":{"event_id":"2099688567429373953","title":"身體我的名片","shortlink":"https://s.opentix.life/p/P142818f5","shows":(("2026-11-28","13:00"),("2026-11-29","11:00")),"face_price":1000},
}
PACKAGE="https://www.opentix.life/ticketpackage/2102208181225205761"
def exact(url,expected):
 if not isinstance(url,str):return False
 a=urlsplit(url);b=urlsplit(expected)
 return (a.scheme,a.netloc,a.path,a.query,a.fragment)==(b.scheme,b.netloc,b.path,b.query,b.fragment)
def normalize_title(value):
 if not isinstance(value,str):return ""
 return value.replace("．","・").replace("·","・")
def inspect(venue,opentix,package,observed_at):
 out={"gate":"P30-VENUE-02AT","acceptedFields":0,"goldenAccepted":0,"published":False,"provenance":[]}
 try:datetime.date.fromisoformat(observed_at)
 except (TypeError,ValueError):return dict(out,decision="HOLD_OBSERVED_AT")
 if not isinstance(venue,dict) or not exact(venue.get("url"),VENUE) or not isinstance(venue.get("shows"),dict) or set(venue["shows"])!=set(EVENTS):
  return dict(out,decision="HOLD_VENUE_SOURCE")
 if not isinstance(opentix,dict) or set(opentix)!=set(EVENTS):return dict(out,decision="HOLD_DISTINCT_OPENTIX_EVENTS")
 for key,expected in EVENTS.items():
  v=venue["shows"][key];r=opentix[key]
  if not isinstance(v,dict) or not isinstance(r,dict):return dict(out,decision="HOLD_SOURCE_SHAPE")
  if not exact(v.get("shortlink"),expected["shortlink"]):return dict(out,decision="HOLD_VENUE_SHORTLINK")
  url="https://www.opentix.life/event/"+expected["event_id"]
  if not exact(r.get("url"),url) or r.get("event_id")!=expected["event_id"]:
   return dict(out,decision="HOLD_OPENTIX_CANONICAL_ID")
  if normalize_title(expected["title"]) not in normalize_title(r.get("title")) or normalize_title(expected["title"]) not in normalize_title(v.get("title")):
   return dict(out,decision="HOLD_INDEPENDENT_TITLE_PARITY")
  if v.get("venue")!="樹林藝文中心演藝廳" or r.get("venue")!="樹林藝文中心演藝廳":
   return dict(out,decision="HOLD_VENUE_PARITY")
  if tuple(map(tuple,v.get("descriptive_shows",())))!=expected["shows"] or tuple(map(tuple,r.get("description_shows",())))!=expected["shows"]:
   return dict(out,decision="HOLD_DESCRIPTIVE_TIME_PARITY")
  if r.get("face_price")!=expected["face_price"] or r.get("price_role")!="ORIGINAL_FACE_PRICE":
   return dict(out,decision="HOLD_PRICE_ROLE")
  if r.get("ticket_session_ids") is not None or r.get("inventory") is not None:
   return dict(out,decision="HOLD_TICKET_SESSION_UNVERIFIED")
  if r.get("shortlink_redirect_verified") is not False:
   return dict(out,decision="HOLD_SHORTLINK_REDIRECT_UNVERIFIED")
  out["provenance"].append({"source":"OPENTIX_CANONICAL_05","source_url":url,"observed_at":observed_at,"role":"INDEPENDENT_EVENT_PAGE_TITLE_DATE_CANDIDATE","decision":"REVIEW_SHORTLINK_MAPPING_UNRESOLVED"})
 if not isinstance(package,dict) or not exact(package.get("url"),PACKAGE):
  return dict(out,decision="HOLD_PACKAGE_ID")
 if package.get("role")!="SALE_PACKAGE" or package.get("sale_window")!=["2026-09-28","2026-11-21"] or package.get("bundle_original_pair")!=["BEL","BODY"] or package.get("bundle_fee")!=1000:
  return dict(out,decision="HOLD_PACKAGE_SALE_VS_SHOWTIME")
 if package.get("ticket_session_ids") is not None:
  return dict(out,decision="HOLD_PACKAGE_NOT_TICKET_SESSION")
 out["provenance"].append({"source":"OPENTIX_CANONICAL_05","source_url":PACKAGE,"observed_at":observed_at,"role":"BUNDLE_SALE_WINDOW_NOT_SHOWTIME","decision":"REVIEW"})
 return dict(out,decision="HOLD_SHORTLINK_MAPPING_AND_TICKET_SESSION_IDS")
