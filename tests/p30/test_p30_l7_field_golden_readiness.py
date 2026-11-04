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
        self.assertEqual(result["A_explicit_start_conflict_hold"],1)
        self.assertEqual(result["B_registration_href_403_hold"],3)
        # Three option-specific public hrefs are exact, but GET 403 means
        # no registration Session, stock, checkout, or Golden acceptance.
        self.assertEqual([r["value"] for r in e["field_receipts"]
            if r["name"].startswith("b_kktix_") and r["name"].endswith("_registration")],
            ["https://kktix.com/events/takasetoya202611-1/registrations/new",
             "https://kktix.com/events/takasetoya202611-2/registrations/new",
             "https://kktix.com/events/takasetoya202611-3/registrations/new"])
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
            ("a_explicit_start_time_conflict","decision","REVIEW"),
            ("a_explicit_start_time_conflict","role","FORMAL_SHOWTIME"),
            ("b_kktix_two_day_registration","decision","REVIEW"),
            ("b_kktix_nov07_registration","value","https://kktix.com/events/takasetoya202611-3/registrations/new"),
            ("b_kktix_nov08_registration","source",m.ZEPP_TAKASE_DETAIL),
            ("b_kktix_nov08_registration","formal_accepted",True),
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


    @staticmethod
    def _dome_fixture():
        # Independent indexed reader; this fixture is NOT a live source GET.
        e={"kind":"P30_L7_DOME_CROSSCHECK_V1",
           "scope":"ISOLATED_EVIDENCE_ONLY",
           "observation_method":"PUBLIC_INDEXED_TEXT_READER_REOBSERVATION",
           "release_state":"HARD_HOLD_NO_PUBLICATION",
           "native_official_get":0,"formal_accepted_fields":0,
           "golden_accepted_events":0,"published_events":0,
           "sources":{"A":m.DOME_TICKET,"B":m.DOME_CALENDAR},
           "identity":{"A_platform_id":"03","A_ticket_event_id":"26_forever",
                       "B_venue_source":"TAIPEI_DOME_OFFICIAL_NOT_FORMAL_19",
                       "B_calendar_event_id":None,"B_direct_ticket_href":None,
                       "B_calendar_show_time":None,"ticket_session_id":None,
                       "formal_eligible_min":None,"formal_img_url":None,
                       "cross_source_identity":"TITLE_DATES_VENUE_REVIEW_NO_DIRECT_ID_EDGE",
                       "cross_event_merge":False}}
        e["field_receipts"]=[{"name":name,"line":line,"source":source,
            "role":role,"value":copy.deepcopy(value),"decision":decision,
            "reason":"Exact official source text, independently indexed; no Golden promotion",
            "observed_at":"2026-11-03T07:55:00+08:00","formal_accepted":False}
            for name,(line,source,role,value,decision) in m.DOME_FIELDS.items()]
        return e

    def test_dome_ticket_calendar_independent_roles(self):
        e=self._dome_fixture()
        result=m.validate_dome_crosscheck(e)
        self.assertEqual((result["A_review"],result["B_review"]), (5,2))
        self.assertEqual((result["formal_accepted"],result["golden"],result["published"]), (0,0,0))
        self.assertEqual(e["identity"]["B_calendar_event_id"],None)
        self.assertEqual(next(x for x in e["field_receipts"] if x["name"]=="b_dates")["value"],
                         ["2026-11-28","2026-11-29"])

    def test_dome_calendar_fail_closed_negative_cases(self):
        e=self._dome_fixture()
        for name,key,bad in (
            ("a_shows","value",["2026-11-28","2026-11-29"]),
            ("a_general_prices","value",[1840]),
            ("a_accessibility","decision","REVIEW"),
            ("a_ibon_fee","role","GENERAL_ADMISSION"),
            ("a_age_advisory","role","AGE_MINIMUM"),
            ("a_child_companion","value",7),
            ("a_session","value","invented"),
            ("b_dates","value",["2026-11-12","2026-11-13"]),
            ("b_other_event","decision","REVIEW"),
            ("b_shuttle","role","TICKET_SESSION"),
            ("b_ticket_href","value",m.DOME_TICKET),
            ("b_show_time","value","2026-11-28T19:00:00+08:00"),
            ("b_img_url","value","https://example.com/poster.jpg"),
            ("b_calendar_title","source",m.DOME_TICKET),
            ("b_calendar_title","formal_accepted",True),
            ("b_dates","observed_at","2026-11-03T07:55:00"),
        ):
            d=copy.deepcopy(e)
            next(x for x in d["field_receipts"] if x["name"]==name)[key]=bad
            with self.subTest(name=name,key=key):
                with self.assertRaises(ValueError):m.validate_dome_crosscheck(d)
        for key,bad in (
            ("B_calendar_event_id","26_forever"),
            ("B_direct_ticket_href",m.DOME_TICKET),
            ("B_calendar_show_time","2026-11-28T19:00:00+08:00"),
            ("ticket_session_id","fabricated"),
            ("formal_eligible_min",1680),
            ("formal_img_url","https://example.com/hero.jpg"),
            ("cross_event_merge",True),
        ):
            d=copy.deepcopy(e);d["identity"][key]=bad
            with self.subTest(identity=key):
                with self.assertRaises(ValueError):m.validate_dome_crosscheck(d)
        for key in ("native_official_get","formal_accepted_fields",
                    "golden_accepted_events","published_events"):
            d=copy.deepcopy(e);d[key]=1
            with self.assertRaises(ValueError):m.validate_dome_crosscheck(d)
        d=copy.deepcopy(e);d["field_receipts"].append(copy.deepcopy(d["field_receipts"][0]))
        with self.assertRaises(ValueError):m.validate_dome_crosscheck(d)



# 2026-11-03: Public indexed text-source receipts; no checkout, no native GET.
class PublicNonSessionFieldReadiness(unittest.TestCase):
    @staticmethod
    def fixture():
        e = {
            "kind": "P30_L7_NON_SESSION_FIELD_READINESS_V1",
            "scope": "ISOLATED_EVIDENCE_ONLY",
            "observation_method": "PUBLIC_INDEXED_TEXT_READER_NOT_NATIVE_GET",
            "source_freshness": "HOLD_INDEXED_CACHE_NOT_SAME_SESSION_NATIVE",
            "release_state": "HARD_HOLD_NO_PUBLICATION",
            "native_official_get": 0, "formal_accepted_fields": 0,
            "golden_accepted_events": 0, "published_events": 0,
            "sources": {
                "A_venue_list": m.PUBLIC_TMC_LIST,
                "A_venue_detail": m.PUBLIC_TMC_DETAIL,
                "A_ticket_detail": m.PUBLIC_KHAM_PRODUCT,
                "B_venue_list": m.PUBLIC_TWTC_LIST,
                "B_venue_detail": m.PUBLIC_TWTC_DETAIL},
            "identity": {
                "A_ticket_platform_id": "04", "A_product_id": "P1DF32E2",
                "A_venue_detail_id": "2026SungNien-Yu",
                "A_direct_official_ticket_edge": m.PUBLIC_KHAM_PRODUCT,
                "A_ticket_session_id": None, "A_checkout_eligible_min": None,
                "B_platform_id": "16", "B_exhibition_detail_id": "29418",
                "B_ticket_session_id": None, "B_admission_verified": False,
                "B_list_detail_same_native_session": False,
                "formal_img_url": None, "cross_event_merge": False}}
        e["field_receipts"] = [
            {"name": name, "line": line, "source": source,
             "role": role, "value": copy.deepcopy(value),
             "decision": decision, "formal_accepted": False,
             "reason": "Exact public indexed official source text; independent native same-session and Golden pending",
             "observed_at": "2026-11-03T08:53:00+08:00"}
            for name, (line, source, role, value, decision)
            in m.PUBLIC_NON_SESSION_FIELDS.items()]
        return e

    def test_public_source_positive_non_session_roles(self):
        e = self.fixture()
        result = m.validate_public_non_session_receipt(e)
        self.assertEqual((result["A_review"], result["B_review"]), (7, 5))
        self.assertEqual((result["formal_accepted"], result["native_get"],
                          result["golden"], result["published"]), (0, 0, 0, 0))
        self.assertEqual(e["identity"]["B_exhibition_detail_id"], "29418")
        self.assertEqual(e["identity"]["A_product_id"], "P1DF32E2")

    def test_non_session_source_role_negative_cases(self):
        e = self.fixture()
        cases = (
            ("a_venue_direct_ticket_href", "value", m.PUBLIC_KHAM_PRODUCT + "&SESSION=guess"),
            ("a_venue_direct_ticket_href", "source", m.PUBLIC_TWTC_DETAIL),
            ("a_ticket_sale_start", "role", "EVENT_SHOWTIME"),
            ("a_ticket_age_advisory", "role", "AGE_MINIMUM"),
            ("a_ticket_duration", "role", "EVENT_SHOWTIME"),
            ("a_eligible_min", "value", 1880),
            ("a_current_stock", "value", 0),
            ("a_ticket_session", "value", "invented"),
            ("b_list_title", "value", "Different exhibition"),
            ("b_detail_title", "source", m.PUBLIC_TWTC_LIST),
            ("b_exhibition_dates", "value", ["2026-11-06", "2026-11-10"]),
            ("b_daily_open_hours", "role", "SHOWTIME"),
            ("b_exhibition_hall", "source", m.PUBLIC_TMC_DETAIL),
            ("b_admission_rules", "value", "free"),
            ("b_ticket_event_id", "value", "29418"),
            ("b_event_image", "value", "https://example.com/fake.jpg"),
            ("b_daily_open_hours", "formal_accepted", True),
            ("b_exhibition_dates", "observed_at", "2026-11-03T08:53:00"),
        )
        for name, key, bad in cases:
            d = copy.deepcopy(e)
            next(x for x in d["field_receipts"] if x["name"] == name)[key] = bad
            with self.subTest(name=name, key=key):
                with self.assertRaises(ValueError):
                    m.validate_public_non_session_receipt(d)
        for key, bad in (
            ("A_product_id", "wrong"),
            ("A_direct_official_ticket_edge", "https://kham.com.tw/other"),
            ("A_ticket_session_id", "invented"),
            ("B_exhibition_detail_id", "29419"),
            ("B_list_detail_same_native_session", True),
            ("B_admission_verified", True),
            ("formal_img_url", "https://example.com/hero.jpg"),
            ("cross_event_merge", True),
        ):
            d = copy.deepcopy(e)
            d["identity"][key] = bad
            with self.subTest(identity=key):
                with self.assertRaises(ValueError):
                    m.validate_public_non_session_receipt(d)
        for key, bad in (
            ("native_official_get", 1),
            ("formal_accepted_fields", 1),
            ("golden_accepted_events", 1),
            ("published_events", 1),
            ("source_freshness", "PASS"),
        ):
            d = copy.deepcopy(e)
            d[key] = bad
            with self.subTest(release=key):
                with self.assertRaises(ValueError):
                    m.validate_public_non_session_receipt(d)
        d = copy.deepcopy(e)
        d["field_receipts"].append(copy.deepcopy(d["field_receipts"][0]))
        with self.assertRaises(ValueError):
            m.validate_public_non_session_receipt(d)


class IndependentPublicFieldCrosscheck(unittest.TestCase):
    def fixture(self):
        return copy.deepcopy(data["independent_public_field_crosscheck"])

    def test_all_eight_independent_reader_values_remain_review_only(self):
        r=m.validate_independent_public_field_crosscheck(self.fixture())
        self.assertEqual((r["A_crosschecked"],r["B_crosschecked"],r["review_only"]),(3,5,8))
        self.assertEqual((r["formal_accepted"],r["golden"],r["published"],r["native_get_this_gate"]),(0,0,0,0))

    def test_independent_crosscheck_negative_identity_role_value_and_release(self):
        for field,key,bad in (
            ("direct_ticket_product","observed_value",{"product_id":"P1DF32E2","official_ticket_url":m.PUBLIC_KHAM_PRODUCT+"&session=guess"}),
            ("venue_showtime","observed_value","2026/08/22 12:00"),
            ("venue_hall","observed_value","臺北流行音樂中心 文化館"),
            ("list_detail_identity","observed_value",{"exhibition_id":"29419","same_row_title":"2026年電器空調影音大展"}),
            ("exhibition_title","observed_value","2026台北國際旅展"),
            ("exhibition_dates","observed_value",{"start":"2026/11/06","end":"2026/11/10"}),
            ("open_hours","role","PERFORMANCE_SHOWTIME"),
            ("venue_hall","source_url",m.PUBLIC_TWTC_LIST),
            ("open_hours","prior_native_body_sha256","0"*64),
            ("exhibition_dates","reader_observed_at_utc","2026-11-03T07:00:00"),
            ("venue_showtime","formal_accepted",True),
        ):
            e=self.fixture()
            row=next(x for x in e["field_receipts"] if x["field"]==field)
            row[key]=bad
            with self.subTest(field=field,key=key):
                with self.assertRaises(ValueError):
                    m.validate_independent_public_field_crosscheck(e)
        for key,bad in (
            ("this_gate_native_get",3),("formal_accepted_fields",1),
            ("golden_accepted_events",1),("published_events",1),
            ("formal_pwa_feed_events",1),
            ("method","NATIVE_GET"),
            ("prior_native_artifact_id",0),
        ):
            e=self.fixture();e[key]=bad
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    m.validate_independent_public_field_crosscheck(e)
        e=self.fixture()
        e["field_receipts"].append(copy.deepcopy(e["field_receipts"][0]))
        with self.assertRaises(ValueError):
            m.validate_independent_public_field_crosscheck(e)


