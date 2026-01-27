# -*- coding: utf-8 -*-
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import json
import re
import time
import logging
import os
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin
from pathlib import Path
from bs4 import BeautifulSoup

# =========================
# 🛠️ 設定區
# =========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("scraper.log", encoding='utf-8', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("docs")
OUTPUT_FILE = OUTPUT_DIR / "data.json"
LINE_TOKEN = os.environ.get("LINE_TOKEN")

# 真實 Chrome Headers
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
]

# =========================
# 🧩 網路請求核心
# =========================
def get_headers(referer=None):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    if referer: headers['Referer'] = referer
    return headers

def fetch_text(url, referer=None, encoding=None, use_session=True):
    """
    use_session=False 用於 KKTIX 等會追蹤 Cookies 的網站
    """
    try:
        time.sleep(random.uniform(1, 2.5))
        headers = get_headers(referer)
        
        if use_session:
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[403, 429, 500, 502])
            session.mount("https://", HTTPAdapter(max_retries=retries))
            resp = session.get(url, headers=headers, timeout=30, verify=False)
        else:
            # 無痕模式
            resp = requests.get(url, headers=headers, timeout=30, verify=False)

        resp.raise_for_status()
        
        if encoding:
            resp.encoding = encoding
        elif 'charset' not in resp.headers.get('content-type', '').lower():
            resp.encoding = resp.apparent_encoding
            
        return resp.text
    except Exception as e:
        logger.error(f"💥 請求失敗: {url} - {e}")
        return None

# =========================
# 🧠 資料清洗與網址修復
# =========================
def fix_utk_url(domain, raw_url):
    """修復 UTK 系列無效連結"""
    match = re.search(r'PRODUCT_ID=([A-Za-z0-9]+)', raw_url, re.I)
    if match:
        pid = match.group(1)
        if "tixfun" in domain:
            return f"https://{domain}/UTK0201_?PRODUCT_ID={pid}"
        else:
            return f"https://{domain}/application/UTK02/UTK0201_.aspx?PRODUCT_ID={pid}"
    return raw_url

def safe_get_text(element):
    if element: return element.get_text(strip=True)
    return ""

def create_event_obj(title, url, platform, img_url=None, type_override=None):
    if not title: return None

    noise_keywords = [
        '立即購票', '詳細內容', 'Read More', '活動詳情', '查看更多', '已結束', '報名', '詳細資訊', '購票', 
        'More', 'None', '活動介紹', 'Traffic', '更多詳情', '其他活動', '開放時間', '交通資訊', 
        '當前頁面', 'Current Page', 'Go to page', '看更多', '查看全部', 'FamiTicket全網購票網', '首頁',
        '找活動', '下一頁', '廣告版位出租', '隱私權政策', '較舊的文章', '詳細介紹', '回首頁', '網站導覽',
        '兩側門廳', '中央通廊', '服務台', '堂景介紹', '租借', '全票', '優待票', '建立活動', 'Facebook'
    ]
    
    if title.strip() in noise_keywords: return None

    title = re.sub(r'^(event-)?banner-', '', title, flags=re.I)
    for n in noise_keywords: title = title.replace(n, "")
    title = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', '', title)
    title = re.sub(r'^[»\s]+|[»\s]+$', '', title).strip()

    if re.match(r'^\d+$', title) or len(title) < 2: return None

    tw_tz = timezone(timedelta(hours=8))
    scraped_time = datetime.now(tw_tz).isoformat()
    event_type = type_override if type_override else get_event_category_from_title(title)

    return {
        'title': title, 'url': url, 'platform': platform, 'img_url': img_url,
        'date': "詳內文", 'type': event_type, 'scraped_at': scraped_time
    }

