import copy,importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[2]/"scripts"/"p30_l5e2_bitan_government.py"
spec=importlib.util.spec_from_file_location("l5e2_bitan",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def parent():
 return {"kind":m.PARENT,"sourceRuntime":"DORMANT",
   "published":False,"goldenAccepted":False,
   "firstPartyEventDetailsIndependentlyVerified":0,
   "fieldPromotionCount":0,"articleSamplesCount":6,
   "samples":[{"aggregatorUrl":m.AGG_URL,
    "title":"碧潭地景裝置展 遇見小王子漫遊碧潭間",
    "articleIdentity":"AGGREGATOR_ARTICLE_H1_MATCH",
    "firstPartyVerified":False,"originalOfficialUrl":None,
    "dateStart":None,"dateEnd":None,"sourceSectionFound":True,
    "credits":[{"role":"ATTRIBUTED_SOCIAL_POST_ACCOUNT_NOT_VERIFIED",
                "originalOfficialEventDetailVerified":False}]}]}
CAL=("碧潭地景裝置展-遇見小王子 漫遊碧潭間 定位點 "
 "活動日期： 2026-10-17 ~ 2026-12-13 "
 "活動地點：新北市新店區碧潭風景區 "
 "主辦單位：觀光旅遊局 各活動時間以主辦單位最新公告為主")
NEWS=("發佈日期：2026-10-14 發佈單位：新北市政府觀光旅遊局 "
 "小王子出版80周年降臨碧潭 打造夢幻水岸童話 "
 "自10月17日起至12月13日期間展出")
class TestGate(unittest.TestCase):
 def test_01_exact_allowlist_only(self):
  self.assertTrue(m.exact_url(m.CALENDAR))
  self.assertTrue(m.exact_url(m.MUNICIPAL))
  for v in ["https://newtaipei.travel/zh-tw/calendar/detail/4058?auth=x",
   "http://newtaipei.travel/zh-tw/calendar/detail/4058",
   "https://newtaipei.travel.evil.com/zh-tw/calendar/detail/4058",
   "https://newtaipei.travel/zh-tw/login",
   "https://www.facebook.com/somepost","https://www.google.com/maps"]:
   self.assertFalse(m.exact_url(v))
 def test_02_government_event_full_name(self):
  v=m.parse_calendar(CAL)
  self.assertEqual(v["identity"],"OFFICIAL_EVENT_TITLE_BOUND")
  self.assertTrue(v["completeIdentity"])
 def test_03_full_gregorian_dates(self):
  v=m.parse_calendar(CAL)
  self.assertEqual(v["observedPeriod"],["2026-10-17","2026-12-13"])
  self.assertEqual(v["dateRole"],"OFFICIAL_ORGANISER_EVENT_PERIOD")
 def test_04_org_and_venue_are_roles(self):
  v=m.parse_calendar(CAL)
  self.assertEqual(v["organiser"],"新北市政府觀光旅遊局")
  self.assertEqual(v["venueEvidence"],m.VENUE)
 def test_05_unrelated_event date earlier in sidebar cannot bind(self):
  v=m.parse_calendar("活動日期： 2026-09-01 ~ 2026-09-22 其他展覽 "+CAL)
  self.assertEqual(v["observedPeriod"],["2026-10-17","2026-12-13"])
 def test_06_date missing rejects(self):
  v=m.parse_calendar(CAL.replace("2026-12-13","2026-12-31"))
  self.assertFalse(v["completeIdentity"])
 def test_07_partial dates cannot get year from news(self):
  v=m.parse_calendar(CAL.replace("2026-10-17 ~ 2026-12-13","10/17 ~ 12/13"))
  self.assertFalse(v["completeIdentity"])
 def test_08_wrong agency fails(self):
  self.assertFalse(m.parse_calendar(CAL.replace("主辦單位：觀光旅遊局","主辦單位：某旅行社"))["completeIdentity"])
 def test_09_wrong venue fails(self):
  self.assertFalse(m.parse_calendar(CAL.replace(m.VENUE,"臺北國際會議中心"))["completeIdentity"])
 def test_10 title mismatch fails(self):
  self.assertEqual(m.parse_calendar(CAL.replace(m.OFFICIAL_NAME,"2026其他展覽"))["identity"],
                   "OFFICIAL_TITLE_MISSING_HOLD")
 def test_11 news published date and agency are separate from event date(self):
  v=m.parse_news(NEWS)
  self.assertEqual(v["publishedAtDate"],"2026-10-14")
  self.assertEqual(v["dateRole"],"NEWS_PUBLICATION_DATE_NOT_EVENT_START")
  self.assertTrue(v["sufficientAdditionalContext"])
 def test_12 news wrong publication fails(self):
  self.assertFalse(m.parse_news(NEWS.replace("2026-10-14","2026-10-15"))["sufficientAdditionalContext"])
 def test_13 unrelated news fails(self):
  self.assertFalse(m.parse_news("市政新聞 資料 2026-10-14")["sufficientAdditionalContext"])
 def test_14 true parent role and first party held until gov(self):
  self.assertIsNotNone(m.vet_parent(parent()))
 def test_15 wrong aggregator H1 rejected(self):
  p=parent();p["samples"][0]["articleIdentity"]="ARTICLE_TITLE_OR_HTTP_HOLD"
  with self.assertRaisesRegex(ValueError,"HOLD_BITAN_UNVERIFIED_AGGREGATOR_ARTICLE"):m.vet_parent(p)
 def test_16 social cannot be forged first-party(self):
  p=parent();p["samples"][0]["credits"][0]["originalOfficialEventDetailVerified"]=True
  with self.assertRaisesRegex(ValueError,"HOLD_FORGED_PARENT_ORIGIN_PROOF"):m.vet_parent(p)
 def test_17 forged writer Golden rejected(self):
  for k,v in [("published",True),("goldenAccepted",True),
   ("sourceRuntime","ACTIVE"),("fieldPromotionCount",1)]:
   p=parent();p[k]=v
   with self.assertRaisesRegex(ValueError,"HOLD_L5E1_GOVERNANCE"):m.vet_parent(p)
 def test_18 duplicate same aggregator source rejected(self):
  p=parent();p["samples"].append(p["samples"][0])
  with self.assertRaisesRegex(ValueError,"HOLD_BITAN_AGGREGATOR_IDENTITY"):m.vet_parent(p)
 def test_19 only one review source and no production promotion(self):
  v=m.assemble(parent(),m.parse_calendar(CAL),m.parse_news(NEWS))
  self.assertEqual(v["officialFirstPartyIndependentEventIdentityCount"],1)
  self.assertEqual(v["reviewOnlyOfficialEventUrl"],m.CALENDAR)
  self.assertEqual(v["reviewOnlyOfficialEventPeriod"],list(m.PERIOD))
  self.assertEqual(v["finalDatePromotionCount"],0)
  self.assertIsNone(v["dateStart"]);self.assertIsNone(v["dateEnd"])
  self.assertFalse(v["published"]);self.assertFalse(v["goldenAccepted"])
  self.assertTrue(v["strolltimesOriginalFacebookCreditsUnverified"])
  self.assertFalse(v["allOtherAggregatorArticlesVerified"])
 def test_20 incomplete government sources stay hold(self):
  v=m.assemble(parent(),m.parse_calendar(CAL),m.parse_news(""))
  self.assertEqual(v["officialFirstPartyIndependentEventIdentityCount"],0)
  self.assertIsNone(v["reviewOnlyOfficialEventUrl"])
  self.assertEqual(v["officialEventSourceMatchState"],"HOLD_FIRST_PARTY_GOV_SOURCE_INCOMPLETE")
if __name__=="__main__":unittest.main()