class FirstUsableNonSessionSubset(unittest.TestCase):
    def fixture(self):
        return copy.deepcopy(data["independent_public_field_crosscheck"])

    def test_proposal_has_five_real_values_two_exact_identity_dependencies_and_zero_release(self):
        source=self.fixture()
        proposal=m.build_independent_field_subset_proposal(source)
        result=m.validate_independent_field_subset_proposal(source,proposal)
        self.assertEqual((result["A_candidate_fields"],result["B_candidate_fields"]), (2,3))
        self.assertEqual(result["identity_dependencies"],2)
        self.assertEqual(result["prior_source_value_crosschecks"],8)
        self.assertEqual((result["native_get_this_gate"],result["formal_accepted"],
                          result["golden"],result["published"],result["formal_pwa_feed"]), (0,0,0,0,0))
        self.assertEqual([(r["line"],r["field"]) for r in proposal["candidate_fields"]],
                         list(m.FIELD_SUBSET_KEYS))
        self.assertEqual([(r["line"],r["field"]) for r in proposal["identity_dependencies"]],
                         list(m.FIELD_SUBSET_DEPENDENCIES))

    def test_fail_closed_cross_event_role_conflict_hash_and_unauthorized_promotion(self):
        source=self.fixture()
        baseline=m.build_independent_field_subset_proposal(source)
        for section,index,key,bad in (
            ("candidate_fields",0,"observed_value","2026/08/22 12:00"),
            ("candidate_fields",1,"observed_value","臺北流行音樂中心 文化館"),
            ("candidate_fields",2,"observed_value",{"start":"2026/11/06","end":"2026/11/10"}),
            ("candidate_fields",3,"observed_value",{"open":"19:30","close":"21:00"}),
            ("candidate_fields",4,"observed_value","世貿三館"),
            ("candidate_fields",0,"role","TICKET_SALE_START"),
            ("candidate_fields",2,"source_url",m.PUBLIC_TWTC_LIST),
            ("candidate_fields",2,"event_id","29419"),
            ("candidate_fields",3,"prior_native_body_sha256","0"*64),
            ("candidate_fields",4,"reader_observed_at_utc","2026-11-03T07:00:00"),
            ("candidate_fields",0,"formal_accepted",True),
            ("identity_dependencies",0,"observed_value",{"product_id":"OTHER","official_ticket_url":m.PUBLIC_KHAM_PRODUCT}),
            ("identity_dependencies",1,"observed_value",{"exhibition_id":"29419","same_row_title":"2026年電器空調影音大展"}),
        ):
            p=copy.deepcopy(baseline);p[section][index][key]=bad
            with self.subTest(section=section,key=key,bad=str(bad)[:40]):
                with self.assertRaises(ValueError):
                    m.validate_independent_field_subset_proposal(source,p)
        for key,bad in (
            ("release_state","PUBLICATION_ALLOWED"),
            ("native_get_this_gate",3),
            ("formal_accepted_fields",1),
            ("golden_accepted_events",1),
            ("published_events",1),
            ("formal_pwa_feed_events",1),
            ("independent_formal_field_authority","APPROVED"),
            ("decision","FORMAL_FIELD_PASS"),
            ("source_freshness","FRESH_NATIVE_THIS_GATE"),
            ("prior_native_matrix_sha256","0"*64),
        ):
            p=copy.deepcopy(baseline);p[key]=bad
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    m.validate_independent_field_subset_proposal(source,p)
        p=copy.deepcopy(baseline);p["candidate_fields"].append(copy.deepcopy(p["candidate_fields"][0]))
        with self.assertRaises(ValueError):
            m.validate_independent_field_subset_proposal(source,p)
        p=copy.deepcopy(baseline);p["identity_dependencies"]=[]
        with self.assertRaises(ValueError):
            m.validate_independent_field_subset_proposal(source,p)


class FixedOfficialHTMLAdapter(unittest.TestCase):
    """Executable source-local parser; fixture input never counts as a live GET."""
    NOW = "2026-11-04T00:00:00+08:00"
    TMC_TITLE = "小宇 宋念宇 《不，完美的人》 演唱會"
    TWTC_TITLE = "2026年電器空調影音大展"
    TMC_HTML = (
        '<html><h2>小宇 宋念宇 《不，完美的人》 演唱會</h2>'
        '<div>2026.11.07 19:30 (六)</div>'
        '<h3>活動地點</h3><p>臺北流行音樂中心 表演廳</p>'
        '<h3>主辦單位</h3><p>寬宏藝術</p>'
        '<a href="https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2">購票連結</a>'
        '<p>演唱會 2026.08.11 發佈日</p></html>'
    )
    TWTC_HTML = (
        '<html><h2>2026年電器空調影音大展</h2>'
        '<p>展覽館別：世貿一館</p><p>主辦單位：台北市電器商業同業公會</p>'
        '<p>展出日期：2026/11/06 ~ 2026/11/09</p>'
        '<p>展出時間：10:00 ~ 18:00</p>'
        '<p>入場方式及是否開放兒童入場，請逕洽主辦單位。</p></html>'
    )

    def parse_a(self, html=None, **kwargs):
        return m.parse_official_non_session_html(
            kwargs.pop("url", m.PUBLIC_TMC_DETAIL),
            self.TMC_HTML if html is None else html,
            kwargs.pop("title", self.TMC_TITLE),
            kwargs.pop("identity", "P1DF32E2"),
            kwargs.pop("observed", self.NOW),
            kwargs.pop("now", __import__("datetime").datetime.fromisoformat(self.NOW)))

    def parse_b(self, html=None, **kwargs):
        return m.parse_official_non_session_html(
            kwargs.pop("url", m.PUBLIC_TWTC_DETAIL),
            self.TWTC_HTML if html is None else html,
            kwargs.pop("title", self.TWTC_TITLE),
            kwargs.pop("identity", "29418"),
            kwargs.pop("observed", self.NOW),
            kwargs.pop("now", __import__("datetime").datetime.fromisoformat(self.NOW)))

    def test_tmc_fixed_detail_parser_has_two_non_session_fields_and_direct_product_edge(self):
        r = self.parse_a()
        self.assertEqual(r["line"], "A")
        self.assertEqual(r["identity"]["product_id"], "P1DF32E2")
        self.assertEqual([(x["field"], x["value"]) for x in r["candidate_fields"]],
                         [("venue_showtime", "2026/11/07 19:30"),
                          ("venue_hall", "臺北流行音樂中心 表演廳")])
        self.assertEqual((r["native_get_verified"], r["formal_accepted_fields"],
                          r["golden_accepted_events"], r["published_events"]),
                         (False, 0, 0, 0))
        self.assertTrue(all(not x["formal_accepted"] for x in r["candidate_fields"]))

    def test_twtc_fixed_detail_parser_has_three_distinct_field_roles(self):
        r = self.parse_b()
        self.assertEqual(r["identity"]["exhibition_id"], "29418")
        self.assertEqual([(x["field"], x["value"]) for x in r["candidate_fields"]],
                         [("exhibition_dates", {"start": "2026/11/06", "end": "2026/11/09"}),
                          ("open_hours", {"open": "10:00", "close": "18:00"}),
                          ("venue_hall", "世貿一館")])
        self.assertTrue(all(x["decision"] == "SOURCE_LOCAL_PARSE_REVIEW_ONLY"
                            for x in r["candidate_fields"]))

    def test_fail_closed_cross_event_role_ambiguity_staleness_and_wrong_authority(self):
        from datetime import datetime
        cases = (
            lambda: self.parse_a(title="另一場演唱會"),
            lambda: self.parse_a(identity="POTHER123"),
            lambda: self.parse_a(url="https://evil.example/tw/blog/show/2026SungNien-Yu"),
            lambda: self.parse_a(html=self.TMC_HTML.replace(
                "2026.11.07 19:30", "2026.11.07 19:30 / 2026.11.08 19:30")),
            lambda: self.parse_a(html=self.TMC_HTML.replace(
                "活動地點", "開賣地點")),
            lambda: self.parse_a(html=self.TMC_HTML.replace(
                "PRODUCT_ID=P1DF32E2", "PRODUCT_ID=PDIFFERENT")),
            lambda: self.parse_b(identity="29419"),
            lambda: self.parse_b(title="2026台北國際旅展"),
            lambda: self.parse_b(html=self.TWTC_HTML.replace(
                "展出日期", "開賣日期")),
            lambda: self.parse_b(html=self.TWTC_HTML.replace(
                "10:00 ~ 18:00", "18:00 ~ 10:00")),
            lambda: self.parse_b(url="https://twtc.com.tw/exhibition_more.aspx?id=29418&p=menu1"),
            lambda: self.parse_b(observed="2026-10-31T00:00:00+08:00"),
        )
        for i, call in enumerate(cases):
            with self.subTest(case=i):
                with self.assertRaises(ValueError):
                    call()



class SafeListDetailCandidatePipeline(unittest.TestCase):
    """In-memory LIST->DETAIL candidate: neither synthetic HTML nor hash proves GET."""
    NOW = __import__("datetime").datetime.fromisoformat("2026-11-04T00:00:00+08:00")
    TMC_TITLE = FixedOfficialHTMLAdapter.TMC_TITLE
    TWTC_TITLE = FixedOfficialHTMLAdapter.TWTC_TITLE
    TMC_DETAIL = FixedOfficialHTMLAdapter.TMC_HTML
    TWTC_DETAIL = FixedOfficialHTMLAdapter.TWTC_HTML
    TMC_LIST = (
        '<a href="/tw/blog/show/2026SungNien-Yu">演唱會 '
        + TMC_TITLE + ' 2026.11.07 (六) 表演廳</a>'
    )
    TWTC_LIST = (
        '<table><tr><td>' + TWTC_TITLE + '</td>'
        '<td><a href="/exhibition_more.aspx?id=29418&amp;p=home">更多</a></td>'
        '</tr></table>'
    )

    def run_a(self, **kwargs):
        return m.build_non_session_list_detail_candidate(
            kwargs.pop("list_url", m.PUBLIC_TMC_LIST),
            kwargs.pop("list_html", self.TMC_LIST),
            kwargs.pop("detail_url", m.PUBLIC_TMC_DETAIL),
            kwargs.pop("detail_html", self.TMC_DETAIL),
            kwargs.pop("title", self.TMC_TITLE),
            kwargs.pop("identity", "P1DF32E2"),
            kwargs.pop("observed", "2026-11-04T00:00:00+08:00"),
            kwargs.pop("now", self.NOW))

    def run_b(self, **kwargs):
        return m.build_non_session_list_detail_candidate(
            kwargs.pop("list_url", m.PUBLIC_TWTC_LIST),
            kwargs.pop("list_html", self.TWTC_LIST),
            kwargs.pop("detail_url", m.PUBLIC_TWTC_DETAIL),
            kwargs.pop("detail_html", self.TWTC_DETAIL),
            kwargs.pop("title", self.TWTC_TITLE),
            kwargs.pop("identity", "29418"),
            kwargs.pop("observed", "2026-11-04T00:00:00+08:00"),
            kwargs.pop("now", self.NOW))

    def test_two_sources_list_detail_to_in_memory_candidate(self):
        import hashlib
        for line, result, count in (
            ("A", self.run_a(), 2), ("B", self.run_b(), 3)):
            with self.subTest(line=line):
                self.assertEqual(result["line"], line)
                self.assertEqual(len(result["candidate_fields"]), count)
                self.assertEqual(result["source_receipts"]["attestation"],
                                 "CALLER_SUPPLIED_HTML_HASH_ONLY_NOT_NATIVE_GET")
                self.assertEqual(result["source_receipts"]["freshness"],
                                 "INPUT_TIMESTAMP_ONLY_SOURCE_FRESHNESS_UNVERIFIED")
                self.assertEqual((result["native_get_verified"],
                                  result["formal_accepted_fields"],
                                  result["golden_accepted_events"],
                                  result["published_events"],
                                  result["formal_pwa_feed_events"]),
                                 (False, 0, 0, 0, 0))
                self.assertEqual(result["release_state"], "HARD_HOLD_NO_PUBLICATION")
                self.assertTrue(all(not x["formal_accepted"] for x in result["candidate_fields"]))
        self.assertEqual(self.run_a()["identity"]["product_id"], "P1DF32E2")
        self.assertEqual(self.run_b()["identity"]["exhibition_id"], "29418")
        self.assertEqual(self.run_b()["source_receipts"]["list_html_sha256"],
                         hashlib.sha256(self.TWTC_LIST.encode("utf-8")).hexdigest())

    def test_cross_row_duplicate_wrong_authority_and_stale_fail_closed(self):
        from datetime import timedelta
        cases = (
            lambda: self.run_a(list_html=self.TMC_LIST + self.TMC_LIST),
            lambda: self.run_a(list_html='<article>OTHER EVENT'
                               '<a href="/tw/blog/show/2026SungNien-Yu">other</a></article>'),
            lambda: self.run_a(list_html=self.TMC_LIST.replace(
                "/2026SungNien-Yu", "/different-show")),
            lambda: self.run_a(list_url="https://evil.example/tw/blog/show"),
            lambda: self.run_a(detail_url="https://evil.example/tw/blog/show/2026SungNien-Yu"),
            lambda: self.run_a(identity="POTHER123"),
            lambda: self.run_a(detail_html=self.TMC_DETAIL.replace(
                "2026.11.07 19:30", "2026.11.08 19:30 / 2026.11.07 19:30")),
            lambda: self.run_b(list_html=self.TWTC_LIST +
                               self.TWTC_LIST.replace("<td><a",
                                                      "<td>OTHER EVENT <a")),
            lambda: self.run_b(list_html=(
                '<tr><td>' + self.TWTC_TITLE + '</td></tr>'
                '<tr><td>OTHER</td><td><a href="/exhibition_more.aspx?id=29418&amp;p=home">更多</a></td></tr>')),
            lambda: self.run_b(list_html=self.TWTC_LIST.replace("id=29418", "id=29419")),
            lambda: self.run_b(detail_url=m.PUBLIC_TWTC_DETAIL.replace("p=home", "p=menu1")),
            lambda: self.run_b(identity="29419"),
            lambda: self.run_b(detail_html=self.TWTC_DETAIL.replace(
                "展覽館別：世貿一館", "展覽館別：世貿三館 展覽館別：世貿一館")),
            lambda: self.run_b(observed="2026-11-01T00:00:00+08:00"),
            lambda: self.run_b(now=self.NOW - timedelta(hours=1)),
        )
        for index, call in enumerate(cases):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    call()




