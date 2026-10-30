#!/usr/bin/env python3
"""L9-BQ strict static HTML route diagnostic; never a FIELD PASS."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9bq_huashan_static_route_topology import diagnose, ROUTE
def link(href):return '<a href="'+href+'"><h3>title</h3></a>'
class Cases(unittest.TestCase):
    def test_exact_one_review_only(self):
        r=diagnose(link(ROUTE))
        self.assertEqual(r["decision"],"REVIEW_STATIC_ANCHOR_FOUND_BUT_FIELDS_HOLD")
        self.assertEqual(r["acceptedFields"],0)
        self.assertFalse(r["published"])
    def test_duplicate_holds(self):
        self.assertEqual(diagnose(link(ROUTE)*2)["decision"],"HOLD_DUPLICATE_SELECTED_ANCHORS")
    def test_no_static_anchor(self):
        self.assertEqual(diagnose("<main></main>")["decision"],"HOLD_NO_STATIC_EXHIBITION_ANCHORS")
    def test_other_exhibition_link(self):
        self.assertEqual(diagnose(link("/exhibition/another"))["decision"],"HOLD_SELECTED_ROUTE_ABSENT_FROM_INDEX_ANCHORS")
    def test_route_only_in_script(self):
        self.assertEqual(diagnose("<script>"+ROUTE+"</script>")["decision"],"HOLD_ROUTE_IN_NON_ANCHOR_STATIC_CONTENT")
    def test_query_route_holds(self):
        self.assertEqual(diagnose(link(ROUTE+"?tracking=1"))["decision"],"HOLD_URL_CANONICALIZATION_OR_QUERY")
    def test_foreign_href_no_identity(self):
        self.assertEqual(diagnose(link("https://evil.example/exhibition/fake"))["selectedExactAnchors"],0)
    def test_selected_foreign_holds(self):
        self.assertEqual(diagnose(link(ROUTE),selected="https://evil.example/exhibition/fake")["decision"],"HOLD_UNSAFE_SELECTED_ROUTE")
    def test_never_golden(self):
        self.assertEqual(diagnose(link(ROUTE))["goldenAccepted"],0)
if __name__=="__main__":unittest.main()
