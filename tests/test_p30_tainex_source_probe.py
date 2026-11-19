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
            probe.LIST: b'<html><a href="/event/691">event</a></html>',
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
        self.assertEqual(len(list(self.out.glob("*.bin"))), 3)
        self.assertEqual(len(list(self.out.glob("*.json"))), 3)

    def test_list_only_exposes_unique_safe_current_event_ids(self):
        self.opener.bodies[probe.LIST] = (
            b'<a href="/event/691">a</a><a href="/event/691">duplicate</a>'
            b'<a href="/event/22">b</a><a href="https://evil.example/event/99">bad</a>'
            b'<a href="/event/23?preview=1">query</a>'
            b'<a href="/event/not-numeric">invalid</a>')
        result = self.run_probe(execute=True)
        self.assertEqual(result["current_list_event_ids"], ["22", "691"])
        self.assertEqual(self.opener.calls, [probe.ROBOTS, probe.LIST])
        self.assertEqual(len(list(self.out.glob("*.bin"))), 2)

    def test_discovery_rejects_cross_origin_and_noncanonical_links(self):
        raw = (b'<a href="//evil.example/event/5">cross</a>'
               b'<a href="/event/123#fragment">fragment</a>'
               b'<a href="/event/1/extra">nested</a>'
               b'<a href="/event/42">valid</a>')
        self.assertEqual(probe.discover_current_list_ids(raw), ["42"])

    def test_delay_applies_after_robots_before_list_and_detail(self):
        delays = []
        result = probe.capture(
            output_dir=self.out, opener=self.opener,
            clock=lambda: "2026-11-19T03:00:00Z",
            sleeper=delays.append, execute=True, detail_id="691")
        self.assertEqual([r["role"] for r in result["receipts"]], ["LIST", "DETAIL"])
        self.assertEqual(delays, [probe.MIN_DELAY, probe.MIN_DELAY])
        self.assertEqual(self.opener.calls,
                         [probe.ROBOTS, probe.LIST, probe.ORIGIN + "/event/691"])

    def test_delay_applies_to_list_only(self):
        delays = []
        probe.capture(output_dir=self.out, opener=self.opener,
                      clock=lambda: "2026-11-19T03:00:00Z",
                      sleeper=delays.append, execute=True)
        self.assertEqual(delays, [probe.MIN_DELAY])
        self.assertEqual(self.opener.calls, [probe.ROBOTS, probe.LIST])

    def test_stale_fixed_staging_file_does_not_block_capture(self):
        # A prior crash can leave the old fixed staging filename behind.
        self.out.mkdir(parents=True)
        stale = self.out / "incoming-list.tmp"
        stale.write_bytes(b"prior-run")
        result = self.run_probe(execute=True)
        self.assertEqual([r["role"] for r in result["receipts"]], ["LIST"])
        self.assertEqual(stale.read_bytes(), b"prior-run")
        self.assertEqual(list(self.out.glob("incoming-list-*.tmp")), [])

    def test_unique_staging_files_are_removed_on_ingest_failure(self):
        # Reject immutable digest collisions without leaving new staging bytes.
        self.run_probe(execute=True)
        with self.assertRaises(FileExistsError):
            self.run_probe(execute=True)
        self.assertEqual(list(self.out.glob("incoming-list-*.tmp")), [])

    def test_detail_must_be_in_current_list(self):
        self.opener.bodies[probe.LIST] = b"<html>no matching event</html>"
        with self.assertRaisesRegex(ValueError, "DETAIL_ID_NOT_IN_CURRENT_LIST_HOLD"):
            self.run_probe(execute=True, detail_id="691")
        self.assertEqual(self.opener.calls, [probe.ROBOTS, probe.LIST])
        # The failed ID check must not erase the actual official LIST bytes.
        self.assertEqual(len(list(self.out.glob("*.bin"))), 1)
        self.assertEqual(len(list(self.out.glob("*.json"))), 2)
        self.assertIn(b"<html>no matching event</html>",
                      [p.read_bytes() for p in self.out.glob("*.bin")])

    def test_robots_raw_preserved_even_when_policy_denies_list(self):
        self.opener.bodies[probe.ROBOTS] = b"User-agent: *\nDisallow: /event\n"
        with self.assertRaisesRegex(ValueError, "ROBOTS_LIST_DENIED_HOLD"):
            self.run_probe(execute=True)
        self.assertEqual(self.opener.calls, [probe.ROBOTS])
        self.assertEqual([p.read_bytes() for p in self.out.glob("*.bin")],
                         [self.opener.bodies[probe.ROBOTS]])
        self.assertEqual(len(list(self.out.glob("*.json"))), 1)

    def test_html_robots_response_cannot_authorize_list(self):
        # A CDN HTML challenge with HTTP 200 is not a robots policy.
        self.opener.bodies[probe.ROBOTS] = b"<html><title>challenge</title></html>"
        with self.assertRaisesRegex(ValueError, "ROBOTS_INVALID_RESPONSE_HOLD"):
            self.run_probe(execute=True)
        self.assertEqual(self.opener.calls, [probe.ROBOTS])

    def test_unrelated_text_robots_response_cannot_authorize_list(self):
        self.opener.bodies[probe.ROBOTS] = b"service unavailable"
        with self.assertRaisesRegex(ValueError, "ROBOTS_INVALID_RESPONSE_HOLD"):
            self.run_probe(execute=True, detail_id="691")
        self.assertEqual(self.opener.calls, [probe.ROBOTS])

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
