"""P30-L9-CL official-source conditional discount strict offline tests."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9cl_tixfun_conditional_discount.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"source_url":m.SOURCE,"product_id":m.PRODUCT,"product_price_band":(800,3200),
      "price_role":"PRODUCT_RANGE_NOT_SESSION_PRICE","eligible_face_value":1800,"conditional_offer":300,
      "offer_role":m.ROLE,"eligibility":"CULTURE_COIN_YOUTH_SEAT",
      "discount_88_role":"KEELUNG_RESIDENT_OR_CITY_EMPLOYEE_CONDITIONAL",
      "ticket_session_id":None,"ticket_inventory":None,"ticket_session_price":None,"universal_discount":None,"purchase_url":None}
class Gate(unittest.TestCase):
    def check(self,key=None,value=None):
        x=fixture()
        if key is not None:x[key]=value
        return m.inspect(x,"2026-11-01")
    def reject(self,decision,key,value):
        x=self.check(key,value);self.assertEqual(x["decision"],decision);self.assertEqual(x["acceptedFields"],0);self.assertFalse(x["published"])
    def test_exact(self):
        x=self.check();self.assertEqual(x["decision"],"HOLD_CONDITIONAL_DISCOUNT_NOT_TICKET_SESSION");self.assertEqual(len(x["provenance"]),3)
    def test_observation(self):self.assertEqual(m.inspect(fixture(),"invalid")["decision"],"HOLD_OBSERVATION")
    def test_source(self):self.reject("HOLD_SOURCE_PRODUCT","source_url","https://evil.example")
    def test_product(self):self.reject("HOLD_SOURCE_PRODUCT","product_id","fake")
    def test_price_band(self):self.reject("HOLD_PRODUCT_BAND_ROLE","product_price_band",(300,300))
    def test_price_role(self):self.reject("HOLD_PRODUCT_BAND_ROLE","price_role","SESSION")
    def test_face_value(self):self.reject("HOLD_CONDITIONAL_OFFER_ROLE","eligible_face_value",800)
    def test_offer(self):self.reject("HOLD_CONDITIONAL_OFFER_ROLE","conditional_offer",800)
    def test_offer_role(self):self.reject("HOLD_CONDITIONAL_OFFER_ROLE","offer_role","GENERAL_PRICE")
    def test_eligibility(self):self.reject("HOLD_ELIGIBILITY_SCOPE","eligibility","ALL_CUSTOMERS")
    def test_keelung(self):self.reject("HOLD_ELIGIBILITY_SCOPE","discount_88_role","UNIVERSAL")
    def test_session_id(self):self.reject("HOLD_UNVERIFIED_TICKET_PROMOTION","ticket_session_id","fake")
    def test_inventory(self):self.reject("HOLD_UNVERIFIED_TICKET_PROMOTION","ticket_inventory",20)
    def test_session_price(self):self.reject("HOLD_UNVERIFIED_TICKET_PROMOTION","ticket_session_price",300)
    def test_universal(self):self.reject("HOLD_UNVERIFIED_TICKET_PROMOTION","universal_discount",300)
    def test_purchase(self):self.reject("HOLD_UNVERIFIED_TICKET_PROMOTION","purchase_url","https://example.com")
if __name__=="__main__":unittest.main()
