#!/usr/bin/env python3
"""VENUE-02AH source-observed metadata date roles are never event sessions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from p30_venue02ah_ceramics_date_role_boundary import inspect_metadata,inspect_pair
from test_venue02ag_ceramics_two_sid_roles import samples
def records():
    a,b=samples()
    a.update(articleUpdatedText="更新日期：2026-10-15 瀏覽人次：1835",
             siteUpdatedText="內容更新 ：2026-10-30")
    b.update(articleUpdatedText="更新日期：2026-10-12 瀏覽人次：1526",
             siteUpdatedText="內容更新 ：2026-10-30")
    return a,b
class Cases(unittest.TestCase):
    def test_two_official_sids_separate_update_and_exhibition(self):
        a,b=records();x=inspect_pair([a,b])
        self.assertEqual(x["decision"],"REVIEW_TWO_SIDS_UPDATE_DATES_NOT_EVENT_SESSIONS")
        self.assertEqual([y["candidateRoleCount"] for y in x["records"]],[4,4])
        self.assertEqual(x["acceptedFields"],0)
    def test_update_role_never_session(self):
        a,_=records();x=inspect_metadata(a,a["articleUpdatedText"],a["siteUpdatedText"])
        self.assertEqual(x["decision"],"REVIEW_DISTINCT_EXHIBITION_VS_UPDATE_ROLES_NO_FORMAL_FIELDS")
        self.assertFalse(x["sessionAccepted"])
        self.assertEqual([e["role"] for e in x["candidateProvenance"]][-2:],
                         ["ARTICLE_UPDATED_AT","SITE_CONTENT_UPDATED_AT"])
        self.assertEqual(x["acceptedFields"],0)
    def test_missing_article_label_refused(self):
        a,_=records()
        self.assertEqual(inspect_metadata(a,"2026-10-15",a["siteUpdatedText"])["decision"],
                         "HOLD_METADATA_ROLE_LABEL_OR_AMBIGUITY")
    def test_exhibition_date_masquerading_as_article_update_refused(self):
        a,_=records()
        self.assertEqual(inspect_metadata(a,"展覽日期：2026年10月16日",a["siteUpdatedText"])["decision"],
                         "HOLD_METADATA_ROLE_LABEL_OR_AMBIGUITY")
    def test_site_footer_label_not_article_date(self):
        a,_=records()
        self.assertEqual(inspect_metadata(a,a["articleUpdatedText"],"展覽日期：2026-10-30")["decision"],
                         "HOLD_METADATA_ROLE_LABEL_OR_AMBIGUITY")
    def test_future_article_update_refused(self):
        a,_=records()
        self.assertEqual(inspect_metadata(a,"更新日期：2027-10-15 瀏覽人次：1835",a["siteUpdatedText"])["decision"],
                         "HOLD_METADATA_AFTER_OBSERVATION")
    def test_invalid_calendar_date_refused(self):
        a,_=records()
        self.assertEqual(inspect_metadata(a,"更新日期：2026-02-30 瀏覽人次：1835",a["siteUpdatedText"])["decision"],
                         "HOLD_METADATA_INVALID_DATE")
    def test_cross_sid_title_refused(self):
        a,b=records();a["title"]=b["title"]
        self.assertEqual(inspect_metadata(a,a["articleUpdatedText"],a["siteUpdatedText"])["decision"],
                         "HOLD_EXHIBITION_ROLE_OR_IDENTITY")
    def test_duplicate_sid_refused(self):
        a,_=records()
        self.assertEqual(inspect_pair([a,a])["decision"],"HOLD_CROSS_SID_OR_DUPLICATE")
    def test_missing_source_date_refused(self):
        a,_=records();a["html"]=a["html"].replace("展覽日期","售票日期")
        self.assertEqual(inspect_metadata(a,a["articleUpdatedText"],a["siteUpdatedText"])["decision"],
                         "HOLD_EXHIBITION_ROLE_OR_IDENTITY")
    def test_no_publication_even_with_review(self):
        a,b=records();x=inspect_pair([a,b])
        self.assertEqual(x["goldenAccepted"],0)
        self.assertFalse(x["published"])
if __name__=="__main__":
    unittest.main()
