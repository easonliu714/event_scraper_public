"""Offline fail-closed contracts; no live HTTP in tests."""
import unittest
from scripts import p30_accupass_native_gate as gate


class TestAccupassSource(unittest.TestCase):
    def setUp(self):
        self.link = "https://www.accupass.com/event/" + gate.EVENT_ID + "?utm_source=web"
        self.listing = ('<main><a href="' + self.link + '"><span>' +
                        gate.EXPECTED_TITLE + '</span></a></main>')
        self.detail = "<main><article><h1>" + gate.EXPECTED_TITLE + "</h1></article></main>"

    def test_same_id_title_review_only(self):
        out = gate.inspect_same_id(self.listing, self.detail)
        self.assertEqual(out["same_id_review"], 1)
        self.assertEqual(out["formal_accepted_fields"], 0)
        self.assertEqual(out["decision"], "REVIEW_NON_SESSION_ONLY")

    def test_no_list_id_edge_holds(self):
        self.assertEqual(gate.inspect_same_id("<main></main>", self.detail)["same_id_review"], 0)

    def test_cross_id_never_matches(self):
        wrong = self.listing.replace(gate.EVENT_ID, "2606282259461938560272")
        self.assertEqual(gate.inspect_same_id(wrong, self.detail)["same_id_review"], 0)

    def test_global_heading_cannot_establish_event_local_identity(self):
        out = gate.inspect_same_id(self.listing, "<header><h1>" + gate.EXPECTED_TITLE + "</h1></header>")
        self.assertEqual(out["first_failure"], "ACCUPASS_DETAIL_MAIN_LOCAL_EXACT_TITLE_HOLD")

    def test_wrong_title_and_duplicate_query_hold(self):
        self.assertEqual(gate.inspect_same_id(self.listing.replace("八十八石佛", "九十九石佛"),
                                              self.detail)["same_id_review"], 0)
        doubled = self.listing.replace("</main>", '<a href="' + self.link.replace(
            "utm_source=web", "utm_medium=search") + '">' + gate.EXPECTED_TITLE + "</a></main>")
        self.assertEqual(gate.inspect_same_id(doubled, self.detail)["same_id_review"], 0)

    def test_no_checkout_foreign_query_or_fragment(self):
        for url in ("https://evil.example/event/" + gate.EVENT_ID,
                    "https://www.accupass.com/event/" + gate.EVENT_ID + "/registrations/new",
                    self.link + "&session=1", self.link + "#checkout"):
            with self.subTest(url=url):
                self.assertIsNone(gate.exact_public_event_url(url))



class TestAccupassRobotsAuthority(unittest.TestCase):
    """The previous permissive text/* policy could treat an HTML HOME as robots."""

    class Response:
        status = 200
        def __init__(self, url, content_type, raw):
            self.url, self.headers, self.raw = url, {"Content-Type": content_type}, raw
        def geturl(self):
            return self.url
        def read(self, cap):
            return self.raw[:cap]
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    def test_robots_html_fallback_rejected_before_policy(self):
        from unittest.mock import Mock
        opener = Mock()
        opener.open.return_value = self.Response(
            "https://www.accupass.com/robots.txt", "text/html",
            b"<html><body>HOME</body></html>")
        with self.assertRaisesRegex(ValueError, "ACCUPASS_ROBOTS_MIME_HOLD"):
            gate.public_get(opener, "https://www.accupass.com/robots.txt",
                            131072, "text/plain")

    def test_list_plain_text_rejected_before_html_parser(self):
        from unittest.mock import Mock
        opener = Mock()
        opener.open.return_value = self.Response(
            gate.LIST_URL, "text/plain", b"User-agent: *\nAllow: /\n")
        with self.assertRaisesRegex(ValueError, "ACCUPASS_HTML_MIME_HOLD"):
            gate.public_get(opener, gate.LIST_URL, gate.MAX_BODY, "text/html")

    def test_robots_other_agent_cannot_default_allow(self):
        receipt = {"content_type": "text/plain"}
        for robots in ("User-agent: OtherBot\nAllow: /\n",
                       "User-agent: *\n",
                       "<html><body>User-agent: *\nAllow: /</body></html>"):
            with self.subTest(robots=robots):
                with self.assertRaisesRegex(ValueError, "ACCUPASS_ROBOTS_.*_HOLD"):
                    gate.checked_robots_policy(robots, receipt)

    def test_applicable_robots_rules_still_enforce_disallow(self):
        receipt = {"content_type": "text/plain"}
        policy = gate.checked_robots_policy(
            "User-agent: *\nDisallow: /search\nAllow: /event/\n", receipt)
        self.assertFalse(policy.can_fetch(gate.USER_AGENT, gate.LIST_URL))
        self.assertTrue(policy.can_fetch(
            gate.USER_AGENT, "https://www.accupass.com" + gate.DETAIL_PATH))

    def test_robots_and_list_identical_body_transport_not_list(self):
        from unittest.mock import patch
        policy = b"User-agent: *\nAllow: /\n"
        class Opener:
            def __init__(self):
                self.calls = []
            def open(self, request, timeout):
                url = request.full_url
                self.calls.append(url)
                return TestAccupassRobotsAuthority.Response(
                    url, "text/plain" if url.endswith("robots.txt") else "text/html",
                    policy)
        opener = Opener()
        with patch.object(gate.urllib.request, "build_opener", return_value=opener):
            result = gate.run_native_once()
        self.assertEqual(len(opener.calls), 2)
        self.assertEqual(result["native_http200"], 1)
        self.assertEqual(result["native_list"], 0)
        self.assertEqual(result["native_detail"], 0)
        self.assertIn("ACCUPASS_ROBOTS_LIST_IDENTICAL_BODY_HOLD", result["first_failure"])
        self.assertEqual(result["formal_accepted_fields"], 0)
        self.assertEqual(result["published"], 0)


if __name__ == "__main__":
    unittest.main()
