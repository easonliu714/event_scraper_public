"""V44.1 queue fairness regression: stdlib only."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'show_news.py').read_text(encoding='utf-8')
module=ast.parse(source)
node=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name=='plan_detail_updates')
ns={}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(ROOT/'show_news.py'),'exec'),ns)
plan=ns['plan_detail_updates']

class DetailQueueRegression(unittest.TestCase):
    def test_untried_precedes_failed_and_fields_include_price(self):
        listed=[{'url':'https://example.org/%d'%i} for i in range(4)]
        saved={row['url']:{'date':'詳內文','location':'詳內文','price':'詳內文','description':'詳內文'} for row in listed}
        saved[listed[0]['url']]['detail_checked_at']='2026-10-23T10:00:00+08:00'
        chosen,new_count,repair_count=plan(listed,saved,0,2)
        self.assertEqual(new_count,0)
        self.assertEqual(repair_count,4)
        self.assertNotIn(listed[0],chosen)
        self.assertEqual(len(chosen),2)

    def test_failed_retry_rotates_to_back(self):
        listed=[{'url':'https://example.org/%d'%i} for i in range(4)]
        saved={row['url']:{'date':'詳內文','location':'詳內文','price':'詳內文','description':'詳內文'} for row in listed}
        first,_,_=plan(listed,saved,0,2)
        for e in first: saved[e['url']]['detail_checked_at']='2026-10-23T10:00:00+08:00'
        second,_,_=plan(listed,saved,0,2)
        self.assertEqual(set(x['url'] for x in first).intersection(x['url'] for x in second),set())

    def test_pending_new_becomes_repair_on_followup(self):
        listed=[{'url':'https://example.org/%d'%i} for i in range(5)]
        selected,new_count,repair_count=plan(listed,{},2,2)
        self.assertEqual((len(selected),new_count,repair_count),(2,5,0))
        saved={e['url']:{'date':'詳內文'} for e in listed}
        second,new_count,repair_count=plan(listed,saved,2,3)
        self.assertEqual((new_count,repair_count,len(second)),(0,5,3))

    def test_complete_event_not_in_repair_queue(self):
        listed=[{'url':'https://example.org/a'}]
        saved={listed[0]['url']:{'date':'2026-11-01','location':'台北','price':'免費','description':'完整活動簡介'}}
        selected,_,repairs=plan(listed,saved,2,2)
        self.assertEqual((selected,repairs),([],0))

if __name__=='__main__':unittest.main()
