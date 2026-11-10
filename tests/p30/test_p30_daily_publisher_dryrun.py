import copy,json,unittest
from datetime import datetime,timedelta,timezone
from scripts.p30_daily_publisher_dryrun import blob_sha,plan,verified_shape,identity,rollback_manifest,verify_rollback_manifest,assess_refresh_request,validate_manual_isolated_request
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

    def test_versioned_diff_and_original_rollback_manifest(self):
        raw,sha=feed()
        p=plan(raw,[row()],sha)
        m=p["rollback_manifest"]
        self.assertEqual(m["base_git_blob"],sha)
        self.assertEqual(m["row_count"],1)
        self.assertFalse(m["storage_retention_attested"])
        self.assertFalse(m["commit_permitted"])
        self.assertTrue(verify_rollback_manifest(raw,m))
        self.assertEqual(p["versioned_diff"][0]["change"],"UNCHANGED")
        self.assertEqual(p["versioned_diff"][0]["authority"],
                         "SHAPE_ONLY_NOT_INDEPENDENTLY_ACCEPTED")
        self.assertEqual(p["versioned_diff"][0]["before_fields_sha256"],
                         p["versioned_diff"][0]["candidate_fields_sha256"])
        self.assertFalse(p["commit_permitted"])

    def test_versioned_diff_change_and_exact_rollback_guard(self):
        raw,sha=feed()
        e=row()
        e["date"]="2026-11-21 12:30"
        e["_formal_field_evidence"]["date"]["value"]=e["date"]
        p=plan(raw,[e],sha)
        self.assertEqual(p["versioned_diff"][0]["change"],"CHANGE")
        self.assertNotEqual(p["versioned_diff"][0]["before_fields_sha256"],
                            p["versioned_diff"][0]["candidate_fields_sha256"])
        self.assertTrue(verify_rollback_manifest(raw,p["rollback_manifest"]))
        altered=raw.replace("士林YES！".encode(), "士林NO！".encode())
        with self.assertRaisesRegex(ValueError,"ROLLBACK_BASE_CAS_HOLD"):
            verify_rollback_manifest(altered,p["rollback_manifest"])
        bad=copy.deepcopy(p["rollback_manifest"])
        bad["event_row_sha256"]["臺北表演藝術中心:program:2040"]="0"*64
        with self.assertRaisesRegex(ValueError,"ROLLBACK_MANIFEST_MISMATCH_HOLD"):
            verify_rollback_manifest(raw,bad)
        self.assertFalse(p["commit_permitted"])

class TestOnDemandRefreshPreflight(unittest.TestCase):
    """Gateway-only eligibility does not authorize a public browser dispatch."""

    def setUp(self):
        self.now=datetime(2026,11,10,9,0,tzinfo=timezone.utc)
        self.old=(self.now-timedelta(hours=26)).isoformat()
        self.last=(self.now-timedelta(hours=2)).isoformat()
        self.flags=dict(gateway_attested=True,claim_attested=True,
                        release_authorized=True)

    def test_eligible_only_after_all_trusted_attestations(self):
        p=assess_refresh_request({"last_success_at":self.old},self.now,
                                 **self.flags)
        self.assertEqual(p["decision"],"REQUEST_ELIGIBLE_NOT_DISPATCHED")
        self.assertTrue(p["request_eligible"])
        for key in ("dispatch_performed","publisher_executed",
                    "formal_write_performed","source_get_performed",
                    "schedule_enabled","source_rate_limits_checked"):
            self.assertFalse(p[key])

    def test_no_authority_never_dispatches(self):
        for flags,decision in (
            ({}, "HOLD_TRUSTED_GATEWAY_NOT_ATTESTED"),
            ({"gateway_attested":True},"HOLD_GLOBAL_CLAIM_NOT_ATTESTED"),
            ({"gateway_attested":True,"claim_attested":True},
             "HOLD_PUBLICATION_AUTHORITY")):
            with self.subTest(decision=decision):
                p=assess_refresh_request({"last_success_at":self.old},
                                          self.now,**flags)
                self.assertEqual(p["decision"],decision)
                self.assertFalse(p["request_eligible"])
                self.assertFalse(p["dispatch_performed"])

    def test_repeated_pwa_open_skips_fresh_and_active(self):
        fresh=(self.now-timedelta(minutes=10)).isoformat()
        self.assertEqual(assess_refresh_request(
            {"last_success_at":fresh},self.now,**self.flags
        )["decision"],"SKIP_DATA_FRESH")
        self.assertEqual(assess_refresh_request(
            {"running":True,"last_success_at":self.old},self.now,**self.flags
        )["decision"],"SKIP_ALREADY_RUNNING")

    def test_failed_last_attempt_cooldown(self):
        ago=(self.now-timedelta(minutes=20)).isoformat()
        p=assess_refresh_request({"last_success_at":self.old,
                                  "last_attempt_at":ago},self.now,**self.flags)
        self.assertEqual(p["decision"],"SKIP_RETRY_COOLDOWN")
        self.assertFalse(p["request_eligible"])
        p2=assess_refresh_request({"last_success_at":self.old,
                                   "last_attempt_at":self.last},
                                  self.now,**self.flags)
        self.assertTrue(p2["request_eligible"])

    def test_server_clock_and_receipt_fail_closed(self):
        badstatus=({"last_success_at":"2026-11-10 09:00"},
                   {"last_attempt_at":(self.now+timedelta(seconds=1)).isoformat()},
                   {"running":"false"},{"last_success_at":13})
        for status in badstatus:
            with self.subTest(status=status):
                with self.assertRaises(ValueError):
                    assess_refresh_request(status,self.now,**self.flags)
        with self.assertRaisesRegex(ValueError,"SERVER_TIMEZONE"):
            assess_refresh_request({},self.now.replace(tzinfo=None),**self.flags)
        with self.assertRaisesRegex(ValueError,"TRUSTED_INPUT"):
            assess_refresh_request([],self.now,**self.flags)

    def test_policy_bounds_and_boolean_authority(self):
        for kwargs in ({"ttl_seconds":0},{"retry_cooldown_seconds":0},
                       {"ttl_seconds":3600,"retry_cooldown_seconds":7200},
                       {"gateway_attested":"yes"},
                       {"claim_attested":1}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    assess_refresh_request({},self.now,**kwargs)


class TestManualIsolatedTransitionContract(unittest.TestCase):
    """No browser-provided request can authorize GET, dispatch or release."""
    def setUp(self):
        self.head = "a"*40
        self.formal = "b"*40
        self.request = {"mode":"ISOLATED_DRY_RUN",
                        "expected_head":self.head,
                        "expected_formal_blob":self.formal,
                        "requested_release":False}

    def evaluate(self, request):
        return validate_manual_isolated_request(
            request, trusted_head=self.head,
            trusted_formal_blob=self.formal)

    def test_pinned_dryrun_never_executes(self):
        result = self.evaluate(self.request)
        self.assertEqual(result["decision"],
            "READY_FOR_SEPARATELY_AUTHORIZED_MANUAL_DRY_RUN_ONLY")
        for key in ("dispatch_performed", "publisher_executed",
                    "formal_write_performed", "source_get_performed",
                    "schedule_enabled", "release_authorized"):
            self.assertFalse(result[key])

    def test_mismatched_head_or_formal_blob_holds(self):
        for key in ("expected_head", "expected_formal_blob"):
            bad = dict(self.request)
            bad[key] = "0"*40
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "STALE_"):
                    self.evaluate(bad)

    def test_public_or_release_input_holds(self):
        for bad in (
            dict(self.request, requested_release=True),
            dict(self.request, mode="PUBLISH"),
            dict(self.request, github_token="secret"),
            dict(self.request, schedule="0 0 * * *"),
            dict(self.request, expected_head="a"*39),
            dict(self.request, requested_release=0),
        ):
            with self.subTest(bad=sorted(bad)):
                with self.assertRaises(ValueError):
                    self.evaluate(bad)

if __name__=="__main__": unittest.main()
