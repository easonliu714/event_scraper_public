"""P30-L9-DH source-bound OPENTIX sale and discount negative gates."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9dh_opentix_sale_roles.py"
spec=importlib.util.spec_from_file_location("l9dh",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
NOW="2026-11-02T10:50:00Z"
def sample():
    return {"ticket_event_url":m.EVENT,"title":m.TITLE,"venue":m.VENUE,"age_min":7,
            "sale_markers_unbound":list(m.MARKERS),"sale_year_explicit":False,
            "conditional_discounts":[{"name":n,"percent":p} for n,p in m.DISCOUNTS],
            "session_picker_heading":"選擇場次","reader_session_rows_exposed":False,
            "change_notice_city":"嘉義市","change_notice_show_date":"2026-11-01"}
class Gate(unittest.TestCase):
    def test_six_review_receipts_no_formal_acceptance(self):
        x=m.inspect(sample(),NOW)
        self.assertEqual(x["decision"],"REVIEW_OPENTIX_SALE_DISCOUNT_SESSION_HOLD")
        self.assertEqual(len(x["candidateFields"]),6)
        self.assertEqual({f["source"] for f in x["candidateFields"]},{m.EVENT})
        self.assertEqual({f["decision"] for f in x["candidateFields"]},{"REVIEW"})
        self.assertEqual((x["acceptedFields"],x["ticketSessionIdsVerified"],x["goldenAccepted"],x["published"]),(0,0,0,False))
    def test_exact_url_and_title(self):
        for k,v in (("ticket_event_url",m.EVENT+"?ticket=1"),("ticket_event_url","https://www.opentix.life.evil.example/event/2072516129034670080"),("title","小王子"),("venue","其他場館"),("age_min",6)):
            with self.subTest(k=k):
                a=sample();a[k]=v;self.assertEqual(m.inspect(a,NOW)["candidateFields"],[])
    def test_sale_marker_year_must_not_be_inferred(self):
        for k,v in (("sale_markers_unbound",list(m.MARKERS[:-1])),("sale_markers_unbound",list(reversed(m.MARKERS))),("sale_year_explicit",True),("sale_year_explicit",None)):
            a=sample();a[k]=v;self.assertEqual(m.inspect(a,NOW)["decision"],"HOLD_SALE_MARKER_YEAR_OR_BINDING")
    def test_discount_eligibility_and_reader_scope(self):
        for k,v in (("conditional_discounts",[]),("conditional_discounts",[{"name":"C+會員","percent":85}]),("session_picker_heading","立即結帳"),("reader_session_rows_exposed",True),("reader_session_rows_exposed",None)):
            a=sample();a[k]=v;self.assertEqual(m.inspect(a,NOW)["candidateFields"],[])
    def test_notice_scope_and_unproven_claims(self):
        for k,v in (("change_notice_city","臺北市"),("change_notice_show_date","2026-11-05")):
            a=sample();a[k]=v;self.assertEqual(m.inspect(a,NOW)["decision"],"HOLD_NOTICE_NOT_TAIPEI_SHOW")
        for k,v in (("sale_year",2026),("sale_marker_discount_mapping",{}),("ticket_session_ids",[]),("checkout_url",m.EVENT),("inventory",0),("ticket_base_price",1200),("formal_min_price",1200),("golden_accepted",False)):
            a=sample();a[k]=v;self.assertEqual(m.inspect(a,NOW)["decision"],"HOLD_UNPROVEN_TICKET_CLAIM")
    def test_timestamp_required(self):
        for when in ("invalid","2026-11-02T18:50:00",None):
            self.assertEqual(m.inspect(sample(),when)["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":unittest.main()
