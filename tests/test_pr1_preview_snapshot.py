import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sp = importlib.util.spec_from_file_location('preview', ROOT/'scripts/pr1_preview_snapshot.py')
m = importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)

class PreviewTests(unittest.TestCase):
    def test_guard_authorized_and_unauthorized(self):
        env={'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'pull_request',
             'GITHUB_REPOSITORY':m.REPO,'GITHUB_HEAD_REF':m.BRANCH,
             'EVENT_RADAR_TELEGRAM':'0','EVENT_RADAR_TERMUX':'0','EVENT_RADAR_ACTIONS':'1',
             'RUNNER_TEMP':'/tmp/preview', 'GITHUB_WORKSPACE':'/tmp/repo'}
        ev={'pull_request':{'number':1,'head':{'ref':m.BRANCH,'sha':'a'*40,
             'repo':{'full_name':m.REPO}},'base':{'ref':'main'}}}
        self.assertTrue(m.guard_env(env,ev))
        for key in ('GITHUB_ACTIONS','GITHUB_EVENT_NAME','GITHUB_REPOSITORY','GITHUB_HEAD_REF',
                    'EVENT_RADAR_TELEGRAM','EVENT_RADAR_TERMUX','EVENT_RADAR_ACTIONS'):
            e=env.copy();e[key]='something_bad';self.assertFalse(m.guard_env(e,ev),key)
        ev['pull_request']['number']=2;self.assertFalse(m.guard_env(env,ev))
    def test_unsafe_urls_rejected(self):
        self.assertFalse(m.safe_url('javascript:alert(1)'))
        self.assertFalse(m.safe_url('http://example.com'))
        self.assertFalse(m.safe_url('https://name:password@example.com/a'))
        self.assertFalse(m.safe_url('https://example.com/x\nxx'))
        self.assertTrue(m.safe_url('https://www.accupass.com/event/123'))
    def test_rows_are_pwa_schema_and_html_escaped(self):
        inp=[{'url':'https://example.com/a','title':'<img onerror=alert(1)>',
              'platform':'P1','price':'" onclick="alert(1)',
              'img_url':'javascript:alert(1)', 'sensitive_private_key':'LEAK'},
             {'url':'javascript:bad','title':'BAD','platform':'P1'},
             {'url':'https://example.com/a','title':'DUP','platform':'P1'}]
        rows,rejected=m.export_rows(inp)
        self.assertEqual((len(rows),rejected),(1,2))
        self.assertNotIn('sensitive_private_key',rows[0])
        self.assertIn('&lt;img',rows[0]['title'])
        self.assertIn('&quot;',rows[0]['price'])
        self.assertEqual(rows[0]['img_url'],'')
    def test_fail_closed_on_bad_evidence(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p);src=root/'data.json'
            src.write_text(json.dumps([{'title':'T','url':f'https://a.example/{i}','platform':'P'} for i in range(25)]))
            report={'changed_or_new_rows':25,'baseline_unchanged':True,'process_exit_code':0,
                    'process_timeout':False,'started_data_sha256':'0'*64,'output_data_sha256':m.sha(src)}
            with self.assertRaisesRegex(ValueError,'OUTPUT_SHA'):
                m.export_snapshot(src,root/'export',expected_source_sha='0'*64,source_head='a'*40,report=report)
            report['baseline_unchanged']=False
            with self.assertRaisesRegex(ValueError,'LIVE_DRYRUN'):
                m.export_snapshot(src,root/'export',expected_source_sha=m.sha(src),source_head='a'*40,report=report)
    def test_successful_sanitized_export_with_provenance(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p);src=root/'data.json'
            src.write_text(json.dumps([{'title':f'A{i}','url':f'https://a.example/{i}',
               'platform':f'P{i%3}','date':'2026-11-01','scraped_at':'2026-10-23T12:00:00+08:00'} for i in range(28)]))
            report={'changed_or_new_rows':28,'added_rows':28,'baseline_unchanged':True,
                'process_exit_code':0,'process_timeout':False,'started_data_sha256':'0'*64,
                'finished_at_utc':'2026-10-23T04:00:00+00:00'}
            meta=m.export_snapshot(src,root/'export',expected_source_sha=m.sha(src),source_head='a'*40,report=report)
            self.assertEqual(meta['preview_rows'],28)
            self.assertTrue(meta['public_unverified'])
            self.assertEqual(meta['source_head_sha'],'a'*40)
            self.assertEqual(m.sha(root/'export/data.json'),meta['preview_data_sha256'])
    def test_workflow_explicitly_readonly_with_artifact(self):
        y=(ROOT/'.github/workflows/event_radar_pr_preview_snapshot.yml').read_text()
        self.assertIn('permissions:\n  contents: read',y)
        self.assertIn('persist-credentials: false',y)
        self.assertIn('pull_request:',y)
        self.assertNotIn('pull_request_target:',y)
        self.assertNotIn('git push',y)
        self.assertNotIn('commit_data.sh',y)
        self.assertNotIn('schedule:',y)
        self.assertNotIn('workflow_dispatch:',y)
        self.assertIn('eventradar-pr1-pwa-preview-snapshot',y)

if __name__=='__main__':unittest.main()
