"""Offline tests for bounded one-shot TPAC native source capture (no actual GET)."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts import p30_tpac_publisher_source_once as m

ROBOTS=b"User-agent: *\nAllow: /program\n"
TITLE="沉浸式劇場《士林YES！》"
LIST=('<main><article><a href="/program/2040">'+TITLE+
      '</a></article></main>').encode()
DETAIL=('<main><article><h1>'+TITLE+'</h1>'+
        '<time datetime="2026-11-20T19:30:00+08:00">11/20</time>'+
        '</article></main>').encode()


class SourceCaptureTests(unittest.TestCase):
    def test_one_robots_list_detail_no_formal_write(self):
        calls=[]
        def fake(url):
            calls.append(url)
            return {m.ROBOTS_URL:ROBOTS,m.LIST_URL:LIST,m.DETAIL_URL:DETAIL}[url]
        with tempfile.TemporaryDirectory() as p:
            root=Path(p)
            report=m.acquire_once(root,fetch=fake)
            self.assertEqual(calls,[m.ROBOTS_URL,m.LIST_URL,m.DETAIL_URL])
            self.assertEqual(report["decision"],"RAW_SOURCE_SAVED_FOR_INDEPENDENT_REPLAY_ONLY")
            self.assertEqual(report["source_native_get"],3)
            self.assertEqual(report["exact_list_edges"],1)
            self.assertEqual(report["detail_exact_label_owned_article_count"],1)
            self.assertEqual(report["list_sha256"],hashlib.sha256(LIST).hexdigest())
            self.assertEqual((root/"tpac_2040_list.html").read_bytes(),LIST)
            self.assertFalse((root/"docs"/"data.json").exists())
            self.assertEqual(json.loads((root/"tpac_2040_source_receipt.json").read_text())["published"],0)

    def test_robots_disallow_blocks_both_source_requests(self):
        calls=[]
        def fake(url):
            calls.append(url)
            return b"User-agent: *\nDisallow: /program\n"
        with tempfile.TemporaryDirectory() as p:
            result=m.acquire_once(p,fetch=fake)
            self.assertEqual(calls,[m.ROBOTS_URL])
            self.assertIn("TPAC_ROBOTS_DISALLOW_HOLD",result["first_failure"])
            self.assertEqual(result["published"],0)
            self.assertFalse((Path(p)/"tpac_2040_list.html").exists())

    def test_first_source_error_no_retry_and_no_second_get(self):
        calls=[]
        def fake(url):
            calls.append(url)
            if url==m.ROBOTS_URL:
                return ROBOTS
            raise ValueError("TPAC_BLOCKED_403_HOLD")
        with tempfile.TemporaryDirectory() as p:
            report=m.acquire_once(p,fetch=fake)
            self.assertEqual(calls,[m.ROBOTS_URL,m.LIST_URL])
            self.assertEqual(report["decision"],"HOLD")
            self.assertEqual(report["source_native_get"],1)
            self.assertFalse((Path(p)/"tpac_2040_list.html").exists())
            self.assertIn("TPAC_BLOCKED_403_HOLD",report["first_failure"])

    def test_exact_link_missing_keeps_native_identity_unaccepted(self):
        bad=LIST.replace(b"/program/2040",b"/program/9999")
        def fake(url):
            return {m.ROBOTS_URL:ROBOTS,m.LIST_URL:bad,m.DETAIL_URL:DETAIL}[url]
        with tempfile.TemporaryDirectory() as p:
            report=m.acquire_once(p,fetch=fake)
            self.assertEqual(report["exact_list_edges"],0)
            self.assertEqual(report["detail_exact_label_owned_article_count"],0)
            self.assertEqual(report["published"],0)


if __name__=="__main__":
    unittest.main()
