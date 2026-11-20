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
        self.assertEqual(MIN_INTERVAL_SECONDS, 21600)  # Owner host-wide 6h, robots may be stricter
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

    def test_owner_six_hours_is_host_wide_and_clock_must_be_aware(self):
        enforce_elapsed(NOW, NOW-timedelta(hours=6))
        with self.assertRaisesRegex(ValueError, "ENGINEERING_MIN_INTERVAL_HOLD"):
            review_two_catalog_plan(**inputs(previous_claim_at=NOW-timedelta(hours=5,minutes=59,seconds=59)))
        # A prior attempt 1h or 5h ago must never pass the Owner 6h rule.
        for elapsed in (timedelta(hours=1), timedelta(hours=5)):
            with self.subTest(elapsed=elapsed):
                with self.assertRaisesRegex(ValueError, "ENGINEERING_MIN_INTERVAL_HOLD"):
                    enforce_elapsed(NOW, NOW-elapsed)
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

    def test_request_rate_is_enforced_and_unsupported_policy_fails_closed(self):
        policy = b"User-agent: *\nAllow: /\nCrawl-delay: 4\nRequest-rate: 1/30\n"
        result = review_two_catalog_plan(**inputs(robots=policy))
        self.assertEqual(result["minimum_request_gap_seconds"], 30)
        self.assertFalse(result["native_get_allowed"])
        for policy in (
            b"User-agent: *\nAllow: /\nRequest-rate: broken\n",
            b"User-agent: *\nAllow: /\nRequest-rate: 1/120\n",
        ):
            with self.subTest(policy=policy):
                with self.assertRaisesRegex(ValueError, "REQUEST_RATE_"):
                    review_two_catalog_plan(**inputs(robots=policy))

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
        # Empty anchor inventory must retain the catalog's bounded-link
        # fail-closed contract; do not weaken the source parser to fit a test.
        d=inputs()
        d["event_body"]=b"<main></main>"
        d["event_receipt"]=receipt(E_URL,d["event_body"])
        with self.assertRaisesRegex(ValueError, "TPAC_CATALOG_LINK_CAP_HOLD"):
            review_two_catalog_plan(**d)
        # Nonempty anchor inventory with no valid official event identity is
        # a distinct negative case and must remain fail-closed as well.
        d=inputs()
        d["event_body"]=b'<main><a href="/unrelated/1301">No event</a></main>'
        d["event_receipt"]=receipt(E_URL,d["event_body"])
        with self.assertRaisesRegex(ValueError, "TPAC_CATALOG_NO_VALID_EVENT_LINK_HOLD"):
            review_two_catalog_plan(**d)

    def test_caller_cannot_grant_immutable_claim_authority(self):
        d=review_two_catalog_plan(**inputs())
        for mutation in ({"native_get_allowed":True},
                         {"immutable_cross_host_claim_verified":True},
                         {"native_get_allowed":"TRUE"}):
            forged={**d,**mutation}
            with self.assertRaisesRegex(ValueError, "UNVERIFIED_LIVE_AUTHORITY_HOLD"):
                assert_no_untrusted_live_authority(forged)


    def test_durable_attempt_preflight_rejects_missing_history_and_weak_lease(self):
        from scripts.p30_tpac_r4_source_policy import validate_durable_source_attempt
        ledger = dict(source_host="tpac.org.taipei", durable_provider_verified=True,
                      owner_run_id="runner-1", first_attempt=False,
                      last_attempt_at=NOW-timedelta(hours=6),
                      fencing_token="fence-001", attempt_written_at=NOW)
        lease = dict(source_host="tpac.org.taipei", atomic_acquire_verified=True,
                     exclusive=True, fencing_token="fence-001",
                     owner_run_id="runner-1", acquired_at=NOW-timedelta(seconds=1))
        self.assertIsNone(validate_durable_source_attempt(now=NOW, ledger=ledger, lease=lease))
        cases = [
            (dict(ledger, fencing_token="old-run"), lease, "LEDGER_LEASE_FENCING_MISMATCH"),
            (dict(ledger, attempt_written_at=None), lease, "ATTEMPT_WRITE_AHEAD_MISSING"),
            (dict(ledger, attempt_written_at=NOW+timedelta(seconds=1)), lease, "ATTEMPT_WRITE_AHEAD_MISSING"),
            (dict(ledger, attempt_written_at=NOW-timedelta(seconds=2)), lease, "ATTEMPT_PRECEDES_LEASE"),
            (dict(ledger, fencing_token=1), lease, "LEDGER_LEASE_FENCING_MISMATCH"),
            (dict(ledger, last_attempt_at=None), lease, "LAST_ATTEMPT_MISSING"),
            (dict(ledger, last_attempt_at=NOW-timedelta(minutes=59)), lease, "ENGINEERING_MIN_INTERVAL"),
            (dict(ledger, first_attempt=True), lease, "FIRST_ATTEMPT_CONFLICT"),
            (dict(ledger, durable_provider_verified=False), lease, "DURABLE_AUTHORITY_UNVERIFIED"),
            (ledger, dict(lease, atomic_acquire_verified=False), "DURABLE_AUTHORITY_UNVERIFIED"),
            (ledger, dict(lease, exclusive=False), "LEASE_NOT_EXCLUSIVE"),
            (ledger, dict(lease, owner_run_id="runner-2"), "LEASE_OWNER_MISMATCH"),
            (ledger, dict(lease, acquired_at=NOW+timedelta(seconds=1)), "LEASE_TIME_INVALID"),
            (ledger, dict(lease, fencing_token=None), "LEASE_NOT_EXCLUSIVE"),
        ]
        for record, claim, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(ValueError, reason):
                    validate_durable_source_attempt(now=NOW, ledger=record, lease=claim)
        with self.assertRaisesRegex(ValueError, "CROSS_HOST_LEDGER_SCOPE"):
            validate_durable_source_attempt(now=NOW, ledger={}, lease=lease)
        with self.assertRaisesRegex(ValueError, "SOURCE_HOST_MISMATCH"):
            validate_durable_source_attempt(now=NOW, ledger=ledger, lease=lease, source_host="other.example")
        first = dict(ledger, first_attempt=True, last_attempt_at=None)
        self.assertIsNone(validate_durable_source_attempt(now=NOW, ledger=first, lease=lease))
        # A forged in-memory boolean cannot grant network authority.
        with self.assertRaisesRegex(ValueError, "IMMUTABLE_CLAIM_PROVIDER_MISSING"):
            assert_no_untrusted_live_authority(review_two_catalog_plan(**inputs()))


    def test_reserve_durable_attempt_real_lifecycle_and_fail_closed(self):
        from scripts.p30_tpac_r4_source_policy import reserve_durable_source_attempt
        class Provider:
            def __init__(self):
                self.calls = []
                self.last = NOW-timedelta(hours=6)
                self.written = None
            def acquire_atomic(self, **kw):
                self.calls.append("acquire")
                return dict(source_host="tpac.org.taipei",
                            atomic_acquire_verified=True, exclusive=True,
                            fencing_token="generation-1", owner_run_id=kw["owner_run_id"],
                            acquired_at=NOW-timedelta(seconds=1))
            def read_last_attempt(self, **kw):
                self.calls.append("history")
                return dict(source_host=kw["source_host"], first_attempt=False,
                            last_attempt_at=self.last)
            def write_attempt(self, **kw):
                self.calls.append("write")
                self.written = kw
            def read_attempt(self, **kw):
                self.calls.append("readback")
                return dict(source_host=kw["source_host"], durable_provider_verified=True,
                            owner_run_id=kw["owner_run_id"], first_attempt=False,
                            last_attempt_at=self.last, fencing_token="generation-1",
                            attempt_written_at=self.written["attempted_at"])
        p = Provider()
        result = reserve_durable_source_attempt(provider=p, now=NOW, run_id="source-run-001")
        self.assertEqual(p.calls, ["acquire","history","write","readback"])
        self.assertTrue(result["attempt_reserved"])
        self.assertFalse(result["native_get_allowed"])
        self.assertEqual(result["decision"], CLAIM_HOLD)
        # Negative: malformed atomic lease must fail before reading history
        # or persisting any source attempt; no mock success grants LIVE GET.
        for override in ({"exclusive": False}, {"fencing_token": ""},
                         {"source_host": "other.example"},
                         {"owner_run_id": "wrong-run"},
                         {"acquired_at": NOW+timedelta(seconds=1)}):
            class InvalidLease(Provider):
                def acquire_atomic(self, **kw):
                    claim = super().acquire_atomic(**kw)
                    claim.update(override)
                    return claim
            invalid = InvalidLease()
            with self.subTest(override=override):
                with self.assertRaisesRegex(ValueError, "PROVIDER_ACQUIRED_LEASE_INVALID|LEASE_TIME_INVALID"):
                    reserve_durable_source_attempt(provider=invalid, now=NOW,
                                                   run_id="source-run-invalid")
                self.assertEqual(invalid.calls, ["acquire"])
                self.assertIsNone(invalid.written)
        p = Provider()
        p.last = NOW-timedelta(seconds=21599)
        with self.assertRaisesRegex(ValueError, "ENGINEERING_MIN_INTERVAL_HOLD"):
            reserve_durable_source_attempt(provider=p, now=NOW, run_id="source-run-002")
        self.assertEqual(p.calls, ["acquire","history"])
        class Broken(Provider):
            def read_attempt(self, **kw):
                self.calls.append("readback")
                raise RuntimeError("provider outage")
        p = Broken()
        with self.assertRaisesRegex(ValueError, "PROVIDER_OPERATION_FAILED_HOLD"):
            reserve_durable_source_attempt(provider=p, now=NOW, run_id="source-run-003")
        self.assertEqual(p.calls, ["acquire","history","write","readback"])
        with self.assertRaisesRegex(ValueError, "SOURCE_RUN_ID_HOLD"):
            reserve_durable_source_attempt(provider=Provider(), now=NOW, run_id="../")