class NativeSameRunFiveFieldReviewGate(unittest.TestCase):
    """Injected HTML proves only contract behavior; only real GET can attest freshness."""
    NOW = __import__("datetime").datetime.fromisoformat("2026-11-04T00:00:00+08:00")
    def bodies(self):
        t = FixedOfficialHTMLAdapter
        return {
            "A_LIST": SafeListDetailCandidatePipeline.TMC_LIST.encode("utf-8"),
            "A_DETAIL": t.TMC_HTML.encode("utf-8"),
            "A_KHAM": '<html><h1>2026 小宇 宋念宇《不，完美的人》演唱會</h1></html>'.encode("utf-8"),
            "B_LIST": ('<table><tr><td>11/06 ~ 11/09</td><td>'
                       + t.TWTC_TITLE +
                       '</td><td>世貿一館</td><td><a href="/exhibition_more.aspx?id=29418&amp;p=home">'
                       '更多</a></td></tr></table>').encode("utf-8"),
            "B_DETAIL": t.TWTC_HTML.encode("utf-8"),
        }

    def run_mock(self, bodies=None, statuses=None):
        bodies = self.bodies() if bodies is None else bodies
        statuses = {} if statuses is None else statuses
        def get(role, url):
            return {"status": statuses.get(role, 200), "body": bodies[role],
                    "content_type": "text/html; charset=utf-8", "url": url}
        return m.collect_native_five_field_readiness(fetcher=get, now_utc=self.NOW)

    def test_complete_source_local_fields_stay_mock_review_and_never_publish(self):
        r = self.run_mock()
        self.assertEqual(r["request_count"], 5)
        self.assertEqual(r["source_identity_dependencies"], 2)
        self.assertEqual(r["source_consistent_fields"], 5)
        self.assertEqual(r["independent_native_review_ready_fields"], 0)
        self.assertEqual(r["native_http_200_count"], 0)
        self.assertEqual(r["decision"], "MOCK_ONLY_NOT_NATIVE_OR_GOLDEN")
        self.assertEqual([x["field"] for x in r["field_matrix"]],
                         ["venue_showtime", "venue_hall", "exhibition_dates",
                          "open_hours", "venue_hall"])
        self.assertEqual((r["formal_accepted_fields"], r["golden_accepted_events"],
                          r["published_events"], r["formal_pwa_feed_events"]), (0, 0, 0, 0))
        self.assertTrue(all(not x["formal_accepted"] for x in r["field_matrix"]))
        self.assertTrue(all(x["body_sha256"] and x["observed_at_utc"]
                            for x in r["field_matrix"]))
        self.assertFalse(r["raw_html_saved"])
        self.assertEqual(r["release_state"], "HARD_HOLD_NO_PUBLICATION")

    def test_native_acquisition_failure_and_identity_conflicts_fail_closed(self):
        cases = []
        cases.append((self.bodies(), {"A_DETAIL": 403}))
        cases.append((self.bodies(), {"B_LIST": 403}))
        b = self.bodies()
        b["A_KHAM"] = b["A_KHAM"].replace("宋念宇".encode(), "另一活動".encode())
        cases.append((b, {}))
        b = self.bodies()
        b["B_LIST"] = b["B_LIST"].replace("11/06 ~ 11/09".encode(), "11/12 ~ 11/15".encode())
        cases.append((b, {}))
        b = self.bodies()
        b["A_LIST"] = b["A_LIST"].replace("2026.11.07".encode(), "2026.11.08".encode())
        cases.append((b, {}))
        b = self.bodies()
        b["B_LIST"] = b["B_LIST"].replace("id=29418".encode(), "id=29419".encode())
        cases.append((b, {}))
        b = self.bodies()
        b["B_DETAIL"] = b["B_DETAIL"].replace("10:00 ~ 18:00".encode(), "18:00 ~ 10:00".encode())
        cases.append((b, {}))
        for i, (body, statuses) in enumerate(cases):
            with self.subTest(case=i):
                r = self.run_mock(body, statuses)
                self.assertTrue(r["decision"].endswith("HOLD"))
                self.assertEqual(r["source_consistent_fields"], 0)
                self.assertEqual(r["independent_native_review_ready_fields"], 0)
                self.assertEqual(len(r["field_matrix"]), 5)
                self.assertTrue(all(x["decision"] == "HOLD" for x in r["field_matrix"]))
                self.assertEqual(r["formal_accepted_fields"], 0)
                self.assertEqual(r["published_events"], 0)





class TWTCBilingualConflictAuthority(unittest.TestCase):
    """Same ID is not proof that the English 2025 title may overwrite 2026."""
    def setUp(self):
        self.cn = {
            "source_url": "https://twtc.com.tw/exhibition_more.aspx?id=29418&p=home",
            "language": "ZH", "exhibition_id": "29418",
            "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
            "observed_at_utc": "2026-11-04T03:50:00+08:00",
            "title": "2026年電器空調影音大展",
            "dates": {"start": "2026/11/06", "end": "2026/11/09"},
            "hours": {"open": "10:00", "close": "18:00"}, "hall": "世貿一館",
        }
        self.en = {
            "source_url": "https://www.twtc.com.tw/en/exhibition_More.aspx?id=29418&p=home",
            "language": "EN", "exhibition_id": "29418",
            "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
            "observed_at_utc": "2026-11-04T03:50:00+08:00",
            "title": "2025 ELECTRIC APPLIANCE FAIR",
            "dates": {"start": "2026/11/06", "end": "2026/11/09"},
            "hours": {"open": "10", "close": "18"}, "hall": "Hall 1",
        }

    def test_title_year_conflict_quarantined_but_matching_non_session_roles_reviewable(self):
        r = m.adjudicate_twtc_bilingual_same_id(self.cn, self.en)
        self.assertEqual(r["title_decision"], "HOLD_CROSS_LANGUAGE_TITLE_YEAR_CONFLICT")
        self.assertEqual(r["source_consistent_fields"], 3)
        self.assertEqual([x["field"] for x in r["field_matrix"]],
                         ["exhibition_dates", "open_hours", "venue_hall"])
        self.assertTrue(all(x["decision"] == "REVIEW_BILINGUAL_AGREEMENT_NOT_NATIVE"
                            and not x["formal_accepted"] for x in r["field_matrix"]))
        self.assertEqual((r["independent_formal_ready_fields"],
                          r["formal_accepted_fields"], r["golden_accepted_events"],
                          r["published_events"], r["formal_pwa_feed_events"]),
                         (0, 0, 0, 0, 0))
        self.assertEqual(r["source_freshness"], "READER_TIMESTAMP_NOT_NATIVE_ATTESTATION")
        self.assertEqual(r["release_state"], "HARD_HOLD_NO_PUBLICATION")

    def test_field_specific_mismatches_cannot_be_silently_reconciled(self):
        import copy
        for section, key, value, field in (
            ("dates", "end", "2026/11/10", "exhibition_dates"),
            ("hours", "close", "17", "open_hours"),
            ("hall", None, "Hall 2", "venue_hall"),
        ):
            with self.subTest(field=field):
                en = copy.deepcopy(self.en)
                if key is None: en[section] = value
                else: en[section][key] = value
                r = m.adjudicate_twtc_bilingual_same_id(self.cn, en)
                self.assertIn("HOLD", next(x["decision"] for x in r["field_matrix"]
                                           if x["field"] == field))
                self.assertEqual(r["formal_accepted_fields"], 0)

    def test_wrong_identity_source_or_unattested_clock_is_rejected(self):
        import copy
        for key, value in (
            ("exhibition_id", "29419"),
            ("source_url", "https://evil.example/en/exhibition_More.aspx?id=29418&p=home"),
            ("evidence_kind", "NATIVE_HTTP_200"),
            ("observed_at_utc", "2026-11-04T03:50:00"),
        ):
            with self.subTest(key=key):
                en = copy.deepcopy(self.en)
                en[key] = value
                with self.assertRaises(ValueError):
                    m.adjudicate_twtc_bilingual_same_id(self.cn, en)





    def test_executor_third_source_review_not_formal(self):
        agency = {
            "source_url": "https://www.sheng-dong.com.tw/activity/appliances-expo/TECO",
            "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
            "observed_at_utc": "2026-11-04T06:30:00+08:00",
            "event_label": "2026台北電器空調影音展",
            "organizer": "台北市電器商業同業公會",
            "executor": "生動國際展覽事業股份有限公司",
            "venue": "台北世貿一館",
            "dates": {"start": "2026/11/06", "end": "2026/11/09"},
            "hours": {"open": "10:00", "close": "18:00"},
        }
        r = m.adjudicate_twtc_executing_agency_public_crosscheck(self.cn,self.en,agency)
        self.assertEqual(r["source_count"],3)
        self.assertIn("NO_DIRECT_TWTC_ID",r["identity_decision"])
        self.assertIn("HOLD",r["title_decision"])
        self.assertEqual([x["field"] for x in r["field_matrix"]],
                         ["exhibition_dates","open_hours","venue_hall"])
        self.assertTrue(all(not x["formal_accepted"] for x in r["field_matrix"]))
        self.assertEqual((r["formal_accepted_fields"],r["golden_accepted_events"],
                          r["published_events"],r["formal_pwa_feed_events"]),(0,0,0,0))
        self.assertEqual(r["release_state"],"HARD_HOLD_NO_PUBLICATION")

    def test_executor_source_identity_role_and_clock_negatives(self):
        import copy
        agency = {
            "source_url": "https://www.sheng-dong.com.tw/activity/appliances-expo/TECO",
            "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
            "observed_at_utc": "2026-11-04T06:30:00+08:00",
            "event_label": "2026台北電器空調影音展",
            "organizer": "台北市電器商業同業公會",
            "executor": "生動國際展覽事業股份有限公司",
            "venue": "台北世貿一館",
            "dates": {"start": "2026/11/06", "end": "2026/11/09"},
            "hours": {"open": "10:00", "close": "18:00"},
        }
        for key,value in (
            ("source_url","https://untrusted.example/TECO"),
            ("event_label","2025台北電器展"),
            ("organizer","另一場主辦單位"),
            ("venue","南港展覽館"),
            ("dates",{"start":"2026/11/12","end":"2026/11/15"}),
            ("hours",{"open":"09:00","close":"18:00"}),
            ("observed_at_utc","2026-11-04T06:30:00"),
            ("observed_at_utc","2026-11-01T06:30:00+08:00"),
            ("evidence_kind","NATIVE_HTTP200"),
        ):
            with self.subTest(key=key,value=str(value)):
                candidate=copy.deepcopy(agency)
                candidate[key]=value
                with self.assertRaises(ValueError):
                    m.adjudicate_twtc_executing_agency_public_crosscheck(
                        self.cn,self.en,candidate)


class TWTCOrganizerCollisionGuard(unittest.TestCase):
    """April/November TWTC events share contact but must never share event identity."""
    def setUp(self):
        from datetime import datetime, timedelta, timezone
        import copy
        base = TWTCBilingualConflictAuthority()
        base.setUp()
        self.cn, self.en = copy.deepcopy(base.cn), copy.deepcopy(base.en)
        self.cn.update(organizer="台北市電器商業同業公會",
                       organizer_phone="886-2-25064871Ext26")
        self.en.update(organizer="TAIPEI ELECTRICAL COMMERCIAL ASSOCIATION",
                       organizer_phone="886-2-25064871Ext26")
        self.april = {
            "source_url": "https://www.twtc.com.tw/en/exhibition_More.aspx?id=29417&p=menu1",
            "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
            "observed_at_utc": "2026-11-04T07:30:00+08:00",
            "exhibition_id": "29417",
            "title": "THE 36TH TAIPEI ELECTRIC APPLIANCE FAIR",
            "organizer": "TAIPEI ELECTRICAL COMMERCIAL ASSOCIATION",
            "organizer_phone": "886-2-25064871Ext26",
            "dates": {"start": "2026/04/10", "end": "2026/04/13"},
            "hours": {"open": "10:00", "close": "18:00"},
        }
        self.now = datetime(2026, 11, 4, 7, 57, tzinfo=timezone(timedelta(hours=8)))

    def test_same_organizer_phone_is_explicit_negative_identity_edge(self):
        r = m.adjudicate_twtc_same_organizer_collision(
            self.cn, self.en, self.april, self.now)
        self.assertEqual(r["source_identity"], "NOVEMBER_29418_NOT_APRIL_29417")
        self.assertIn("REJECT", r["negative_identity_edge"])
        self.assertEqual(r["reviewable_non_session_fields"], 3)
        self.assertEqual((r["independent_formal_accepted_fields"],
                          r["golden_accepted_events"], r["published_events"],
                          r["formal_pwa_feed_events"]), (0, 0, 0, 0))
        self.assertEqual(r["release_state"], "HARD_HOLD_NO_PUBLICATION")

    def test_wrong_id_organizer_phone_dates_or_stale_clock_fail_closed(self):
        import copy
        for target, field, value in (
            ("april", "exhibition_id", "29418"),
            ("april", "source_url", "https://untrusted.example/id=29417"),
            ("april", "dates", {"start": "2026/11/06", "end": "2026/11/09"}),
            ("april", "organizer_phone", "886-2-25064871Ext27"),
            ("april", "title", "2025 ELECTRIC APPLIANCE FAIR"),
            ("april", "observed_at_utc", "2026-11-01T07:30:00+08:00"),
            ("cn", "organizer_phone", "886-2-25064871Ext27"),
            ("en", "organizer", "ANOTHER ORGANIZER"),
            ("en", "exhibition_id", "29417"),
        ):
            with self.subTest(target=target, field=field):
                cn, en, april = (copy.deepcopy(self.cn), copy.deepcopy(self.en),
                                 copy.deepcopy(self.april))
                {"cn": cn, "en": en, "april": april}[target][field] = value
                with self.assertRaises(ValueError):
                    m.adjudicate_twtc_same_organizer_collision(
                        cn, en, april, self.now)


