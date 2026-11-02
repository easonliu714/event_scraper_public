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

    def test_existing_l7_candidate_pipeline_bridge(self):
        # This is a synthetic integration regression, NOT the Owner's 5-row JSON
        # and NOT a new native GET or formally accepted event field.
        from scripts.p30_candidate_review_pipeline import build_candidate_dataset
        raw = {
            "title": m.TICKET and data["identity"]["title"],
            "url": m.TICKET, "platform": "OPENTIX", "type": "UNKNOWN",
            "scraped_at": "2026-11-02T20:55:00+08:00",
            "location": "臺北表演藝術中心 藍盒子",
            "_candidate": {
                "scope": "CANDIDATE_PREVIEW_ONLY", "decision": "REVIEW_WITH_HOLD",
                "published": False, "golden_accepted": False, "formal_field_pass": False,
                "platform_id": "05", "source_event_id": "2072516129034670080",
                "record_id": "SYNTHETIC_BRIDGE_TEST_ONLY", "sources": [m.TICKET],
                "hold_reasons": ["AGE_DATE_SESSION_PRICE_CONFLICT_HOLD"],
                "field_evidence": {"location": {
                    "value": "臺北表演藝術中心 藍盒子", "source": m.TICKET,
                    "observed_at": "2026-11-02T20:55:00+08:00",
                    "role": "EVENT_VENUE", "decision": "REVIEW"
                }}
            }
        }
        preview, report = build_candidate_dataset([raw])
        self.assertEqual((len(preview), report["formalFieldAccepted"],
                          report["goldenAccepted"], report["published"]), (1, 0, 0, 0))
        self.assertEqual(preview[0]["price"], "未確認")
        self.assertEqual(preview[0]["date"], "未確認")
        self.assertIsNone(preview[0]["img_url"])
        self.assertEqual(preview[0]["_candidate"]["sessions"], [])
        self.assertEqual(m.audit_l7_candidate_parity(data, raw)["decision"], "REVIEW_PARITY_ONLY")
        for key, value in (("title", "另一個節目"), ("url", "https://www.opentix.life/event/999"),
                           ("location", "另一個場館"), ("img_url", m.TICKET_IMAGE)):
            changed = copy.deepcopy(raw); changed[key] = value
            with self.subTest(field=key):
                self.assertEqual(m.audit_l7_candidate_parity(data, changed)["decision"], "HOLD")
        for key, value in (("source_event_id", "999"), ("platform_id", "17"),
                           ("published", True)):
            changed = copy.deepcopy(raw); changed["_candidate"][key] = value
            with self.subTest(meta=key):
                self.assertEqual(m.audit_l7_candidate_parity(data, changed)["decision"], "HOLD")
        for untrusted_sources in ([m.TICKET, m.VENUE], [m.TICKET, m.TICKET], [m.VENUE, m.TICKET]):
            changed = copy.deepcopy(raw)
            changed["_candidate"]["sources"] = untrusted_sources
            with self.subTest(sources=untrusted_sources):
                outcome = m.audit_l7_candidate_parity(data, changed)
                self.assertEqual(outcome["decision"], "HOLD")
                self.assertIn("UNVERIFIED_EXTRA_OR_DUPLICATE_SOURCE", outcome["reasons"])
        changed = copy.deepcopy(raw)
        changed["_candidate"]["field_evidence"]["location"]["source"] = m.VENUE
        self.assertEqual(m.audit_l7_candidate_parity(data, changed)["decision"], "HOLD")
        changed = copy.deepcopy(raw)
        changed["_candidate"]["field_evidence"]["location"]["observed_at"] = "2026-11-02T20:56:00+08:00"
        self.assertEqual(m.audit_l7_candidate_parity(data, changed)["decision"], "HOLD")
        changed = copy.deepcopy(raw)
        changed["price"] = "800"
        self.assertEqual(m.audit_l7_candidate_parity(data, changed)["decision"], "HOLD")
        changed = copy.deepcopy(raw)
        changed["_candidate"]["field_evidence"]["price"] = {
            "value": "1200", "source": m.TICKET, "observed_at": "2026-11-02T20:55:00+08:00",
            "role": "EVENT_ADMISSION_PRICE", "decision": "REVIEW"}
        changed["price"] = "1200"
        self.assertEqual(m.audit_l7_candidate_parity(data, changed)["decision"], "HOLD")


    def test_tmc_kham_source_edge_is_review_not_formal(self):
        receipt=data["tmc_kham_indexed_receipt"]
        self.assertEqual(m.validate_tmc_kham_receipt(receipt),{
            "A_review":4,"B_review":5,"formal_accepted":0,"golden":0,
            "published":0,"native_get":0,"decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"})
        # Source role and value cannot be borrowed across venue and ticket.
        for name,key,bad in (
            ("ticket_sale_open","value","2026-11-07T19:30:00+08:00"),
            ("venue_showtime","value","2026-08-22T12:00:00+08:00"),
            ("venue_advertised_prices","role","EVENT_ADMISSION_ELIGIBLE_MIN"),
            ("venue_advertised_prices","value",[1880]),
            ("ticket_age_recommendation","value",7),
            ("venue_direct_ticket_url","value","https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=OTHER"),
            ("ticket_title","source",m.TMC_DETAIL),
            ("venue_room","observed_at","2026-11-03T00:52:00"),
            ("ticket_one_person_one_ticket","formal_accepted",True),
        ):
            changed=copy.deepcopy(receipt)
            next(f for f in changed["field_receipts"] if f["name"]==name)[key]=bad
            with self.subTest(name=name,key=key):
                with self.assertRaises(ValueError): m.validate_tmc_kham_receipt(changed)
        for key,bad in (("ticket_session_id","invented"),("eligible_general_price",1880),
                        ("image_url","https://example.org/other.jpg")):
            changed=copy.deepcopy(receipt);changed["identity"][key]=bad
            with self.subTest(identity=key):
                with self.assertRaises(ValueError): m.validate_tmc_kham_receipt(changed)
        for key in ("formal_accepted_fields","golden_accepted_events","published_events","native_official_get"):
            changed=copy.deepcopy(receipt);changed[key]=1
            with self.subTest(release=key):
                with self.assertRaises(ValueError): m.validate_tmc_kham_receipt(changed)
        changed=copy.deepcopy(receipt);changed["field_receipts"].append(copy.deepcopy(changed["field_receipts"][0]))
        with self.assertRaises(ValueError):m.validate_tmc_kham_receipt(changed)


if __name__=="__main__":unittest.main()