class DurableCooldownPolicyTests(unittest.TestCase):
    def state(self, **changes):
        d = dict(source_host="tpac.org.taipei", source_identity="tpac:program:1423",
                 durable_readback_verified=True, last_attempt_at=NOW,
                 last_http_status=429, last_failure_class="RATE_LIMIT",
                 consecutive_failures=1, cooldown_until=NOW+timedelta(hours=24))
        d.update(changes)
        return d

    def test_429_expiry_is_review_only_never_live_get(self):
        from scripts.p30_tpac_r4_source_policy import evaluate_source_cooldown
        self.assertEqual(evaluate_source_cooldown(now=NOW+timedelta(hours=23),
                                                  state=self.state())["decision"], "COOLDOWN_ACTIVE")
        result = evaluate_source_cooldown(now=NOW+timedelta(hours=24), state=self.state())
        self.assertEqual(result["decision"], "REVIEW_ONLY")
        self.assertTrue(result["eligible_for_review"])
        self.assertFalse(result["native_get_allowed"])
        for count, hours in ((2, 48), (3, 96), (4, 168)):
            with self.subTest(count=count):
                with self.assertRaisesRegex(ValueError, "MINIMUM_VIOLATION"):
                    evaluate_source_cooldown(now=NOW+timedelta(days=8),
                        state=self.state(consecutive_failures=count,
                                         cooldown_until=NOW+timedelta(hours=24)))
                result = evaluate_source_cooldown(now=NOW+timedelta(days=8),
                    state=self.state(consecutive_failures=count,
                                     cooldown_until=NOW+timedelta(hours=hours)))
                self.assertFalse(result["native_get_allowed"])

    def test_retry_after_cannot_be_ignored_or_malformed(self):
        from scripts.p30_tpac_r4_source_policy import evaluate_source_cooldown
        for header in ("259200", "Fri, 27 Nov 2026 12:00:00 GMT"):
            with self.subTest(header=header):
                with self.assertRaisesRegex(ValueError, "MINIMUM_VIOLATION"):
                    evaluate_source_cooldown(now=NOW+timedelta(days=8),
                        state=self.state(retry_after_header=header))
        for header in ("nonsense", "-1", "", True):
            with self.subTest(header=header):
                with self.assertRaisesRegex(ValueError, "RETRY_AFTER_INVALID"):
                    evaluate_source_cooldown(now=NOW+timedelta(days=8),
                        state=self.state(retry_after_header=header))
        result = evaluate_source_cooldown(now=NOW+timedelta(days=8),
            state=self.state(retry_after_header="259200",
                             cooldown_until=NOW+timedelta(days=3)))
        self.assertEqual(result["decision"], "REVIEW_ONLY")
        self.assertFalse(result["native_get_allowed"])

    def test_403_requires_policy_review_even_after_expiry(self):
        from scripts.p30_tpac_r4_source_policy import evaluate_source_cooldown
        state = self.state(last_http_status=403, last_failure_class="ACCESS_DENIED",
                           cooldown_until=NOW+timedelta(hours=72))
        result = evaluate_source_cooldown(now=NOW+timedelta(days=4), state=state)
        self.assertEqual(result["decision"], "SOURCE_ACCESS_HOLD_POLICY_REVIEW_REQUIRED")
        self.assertFalse(result["native_get_allowed"])
        with self.assertRaisesRegex(ValueError, "MINIMUM_VIOLATION"):
            evaluate_source_cooldown(now=NOW+timedelta(days=4),
                                    state=dict(state, cooldown_until=NOW+timedelta(hours=24)))

    def test_unverified_readback_or_invalid_identity_never_eligible(self):
        from scripts.p30_tpac_r4_source_policy import evaluate_source_cooldown
        for change in ({"durable_readback_verified": False},
                       {"source_identity": "tpac:other:1423"},
                       {"last_attempt_at": NOW+timedelta(days=2)},
                       {"cooldown_until": NOW+timedelta(hours=1)},
                       {"consecutive_failures": True}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    evaluate_source_cooldown(now=NOW+timedelta(days=1),
                                             state=self.state(**change))
        result = evaluate_source_cooldown(now=NOW+timedelta(days=5),
            state=self.state(last_http_status=404, last_failure_class="PERMANENT",
                             cooldown_until=NOW+timedelta(days=1)))
        self.assertEqual(result["decision"], "SOURCE_ACCESS_HOLD")
        self.assertFalse(result["native_get_allowed"])


if __name__ == "__main__":
    unittest.main()