class NativeArtifactIndependentAuthorityAudit(unittest.TestCase):
    """Artifact structure/freshness review cannot authenticate its ZIP or grant Golden."""
    def sample(self):
        from datetime import datetime, timezone
        a='https://www.tmc.taipei/tw/blog/show/2026SungNien-Yu'
        bl='https://twtc.com.tw/exhibition?p=home'
        bd='https://twtc.com.tw/exhibition_more.aspx?id=29418&p=home'
        ticket='https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2'
        title='2026年電器空調影音大展'
        cases=[
            ('A','direct_ticket_product','LOCAL_PURCHASE_ANCHOR_NOT_SESSION',a,{'product_id':'P1DF32E2','official_ticket_url':ticket}),
            ('A','venue_showtime','VENUE_SHOW_NOT_SALE',a,'2026/11/07 19:30'),
            ('A','venue_hall','VENUE_HALL',a,'臺北流行音樂中心 表演廳'),
            ('B','list_detail_identity','SAME_ROW_SAME_ID',bl,{'exhibition_id':'29418','same_row_title':title}),
            ('B','exhibition_title','EXACT_EVENT_TITLE',bd,title),
            ('B','exhibition_dates','EXHIBITION_DATE_NOT_SALE',bd,{'start':'2026/11/06','end':'2026/11/09'}),
            ('B','open_hours','DAILY_OPEN_HOURS_NOT_SHOWTIME',bd,{'open':'10:00','close':'18:00'}),
            ('B','venue_hall','EXHIBITION_HALL_NOT_TICKET_ID',bd,'世貿一館'),
        ]
        sources=[{'url':u,'observed_at_utc':'2026-11-03T19:54:40+00:00','http_status':200,
                  'sha256':h*64,'bytes':100,'decision':'NATIVE_PARSED_REVIEW_ONLY'}
                 for u,h in ((a,'a'),(bl,'b'),(bd,'c'))]
        by_url={x['url']:x for x in sources}
        receipts=[{'line':line,'field':field,'role':role,'event_id':'P1DF32E2' if line=='A' else '29418',
                   'source_url':url,'observed_at_utc':by_url[url]['observed_at_utc'],
                   'body_sha256':by_url[url]['sha256'],'native_same_session_match':True,
                   'observed_value':value,'value_basis':'EXACT_SOURCE_LOCAL_PATTERN_OR_ANCHOR',
                   'decision':'ACCEPTABLE_FOR_INDEPENDENT_GOLDEN_REVIEW_ONLY',
                   'formal_accepted':False} for line,field,role,url,value in cases]
        return {'kind':'P30_L7_NATIVE_SAME_SESSION_FIELD_MATRIX_V1',
                'request_count':3,'native_http_200':3,'acceptability_review':8,'hold':0,
                'raw_html_saved':False,'release_state':'HARD_HOLD_NO_PUBLICATION',
                'formal_accepted_fields':0,'golden':0,'published':0,
                'sources':sources,'field_receipts':receipts}
    def test_five_field_native_receipt_parity_still_holds_formal_authority(self):
        from datetime import datetime
        r=m.audit_native_same_session_field_matrix(
            self.sample(),datetime.fromisoformat('2026-11-04T04:55:00+08:00'))
        self.assertEqual((r['internally_consistent_native_sources'],
                          r['source_bound_review_fields']), (3,5))
        self.assertEqual(len(r['field_matrix']),5)
        self.assertEqual(r['identity_dependencies']['A_KHAM'],
                         'HOLD_KHAM_PRODUCT_DETAIL_NOT_NATIVE_FETCHED')
        self.assertIn('HOLD',r['independent_artifact_integrity'])
        self.assertIn('HOLD',r['bilingual_title'])
        self.assertEqual((r['formal_accepted_fields'],r['golden_accepted_events'],
                          r['published_events'],r['formal_pwa_feed_events']), (0,0,0,0))
        self.assertTrue(all(not x['formal_accepted'] for x in r['field_matrix']))
    def test_forged_stale_or_cross_event_native_receipts_fail_closed(self):
        import copy
        from datetime import datetime
        now=datetime.fromisoformat('2026-11-04T04:55:00+08:00')
        changes=(
            lambda x:x['field_receipts'][0].update(event_id='OTHER'),
            lambda x:x['field_receipts'][1].update(body_sha256='0'*64),
            lambda x:x['sources'][0].update(observed_at_utc='2026-11-01T00:00:00+00:00'),
            lambda x:x['field_receipts'][2].update(role='SALE'),
            lambda x:x['field_receipts'][5].update(observed_value={'start':'2026/11/12','end':'2026/11/15'}),
            lambda x:x['field_receipts'][1].update(field='direct_ticket_product'),
            lambda x:x['sources'][0].update(url='https://other.example/'),
            lambda x:x.update(formal_accepted_fields=1),
        )
        for i,mutate in enumerate(changes):
            with self.subTest(case=i):
                data=copy.deepcopy(self.sample()); mutate(data)
                r=m.audit_native_same_session_field_matrix(data,now)
                self.assertEqual(r['source_bound_review_fields'],0)
                self.assertTrue(r['decision'].startswith('HOLD'))
                self.assertEqual(r['formal_accepted_fields'],0)


class DownloadedNativeArtifactIntegrity(unittest.TestCase):
    """Verify actual ZIP-shaped evidence, but keep field and Golden acceptance locked."""
    def sample_zip(self):
        import hashlib, io, zipfile
        matrix=NativeArtifactIndependentAuthorityAudit().sample()
        head='1'*40
        payloads={
            'readiness.txt':f'head={head}\nformal_fields=0\ngolden=0\npublished=0\n'.encode(),
            'native_same_session_field_matrix.json':json.dumps(matrix,sort_keys=True).encode(),
            'field_subset_review_proposal.json':b'{}',
        }
        entries={
            '.github/workflows/eventradar_p30_l7_field_readiness.yml':'a'*64,
            'scripts/p30_l7_field_golden_readiness.py':'b'*64,
            'tests/p30/test_p30_l7_field_golden_readiness.py':'c'*64,
            'tests/p30/fixtures/p30_l7_prince_field_readiness.json':'d'*64,
        }
        for name,value in payloads.items():
            entries['evidence/'+name]=hashlib.sha256(value).hexdigest()
        payloads['SHA256SUMS.txt']=''.join(
            f'{h}  {name}\n' for name,h in entries.items()).encode()
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
            for name,value in payloads.items():z.writestr(name,value)
        data=stream.getvalue()
        return data,'sha256:'+hashlib.sha256(data).hexdigest(),head

    def test_valid_zip_integrity_cannot_grant_formal_fields(self):
        from datetime import datetime
        data,digest,head=self.sample_zip()
        r=m.audit_downloaded_native_artifact_zip(
            data,digest,head,datetime.fromisoformat('2026-11-04T04:55:00+08:00'))
        self.assertEqual((r['zip_sha256'],r['zip_crc'],r['evidence_member_hashes']),
                         ('PASS','PASS','PASS'))
        self.assertEqual(r['native_receipt_parity'],'PASS_INTERNAL_ONLY')
        self.assertEqual(r['independently_verified_evidence_members'],3)
        self.assertEqual(r['decision'],'ARTIFACT_INTEGRITY_PASS_FORMAL_AUTHORITY_HOLD')
        self.assertFalse(r['raw_source_html_verified'])
        self.assertFalse(r['code_files_in_zip_verified'])
        self.assertEqual((r['formal_accepted_fields'],r['golden_accepted_events'],
                          r['published_events'],r['formal_pwa_feed_events']),(0,0,0,0))

    def test_digest_head_stale_and_truncated_zip_fail_closed(self):
        from datetime import datetime
        import hashlib
        data,digest,head=self.sample_zip()
        now=datetime.fromisoformat('2026-11-04T04:55:00+08:00')
        cases=((data,'sha256:'+'0'*64,head,now),
               (data,digest,'2'*40,now),
               (data,digest,head,datetime.fromisoformat('2026-11-07T04:55:00+08:00')),
               (data[:-8],'sha256:'+hashlib.sha256(data[:-8]).hexdigest(),head,now))
        for i,args in enumerate(cases):
            with self.subTest(case=i):
                r=m.audit_downloaded_native_artifact_zip(*args)
                self.assertTrue(r['decision'].startswith('HOLD_'))
                self.assertEqual((r['formal_accepted_fields'],r['golden_accepted_events']),(0,0))


if __name__=="__main__":unittest.main()


