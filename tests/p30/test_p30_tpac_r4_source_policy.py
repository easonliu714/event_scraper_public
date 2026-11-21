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
            def read_host_cooldown(self, **kw):
                self.calls.append("cooldown")
                status = getattr(self, "cooldown_status", 200)
                reason = ("NONE" if status == 200 else
                          "RATE_LIMIT" if status == 429 else
                          "ACCESS_DENIED" if status == 403 else "TRANSIENT")
                minimum_hours = (24 if status == 429 else 72 if status == 403
                                 else 12 if status >= 500 else 6)
                return dict(scope="HOST_WIDE", source_host=kw["source_host"],
                            source_identity="tpac:program:1423",
                            durable_readback_verified=True,
                            last_attempt_at=self.last, last_http_status=status,
                            last_failure_class=reason,
                            consecutive_failures=0 if status == 200 else 1,
                            cooldown_until=self.last + timedelta(hours=minimum_hours))
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
        self.assertEqual(p.calls, ["acquire","history","cooldown","write","readback"])
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
        self.assertEqual(p.calls, ["acquire","history","cooldown","write","readback"])
        with self.assertRaisesRegex(ValueError, "SOURCE_RUN_ID_HOLD"):
            reserve_durable_source_attempt(provider=Provider(), now=NOW, run_id="../")
        # Reject a prior /program 429 for every /event attempt on this host,
        # even though the Owner's six-hour minimum has already elapsed.
        p = Provider()
        p.last = NOW-timedelta(hours=7)
        p.cooldown_status = 429
        # Active 429 must report the cooldown fence, not the expired-only
        # probe authorization fence; both reject before write_attempt.
        with self.assertRaisesRegex(ValueError, "TPAC_R4_HOST_COOLDOWN_ACTIVE_OR_POLICY_HOLD"):
            reserve_durable_source_attempt(provider=p, now=NOW,
                                           run_id="event-run-after-429")
        self.assertEqual(p.calls, ["acquire", "history", "cooldown"])
        self.assertIsNone(p.written)
        # Expired 429 permits offline policy review, but must not consume
        # a new attempt without a separately verified probe authorization.
        p = Provider()
        p.last = NOW-timedelta(hours=25)
        p.cooldown_status = 429
        with self.assertRaisesRegex(ValueError, "429_PROBE_AUTHORIZATION_REQUIRED_HOLD"):
            reserve_durable_source_attempt(provider=p, now=NOW,
                                           run_id="event-run-after-wait")
        self.assertEqual(p.calls, ["acquire", "history", "cooldown"])
        self.assertIsNone(p.written)
        # 403 is never an automatic retry merely because the 72h elapsed.
        p = Provider()
        p.last = NOW-timedelta(hours=80)
        p.cooldown_status = 403
        with self.assertRaisesRegex(ValueError, "HOST_COOLDOWN_ACTIVE_OR_POLICY_HOLD"):
            reserve_durable_source_attempt(provider=p, now=NOW,
                                           run_id="event-run-after-403")
        self.assertIsNone(p.written)
        # Missing/stale/per-event state must fail *before* request reservation.
        for mutation in ({"scope": "PER_EVENT"},
                         {"last_attempt_at": NOW-timedelta(hours=7)},
                         {"durable_readback_verified": False}):
            class UntrustedCooldown(Provider):
                def read_host_cooldown(self, **kw):
                    result = super().read_host_cooldown(**kw)
                    result.update(mutation)
                    return result
            p = UntrustedCooldown()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                reserve_durable_source_attempt(provider=p, now=NOW,
                                               run_id="event-untrusted-state")
            self.assertIsNone(p.written)
        class MissingCooldown(Provider):
            read_host_cooldown = None
        p = MissingCooldown()
        with self.assertRaisesRegex(ValueError, "HOST_COOLDOWN_PROVIDER_MISSING_HOLD"):
            reserve_durable_source_attempt(provider=p, now=NOW,
                                           run_id="event-missing-provider")
        self.assertIsNone(p.written)




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



