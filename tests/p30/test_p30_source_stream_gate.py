"""Offline integration of the A full-stream and B prior-receipt gates."""
import hashlib
import io
import unittest
from datetime import datetime, timezone
from scripts import p30_source_stream_gate as m


class TestSourceStreamGate(unittest.TestCase):
    def setUp(self):
        self.clock = datetime.now(timezone.utc).isoformat()
        self.html = ('<main><section><h1>' + m.TITLE + '</h1>'
                     '<a href="' + m.TICKET_URL + '">購票去</a>'
                     '<p>臺北表演藝術中心 藍盒子</p></section></main>')
        self.large = ('<script>' + 'x' * 550000 + '</script>' + self.html).encode()

    def replay(self, raw, **overrides):
        params = dict(status=200, content_type="text/html; charset=utf-8",
                      final_url=m.TPAC_URL, observed_at_utc=self.clock)
        params.update(overrides)
        return m.inspect_tpac_complete_stream(io.BytesIO(raw), **params)

    def test_large_complete_body_has_real_full_hash_not_prefix(self):
        result = self.replay(self.large)
        self.assertEqual(result["decision"], "REVIEW_DIRECT_EDGE_ONLY", result)
        self.assertEqual(result["body_bytes"], len(self.large))
        self.assertEqual(result["body_sha256"], hashlib.sha256(self.large).hexdigest())
        self.assertFalse(result["body_truncated"])
        self.assertEqual(result["native_get_this_call"], 0)
        self.assertEqual(result["formal_accepted_fields"], 0)

    def test_bound_rejects_without_full_hash(self):
        result = self.replay(self.large, max_bytes=524289)
        self.assertEqual(result["decision"], "HOLD")
        self.assertEqual(result["first_failure"],
                         "TPAC_STREAM_COMPLETE_BODY_EXCEEDS_POLICY_HOLD")
        self.assertTrue(result["body_truncated"])
        self.assertNotIn("body_sha256", result)
        self.assertIn("prefix_sha256", result)

    def test_wrong_title_link_room_and_unscoped_header_hold(self):
        cases = [
            self.html.replace(m.TITLE, "其他活動"),
            self.html.replace(m.TICKET_URL, "https://www.opentix.life/event/0"),
            self.html.replace("藍盒子", "其他場館"),
            '<header><h1>' + m.TITLE + '</h1><a href="' + m.TICKET_URL +
            '">票</a></header><main><p>藍盒子</p></main>',
        ]
        for html in cases:
            with self.subTest(html=html[:30]):
                self.assertEqual(self.replay(html.encode())["decision"], "HOLD")

    def test_transport_and_encoding_fail_closed(self):
        for options in ({"status": 302},
                        {"final_url": "https://example.org/"},
                        {"content_type": "application/json"},
                        {"content_type": "text/html; charset=big5"}):
            with self.subTest(options=options):
                self.assertEqual(self.replay(self.html.encode(), **options)["decision"],
                                 "HOLD")
        self.assertEqual(self.replay(bytes([255, 254]))["decision"], "HOLD")

    def test_songshan_historical_receipts_do_not_upgrade_identity(self):
        evidence = {
            "target_uuid": m.SONGSHAN_UUID, "same_uuid_review_lkg": 0,
            "persisted": False, "native_get_200_count": 2,
            "reason": "SONGSHAN_DETAIL_EXACT_HEADING_HOLD:h1=0,h2=0,h3=0",
            "source_receipts": [
                {"url": m.SONGSHAN_LIST, "http_status": 200, "bytes": 34242,
                 "body_sha256": "de3df20bcd78e264c7f0eff8bafedbeb39aa580d7892e738bb2eb792c68e33cb"},
                {"url": m.SONGSHAN_DETAIL, "http_status": 200, "bytes": 26506,
                 "body_sha256": "1226b2f61dd328c08a2ff456e4f36dcc20dd23ce9d18219e377bafa4d404e02d"},
            ],
        }
        out = m.audit_songshan_prior_native_receipt(evidence)
        self.assertEqual(out["decision"],
                         "PRIOR_NATIVE_HTTP_CONFIRMED_IDENTITY_STILL_HOLD")
        self.assertEqual(out["replayed_prior_http200"], 2)
        self.assertEqual(out["native_get_this_call"], 0)
        self.assertEqual(out["native_same_uuid_lkg_new"], 0)
        evidence["source_receipts"][1]["body_sha256"] = "invalid"
        self.assertEqual(m.audit_songshan_prior_native_receipt(evidence)["decision"],
                         "HOLD")


if __name__ == "__main__":
    unittest.main()