class ExecutorSameDayVenueCollisionGuard(unittest.TestCase):
    """A separate public executor index lists three distinct events at one hall/date."""
    def setUp(self):
        from datetime import datetime, timedelta, timezone
        self.now = datetime(2026, 11, 4, 9, 55, tzinfo=timezone(timedelta(hours=8)))
        self.receipt = {
            "source_url": "https://www.sheng-dong.com.tw/",
            "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
            "observed_at_utc": "2026-11-04T09:40:00+08:00",
            "native_official_get": 0,
            "formal_accepted_fields": 0,
            "golden_accepted_events": 0,
            "published_events": 0,
            "events": [
                {"title": "2026台北電器空調影音大展｜超越雙11家電週年慶",
                 "start_date": "2026/11/06", "end_date": "2026/11/09",
                 "venue": "台北世貿一館", "twtc_exhibition_id": None,
                 "ticket_session_id": None},
                {"title": "台北Méng萌寵物用品展",
                 "start_date": "2026/11/06", "end_date": "2026/11/09",
                 "venue": "台北世貿一館", "twtc_exhibition_id": None,
                 "ticket_session_id": None},
                {"title": "2026玩轉文具暨手作創意展｜11/6-9世貿一館",
                 "start_date": "2026/11/06", "end_date": "2026/11/09",
                 "venue": "台北世貿一館", "twtc_exhibition_id": None,
                 "ticket_session_id": None},
            ],
        }

    def test_same_day_venue_is_not_event_identity(self):
        out = m.audit_executor_same_day_venue_collision(self.receipt, self.now)
        self.assertEqual(out["distinct_event_labels"], 3)
        self.assertFalse(out["shared_date_venue_is_unique_event_identity"])
        self.assertIsNone(out["twtc_id_29418_from_executor_index"])
        self.assertEqual(out["identity_decision"], "REJECT_DATE_VENUE_ONLY_CROSS_EVENT_MERGE")
        self.assertEqual(
            (out["independent_formal_accepted_fields"], out["golden_accepted_events"],
             out["published_events"], out["formal_pwa_feed_events"]), (0, 0, 0, 0))
        self.assertEqual(out["release_state"], "HARD_HOLD_NO_PUBLICATION")

    def test_cross_event_freshness_and_false_authority_refused(self):
        for key, value in (
            ("source_url", "https://twtc.com.tw/exhibition_more.aspx?id=29418&p=home"),
            ("evidence_kind", "NATIVE_HTTP200"),
            ("observed_at_utc", "2026-11-04T09:40:00"),
            ("observed_at_utc", "2026-11-02T09:40:00+08:00"),
            ("native_official_get", 1),
            ("formal_accepted_fields", 1),
            ("golden_accepted_events", 1),
            ("published_events", 1),
        ):
            changed = copy.deepcopy(self.receipt)
            changed[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    m.audit_executor_same_day_venue_collision(changed, self.now)
        for row_key, value in (
            ("title", self.receipt["events"][0]["title"]),
            ("start_date", "2026/11/07"),
            ("venue", "台北世貿二館"),
            ("twtc_exhibition_id", "29418"),
            ("ticket_session_id", "invented"),
        ):
            changed = copy.deepcopy(self.receipt)
            changed["events"][1][row_key] = value
            with self.subTest(row_key=row_key):
                with self.assertRaises(ValueError):
                    m.audit_executor_same_day_venue_collision(changed, self.now)
        changed = copy.deepcopy(self.receipt)
        changed["events"].pop()
        with self.assertRaises(ValueError):
            m.audit_executor_same_day_venue_collision(changed, self.now)


class TestTwtcOfficialHostMirrorReader(unittest.TestCase):
    """A second official TWTC host has the same id, not an independent executor event edge."""
    def setUp(self):
        from datetime import datetime, timezone, timedelta
        self.now = datetime(2026, 11, 4, 10, 55, tzinfo=timezone(timedelta(hours=8)))
        self.receipt = {
            "index_url": "https://twtc.org.tw/exhibition.aspx",
            "mirror_detail_url": "https://twtc.org.tw/exhibition_more.aspx?id=29418&p=home",
            "primary_detail_url": "https://www.twtc.com.tw/exhibition_more.aspx?id=29418&p=menu1",
            "organizer_url": "https://www.teca.org.tw/",
            "organizer_edge_scope": "ORGANIZER_HOMEPAGE_ONLY_NOT_EVENT_ID",
            "evidence_kind": "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE",
            "observed_date_taipei": "2026-11-04",
            "event_title": "2026年電器空調影音大展",
            "organizer": "台北市電器商業同業公會",
            "date_start": "2026/11/06",
            "date_end": "2026/11/09",
            "hours": "10:00 ~ 18:00",
            "venue": "世貿一館",
            "native_official_get": 0,
            "formal_accepted_fields": 0,
            "golden_accepted_events": 0,
            "published_events": 0,
            "formal_pwa_feed_events": 0,
        }

    def test_same_id_mirror_is_source_quality_not_formal_field(self):
        result = m.audit_twtc_official_same_id_host_mirror(self.receipt, self.now)
        self.assertEqual(result["same_id_official_host_pair"], 2)
        self.assertEqual(result["source_local_identity"], "REVIEW_CORROBORATED_SAME_TWTC_ID_29418")
        self.assertEqual(set(result["field_roles"].values()), {"REVIEW"})
        self.assertFalse(result["organizer_homepage_is_event_identity"])
        self.assertEqual(result["executor_to_twtc_id_edge"], "HOLD")
        self.assertEqual(result["english_title_year_conflict"], "HOLD")
        self.assertEqual(
            tuple(result[k] for k in ("native_official_get", "independent_formal_accepted_fields",
              "golden_accepted_events", "published_events", "formal_pwa_feed_events")),
            (0, 0, 0, 0, 0))
        self.assertEqual(result["release_state"], "HARD_HOLD_NO_PUBLICATION")

    def test_refuse_foreign_id_false_authority_stale_and_organizer_identity(self):
        cases = {
            "mirror_detail_url": "https://twtc.org.tw/exhibition_more.aspx?id=29417&p=home",
            "primary_detail_url": "https://www.twtc.com.tw/exhibition_more.aspx?id=29417&p=menu1",
            "index_url": "https://twtc.org.tw/exhibition_more.aspx?id=29418&p=home",
            "organizer_url": "https://www.sheng-dong.com.tw/",
            "organizer_edge_scope": "EVENT_ID_CONFIRMED",
            "evidence_kind": "NATIVE_HTTP200",
            "observed_date_taipei": "2026-11-03",
            "event_title": "2025 ELECTRIC APPLIANCE FAIR",
            "organizer": "生動國際展覽事業股份有限公司",
            "date_start": "2026/04/10",
            "date_end": "2026/11/08",
            "hours": "09:00 ~ 18:00",
            "venue": "世貿二館",
            "native_official_get": 1,
            "formal_accepted_fields": 1,
            "golden_accepted_events": 1,
            "published_events": 1,
            "formal_pwa_feed_events": 1,
        }
        for key, wrong in cases.items():
            with self.subTest(key=key):
                altered = copy.deepcopy(self.receipt)
                altered[key] = wrong
                with self.assertRaises(ValueError):
                    m.audit_twtc_official_same_id_host_mirror(altered, self.now)


class TestNativeOfficialLinkEdges(unittest.TestCase):
    """Native source-local links are stronger identity evidence, never formal acceptance."""

    def setUp(self):
        from datetime import datetime, timezone
        self.now = datetime(2026, 11, 4, 3, 55, tzinfo=timezone.utc)
        self.urls = (
            "https://www.tmc.taipei/tw/blog/show/2026SungNien-Yu",
            "https://twtc.org.tw/exhibition.aspx",
            "https://twtc.org.tw/exhibition_more.aspx?id=29418&p=home",
        )
        self.receipts = [
            {"url": url, "http_status": 200, "decision": "NATIVE_HTTP200_BODY_HASH_ONLY",
             "body_sha256": "a" * 64, "bytes": 100,
             "observed_at_utc": "2026-11-04T03:55:00+00:00"}
            for url in self.urls
        ]
        self.tmc = (
            '<article>小宇 宋念宇 《不，完美的人》 2026.11.07 19:30 '
            '活動地點 臺北流行音樂中心 表演廳'
            '<a href="https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2">'
            '購票連結</a></article>'
        )
        self.index = (
            '<table><tr><td>11/06 ~ 11/09</td>'
            '<td>2026年電器空調影音大展 '
            '<a href="/exhibition_more.aspx?id=29418&amp;p=home">more</a></td>'
            '<td>台北市電器商業同業公會</td></tr>'
            '<tr><td>11/06 ~ 11/09</td><td>另一個活動 '
            '<a href="/exhibition_more.aspx?id=29419&amp;p=home">more</a></td></tr></table>'
        )
        self.detail = (
            '<article>2026年電器空調影音大展 展覽館別：世貿一館 '
            '主辦單位：台北市電器商業同業公會 '
            '展出日期：2026/11/06 ~ 2026/11/09 '
            '展出時間：10:00 ~ 18:00</article>'
        )

    def audit(self, tmc=None, index=None, detail=None, receipts=None):
        return m.audit_native_source_link_edges(
            self.tmc if tmc is None else tmc,
            self.index if index is None else index,
            self.detail if detail is None else detail,
            self.receipts if receipts is None else receipts, self.now)

    def test_direct_source_links_not_checkout_or_formal_authority(self):
        result = self.audit()
        self.assertEqual(result["source_local_native_link_edges"], 2)
        self.assertEqual(result["A_venue_to_kham_product"], "REVIEW_DIRECT_ANCHOR_PRODUCT_NOT_SESSION")
        self.assertEqual(result["B_twtc_index_to_same_id_detail"], "REVIEW_DIRECT_SAME_ROW_ID29418")
        self.assertEqual(set(result["field_roles"].values()), {"REVIEW"})
        self.assertEqual(tuple(result[k] for k in
            ("formal_accepted_fields", "golden", "published", "formal_pwa_feed")), (0, 0, 0, 0))
        self.assertEqual(result["release_state"], "HARD_HOLD_NO_PUBLICATION")

    def test_exact_href_accepts_responsive_duplicate_and_image_only_label(self):
        duplicate = self.tmc.replace("</article>",
            '<a href="https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2">'
            '<img alt="票券"/></a></article>')
        self.assertEqual(self.audit(tmc=duplicate)["source_local_native_link_edges"], 2)

    def test_official_responsive_duplicate_row_not_a_second_event(self):
        first = self.index.split("</tr>")[0] + "</tr>"
        doubled = self.index.replace("</table>", first + "</table>")
        result = self.audit(index=doubled)
        self.assertEqual(result["source_local_native_link_edges"], 2)
        tripled = doubled.replace("</table>", first + "</table>")
        result = self.audit(index=tripled)
        self.assertEqual(result["source_local_native_link_edges"], 1)
        self.assertEqual(result["B_twtc_index_to_same_id_detail"],
                         "HOLD_SAME_ROW_OR_DETAIL_CONTEXT_UNPROVEN")

    def test_cross_event_link_wrong_id_or_false_ticket_anchor_refused(self):
        for tmc in (
            self.tmc.replace("P1DF32E2", "OTHER"),
            self.tmc.replace("<a ", "<span ").replace("</a>", "</span>"),
        ):
            with self.subTest(line="A"):
                with self.assertRaises(ValueError):
                    self.audit(tmc=tmc)
        for index, detail in (
            (self.index.replace("id=29418", "id=29417"), self.detail),
            (self.index.replace("11/06", "11/05"), self.detail),
            (self.index.replace("2026年電器空調影音大展", "另一個活動"), self.detail),
            (self.index, self.detail.replace("10:00", "09:00")),
        ):
            with self.subTest(line="B"):
                result = self.audit(index=index, detail=detail)
                self.assertEqual(result["source_local_native_link_edges"], 1)
                self.assertEqual(result["B_twtc_index_to_same_id_detail"],
                                 "HOLD_SAME_ROW_OR_DETAIL_CONTEXT_UNPROVEN")

    def test_fresh_native_receipt_is_required(self):
        for key, wrong in [
            ("url", "https://twtc.org.tw/exhibition_more.aspx?id=29417&p=home"),
            ("http_status", 403),
            ("decision", "PUBLIC_READER_TRANSCRIPTION_NOT_NATIVE"),
            ("body_sha256", "0" * 63),
            ("observed_at_utc", "2026-11-02T03:55:00Z"),
        ]:
            receipts = copy.deepcopy(self.receipts)
            receipts[2][key] = wrong
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    self.audit(receipts=receipts)


class TestFixedSourceAdapterToReviewPipeline(unittest.TestCase):
    """Executable LIST -> same-ID DETAIL -> five role receipts -> REVIEW LKG."""

    def setUp(self):
        from datetime import datetime, timezone
        self.now = datetime(2026, 11, 4, 4, 52, tzinfo=timezone.utc)
        self.stamp = "2026-11-04T04:50:00+00:00"
        self.btitle = "2026年電器空調影音大展"
        self.blist = ('<table><tr><td>11/06 ~ 11/09</td>'
                      '<td>' + self.btitle +
                      '<a href="/exhibition_more.aspx?id=29418&amp;p=home">詳情</a>'
                      '</td></tr></table>')
        self.bdetail = ('<h1>' + self.btitle + '</h1>'
                        '<p>展出日期：2026/11/06 ~ 2026/11/09</p>'
                        '<p>展出時間：10:00 ~ 18:00</p>'
                        '<p>展覽館別：世貿一館</p>')
        self.atitle = "小宇 宋念宇《不，完美的人》"
        self.alist = ('<a href="/tw/blog/show/2026SungNien-Yu">' +
                      self.atitle + '</a>')
        self.adetail = (
            '<h1>' + self.atitle + '</h1>'
            '<p>2026.11.07 19:30</p>'
            '<p>活動地點 臺北流行音樂中心 表演廳 主辦單位 小宇</p>'
            '<a href="https://kham.com.tw/application/UTK02/UTK0201_.aspx'
            '?PRODUCT_ID=P1DF32E2">購票連結</a>')

    def b(self, index=None, detail=None, previous=None, identity="29418"):
        return m.build_source_adapter_review_snapshot(
            m.PUBLIC_TWTC_LIST, self.blist if index is None else index,
            m.PUBLIC_TWTC_DETAIL, self.bdetail if detail is None else detail,
            self.btitle, identity, self.stamp, self.now, previous)

    def test_b_twtc_same_id_review_pipeline_with_daily_hours_sidecar(self):
        snap = self.b()
        self.assertEqual(snap["quality"]["previewRows"], 1)
        self.assertEqual(snap["quality"]["rejectedRows"], 0)
        self.assertEqual(snap["rows"][0]["_candidate"]["platform_id"], "16")
        self.assertEqual(snap["rows"][0]["date"], "2026/11/06 ~ 2026/11/09")
        self.assertEqual(snap["rows"][0]["location"], "世貿一館")
        self.assertEqual(len(snap["field_receipts"]), 3)
        self.assertEqual({f["field"] for f in snap["field_receipts"]},
                         {"exhibition_dates", "open_hours", "venue_hall"})
        self.assertEqual(snap["incremental_diff"]["added_ids"], [("16", "29418")])
        self.assertFalse(snap["native_get_verified"])
        self.assertEqual((snap["formal_accepted_fields"], snap["golden_accepted_events"],
                          snap["published_events"]), (0, 0, 0))
        self.assertEqual(snap["release_state"], "HARD_HOLD_NO_PUBLICATION")

    def test_a_tmc_exact_detail_and_kham_product_not_session(self):
        snap = m.build_source_adapter_review_snapshot(
            m.PUBLIC_TMC_LIST, self.alist, m.PUBLIC_TMC_DETAIL,
            self.adetail, self.atitle, "P1DF32E2", self.stamp, self.now)
        self.assertEqual(snap["quality"]["previewRows"], 1)
        self.assertEqual(snap["rows"][0]["_candidate"]["platform_id"], "TMC_OFFICIAL")
        self.assertEqual(snap["rows"][0]["_candidate"]["source_event_id"],
                         "2026SungNien-Yu")
        self.assertEqual(snap["rows"][0]["date"], "2026/11/07 19:30")
        self.assertEqual(len(snap["field_receipts"]), 2)
        self.assertIn("KHAM_PRODUCT_NOT_CHECKOUT_SESSION",
                      snap["rows"][0]["_candidate"]["hold_reasons"])
        self.assertEqual(snap["published_events"], 0)

    def test_empty_and_conflicting_scrape_roll_back_without_empty_feed(self):
        previous = self.b()
        for bad_index, bad_detail in (
            ("", self.bdetail),
            (self.blist.replace("29418", "29419"), self.bdetail),
            (self.blist, self.bdetail.replace("世貿一館", "世貿二館")
             .replace("展覽館別：世貿二館", "")),
        ):
            with self.subTest(bad_index=bad_index[:12]):
                restored = self.b(index=bad_index, detail=bad_detail,
                                  previous=previous)
                self.assertEqual(restored["decision"],
                                 "ROLLBACK_TO_ISOLATED_LAST_KNOWN_GOOD")
                self.assertEqual(restored["rows"], previous["rows"])
                self.assertFalse(restored["incremental_diff"]["changed"])
        with self.assertRaises(ValueError):
            self.b(index="")
        tampered = copy.deepcopy(previous)
        tampered["rows"][0]["title"] = "other event"
        with self.assertRaises(ValueError):
            self.b(previous=tampered)

    def test_exact_responsive_duplicate_collapses_but_cross_event_holds(self):
        # Two byte-equivalent mobile/desktop rows are ONE same-ID edge.
        same_row = self.blist.replace("<table>", "").replace("</table>", "")
        duplicated = "<table>" + same_row + same_row + "</table>"
        snap = self.b(index=duplicated)
        self.assertEqual(snap["quality"]["previewRows"], 1)
        self.assertEqual(snap["rows"][0]["_candidate"]["source_event_id"], "29418")
        # Nested semantic ancestors must not duplicate a child <tr> anchor.
        self.assertEqual(self.b(index="<article>" + self.blist +
                                "</article>")["quality"]["previewRows"], 1)
        # A different title-bearing row with the same ID is NOT a copy.
        conflict = duplicated.replace(
            same_row + "</table>",
            same_row.replace("11/06 ~ 11/09", "11/07 ~ 11/10") + "</table>")
        with self.assertRaisesRegex(ValueError, "AMBIGUOUS"):
            self.b(index=conflict)
        # Two distinct detail IDs inside a title-bearing row must fail closed.
        two_ids = self.blist.replace(
            "</td></tr>",
            '<a href="/exhibition_more.aspx?id=29419&amp;p=home">'
            'other</a></td></tr>')
        with self.assertRaisesRegex(ValueError, "CONFLICTING_DETAIL_IDS"):
            self.b(index=two_ids)
        with self.assertRaises(ValueError):
            self.b(identity="29417")


    def test_responsive_same_id_layout_variants_require_identical_detail_period(self):
        # Distinct desktop/mobile row wording must not create a second event.
        # Both title cells independently carry the exact same ID and dates.
        base = self.blist.replace("<table>", "").replace("</table>", "")
        mobile = base.replace("11/06 ~ 11/09",
                              "2026/11/06 ~ 2026/11/09").replace(
                                  "<td>2026/11/06", "<td>Mobile 2026/11/06")
        merged = "<table>" + base + mobile + "</table>"
        result = self.b(index=merged)
        self.assertEqual(result["quality"]["previewRows"], 1)
        self.assertEqual(result["rows"][0]["_candidate"]["source_event_id"],
                         "29418")
        self.assertEqual(result["formal_accepted_fields"], 0)
        # A different date context is NOT a responsive duplicate.
        changed = mobile.replace("2026/11/09", "2026/11/10")
        with self.assertRaisesRegex(ValueError, "RESPONSIVE_PERIOD_CONFLICT"):
            self.b(index="<table>" + base + changed + "</table>")
        # Even matching responsive rows cannot override official DETAIL dates.
        wrong_detail = self.bdetail.replace("2026/11/09", "2026/11/10")
        with self.assertRaisesRegex(ValueError, "RESPONSIVE_PERIOD_DETAIL_MISMATCH"):
            self.b(index=merged, detail=wrong_detail)

    def test_twtc_title_cell_local_edge_excludes_unrelated_sibling_cell(self):
        # A responsive row may contain a second unrelated event anchor.
        # The exact title+ID within ONE cell is authoritative for REVIEW;
        # no cross-cell or title-only fuzzy joining is permitted.
        html = ('<table><tr><td>' + self.btitle +
                '<a href="/exhibition_more.aspx?id=29418&amp;p=home">詳情</a>'
                '</td><td>另一場活動'
                '<a href="/exhibition_more.aspx?id=29419&amp;p=home">詳情</a>'
                '</td></tr></table>')
        snap = self.b(index=html)
        self.assertEqual(snap["rows"][0]["_candidate"]["source_event_id"], "29418")
        self.assertEqual(snap["quality"]["previewRows"], 1)
        self.assertEqual(snap["formal_accepted_fields"], 0)

    def test_twtc_title_cell_same_id_secondary_scope_is_not_second_event(self):
        # Native parser previously counted p=menu1 as a competing URL.
        # It is a different presentation scope, not a different event ID.
        html = ('<table><tr><td>' + self.btitle +
                '<a href="/exhibition_more.aspx?id=29418&amp;p=home">詳情</a>'
                '<a href="/exhibition_more.aspx?id=29418&amp;p=menu1">更多</a>'
                '</td></tr></table>')
        snap = self.b(index=html)
        self.assertEqual(snap["quality"]["previewRows"], 1)
        self.assertEqual(snap["rows"][0]["_candidate"]["source_event_id"],
                         "29418")
        self.assertEqual(snap["formal_accepted_fields"], 0)
        # A different event ID in the same cell remains an explicit HOLD.
        with self.assertRaisesRegex(ValueError, "CONFLICTING_DETAIL_IDS"):
            self.b(index=html.replace("id=29418&amp;p=menu1",
                                      "id=29419&amp;p=menu1"))
        # Secondary scope alone cannot establish the canonical p=home edge.
        with self.assertRaisesRegex(ValueError, "CONFLICTING_DETAIL_IDS"):
            self.b(index=html.replace(
                '<a href="/exhibition_more.aspx?id=29418&amp;p=home">詳情</a>',
                ''))

    def test_twtc_title_cell_conflict_or_cross_cell_ambiguity_holds(self):
        local_conflict = ('<table><tr><td>' + self.btitle +
                          '<a href="/exhibition_more.aspx?id=29418&amp;p=home">詳情</a>'
                          '<a href="/exhibition_more.aspx?id=29419&amp;p=home">另一詳情</a>'
                          '</td></tr></table>')
        with self.assertRaisesRegex(ValueError, "TITLE_CELL_CONFLICTING"):
            self.b(index=local_conflict)
        cross_cell = ('<table><tr><td>' + self.btitle +
                      '</td><td><a href="/exhibition_more.aspx?id=29418&amp;p=home">'
                      '詳情</a><a href="/exhibition_more.aspx?id=29419&amp;p=home">'
                      '另一詳情</a></td></tr></table>')
        with self.assertRaisesRegex(ValueError, "ROW_CONFLICTING"):
            self.b(index=cross_cell)

    def test_composite_responsive_parent_not_a_cross_event_row(self):
        # Real native failure was a title-bearing composite with other IDs.
        # A child <tr> must be the exact atomic same-ID authority, never its
        # ancestor <article> that also wraps unrelated event links.
        target = self.blist.replace("<table>", "").replace("</table>", "")
        unrelated = ('<tr><td>另一場活動</td><td><a '
                     'href="/exhibition_more.aspx?id=29419&amp;p=home">'
                     '詳情</a></td></tr>')
        nested = "<article><table>" + target + unrelated + "</table></article>"
        snap = self.b(index=nested)
        self.assertEqual(snap["quality"]["previewRows"], 1)
        self.assertEqual(snap["rows"][0]["_candidate"]["source_event_id"], "29418")
        # A title on an ancestor cannot be paired with an unrelated child link.
        cross_row = ('<article>' + self.btitle + '<tr><td><a '
                     'href="/exhibition_more.aspx?id=29418&amp;p=home">'
                     '詳情</a></td></tr></article>')
        with self.assertRaisesRegex(ValueError, "AMBIGUOUS"):
            self.b(index=cross_row)


class TestDurableIsolatedReviewLKG(unittest.TestCase):
    """Real tempfile atomic persistence, tamper detection and rollback."""

    def setUp(self):
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.destination = pathlib.Path(self.temp.name) / "review_lkg_snapshot.json"
        self.case = TestFixedSourceAdapterToReviewPipeline(
            "test_b_twtc_same_id_review_pipeline_with_daily_hours_sidecar")
        self.case.setUp()

    def run_b(self, index=None, detail=None):
        c = self.case
        return m.run_persistent_isolated_review_lkg(
            m.PUBLIC_TWTC_LIST, c.blist if index is None else index,
            m.PUBLIC_TWTC_DETAIL, c.bdetail if detail is None else detail,
            c.btitle, "29418", c.stamp, self.destination, ROOT, c.now)

    def test_atomic_write_reload_and_idempotent_diff(self):
        first = self.run_b()
        self.assertTrue(first["persisted"])
        self.assertEqual(first["snapshot"]["quality"]["previewRows"], 1)
        self.assertTrue(self.destination.is_file())
        old = m.load_isolated_review_lkg(self.destination, ROOT)
        self.assertEqual(old["last_known_good_sha256"],
                         first["snapshot"]["last_known_good_sha256"])
        second = self.run_b()
        self.assertTrue(second["persisted"])
        self.assertFalse(second["snapshot"]["incremental_diff"]["changed"])
        self.assertEqual(second["snapshot"]["incremental_diff"]["added_ids"], [])
        self.assertEqual(second["snapshot"]["formal_accepted_fields"], 0)
        self.assertEqual(second["snapshot"]["golden_accepted_events"], 0)
        self.assertEqual(second["snapshot"]["published_events"], 0)

    def test_empty_and_conflicting_source_preserve_exact_disk_bytes(self):
        self.run_b()
        before = self.destination.read_bytes()
        for index, detail in (
            ("", self.case.bdetail),
            (self.case.blist.replace("29418", "29419"), self.case.bdetail),
            (self.case.blist, "<h1>unrelated event</h1>"),
        ):
            with self.subTest(index=index[:15]):
                result = self.run_b(index, detail)
                self.assertFalse(result["persisted"])
                self.assertEqual(result["snapshot"]["decision"],
                                 "ROLLBACK_TO_ISOLATED_LAST_KNOWN_GOOD")
                self.assertEqual(self.destination.read_bytes(), before)
        self.assertFalse(self.destination.with_name(
            self.destination.name + ".lock").exists())

    def test_tamper_is_hold_never_auto_overwrite(self):
        self.run_b()
        bad = json.loads(self.destination.read_text(encoding="utf-8"))
        bad["snapshot"]["rows"][0]["title"] = "cross-event tampering"
        self.destination.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_b()
        self.assertEqual(json.loads(self.destination.read_text())["snapshot"]
                         ["rows"][0]["title"], "cross-event tampering")

    def test_cas_and_untrusted_release_flags_are_rejected(self):
        first = self.run_b()
        with self.assertRaisesRegex(ValueError, "COMPARE_AND_SWAP"):
            m.persist_isolated_review_lkg(
                first["snapshot"], self.destination, ROOT)
        bad = copy.deepcopy(first["snapshot"])
        bad["published_events"] = 1
        with self.assertRaises(ValueError):
            m.persist_isolated_review_lkg(
                bad, self.destination, ROOT,
                first["snapshot"]["last_known_good_sha256"])

    def test_forbidden_repo_path_and_missing_initial_input(self):
        with self.assertRaisesRegex(ValueError, "OUTSIDE_REPOSITORY"):
            m.run_persistent_isolated_review_lkg(
                m.PUBLIC_TWTC_LIST, self.case.blist, m.PUBLIC_TWTC_DETAIL,
                self.case.bdetail, self.case.btitle, "29418",
                self.case.stamp, ROOT / "docs" / "review_lkg_snapshot.json",
                ROOT, self.case.now)
        with self.assertRaises(ValueError):
            self.run_b(index="")
        self.assertFalse(self.destination.exists())

    def test_existing_lock_fails_closed(self):
        self.run_b()
        lock = self.destination.with_name(self.destination.name + ".lock")
        lock.write_text("another writer", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.run_b()
        self.assertEqual(lock.read_text(), "another writer")


class TestBoundedNativeToReviewLKG(unittest.TestCase):
    """No CI network: two explicit official URLs -> same-ID REVIEW disk LKG."""

    def setUp(self):
        import tempfile
        from datetime import datetime, timezone
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.destination = pathlib.Path(self.temp.name) / "review_lkg_snapshot.json"
        self.case = TestFixedSourceAdapterToReviewPipeline(
            "test_b_twtc_same_id_review_pipeline_with_daily_hours_sidecar")
        self.case.setUp()
        self.now = datetime(2026, 11, 4, 6, 55, tzinfo=timezone.utc)
        self.calls = []

    def fake(self, mapping, *, bad_status=None, bad_content_type=None):
        def fetch(url):
            self.calls.append(url)
            body = mapping[url].encode("utf-8")
            return (bad_status if bad_status and url == m.PUBLIC_TWTC_DETAIL
                    else 200,
                    bad_content_type if bad_content_type else
                    "text/html; charset=utf-8", body, url)
        return fetch

    def b(self, fetcher):
        c = self.case
        return m.run_bounded_native_source_to_review_lkg(
            m.PUBLIC_TWTC_LIST, m.PUBLIC_TWTC_DETAIL,
            c.btitle, "29418", self.destination, ROOT,
            fetcher=fetcher, now_utc=self.now)

    def test_b_two_bounded_gets_to_durable_same_id_review(self):
        c = self.case
        mapping = {m.PUBLIC_TWTC_LIST: c.blist,
                   m.PUBLIC_TWTC_DETAIL: c.bdetail}
        out = self.b(self.fake(mapping))
        self.assertTrue(out["persisted"])
        self.assertEqual(self.calls, [m.PUBLIC_TWTC_LIST, m.PUBLIC_TWTC_DETAIL])
        self.assertEqual(len(out["source_receipts"]), 2)
        self.assertEqual(len(out["snapshot"]["field_receipts"]), 3)
        self.assertEqual(out["snapshot"]["rows"][0]["_candidate"]
                         ["source_event_id"], "29418")
        self.assertFalse(out["native_get_verified"])
        self.assertEqual(out["source_receipts"][0]["transport"],
                         "TEST_INJECTED_NOT_NATIVE")
        self.assertEqual(out["formal_accepted_fields"], 0)
        self.assertEqual(out["published_events"], 0)
        self.assertEqual(out["release_state"], "HARD_HOLD_NO_PUBLICATION")
        durable = m.load_isolated_review_lkg(self.destination, ROOT)
        self.assertIsNotNone(durable)
        import hashlib
        acquired = durable["source_receipts"]["bounded_acquisition"]
        self.assertEqual(acquired["transport"], "TEST_INJECTED_NOT_NATIVE")
        self.assertEqual(acquired["list_url"], m.PUBLIC_TWTC_LIST)
        self.assertEqual(acquired["detail_url"], m.PUBLIC_TWTC_DETAIL)
        self.assertEqual(acquired["list_body_sha256"],
                         hashlib.sha256(c.blist.encode("utf-8")).hexdigest())
        self.assertEqual(acquired["detail_body_sha256"],
                         hashlib.sha256(c.bdetail.encode("utf-8")).hexdigest())
        self.assertFalse(durable["native_get_verified"])

    def test_a_two_gets_never_fetch_checkout_and_keep_product_hold(self):
        c = self.case
        mapping = {m.PUBLIC_TMC_LIST: c.alist,
                   m.PUBLIC_TMC_DETAIL: c.adetail}
        out = m.run_bounded_native_source_to_review_lkg(
            m.PUBLIC_TMC_LIST, m.PUBLIC_TMC_DETAIL,
            c.atitle, "P1DF32E2", self.destination, ROOT,
            fetcher=self.fake(mapping), now_utc=self.now)
        self.assertTrue(out["persisted"])
        self.assertEqual(self.calls, [m.PUBLIC_TMC_LIST, m.PUBLIC_TMC_DETAIL])
        self.assertTrue(all("kham.com.tw" not in url for url in self.calls))
        self.assertIn("KHAM_PRODUCT_NOT_CHECKOUT_SESSION",
                      out["snapshot"]["rows"][0]["_candidate"]["hold_reasons"])
        self.assertEqual(len(out["snapshot"]["field_receipts"]), 2)
        self.assertFalse(out["native_get_verified"])

    def test_http_failure_and_cross_id_keep_lkg_bytes_unchanged(self):
        c = self.case
        mapping = {m.PUBLIC_TWTC_LIST: c.blist,
                   m.PUBLIC_TWTC_DETAIL: c.bdetail}
        self.assertTrue(self.b(self.fake(mapping))["persisted"])
        prior = self.destination.read_bytes()
        failed = self.b(self.fake(mapping, bad_status=503))
        self.assertEqual(failed["decision"], "SOURCE_ACQUISITION_HOLD_NO_WRITE")
        self.assertEqual(self.destination.read_bytes(), prior)
        conflicting = dict(mapping)
        conflicting[m.PUBLIC_TWTC_LIST] = c.blist.replace("29418", "29419")
        result = self.b(self.fake(conflicting))
        self.assertFalse(result["persisted"])
        self.assertEqual(result["snapshot"]["decision"],
                         "ROLLBACK_TO_ISOLATED_LAST_KNOWN_GOOD")
        self.assertEqual(self.destination.read_bytes(), prior)

    def test_reject_checkout_redirect_non_html_and_implicit_network(self):
        c = self.case
        with self.assertRaisesRegex(ValueError, "EXACT_ALLOWLIST"):
            m.run_bounded_native_source_to_review_lkg(
                m.PUBLIC_TMC_LIST,
                "https://kham.com.tw/application/UTK02/UTK0201_.aspx"
                "?PRODUCT_ID=P1DF32E2",
                c.atitle, "P1DF32E2", self.destination, ROOT,
                fetcher=lambda _: None, now_utc=self.now)
        with self.assertRaisesRegex(ValueError, "EXPLICIT_NEW_HYPOTHESIS"):
            m.run_bounded_native_source_to_review_lkg(
                m.PUBLIC_TWTC_LIST, m.PUBLIC_TWTC_DETAIL,
                c.btitle, "29418", self.destination, ROOT)
        mapping = {m.PUBLIC_TWTC_LIST: c.blist,
                   m.PUBLIC_TWTC_DETAIL: c.bdetail}
        failed = self.b(self.fake(mapping, bad_content_type="application/json"))
        self.assertEqual(failed["decision"], "SOURCE_ACQUISITION_HOLD_NO_WRITE")
        self.assertFalse(self.destination.exists())

    def test_sealed_acquisition_receipt_cannot_rebind_identity_or_time(self):
        c = self.case
        mapping = {m.PUBLIC_TWTC_LIST: c.blist,
                   m.PUBLIC_TWTC_DETAIL: c.bdetail}
        self.assertTrue(self.b(self.fake(mapping))["persisted"])
        original = json.loads(self.destination.read_text(encoding="utf-8"))
        for key, bad in (
                ("list_url", "https://example.org/unrelated"),
                ("detail_url", m.PUBLIC_TWTC_DETAIL.replace("29418", "29419")),
                ("observed_at_utc", "2025-01-01T00:00:00+00:00"),
                ("list_body_sha256", "not-a-sha256")):
            with self.subTest(key=key):
                forged = copy.deepcopy(original)
                forged["snapshot"]["source_receipts"]["bounded_acquisition"][key] = bad
                # Rehash the envelope to prove semantic provenance validation
                # is independent of the envelope's byte-integrity check.
                forged["sha256"] = m._isolated_lkg_digest(forged["snapshot"])
                self.destination.write_text(
                    json.dumps(forged, ensure_ascii=False), encoding="utf-8")
                with self.assertRaisesRegex(
                        ValueError, "ISOLATED_LKG_ACQUISITION_PROVENANCE_HOLD"):
                    m.load_isolated_review_lkg(self.destination, ROOT)
        self.destination.write_text(
            json.dumps(original, ensure_ascii=False), encoding="utf-8")
        self.assertIsNotNone(m.load_isolated_review_lkg(self.destination, ROOT))


class TestTWTCNativeStructuralRootCauseAudit(unittest.TestCase):
    """Structural evidence is never a native same-ID/Golden acceptance."""

    def test_title_cell_exact_id_with_unrelated_sibling(self):
        html = ('<table><tr><td><a href="/exhibition_more.aspx?id=29418&p=home">'
                '2026年電器空調影音大展</a></td>'
                '<td><a href="/exhibition_more.aspx?id=99999&p=home">'
                'Other event</a></td></tr></table>')
        out = m.diagnose_twtc_title_row_structure(
            html, "2026年電器空調影音大展", "29418")
        self.assertEqual(out["root_cause_class"],
                         "TITLE_CELL_EXACT_ID_EDGE_HYPOTHESIS")
        self.assertEqual(out["title_cell_detail_ids"], ["29418"])
        self.assertEqual(out["atomic_row_detail_ids"], ["29418", "99999"])
        self.assertEqual(out["formal_accepted_fields"], 0)
        self.assertNotIn("Other event", json.dumps(out, ensure_ascii=False))

    def test_title_only_cell_mixed_ids_is_hold(self):
        html = ('<table><tr><td>2026年電器空調影音大展</td>'
                '<td><a href="/exhibition_more.aspx?id=29418&p=home">more</a>'
                '<a href="/exhibition_more.aspx?id=99999&p=home">'
                'other</a></td></tr></table>')
        out = m.diagnose_twtc_title_row_structure(
            html, "2026年電器空調影音大展", "29418")
        self.assertEqual(out["root_cause_class"],
                         "TITLE_ROW_MULTIPLE_IDS_WITHOUT_CELL_EDGE")
        self.assertEqual(out["title_cell_detail_ids"], [])
        self.assertEqual(out["formal_accepted_fields"], 0)

    def test_no_atomic_row_and_cross_source_refused(self):
        out = m.diagnose_twtc_title_row_structure(
            "<div>2026年電器空調影音大展</div>",
            "2026年電器空調影音大展", "29418")
        self.assertEqual(out["root_cause_class"],
                         "NO_ATOMIC_SEMANTIC_TITLE_ROW")
        with self.assertRaisesRegex(ValueError, "EXACT_SOURCE_ID_REQUIRED"):
            m.diagnose_twtc_title_row_structure(
                "<tr><td>2026年電器空調影音大展</td></tr>",
                "2026年電器空調影音大展", "29419")


class TestCKSMHCanonicalRotation(unittest.TestCase):
    """Canonical platform #17, exact actId; never ticket Session or publication."""
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = ROOT
        self.dest = pathlib.Path(self.tmp.name) / "review_lkg_snapshot.json"
        self.list_url = m.CKSMH_PUBLIC_LIST
        self.detail_url = m.CKSMH_PUBLIC_DETAIL
        self.list_html = ('<html><a href="/mocweb/reg/CKSMH/Detail.init.ctr?actId=61023">'
                          '「民主女路」走讀活動</a></html>')
        self.detail_html = ('<html><h1>「民主女路」走讀活動</h1>'
                            '<section>場次 2026/11/08 14:00，'
                            '2026/11/21 13:30；不同集合地點</section></html>')
    def run_rotation(self, list_html=None, detail_html=None, status=200):
        from datetime import datetime, timezone
        payloads = {self.list_url: self.list_html if list_html is None else list_html,
                    self.detail_url: self.detail_html if detail_html is None else detail_html}
        def fake(url):
            return (status, 'text/html; charset=utf-8', payloads[url].encode('utf-8'), url)
        return m.run_cksmh_actid_review_lkg(
            self.dest, self.repo, fetcher=fake, now_utc=datetime.now(timezone.utc))
    def test_existing_canonical_id_to_review_lkg_not_formal(self):
        out = self.run_rotation()
        self.assertEqual((out['decision'], out['same_id_review_lkg'],
                          out['native_get_200_count']), ('REVIEW_ONLY', 1, 0))
        snap = m.load_isolated_review_lkg(self.dest, self.repo)
        self.assertEqual(snap['rows'][0]['_candidate']['platform_id'], '17')
        self.assertEqual(snap['rows'][0]['_candidate']['source_event_id'], '61023')
        self.assertEqual(snap['rows'][0]['date'], '未確認')
        self.assertEqual(snap['rows'][0]['location'], '未確認')
        self.assertEqual(snap['rows'][0]['_candidate']['sessions'], [])
        self.assertEqual((snap['formal_accepted_fields'], snap['golden_accepted_events'],
                          snap['published_events']), (0, 0, 0))
        self.assertEqual(snap['source_receipts']['bounded_acquisition']['transport'],
                         'TEST_INJECTED_NOT_NATIVE')
    def test_foreign_actid_duplicate_title_and_wrong_detail_hold_without_write(self):
        ok = self.run_rotation()
        self.assertTrue(ok['persisted'])
        prior = self.dest.read_bytes()
        bad_cases = [
            dict(list_html='<a href="/mocweb/reg/CKSMH/Detail.init.ctr?actId=99999">「民主女路」走讀活動</a>'),
            dict(list_html=self.list_html + '<a href="/mocweb/reg/CKSMH/Detail.init.ctr?actId=123">「民主女路」走讀活動</a>'),
            dict(list_html='<a href="https://example.org/mocweb/reg/CKSMH/Detail.init.ctr?actId=61023">「民主女路」走讀活動</a>'),
            dict(detail_html='<h1>不同活動</h1>'),
            dict(status=403),
        ]
        for case in bad_cases:
            with self.subTest(case=case):
                result = self.run_rotation(**case)
                self.assertEqual(result['decision'], 'SOURCE_OR_IDENTITY_HOLD_NO_WRITE')
                self.assertFalse(result['persisted'])
                self.assertEqual(self.dest.read_bytes(), prior)
    def test_no_implicit_network_or_checkout(self):
        with self.assertRaises(ValueError):
            m.run_cksmh_actid_review_lkg(self.dest, self.repo)
        with self.assertRaises(ValueError):
            m.run_cksmh_actid_review_lkg(self.dest, self.repo, fetcher=123)



class TestTMCAuthorityContractAndHuashanRotation(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = pathlib.Path(self.tmp.name) / "review_lkg_snapshot.json"
        self.title = m.HUASHAN_ROTATION_TITLE
        self.index = '<a href="' + m.HUASHAN_PUBLIC_DETAIL + '">2026.11.07 ' + self.title + ' 西1館</a>'
        self.detail = '<h1>' + self.title + '</h1>'
    def run_huashan(self, index=None, detail=None, status=200):
        from datetime import datetime, timezone
        pages = {m.HUASHAN_PUBLIC_LIST: self.index if index is None else index,
                 m.HUASHAN_PUBLIC_DETAIL: self.detail if detail is None else detail}
        def fake(url):
            return status, "text/html; charset=utf-8", pages[url].encode(), url
        return m.run_huashan_exact_path_review_lkg(
            self.dest, ROOT, fetcher=fake, now_utc=datetime.now(timezone.utc))
    def test_a_no_native_snapshot_does_not_accept_fields(self):
        a = m.assess_tmc_non_session_field_authority(None)
        self.assertEqual(a["decision"], "HOLD_NO_SEALED_NATIVE_AUTHORITY")
        self.assertEqual((a["formal_accepted_fields"], a["published_events"]), (0, 0))
    def test_b_same_official_path_is_review_not_numeric_id(self):
        out = self.run_huashan()
        self.assertEqual((out["same_path_review_lkg"], out["native_same_numeric_id"]), (1, 0))
        snap = m.load_isolated_review_lkg(self.dest, ROOT)
        self.assertEqual(snap["rows"][0]["_candidate"]["platform_id"], "13")
        self.assertTrue(snap["rows"][0]["_candidate"]["source_event_id"].startswith("path-sha256-"))
        self.assertEqual(snap["rows"][0]["date"], "未確認")
    def test_b_cross_path_missing_link_wrong_h1_http_fail_closed(self):
        self.assertEqual(self.run_huashan()["decision"], "REVIEW_ONLY")
        old = self.dest.read_bytes()
        cases = [{"index": '<a href="/exhibition/other">' + self.title + '</a>'},
                 {"index": "<div>" + self.title + "</div>"},
                 {"detail": "<h1>另一個活動</h1>"},
                 {"status": 403}]
        for case in cases:
            with self.subTest(case=case):
                out = self.run_huashan(**case)
                self.assertEqual(out["decision"], "SOURCE_OR_IDENTITY_HOLD_NO_WRITE")
                self.assertEqual(self.dest.read_bytes(), old)
    def test_b_no_implicit_network(self):
        with self.assertRaises(ValueError):
            m.run_huashan_exact_path_review_lkg(self.dest, ROOT)


class TestHuashanOfficialDetailFieldRoles(unittest.TestCase):
    def setUp(self):
        from datetime import datetime,timezone
        self.observed="2026-11-04T13:59:00+00:00"
        self.now=datetime(2026,11,4,14,0,tzinfo=timezone.utc)
        self.html=('<h1>'+m.HUASHAN_ROTATION_TITLE+'</h1>'
          '<h3>活動時間：</h3>2026 11.07(六) 11.07(六) 11:00 ~ 16:30 '
          '西1館11:30開放 /西2館、西5-1館11:00開放 '
          '<h3>地點：</h3>西5-1館 壓縮兼包裝工場 / 西2館 第三乾餾場 / 西1館 第二乾餾場 '
          '<h3>主辦單位：</h3>測試主辦'
          '<footer>開放時間：每日09:30 ~ 21:00</footer>')
    def run_contract(self,html=None,source=None,sha=None,observed=None):
        import hashlib
        html=self.html if html is None else html
        return m.adjudicate_huashan_detail_field_roles(
            html,m.HUASHAN_PUBLIC_DETAIL if source is None else source,
            self.observed if observed is None else observed,
            hashlib.sha256(html.encode()).hexdigest() if sha is None else sha,
            now_utc=self.now)
    def test_four_event_local_roles_never_formal_or_numeric_id(self):
        r=self.run_contract()
        self.assertEqual(r["decision"],"REVIEW_FOUR_SOURCE_ROLES_INDEPENDENT_ACCEPTANCE_HOLD")
        self.assertEqual([f["field"] for f in r["field_matrix"]],
            ["event_date","event_public_hours","event_halls","hall_opening_exceptions"])
        self.assertEqual(r["field_matrix"][0]["value"],"2026-11-07")
        self.assertEqual((r["formal_accepted_fields"],r["golden_accepted_events"],
                          r["published_events"],r["same_numeric_event_id"]),(0,0,0,0))
    def test_split_date_weekday_nodes_still_bounded_and_review_only(self):
        # New DOM hypothesis: date and weekday are split across inline nodes.
        html=self.html.replace("11.07(六)","11.07 <span>(六)</span>")
        r=self.run_contract(html=html)
        self.assertEqual(r["decision"],"REVIEW_FOUR_SOURCE_ROLES_INDEPENDENT_ACCEPTANCE_HOLD")
        self.assertEqual(len(r["field_matrix"]),4)
    def test_wrong_source_time_hall_identity_sha_and_stale_hold(self):
        cases=[
          dict(html=self.html.replace("11.07(六)","11.08(日)",1)),
          dict(html=self.html.replace("11:00 ~ 16:30","09:30 ~ 21:00",1)),
          dict(html=self.html.replace("西1館11:30開放","西1館11:00開放",1)),
          dict(html=self.html.replace("西2館 第三乾餾場","西2館 其他場地",1)),
          dict(html=self.html.replace(m.HUASHAN_ROTATION_TITLE,"其他活動",1)),
          dict(source="https://example.org/other"),dict(sha="0"*64),
          dict(observed="2026-10-30T13:59:00+00:00"),
          dict(html="<h1>"+m.HUASHAN_ROTATION_TITLE+"</h1><footer>開放時間：每日09:30~21:00</footer>")]
        for case in cases:
            with self.subTest(case=case):
                r=self.run_contract(**case)
                self.assertEqual(r["decision"],"SOURCE_FIELD_SEMANTICS_HOLD")
                self.assertEqual(r["field_matrix"],[])
                self.assertEqual(r["formal_accepted_fields"],0)


class TestHuashanEmbeddedNumericIdentityHypothesis(unittest.TestCase):
    """New official JSON-LD hypothesis; never infer an ID from path or analytics."""

    def run_identity(self, nodes, url=None):
        body = '<h1>' + m.HUASHAN_ROTATION_TITLE + '</h1>'
        if nodes is not None:
            body += ('<script type="application/ld+json">' +
                     json.dumps(nodes, ensure_ascii=False) + '</script>')
        return m.inspect_huashan_embedded_event_identity(
            body, m.HUASHAN_PUBLIC_DETAIL if url is None else url)

    def test_exact_event_owned_numeric_identifier_is_review_not_same_id(self):
        report = self.run_identity({
            "@context": "https://schema.org", "@type": "Event",
            "url": m.HUASHAN_PUBLIC_DETAIL, "identifier": "12345"})
        self.assertEqual(report["decision"], "REVIEW_EMBEDDED_ID_NOT_LIST_BOUND")
        self.assertEqual(report["embedded_numeric_id_review"], "12345")
        self.assertEqual((report["same_numeric_event_id"],
                          report["formal_accepted_fields"],
                          report["golden_accepted_events"],
                          report["published_events"]), (0, 0, 0, 0))

    def test_unrelated_sitewide_event_and_local_path_hash_are_not_identity(self):
        unrelated = {"@type": "Event", "url": "https://www.huashan1914.com/other",
                     "identifier": "12345"}
        for nodes in (None, unrelated,
                      {"@type": "Event", "url": m.HUASHAN_PUBLIC_DETAIL,
                       "identifier": "path-sha256-12345"},
                      {"@type": "Event", "identifier": "12345"},
                      {"@type": "Event", "url": m.HUASHAN_PUBLIC_DETAIL,
                       "identifier": {"value": "12345"}},
                      {"@type": "Organization", "url": m.HUASHAN_PUBLIC_DETAIL,
                       "identifier": "12345"}):
            with self.subTest(nodes=nodes):
                r = self.run_identity(nodes)
                self.assertTrue(r["decision"].startswith("HOLD_"))
                self.assertIsNone(r["embedded_numeric_id_review"])

    def test_conflicting_event_ids_and_wrong_source_fail_closed(self):
        nodes = {"@graph": [
            {"@type": "Event", "url": m.HUASHAN_PUBLIC_DETAIL,
             "identifier": "12345"},
            {"@type": "Event", "url": m.HUASHAN_PUBLIC_DETAIL,
             "identifier": "99999"}]}
        self.assertTrue(self.run_identity(nodes)["decision"].startswith("HOLD_"))
        self.assertTrue(self.run_identity(
            {"@type": "Event", "url": m.HUASHAN_PUBLIC_DETAIL,
             "identifier": "12345"},
            "https://example.com/other")["decision"].startswith("HOLD_"))

    def test_invalid_json_and_oversize_are_holds(self):
        bad = m.inspect_huashan_embedded_event_identity(
            '<script type="application/ld+json">{bad</script>',
            m.HUASHAN_PUBLIC_DETAIL)
        self.assertTrue(bad["decision"].startswith("HOLD_"))
        self.assertTrue(self.run_identity(
            {"@type": "Event", "url": m.HUASHAN_PUBLIC_DETAIL,
             "identifier": "12345", "description": "X" * 530000}
        )["decision"].startswith("HOLD_"))


class TestTmcNativeAuthorityExpectedTitleParity(unittest.TestCase):
    """A first real failure was using a synthetic fixture H1 in a native probe."""

    def test_source_owned_official_title_parses_but_never_accepts(self):
        from datetime import datetime, timezone
        title = m.TMC_KHAM_FIELDS["venue_title"][3]
        self.assertNotEqual(title, "小宇 宋念宇《不，完美的人》")
        html = ('<h1>' + title + '</h1>'
                '<p>2026.11.07 19:30</p>'
                '<p>活動地點 臺北流行音樂中心 表演廳 主辦單位 小宇</p>'
                '<a href="https://kham.com.tw/application/UTK02/UTK0201_.aspx'
                '?PRODUCT_ID=P1DF32E2">購票連結</a>')
        observed = "2026-11-04T14:57:31+00:00"
        parsed = m.parse_official_non_session_html(
            m.PUBLIC_TMC_DETAIL, html, title, "P1DF32E2", observed,
            datetime(2026, 11, 4, 14, 58, tzinfo=timezone.utc))
        self.assertEqual([f["field"] for f in parsed["candidate_fields"]],
                         ["venue_showtime", "venue_hall"])
        with self.assertRaisesRegex(ValueError, "LIST_DETAIL_TITLE_IDENTITY_HOLD"):
            m.parse_official_non_session_html(
                m.PUBLIC_TMC_DETAIL, html, "小宇 宋念宇《不，完美的人》",
                "P1DF32E2", observed,
                datetime(2026, 11, 4, 14, 58, tzinfo=timezone.utc))


class TestSongshanCanonicalUUIDRotation(unittest.TestCase):
    """B #14 is an existing platform; LIST-owned UUID is not ticket Session."""

    def setUp(self):
        import tempfile
        from datetime import datetime, timezone
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = pathlib.Path(self.tmp.name) / "review_lkg_snapshot.json"
        self.now = datetime(2026, 11, 4, 15, 0, tzinfo=timezone.utc)
        self.uuid = m.SONGSHAN_EVENT_UUID
        self.title = m.SONGSHAN_EVENT_TITLE
        self.other = "11111111-2222-3333-4444-555555555555"
        self.listing = (
            '<div class="exhibition-card"><h3>' + self.title + '</h3>'
            '<a href="/exhibition/activity/' + self.uuid + '">看更多</a></div>'
            '<div class="exhibition-card"><h3>不同活動</h3>'
            '<a href="/exhibition/activity/' + self.other + '">看更多</a></div>')
        self.detail = ('<main><h1>' + self.title + '</h1>'
                       '<p>日期 2026-11-14 - 2026-11-22</p>'
                       '<p>地點 松山文創園區 藝異空間</p></main>')

    def run_source(self, listing=None, detail=None, status=200,
                   final_url=None):
        pages = {
            m.SONGSHAN_PUBLIC_LIST: self.listing if listing is None else listing,
            m.SONGSHAN_PUBLIC_DETAIL: self.detail if detail is None else detail}
        def fake(url):
            return (status, "text/html; charset=utf-8",
                    pages[url].encode("utf-8"), final_url or url)
        return m.run_songshan_uuid_review_lkg(
            self.dest, ROOT, fetcher=fake, now_utc=self.now)

    def test_exact_uuid_and_local_title_to_atomic_review_lkg(self):
        result = self.run_source()
        self.assertEqual(result["decision"], "REVIEW_ONLY")
        self.assertEqual(result["native_get_200_count"], 0)
        self.assertEqual(result["same_uuid_review_lkg"], 1)
        self.assertEqual(result["official_uuid"], self.uuid)
        snap = m.load_isolated_review_lkg(self.dest, ROOT)
        self.assertEqual(snap["rows"][0]["_candidate"]["platform_id"], "14")
        self.assertEqual(snap["rows"][0]["_candidate"]["source_event_id"], self.uuid)
        self.assertEqual(snap["rows"][0]["date"], "未確認")
        self.assertEqual(snap["source_receipts"]["bounded_acquisition"]["transport"],
                         "TEST_INJECTED_NOT_NATIVE")
        self.assertEqual((result["formal_accepted_fields"],
                          result["golden_accepted_events"],
                          result["published_events"]), (0, 0, 0))

    def test_exact_h3_with_nested_span_is_detail_owned(self):
        # Official-detail DOM hypothesis: H3 is a valid exact title heading,
        # not a global text match. This remains REVIEW-only and non-publishing.
        detail = ('<main><h1>展演資訊</h1><h3><span>' + self.title +
                  '</span></h3><p>日期 2026-11-14 - 2026-11-22</p></main>')
        result = self.run_source(detail=detail)
        self.assertEqual(result["decision"], "REVIEW_ONLY")
        self.assertEqual(result["same_uuid_review_lkg"], 1)
        self.assertEqual(result["formal_accepted_fields"], 0)

    def test_duplicate_h3_heading_remains_fail_closed(self):
        detail = ('<main><h2>' + self.title + '</h2><h3>' +
                  self.title + '</h3></main>')
        report = self.run_source(detail=detail)
        self.assertEqual(report["decision"], "SOURCE_OR_IDENTITY_HOLD_NO_WRITE")
        self.assertIn("SONGSHAN_DETAIL_EXACT_HEADING_HOLD", report["reason"])
        self.assertFalse(self.dest.exists())

    def test_unrelated_title_cannot_borrow_another_card_uuid(self):
        self.assertEqual(self.run_source()["decision"], "REVIEW_ONLY")
        before = self.dest.read_bytes()
        cases = [
            {"listing": '<div><h3>' + self.title + '</h3></div>'
                        '<div><a href="/exhibition/activity/' + self.uuid +
                        '">看更多</a></div>'},
            {"listing": '<div><h3>' + self.title + '</h3>'
                        '<a href="/exhibition/activity/' + self.other +
                        '">看更多</a></div>'},
            {"listing": '<div><h3>' + self.title + '</h3>'
                        '<a href="/exhibition/activity/' + self.uuid +
                        '">看更多</a><a href="/exhibition/activity/' +
                        self.other + '">其他</a></div>'},
            {"detail": "<h1>另一個活動</h1>"},
            {"detail": "<h1>" + self.title + "</h1><h2>" +
                       self.title + "</h2>"},
            {"status": 403},
            {"final_url": "https://example.com/redirect"}]
        for case in cases:
            with self.subTest(case=case):
                report = self.run_source(**case)
                self.assertEqual(report["decision"], "SOURCE_OR_IDENTITY_HOLD_NO_WRITE")
                self.assertEqual(report["same_uuid_review_lkg"], 0)
                self.assertEqual(self.dest.read_bytes(), before)

    def test_no_implicit_network_and_foreign_lkg_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "NEW_HYPOTHESIS"):
            m.run_songshan_uuid_review_lkg(self.dest, ROOT)
        with self.assertRaisesRegex(ValueError, "FETCHER_NOT_CALLABLE"):
            m.run_songshan_uuid_review_lkg(self.dest, ROOT, fetcher=123)
