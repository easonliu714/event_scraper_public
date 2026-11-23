"""Read-only platform audit tests."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit_quality',ROOT/'scripts/audit_quality.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class AuditTests(unittest.TestCase):
    def test_presence_not_placeholders(self):
        self.assertFalse(m.populated('詳內文'))
        self.assertFalse(m.populated('暫無詳細簡介，請點擊下方按鈕前往官網查看。'))
        self.assertTrue(m.populated('2026-12-01'))
    def test_read_only_audit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.json'
            p.write_text(json.dumps([{'platform':'A','url':'https://example.com/e/1','title':'a','date':'詳內文'}, {'platform':'B','url':'http://example.com/e/2','title':'b','price':'免費'}]),encoding='utf-8')
            before=p.read_bytes()
            self.assertEqual(m.audit(p),(2,2,1))
            self.assertEqual(before,p.read_bytes())
if __name__=='__main__': unittest.main()
