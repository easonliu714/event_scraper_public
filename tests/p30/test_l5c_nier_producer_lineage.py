"""P30-L5-C NieR independent producer-vendor-secondary lineage negatives."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

path=Path(__file__).resolve().parents[2]/"scripts"/"p30_l5c_nier_producer_lineage.py"
spec=importlib.util.spec_from_file_location("p30_l5c",path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PARENT={
 "kind":m.PARENT_KIND,"sourceCount":2,"sourceRuntime":"DORMANT",
 "published":False,"goldenAccepted":False,"organiserConfirmationCount":0,
 "formalDatePromotionCount":0,
 "details":[
   {"listTitle":"RUNIDRE","officialUrl":"https://ticket.ibon.com.tw/ActivityInfo/Details/40010",
    "httpStatus":200,"scheduleParity":"EXACT_SAMPLED_EVENT_STARTS",
    "currentSampleEventStarts":["2026-12-19T17:00"],
    "notice":{"isNoChangesProven":False},"organiserChangeApproval":"NOT_VERIFIED"},
   {"listTitle":"NieR：Orchestra Concert 12026［YoRHa］",
    "officialUrl":"https://ticket.ibon.com.tw/ActivityInfo/Details/39974",
    "httpStatus":200,"scheduleParity":"EXACT_SAMPLED_EVENT_STARTS",
    "currentSampleEventStarts":["2027-02-20T18:00","2027-02-21T14:00"],
    "notice":{"isNoChangesProven":False},"organiserChangeApproval":"NOT_VERIFIED"}]}
TOUR=("Feb 20 Taipei, Taiwan Saturday, February 20, 2027 "
      "6:00 PM 8:30 PM Taipei International Convention Center On Sale Now "
      "Feb 21 Taipei, Taiwan Sunday, February 21, 2027 "
      "2:00 PM 4:30 PM Taipei International Convention Center On Sale Now "
      "NieR:Orchestra Concert 12026 [ YoRHa ] is produced by AWR Music Productions and Square Enix")
DETAIL=("Taipei, Taiwan Sunday, February 21, 2027 "
 "2:00 PM 4:30 PM Taipei International Convention Center "
 "AWR Music Productions and SQUARE ENIX are proud to present NieR:Orchestra Concert 12026 [ YoRHa ] "
 "On Sale Oct. 21, 9 AM (UTC+8)")
SECONDARY=("我們是台灣最好用的二手門票交易平台。"
 "演出時間 ⎪ 2027/02/20（六）18:00 2027/02/21（日）14:00 #加場 "
 "售票時間 ⎪ 2026/10/13（二）12:00 "
 "加場售票時間 ⎪ 2026/10/21（三）12:00")
class Checks(unittest.TestCase):
 def test_01_url_exact_only(self):
  self.assertTrue(all(m.allow_url(x) for x in m.KNOWN))
  for x in ["http://www.nierconcert.com/12026",
   "https://www.nierconcert.com.evil.com/12026",
   "https://www.nierconcert.com/12026?token=x",
   "https://www.nierconcert.com/login",
   "https://itix2go.com/guest/order"]:
   self.assertFalse(m.allow_url(x))
 def test_02_parent_proof_strict(self):
  p=m.vet_parent(PARENT)
  self.assertEqual(p["officialUrl"],"https://ticket.ibon.com.tw/ActivityInfo/Details/39974")
 def test_03_producer_dates_near_taipei(self):
  data=m.producer_schedule(TOUR)
  self.assertEqual(sorted(data),sorted(m.EXPECTED))
  self.assertEqual(data["2027-02-21T14:00"]["identity"],"CITY_DAY_TIME_VENUE_BOUND")
 def test_04_bangkok_venue_ticc_cannot_impersonate_taipei(self):
  bad="Bangkok, Thailand Saturday, February 20, 2027 6:00 PM "+m.VENUE
  self.assertEqual(m.producer_schedule(bad),{})
 def test_05_just_city_without_time_or_venue_is_invalid(self):
  self.assertEqual(m.producer_schedule("Taipei, Taiwan Saturday, February 20, 2027 "+m.VENUE),{})
 def test_06_producer_detail_bound_to_date_and_title(self):
  val=m.producer_added_event(DETAIL)
  self.assertEqual(val["detailIdentity"],"ADDED_TAIPEI_EVENT_DETAIL_MATCH")
  self.assertEqual(val["eventStartLocal"],"2027-02-21T14:00")
 def test_07_seller_sale_not_announcement_published_at(self):
  val=m.producer_added_event(DETAIL)
  self.assertEqual(val["producerAddedShowSaleTime"],"2026-10-21T09:00+08:00")
  self.assertIsNone(val["announcementPublishedAt"])
  self.assertFalse(val["announcementPublishTimeVerified"])
 def test_08_secondary_is_ticket_resale_listing(self):
  val=m.secondary_sale(SECONDARY)
  self.assertEqual(val["sourceRole"],"THIRD_PARTY_TICKET_RESALE_LISTING")
  self.assertEqual(val["addedShowSaleTime"],"2026-10-21T12:00")
  self.assertTrue(val["notOriginalOrganiser"])
 def test_09_sale_conflict_not_event_time_conflict(self):
  x=m.reconcile(PARENT,m.producer_schedule(TOUR),m.producer_added_event(DETAIL),
                m.secondary_sale(SECONDARY))
  self.assertEqual(x["status"],"PRODUCER_TWO_TAIPEI_SESSIONS_CORROBORATED_REVIEW_ONLY")
  self.assertEqual(x["ticketSaleEvidence"]["saleTimeConflict"],"SECONDARY_DISAGREEMENT_HOLD")
  self.assertEqual(x["producerOriginalTwoStartsSame"],True)
 def test_10_missing_reseller_information_no_fabricated_conflict(self):
  x=m.reconcile(PARENT,m.producer_schedule(TOUR),m.producer_added_event(DETAIL),
                m.secondary_sale(""))
  self.assertEqual(x["ticketSaleEvidence"]["saleTimeConflict"],"NO_COMPARABLE_SALE_TIMES_OBSERVED")
 def test_11_missing_original_detail_page_hold(self):
  x=m.reconcile(PARENT,m.producer_schedule(TOUR),m.producer_added_event(""),m.secondary_sale(SECONDARY))
  self.assertEqual(x["status"],"HOLD_PRODUCER_SCHEDULE_PARITY_OR_DETAIL_IDENTITY")
 def test_12_wrong_producer_start_not_matched(self):
  bad=TOUR.replace("6:00 PM 8:30 PM","7:00 PM 9:30 PM")
  x=m.reconcile(PARENT,m.producer_schedule(bad),m.producer_added_event(DETAIL),m.secondary_sale(SECONDARY))
  self.assertEqual(x["status"],"HOLD_PRODUCER_SCHEDULE_PARITY_OR_DETAIL_IDENTITY")
 def test_13_no_golden_promotion_or_organiser_publish_claim(self):
  x=m.reconcile(PARENT,m.producer_schedule(TOUR),m.producer_added_event(DETAIL),m.secondary_sale(SECONDARY))
  self.assertIsNone(x["announcementPublicationTimestamp"])
  self.assertFalse(x["announcementTimestampVerified"])
  self.assertFalse(x["additionalShowAnnouncementIndependentlyVerified"])
  self.assertFalse(x["ticketSaleEvidence"]["salesTimeOfficiallyApproved"])
  self.assertEqual(x["organiserConfirmationStatus"],"OFFICIAL_TOUR_SCHEDULE_CORROBORATED_ANNOUNCEMENT_TIMESTAMP_HOLD")
  self.assertFalse(x["goldenAccepted"]);self.assertFalse(x["published"])
  self.assertEqual(x["formalFieldPromotionCount"],0);self.assertEqual(x["acceptedEventCount"],0)
  self.assertEqual(x["ticketStatus"],"UNKNOWN")
 def test_14_forged_parent_golden_writer_flags(self):
  for key,value in [("goldenAccepted",True),("published",True),
                   ("organiserConfirmationCount",1),("formalDatePromotionCount",2),
                   ("sourceRuntime","ACTIVE")]:
   p={**PARENT,key:value}
   with self.assertRaisesRegex(ValueError,"HOLD_PARENT_GOVERNANCE"):m.vet_parent(p)
 def test_15_parent_foreign_NIER_ID_invalid(self):
  import copy
  p=copy.deepcopy(PARENT);p["details"][1]["officialUrl"]="https://ticket.ibon.com.tw/ActivityInfo/Details/12345"
  with self.assertRaisesRegex(ValueError,"HOLD_NOT_PINNED_NIER_OFFICIAL_URL"):m.vet_parent(p)
 def test_16_wrong_title_source_or_missing_session(self):
  import copy
  p=copy.deepcopy(PARENT)
  p["details"][1]["currentSampleEventStarts"]=["2027-02-21T14:00"]
  with self.assertRaisesRegex(ValueError,"HOLD_PARENT_NIER_TWO_EVENT_TIMES_MISMATCH"):m.vet_parent(p)
 def test_17_no_change_not_proven(self):
  import copy
  p=copy.deepcopy(PARENT)
  p["details"][1]["notice"]["isNoChangesProven"]=True
  with self.assertRaisesRegex(ValueError,"HOLD_PRIOR_NOTICE_NOT_FAIL_CLOSED"):m.vet_parent(p)
 def test_18_annotation_role_secondary_remains_secondary(self):
  a=m.secondary_sale(SECONDARY)
  self.assertIsNone(a["publisherTimestamp"])
  self.assertFalse(a["publisherTimestampVerified"])
 def test_19_no_mainstream_event_year_inferred_from_sales_date(self):
  result=m.producer_schedule("Taipei, Taiwan On Sale Oct. 21, 9 AM (UTC+8)")
  self.assertFalse(result)
 def test_20_inbound_missing_NIER_prevents_claim(self):
  import copy
  p=copy.deepcopy(PARENT);p["details"][1]["listTitle"]="Another concert"
  with self.assertRaisesRegex(ValueError,"HOLD_NIER_IDENTITY_NOT_UNIQUE"):m.vet_parent(p)
if __name__=="__main__":unittest.main()
