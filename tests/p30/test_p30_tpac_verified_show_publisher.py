"""Synthetic strict roles; the separate CI runs archived real native replay."""
import hashlib
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from scripts.p30_tpac_verified_show_publisher import parse_verified_program

NOW=datetime(2026,11,8,13,18,tzinfo=timezone.utc)
TITLE="沉浸式劇場《士林YES！》"


def example():
    li=('<a class="card-program" href="/program/2040" title="'+TITLE+'">'
        '<div class="card-program__text-title">'+TITLE+'</div>'
        '<div class="card-program__text-date">2026-11-19 - 2026-11-28</div>'
        '</a>').encode()
    de=('<main><article class="page-program__article"><h1>'+TITLE+'</h1>'
        '<div class="page-program__article-top">2026-11-20 - 2026-11-29</div>'
        '</article><div class="page-program__aside-place-venue"><h3>場地</h3>'
        '<p>藍盒子；實際一樓小戲台</p></div>'
        '<div class="page-program__aside-place-showtimes"><h3>場次</h3><ul>'
        '<li><p>2026-11-20 (五) 19:30</p></li>'
        '<li><p>2026-11-21 (六) 12:30</p></li></ul></div></main>').encode()
    r={'kind':'EVENTRADAR_TPAC_2040_FIRST_PARTY_ONE_SHOT',
       'list_url':'https://tpac.org.taipei/program',
       'detail_url':'https://tpac.org.taipei/program/2040',
       'source_native_get':3,'decision':'RAW_SOURCE_SAVED_FOR_INDEPENDENT_REPLAY_ONLY',
       'started_at':'2026-11-08T13:15:54Z',
       'list_bytes':len(li),'detail_bytes':len(de),
       'list_sha256':hashlib.sha256(li).hexdigest(),
       'detail_sha256':hashlib.sha256(de).hexdigest()}
    return li,de,r


class StrictTPACPublisherTests(unittest.TestCase):
    def test_source_qualified_core_but_conflicting_period_is_quarantined(self):
        li,de,r=example()
        v=parse_verified_program(li,de,r,NOW)
        self.assertEqual(v['decision'],'SOURCE_QUALIFIED_CORE_REQUIRES_INDEPENDENT_RELEASE')
        self.assertEqual(v['accepted_roles'],['EVENT_TITLE','NEXT_EVENT_SHOW_START'])
        self.assertEqual(v['record']['date'],'2026-11-20 19:30')
        self.assertFalse(v['record']['published'])
        self.assertFalse(v['record']['golden_accepted'])
        self.assertEqual(v['record']['price'],'')
        self.assertIn('LIST_DETAIL_EVENT_PERIOD_RANGE_CONFLICT_HOLD',v['hold_fields'])
        self.assertEqual(v['all_showtimes'],2)

    def test_source_and_date_mismatch_fail_closed(self):
        li,de,r=example()
        bad=de.replace(b'(\xe4\xba\x94)',b'(\xe4\xb8\x80)')
        r['detail_bytes']=len(bad)
        r['detail_sha256']=hashlib.sha256(bad).hexdigest()
        self.assertEqual(parse_verified_program(li,bad,r,NOW)['first_failure'],
                         'TPAC_SHOW_WEEKDAY_OR_DETAIL_PERIOD_HOLD')
        li,de,r=example()
        wrong=de.replace(b'2026-11-20 (\xe4\xba\x94)',b'2026-12-30 (\xe4\xba\x94)')
        r['detail_bytes']=len(wrong);r['detail_sha256']=hashlib.sha256(wrong).hexdigest()
        self.assertEqual(parse_verified_program(li,wrong,r,NOW)['decision'],'HOLD')

    def test_sha_replay_stale_or_wrong_detail_id_hold(self):
        li,de,r=example()
        self.assertEqual(parse_verified_program(li,de+b'!',r,NOW)['first_failure'],
                         'TPAC_NATIVE_SOURCE_SHA_HOLD')
        li,de,r=example();r['started_at']='2026-11-05T12:00:00Z'
        self.assertEqual(parse_verified_program(li,de,r,NOW)['first_failure'],
                         'TPAC_NATIVE_FRESHNESS_HOLD')
        li,de,r=example();r['detail_url']='https://tpac.org.taipei/program/9999'
        self.assertEqual(parse_verified_program(li,de,r,NOW)['first_failure'],
                         'TPAC_EXACT_LIST_ID_EDGE_HOLD')

    def test_unlabeled_or_duplicated_showtimes_hold(self):
        li,de,r=example()
        bad=de.replace('2026-11-20 (五) 19:30'.encode(),
                       '2026-11-20 開賣 19:30'.encode())
        r['detail_bytes']=len(bad);r['detail_sha256']=hashlib.sha256(bad).hexdigest()
        self.assertEqual(parse_verified_program(li,bad,r,NOW)['first_failure'],
                         'TPAC_SHOW_ROLE_LABEL_HOLD')


if __name__=='__main__':
    unittest.main()
