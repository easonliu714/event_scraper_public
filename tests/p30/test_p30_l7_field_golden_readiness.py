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
            "A_review":5,"B_review":5,"B_rejected_as_poster":1,"formal_accepted":0,"golden":0,
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


    def test_kham_tmc_image_provenance_and_seat_map_rejection(self):
        # Official product poster is a source-bound REVIEW image; TMC's
        # seating diagram must never be promoted to a generic event poster.
        receipt=data["tmc_kham_indexed_receipt"]
        rows={f["name"]:f for f in receipt["field_receipts"]}
        self.assertEqual(rows["ticket_product_poster"]["value"],m.TMC_KHAM_TICKET_POSTER)
        self.assertEqual(rows["ticket_product_poster"]["decision"],"REVIEW")
        self.assertEqual(rows["venue_seat_map_not_poster"]["value"],m.TMC_KHAM_VENUE_SEAT_MAP)
        self.assertEqual(rows["venue_seat_map_not_poster"]["decision"],"REJECT_FOR_EVENT_POSTER")
        self.assertIsNone(receipt["identity"]["image_url"])
        for name,key,bad in (
            ("ticket_product_poster","value","https://imgs2.utiki.com.tw/Data/KHAM/Images/UTK2401/OTHER_Large.JPG?v=202610231202"),
            ("ticket_product_poster","value",m.TMC_KHAM_TICKET_POSTER.split("?")[0]),
            ("ticket_product_poster","source",m.TMC_DETAIL),
            ("ticket_product_poster","role","GOLDEN_OFFICIAL_IMAGE"),
            ("ticket_product_poster","formal_accepted",True),
            ("venue_seat_map_not_poster","value",m.TMC_KHAM_TICKET_POSTER),
            ("venue_seat_map_not_poster","decision","REVIEW"),
            ("venue_seat_map_not_poster","role","EVENT_POSTER"),
            ("venue_seat_map_not_poster","formal_accepted",True),
        ):
            changed=copy.deepcopy(receipt)
            next(f for f in changed["field_receipts"] if f["name"]==name)[key]=bad
            with self.subTest(name=name,key=key):
                with self.assertRaises(ValueError):m.validate_tmc_kham_receipt(changed)
        changed=copy.deepcopy(receipt)
        changed["identity"]["image_url"]=m.TMC_KHAM_TICKET_POSTER
        with self.assertRaises(ValueError):m.validate_tmc_kham_receipt(changed)



    def test_rotated_price_image_role_gate(self):
        # A canonical tixCraft #03 and B P0 TMC are different events; no
        # cross-event identity, no formal tier/asset, no synthetic Golden.
        receipt=data["role_rotation_indexed_receipt"]
        self.assertEqual(m.validate_role_rotation_receipt(receipt),{
            "A_review":3,"A_rejected_as_admission":2,"B_review":6,
            "B_rejected_as_base_or_poster":2,"native_get":0,"formal_accepted":0,
            "golden":0,"published":0,"decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"})
        rows={r["name"]:r for r in receipt["field_receipts"]}
        self.assertEqual(rows["ticket_standard_advertised_tiers"]["value"][-1],1680)
        self.assertEqual(rows["venue_standard_presale_tiers"]["value"][-1],800)
        self.assertEqual(rows["venue_accessibility_restricted_tiers"]["value"][-1],400)
        self.assertEqual(rows["venue_event_poster"]["value"],m.TMC_SCENE_POSTER)
        self.assertEqual(rows["venue_seating_chart"]["value"],m.TMC_SCENE_SEAT_MAP)
        self.assertEqual(rows["ticket_ibon_pickup_fee"]["decision"],"REJECT_FOR_ADMISSION_PRICE")
        self.assertEqual(rows["venue_cassette_bundle_tiers"]["decision"],"REJECT_FOR_BASE_ADMISSION")
        self.assertIsNone(receipt["identity"]["formal_eligible_min_price"])
        self.assertIsNone(receipt["identity"]["formal_img_url"])

    def test_rotated_source_role_negative_matrix(self):
        receipt=data["role_rotation_indexed_receipt"]
        for name,key,bad in (
            ("ticket_standard_advertised_tiers","value",[30]),
            ("ticket_disability_restricted_tiers","role","GENERAL_ADMISSION"),
            ("ticket_ibon_pickup_fee","decision","REVIEW"),
            ("ticket_bank_transfer_fee","value",1680),
            ("ticket_showtimes","value",["2026-11-21T19:30:00+08:00"]),
            ("venue_standard_presale_tiers","value",[400]),
            ("venue_accessibility_restricted_tiers","role","GENERAL_ADMISSION"),
            ("venue_cassette_bundle_tiers","decision","REVIEW"),
            ("venue_ticket_platform_claim","role","TICKET_EVENT_ID"),
            ("venue_event_poster","value",m.TMC_SCENE_SEAT_MAP),
            ("venue_event_poster","source",m.TIX_FOREVER),
            ("venue_seating_chart","decision","REVIEW"),
            ("venue_seating_chart","role","EVENT_POSTER"),
            ("venue_room","observed_at","2026-11-03T02:58:05"),
            ("venue_showtime","formal_accepted",True),
        ):
            changed=copy.deepcopy(receipt)
            next(r for r in changed["field_receipts"] if r["name"]==name)[key]=bad
            with self.subTest(name=name,key=key):
                with self.assertRaises(ValueError):m.validate_role_rotation_receipt(changed)
        for key,bad in (
            ("A_ticket_session_id","invented"),("B_ticket_event_id","invented"),
            ("B_ticket_session_id","invented"),("formal_eligible_min_price",400),
            ("formal_img_url",m.TMC_SCENE_POSTER),("cross_event_identity_merge",True),
        ):
            changed=copy.deepcopy(receipt);changed["identity"][key]=bad
            with self.subTest(identity=key):
                with self.assertRaises(ValueError):m.validate_role_rotation_receipt(changed)
        for key in ("native_official_get","formal_accepted_fields","golden_accepted_events","published_events"):
            changed=copy.deepcopy(receipt);changed[key]=1
            with self.subTest(release=key):
                with self.assertRaises(ValueError):m.validate_role_rotation_receipt(changed)
        changed=copy.deepcopy(receipt)
        changed["field_receipts"].append(copy.deepcopy(changed["field_receipts"][0]))
        with self.assertRaises(ValueError):m.validate_role_rotation_receipt(changed)
        changed=copy.deepcopy(receipt);changed["sources"]["B_detail"]=m.TMC_DETAIL
        with self.assertRaises(ValueError):m.validate_role_rotation_receipt(changed)



    def test_independent_klook_tmc_event_edge_and_tixcraft_sale_roles(self):
        # Independent indexed official pages: A ticket sale is not SHOW/stock;
        # B ticket Event path matches venue title/show/room, not a Session.
        e=data["ticket_bridge_indexed_receipt"]
        self.assertEqual(m.validate_ticket_bridge_receipt(e),{
            "A_review":2,"A_reject_stock":1,"B_review":6,"B_reject_price":2,
            "B_ticket_event_id_review":"102001087","B_ticket_session_id":None,
            "native_get":0,"formal_accepted":0,"golden":0,"published":0,
            "decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"})
        rows={x["name"]:x for x in e["field_receipts"]}
        self.assertEqual(rows["klook_ticket_event_url"]["value"],m.KLOOK_SCENE)
        self.assertEqual(rows["klook_showtime"]["value"],rows["venue_showtime"]["value"] if "venue_showtime" in rows else "2026-11-21T19:30:00+08:00")
        self.assertEqual(rows["klook_standard_tiers"]["value"],[1600,1200,800])
        self.assertEqual(rows["klook_accessibility_tiers"]["value"],[800,600,400])
        self.assertEqual(rows["klook_display_range"]["decision"],"REJECT_FOR_ELIGIBLE_MIN")
        self.assertFalse(e["identity"]["B_venue_direct_href_verified"])
        self.assertIsNone(e["identity"]["B_ticket_session_id"])

    def test_independent_ticket_bridge_negative_parity_and_release_guards(self):
        e=data["ticket_bridge_indexed_receipt"]
        for name,key,bad in (
            ("ticket_initial_general_sale","value","2026-11-28T19:00:00+08:00"),
            ("ticket_partial_release","role","TICKET_ANNOUNCED_SHOW"),
            ("ticket_partial_release_not_inventory","decision","REVIEW"),
            ("klook_ticket_event_url","value","https://www.klook.com/zh-TW/event-detail/999-other/"),
            ("klook_event_title","value","another event"),
            ("klook_showtime","value","2026-11-28T19:00:00+08:00"),
            ("klook_venue","value","臺北大巨蛋"),
            ("klook_standard_tiers","value",[400]),
            ("klook_accessibility_tiers","role","GENERAL_ADMISSION"),
            ("klook_bundle_tiers","decision","REVIEW"),
            ("klook_display_range","decision","REVIEW"),
            ("klook_ticket_event_url","source",m.TMC_SCENE),
            ("klook_ticket_event_url","formal_accepted",True),
            ("klook_showtime","observed_at","2026-11-03T03:54:00"),
        ):
            d=copy.deepcopy(e)
            next(x for x in d["field_receipts"] if x["name"]==name)[key]=bad
            with self.subTest(name=name,key=key):
                with self.assertRaises(ValueError):m.validate_ticket_bridge_receipt(d)
        for key,bad in (
            ("B_ticket_event_id","999"),("B_ticket_session_id","invented"),
            ("B_venue_direct_href_verified",True),
            ("A_ticket_session_id","invented"),
            ("formal_eligible_min_price",800),("formal_img_url",m.TMC_SCENE_POSTER),
            ("cross_event_identity_merge",True),
        ):
            d=copy.deepcopy(e);d["identity"][key]=bad
            with self.subTest(identity=key):
                with self.assertRaises(ValueError):m.validate_ticket_bridge_receipt(d)
        for key in ("native_official_get","formal_accepted_fields","golden_accepted_events","published_events"):
            d=copy.deepcopy(e);d[key]=1
            with self.subTest(release=key):
                with self.assertRaises(ValueError):m.validate_ticket_bridge_receipt(d)
        d=copy.deepcopy(e);d["field_receipts"].append(copy.deepcopy(d["field_receipts"][0]))
        with self.assertRaises(ValueError):m.validate_ticket_bridge_receipt(d)
        d=copy.deepcopy(e);d["sources"]["B_ticket_detail"]=m.TIX_FOREVER
        with self.assertRaises(ValueError):m.validate_ticket_bridge_receipt(d)



    def test_timeline_package_source_roles_and_explicit_shortlink_hold(self):
        # Independent source labels: doors/sale/payment windows are not SHOW,
        # two-person and restricted bundles are not one unrestricted ticket.
        e=data["timeline_package_indexed_receipt"]
        self.assertEqual(m.validate_timeline_package_receipt(e),{
            "A_rejected_session_or_stock":2,"B_review":4,"B_shortlink_hold":1,
            "B_rejected_general_price":2,"native_get":0,"formal_accepted":0,
            "golden":0,"published":0,"decision":"INDEPENDENT_GOLDEN_GATE_STILL_REQUIRED"})
        rows={x["name"]:x for x in e["field_receipts"]}
        self.assertEqual(rows["venue_klook_shortlink"]["value"],m.TMC_KLOOK_SHORTLINK)
        self.assertEqual(rows["venue_klook_shortlink"]["decision"],"HOLD_FOR_FINAL_DESTINATION")
        self.assertEqual(rows["klook_entrance_time"]["value"],"2026-11-21T18:30:00+08:00")
        self.assertEqual(rows["klook_two_person_bundle_quantity"]["value"],2)
        self.assertEqual(rows["klook_two_person_bundle_total"]["decision"],"REJECT_FOR_SINGLE_ADMISSION")
        self.assertFalse(e["identity"]["B_shortlink_final_destination_verified"])

    def test_timeline_package_negative_source_role_identity_release(self):
        e=data["timeline_package_indexed_receipt"]
        for name,key,bad in (
            ("ticket_failed_payment_window","role","TICKET_SESSION"),
            ("ticket_oct4_release_notice","decision","REVIEW"),
            ("venue_klook_shortlink","value",m.KLOOK_SCENE),
            ("venue_klook_shortlink","decision","REVIEW"),
            ("klook_entrance_time","role","SHOWTIME"),
            ("klook_presale_start","value","2026-11-21T19:30:00+08:00"),
            ("klook_presale_end","role","EVENT_END"),
            ("klook_two_person_bundle_total","decision","REVIEW"),
            ("klook_two_person_bundle_quantity","value",1),
            ("klook_accessibility_cassette_bundle","role","GENERAL_ADMISSION"),
            ("klook_two_person_bundle_total","source",m.TMC_SCENE),
            ("klook_entrance_time","formal_accepted",True),
            ("venue_klook_shortlink","observed_at","2026-11-03T04:58:43"),
        ):
            d=copy.deepcopy(e)
            next(x for x in d["field_receipts"] if x["name"]==name)[key]=bad
            with self.subTest(name=name,key=key):
                with self.assertRaises(ValueError):m.validate_timeline_package_receipt(d)
        for key,bad in (
            ("B_shortlink_final_destination_verified",True),
            ("B_ticket_event_id","999"),("B_ticket_session_id","invented"),
            ("A_ticket_session_id","invented"),("B_checkout_eligible_single_ticket_min",400),
            ("formal_img_url",m.TMC_SCENE_POSTER),("cross_event_identity_merge",True),
        ):
            d=copy.deepcopy(e);d["identity"][key]=bad
            with self.subTest(identity=key):
                with self.assertRaises(ValueError):m.validate_timeline_package_receipt(d)
        for key in ("native_official_get","formal_accepted_fields","golden_accepted_events","published_events"):
            d=copy.deepcopy(e);d[key]=1
            with self.subTest(release=key):
                with self.assertRaises(ValueError):m.validate_timeline_package_receipt(d)
        d=copy.deepcopy(e);d["field_receipts"].append(copy.deepcopy(d["field_receipts"][0]))
        with self.assertRaises(ValueError):m.validate_timeline_package_receipt(d)
        d=copy.deepcopy(e);d["sources"]["B_ticket_detail"]=m.TIX_FOREVER
        with self.assertRaises(ValueError):m.validate_timeline_package_receipt(d)



    def test_rotated_a_indievox_b_zepp_kktix_same_event_receipts(self):
        # Independent indexed source pages, not a native GET or Golden acceptance.
        e=self._rotated_source_fixture()
        result=m.validate_rotated_event_receipt(e)
        self.assertEqual(result["formal_accepted"],0)
        self.assertEqual(result["A_conflict_hold"],1)
        self.assertEqual(result["B_reject_general_price"],3)
        self.assertEqual(e["identity"]["A_event_id"],e["identity"]["A_game_event_id"])
        self.assertIsNone(e["identity"]["B_ticket_session_id"])
        self.assertIsNone(e["identity"]["formal_eligible_checkout_min"])

    @staticmethod
    def _rotated_source_fixture():
        e={"kind":"P30_L7_A_B_SOURCE_ROTATION_V1",
           "observation_method":"PUBLIC_INDEXED_TEXT_READER_REOBSERVATION",
           "release_state":"HARD_HOLD_NO_PUBLICATION",
           "native_official_get":0,"formal_accepted_fields":0,
           "golden_accepted_events":0,"published_events":0,
           "sources":{"A_detail":m.MYCELIUM_DETAIL,"A_game":m.MYCELIUM_GAME,
                      "B_venue_list":m.ZEPP_TAKASE_LIST,
                      "B_venue_detail":m.ZEPP_TAKASE_DETAIL,
                      "B_ticket_detail":m.KKTIX_TAKASE},
           "identity":{"A_event_id":"26_iv04256e8","A_game_event_id":"26_iv04256e8",
                       "A_header_game_time_conflict_with_body_poster":True,
                       "A_ticket_session_id":None,"B_venue_rid":"160668",
                       "B_ticket_event_url":m.KKTIX_TAKASE,
                       "B_ticket_session_id":None,
                       "B_fanclub_two_day_is_single_day":False,
                       "formal_eligible_checkout_min":None,"formal_img_url":None,
                       "cross_event_identity_merge":False}}
        e["field_receipts"]=[{"name":name,"line":line,"source":source,"role":role,
             "value":copy.deepcopy(value),"decision":decision,
             "observed_at":"2026-11-03T05:55:00+08:00","formal_accepted":False}
             for name,(line,source,role,value,decision) in m.ROTATED_EVENT_FIELDS.items()]
        return e

    def test_rotated_source_negative_cross_event_role_time_price_and_image(self):
        e=self._rotated_source_fixture()
        for name,key,bad in (
            ("a_game_show","source",m.MYCELIUM_DETAIL),
            ("a_body_show","decision","REVIEW"),
            ("a_header_show","value","2026-11-13T19:00:00+08:00"),
            ("a_single_presale","value",350),
            ("a_two_person_total","decision","REVIEW"),
            ("a_accessibility","role","GENERAL_ADMISSION"),
            ("a_event_poster","value",m.ZEPP_TAKASE_POSTER),
            ("b_direct_ticket_event","value","https://freeplanetml.kktix.cc/events/other"),
            ("b_ticket_options","value",["NOV_07_SINGLE_DAY"]),
            ("b_kktix_showtimes","source",m.ZEPP_TAKASE_DETAIL),
            ("b_general_single","value",900),
            ("b_fanclub_two_day","decision","REVIEW"),
            ("b_accessibility","decision","REVIEW"),
            ("b_pickup_fee","role","GENERAL_ADMISSION"),
            ("b_venue_poster","value",m.KKTIX_TAKASE_POSTER),
            ("b_ticket_poster","value",m.ZEPP_TAKASE_POSTER),
            ("b_ticket_session","value","invented"),
            ("b_current_stock","value",0),
            ("b_general_single","formal_accepted",True),
            ("a_event_title","observed_at","2026-11-03T05:55:00"),
        ):
            d=copy.deepcopy(e)
            next(x for x in d["field_receipts"] if x["name"]==name)[key]=bad
            with self.subTest(name=name,key=key):
                with self.assertRaises(ValueError):m.validate_rotated_event_receipt(d)
        for key,bad in (
            ("A_game_event_id","different"),
            ("A_header_game_time_conflict_with_body_poster",False),
            ("B_venue_rid","166457"),
            ("B_ticket_event_url","https://other.kktix.cc/events/other"),
            ("B_fanclub_two_day_is_single_day",True),
            ("B_ticket_session_id","invented"),
            ("formal_eligible_checkout_min",900),
            ("formal_img_url",m.ZEPP_TAKASE_POSTER),
            ("cross_event_identity_merge",True),
        ):
            d=copy.deepcopy(e);d["identity"][key]=bad
            with self.subTest(identity=key):
                with self.assertRaises(ValueError):m.validate_rotated_event_receipt(d)
        for key in ("native_official_get","formal_accepted_fields",
                    "golden_accepted_events","published_events"):
            d=copy.deepcopy(e);d[key]=1
            with self.subTest(release=key):
                with self.assertRaises(ValueError):m.validate_rotated_event_receipt(d)
        d=copy.deepcopy(e);d["field_receipts"].append(copy.deepcopy(d["field_receipts"][0]))
        with self.assertRaises(ValueError):m.validate_rotated_event_receipt(d)

if __name__=="__main__":unittest.main()
