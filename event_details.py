"""Conservative event-detail extraction. Unknown fields remain unset, never guessed.

Uses JSON-LD Event first, then event-specific DOM metadata/labels.
All parsing is deterministic and can be tested without network access.
"""
import html as html_entities
import json
import re
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

DATE_RE = re.compile(r'(?:19|20)\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}(?:日)?')
SKIP = {'', '詳內文', 'None', 'null', 'undefined', '請選擇', '敬請期待', '待公布'}
NOISE = {'立即購票', '詳細內容', 'Read More', '活動詳情', '查看更多', '報名', '購票',
         '更多詳情', '交通資訊', '回首頁', '網站導覽', 'Facebook', 'Instagram'}


def clean_text(value, limit=1000):
    if not isinstance(value, str):
        return None
    # Do not feed plain URLs to BeautifulSoup: it emits MarkupResemblesLocatorWarning.
    # Only markup requires an HTML parser; entities in plain text still get decoded.
    if '<' in value:
        value = BeautifulSoup(value, 'html.parser').get_text(' ', strip=True)
    else:
        value = html_entities.unescape(value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value[:limit] if value and value not in SKIP else None


def clean_event_url(url, platform):
    """Only genuine same-site event links; no navigation, search, or tracking pages."""
    if not isinstance(url, str):
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        return None
    host = parsed.hostname.lower().removeprefix('www.')
    platforms = {
        'KKTIX': ('kktix.com',), 'ACCUPASS': ('accupass.com',),
        '拓元售票': ('tixcraft.com',), '寬宏': ('kham.com.tw',),
        'OPENTIX': ('opentix.life',), 'UDN售票網': ('tickets.udnfunlife.com',),
        'FamiTicket': ('famiticket.com.tw',), '年代售票': ('ticket.com.tw',),
        'TixFun售票網': ('tixfun.com',), 'Event Go': ('eventgo.bnextmedia.com.tw',),
        'BeClass': ('beclass.com',), 'ibon': ('ticket.ibon.com.tw',),
        '華山1914': ('huashan1914.com',), '松山文創': ('songshanculturalpark.org',),
        'KidsClub': ('kidsclub.com.tw',), '台北世貿': ('twtc.com.tw',),
        '中正紀念堂': ('cksmh.gov.tw', 'event.culture.tw'),
        'iNDIEVOX': ('indievox.com',), 'StrollTimes': ('strolltimes.com',)
    }
    allowed = platforms.get(platform)
    if not allowed or not any(host == h or host.endswith('.' + h) for h in allowed):
        return None
    path = parsed.path.rstrip('/').lower()
    if path in ('', '/', '/event', '/events', '/activity', '/exhibition', '/activity/index'):
        return None
    bad_path = ('/category/', '/tag/', '/search/', '/login', '/register', '/contact',
                '/about', '/privacy', '/terms', '/product-category/', '/courses/category/',
                '/activity/search', '/events?')
    if any(q in path for q in bad_path):
        return None
    if platform in ('寬宏', 'UDN售票網', '年代售票', 'TixFun售票網') and 'product_id=' not in parsed.query.lower():
        return None
    if platform == '華山1914' and '/exhibition/' not in path:
        return None
    if platform == '松山文創' and not re.search(r'/exhibition/[^/]+', path):
        return None
    if platform == 'KKTIX' and '/events/' not in path:
        return None
    if platform == 'ACCUPASS' and '/event/' not in path:
        return None
    if platform == 'ibon' and ('/index' in path or '/search' in path):
        return None
    return parsed._replace(fragment='').geturl()


def clean_event_title(raw):
    title = clean_text(raw, 250)
    if not title:
        return None
    title = re.sub(r'^(?:event-)?banner-', '', title, flags=re.I)
    title = re.sub(r'^(?:立即購票|活動詳情|詳細內容|看更多)\s*[-:：|]*\s*', '', title)
    title = re.sub(r'\s*(?:立即購票|活動詳情|詳細內容|看更多|Read More)$', '', title, flags=re.I)
    title = title.strip(' ｜-|›»')
    if title in NOISE or len(title) < 3 or title.isdigit():
        return None
    return title


def _walk(obj):
    if isinstance(obj, list):
        for child in obj:
            yield from _walk(child)
    elif isinstance(obj, dict):
        kind = obj.get('@type', '')
        if (isinstance(kind, str) and kind.lower() == 'event') or (isinstance(kind, list) and any(str(x).lower() == 'event' for x in kind)):
            yield obj
        for key in ('@graph', 'mainEntity', 'itemListElement'):
            if key in obj:
                yield from _walk(obj[key])


def _loc(value):
    if isinstance(value, list):
        return next((v for x in value if (v := _loc(x))), None)
    if isinstance(value, dict):
        address = value.get('address', {})
        if isinstance(address, dict):
            address = ' '.join(str(address.get(k, '')) for k in ('addressLocality', 'streetAddress')).strip()
        return clean_text(value.get('name') or address, 200)
    return clean_text(value, 200)


def _price(value):
    if isinstance(value, list):
        return next((v for x in value if (v := _price(x))), None)
    if not isinstance(value, dict):
        return None
    currency = str(value.get('priceCurrency') or 'TWD').upper()
    if currency not in ('TWD', 'NTD'):
        return None
    low = value.get('lowPrice', value.get('price'))
    high = value.get('highPrice')
    if low is None:
        return None
    try:
        a = float(low)
        b = float(high) if high is not None else a
        if not 0 <= a <= b <= 10000000:
            return None
        label = '免費' if a == b == 0 else 'NT$ ' + f'{a:g}' + (f'–{b:g}' if b != a else '')
        return label
    except (ValueError, TypeError):
        return None


def _date(value):
    if isinstance(value, dict):
        value = value.get('@value')
    if not isinstance(value, str):
        return None
    match = DATE_RE.search(value)
    if not match:
        return None
    raw = match.group().replace('年', '-').replace('月', '-').replace('日', '').replace('/', '-').replace('.', '-')
    pieces = raw.split('-')
    try:
        d = datetime(int(pieces[0]), int(pieces[1]), int(pieces[2]))
        return d.strftime('%Y-%m-%d')
    except (ValueError, IndexError):
        return None


def _meta(soup, *keys):
    for key in keys:
        el = soup.find('meta', attrs={'property': key}) or soup.find('meta', attrs={'name': key})
        if el and el.get('content'):
            value = clean_text(el.get('content'))
            if value:
                return value
    return None


# [SRC-P1] Date and ticket scope classification; never certifies availability.
def classify_source_page(soup, expected_url=None):
    """Conservative role tag only. One program page is not one performance."""
    host = (urlparse(expected_url or '').hostname or '').lower()
    title = _meta(soup, 'og:title', 'twitter:title')
    if not title and soup.title:
        title = clean_text(soup.title.get_text(' ', strip=True), 300)
    title = title or ''
    if (host in ('www.opentix.life', 'opentix.life') and
            '專區' in title and
            any(x in title for x in ('身障', '身心障礙'))):
        return 'SPECIAL_ELIGIBILITY_COLLECTION'
    if host in ('kidsclub.com.tw', 'www.kidsclub.com.tw'):
        path = urlparse(expected_url or '').path.lower()
        if path.startswith('/courses/') or path.startswith('/product/'):
            return 'COURSE_OR_CATALOG_UNVERIFIED'
    return 'EVENT_DETAIL_UNVERIFIED'

# [SRC-P4] Scoped extraction: event time and identity are candidates, not availability.
def extract_source_time_roles(soup, events, expected_url, scope):
    """Read only SAME-PAGE JSON-LD nodes; refuse unbound/global expiry claims."""
    from urllib.parse import urlsplit
    from datetime import datetime
    def norm(url):
        try:
            p=urlsplit(url or '')
            if p.scheme != 'https' or p.username or p.password or not p.hostname or p.port not in (None,443):
                return None
            host=p.hostname.lower().removeprefix('www.')
            if host not in ('accupass.com','opentix.life'):
                return None
            return (host,p.path.rstrip('/'),p.query)
        except (ValueError,AttributeError,TypeError):
            return None
    def instant(value):
        if isinstance(value,dict):value=value.get('@value')
        if not isinstance(value,str) or 'T' not in value or len(value)>42:
            return None
        try:
            d=datetime.fromisoformat(value.replace('Z','+00:00'))
            if not 2020<=d.year<=2040:return None
            return {'value':d.isoformat(timespec='seconds'),
                    'timezone': 'EXPLICIT_OFFSET' if d.utcoffset() is not None else 'UNSPECIFIED'}
        except (ValueError,OverflowError,TypeError):return None
    expected=norm(expected_url)
    if not expected:return {}
    if expected[0]=='accupass.com':
        if not re.fullmatch(r'/event/[0-9]{22}',expected[1]):return {}
        if len(events)!=1:return {'source_time_role':'MULTIPLE_OR_NO_EVENT_NODES_HOLD'}
        e=events[0]
        evurl=e.get('url') or e.get('@id')
        # An explicit Event URL, when present, must match the original exact target.
        if evurl and norm(evurl)!=expected:
            return {'source_time_role':'JSONLD_EVENT_ID_MISMATCH_HOLD'}
        canonical=soup.find('link',rel=lambda v: bool(v and 'canonical' in (v if isinstance(v,list) else [v])))
        canonical_url=(canonical.get('href') if canonical else None)
        og=soup.find('meta',attrs={'property':'og:url'})
        og_url=(og.get('content') if og else None)
        observed=[v for v in (canonical_url,og_url) if v]
        if observed and any(norm(v)!=expected for v in observed):
            return {'source_time_role':'PAGE_IDENTITY_CONFLICT_HOLD'}
        e_title=clean_text(e.get('name'),240)
        ogtitle=_meta(soup,'og:title','twitter:title')
        # If title exists, require the same bounded activity label on the page.
        if e_title and ogtitle:
            clean=lambda x:re.sub(r'[\s｜|–—:：·\\]+','',x).lower()
            if clean(e_title) not in clean(ogtitle) and clean(ogtitle) not in clean(e_title):
                return {'source_time_role':'TITLE_CONFLICT_HOLD'}
        start,end=instant(e.get('startDate')),instant(e.get('endDate'))
        if not start:return {'source_time_role':'NO_EXPLICIT_EVENT_DATETIME'}
        result={'source_time_role':('EVENT_URL_BOUND_CANDIDATE' if evurl else
                                    'SINGLE_EVENT_PAGE_MATCH_CANDIDATE' if observed else
                                    'SINGLE_EVENT_UNBOUND_TIME_CANDIDATE'),
                'event_start_at_candidate':start['value'],
                'event_start_timezone':start['timezone']}
        if end:
            try:
                a=datetime.fromisoformat(start['value']);b=datetime.fromisoformat(end['value'])
                if (a.tzinfo is None)==(b.tzinfo is None) and b>=a:
                    result['event_end_at_candidate']=end['value']
                    result['event_end_timezone']=end['timezone']
                else:result['source_time_role']='TIME_RANGE_CONFLICT_HOLD'
            except TypeError:result['source_time_role']='TIME_RANGE_CONFLICT_HOLD'
        return result
    if expected[0]=='opentix.life' and scope=='SPECIAL_ELIGIBILITY_COLLECTION':
        if not re.fullmatch(r'/event/[0-9]{18,20}',expected[1]):return {}
        if len(events)>64:return {'source_time_role':'MULTI_PROGRAM_TOO_MANY_NODES_HOLD'}
        sessions=[]
        for node in events:
            start,end=instant(node.get('startDate')),instant(node.get('endDate'))
            if not start:continue
            sessions.append({'start':start['value'], 'end':end['value'] if end else None,
                             'time_zone_evidence':start['timezone']})
        # These may be different performances. Not authoritative collection end.
        return {'source_time_role':'MULTI_PROGRAM_SCHEDULE_CANDIDATES_ONLY',
                'event_session_candidates':sessions,
                'event_session_candidate_count':len(sessions)}
    return {}

def parse_detail(html, expected_url=None):
    """Returns only attributable fields from an event detail page.

    JSON-LD with multiple events is selected by matching page URL. Avoids unrelated
    dates (presale / discounts) in full-page body text.
    """
    soup = BeautifulSoup(html or '', 'html.parser')
    result = {}
    # [SRC-P1] Source role and ticket unknown are provenance, not expiry decisions.
    scope = classify_source_page(soup, expected_url)
    result['source_page_type'] = scope
    result['ticket_availability'] = 'UNKNOWN'
    pageurl = (expected_url or '').split('#')[0].rstrip('/')
    candidates = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            candidates.extend(_walk(json.loads(script.string or script.get_text())))
        except (ValueError, TypeError):
            continue
    # G5H provenance guard: an URL-less Event in a multi-Event graph is
    # ambiguous. Prefer an explicit matching URL; never take the first orphan.
    # Preserve the previous single-Event (URL-less) behavior for compatibility.
    exact_matches = [e for e in candidates
                     if pageurl and str(e.get('url') or '').split('#')[0].rstrip('/') == pageurl]
    if exact_matches:
        chosen = exact_matches[0]
    elif len(candidates) == 1 and not str(candidates[0].get('url') or '').strip():
        chosen = candidates[0]
    elif not pageurl and len(candidates) == 1:
        chosen = candidates[0]
    else:
        chosen = None
    # [SRC-P1] A URL-less JSON-LD Event is a candidate, not exact source identity.
    result['source_identity_status'] = (
        'EXACT_JSONLD_EVENT_URL' if exact_matches else
        'SINGLE_JSONLD_URLLESS_CANDIDATE' if chosen is not None and not chosen.get('url') else
        'UNBOUND_OR_MULTI_EVENT'
    )
    if scope == 'SPECIAL_ELIGIBILITY_COLLECTION':
        # Multi-program qualification listings are not a single dated performance.
        chosen = None
    for event in ([chosen] if chosen is not None else []):
        start, end = _date(event.get('startDate')), _date(event.get('endDate'))
        if start:
            result['date'] = start + (' ~ ' + end if end and end != start and end >= start else '')
        for key, val in [('location', _loc(event.get('location'))),
                         ('price', _price(event.get('offers'))),
                         ('description', clean_text(event.get('description'), 1200)),
                         ('title', clean_event_title(event.get('name'))),
                         ('img_url', _loc(event.get('image')) if isinstance(event.get('image'), str) else None)]:
            if val:
                result[key] = val
        break
    if 'description' not in result:
        description = _meta(soup, 'description', 'og:description', 'twitter:description')
        if description and len(description) > 25 and 'cookie' not in description.lower():
            result['description'] = description[:1200]
    if 'img_url' not in result:
        image = _meta(soup, 'og:image', 'twitter:image')
        if image:
            p = urlparse(urljoin(pageurl + '/', image))
            if p.scheme == 'https' and p.hostname:
                result['img_url'] = p.geturl()
    if 'date' not in result:
        for selector in ('[itemprop="startDate"]', 'time[datetime]', 'meta[property="event:start_time"]'):
            el = soup.select_one(selector)
            if el:
                date = _date(el.get('content') or el.get('datetime') or el.get_text(' ', strip=True))
                if date:
                    result['date'] = date
                    break
    # Restrict label fallback to small blocks, not page-wide date/presale content.
    for label, field in (('活動日期', 'date'), ('展覽日期', 'date'), ('展演日期', 'date'),
                         ('活動地點', 'location'), ('展覽地點', 'location'), ('演出地點', 'location'),
                         ('票價', 'price'), ('門票', 'price')):
        if field in result:
            continue
        for node in soup.find_all(['li', 'p', 'td', 'div'], limit=1000):
            text = clean_text(node.get_text(' ', strip=True), 240)
            if not text or len(text) > 190 or not text.startswith(label):
                continue
            value = re.sub(r'^' + re.escape(label) + r'\s*[:：]?\s*', '', text).strip()
            if field == 'date':
                dates = [_date(m.group()) for m in DATE_RE.finditer(value)]
                dates = [v for v in dates if v]
                if dates:
                    result[field] = dates[0] + (' ~ ' + dates[1] if len(dates) > 1 and dates[1] >= dates[0] else '')
            elif field == 'price':
                m = re.search(r'(?:NT\$|新臺幣|新台幣|票價)?\s*[\d,]+\s*(?:[-~–]\s*[\d,]+)?\s*元?', value)
                if '免費' in value:
                    result[field] = '免費'
                elif m and re.search(r'\d', m.group()):
                    result[field] = clean_text(m.group(), 80)
            else:
                loc = clean_text(value, 200)
                if loc:
                    result[field] = loc
            if field in result:
                break
    # [SRC-P4] Full ISO local time and cross-program nodes are provenance-only.
    # Never use these candidates to auto-expire or to assert ticket availability.
    result.update(extract_source_time_roles(soup, candidates, pageurl, scope))
    # [SRC-P1] Reject global first-date fallback on special-ticket collection pages.
    if scope == 'SPECIAL_ELIGIBILITY_COLLECTION':
        result.pop('date', None)
    return result