def get_event_category_from_title(title):
    if not title: return "其他"
    title_lower = title.lower()
    category_mapping = {
        "音樂會/演唱會": ["音樂會", "演唱會", "獨奏會", "合唱", "交響", "管樂", "國樂", "弦樂", "鋼琴", "提琴", "巡演", "fan concert", "fancon", "音樂節", "爵士", "演奏", "歌手", "樂團", "tour", "live", "concert", "solo", "recital", "電音派對", "藝人見面會", "音樂祭", "Voice", "聲優"],
        "音樂劇/歌劇": ["音樂劇", "歌劇", "musical", "opera"],
        "戲劇表演": ["戲劇", "舞台劇", "劇團", "劇場", "喜劇", "公演", "掌中戲", "歌仔戲", "豫劇", "話劇", "相聲", "布袋戲", "京劇", "崑劇", "藝文活動"],
        "舞蹈表演": ["舞蹈", "舞作", "舞團", "芭蕾", "舞劇", "現代舞", "民族舞", "踢踏舞", "zumba"],
        "展覽/博覽": ["展覽", "特展", "博物館", "美術館", "藝術展", "畫展", "攝影展", "文物展", "科學展", "博覽會", "動漫", "展出", "聯展", "個展"],
        "親子活動": ["親子", "兒童", "寶寶", "家庭", "小朋友", "童話", "卡通", "動畫", "體驗", "營隊", "冬令營", "夏令營"],
        "電影放映": ["電影", "影展", "數位修復", "放映", "首映", "紀錄片", "動畫電影"],
        "體育賽事": ["棒球", "籃球", "錦標賽", "運動會", "足球", "羽球", "網球", "馬拉松", "路跑", "游泳", "體操", "championship", "遊戲競賽"],
        "講座/工作坊": ["工作坊", "課程", "導讀", "沙龍", "講座", "體驗", "研習", "培訓", "論壇", "研討會", "座談", "workshop", "職場工作術", "資訊科技", "AI", "Python", "競賽", "創作", "纏繞"],
        "娛樂表演": ["脫口秀", "魔術", "雜技", "馬戲", "特技", "魔幻", "綜藝", "娛樂", "秀場", "表演秀", "社群活動", "派對", "市集"],
        "其他": ["旅遊", "美食", "公益"]
    }
    for category, keywords in category_mapping.items():
        if any(keyword in title_lower for keyword in keywords): return category
    return "其他"

# =========================
# 🕷️ 平台爬蟲 (V56)
# =========================

