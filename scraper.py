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

# [V52] 恢復 V50 的 User-Agent 策略
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
]

# =========================
# 🧩 網路請求核心 (V52: 回歸 Session)
# =========================
def create_session():
    """建立共用 Session，解決 KKTIX 403 問題"""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[403, 429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    
    session.headers.update({
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    })
    return session

def fetch_text(session, url, referer=None):
    try:
        if referer:
            session.headers.update({'Referer': referer})
        
        # 隨機延遲
        time.sleep(random.uniform(0.5, 1.5))
        
        resp = session.get(url, timeout=30, verify=False)
        resp.raise_for_status()
        
        if 'charset' not in resp.headers.get('content-type', '').lower():
            resp.encoding = resp.apparent_encoding
            
        return resp.text
    except Exception as e:
        logger.error(f"💥 請求失敗: {url} - {e}")
        return None

# =========================
# 🧠 內容解析工具
# =========================
def extract_smart_title(link_tag):
    title = link_tag.get('title')
    if not title:
        header = link_tag.find(['h3', 'h4', 'h5', 'h6', 'span', 'div'], class_=re.compile(r'(title|name|subject|header|caption)', re.I))
        if header: title = header.get_text(strip=True)
    if not title:
        img = link_tag.find('img')
        if img: title = img.get('alt') or img.get('title')
    if not title:
        text = link_tag.get_text(" ", strip=True)
        if text: title = text
    return title

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

def create_event_obj(title, url, platform, img_url=None, type_override=None):
    if not title: return None

    noise_keywords = [
        '立即購票', '詳細內容', 'Read More', '活動詳情', '查看更多', '已結束', '報名', '詳細資訊', '購票', 
        'More', 'None', '活動介紹', 'Traffic', '更多詳情', '其他活動', '開放時間', '交通資訊', 
        '當前頁面', 'Current Page', 'Go to page', '看更多', '查看全部', 'FamiTicket全網購票網', '首頁',
        '找活動', '下一頁', '廣告版位出租', '隱私權政策', '較舊的文章', '詳細介紹', '回首頁', '網站導覽',
        '兩側門廳', '中央通廊', '服務台', '堂景介紹', '租借', '全票', '優待票'
    ]
    
    if title.strip() in noise_keywords: return None

    title = re.sub(r'^(event-)?banner-', '', title, flags=re.I)
    for n in noise_keywords: title = title.replace(n, "")
    title = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', '', title)
    title = re.sub(r'^[»\s]+|[»\s]+$', '', title).strip()

    if re.match(r'^\d+$', title) or len(title) < 3: return None

    tw_tz = timezone(timedelta(hours=8))
    scraped_time = datetime.now(tw_tz).isoformat()

    event_type = type_override if type_override else get_event_category_from_title(title)

    return {
        'title': title,
        'url': url,
        'platform': platform,
        'img_url': img_url,
        'date': "詳內文",
        'type': event_type,
        'scraped_at': scraped_time
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
# 🕷️ 平台爬蟲 (V52: KKTIX 恢復 Session, 其他平台廣域搜索)
# =========================

def fetch_kktix(session):
    logger.info("🚀 啟動 KKTIX (Session Restored)...")
    urls = [f"https://kktix.com/events?category_id={i}" for i in [2,6,4,3,8]] + ["https://kktix.com/"]
    events = []
    seen = set()
    for url in urls:
        html = fetch_text(session, url) # 使用 session
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="/events/"], .event-item a, .event-card a')
        for link in links:
            href = link.get('href')
            if not href: continue
            full_url = urljoin("https://kktix.com", href).split('?')[0]
            if full_url in seen: continue
            title = extract_smart_title(link)
            img = link.find('img')
            ev = create_event_obj(title, full_url, "KKTIX", img.get('src') if img else None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[KKTIX] 抓取 {len(events)} 筆")
    return events

def fetch_accupass(session):
    logger.info("🚀 啟動 ACCUPASS...")
    urls = [f"https://www.accupass.com/search?q={k}" for k in ["音樂", "藝文", "學習", "科技", "展覽"]] + ["https://www.accupass.com/?area=north"]
    events = []
    seen = set()
    for url in urls:
        html = fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        candidates = soup.find_all('a', href=re.compile(r'^/event/([A-Za-z0-9]+)'))
        for link in candidates:
            href = link.get('href')
            full_url = urljoin("https://www.accupass.com", href).split('?')[0]
            if full_url in seen: continue
            title = extract_smart_title(link)
            img = link.find('img')
            ev = create_event_obj(title, full_url, "ACCUPASS", img.get('src') if img else None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[ACCUPASS] 抓取 {len(events)} 筆")
    return events

def fetch_tixcraft(session):
    logger.info("🚀 啟動 拓元...")
    urls = ["https://tixcraft.com/activity", "https://tixcraft.com/activity/list/select_type/all"]
    events = []
    seen = set()
    for url in urls:
        html = fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="/activity/detail/"]')
        for link in links:
            full_url = urljoin("https://tixcraft.com", link.get('href'))
            if full_url in seen: continue
            title = extract_smart_title(link)
            ev = create_event_obj(title, full_url, "拓元售票", None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[拓元] 抓取 {len(events)} 筆")
    return events

def fetch_kham(session):
    logger.info("🚀 啟動 寬宏...")
    urls = [f"https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY={i}" for i in [205,231,116,129]]
    events = []
    seen = set()
    for url in urls:
        html = fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="UTK0201_"]') 
        for link in links:
            raw_url = urljoin("https://kham.com.tw", link.get('href'))
            full_url = fix_utk_url("kham.com.tw", raw_url)
            
            if full_url in seen: continue
            if "PRODUCT_ID" not in full_url: continue
            
            title = extract_smart_title(link)
            ev = create_event_obj(title, full_url, "寬宏", None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[寬宏] 抓取 {len(events)} 筆")
    return events

def fetch_opentix(session):
    logger.info("🚀 啟動 OPENTIX...")
    html = fetch_text(session, "https://www.opentix.life/event")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.opentix.life", link.get('href'))
        if full_url in seen: continue
        title = extract_smart_title(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "OPENTIX", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[OPENTIX] 抓取 {len(events)} 筆")
    return events

def fetch_udn(session):
    logger.info("🚀 啟動 UDN...")
    categories = [231, 205, 77, 116, 100, 129, 218, 163, 101]
    urls = [f"https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category={c}&kdid=cateList" for c in categories]
    events = []
    seen = set()
    for url in urls:
        html = fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="UTK0201_"]')
        for link in links:
            raw_url = urljoin("https://tickets.udnfunlife.com", link.get('href'))
            full_url = fix_utk_url("tickets.udnfunlife.com", raw_url)
            
            if full_url in seen: continue
            if "PRODUCT_ID" not in full_url: continue

            title_raw = extract_smart_title(link)
            title = title_raw.split("NT$")[0].strip() if title_raw else ""
            ev = create_event_obj(title, full_url, "UDN售票網", None)
            if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[UDN] 抓取 {len(events)} 筆")
    return events

def fetch_fami(session):
    logger.info("🚀 啟動 FamiTicket...")
    html = fetch_text(session, "https://www.famiticket.com.tw/Home/Activity/Search/242")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all('a', href=re.compile(r'Activity', re.I))
    events = []
    seen = set()
    for link in links:
        href = link.get('href')
        full_url = urljoin("https://www.famiticket.com.tw", link.get('href'))
        if full_url in seen: continue
        if "Info" not in full_url and "Search" not in full_url: continue
        title = extract_smart_title(link)
        ev = create_event_obj(title, full_url, "FamiTicket", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[FamiTicket] 抓取 {len(events)} 筆")
    return events

def fetch_era(session):
    logger.info("🚀 啟動 年代 (V52 Broad Search)...")
    html = fetch_text(session, "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    
    # [V52] 廣域搜索 UTK 相關連結 (解決 0 筆問題)
    links = soup.find_all('a', href=re.compile(r'UTK0201', re.I))
    
    events = []
    seen = set()
    for link in links:
        raw_url = urljoin("https://ticket.com.tw", link.get('href'))
        full_url = fix_utk_url("ticket.com.tw", raw_url)
        
        if full_url in seen: continue
        # 年代即使沒有 ID 也可以抓抓看，靠 title 過濾
        title = extract_smart_title(link)
        ev = create_event_obj(title, full_url, "年代售票", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[年代] 抓取 {len(events)} 筆")
    return events

def fetch_tixfun(session):
    logger.info("🚀 啟動 TixFun...")
    html = fetch_text(session, "https://tixfun.com/UTK0101_?TYPE=1&CATEGORY=77")
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
        title = extract_smart_title(link)
        ev = create_event_obj(title, full_url, "TixFun售票網", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[TixFun] 抓取 {len(events)} 筆")
    return events

def fetch_eventgo(session):
    logger.info("🚀 啟動 Event Go...")
    html = fetch_text(session, "https://eventgo.bnextmedia.com.tw/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/detail"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://eventgo.bnextmedia.com.tw", link.get('href'))
        if full_url in seen: continue
        title = extract_smart_title(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "Event Go", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[Event Go] 抓取 {len(events)} 筆")
    return events

def fetch_beclass(session):
    logger.info("🚀 啟動 BeClass...")
    html = fetch_text(session, "https://www.beclass.com/default.php?name=ShowList&op=recent")
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

def fetch_indievox(session):
    logger.info("🚀 啟動 iNDIEVOX...")
    html = fetch_text(session, "https://www.indievox.com/activity/list")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/activity/detail"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.indievox.com", link.get('href'))
        if full_url in seen: continue
        title = extract_smart_title(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "iNDIEVOX", img.get('src') if img else None, type_override="音樂會/演唱會")
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[iNDIEVOX] 抓取 {len(events)} 筆")
    return events

def fetch_ibon(session):
    logger.info("🚀 啟動 ibon (V52 Broad Search)...")
    html = fetch_text(session, "https://ticket.ibon.com.tw/Activity/Index")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    
    # [V52] 廣域搜索 href 包含 activity
    all_links = soup.find_all('a', href=re.compile(r'activity', re.I))
    
    events = []
    seen = set()
    for link in all_links:
        href = link.get('href')
        full_url = urljoin("https://ticket.ibon.com.tw", href)
        if full_url in seen: continue
        title = extract_smart_title(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "ibon", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[ibon] 抓取 {len(events)} 筆")
    return events

def fetch_huashan(session):
    logger.info("🚀 啟動 華山...")
    html = fetch_text(session, "https://www.huashan1914.com/w/huashan1914/exhibition")
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

def fetch_songshan(session):
    logger.info("🚀 啟動 松山...")
    html = fetch_text(session, "https://www.songshanculturalpark.org/exhibition")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all('a', href=re.compile(r'/exhibition/'))
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.songshanculturalpark.org", link.get('href'))
        if full_url in seen: continue
        title = extract_smart_title(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "松山文創", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[松山] 抓取 {len(events)} 筆")
    return events

def fetch_stroll(session):
    logger.info("🚀 啟動 StrollTimes (V51 Fix)...")
    # [V51] 維持成功版本：廣域搜索所有連結
    html = fetch_text(session, "https://strolltimes.com/", referer="https://www.google.com/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    all_links = soup.find_all('a', href=True)
    events = []
    seen = set()
    for link in all_links:
        href = link.get('href')
        if not href or len(href) < 15: continue
        if any(x in href for x in ['category', 'tag', 'contact', 'about', 'facebook']): continue
        
        full_url = href
        if full_url in seen: continue
        
        title = extract_smart_title(link)
        if not title or len(title) < 8: continue
        
        ev = create_event_obj(title, full_url, "StrollTimes", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[StrollTimes] 抓取 {len(events)} 筆")
    return events

def fetch_kidsclub(session):
    logger.info("🚀 啟動 KidsClub...")
    html = fetch_text(session, "https://www.kidsclub.com.tw/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    all_links = soup.find_all('a', href=True)
    events = []
    seen = set()
    for link in all_links:
        href = link.get('href')
        if "product-category" in href: continue
        if not re.search(r'(product|courses)', href): continue
        full_url = urljoin("https://www.kidsclub.com.tw", href)
        if full_url in seen: continue
        title = extract_smart_title(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "KidsClub", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[KidsClub] 抓取 {len(events)} 筆")
    return events

def fetch_wtc(session):
    logger.info("🚀 啟動 台北世貿...")
    url = "https://www.twtc.com.tw/exhibition?p=home"
    html = fetch_text(session, url)
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
        raw_title = link.get_text(strip=True)
        if not raw_title or raw_title.lower() in ['more', 'top', '詳細內容']:
            candidates = []
            for td in row.find_all('td'):
                txt = td.get_text(strip=True)
                if len(txt) > 4 and not re.match(r'^[\d/\-\.:\s]+$', txt):
                    candidates.append(txt)
            if candidates:
                raw_title = max(candidates, key=len)
        if not raw_title: continue
        full_url = urljoin(base_url, href)
        if full_url in seen: continue
        ev = create_event_obj(raw_title, full_url, "台北世貿", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[台北世貿] 抓取 {len(events)} 筆")
    return events

def fetch_cksmh(session):
    logger.info("🚀 啟動 中正紀念堂 (V52 Broad Search)...")
    html = fetch_text(session, "https://www.cksmh.gov.tw/activitybee_list.aspx?n=105")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    
    # [V52] 廣域搜索 activitybee
    links = soup.find_all('a', href=re.compile(r'activitybee', re.I))
    
    events = []
    seen = set()
    for link in links:
        href = link.get('href')
        if not href: continue
        full_url = urljoin("https://www.cksmh.gov.tw", href)
        if full_url in seen: continue
        title = extract_smart_title(link)
        ev = create_event_obj(title, full_url, "中正紀念堂", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[中正紀念堂] 抓取 {len(events)} 筆")
    return events

# =========================
# 💾 存檔與執行
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
    existing_file = OUTPUT_FILE
    existing_events = []
    if existing_file.exists():
        try:
            with open(existing_file, 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
        except: pass

    existing_map = {e['url']: e for e in existing_events}
    added_events = []
    updated_count = 0
    
    for event in new_events:
        url = event['url']
        if url not in existing_map:
            existing_map[url] = event
            added_events.append(event)
        else:
            existing_map[url].update(event)
            updated_count += 1
    
    final_list = list(existing_map.values())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding
