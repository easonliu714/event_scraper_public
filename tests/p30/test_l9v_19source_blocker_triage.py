#!/usr/bin/env python3
"""P30-L9-V offline fail-closed contracts; no live network in tests."""
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

PATH = Path(__file__).resolve().parents[2] / "scripts/p30_l9v_19source_blocker_triage.py"
spec = importlib.util.spec_from_file_location("l9v", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

NAMES = [
    "KKTIX", "ACCUPASS", "拓元售票", "寬宏", "OPENTIX", "UDN售票網",
    "FamiTicket", "年代售票", "TixFun售票網", "Event Go", "BeClass",
    "ibon", "華山1914", "松山文創", "KidsClub", "台北世貿",
    "中正紀念堂", "iNDIEVOX", "StrollTimes",
]
CODES = [403,200,403,200,200,200,200,200,200,200,403,200,200,200,200,200,200,200,200]
LISTS = [0,25,0,0,40,6,40,28,24,38,0,0,7,1,33,0,0,19,3]
MATCHES = [0,0,0,0,1,1,0,0,0,1,0,0,1,0,0,0,0,1,0]
DETAILS = [0 if n==0 else 1 for n in LISTS]
INDEPENDENT = {"ibon", "台北世貿", "中正紀念堂"}

def rows():
    a, b = [], []
    for i, name in enumerate(NAMES):
        a.append({"id": f"{i+1:02d}", "platform": name,
                  "baseline": {"httpStatus": CODES[i], "listCandidates": LISTS[i],
                               "detailAttempted": DETAILS[i], "detailTitleMatches": MATCHES[i]},
                  "independentGate": {"gate":"separate"} if name in INDEPENDENT else None})
        b.append({"platform": name, "http": {"httpStatus": CODES[i], "redirectTrail": []},
                  "listCandidateCount": LISTS[i], "detailAttempted": DETAILS[i],
                  "detailIdentityVerified": MATCHES[i]})
    return a,b

def sample_probe():
    return {"platform":"BeClass","requested":1,"followedRedirects":0,
            "responseHTTP":403,"state":"HOLD_HTTP403","redirectClass":"NONE",
            "observedAtUTC":"2026-10-29T00:00:00Z",
            "rawBodySaved":False,"rawUrlSaved":False}

class FakeResponse:
    def __init__(self, status, location=None):
        self.status = status
        self.headers = {"Location": location} if location else {}
        self.body_read = False
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self):
        self.body_read = True
        raise AssertionError("must not read raw source body")

class FakeOpener:
    def __init__(self, response):
        self.response, self.calls, self.request = response, 0, None
    def open(self, request, timeout):
        self.calls += 1
        self.request = request
        assert timeout == 9
        return self.response

