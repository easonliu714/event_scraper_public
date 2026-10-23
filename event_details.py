"""Conservative event-detail extraction. Unknown fields remain unset, never guessed.

Uses JSON-LD Event first, then event-specific DOM metadata/labels.
All parsing is deterministic and can be tested without network access.
"""
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
    value = re.sub(r'\s+', ' ', BeautifulSoup(value, 'html.parser').get_text(' ', strip=True)).strip()
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


def parse_detail(html, expected_url=None):
    """Returns only attributable fields from an event detail page.

    JSON-LD with multiple events is selected by matching page URL. Avoids unrelated
    dates (presale / discounts) in full-page body text.
    """
    soup = BeautifulSoup(html or '', 'html.parser')
    result = {}
    pageurl = (expected_url or '').split('#')[0].rstrip('/')
    candidates = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            candidates.extend(_walk(json.loads(script.string or script.get_text())))
        except (ValueError, TypeError):
            continue
    for event in candidates:
        target = str(event.get('url') or '').split('#')[0].rstrip('/')
        if target and pageurl and target != pageurl:
            continue
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
    return result
