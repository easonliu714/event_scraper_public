#!/usr/bin/env python3
"""L9-BR route discrepancy regression, source-derived shapes, fail-closed."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9br_huashan_route_reason import diagnose, ROUTE
def link(url): return '<a href="'+url+'"><h3>title</h3></a>'
class Cases(unittest.TestCase):
    def test_exact_review_not_field(self):
        x=diagnose(link(ROUTE))
        self.assertEqual(x["decision"],"REVIEW_EXACT_ROUTE_ONLY_NO_FIELDS")
        self.assertEqual(x["acceptedFields"],0)
    def test_query_is_not_identity(self):
        x=diagnose(link(ROUTE+"?utm_source=official"))
        self.assertEqual(x["decision"],"HOLD_ROUTE_VARIANT_REQUIRES_SOURCE_IDENTITY")
        self.assertEqual(x["reasonCounts"]["QUERY_OR_FRAGMENT_NOT_IDENTITY"],1)
    def test_fragment_is_not_identity(self):
        self.assertEqual(diagnose(link(ROUTE+"#event"))["decision"],"HOLD_ROUTE_VARIANT_REQUIRES_SOURCE_IDENTITY")
    def test_percent_encoding_variant_not_silently_accepted(self):
        x=diagnose(link(ROUTE.replace("%E6","%e6")))
        self.assertEqual(x["decision"],"HOLD_ROUTE_VARIANT_REQUIRES_SOURCE_IDENTITY")
    def test_duplicate_same_path_refused(self):
        self.assertEqual(diagnose(link(ROUTE)+link(ROUTE+"?x=1"))["decision"],"HOLD_DUPLICATE_OR_CONFLICTING_ROUTE")
    def test_foreign_origin_refused(self):
        self.assertEqual(diagnose(link("https://evil.example"+ROUTE))["strictMatches"],0)
    def test_no_anchor(self):
        self.assertEqual(diagnose("<main/>")["decision"],"HOLD_ROUTE_NOT_PRESENT")
    def test_no_publication(self):
        x=diagnose(link(ROUTE))
        self.assertEqual(x["goldenAccepted"],0)
        self.assertFalse(x["published"])
        self.assertIsNone(x["ticketEventId"])
if __name__=="__main__": unittest.main()
