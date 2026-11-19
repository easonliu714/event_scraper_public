"""Offline source evidence tests; no official HTTP calls."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "p30_tainex_response_evidence.py"
spec = importlib.util.spec_from_file_location("evidence", MODULE)
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


class ResponseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "response.raw").write_bytes(b"<html>sample</html>")
        self.args = dict(raw_path=self.root / "response.raw",
                         output_dir=self.root / "isolated",
                         source_url="https://www.tainex.com.tw/robots.txt",
                         final_url="https://www.tainex.com.tw/robots.txt",
                         http_status=200, observed_at="2026-11-19T01:00:00Z")

    def test_persists_bytes_and_sha_without_attesting_http(self):
        result = evidence.ingest_response(**self.args)
        self.assertFalse(result["native_http_attested"])
        self.assertEqual(result["raw_bytes"], 19)
        self.assertEqual(len(list((self.root / "isolated").glob("*.bin"))), 1)
        with self.assertRaises(FileExistsError):
            evidence.ingest_response(**self.args)

    def test_rejects_unapproved_host(self):
        self.args["final_url"] = "https://evil.example/robots.txt"
        with self.assertRaises(ValueError):
            evidence.ingest_response(**self.args)

    def test_rejects_non_utc_and_redirect(self):
        self.args["observed_at"] = "2026-11-19T09:00:00+08:00"
        with self.assertRaises(ValueError):
            evidence.ingest_response(**self.args)
        self.args["observed_at"] = "2026-11-19T01:00:00Z"
        self.args["final_url"] = "https://tainex.com.tw/robots.txt"
        with self.assertRaises(ValueError):
            evidence.ingest_response(**self.args)

    def test_rejects_oversize(self):
        (self.root / "response.raw").write_bytes(b"x" * (evidence.MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            evidence.ingest_response(**self.args)


if __name__ == "__main__":
    unittest.main()
