"""P30-L7 readiness: source-bound positive AND fail-closed negative acceptance tests."""
import copy,importlib.util,json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
p=ROOT/"scripts/p30_l7_field_golden_readiness.py"
spec=importlib.util.spec_from_file_location("readiness",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
data=json.loads((ROOT/"tests/p30/fixtures/p30_l7_prince_field_readiness.json").read_text(encoding="utf-8"))
def mutate(line,name,key,value):
    d=copy.deepcopy(data)
    for f in d["field_receipts"]:
        if f["line"]==line and f["name"]==name: f[key]=value;break
    return d
class Readiness(unittest.TestCase):
    def test_a_b_review_ready_but_formal_zero(self):
        self.assertEqual(m.validate(data),{"A_review_ready":4,"B_review_ready":5,
            "formal_accepted":0,"golden":0,"published":0,"native_get":0,
            "decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"})
    def test_unverified_price_age_and_images_must_not_promote(self):
        for line,name in (("A","age_min"),("A","admission_price"),
                          ("B","age_min"),("B","advertised_price_range")):
            with self.subTest(line=line,name=name):
                with self.assertRaises(ValueError):m.validate(mutate(line,name,"decision",m.READY))
    def test_official_same_event_image_links_review_only(self):
        for line,name,expected in (("A","img_url",m.TICKET_IMAGE),("B","img_url",m.VENUE_IMAGE)):
            receipt=next(f for f in data["field_receipts"] if (f["line"],f["name"])==(line,name))
            self.assertEqual(receipt["value"],expected)
            self.assertFalse(receipt["formal_accepted"])
            for invalid in (expected+"?size=small",expected.replace("https://","http://"),"https://example.org/fake.jpg",expected.rsplit(".",1)[0]+".png"):
                with self.subTest(line=line,invalid=invalid):
                    with self.assertRaises(ValueError):m.validate(mutate(line,name,"value",invalid))
            with self.assertRaises(ValueError):m.validate(mutate(line,name,"formal_accepted",True))
    def test_false_golden_and_native_claims_rejected(self):
        for k,v in (("formal_accepted_fields",1),("golden_accepted_events",1),
                    ("published_events",1),("native_official_get_this_gate",1),
                    ("reader_is_not_native_get",False),("release_state","RELEASED")):
            with self.subTest(k=k):
                d=copy.deepcopy(data);d[k]=v
                with self.assertRaises(ValueError):m.validate(d)
    def test_exact_event_url_no_cross_event_or_query(self):
        for line,name in (("A","ticket_event_url"),("B","direct_ticket_event_url")):
            for url in (m.TICKET+"?session=1","https://www.opentix.life/event/999",
                        "https://www.opentix.life.evil.example/event/2072516129034670080"):
                with self.subTest(line=line,name=name,url=url):
                    with self.assertRaises(ValueError):m.validate(mutate(line,name,"value",url))
    def test_source_provenance_and_timezone(self):
        for line,name in (("A","title"),("B","showtimes")):
            with self.assertRaises(ValueError):m.validate(mutate(line,name,"source",m.LIST))
            with self.assertRaises(ValueError):m.validate(mutate(line,name,"observed_at","2026-11-02T20:55:00"))
            with self.assertRaises(ValueError):m.validate(mutate(line,name,"formal_accepted",True))
    def test_twelve_venue_showtimes_not_ticket_session_ids(self):
        d=copy.deepcopy(data)
        for f in d["field_receipts"]:
            if (f["line"],f["name"])==("B","showtimes"):
                f["value"]=f["value"][:-1]+[f["value"][0]]
        with self.assertRaises(ValueError):m.validate(d)
        with self.assertRaises(ValueError):m.validate(mutate("A","ticket_session_id","value","123"))
    def test_source_observed_venue_and_exact_showtime_values(self):
        with self.assertRaises(ValueError):m.validate(mutate("A","venue","value","臺北表演藝術中心 大劇院"))
        with self.assertRaises(ValueError):m.validate(mutate("B","venue_room","value","球劇場"))
        d=copy.deepcopy(data)
        for f in d["field_receipts"]:
            if (f["line"],f["name"])==("B","showtimes"):
                f["value"][0]="2026-11-04T19:30:00+08:00"
        with self.assertRaises(ValueError):m.validate(d)
    def test_conflict_must_remain_explicit(self):
        with self.assertRaises(ValueError):m.validate(mutate("B","age_min","value",7))
        with self.assertRaises(ValueError):m.validate(mutate("B","index_advertised_range","value",["2026-11-05","2026-11-15"]))
        with self.assertRaises(ValueError):m.validate(mutate("B","advertised_price_range","value",[600,1200]))
    def test_no_extra_untrusted_field_or_duplicate(self):
        d=copy.deepcopy(data);d["field_receipts"].append(copy.deepcopy(d["field_receipts"][0]))
        with self.assertRaises(ValueError):m.validate(d)
if __name__=="__main__":unittest.main()