def fetch_kktix():
    logger.info("🚀 啟動 KKTIX (V56 No-Session)...")
    urls = [f"https://kktix.com/events?category_id={i}" for i in [2,6,4,3,8]] + ["https://kktix.com/"]
    events = []
    seen = set()
    for url in urls:
        # [V56] 關閉 Session，避免 403
        html = fetch_text(url, use_session=False)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="/events/"], .event-item a, .event-card a')
        for link in links:
            href = link.get('href')
            if not href: continue
            full_url = urljoin("https://kktix.com", href).split('?')[0]
            if full_url in seen: continue
            title = link.get('title') or safe_get_text(link.find(class_='name')) or safe_get_text(link)
            img = link.find('img')
            ev = create_event_obj(title, full_url, "KKTIX", img.get('src') if img else None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[KKTIX] 抓取 {len(events)} 筆")
    return events

def fetch_accupass():
    logger.info("🚀 啟動 ACCUPASS...")
    urls = [f"https://www.accupass.com/search?q={k}" for k in ["音樂", "藝文", "學習", "科技", "展覽"]] + ["https://www.accupass.com/?area=north"]
    events = []
    seen = set()
    for url in urls:
        html = fetch_text(url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        candidates = soup.find_all('a', href=re.compile(r'^/event/([A-Za-z0-9]+)'))
        for link in candidates:
            href = link.get('href')
            full_url = urljoin("https://www.accupass.com", href).split('?')[0]
            if full_url in seen: continue
            title = safe_get_text(link.find('h3')) or safe_get_text(link)
            img = link.find('img')
            ev = create_event_obj(title, full_url, "ACCUPASS", img.get('src') if img else None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[ACCUPASS] 抓取 {len(events)} 筆")
    return events

def fetch_tixcraft():
    logger.info("🚀 啟動 拓元...")
    urls = ["https://tixcraft.com/activity", "https://tixcraft.com/activity/list/select_type/all"]
    events = []
    seen = set()
    for url in urls:
        html = fetch_text(url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="/activity/detail/"]')
        for link in links:
            full_url = urljoin("https://tixcraft.com", link.get('href'))
            if full_url in seen: continue
            title = link.get('title') or safe_get_text(link)
            ev = create_event_obj(title, full_url, "拓元售票", None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[拓元] 抓取 {len(events)} 筆")
    return events

def fetch_kham():
    logger.info("🚀 啟動 寬宏 (V56 URL Fix)...")
    urls = [f"https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY={i}" for i in [205,231,116,129]]
    events = []
    seen = set()
    for url in urls:
        html = fetch_text(url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="UTK0201_"]') 
        for link in links:
            raw_url = urljoin("https://kham.com.tw", link.get('href'))
            # [V56] 網址修復
            full_url = fix_utk_url("kham.com.tw", raw_url)
            if full_url in seen: continue
            if "PRODUCT_ID" not in full_url: continue
            title = safe_get_text(link)
            ev = create_event_obj(title, full_url, "寬宏", None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[寬宏] 抓取 {len(events)} 筆")
    return events

def fetch_opentix():
    logger.info("🚀 啟動 OPENTIX...")
    html = fetch_text("https://www.opentix.life/event")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.opentix.life", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "OPENTIX", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[OPENTIX] 抓取 {len(events)} 筆")
    return events

def fetch_udn():
    logger.info("🚀 啟動 UDN (V56 URL Fix)...")
    categories = [231, 205, 77, 116, 100, 129, 218, 163, 101]
    urls = [f"https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category={c}&kdid=cateList" for c in categories]
    events = []
    seen = set()
    for url in urls:
        html = fetch_text(url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="UTK0201_"]')
        for link in links:
            raw_url = urljoin("https://tickets.udnfunlife.com", link.get('href'))
            # [V56] 網址修復
            full_url = fix_utk_url("tickets.udnfunlife.com", raw_url)
            if full_url in seen: continue
            if "PRODUCT_ID" not in full_url: continue
            title = safe_get_text(link).split("NT$")[0].strip()
            ev = create_event_obj(title, full_url, "UDN售票網", None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[UDN] 抓取 {len(events)} 筆")
    return events

def fetch_fami():
    logger.info("🚀 啟動 FamiTicket (V56 Filter)...")
    html = fetch_text("https://www.famiticket.com.tw/Home")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    # V34 Logic: links = soup.select("a[href*='Content/Home/Activity']")
    # 搭配 filter
    links = soup.find_all('a', href=re.compile(r'Activity', re.I))
    events = []
    seen = set()
    for link in links:
        href = link.get('href')
        full_url = urljoin("https://www.famiticket.com.tw", link.get('href'))
        if full_url in seen: continue
        # [V56] 排除 Search 列表頁
        if "Search" in full_url or "Info" not in full_url: continue
        
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "FamiTicket", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[FamiTicket] 抓取 {len(events)} 筆")
    return events

def fetch_era():
    logger.info("🚀 啟動 年代 (V56 Big5)...")
    # [V56] 指定 Big5 編碼
    html = fetch_text("https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77", encoding='big5')
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="UTK0201_"]')
    events = []
    seen = set()
    for link in links:
        raw_url = urljoin("https://ticket.com.tw", link.get('href'))
        full_url = fix_utk_url("ticket.com.tw", raw_url)
        if full_url in seen: continue
        if "PRODUCT_ID" not in full_url: continue
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "年代售票", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[年代] 抓取 {len(events)} 筆")
    return events

def fetch_tixfun():
    logger.info("🚀 啟動 TixFun...")
    html = fetch_text("https://tixfun.com/UTK0101_?TYPE=1&CATEGORY=77")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="UTK0201_"]')
    events = []
    seen = set()
    for link in links:
        raw_url = urljoin("https://tixfun.com", link.get('href'))
        full_url = fix_utk_url("tixfun.com", raw_url)
        if full_url in seen: continue
        if "PRODUCT_ID" not in full_url: continue
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "TixFun售票網", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[TixFun] 抓取 {len(events)} 筆")
    return events

def fetch_eventgo():
    logger.info("🚀 啟動 Event Go...")
    html = fetch_text("https://eventgo.bnextmedia.com.tw/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/detail"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://eventgo.bnextmedia.com.tw", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "Event Go", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[Event Go] 抓取 {len(events)} 筆")
    return events

def fetch_beclass():
    logger.info("🚀 啟動 BeClass...")
    html = fetch_text("https://www.beclass.com/default.php?name=ShowList&op=recent")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='rid=']")
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.beclass.com", link.get('href'))
        if full_url in seen: continue
        title = link.get_text(strip=True)
        ev = create_event_obj(title, full_url, "BeClass", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[BeClass] 抓取 {len(events)} 筆")
    return events

def fetch_indievox():
    logger.info("🚀 啟動 iNDIEVOX...")
    html = fetch_text("https://www.indievox.com/activity/list")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/activity/detail"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.indievox.com", link.get('href'))
        if full_url in seen: continue
        title = link.get('title') or safe_get_text(link.find('h5'))
        img = link.find('img')
        ev = create_event_obj(title, full_url, "iNDIEVOX", img.get('src') if img else None, type_override="音樂會/演唱會")
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[iNDIEVOX] 抓取 {len(events)} 筆")
    return events

def fetch_ibon():
    logger.info("🚀 啟動 ibon...")
    html = fetch_text("https://ticket.ibon.com.tw/Activity/Index", use_session=False)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    all_links = soup.find_all('a', href=True)
    events = []
    seen = set()
    for link in all_links:
        href = link.get('href')
        if "activity" not in href.lower(): continue
        full_url = urljoin("https://ticket.ibon.com.tw", href)
        if full_url in seen: continue
        title = safe_get_text(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "ibon", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[ibon] 抓取 {len(events)} 筆")
    return events

def fetch_huashan():
    logger.info("🚀 啟動 華山...")
    html = fetch_text("https://www.huashan1914.com/w/huashan1914/exhibition")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='exhibition_']")
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.huashan1914.com", link.get('href'))
        if full_url in seen: continue
        title = link.get_text(strip=True) or link.get('title')
        ev = create_event_obj(title, full_url, "華山1914", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[華山] 抓取 {len(events)} 筆")
    return events

def fetch_songshan():
    logger.info("🚀 啟動 松山...")
    html = fetch_text("https://www.songshanculturalpark.org/exhibition")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all('a', href=re.compile(r'/exhibition/'))
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.songshanculturalpark.org", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "松山文創", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[松山] 抓取 {len(events)} 筆")
    return events

def fetch_stroll():
    logger.info("🚀 啟動 StrollTimes...")
    html = fetch_text("https://strolltimes.com/", referer="https://www.google.com/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('h3.post-title a')
    events = []
    seen = set()
    for link in links:
        full_url = link.get('href')
        if not full_url or full_url in seen: continue
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "StrollTimes", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[StrollTimes] 抓取 {len(events)} 筆")
    return events

def fetch_kidsclub():
    logger.info("🚀 啟動 KidsClub (V56 Filter)...")
    html = fetch_text("https://www.kidsclub.com.tw/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='/product/'], a[href*='/courses/']")
    events = []
    seen = set()
    for link in links:
        href = link.get('href')
        # [V56] 排除 category
        if not href or "product-category" in href or "tag" in href: continue
        
        full_url = urljoin("https://www.kidsclub.com.tw", href)
        if full_url in seen: continue
        title = link.get('title') or safe_get_text(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "KidsClub", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[KidsClub] 抓取 {len(events)} 筆")
    return events

def fetch_wtc():
    logger.info("🚀 啟動 台北世貿...")
    url = "https://www.twtc.com.tw/exhibition?p=home"
    html = fetch_text(url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://www.twtc.com.tw/"
    events = []
    seen = set()
    rows = soup.select("tr")
    for row in rows:
        link = row.select_one("a[href*='detail'], a[href*='id=']")
        if not link: continue
        href = link['href']
        raw_title = link.get_text(strip=True) # V55 改回 link.get_text
        if not raw_title or len(raw_title) < 5: continue
        
        full_url = urljoin(base_url, href)
        if full_url in seen: continue
        ev = create_event_obj(raw_title, full_url, "台北世貿", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[台北世貿] 抓取 {len(events)} 筆")
    return events

def fetch_cksmh():
    logger.info("🚀 啟動 中正紀念堂...")
    html = fetch_text("https://www.cksmh.gov.tw/activitybee_list.aspx?n=105")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="activitybee_"]')
    events = []
    seen = set()
    for link in links:
        href = link.get('href')
        if not href: continue
        full_url = urljoin("https://www.cksmh.gov.tw", href)
        if full_url in seen: continue
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "中正紀念堂", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[中正紀念堂] 抓取 {len(events)} 筆")
    return events

# =========================
# 💾 存檔與執行 (覆蓋模式)
# =========================
def send_line_notify(message):
    if not LINE_TOKEN: return
    try:
        requests.post(
            "https://notify-api.line.me/api/notify",
            headers={"Authorization": f"Bearer {LINE_TOKEN}"},
            data={"message": message},
            timeout=10
        )
    except: pass

def save_data_and_notify(new_events):
    # 直接覆蓋
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_events, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📊 資料庫重置完畢 | 本次總筆數: {len(new_events)}")

    if new_events and LINE_TOKEN:
        msg = f"\n🔥 發現 {len(new_events)} 個新活動！\n"
        for e in new_events[:5]:
            msg += f"\n📌 {e['title'][:30]}\n🔗 {e['url']}\n"
        if len(new_events) > 5:
            msg += f"\n...還有 {len(new_events)-5} 筆，請上網頁查看！"
        send_line_notify(msg)

def main():
    logger.info("🔥 爬蟲程式開始執行 (V56 Final Integration)...")
    all_new_events = []
    try:
        all_new_events.extend(fetch_kktix())
        all_new_events.extend(fetch_accupass())
        all_new_events.extend(fetch_tixcraft())
        all_new_events.extend(fetch_kham())
        all_new_events.extend(fetch_opentix())
        all_new_events.extend(fetch_udn())
        all_new_events.extend(fetch_fami())
        all_new_events.extend(fetch_era())
        all_new_events.extend(fetch_tixfun())
        all_new_events.extend(fetch_eventgo())
        all_new_events.extend(fetch_beclass())
        all_new_events.extend(fetch_indievox())
        all_new_events.extend(fetch_ibon())
        all_new_events.extend(fetch_huashan())
        all_new_events.extend(fetch_songshan())
        all_new_events.extend(fetch_stroll())
        all_new_events.extend(fetch_kidsclub())
        all_new_events.extend(fetch_wtc())
        all_new_events.extend(fetch_cksmh())
    except Exception as e:
        logger.error(f"❌ 主程式執行錯誤: {e}")

    logger.info(f"🔍 本輪爬取匯總: 共抓取到 {len(all_new_events)} 筆有效資料")
    save_data_and_notify(all_new_events)

if __name__ == "__main__":
    main()
