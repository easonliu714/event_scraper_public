import copy,json,unittest
from scripts.p30_daily_publisher_dryrun import blob_sha,plan,verified_shape,identity
U="https://tpac.org.taipei/program/2040"
def row():
    e={"platform":"臺北表演藝術中心","source_event_id":"2040","url":U,
       "title":"士林YES！","date":"2026-11-20 19:30","price":"",
       "formal_field_pass":True,"_publication":{"source_body_sha256":{"detail":"a"*64}},
       "_formal_field_evidence":{}}
    for k,role in (("title","EVENT_TITLE"),("date","EVENT_SHOW_START")):
        e["_formal_field_evidence"][k]={"value":e[k],"role":role,"decision":"ACCEPTED",
           "event_id":"2040","source":U,"source_url":U,"observed_at":"2026-11-08T13:15:54+00:00"}
    return e
def feed():
    raw=(json.dumps([row()],ensure_ascii=False)+"\n").encode()
    return raw,blob_sha(raw)
class TestSafety(unittest.TestCase):
    def test_unchanged(self):
        raw,sha=feed(); p=plan(raw,[row()],sha)
        self.assertEqual((p["formal_rows_before"],p["formal_rows_after"]),(1,1))
        self.assertEqual(len(p["unchanged"]),1); self.assertFalse(p["commit_permitted"])
    def test_empty_lkg(self):
        raw,sha=feed(); p=plan(raw,[],sha)
        self.assertEqual(p["lkg_retained"],1); self.assertEqual(p["published_delta"],0)
    def test_cas(self):
        raw,_=feed()
        with self.assertRaisesRegex(ValueError,"CAS_MISMATCH"): plan(raw,[],"0"*40)
    def test_review(self):
        raw,sha=feed(); e=row(); e["formal_field_pass"]=False
        self.assertIn("REVIEW_ONLY",plan(raw,[e],sha)["rejected"][0]["reason"])
    def test_unaccepted_price(self):
        e=row(); e["price"]="NT$500 起"
        with self.assertRaisesRegex(ValueError,"UNACCEPTED_PRICE"): verified_shape(e)
    def test_accepted_general_price_shape_only_not_release(self):
        e=row(); e["price"]="NT$1,500 起"
        e["_formal_field_evidence"]["price"]={
            "accepted":True,"decision":"FIELD_ACCEPTED",
            "role":"EVENT_GENERAL_ADMISSION_MIN_PRICE",
            "price_kind":"GENERAL_NON_DISCOUNTED",
            "source":U,"source_url":U,"event_id":"2040",
            "value":e["price"],"source_body_sha256":"a"*64,
            "observed_at":"2026-11-08T13:15:54+00:00",
            "min_price_ntd":1500,"max_price_ntd":3500}
        self.assertEqual(verified_shape(e)["price"],"NT$1,500 起")
        raw,sha=feed(); p=plan(raw,[e],sha)
        self.assertFalse(p["commit_permitted"])
        e["_formal_field_evidence"]["price"]["price_kind"]="EARLY_BIRD"
        with self.assertRaisesRegex(ValueError,"UNACCEPTED_PRICE"):
            verified_shape(e)
    def test_same_numeric_id_in_two_namespaces_does_not_collapse(self):
        # Identity regression only: this fixture does NOT attest /event/2040 native existence.
        raw,sha=feed()
        e=row()
        e["url"]="https://tpac.org.taipei/event/2040"
        for field in ("title","date"):
            e["_formal_field_evidence"][field]["source"]=e["url"]
            e["_formal_field_evidence"][field]["source_url"]=e["url"]
        p=plan(raw,[row(),e],sha)
        self.assertEqual(p["shape_valid"],2)
        self.assertEqual(p["unchanged"],["臺北表演藝術中心:program:2040"])
        self.assertEqual(p["would_add"],["臺北表演藝術中心:event:2040"])
        self.assertFalse(p["commit_permitted"])
    def test_prior_namespace_collision_is_not_duplicate(self):
        a=row(); b=copy.deepcopy(a)
        b["url"]="https://tpac.org.taipei/event/2040"
        for field in ("title","date"):
            b["_formal_field_evidence"][field]["source"]=b["url"]
            b["_formal_field_evidence"][field]["source_url"]=b["url"]
        raw=(json.dumps([a,b],ensure_ascii=False)+"\n").encode()
        p=plan(raw,[],blob_sha(raw))
        self.assertEqual(p["formal_rows_before"],2)
        self.assertEqual(p["lkg_retained"],2)
        self.assertEqual(p["published_delta"],0)
    def test_namespace_id_url_mismatch_holds(self):
        e=row(); e["url"]="https://tpac.org.taipei/event/2041"
        with self.assertRaisesRegex(ValueError,"SOURCE_NAMESPACE_ID_HOLD"):
            verified_shape(e)
    def test_host_spoof(self):
        e=row(); e["url"]="https://tpac.org.taipei.evil.example/program/2040"
        with self.assertRaisesRegex(ValueError,"EXACT_OFFICIAL"): verified_shape(e)
    def test_event_id_conflict(self):
        e=row(); e["_formal_field_evidence"]["title"]["event_id"]="2041"
        with self.assertRaisesRegex(ValueError,"FIELD_TITLE_AUTHORITY"): verified_shape(e)
    def test_duplicate(self):
        raw,sha=feed(); p=plan(raw,[row(),row()],sha)
        self.assertEqual(p["shape_valid"],0)
    def test_body_sha(self):
        e=row(); e["_publication"]["source_body_sha256"]["detail"]="bad"
        with self.assertRaisesRegex(ValueError,"NATIVE_SHA"): verified_shape(e)
    def test_changed_still_hold(self):
        raw,sha=feed(); e=row(); e["date"]="2026-11-21 12:30"
        e["_formal_field_evidence"]["date"]["value"]=e["date"]
        p=plan(raw,[e],sha)
        self.assertEqual(len(p["would_change"]),1); self.assertFalse(p["commit_permitted"])
    def test_unregistered_adapter(self):
        e=row(); e["platform"]="UNKNOWN"
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_ADAPTER"): verified_shape(e)

    def test_historical_opentix_review_bridge_stays_review(self):
        # The ID is the historical OPENTIX #05 same-ID REVIEW, not a new GET.
        # Hashes below are test-only placeholders and never native attestation.
        event_id="2070446724700692480"
        e={"kind":"EVENTRADAR_AB_ISOLATED_REVIEW_BRIDGE_V1",
           "adapter_key":"A_OPENTIX","line":"A","source_id":"05",
           "source_event_id":event_id,"list_url":"https://www.opentix.life/",
           "detail_url":"https://www.opentix.life/event/"+event_id,
           "source_attestation":"CALLER_SUPPLIED_NOT_NATIVE",
           "decision":"REVIEW_ONLY_NOT_NATIVE",
           "release_state":"HARD_HOLD_NO_PUBLICATION",
           "native_get":0,"native_body_lkg":0,"formal_accepted_fields":0,
           "golden":0,"published":0,
           "observed_at_utc":"2026-11-08T00:00:00+00:00",
           "body_digests":{"list_sha256":"a"*64,"detail_sha256":"b"*64}}
        raw,sha=feed()
        p=plan(raw,[e],sha)
        self.assertEqual(p["review_only_count"],1)
        self.assertEqual(p["shape_valid"],0)
        self.assertEqual(p["would_add"],[])
        self.assertEqual(p["lkg_retained"],1)
        self.assertFalse(p["commit_permitted"])
        self.assertEqual(p["review_only"][0]["source_event_id"],event_id)
        self.assertEqual(p["review_only"][0]["decision"],"REVIEW_ONLY_NOT_NATIVE")
        for key,val in (("source_attestation","NATIVE_ATTESTED"),
                        ("native_get",1),("published",1)):
            bad=copy.deepcopy(e); bad[key]=val
            q=plan(raw,[bad],sha)
            self.assertEqual(q["review_only_count"],0)
            self.assertEqual(len(q["rejected"]),1)
        bad=copy.deepcopy(e); bad["candidate"]={"formal_field_pass":True}
        self.assertEqual(plan(raw,[bad],sha)["review_only_count"],0)

    def test_opentix_official_identity_registered_without_field_acceptance(self):
        event_id="2070446724700692480"
        e={"platform":"OPENTIX","source_event_id":event_id,
           "url":"https://www.opentix.life/event/"+event_id}
        self.assertEqual(identity(e),("OPENTIX","event",event_id))
        for url in ("https://www.opentix.life/program/"+event_id,
                    "https://www.opentix.life.evil.example/event/"+event_id):
            bad=copy.deepcopy(e);bad["url"]=url
            if "/program/" in url:
                with self.assertRaisesRegex(ValueError,"NAMESPACE_NOT_REGISTERED"):
                    identity(bad)
            else:
                with self.assertRaisesRegex(ValueError,"EXACT_OFFICIAL"):
                    verified_shape(bad)
        with self.assertRaisesRegex(ValueError,"REVIEW_ONLY_HOLD"):
            verified_shape(e)
if __name__=="__main__": unittest.main()
