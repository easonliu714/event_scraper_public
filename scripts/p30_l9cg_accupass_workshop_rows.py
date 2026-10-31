"""ACCUPASS #02 public description contains 16 distinct named workshop rows.
Only description-local time evidence: never infer ticket-session IDs or inventory.
Source: https://www.accupass.com/event/2609041147021848655729
"""
import datetime
from urllib.parse import urlsplit

SOURCE = "https://www.accupass.com/event/2609041147021848655729"
# (source-local workshop heading, date, start, end), manually audited 2026-10-31
ROWS = (
 ("每個人的身體都有自己的故事","2026-11-16","14:30","16:30"),
 ("當踢踏碰上街舞：踢踏跨界工作坊","2026-11-17","10:00","12:00"),
 ("Waacking零基礎工作坊","2026-11-17","14:30","16:30"),
 ("摸鏡！模鏡！","2026-11-18","10:00","12:00"),
 ("一起跳島超浪漫","2026-11-18","14:30","16:30"),
 ("身體與他（它）的關係","2026-11-19","10:00","12:00"),
 ("會唱歌的身體！—逗陣來車鼓","2026-11-19","14:30","16:30"),
 ("當代土風舞一起跳","2026-11-20","10:00","12:00"),
 ("一起來跳Modern Dance","2026-11-20","14:30","16:30"),
 ("身體裡長出律動","2026-11-25","10:00","12:00"),
 ("跳舞機：玩轉規則","2026-11-25","14:30","16:30"),
 ("在往返中 再見","2026-11-26","10:00","12:00"),
 ("路之行走｜走回自己的身體","2026-11-26","14:30","16:30"),
 ("當代舞－身體探索","2026-11-26","19:00","21:00"),
 ("The Art of Falling","2026-11-27","10:00","12:00"),
 ("我愛我","2026-11-27","14:30","16:30"),
)
def exact_source(url):
 if not isinstance(url,str): return False
 p=urlsplit(url)
 return (p.scheme,p.netloc,p.path,p.query,p.fragment)==("https","www.accupass.com","/event/2609041147021848655729","","")
def inspect(record, observed_at):
 out={"gate":"P30-L9-CG","acceptedFields":0,"goldenAccepted":0,"published":False,"provenance":[]}
 try: datetime.date.fromisoformat(observed_at)
 except (TypeError,ValueError): return dict(out,decision="HOLD_OBSERVED_AT")
 if not isinstance(record,dict) or not exact_source(record.get("url")) or record.get("event_id")!="2609041147021848655729":
  return dict(out,decision="HOLD_SAME_EVENT_ID")
 if record.get("ticket_session_ids") is not None or record.get("inventory") is not None:
  return dict(out,decision="HOLD_NO_PUBLIC_TICKET_SESSION_IDS")
 if record.get("fee_unit")!="PER_WORKSHOP" or record.get("listed_fee")!=100:
  return dict(out,decision="HOLD_FEE_UNIT")
 rows=record.get("description_rows")
 if not isinstance(rows,list) or len(rows)!=16: return dict(out,decision="HOLD_DESCRIPTION_ROW_COUNT")
 seen=set()
 for i,row in enumerate(rows):
  if not isinstance(row,dict): return dict(out,decision="HOLD_LOCAL_ROW_SHAPE")
  key=(row.get("title"),row.get("date"),row.get("start"),row.get("end"))
  if key in seen: return dict(out,decision="HOLD_DUPLICATE_DESCRIPTION_ROW")
  seen.add(key)
  if key!=ROWS[i] or row.get("role")!="DESCRIPTION_WORKSHOP_TIME":
   return dict(out,decision="HOLD_TITLE_DATE_LOCAL_BINDING")
  try:
   day=datetime.date.fromisoformat(key[1]);start=datetime.time.fromisoformat(key[2]);end=datetime.time.fromisoformat(key[3])
  except (TypeError,ValueError):return dict(out,decision="HOLD_DATE_TIME_FORMAT")
  if not datetime.date(2026,11,16)<=day<=datetime.date(2026,11,27) or start>=end:
   return dict(out,decision="HOLD_DATE_TIME_RANGE")
  out["provenance"].append({"source":"ACCUPASS_CANONICAL_02","source_url":SOURCE,"observed_at":observed_at,"role":"DESCRIPTION_WORKSHOP_TIME","title":key[0],"decision":"REVIEW_NOT_TICKET_SESSION"})
 return dict(out,decision="HOLD_16_DESCRIPTION_ROWS_NOT_16_TICKET_SESSIONS")
