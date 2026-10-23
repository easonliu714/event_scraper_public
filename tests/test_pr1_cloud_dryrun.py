import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest

P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dryrun',P/'scripts/pr1_cloud_dryrun.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class DryRunTests(unittest.TestCase):
    def test_authorization_fails_on_missing_or_wrong_config(self):
        good={'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'pull_request',
              'GITHUB_REPOSITORY':m.REPO_NAME,'GITHUB_HEAD_REF':m.PR_BRANCH,
              'EVENT_RADAR_TELEGRAM':'0','EVENT_RADAR_TERMUX':'0',
              'EVENT_RADAR_ACTIONS':'1','RUNNER_TEMP':'/tmp/test',
              'GITHUB_WORKSPACE':'/home/runner/work/test'}
        self.assertTrue(m.is_runner_authorized(good))
        for key, value in [('GITHUB_EVENT_NAME','schedule'),('GITHUB_HEAD_REF','main'),
                           ('EVENT_RADAR_ACTIONS','0'),('EVENT_RADAR_TELEGRAM','1'),
                           ('EVENT_RADAR_TERMUX','1')]:
            bad=dict(good);bad[key]=value;self.assertFalse(m.is_runner_authorized(bad))
    def test_workflow_has_no_write_or_main_actions(self):
        yaml=(P/'.github/workflows/event_radar_pr_dryrun.yml').read_text(encoding='utf-8')
        self.assertIn('permissions:\n  contents: read',yaml)
        self.assertIn('persist-credentials: false',yaml)
        self.assertIn('pull_request:',yaml)
        self.assertNotIn('workflow_dispatch:',yaml)
        self.assertNotIn('schedule:',yaml)
        self.assertNotIn('commit_data.sh',yaml)
        self.assertNotIn('git push',yaml)
        self.assertIn('if: always()',yaml)
    def test_synthetic_crawl_temp_only_and_no_notification(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);repo=root/'repo';repo.mkdir();(repo/'docs').mkdir()
            baseline=[{'url':'https://example.com/old','platform':'OLD','title':'Old'}]
            (repo/'docs/data.json').write_text(json.dumps(baseline))
            (repo/'event_details.py').write_text('')
            payload=r"""import json,os,pathlib
assert os.environ['EVENT_RADAR_TELEGRAM']=='0'
assert os.environ['EVENT_RADAR_TERMUX']=='0'
assert os.environ['EVENT_RADAR_ACTIONS']=='1'
assert not os.environ.get('GITHUB_TOKEN')
p=pathlib.Path('docs/data.json')
a=json.loads(p.read_text())
for i in range(24):
 a.append({'title':f'event {i}','url':f'https://example.com/{i}',
           'platform':f'P{i%3}','date':'2026-11-01','location':'Taipei',
           'price':'free','description':'desc'})
p.write_text(json.dumps(a))
"""
            (repo/'show_news.py').write_text(payload)
            original=(repo/'docs/data.json').read_bytes()
            code=m.run_live(repo,root/'sandbox',max_seconds=30)
            self.assertEqual(code,0)
            self.assertEqual((repo/'docs/data.json').read_bytes(),original)
            result=json.loads((root/'sandbox/evidence/report.json').read_text())
            self.assertTrue(result['baseline_unchanged'])
            self.assertEqual(result['added_rows'],24)
            self.assertEqual(len(result['platforms']),4)
            self.assertTrue((root/'sandbox/evidence/report.md').exists())
    def test_fail_closed_zero_events(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);repo=root/'repo';repo.mkdir();(repo/'docs').mkdir()
            (repo/'docs/data.json').write_text('[]')
            (repo/'event_details.py').write_text('')
            (repo/'show_news.py').write_text("print('no change')")
            self.assertEqual(m.run_live(repo,root/'sandbox',max_seconds=30),5)
    def test_reject_workspace_as_temp(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'docs').mkdir();(root/'docs/data.json').write_text('[]')
            with self.assertRaises(ValueError):m.run_live(root,root/'nested',30)

if __name__=='__main__':unittest.main()