class Tests(unittest.TestCase):
    def test_01_exact_19_names_unique(self):
        self.assertEqual(len(NAMES),len(set(NAMES)))
        self.assertEqual(len(NAMES),19)
    def test_02_http_tiers_are_16_3(self):
        self.assertEqual(CODES.count(200),16)
        self.assertEqual(CODES.count(403),3)
    def test_03_list_count_264(self):
        self.assertEqual(sum(LISTS),264)
    def test_04_detail_match_count_5(self):
        self.assertEqual(sum(MATCHES),5)
    def test_05_blocked_kktix(self):
        a,b=rows();self.assertEqual(m.classify(a[0],b[0])["bucket"],m.BUCKETS[0])
    def test_06_blocked_tixcraft(self):
        a,b=rows();self.assertEqual(m.classify(a[2],b[2])["bucket"],m.BUCKETS[0])
    def test_07_blocked_beclass(self):
        a,b=rows();self.assertEqual(m.classify(a[10],b[10])["bucket"],m.BUCKETS[0])
    def test_08_200_zero_kham(self):
        a,b=rows();self.assertEqual(m.classify(a[3],b[3])["bucket"],m.BUCKETS[1])
    def test_09_200_zero_ibon_has_independent(self):
        a,b=rows();self.assertEqual(m.classify(a[11],b[11])["bucket"],m.BUCKETS[2])
    def test_10_200_zero_twtc_has_independent(self):
        a,b=rows();self.assertEqual(m.classify(a[15],b[15])["bucket"],m.BUCKETS[2])
    def test_11_200_zero_cksmh_has_independent(self):
        a,b=rows();self.assertEqual(m.classify(a[16],b[16])["bucket"],m.BUCKETS[2])
    def test_12_positive_list_identity_hold(self):
        a,b=rows();self.assertEqual(m.classify(a[1],b[1])["bucket"],m.BUCKETS[3])
    def test_13_positive_list_field_hold(self):
        a,b=rows();self.assertEqual(m.classify(a[4],b[4])["bucket"],m.BUCKETS[4])
    def test_14_unsupported_status_fail_closed(self):
        a,b=rows();a[0]["baseline"]["httpStatus"]=302
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_HTTP"):
            m.classify(a[0],b[0])
    def test_15_original_redirect_code_only(self):
        a,b=rows()
        b[10]["http"]["redirectTrail"]=[
            {"url":"https://www.beclass.com/secret?q=private","httpStatus":302},
            {"url":"https://www.beclass.com/other","httpStatus":403}]
        out=m.classify(a[10],b[10])
        self.assertEqual(out["originalRedirectCodes"],[302])
        self.assertNotIn("secret",json.dumps(out))
    def test_16_matrix_all_19_and_hard_hold(self):
        a,b=rows();r=m.build_report(a,b,sample_probe())
        self.assertEqual(len(r["matrix"]),19)
        self.assertEqual(sum(r["counts"].values()),19)
        self.assertEqual(r["releaseState"],m.RELEASE)
        self.assertEqual(r["goldenAccepted"],0)
        self.assertFalse(r["published"])
    def test_17_bucket_counts(self):
        a,b=rows();r=m.build_report(a,b,sample_probe())
        self.assertEqual([r["counts"][k] for k in m.BUCKETS],[3,1,3,7,5])
    def test_18_no_false_root_cause_proof(self):
        a,b=rows();r=m.build_report(a,b,sample_probe())
        self.assertTrue(all(not x["sourceCauseProven"] and
                            not x["freshSourceReverified"] for x in r["matrix"]))
    def test_19_probe_count_tamper_fail_closed(self):
        a,b=rows();p=sample_probe();p["requested"]=2
        with self.assertRaisesRegex(ValueError,"PROBE_SCOPE"):
            m.build_report(a,b,p)
    def test_20_redirect_same_site(self):
        self.assertEqual(m.redirect_class("/other?secret=1"),"SAME_SITE_HTTPS_NOT_FOLLOWED")
    def test_21_redirect_external_never_follow(self):
        self.assertEqual(m.redirect_class("https://evil.example/x"),"OFFSITE_NOT_FOLLOWED")
    def test_22_redirect_http_downgrade(self):
        self.assertEqual(m.redirect_class("http://www.beclass.com/"),"NON_HTTPS_HOLD")
    def test_23_redirect_missing_location(self):
        self.assertEqual(m.redirect_class(""),"MISSING_LOCATION")
    def test_24_redirect_credentials_rejected(self):
        self.assertEqual(m.redirect_class("https://user:pass@beclass.com/"),"UNSAFE_TARGET_HOLD")
    def test_25_probe_200_no_list_claim(self):
        fake=FakeResponse(200);op=FakeOpener(fake)
        r=m.probe_beclass(op)
        self.assertEqual(r["state"],"HTTP200_REACHABLE_LIST_UNVERIFIED")
        self.assertEqual(op.calls,1)
        self.assertFalse(fake.body_read)
    def test_26_probe_302_no_follow_no_url(self):
        fake=FakeResponse(302,"https://beclass.com/landing?secret=1")
        op=FakeOpener(fake);r=m.probe_beclass(op)
        self.assertEqual(r["state"],"HOLD_REDIRECT_NOT_FOLLOWED")
        self.assertEqual(r["redirectClass"],"SAME_SITE_HTTPS_NOT_FOLLOWED")
        self.assertEqual(op.calls,1)
        self.assertNotIn("landing",json.dumps(r))
    def test_27_probe_http_error_403(self):
        error=HTTPError(m.BECLASS_URL,403,"Forbidden",{},io.BytesIO(b"private"))
        op=FakeOpener(error);r=m.probe_beclass(op)
        self.assertEqual(r["state"],"HOLD_HTTP403")
        self.assertEqual(op.calls,1)
    def test_28_probe_http_error_429_no_retry(self):
        error=HTTPError(m.BECLASS_URL,429,"Too Many",{},io.BytesIO(b"private"))
        op=FakeOpener(error);r=m.probe_beclass(op)
        self.assertEqual(r["state"],"HOLD_HTTP429_NO_RETRY")
        self.assertEqual(op.calls,1)
    def test_29_sha_and_git_blob(self):
        self.assertEqual(m.sha256(b"abc"),hashlib.sha256(b"abc").hexdigest())
        self.assertEqual(m.git_blob(b"abc"),hashlib.sha1(b"blob 3\0abc").hexdigest())
    def test_30_status_sha_mismatch_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"STATUS_BLOB"):
            m.validate({},b"{}",{},b"{}",{})
    def test_31_no_unpinned_l7b_report(self):
        with self.assertRaisesRegex(ValueError,"L7B_REPORT_SHA"):
            m.validate({},b"{}",{},b"{}",{})
    def test_32_isolated_artifact_and_sha(self):
        a,b=rows();r=m.build_report(a,b,sample_probe())
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            man=m.emit(r,temp)
            raw=(Path(temp)/"blocker_matrix.json").read_bytes()
            self.assertEqual(man["filesSHA256"]["blocker_matrix.json"],m.sha256(raw))
            self.assertEqual(json.loads(raw)["goldenAccepted"],0)
    def test_33_reject_production_output_path(self):
        a,b=rows();r=m.build_report(a,b,sample_probe())
        for path in ("docs/p30-l9v", "scripts/p30-l9v", ".git/tmp", ".github/tmp"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError,"ISOLATED"):
                    m.emit(r,path)
    def test_34_no_raw_url_html_in_report(self):
        a,b=rows();r=m.build_report(a,b,sample_probe())
        data=json.dumps(r,ensure_ascii=False)
        self.assertNotIn("https://",data)
        self.assertNotIn("<html",data)
        self.assertEqual(r["freshSourcesProbed"],1)
        self.assertEqual(r["otherSourcesReprobed"],0)

if __name__=="__main__":
    unittest.main()
