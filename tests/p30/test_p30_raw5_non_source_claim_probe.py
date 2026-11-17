"""Real transport-contract tests for the NON-SOURCE GitHub claim probe."""
import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "p30_raw5_non_source_claim_probe.py"
spec = importlib.util.spec_from_file_location("probe", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
A = "a" * 40
T = "b" * 40
C = "c" * 40
D = "d" * 40  # Loser candidate must be a different owner-bound Git commit.

def transport_for(outcome, winner_owner="runner-one", ref_status=200,
                  ruleset_status=200, ruleset_override=None,
                  collision_message="Reference already exists",
                  same_candidate=False, ref_type="commit"):
    calls = []
    def call(method, path, token, payload=None):
        calls.append((method, path, payload))
        if method == "GET" and path.endswith("/rulesets/27026973"):
            policy = {
                "id": 27026973, "target": "branch", "enforcement": "active",
                "current_user_can_bypass": "never",
                "conditions": {"ref_name": {
                    "include": ["refs/heads/source-claims/*"], "exclude": []}},
                "bypass_actors": [],
                "rules": [{"type": "deletion"}, {"type": "update"},
                          {"type": "non_fast_forward"}],
            }
            if ruleset_override is not None:
                policy.update(ruleset_override)
            return ruleset_status, policy
        if method == "GET" and path.endswith("/git/commits/" + A):
            return 200, {"tree": {"sha": T}}
        if method == "POST" and path.endswith("/git/commits"):
            return 201, {"sha": D}
        if method == "POST" and path.endswith("/git/refs"):
            return outcome, {} if outcome == 201 else {"message": collision_message}
        if method == "GET" and "/git/ref/" in path:
            pointed = D if outcome == 201 or same_candidate else C
            return ref_status, {"object": {"sha": pointed, "type": ref_type}} if ref_status == 200 else {}
        if method == "GET" and path.endswith("/git/commits/" + C):
            return 200, {"sha": C, "message": "NON_SOURCE_RAW5_TEST_V1 isolated-run-01 " + winner_owner,
                         "parents": [{"sha": A}], "tree": {"sha": T}}
        if method == "GET" and path.endswith("/git/commits/" + D):
            return 200, {"sha": D, "message": "NON_SOURCE_RAW5_TEST_V1 isolated-run-01 runner-two",
                         "parents": [{"sha": A}], "tree": {"sha": T}}
        raise AssertionError((method, path))
    return call, calls

class NonSourceClaimProbeTests(unittest.TestCase):
    def test_winner_requires_real_commit_and_ref_readback(self):
        transport, calls = transport_for(201)
        result = module.probe("isolated-run-01", A, "runner-one", "token", transport)
        self.assertEqual(result["decision"], "WON_TEST_ONLY")
        self.assertFalse(result["native_get_allowed"])
        self.assertEqual([c[0] for c in calls], ["GET", "GET", "POST", "POST", "GET", "GET"])
    def test_loser_returns_collision_without_source_get(self):
        transport, calls = transport_for(422)
        result = module.probe("isolated-run-01", A, "runner-two", "token", transport)
        self.assertEqual(result["decision"], "LOST_COLLISION")
        self.assertEqual(result["winner_run"], "runner-one")
        self.assertEqual(result["winner_commit_sha"], C)
        self.assertEqual(result["loser_commit_sha"], D)
        self.assertFalse(result["native_get_allowed"])
        self.assertEqual(len(calls), 6)
    def test_422_ruleset_or_validation_reason_never_counts_as_collision(self):
        for reason in ("Validation Failed", "Repository ruleset violations", "", None):
            transport, calls = transport_for(422, collision_message=reason)
            with self.subTest(reason=reason), self.assertRaisesRegex(
                    RuntimeError, "COLLISION_REASON_UNVERIFIED_HOLD"):
                module.probe("isolated-run-01", A, "runner-two", "token", transport)
            # Ref and winner must not be read after an invalid 422 reason.
            self.assertFalse(any("/git/ref/" in path for _, path, _ in calls))

    def test_422_same_commit_cannot_be_two_distinct_owners(self):
        transport, _ = transport_for(422, same_candidate=True)
        with self.assertRaisesRegex(RuntimeError, "COLLISION_REF_UNPROVEN_HOLD"):
            module.probe("isolated-run-01", A, "runner-two", "token", transport)

    def test_422_non_commit_ref_object_not_a_valid_winner(self):
        transport, _ = transport_for(422, ref_type="blob")
        with self.assertRaisesRegex(RuntimeError, "COLLISION_REF_UNPROVEN_HOLD"):
            module.probe("isolated-run-01", A, "runner-two", "token", transport)

    def test_422_without_existing_ref_is_not_a_collision(self):
        transport, _ = transport_for(422, ref_status=404)
        with self.assertRaisesRegex(RuntimeError, "COLLISION_REF_UNPROVEN_HOLD:404"):
            module.probe("isolated-run-01", A, "runner-two", "token", transport)
    def test_422_self_owned_ref_is_not_an_independent_loser(self):
        transport, _ = transport_for(422, winner_owner="runner-two")
        with self.assertRaisesRegex(RuntimeError, "COLLISION_WINNER_UNPROVEN_HOLD"):
            module.probe("isolated-run-01", A, "runner-two", "token", transport)
    def test_scope_validation_rejects_source_or_short_id(self):
        for scope in ("tpac", "../source-claims/raw5-tpac-123", "A" * 12):
            with self.assertRaises(ValueError):
                module.validate(scope, A, "runner-one")
    def test_ruleset_missing_or_read_denied_blocks_before_any_write(self):
        for status in (403, 404, 500):
            transport, calls = transport_for(201, ruleset_status=status)
            with self.subTest(status=status), self.assertRaisesRegex(
                    RuntimeError, "NON_SOURCE_RULESET_UNREADABLE_HOLD"):
                module.probe("isolated-run-01", A, "runner-one", "token", transport)
            self.assertEqual([x[0] for x in calls], ["GET"])

    def test_ruleset_inactive_bypass_or_missing_protection_blocks_writes(self):
        cases = (
            {"target": "tag"},
            {"current_user_can_bypass": "always"},
            {"conditions": {"ref_name": {"include": "refs/heads/source-claims/*", "exclude": []}}},
            {"enforcement": "disabled"},
            {"id": 111},
            {"bypass_actors": [{"actor_id": 42, "actor_type": "Integration"}]},
            {"conditions": {"ref_name": {
                "include": ["refs/heads/unrelated/*"], "exclude": []}}},
            {"conditions": {"ref_name": {
                "include": ["refs/heads/source-claims/*"],
                "exclude": ["refs/heads/source-claims/validation-raw5-*"]}}},
            {"rules": [{"type": "deletion"}, {"type": "non_fast_forward"}]},
            {"rules": [{"type": "update"}, {"type": "deletion"}]},
            {"conditions": None},
            {"rules": None},
        )
        for policy_change in cases:
            transport, calls = transport_for(201, ruleset_override=policy_change)
            with self.subTest(policy_change=policy_change), self.assertRaisesRegex(
                    RuntimeError, "NON_SOURCE_RULESET_PROTECTION_UNVERIFIED_HOLD"):
                module.probe("isolated-run-01", A, "runner-one", "token", transport)
            self.assertTrue(calls)
            self.assertEqual([x[0] for x in calls], ["GET"])

    def test_ruleset_readback_has_no_source_get_authority(self):
        transport, calls = transport_for(201)
        ref = module.validate("isolated-run-01", A, "runner-one")
        check = module.verify_protected_claim_ruleset(ref, "token", transport)
        self.assertTrue(check["verified"])
        self.assertFalse(check["native_get_allowed"])
        self.assertEqual(check["ruleset_id"], 27026973)
        self.assertEqual(len(calls), 1)
        for foreign in ("refs/heads/other", "refs/heads/source-claims/sub/branch"):
            with self.subTest(foreign=foreign), self.assertRaises(ValueError):
                module.verify_protected_claim_ruleset(foreign, "token", transport)
        self.assertEqual(len(calls), 1)

    def test_unexpected_status_fails_closed(self):
        transport, _ = transport_for(403)
        with self.assertRaisesRegex(RuntimeError, "REF_CREATE_HOLD:403"):
            module.probe("isolated-run-01", A, "runner-one", "token", transport)

if __name__ == "__main__":
    unittest.main()
