"""G5H source-bound JSON-LD provenance regression tests (offline and safe)."""
import json
import unittest
import warnings
from bs4 import MarkupResemblesLocatorWarning
from event_details import parse_detail, clean_text

PAGE='https://www.accupass.com/event/2610150106001825130082'
OTHER='https://www.accupass.com/event/2610040452086680116600'

def page(events):
    return '<script type="application/ld+json">'+json.dumps({'@graph':events},ensure_ascii=False)+'</script>'

def ev(**kw):
    return {'@type':'Event',**kw}

class G5HParserIntegration(unittest.TestCase):
    def test_01_do_not_select_unattributed_multi_events(self):
        d=parse_detail(page([ev(startDate='2021-06-11',name='Wrong'),ev(startDate='2026-10-24',name='Second')]),PAGE)
        self.assertNotIn('date',d)
        self.assertNotIn('title',d)
    def test_02_explicit_page_url_wins_over_other(self):
        d=parse_detail(page([ev(url=OTHER,startDate='2021-06-11'),ev(url=PAGE,startDate='2026-10-24')]),PAGE)
        self.assertEqual(d['date'],'2026-10-24')
    def test_03_unattributed_candidate_cannot_preempt_matching_event(self):
        d=parse_detail(page([ev(startDate='2021-06-11'),ev(url=PAGE,startDate='2026-10-24')]),PAGE)
        self.assertEqual(d['date'],'2026-10-24')
    def test_04_url_mismatch_no_fields(self):
        d=parse_detail(page([ev(url=OTHER,startDate='2021-06-11')]),PAGE)
        self.assertNotIn('date',d)
    def test_05_single_without_url_legacy_compatible(self):
        d=parse_detail(page([ev(startDate='2026-10-24')]),PAGE)
        self.assertEqual(d['date'],'2026-10-24')
    def test_06_range(self):
        d=parse_detail(page([ev(url=PAGE,startDate='2026-10-24',endDate='2026-11-15')]),PAGE)
        self.assertEqual(d['date'],'2026-10-24 ~ 2026-11-15')
    def test_07_kktix_location_and_free(self):
        d=parse_detail(page([ev(url=PAGE,startDate='2026-07-03',endDate='2026-07-26',
             location={'@type':'Place','name':'新竹市影像博物館'},offers={'price':'0','priceCurrency':'TWD'})]),PAGE)
        self.assertEqual(d['location'],'新竹市影像博物館')
        self.assertEqual(d['price'],'免費')
    def test_08_plain_url_warning_is_removed(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always',MarkupResemblesLocatorWarning)
            self.assertEqual(clean_text(PAGE),PAGE)
        self.assertFalse(any(issubclass(x.category,MarkupResemblesLocatorWarning) for x in caught))
    def test_09_html_remains_sanitized(self):
        self.assertEqual(clean_text('<b>活動</b> &amp; 展覽'),'活動 & 展覽')
    def test_10_plain_entity_decodes(self):
        self.assertEqual(clean_text('伊莎貝拉&amp;吳站長'),'伊莎貝拉&吳站長')
    def test_11_do_not_invent_body_date(self):
        self.assertNotIn('date',parse_detail('<p>早鳥售票截止 2021-06-11</p>',PAGE))
    def test_12_single_mismatch_plus_url_less_fails_closed(self):
        d=parse_detail(page([ev(url=OTHER,startDate='2021-06-11'),ev(startDate='2026-10-24')]),PAGE)
        self.assertNotIn('date',d)

if __name__ == '__main__':
    unittest.main()
