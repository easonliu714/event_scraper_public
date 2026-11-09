"""Owner TPAC-R4 policy regression; all bytes are synthetic OFFLINE, no GET."""
import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from scripts.p30_tpac_r4_source_policy import (
    CLAIM_HOLD, MAX_REQUESTS, MIN_INTERVAL_SECONDS, RequestBudget,
    assert_no_untrusted_live_authority, enforce_elapsed,
    review_two_catalog_plan, stop_on_response,
)

NOW = datetime(2026, 11, 9, 9, 35, tzinfo=timezone.utc)
P_URL = "https://tpac.org.taipei/program"
E_URL = "https://tpac.org.taipei/event"
ROBOT_URL = "https://tpac.org.taipei/robots.txt"
ROBOT_ALLOW = b"User-agent: *\nAllow: /program\nAllow: /event\nCrawl-delay: 4\n"


def program():
    return (b'<main><a class="card-program" href="/program/1301"'
            b' title="Concert ABC"><span class="card-program__text-title">'
            b'Concert ABC</span><span class="card-program__text-date">'
            b'2026-11-11 - 2026-12-31</span></a></main>')


def event():
    return ('<main><a class="card-event" href="/event/1301"'
            ' title="連結到展覽 ABC"><div class="card-event__text-title">'
            '展覽 ABC</div><div class="card-event__text-datecate">'
            '<p>2026-11-11 - 2026-12-31</p><p>展覽</p></div>'
            '</a></main>').encode("utf-8")


def receipt(url, raw):
    return dict(http_status=200, final_url=url, robots_allowed=True,
                body_sha256=hashlib.sha256(raw).hexdigest(),
                body_bytes=len(raw),
                observed_at=(NOW-timedelta(minutes=5)).isoformat())


def inputs(**changes):
    p, e = program(), event()
    data = dict(cycle_id="tpac-r4-20261109-173500-a1b2c3d4",
                start_at=NOW,
                previous_claim_at=NOW-timedelta(hours=6),
                robots=ROBOT_ALLOW,
                program_body=p, program_receipt=receipt(P_URL, p),
                event_body=e, event_receipt=receipt(E_URL, e),
                attempts=())
    data.update(changes)
    return data


