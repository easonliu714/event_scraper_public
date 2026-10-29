"""G5H R1: enforce exact G5G parser binding across intentional parser updates."""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
import event_details
import g5g_field_probe as probe

NEW='ed425662b4f2ce2032a0fa0c3e83075842f30767'
OLD='d5b8b6600aff987f350ea211dd293ec2ab3e2ee0'
URL='https://www.accupass.com/event/2610150106001825130082'
def blob(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()

class G5HG5GBinding(unittest.TestCase):
    def test_01_new_parser_exact_blob(self):
        self.assertEqual(blob(ROOT/'event_details.py'),NEW)
    def test_02_probe_declared_blob_exact(self):
        self.assertEqual(probe.EXPECTED_PARSER_BLOB,NEW)
    def test_03_old_parser_not_accepted(self):
        self.assertNotEqual(probe.EXPECTED_PARSER_BLOB,OLD)
    def test_04_sha_provenance_not_skipped(self):
        self.assertIn("blob_hash(REPO/'event_details.py') != EXPECTED_PARSER_BLOB",
                      (ROOT/'scripts/g5g_field_probe.py').read_text())
    def test_05_source_gate_real_manifest(self):
        targets=probe.source_gate(ROOT/'fixtures/g5f_probe_targets.json')
        self.assertEqual(len(targets),11)
    def test_06_reject_parser_drift(self):
        with patch.object(probe, 'blob_hash', return_value=OLD):
            with self.assertRaisesRegex(ValueError,'HOLD EVENT_DETAILS_BLOB_CHANGED'):
                probe.source_gate(ROOT/'fixtures/g5f_probe_targets.json')
    def test_07_mixed_unattributed_events_no_invented_date(self):
        html=("""<script type="application/ld+json">[
            {"@type":"Event","name":"unrelated","startDate":"2025-01-01"},
            {"@type":"Event","name":"unrelated2","startDate":"2025-01-02"}
        ]</script>""")
        p=probe.analyze_html(html.encode(),URL)
        self.assertFalse(p['fields_present']['date'])
    def test_08_matched_event_date(self):
        html=("""<script type="application/ld+json">[
         {"@type":"Event","url":"https://other.example/other","startDate":"2025-01-01"},
         {"@type":"Event","url":"https://www.accupass.com/event/2610150106001825130082","startDate":"2026-10-24"}
        ]</script>""")
        p=probe.analyze_html(html.encode(),URL)
        self.assertEqual(p['fields']['date'],'2026-10-24')
    def test_09_no_raw_html_in_result(self):
        p=probe.analyze_html(b'<title>Sample</title>',URL)
        self.assertNotIn('raw_html',p)
    def test_10_json_output_bound(self):
        self.assertLessEqual(probe.MAX_FIELD['date'],100)
        self.assertLessEqual(probe.MAX_BYTES,350000)
    def test_11_runtime_does_not_save_html(self):
        s=(ROOT/'scripts/g5g_field_probe.py').read_text()
        self.assertIn("'no_html_saved':True",s)
        self.assertIn("'auto_hidden':0",s)
    def test_12_no_unrestricted_redirect(self):
        self.assertIsNone(probe.NoRedirect().redirect_request(None,None,302,'',{},URL))
    def test_13_manifest_pinned(self):
        self.assertEqual(len(probe.EXPECTED_G5F_MANIFEST),64)
        self.assertEqual(len(probe.load_targets(ROOT/'fixtures/g5f_probe_targets.json')),11)
    def test_14_output_parser_identity_versioned(self):
        s=(ROOT/'scripts/g5g_field_probe.py').read_text()
        self.assertIn("'source_parser_blob_sha':EXPECTED_PARSER_BLOB",s)
    def test_15_workflow_no_main_writer(self):
        s=(ROOT/'.github/workflows/event_radar_pr_g5g_field_ab.yml').read_text()
        self.assertIn('contents: read',s)
        self.assertNotIn('schedule:',s)
        self.assertNotIn('git push',s)
        self.assertNotIn('data.json',s)
    def test_16_failure_on_bad_manifest(self):
        with patch.object(probe,'MANIFEST_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'HOLD G5F_MANIFEST_CONTRACT'):
                probe.source_gate(ROOT/'fixtures/g5f_probe_targets.json')

if __name__=='__main__':unittest.main()
