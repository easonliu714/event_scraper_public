"""P30-VENUE-02AY official museum admission versus exhibition tickets."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02ay_yingge_museum_admission.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"standard_url":m.STANDARD,"legacy_url":m.LEGACY,"museum_admission_ntd":80,
      "price_role":"GENERAL_MUSEUM_ENTRY_NOT_EXHIBITION_PRICE",
      "new_taipei_resident_free":True,"students_free":True,"age_65_plus_free":True,"under_12_free":True,"proof_required":True,
      "exhibition_sids":m.EXHIBITIONS,"exhibition_price_role":"UNKNOWN_NOT_DERIVED_FROM_MUSEUM_ADMISSION",
      "legacy_retired_civil_servant_listed":True,"newer_standard_retired_civil_servant_listed":False,
      "conflict_decision":"HOLD_OLDER_ONLY_CATEGORY_NO_AUTOMATIC_ELIGIBILITY",
      "exhibition_ticket_price":None,"exhibition_ticket_url":None,"ticket_session_id":None,"inventory":None,"assumed_legacy_eligibility":None}
class Gate(unittest.TestCase):
    def check(self,k=None,v=None):
        x=fixture()
        if k is not None:x[k]=v
        return m.inspect(x,"2026-11-01")
    def reject(self,d,k,v):
        z=self.check(k,v);self.assertEqual(z["decision"],d);self.assertEqual(z["acceptedFields"],0);self.assertFalse(z["published"])
    def test_exact(self):
        z=self.check();self.assertEqual(z["decision"],"HOLD_MUSEUM_ADMISSION_NOT_EXHIBITION_TICKET");self.assertEqual(len(z["provenance"]),2)
    def test_date(self):self.assertEqual(m.inspect(fixture(),"bad")["decision"],"HOLD_OBSERVATION")
    def test_standard(self):self.reject("HOLD_OFFICIAL_DOCUMENTS","standard_url","https://evil.example")
    def test_legacy(self):self.reject("HOLD_OFFICIAL_DOCUMENTS","legacy_url","https://evil.example")
    def test_fee(self):self.reject("HOLD_MUSEUM_ADMISSION_ROLE","museum_admission_ntd",0)
    def test_fee_role(self):self.reject("HOLD_MUSEUM_ADMISSION_ROLE","price_role","EXHIBITION_PRICE")
    def test_resident(self):self.reject("HOLD_ELIGIBILITY_ROLE","new_taipei_resident_free",False)
    def test_student(self):self.reject("HOLD_ELIGIBILITY_ROLE","students_free",False)
    def test_proof(self):self.reject("HOLD_ELIGIBILITY_ROLE","proof_required",False)
    def test_sids(self):self.reject("HOLD_EXHIBITION_PRICE_SCOPE","exhibition_sids",(m.EXHIBITIONS[0],))
    def test_scope(self):self.reject("HOLD_EXHIBITION_PRICE_SCOPE","exhibition_price_role","EACH_EXHIBITION_80")
    def test_legacy(self):self.reject("HOLD_DOCUMENT_VERSION_CONFLICT","conflict_decision","FREE_FOR_ALL")
    def test_older_category(self):self.reject("HOLD_DOCUMENT_VERSION_CONFLICT","newer_standard_retired_civil_servant_listed",True)
    def test_exhibition_fee(self):self.reject("HOLD_UNVERIFIED_EXHIBITION_TICKET","exhibition_ticket_price",80)
    def test_exhibition_url(self):self.reject("HOLD_UNVERIFIED_EXHIBITION_TICKET","exhibition_ticket_url","https://example.com")
    def test_session(self):self.reject("HOLD_UNVERIFIED_EXHIBITION_TICKET","ticket_session_id","invented")
    def test_inventory(self):self.reject("HOLD_UNVERIFIED_EXHIBITION_TICKET","inventory",20)
if __name__=="__main__":unittest.main()
