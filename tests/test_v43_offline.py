import ast, json, os, tempfile, unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
MODULE = ast.parse((ROOT/'show_news.py').read_text(encoding='utf-8'))

def load_functions(*names):
    nodes = [node for node in MODULE.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names]
    import re
    ns={'Path':Path,'json':json,'os':os,'datetime':datetime,'re':re,'append_log_run':lambda msg:None,
        'get_event_region':lambda p, loc, title='':'Unknown'}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'isolated_functions','exec'),ns)
    return ns

class OfflineTests(unittest.TestCase):
    def test_no_tls_verification_bypass(self):
        text=(ROOT/'show_news.py').read_text(encoding='utf-8')
        self.assertNotIn('verify=False',text)
        self.assertNotIn('ssl=False',text)
    def test_invalid_existing_json_not_overwritten(self):
        import os
        f=load_functions('save_data_to_docs')['save_data_to_docs']
        with tempfile.TemporaryDirectory() as temp:
            cwd=os.getcwd();os.chdir(temp)
            try:
                Path('docs').mkdir();Path('docs/data.json').write_text('NOT_JSON',encoding='utf-8')
                self.assertIsNone(f([{'url':'u','title':'t','platform':'p'}]))
                self.assertEqual(Path('docs/data.json').read_text(), 'NOT_JSON')
            finally:os.chdir(cwd)
    def test_good_old_fields_kept_and_historical_rows(self):
        fn=load_functions('save_data_to_docs')['save_data_to_docs']
        old=[{'url':'https://test/1','title':'舊活動','platform':'P1','date':'2026-11-09','location':'北流','price':'NT$ 800','scraped_at':'2026-07-01T20:00:00+08:00'},
             {'url':'https://test/retired','title':'舊資料','platform':'P2','scraped_at':'2026-07-01T20:00:00+08:00'}]
        fresh=[{'url':'https://test/1','title':'舊活動','platform':'P1','date':'詳內文','location':'詳內文','price':'詳內文'}]
        fresh += [{'url':f'https://test/new/{i}','title':f'活動{i}','platform':f'P{i%3}'} for i in range(30)]
        with tempfile.TemporaryDirectory() as temp:
            cwd=os.getcwd();os.chdir(temp)
            try:
                Path('docs').mkdir(); Path('docs/data.json').write_text(json.dumps(old,ensure_ascii=False),encoding='utf-8')
                self.assertIsNotNone(fn(fresh))
                out=json.loads(Path('docs/data.json').read_text(encoding='utf-8'))
                mp={x['url']:x for x in out}
                self.assertEqual(mp['https://test/1']['date'],'2026-11-09')
                self.assertEqual(mp['https://test/1']['price'],'NT$ 800')
                self.assertIn('https://test/retired',mp)
                self.assertEqual(len(out),32)
            finally:os.chdir(cwd)
    def test_legacy_daemon_schedule_retained(self):
        text=(ROOT/'show_news.py').read_text(encoding='utf-8')
        for hr in ('09:00','15:00','21:00'):self.assertIn('at("'+hr+'")',text)
    def test_old_event_refresh_logic_present(self):
        text=(ROOT/'show_news.py').read_text(encoding='utf-8')
        self.assertIn('DETAIL_REPAIR_LIMIT',text)
        self.assertIn('fresh[:new_budget]',text)
        self.assertIn('repairs[:repair_budget]',text)
        self.assertIn('plan_detail_updates',text)

if __name__=='__main__':unittest.main()
