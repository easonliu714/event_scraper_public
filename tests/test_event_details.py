import json
import unittest
from event_details import clean_event_title, clean_event_url, parse_detail


class DetailTests(unittest.TestCase):
    def test_jsonld_complete_event(self):
        payload={'@context':'https://schema.org','@type':'Event',
                 'url':'https://www.opentix.life/event/123',
                 'name':'測試舞台劇', 'startDate':'2026-11-06T18:00:00+08:00',
                 'endDate':'2026-11-07T20:00:00+08:00',
                 'location':{'@type':'Place','name':'國家戲劇院'},
                 'offers':{'price':'1200','priceCurrency':'TWD'},
                 'description':'這是正式活動介紹，歡迎觀賞。'}
        html='<script type="application/ld+json">'+json.dumps(payload,ensure_ascii=False)+'</script>'
        result=parse_detail(html,'https://www.opentix.life/event/123')
        self.assertEqual(result['date'],'2026-11-06 ~ 2026-11-07')
        self.assertEqual(result['location'],'國家戲劇院')
        self.assertEqual(result['price'],'NT$ 1200')
        self.assertEqual(result['title'],'測試舞台劇')

    def test_event_url_mismatch_not_accepted(self):
        payload={'@type':'Event','url':'https://other.example/event','startDate':'2026-11-01'}
        html='<script type="application/ld+json">'+json.dumps(payload)+'</script>'
        self.assertNotIn('date',parse_detail(html,'https://www.opentix.life/event/123'))

    def test_graph_event(self):
        payload={'@graph':[{'@type':'Organization','name':'test'},
                           {'@type':['Thing','Event'],'startDate':'2026-10-31','offers':{'lowPrice':500,'highPrice':1200}}]}
        r=parse_detail('<script type="application/ld+json">'+json.dumps(payload)+'</script>')
        self.assertEqual(r['date'],'2026-10-31')
        self.assertEqual(r['price'],'NT$ 500–1200')

    def test_no_booking_date_as_event_date(self):
        html='<html><body><div>早鳥優惠截止 2026-11-01</div><div>正式啟售 2026-10-10</div></body></html>'
        self.assertNotIn('date',parse_detail(html))

    def test_labeled_fallback(self):
        html='<p>活動日期：2026/11/05 - 2026/11/10</p><p>活動地點：高雄流行音樂中心</p>'
        r=parse_detail(html)
        self.assertEqual(r['date'],'2026-11-05 ~ 2026-11-10')
        self.assertEqual(r['location'],'高雄流行音樂中心')

    def test_iso_invalid_calendar_date(self):
        html='<time datetime="2026-02-31">invalid</time>'
        self.assertNotIn('date',parse_detail(html))

    def test_meta_description(self):
        html='<meta property="og:description" content="這是一場精彩的活動，歡迎大家攜伴來參與，資訊以官網公告為準。">'
        self.assertIn('description',parse_detail(html))

    def test_noise_title_exact_not_substring(self):
        self.assertIsNone(clean_event_title('立即購票'))
        self.assertEqual(clean_event_title('Learn More About Taiwan'),'Learn More About Taiwan')
        self.assertEqual(clean_event_title('活動詳情 全新展覽'),'全新展覽')

    def test_safe_kktix_url(self):
        self.assertEqual(clean_event_url('https://kktix.com/events/abc#top','KKTIX'),'https://kktix.com/events/abc')
        self.assertIsNone(clean_event_url('https://evil.example/events/abc','KKTIX'))

    def test_safe_utk_link(self):
        self.assertEqual(clean_event_url('https://tixfun.com/UTK0201_?PRODUCT_ID=Q023ZQIS','TixFun售票網'),
                         'https://tixfun.com/UTK0201_?PRODUCT_ID=Q023ZQIS')
        self.assertIsNone(clean_event_url('https://tixfun.com/UTK0201_','TixFun售票網'))

    def test_filter_navigation(self):
        for platform,url in [('華山1914','https://www.huashan1914.com/exhibition'),
                             ('ibon','https://ticket.ibon.com.tw/Activity/Index'),
                             ('StrollTimes','https://strolltimes.com/about'),
                             ('ACCUPASS','https://www.accupass.com/search?q=aaa')]:
            with self.subTest(platform=platform):
                self.assertIsNone(clean_event_url(url,platform))

    def test_no_http_or_javascript_url(self):
        self.assertIsNone(clean_event_url('http://www.opentix.life/event/123','OPENTIX'))
        self.assertIsNone(clean_event_url('javascript:alert(1)','OPENTIX'))

    def test_price_free(self):
        r=parse_detail('<script type="application/ld+json">{"@type":"Event","offers":{"price":0,"priceCurrency":"TWD"}}</script>')
        self.assertEqual(r['price'],'免費')


if __name__=='__main__': unittest.main()