class TPACR4OwnerPolicyTests(unittest.TestCase):
    def test_exact_owner_budget_is_frozen_and_shared_across_both_catalogs(self):
        b = RequestBudget()
        self.assertEqual(b.interval_seconds, MIN_INTERVAL_SECONDS)
        self.assertEqual((b.robots, b.program_list, b.event_list, b.detail_total),
                         (1, 1, 1, 2))
        self.assertEqual(b.concurrency, 1)
        self.assertEqual(b.stop_http, (403,429))
        self.assertEqual(MAX_REQUESTS, 5)
        with self.assertRaises(FrozenInstanceError):
            b.detail_total=5
        with self.assertRaisesRegex(ValueError, "OWNER_BUDGET_IMMUTABLE_HOLD"):
            RequestBudget(detail_total=3)

    def test_two_catalogs_distinct_identity_even_same_numeric_id_and_no_live_get(self):
        plan=review_two_catalog_plan(**inputs())
        self.assertEqual(plan["decision"], CLAIM_HOLD)
        self.assertEqual(plan["detail_source_identities"],
                         ["tpac:program:1301","tpac:event:1301"])
        self.assertEqual(plan["source_lists"], {"program":1,"event":1})
        self.assertEqual(plan["request_urls_for_future_authorized_cycle"], [
            ROBOT_URL,P_URL,E_URL,P_URL+"/1301",E_URL+"/1301"])
        self.assertEqual(plan["detail_count"], 2)
        self.assertEqual(len(set(plan["request_urls_for_future_authorized_cycle"])), 5)
        self.assertEqual(plan["minimum_request_gap_seconds"], 4)
        self.assertEqual(plan["new_native_http_get"], 0)
        self.assertEqual(plan["published"], 0)
        self.assertFalse(plan["native_get_allowed"])
        self.assertFalse(plan["immutable_cross_host_claim_verified"])
        with self.assertRaisesRegex(ValueError, "IMMUTABLE_CLAIM_PROVIDER_MISSING_HOLD"):
            assert_no_untrusted_live_authority(plan)

    def test_six_hours_is_host_wide_and_clock_must_be_aware(self):
        enforce_elapsed(NOW, NOW-timedelta(hours=6))
        with self.assertRaisesRegex(ValueError, "SIX_HOUR_MIN_INTERVAL_HOLD"):
            review_two_catalog_plan(**inputs(previous_claim_at=NOW-timedelta(hours=5,minutes=59,seconds=59)))
        with self.assertRaisesRegex(ValueError, "CLOCK_ROLLBACK_HOLD"):
            review_two_catalog_plan(**inputs(previous_claim_at=NOW+timedelta(minutes=1)))
        with self.assertRaisesRegex(ValueError, "START_AWARE_UTC_REQUIRED_HOLD"):
            review_two_catalog_plan(**inputs(start_at=NOW.replace(tzinfo=None)))

    def test_robots_allowlist_must_cover_both_lists_and_selected_details(self):
        for robots in [
            b"User-agent: *\nDisallow: /program\n",
            b"User-agent: *\nDisallow: /event\n",
            b"User-agent: *\nAllow: /program\nDisallow: /event/1301\n",
        ]:
            with self.subTest(robots=robots):
                with self.assertRaisesRegex(ValueError, "ROBOTS_DENIED"):
                    review_two_catalog_plan(**inputs(robots=robots))

    def test_crawl_delay_beyond_budget_holds_and_no_policy_directives_fail(self):
        with self.assertRaisesRegex(ValueError, "CRAWL_DELAY_EXCEEDS_BUDGET_HOLD"):
            review_two_catalog_plan(**inputs(
                robots=b"User-agent: *\nCrawl-delay: 120\nAllow: /\n"))
        with self.assertRaisesRegex(ValueError, "ROBOTS_DIRECTIVES_MISSING_HOLD"):
            review_two_catalog_plan(**inputs(robots=b"just text"))

    def test_403_429_and_any_non_200_stop_without_retry(self):
        stop_on_response(200)
        for status in (403, 429):
            with self.assertRaisesRegex(ValueError, "403_429_STOP_NO_RETRY_HOLD"):
                stop_on_response(status)
        for status in (302, 404, 500):
            with self.assertRaisesRegex(ValueError, "NON_200_STOP_NO_RETRY_HOLD"):
                stop_on_response(status)
        with self.assertRaisesRegex(ValueError, "NON_200_STOP_NO_RETRY_HOLD"):
            stop_on_response(True)

    def test_consumed_earlier_attempt_blocks_even_offline_planning(self):
        with self.assertRaisesRegex(ValueError, "PRECONSUMED_REQUEST_BUDGET_HOLD"):
            review_two_catalog_plan(**inputs(attempts=(ROBOT_URL,)))
        with self.assertRaisesRegex(ValueError, "ATTEMPT_LOG_SCHEMA_HOLD"):
            review_two_catalog_plan(**inputs(attempts=[ROBOT_URL]))

    def test_weak_source_receipt_and_missing_list_fail_closed(self):
        d=inputs()
        d["program_receipt"]["http_status"]=403
        with self.assertRaisesRegex(ValueError, "RECEIPT_STATUS_URL_ROBOTS_SHA_HOLD"):
            review_two_catalog_plan(**d)
        d=inputs()
        d["event_body"]=b"<main></main>"
        d["event_receipt"]=receipt(E_URL,d["event_body"])
        with self.assertRaisesRegex(ValueError, "NO_VALID_EVENT_LINK_HOLD"):
            review_two_catalog_plan(**d)

    def test_caller_cannot_grant_immutable_claim_authority(self):
        d=review_two_catalog_plan(**inputs())
        for mutation in ({"native_get_allowed":True},
                         {"immutable_cross_host_claim_verified":True},
                         {"native_get_allowed":"TRUE"}):
            forged={**d,**mutation}
            with self.assertRaisesRegex(ValueError, "UNVERIFIED_LIVE_AUTHORITY_HOLD"):
                assert_no_untrusted_live_authority(forged)

if __name__ == "__main__":
    unittest.main()
