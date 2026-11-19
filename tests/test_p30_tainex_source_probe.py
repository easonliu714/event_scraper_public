"""No-network tests for opt-in TaiNEX HTTP -> LIST -> exact-ID DETAIL gateway."""
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from scripts import p30_tainex_source_probe as probe


class Response:
    status = 200
    def __init__(self, url, body):
        self.url, self.body = url, body
    def geturl(self):
        return self.url
    def read(self, count):
        return self.body[:count]
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class Opener:
    def __init__(self, bodies):
        self.bodies = bodies
        self.calls = []
    def open(self, request, timeout):
        url = request.full_url
        self.calls.append(url)
        item = self.bodies[url]
        if isinstance(item, Exception):
            raise item
        return Response(url, item)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "isolated"
        self.robots = b"User-agent: *\nAllow: /event\n"
        self.opener = Opener({
            probe.ROBOTS: self.robots,
            probe.LIST: b"<html>list</html>",
            probe.ORIGIN + "/event/691": b"<html>detail</html>",
        })

    def run_probe(self, **kwargs):
        return probe.capture(output_dir=self.out, opener=self.opener,
                             clock=lambda: "2026-11-19T03:00:00Z",
                             sleeper=lambda seconds: None, **kwargs)

    def test_explicit_opt_in_required_before_network(self):
        with self.assertRaisesRegex(ValueError, "EXPLICIT_EXECUTE_REQUIRED"):
            self.run_probe()
        self.assertEqual(self.opener.calls, [])

    def test_robots_list_and_exact_detail_persist_isolated_bytes(self):
        result = self.run_probe(execute=True, detail_id="691")
        self.assertEqual(self.opener.calls,
                         [probe.ROBOTS, probe.LIST, probe.ORIGIN + "/event/691"])
        self.assertEqual([r["role"] for r in result["receipts"]], ["LIST", "DETAIL"])
        self.assertFalse(result["native_http_attested"])
        self.assertEqual(len(list(self.out.glob("*.bin"))), 2)
        self.assertEqual(len(list(self.out.glob("*.json"))), 2)

    def test_robots_denial_stops_before_list(self):
        self.opener.bodies[probe.ROBOTS] = b"User-agent: *\nDisallow: /event\n"
        with self.assertRaisesRegex(ValueError, "ROBOTS_LIST_DENIED_HOLD"):
            self.run_probe(execute=True, detail_id="691")
        self.assertEqual(self.opener.calls, [probe.ROBOTS])

    def test_403_stops_without_detail(self):
        self.opener.bodies[probe.LIST] = HTTPError(probe.LIST, 403, "Forbidden", {}, None)
        with self.assertRaisesRegex(ValueError, "SOURCE_403_429_STOP"):
            self.run_probe(execute=True, detail_id="691")
        self.assertEqual(self.opener.calls, [probe.ROBOTS, probe.LIST])

    def test_invalid_detail_id_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError, "DETAIL_ID_SCOPE_HOLD"):
            self.run_probe(execute=True, detail_id="../other")
        self.assertEqual(self.opener.calls, [])

    def test_redirect_rejected(self):
        class RedirectOpener(Opener):
            def open(self, request, timeout):
                self.calls.append(request.full_url)
                return Response("https://example.com/other", b"redirected")
        self.opener = RedirectOpener(self.opener.bodies)
        with self.assertRaisesRegex(ValueError, "SOURCE_REDIRECT_HOLD"):
            self.run_probe(execute=True)
        self.assertEqual(self.opener.calls, [probe.ROBOTS])


if __name__ == "__main__":
    unittest.main()
