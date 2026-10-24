# -*- coding: utf-8 -*-
"""G4B: exact-source evidence tests, no outside HTTP or remote Git actions."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from unittest import TestCase, mock
from email.message import Message
from urllib import error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pr1_probe', ROOT/'scripts/pr1_source_probe.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FakeResponse:
    def __init__(self, text, content_type='text/html; charset=utf-8', length=None):
        self.stream=io.BytesIO(text.encode('utf-8'))
        self.status=200
        self.headers=Message()
        self.headers['Content-Type']=content_type
        if length is not None:self.headers['Content-Length']=str(length)
    def read(self,n=-1):return self.stream.read(n)
    def __enter__(self):return self
    def __exit__(self,*args):return False


class FakeOpener:
    def __init__(self,response):self.response=response
    def open(self,req,timeout):
        assert req.get_method()=='GET'
        assert timeout <= 15
        return self.response


class SourceProbeTests(TestCase):
    def env(self,tmp,repo):
        return {'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'pull_request',
                'GITHUB_REPOSITORY':m.REPO,'GITHUB_HEAD_REF':m.BRANCH,
                'EVENT_RADAR_TELEGRAM':'0','EVENT_RADAR_TERMUX':'0',
                'EVENT_RADAR_ACTIONS':'0', 'RUNNER_TEMP':str(tmp),'GITHUB_WORKSPACE':str(repo)}

    def test_exact_seven_source_bound_samples(self):
        rows=m.load_manifest()
        self.assertEqual(len(rows),7)
        self.assertEqual({p:sum(x['platform']==p for x in rows) for p in m.ALLOWED},
                         {'ACCUPASS':2,'FamiTicket':2,'OPENTIX':3})
        self.assertTrue(all(x['golden_status']=='UNVERIFIED_SOURCE_CAPTURE_PENDING' for x in rows))

    def test_reject_forged_cross_site_and_credentials(self):
        self.assertFalse(m.safe_target('https://www.opentix.life.attacker.net/event/1234567890123456789','OPENTIX'))
        self.assertFalse(m.safe_target('http://www.accupass.com/event/2610150106001825130082','ACCUPASS'))
        self.assertFalse(m.safe_target('https://user:pass@www.accupass.com/event/2610150106001825130082','ACCUPASS'))
        self.assertFalse(m.safe_target('https://www.opentix.life/event/1681876419374891009#frag','OPENTIX'))
        self.assertFalse(m.safe_target('https://www.opentix.life/event/1681876419374891009','ACCUPASS'))

    def test_fail_closed_runner_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);repo=r/'workspace';repo.mkdir();tmp=r/'temp';tmp.mkdir()
            good=self.env(tmp,repo)
            self.assertTrue(m.authorized(good))
            for key,value in [('GITHUB_ACTIONS','false'),('GITHUB_EVENT_NAME','schedule'),
                              ('GITHUB_REPOSITORY','other/repo'),('GITHUB_HEAD_REF','main'),
                              ('EVENT_RADAR_TELEGRAM','1'),('EVENT_RADAR_TERMUX','1'),
                              ('EVENT_RADAR_ACTIONS','1')]:
                bad=dict(good);bad[key]=value;self.assertFalse(m.authorized(bad),key)

    def test_source_html_category_product_without_guessing_price(self):
        h='<html><head><meta property="og:title" content="國家兩廳院X紅玉滿赤心雞蛋糕"></head><body><h1>雞蛋糕</h1><div>類別： 商品</div></body></html>'
        out=m.summary_from_html(h,'https://www.opentix.life/event/1681876419374891009',lambda h,u:{})
        self.assertEqual(out['official_category_label'],'商品')
        self.assertFalse(out['parser_fields_present']['date'])
        self.assertFalse(out['parser_fields_present']['price'])

    def test_source_html_official_drama_category(self):
        h='<html><body><h1>臺北戲棚</h1><div>類別： 戲劇</div></body></html>'
        out=m.summary_from_html(h,'https://www.opentix.life/event/1863403624657735681',lambda h,u:{})
        self.assertEqual(out['official_category_label'],'戲劇')

    def test_jsonld_metadata_only_and_source_event_parser(self):
        event={'@context':'https://schema.org','@type':'Event',
               'url':'https://www.accupass.com/event/2610150106001825130082',
               'startDate':'2026-12-02','location':{'name':'示範場館'},'name':'示範活動'}
        html='<html><head><script type="application/ld+json">'+json.dumps(event,ensure_ascii=False)+'</script></head><body><h1>活動</h1></body></html>'
        out=m.summary_from_html(html,event['url'],lambda h,u:{'date':'2026-12-02','location':'示範場館'})
        self.assertTrue(out['parser_fields_present']['date'])
        self.assertEqual(out['parser_date'],'2026-12-02')
        self.assertTrue(out['parser_fields_present']['location'])
        self.assertFalse(out['parser_fields_present']['price'])
        self.assertEqual(out['jsonld_event_scripts'],1)

    def test_http_get_limit_non_html_and_declared_oversize(self):
        with self.assertRaises(ValueError):m.get_public_html('https://www.opentix.life/event/1681876419374891009',FakeOpener(FakeResponse('x',content_type='application/pdf')))
        with self.assertRaises(ValueError):m.get_public_html('https://www.opentix.life/event/1681876419374891009',FakeOpener(FakeResponse('x',length=m.MAX_BYTES+1)))
        with self.assertRaises(ValueError):m.get_public_html('https://www.opentix.life/event/1681876419374891009',FakeOpener(FakeResponse('x'*(m.MAX_BYTES+1))))

    def test_runner_temp_must_be_disjoint(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);workspace=base/'workspace';workspace.mkdir()
            with self.assertRaises(ValueError):m.evidence_dir(self.env(workspace,workspace))
            (workspace/'child').mkdir()
            with self.assertRaises(ValueError):m.evidence_dir(self.env(workspace/'child',workspace))

    def test_synthetic_exact_seven_evidence_and_baseline_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);workspace=base/'workspace';workspace.mkdir();temp=base/'runner_temp';temp.mkdir()
            (workspace/'docs').mkdir()
            p=workspace/'docs/data.json';p.write_text('[{"title":"protected baseline"}]')
            before=p.read_bytes()
            example='<html><head><meta property="og:title" content="sample"></head><body><div>類別： 戲劇</div><h1>sample</h1></body></html>'
            with mock.patch.object(m,'get_public_html',return_value=(example,'a'*64,len(example))):
                with mock.patch.object(m,'summary_from_html',return_value={'official_category_label':'戲劇','parser_fields_present':{}}):
                    self.assertEqual(m.run(self.env(temp,workspace)),0)
            self.assertEqual(p.read_bytes(),before)
            out=json.loads((temp/'eventradar_pr1_g4b_probe/evidence/report.json').read_text())
            self.assertEqual(out['accessible'],7)
            self.assertTrue(out['baseline_unchanged'])
            self.assertEqual(len(out['samples']),7)
            self.assertNotIn('<html',json.dumps(out))
            self.assertIn('GOLDEN', (temp/'eventradar_pr1_g4b_probe/evidence/report.md').read_text().upper())

    def test_no_source_access_produces_hold_and_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);workspace=base/'workspace';workspace.mkdir();tmp=base/'tmp';tmp.mkdir();(workspace/'docs').mkdir()
            (workspace/'docs/data.json').write_text('[]')
            with mock.patch.object(m,'get_public_html',side_effect=error.HTTPError('https://example.com',403,'Blocked',{},None)):
                self.assertEqual(m.run(self.env(tmp,workspace)),23)
            out=json.loads((tmp/'eventradar_pr1_g4b_probe/evidence/report.json').read_text())
            self.assertEqual(out['blocked'],7)
            self.assertTrue(out['baseline_unchanged'])

    def test_readonly_workflow_has_zero_publish_actions(self):
        text=(ROOT/'.github/workflows/event_radar_pr_source_probe.yml').read_text()
        self.assertIn('contents: read',text)
        self.assertIn('persist-credentials: false',text)
        self.assertNotIn('schedule:',text)
        self.assertNotIn('workflow_dispatch:',text)
        self.assertNotIn('commit_data.sh',text)
        self.assertNotIn('git push',text)
        self.assertNotIn('show_news.sh --once',text)
        self.assertIn('if: always()',text)
