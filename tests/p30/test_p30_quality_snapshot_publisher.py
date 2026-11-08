"""Publish-plan positive/negative/regression tests; synthetic evidence never publishes."""
import hashlib
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from scripts.p30_quality_snapshot_publisher import assess_packet, plan_replacement

NOW = datetime(2026,11,8,13,0,tzinfo=timezone.utc)
OBS = "2026-11-08T12:50:00Z"
LIST_URL = "https://example.org/events"
DETAIL_URL = "https://example.org/events/evt-123"
TITLE = "官方節目 2026"


def packet():
    listing='<main><article><a href="/events/evt-123">'+TITLE+'</a></article></main>'
    detail='<main><article><h1>'+TITLE+'</h1><time datetime="2026-11-21T19:30:00+08:00">11/21 19:30</time></article></main>'
    return {"platform":"官方測試來源", "source_event_id":"evt-123",
            "list_url":LIST_URL,"detail_url":DETAIL_URL,
            "list_html":listing,"detail_html":detail,
            "receipt":{"attestation":"NATIVE_SOURCE_REQUIRES_INDEPENDENT_READBACK",
                       "robots_allowed":True,"list_status":200,"detail_status":200,
                       "list_final_url":LIST_URL,"detail_final_url":DETAIL_URL,
                       "observed_at":OBS,
                       "list_sha256":hashlib.sha256(listing.encode()).hexdigest(),
                       "detail_sha256":hashlib.sha256(detail.encode()).hexdigest()}}