class IsolatedSingleExecutorLedgerTests(unittest.TestCase):
    """Real local SQLite/POSIX lock/restart IO; NO official HTTP or publication."""

    def test_host_429_shares_fence_but_independent_sources_are_not_blocked(self):
        import tempfile
        from pathlib import Path
        from scripts.p30_tpac_r4_source_policy import IsolatedSingleExecutorLedger
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "source-ledger.sqlite"
            with IsolatedSingleExecutorLedger(db) as store:
                lease = store.begin_attempt(
                    source_host="tpac.org.taipei", source_identity="tpac:program:list",
                    owner_run_id="runner-program-0001", now=NOW)
                self.assertFalse(lease["native_get_allowed"])
                result = store.commit_response(
                    source_host="tpac.org.taipei", owner_run_id="runner-program-0001",
                    fencing_token=lease["fencing_token"], status=429,
                    observed_at=NOW+timedelta(minutes=1),
                    retry_after_header="259200")
                self.assertFalse(result["native_get_allowed"])
                self.assertEqual(result["cooldown_until"],
                                 NOW+timedelta(days=3, minutes=1))
                # The second LIST namespace cannot bypass the first 429.
                with self.assertRaisesRegex(ValueError, "POLICY_OR_PROBE_REVIEW_HOLD"):
                    store.begin_attempt(
                        source_host="tpac.org.taipei", source_identity="tpac:event:list",
                        owner_run_id="runner-event-0001",
                        now=NOW+timedelta(days=4))
                # Another explicitly isolated source host is independent.
                other = store.begin_attempt(
                    source_host="tainex.example", source_identity="tainex:event:701",
                    owner_run_id="runner-tainex-0001",
                    now=NOW+timedelta(hours=1))
                self.assertFalse(other["native_get_allowed"])
            with IsolatedSingleExecutorLedger(db) as reopened:
                saved = reopened.read_host_cooldown(source_host="tpac.org.taipei")
                self.assertEqual(saved["last_http_status"], 429)
                self.assertEqual(saved["retry_after_header"], "259200")
                self.assertEqual(saved["evidence_class"], "ISOLATED_LOCAL_PROCESS_ONLY")
                self.assertFalse(saved["native_get_allowed"])
                with self.assertRaisesRegex(ValueError, "POLICY_OR_PROBE_REVIEW_HOLD"):
                    reopened.begin_attempt(
                        source_host="tpac.org.taipei", source_identity="tpac:event:list",
                        owner_run_id="runner-event-after-restart", now=NOW+timedelta(days=6))
                with self.assertRaisesRegex(ValueError, "PENDING_RESPONSE_HOLD"):
                    reopened.read_host_cooldown(source_host="tainex.example")

    def test_stale_fence_untrusted_200_and_bad_retry_after_preserve_pending(self):
        import tempfile
        from pathlib import Path
        from scripts.p30_tpac_r4_source_policy import IsolatedSingleExecutorLedger
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "test.sqlite"
            with IsolatedSingleExecutorLedger(db) as store:
                lease = store.begin_attempt(
                    source_host="tpac.org.taipei", source_identity="tpac:program:list",
                    owner_run_id="runner-program-0002", now=NOW)
                def submit(**changes):
                    args = dict(source_host="tpac.org.taipei",
                                owner_run_id="runner-program-0002",
                                fencing_token=lease["fencing_token"], status=429,
                                observed_at=NOW+timedelta(minutes=1))
                    args.update(changes)
                    return store.commit_response(**args)
                with self.assertRaisesRegex(ValueError, "FENCING_OR_PENDING_HOLD"):
                    submit(fencing_token="stale-generation")
                with self.assertRaisesRegex(ValueError, "RESPONSE_BEFORE_ATTEMPT_HOLD"):
                    submit(observed_at=NOW-timedelta(seconds=1))
                for bad in ("garbled", "-1", "", True):
                    with self.subTest(bad=bad):
                        with self.assertRaisesRegex(ValueError, "RETRY_AFTER"):
                            submit(retry_after_header=bad)
                with self.assertRaisesRegex(ValueError, "200_TRUSTED_PARSER_RECEIPT_HOLD"):
                    submit(status=200)
                with self.assertRaisesRegex(ValueError, "MISSING_OR_PENDING_RESPONSE_HOLD"):
                    store.read_host_cooldown(source_host="tpac.org.taipei")
                committed = submit()
                self.assertEqual(committed["last_http_status"], 429)
                with self.assertRaisesRegex(ValueError, "FENCING_OR_PENDING_HOLD"):
                    submit()
            with IsolatedSingleExecutorLedger(db) as reopened:
                self.assertEqual(reopened.read_host_cooldown(
                    source_host="tpac.org.taipei")["consecutive_failures"], 1)

    def test_verified_offline_list_200_requires_real_bytes_and_allows_next_cycle(self):
        import tempfile
        from pathlib import Path
        from scripts.p30_tpac_r4_source_policy import IsolatedSingleExecutorLedger
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "test.sqlite"
            with IsolatedSingleExecutorLedger(db) as store:
                lease = store.begin_attempt(
                    source_host="tpac.org.taipei", source_identity="tpac:program:list",
                    owner_run_id="runner-program-0003", now=NOW)
                raw = program()
                observed = NOW+timedelta(minutes=1)
                bound_receipt = receipt(P_URL, raw)
                bound_receipt.update(
                    observed_at=observed.isoformat(),
                    ledger_evidence_class="ISOLATED_OFFLINE_SOURCE_RECEIPT",
                    ledger_owner_run_id="runner-program-0003",
                    ledger_fencing_token=lease["fencing_token"],
                    ledger_source_host="tpac.org.taipei",
                    ledger_source_identity="tpac:program:list",
                    ledger_source_url=P_URL,
                    ledger_observed_at=observed.isoformat())
                args = dict(
                    source_host="tpac.org.taipei", owner_run_id="runner-program-0003",
                    fencing_token=lease["fencing_token"], status=200,
                    observed_at=observed, raw_body=raw)
                # One changed attribute cannot silently commit a different
                # event, host, owner, time or fencing token.
                with self.assertRaisesRegex(ValueError, "PARSER_RECEIPT_BINDING_HOLD"):
                    store.commit_response(**args, source_receipt=receipt(P_URL, raw))
                tampered = (
                    ("ledger_owner_run_id", "wrong-owner"),
                    ("ledger_fencing_token", "wrong-fence"),
                    ("ledger_source_identity", "tpac:event:list"),
                    ("ledger_source_host", "other.example"),
                    ("ledger_source_url", E_URL),
                    ("ledger_observed_at", NOW.isoformat()),
                    ("observed_at", NOW.isoformat()),
                    ("final_url", E_URL),
                    ("ledger_evidence_class", "LIVE_AUTHORIZED"))
                for key, value in tampered:
                    with self.subTest(field=key):
                        forged = {**bound_receipt, key: value}
                        with self.assertRaisesRegex(
                                ValueError, "PARSER_RECEIPT_BINDING_HOLD"):
                            store.commit_response(**args, source_receipt=forged)
                with self.assertRaisesRegex(ValueError, "RECEIPT_STATUS_URL_ROBOTS_SHA_HOLD"):
                    store.commit_response(**{**args, "raw_body": raw+b" "},
                                          source_receipt=bound_receipt)
                with self.assertRaisesRegex(ValueError, "MISSING_OR_PENDING_RESPONSE_HOLD"):
                    store.read_host_cooldown(source_host="tpac.org.taipei")
                response = store.commit_response(**args, source_receipt=bound_receipt)
                self.assertFalse(response["native_get_allowed"])
                evidence = store.read_last_bound_source(source_host="tpac.org.taipei")
                self.assertEqual(evidence["source_identity"], "tpac:program:list")
                self.assertEqual(evidence["source_url"], P_URL)
                self.assertEqual(evidence["source_observed_at"], observed)
                self.assertEqual(evidence["body_sha256"], hashlib.sha256(raw).hexdigest())
                self.assertFalse(evidence["native_get_allowed"])
                with self.assertRaisesRegex(ValueError, "SIX_HOUR_HOST_HOLD"):
                    store.begin_attempt(
                        source_host="tpac.org.taipei", source_identity="tpac:event:list",
                        owner_run_id="runner-event-too-soon", now=NOW+timedelta(hours=2))
            with IsolatedSingleExecutorLedger(db) as store:
                evidence = store.read_last_bound_source(source_host="tpac.org.taipei")
                self.assertEqual(evidence["source_url"], P_URL)
                self.assertFalse(evidence["native_get_allowed"])
                other = store.begin_attempt(
                    source_host="tpac.org.taipei", source_identity="tpac:event:list",
                    owner_run_id="runner-event-six-hour-later",
                    now=NOW+timedelta(hours=7))
                self.assertFalse(other["native_get_allowed"])

    def test_legacy_success_without_fenced_source_receipt_stays_hold(self):
        import sqlite3
        import tempfile
        from pathlib import Path
        from scripts.p30_tpac_r4_source_policy import IsolatedSingleExecutorLedger
        # Existing durable DBs may contain an old 200 without audited
        # source-url and attempt-bound parser receipt. Schema migration must
        # NEVER allow it to become a new source authorization.
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "legacy.sqlite"
            with sqlite3.connect(str(db)) as conn:
                conn.execute("""CREATE TABLE source_attempts (
                    id INTEGER PRIMARY KEY, source_host TEXT NOT NULL,
                    source_identity TEXT NOT NULL,
                    owner_run_id TEXT NOT NULL UNIQUE, fencing_token TEXT NOT NULL,
                    attempted_at TEXT NOT NULL, response_at TEXT,
                    outcome TEXT NOT NULL, last_http_status INTEGER,
                    failure_class TEXT, consecutive_failures INTEGER DEFAULT 0,
                    retry_after_header TEXT, cooldown_until TEXT,
                    body_sha256 TEXT)""")
                conn.execute("""INSERT INTO source_attempts
                    (source_host,source_identity,owner_run_id,fencing_token,
                    attempted_at,response_at,outcome,last_http_status,
                    failure_class,cooldown_until,body_sha256)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (
                    "tpac.org.taipei", "tpac:program:list", "legacy-run-0001",
                    "old-fence", NOW.isoformat(), NOW.isoformat(),
                    "COMMITTED", 200, "NONE",
                    (NOW+timedelta(hours=6)).isoformat(),
                    "0"*64))
            with IsolatedSingleExecutorLedger(db) as store:
                with self.assertRaisesRegex(ValueError, "LEGACY_UNBOUND_200_HOLD"):
                    store.begin_attempt(
                        source_host="tpac.org.taipei", source_identity="tpac:event:list",
                        owner_run_id="post-migration-run",
                        now=NOW+timedelta(days=1))
                with self.assertRaisesRegex(ValueError, "BOUND_SOURCE_NOT_AVAILABLE_HOLD"):
                    store.read_last_bound_source(source_host="tpac.org.taipei")

    def test_actual_os_process_lock_and_crash_pending_recovery(self):
        import tempfile
        import subprocess
        import sys
        from pathlib import Path
        from scripts.p30_tpac_r4_source_policy import IsolatedSingleExecutorLedger
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "exclusive.sqlite"
            with IsolatedSingleExecutorLedger(db):
                # A separate Python interpreter must not take over the same DB.
                child = subprocess.run([sys.executable, "-c",
                    "import sys;from scripts.p30_tpac_r4_source_policy import "
                    "IsolatedSingleExecutorLedger as L;"
                    "db=sys.argv[1];"
                    "\ntry:\n L(db)\nexcept ValueError:\n sys.exit(0)"
                    "\nelse:\n sys.exit(5)", str(db)],
                    capture_output=True, text=True)
                self.assertEqual(child.returncode, 0, child.stderr)
            # Abrupt process exit releases OS lock but leaves pending attempt.
            child = subprocess.run([sys.executable, "-c",
                "import os,sys;from datetime import datetime,timezone;"
                "from scripts.p30_tpac_r4_source_policy import "
                "IsolatedSingleExecutorLedger as L;"
                "db=sys.argv[1];x=L(db);"
                "x.begin_attempt(source_host='tpac.org.taipei',"
                "source_identity='tpac:program:list',"
                "owner_run_id='runner-crash-0001',"
                "now=datetime(2026,11,9,9,35,tzinfo=timezone.utc));"
                "os._exit(7)", str(db)], capture_output=True, text=True)
            self.assertEqual(child.returncode, 7, child.stderr)
            with IsolatedSingleExecutorLedger(db) as reopened:
                with self.assertRaisesRegex(ValueError, "UNCERTAIN_CRASH_OUTCOME_HOLD"):
                    reopened.begin_attempt(
                        source_host="tpac.org.taipei", source_identity="tpac:event:list",
                        owner_run_id="runner-retry-after-crash",
                        now=NOW+timedelta(days=10))
                with self.assertRaisesRegex(ValueError, "MISSING_OR_PENDING_RESPONSE_HOLD"):
                    reopened.read_host_cooldown(source_host="tpac.org.taipei")


if __name__ == "__main__":
    unittest.main()
