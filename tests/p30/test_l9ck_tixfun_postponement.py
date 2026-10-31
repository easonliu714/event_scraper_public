"""Source-observed TixFun list-to-detail and reschedule negative tests (offline, no requests)."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9ck_tixfun_postponement.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"list_url":m.LIST_URL,"list_title":m.LIST_TITLE,"detail_url":m.DETAIL_URL,"product_id":m.PRODUCT_ID,
     "detail_title":m.TITLE,"header_range":m.HEADER,"price_band":(800,3200),
     "original":m.ORIGINAL,"postponed":m.POSTPONED,"change_role":"ONE_CHIAYI_SHOW_RESCHEDULE_NOT_ALL_SHOWS",
     "refund_exception_cutoff":"2026-09-05","refund_exception_role":"PAST_RESCHEDULE_EXCEPTION_NOT_CURRENT_POLICY",
     "general_refund_days":10,"general_refund_fee_percent":10,"general_refund_role":"RELATIVE_POLICY_NOT_ABSOLUTE",
     "show_duration_minutes":160,"intermission_minutes":15,"duration_role":"DESCRIPTION_NOT_TICKET_SESSION",
     "ticket_session_id":None,"inventory":None,"session_price":None,"computed_refund_deadline":None}
class Gate(unittest.TestCase):
    def check(self,k=None,v=None):
        x=fixture()
        if k is not None:x[k]=v
        return m.inspect(x,"2026-11-01")
    def reject(self,decision,k,v):
        r=self.check(k,v);self.assertEqual(r["decision"],decision);self.assertEqual(r["acceptedFields"],0);self.assertFalse(r["published"])
    def test_exact_list_detail(self):
        r=self.check();self.assertEqual(r["decision"],"HOLD_PRODUCT_DETAIL_SOURCE_BOUND_NO_SESSION_ID");self.assertEqual(len(r["provenance"]),3)
    def test_bad_date(self):self.assertEqual(m.inspect(fixture(),"bad")["decision"],"HOLD_OBSERVATION")
    def test_list_title(self):self.reject("HOLD_LIST_IDENTITY","list_title","similar")
    def test_list_url(self):self.reject("HOLD_LIST_IDENTITY","list_url","https://evil.example")
    def test_product_id(self):self.reject("HOLD_PRODUCT_ID","product_id","QFAKE")
    def test_product_url(self):self.reject("HOLD_PRODUCT_ID","detail_url",m.DETAIL_URL+"&other=1")
    def test_detail_title(self):self.reject("HOLD_DETAIL_PARITY","detail_title","different")
    def test_header_not_single_show(self):self.reject("HOLD_DETAIL_PARITY","header_range",("2027-03-06","2027-03-06"))
    def test_price_band(self):self.reject("HOLD_DETAIL_PARITY","price_band",(800,800))
    def test_original_date(self):self.reject("HOLD_POSTPONEMENT_SCOPE","original",("2026-11-06","14:30",m.ORIGINAL[2]))
    def test_postponement_not_all(self):self.reject("HOLD_POSTPONEMENT_SCOPE","change_role","ALL_SHOWS")
    def test_refund_exception(self):self.reject("HOLD_REFUND_EXCEPTION_ROLE","refund_exception_cutoff","2027-02-24")
    def test_refund_scope(self):self.reject("HOLD_REFUND_EXCEPTION_ROLE","refund_exception_role","CURRENT_POLICY")
    def test_general_refund(self):self.reject("HOLD_GENERAL_REFUND_ROLE","general_refund_days",0)
    def test_duration(self):self.reject("HOLD_DURATION_ROLE","duration_role","SESSION")
    def test_session_id(self):self.reject("HOLD_UNVERIFIED_SESSION_FIELDS","ticket_session_id","invented")
    def test_inventory(self):self.reject("HOLD_UNVERIFIED_SESSION_FIELDS","inventory",5)
    def test_price(self):self.reject("HOLD_UNVERIFIED_SESSION_FIELDS","session_price",800)
if __name__=="__main__":unittest.main()
