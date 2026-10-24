# -*- coding: utf-8 -*-
"""PR1 G4A: evidence-bound, source-specific list guard regressions."""
import ast
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'show_news.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)


def function_body(name):
    node = next(n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    return node


def extracted_guard():
    node = function_body('is_known_non_event_list_entry')
    defs = next(n for n in TREE.body if isinstance(n, ast.Assign) and
                any(isinstance(t, ast.Name) and t.id == 'KNOWN_NON_EVENT_TITLES' for t in n.targets))
    ns = {'re': re, 'frozenset': frozenset}
    exec(compile(ast.Module(body=[defs, node], type_ignores=[]), '<isolated>', 'exec'), ns)
    return ns['is_known_non_event_list_entry']


class ListGuardTests(unittest.TestCase):
    def test_accupass_seven_distinct_theme_urls(self):
        n = function_body('fetch_accupass_events_list')
        assign = next(x for x in n.body if isinstance(x, ast.Assign) and
                      any(isinstance(t,ast.Name) and t.id == 'theme_urls' for t in x.targets))
        urls = ast.literal_eval(assign.value)
        self.assertEqual(len(urls), 7)
        self.assertEqual(len(set(urls)), 7)
        self.assertTrue(all(u.startswith('https://www.accupass.com/') for u in urls))
        self.assertTrue(any('c=arts&' in u for u in urls))
        self.assertTrue(any('c=travel&' in u for u in urls))
        self.assertTrue(any('area=north' in u for u in urls))
        self.assertTrue(all(u.count('https://') == 1 for u in urls))

    def test_exact_source_navigation_titles_removed(self):
        check = extracted_guard()
        for platform, title in [('年代售票', 'slide'),('中正紀念堂','我要報名'),('松山文創','展演活動')]:
            with self.subTest(platform=platform):
                self.assertTrue(check({'platform':platform,'title':title,'url':'https://example.org/event'}))

    def test_navigation_query_link_removed_regardless_of_title(self):
        check = extracted_guard()
        self.assertTrue(check({'platform':'中正紀念堂','title':'文化藝術報名','url':
                              'https://event.culture.tw/mocweb/reg/CKSMH/QueryReg.init.ctr?dataVo.actKind=002'}))
        self.assertFalse(check({'platform':'中正紀念堂','title':'自由花蕊','url':
                               'https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId=51331'}))

    def test_similar_legitimate_titles_preserved(self):
        check = extracted_guard()
        for platform,title in [('年代售票','slide guitar 現場演出'),('中正紀念堂','我要報名｜工藝講座'),
                               ('松山文創','展演活動：精彩展覽'),('OPENTIX','展演活動'),('KidsClub','slide')]:
            with self.subTest(platform=platform,title=title):
                self.assertFalse(check({'platform':platform,'title':title,'url':'https://example.org/event'}))

    def test_guard_is_not_mutating_saved_historical_data(self):
        node=function_body('check_and_notify')
        src=ast.get_source_segment(SOURCE,node)
        self.assertIn('PR1_G4A_NAVIGATION_FILTER',src)
        self.assertIn('all_list_events = [e for e in all_list_events if not is_known_non_event_list_entry(e)]',src)
        self.assertNotIn('del existing_rows',src)
        self.assertNotIn('git push',src)
        self.assertNotIn('os.remove',src)

    def test_known_positive_evidence_remains(self):
        check=extracted_guard()
        for platform,title,url in [
            ('ACCUPASS','漫才 Open Mic','https://www.accupass.com/event/2610040452086680116600'),
            ('FamiTicket','屏菸1936文化基地｜屏東縣立美術館','https://www.famiticket.com.tw/Home/Activity/Info/demo'),
            ('OPENTIX','國家兩廳院X紅玉滿赤心雞蛋糕','https://www.opentix.life/event/1681876419374891009'),
        ]:
            self.assertFalse(check({'platform':platform,'title':title,'url':url}))
        # OPENTIX's example is a *product*, flagged for later category validation;
        # this Gate deliberately does not invent a new product-vs-event rule.

    def test_source_ast_valid_and_version_constant_unchanged(self):
        n=next(n for n in TREE.body if isinstance(n,ast.Assign) and
               any(isinstance(t,ast.Name) and t.id=='VERSION' for t in n.targets))
        self.assertEqual(ast.literal_eval(n.value),'V44.2-CLOUD-GATE3')
        self.assertFalse(any('\t' in ln for ln in SOURCE.splitlines()))

if __name__ == '__main__': unittest.main()
