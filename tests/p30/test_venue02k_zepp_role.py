#!/usr/bin/env python3
"""P30-VENUE-02K strict OPEN/START/ticket URL refusal regressions."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02k_zepp_role import inspect
from p30_venue02j_zepp_newtaipei import DETAIL

L = f'<a href="{DETAIL}">2026 10.30 40 Fingers START 19:30 READ MORE</a>'
D = ('<h2>FORTY FINGERS ASIAN TOUR 2026</h2><h3>40 Fingers</h3>'
     '<p>[OPEN] 18:30</p><p>[START] 19:30</p><p>チケット販売 KKTIX</p>')

class Cases(unittest.TestCase):
    def check(self, listing, detail, decision):
        x = inspect(listing, detail, "2026-10-30T01:55:00Z")
        self.assertEqual(x["decision"], decision)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
        self.assertIsNone(x["ticketEventId"])
        self.assertEqual(x["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        return x
    def test_review_without_ticket_url(self):
        x = self.check(L, D, "REVIEW_ZEPP_LOCAL_OPEN_START_TICKET_BOUNDARY_NO_FIELDS")
        self.assertEqual(x["roleProvenance"]["TICKET"]["decision"], "HOLD_PLATFORM_NAME_WITHOUT_VERIFIED_TICKET_URL")
    def test_review_with_exact_external_link(self):
        x = self.check(L, D + '<a href="https://example.kktix.com/events/example">Tickets</a>',
                       "REVIEW_ZEPP_LOCAL_OPEN_START_TICKET_BOUNDARY_NO_FIELDS")
        self.assertEqual(x["externalTicketLinksReview"], 1)
        self.assertEqual(x["roleProvenance"]["TICKET"]["decision"], "REVIEW_EXTERNAL_LINK_NOT_VERIFIED_TICKET_EVENT_ID")
    def test_missing_open(self):
        self.check(L, D.replace("[OPEN]", "DOORS"), "HOLD_OPEN_LOCAL_TIME_AMBIGUOUS")
    def test_duplicate_open(self):
        self.check(L, D + "<p>[OPEN] 18:30</p>", "HOLD_OPEN_LOCAL_TIME_AMBIGUOUS")
    def test_open_missing_time(self):
        self.check(L, D.replace("18:30", "TBA"), "HOLD_OPEN_LOCAL_TIME_AMBIGUOUS")
    def test_start_two_times(self):
        self.check(L, D.replace("[START] 19:30", "[START] 19:30 20:30"), "HOLD_START_LOCAL_TIME_AMBIGUOUS")
    def test_same_node_unscoped(self):
        self.check(L, D.replace("<p>[OPEN] 18:30</p><p>[START] 19:30</p>",
                                "<p>[OPEN] [START] 19:30</p>"), "HOLD_OPEN_START_SAME_UNSCOPED_NODE")
    def test_duplicate_external_ticket_urls(self):
        self.check(L, D + '<a href="https://a.kktix.com/events/a">A</a><a href="https://b.kktix.com/events/b">B</a>',
                   "HOLD_MULTIPLE_EXTERNAL_TICKET_LINKS")
    def test_lookalike_domain_not_verified(self):
        x = self.check(L, D + '<a href="https://notkktix.com/events/x">Fake</a>',
                       "REVIEW_ZEPP_LOCAL_OPEN_START_TICKET_BOUNDARY_NO_FIELDS")
        self.assertEqual(x["externalTicketLinksReview"], 0)
    def test_prior_identity_fail(self):
        self.check(L.replace("162473", "999999"), D, "HOLD_PRIOR_SAME_RID_IDENTITY")

if __name__ == "__main__":
    unittest.main()