class QualityPublisherTests(unittest.TestCase):
    def assert_hold(self, changed, reason):
        x=assess_packet(changed,NOW)
        self.assertEqual(x["decision"],"HOLD",x)
        self.assertEqual(x["reason"],reason)

    def test_exact_same_id_event_article_and_future_role_is_stage_only(self):
        d=assess_packet(packet(),NOW)
        self.assertEqual(d["decision"],"QUALIFIED_PACKET_REQUIRES_INDEPENDENT_NATIVE_ATTESTATION")
        self.assertEqual(d["event"]["title"],TITLE)
        self.assertEqual(d["event"]["url"],DETAIL_URL)
        self.assertEqual(d["provenance"]["date_role"],"EVENT_START_NOT_SALE_OR_SESSION")
        self.assertEqual(d["event"]["date"],"2026-11-21T19:30:00+08:00")
        self.assertEqual(d["event"]["price"],"")
        self.assertNotIn("published",d["event"])

    def test_caller_only_review_must_not_be_promoted(self):
        p=packet()
        p["receipt"]["attestation"]="CALLER_SUPPLIED_NOT_NATIVE"
        self.assert_hold(p,"SOURCE_ATTESTATION_HOLD")

    def test_official_url_identity_and_first_party_protected(self):
        p=packet();p["source_event_id"]="evt-456"
        self.assert_hold(p,"SOURCE_ID_DETAIL_PATH_HOLD")
        p=packet();p["detail_url"]="https://other.example.org/events/evt-123"
        self.assert_hold(p,"FIRST_PARTY_HTTPS_HOLD")
        p=packet();p["receipt"]["detail_final_url"]="https://other.example.org/events/evt-123"
        self.assert_hold(p,"NATIVE_HTTP_ROBOTS_OR_REDIRECT_HOLD")

    def test_sha_stale_robots_and_http_gate(self):
        p=packet();p["detail_html"]+="<!-- drift -->"
        self.assert_hold(p,"SOURCE_BODY_SHA_HOLD")
        p=packet();p["receipt"]["observed_at"]="2026-11-05T11:00:00Z"
        self.assert_hold(p,"SOURCE_STALE_OR_FUTURE_HOLD")
        p=packet();p["receipt"]["robots_allowed"]=False
        self.assert_hold(p,"NATIVE_HTTP_ROBOTS_OR_REDIRECT_HOLD")
        p=packet();p["receipt"]["detail_status"]=403
        self.assert_hold(p,"NATIVE_HTTP_ROBOTS_OR_REDIRECT_HOLD")

    def test_date_title_role_ambiguity_fail_closed(self):
        p=packet()
        old=p["detail_html"]
        p["detail_html"]=old.replace('<time datetime="2026-11-21T19:30:00+08:00">11/21 19:30</time>',
                                     '<time datetime="2026-11-21T19:30:00+08:00">11/21</time><time datetime="2026-11-22T19:30:00+08:00">11/22</time>')
        p["receipt"]["detail_sha256"]=hashlib.sha256(p["detail_html"].encode()).hexdigest()
        self.assert_hold(p,"EVENT_LOCAL_TIME_ROLE_HOLD")
        p=packet()
        p["detail_html"]=p["detail_html"].replace(TITLE,"其他節目")
        p["receipt"]["detail_sha256"]=hashlib.sha256(p["detail_html"].encode()).hexdigest()
        self.assert_hold(p,"EXACT_ARTICLE_TITLE_IDENTITY_HOLD")
        p=packet()
        p["detail_html"]=p["detail_html"].replace("2026-11-21","2026-11-01")
        p["receipt"]["detail_sha256"]=hashlib.sha256(p["detail_html"].encode()).hexdigest()
        self.assert_hold(p,"PAST_OR_IMPLAUSIBLE_EVENT_HOLD")

    def test_inert_anchor_never_counts_as_direct_identity(self):
        p=packet()
        p["list_html"]='<main><template>'+p["list_html"]+'</template></main>'
        p["receipt"]["list_sha256"]=hashlib.sha256(p["list_html"].encode()).hexdigest()
        self.assert_hold(p,"EXACT_LIST_DETAIL_EDGE_HOLD")

    def test_plan_allows_legacy_retire_request_but_never_without_authority(self):
        p=packet()
        result=plan_replacement([p],now=NOW,legacy_count=8436,
                                source_collection_ok=True,
                                owner_allows_legacy_retirement=True)
        self.assertEqual(result["qualified_packet_count"],1)
        self.assertEqual(result["independently_accepted_events"],0)
        self.assertEqual(result["published_events"],0)
        self.assertEqual(result["legacy_rows"],8436)
        self.assertEqual(result["decision"],"HOLD_INDEPENDENT_FIELD_AUTHORITY_AND_RELEASE")
        self.assertFalse(result["formal_feed_mutated"])
        self.assertEqual(result["release_state"],"HARD_HOLD_NO_PUBLICATION")

    def test_all_rejected_and_source_failure_preserve_existing_snapshot(self):
        invalid=packet()
        invalid["receipt"]["list_status"]=500
        result=plan_replacement([invalid],now=NOW,legacy_count=8436,
                                source_collection_ok=True,
                                owner_allows_legacy_retirement=True)
        self.assertEqual(result["qualified_packet_count"],0)
        self.assertEqual(result["decision"],"HOLD_NO_QUALIFIED_EVENTS")
        self.assertEqual(result["published_events"],0)
        result=plan_replacement([packet()],now=NOW,legacy_count=8436,
                                source_collection_ok=False,
                                owner_allows_legacy_retirement=True)
        self.assertEqual(result["decision"],"HOLD_SOURCE_COLLECTION")
        result=plan_replacement([packet()],now=NOW,legacy_count=8436,
                                source_collection_ok=True,
                                owner_allows_legacy_retirement=False)
        self.assertEqual(result["decision"],"HOLD_NO_LEGACY_RETIREMENT_AUTHORIZATION")

    def test_duplicate_exact_source_is_quarantined(self):
        p=packet()
        result=plan_replacement([p,deepcopy(p)],now=NOW,legacy_count=8436,
                                source_collection_ok=True,
                                owner_allows_legacy_retirement=True)
        self.assertEqual(result["qualified_packet_count"],0)
        self.assertEqual(len(result["quarantined"]),2)
        self.assertEqual(result["decision"],"HOLD_NO_QUALIFIED_EVENTS")

    def test_no_write_to_repository_formal_feed(self):
        with tempfile.TemporaryDirectory() as d:
            formal=Path(d)/"docs"/"data.json"
            formal.parent.mkdir()
            formal.write_text('[{"original":true}]')
            before=formal.read_bytes()
            result=plan_replacement([packet()],now=NOW,legacy_count=8436,
                                    source_collection_ok=True,
                                    owner_allows_legacy_retirement=True)
            self.assertFalse(result["formal_feed_mutated"])
            self.assertEqual(formal.read_bytes(),before)


if __name__=="__main__":
    unittest.main()
