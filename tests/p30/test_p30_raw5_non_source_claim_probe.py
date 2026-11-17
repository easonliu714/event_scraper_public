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

def transport_for(outcome, winner_owner="runner-one", ref_status=200):
    calls = []
    def call(method, path, token, payload=None):
        calls.append((method, path, payload))
        if method == "GET" and path.endswith("/git/commits/" + A):
            return 200, {"tree": {"sha": T}}
        if method == "POST" and path.endswith("/git/commits"):
            return 201, {"sha": C}
        if method == "POST" and path.endswith("/git/refs"):
            return outcome, {} if outcome == 201 else {"message": "Reference already exists"}
        if method == "GET" and "/git/ref/" in path:
            return ref_status, {"object": {"sha": C}} if ref_status == 200 else {}
        if method == "GET" and path.endswith("/git/commits/" + C):
            return 200, {"message": "NON_SOURCE_RAW5_TEST_V1 isolated-run-01 " + winner_owner,
                         "parents": [{"sha": A}], "tree": {"sha": T}}
        raise AssertionError((method, path))
    return call, calls

class NonSourceClaimProbeTests(unittest.TestCase):
    def test_winner_requires_real_commit_and_ref_readback(self):
        transport, calls = transport_for(201)
        result = module.probe("isolated-run-01", A, "runner-one", "token", transport)
        self.assertEqual(result["decision"], "WON_TEST_ONLY")
        self.assertFalse(result["native_get_allowed"])
        self.assertEqual([c[0] for c in calls], ["GET", "POST", "POST", "GET", "GET"])
    def test_loser_returns_collision_without_source_get(self):
        transport, calls = transport_for(422)
        result = module.probe("isolated-run-01", A, "runner-two", "token", transport)
        self.assertEqual(result["decision"], "LOST_COLLISION")
        self.assertEqual(result["winner_run"], "runner-one")
        self.assertFalse(result["native_get_allowed"])
        self.assertEqual(len(calls), 5)
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
    def test_unexpected_status_fails_closed(self):
        transport, _ = transport_for(403)
        with self.assertRaisesRegex(RuntimeError, "REF_CREATE_HOLD:403"):
            module.probe("isolated-run-01", A, "runner-one", "token", transport)

if __name__ == "__main__":
    unittest.main()
