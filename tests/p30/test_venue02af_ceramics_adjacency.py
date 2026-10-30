#!/usr/bin/env python3
"""VENUE-02AF strict adjacent sibling tests; source-derived roles."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02af_ceramics_adjacency import diagnose
TITLE="山彩疊疊-唐榕個展"
def p(label,value):return "<p><span>"+label+"</span><span>"+value+"</span></p>"
D=p("展覽日期：","2026年10月16日至2026年11月15日")
V=p("展覽地點：","b1陶藝長廊")
def page(content,title=TITLE):return "<main><h3>"+title+"</h3><article>"+content+"</article></main>"
class Cases(unittest.TestCase):
    def test_adjacent_review_only(self):
        x=diagnose(page(D+V))
        self.assertEqual(x["decision"],"REVIEW_ADJACENT_SOURCE_LOCAL_ROLES_NO_FIELD_ACCEPTANCE")
        self.assertEqual(x["datePairs"],1)
        self.assertEqual(x["venuePairs"],1)
        self.assertEqual(x["acceptedFields"],0)
    def test_cross_paragraph_not_joined(self):
        self.assertEqual(diagnose(page("<p><span>展覽日期：</span></p><p><span>2026年10月16日至2026年11月15日</span></p>"+V))["decision"],"HOLD_MISSING_OR_NONADJACENT_ROLE_VALUE")
    def test_duplicate_date_holds(self):
        self.assertEqual(diagnose(page(D+D+V))["decision"],"HOLD_DUPLICATE_ROLE_PAIRS")
    def test_invalid_date_holds(self):
        self.assertEqual(diagnose(page(p("展覽日期:","2026年02月30日至2026年11月15日")+V))["decision"],"HOLD_INVALID_ADJACENT_ROLE_VALUE")
    def test_inverted_date_holds(self):
        self.assertEqual(diagnose(page(p("展覽日期:","2026年11月16日至2026年10月15日")+V))["decision"],"HOLD_INVALID_ADJACENT_ROLE_VALUE")
    def test_mixed_sale_holds(self):
        self.assertEqual(diagnose(page(D+p("展覽地點:","售票日期明天")))["decision"],"HOLD_INVALID_ADJACENT_ROLE_VALUE")
    def test_cross_sid_title_holds(self):
        self.assertEqual(diagnose(page(D+V,title="殼之巢"))["decision"],"HOLD_SID_OR_TITLE")
    def test_nonadjacent_nested_holds(self):
        self.assertEqual(diagnose(page("<p><b>展覽日期:</b><span>2026年10月16日至2026年11月15日</span></p>"+V))["decision"],"HOLD_MISSING_OR_NONADJACENT_ROLE_VALUE")
    def test_no_golden(self):
        x=diagnose(page(D+V))
        self.assertEqual(x["goldenAccepted"],0)
        self.assertIsNone(x["ticketEventId"])
        self.assertFalse(x["published"])
if __name__=="__main__":unittest.main()
