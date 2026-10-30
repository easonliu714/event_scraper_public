#!/usr/bin/env python3
"""L9-BC source identity safety tests, no network."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9bc_tixfun_identity import safe_product,list_identity,detail_identity,PRODUCT

class Cases(unittest.TestCase):
    def test_source_derived_exact_id(self):
        u=f"https://tixfun.com/UTK0201_?PRODUCT_ID={PRODUCT}"
        self.assertEqual(safe_product(u),u)
    def test_wrong_product_refused(self):
        self.assertIsNone(safe_product("/UTK0201_?PRODUCT_ID=WRONG"))
    def test_http_refused(self):
        self.assertIsNone(safe_product("http://tixfun.com/UTK0201_?PRODUCT_ID="+PRODUCT))
    def test_external_refused(self):
        self.assertIsNone(safe_product("https://elsewhere.example/UTK0201_?PRODUCT_ID="+PRODUCT))
    def test_userinfo_refused(self):
        self.assertIsNone(safe_product("https://u:p@tixfun.com/UTK0201_?PRODUCT_ID="+PRODUCT))
    def test_nondefault_port_refused(self):
        self.assertIsNone(safe_product("https://tixfun.com:8443/UTK0201_?PRODUCT_ID="+PRODUCT))
    def test_duplicate_id_query_refused(self):
        self.assertIsNone(safe_product("/UTK0201_?PRODUCT_ID="+PRODUCT+"&PRODUCT_ID=OTHER"))
    def test_unique_list_candidate_review(self):
        u,m=list_identity(f'<a href="/UTK0201_?PRODUCT_ID={PRODUCT}">灣聲映像館VIII 音樂會</a>')
        self.assertIsNotNone(u)
        self.assertEqual(m["decision"],"REVIEW_ONE_LIST_PRODUCT_LINK")
    def test_conflicting_paths_hold(self):
        h=(f'<a href="/UTK0201_?PRODUCT_ID={PRODUCT}">灣聲映像館VIII</a>'
           f'<a href="/UTK0201_?PRODUCT_ID={PRODUCT}&mode=other">灣聲映像館VIII</a>')
        self.assertIsNone(list_identity(h)[0])
    def test_detail_heading_review_only(self):
        x=detail_identity("<h1>灣聲映像館VIII：音樂會</h1>")
        self.assertEqual(x["decision"],"REVIEW_SAME_PRODUCT_TITLE_HEADING_NO_FIELDS")
    def test_detail_missing_heading_hold(self):
        self.assertEqual(detail_identity("<div>灣聲映像館VIII</div>")["decision"],"HOLD_DETAIL_TITLE_NOT_UNIQUE_OR_ABSENT")
    def test_duplicate_headings_hold(self):
        self.assertEqual(detail_identity("<h1>灣聲映像館VIII</h1><h2>灣聲映像館VIII</h2>")["decision"],"HOLD_DETAIL_TITLE_NOT_UNIQUE_OR_ABSENT")

if __name__=="__main__":unittest.main()
