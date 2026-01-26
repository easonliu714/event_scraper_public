# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import random
import json
import re
import time
import logging
import os
from datetime import datetime
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

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
]

# =========================
# 🧩 輔助工具
# =========================
def get_headers(referer=None):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    if referer: headers['Referer'] = referer
    return headers

def safe_get_text(element):
    if element and hasattr(element, 'get_text'):
        return element.get_text(strip=True)
    return ""

def get_event_category_from_title(title):
    if not title: return "其他"
    title_lower = title.lower()
    category_mapping = {
        "音樂會/演唱會": ["音樂會", "演唱會", "獨奏會", "合唱", "交響", "管樂", "國樂", "弦樂", "鋼琴", "提琴", "巡演", "fan concert", "fancon", "音樂節", "爵士", "演奏", "歌手", "樂團", "tour", "live", "concert", "solo", "recital", "電音派對", "藝人見面會", "音樂祭"],
        "音樂劇/歌劇": ["音樂劇", "歌劇", "musical", "opera"],
        "戲劇表演": ["戲劇", "舞台劇", "劇團", "劇場", "喜劇", "公演", "掌中戲", "歌仔戲", "豫劇", "話劇", "相聲", "布袋戲", "京劇", "崑劇", "藝文活動"],
        "舞蹈表演": ["舞蹈", "舞作", "舞團", "芭蕾", "舞劇", "現代舞", "民族舞", "踢踏舞", "zumba"],
        "展覽/博覽": ["展覽", "特展", "博物館", "美術館", "藝術展", "畫展", "攝影展", "文物展", "科學展", "博覽會", "動漫", "展出"],
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

async def fetch_text(session, url, headers=None, timeout_sec=20):
    if not headers: headers = get_headers()
    try:
        async with session.get(url, headers=headers, ssl=False, timeout=timeout_sec) as resp:
            if resp.status != 200:
                logger.warning(f"❌ HTTP {resp.status} - {url}")
                return None
            # 自動偵測編碼
            content_type = resp.headers.get('Content-Type', '').lower()
            if 'charset' in content_type:
                return await resp.text()
            else:
                data = await resp.read()
                try: return data.decode('utf-8')
                except: 
                    try: return data.decode('big5')
                    except: return data.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"💥 請求異常: {url} - {e}")
        return None

# 通用活動物件產生器
def create_event_obj(title, url, platform, img_url=None):
    # 標題清理
    if title:
        noise = ['立即購票', '詳細內容', 'Read More', '活動詳情', '查看更多', '已結束', '報名', '詳細資訊', '購票', 'More']
        for n in noise: title = title.replace(n, "")
        title = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
    
    if not title or len(title) < 2 or title in ['詳內文', '更多資訊']: return None

    return {
        'title': title,
        'url': url,
        'platform': platform,
        'img_url': img_url,
        'date': "詳內文",
        'type': get_event_category_from_title(title),
        'scraped_at': datetime.now().isoformat()
    }

# =========================
# 🕷️ 獨立平台爬蟲 (V34 邏輯移植)
# =========================

async def fetch_kktix(session):
    logger.info("🚀 啟動 KKTIX...")
    base = "https://kktix.com/events"
    urls = [f"{base}?category_id={i}" for i in [2,6,4,3,8]] + ["https://kktix.com/"]
    events = []
    seen = set()
    
    for url in urls:
        await asyncio.sleep(1)
        html = await fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        
        # V34: select multiple selectors
        links = soup.select('a[href*="/events/"], .event-item a, .event-card a')
        for link in links:
            href = link.get('href')
            if not href: continue
            full_url = urljoin("https://kktix.com", href).split('?')[0]
            if full_url in seen: continue
            
            title = link.get('title') or safe_get_text(link.find(class_='name')) or safe_get_text(link)
            img = link.find('img')
            
            ev = create_event_obj(title, full_url, "KKTIX", img.get('src') if img else None)
            if ev: 
                events.append(ev)
                seen.add(full_url)
    logger.info(f"[KKTIX] 抓取 {len(events)} 筆")
    return events

async def fetch_accupass(session):
    logger.info("🚀 啟動 ACCUPASS...")
    urls = [f"https://www.accupass.com/search?q={k}" for k in ["音樂", "藝文", "學習", "科技", "展覽"]] + ["https://www.accupass.com/?area=north"]
    events = []
    seen = set()
    
    for url in urls:
        await asyncio.sleep(2)
        html = await fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        # V34: Regex find_all
        candidates = soup.find_all('a', href=re.compile(r'^/event/([A-Za-z0-9]+)'))
        
        for link in candidates:
            href = link.get('href')
            full_url = urljoin("https://www.accupass.com", href).split('?')[0]
            if full_url in seen: continue
            
            title = safe_get_text(link.find('h3')) or safe_get_text(link.find(class_=re.compile('title', re.I))) or safe_get_text(link)
            img = link.find('img')
            
            ev = create_event_obj(title, full_url, "ACCUPASS", img.get('src') if img else None)
            if ev:
                events.append(ev)
                seen.add(full_url)
    logger.info(f"[ACCUPASS] 抓取 {len(events)} 筆")
    return events

async def fetch_tixcraft(session):
    logger.info("🚀 啟動 拓元...")
    urls = ["https://tixcraft.com/activity", "https://tixcraft.com/activity/list/select_type/all"]
    events = []
    seen = set()
    
    for url in urls:
        await asyncio.sleep(1)
        html = await fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="/activity/detail/"]')
        
        for link in links:
            full_url = urljoin("https://tixcraft.com", link.get('href'))
            if full_url in seen: continue
            
            title = link.get('title')
            if not title:
                img = link.find('img')
                if img: title = img.get('alt')
            if not title: title = safe_get_text(link)
            
            ev = create_event_obj(title, full_url, "拓元售票", None) # 拓元列表圖不好抓，先略過
            if ev:
                events.append(ev)
                seen.add(full_url)
    logger.info(f"[拓元] 抓取 {len(events)} 筆")
    return events

async def fetch_kham(session):
    logger.info("🚀 啟動 寬宏...")
    # V34: Explicit categories
    urls = [f"https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY={i}" for i in [205,231,116,129]]
    events = []
    seen = set()
    
    for url in urls:
        await asyncio.sleep(1)
        html = await fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        # V34: UTK0201 selector
        links = soup.select('a[href*="UTK0201"]')
        
        for link in links:
            full_url = urljoin("https://kham.com.tw", link.get('href'))
            if full_url in seen: continue
            
            title = safe_get_text(link)
            ev = create_event_obj(title, full_url, "寬宏", None)
            if ev:
                events.append(ev)
                seen.add(full_url)
    logger.info(f"[寬宏] 抓取 {len(events)} 筆")
    return events

async def fetch_opentix(session):
    logger.info("🚀 啟動 OPENTIX...")
    html = await fetch_text(session, "https://www.opentix.life/event")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/"]')
    events = []
    seen = set()
    
    for link in links:
        full_url = urljoin("https://www.opentix.life", link.get('href'))
        if full_url in seen: continue
        
        title = safe_get_text(link.find(class_=re.compile('title', re.I))) or safe_get_text(link)
        img = link.find('img')
        
        ev = create_event_obj(title, full_url, "OPENTIX", img.get('src') if img else None)
        if ev:
            events.append(ev)
            seen.add(full_url)
    logger.info(f"[OPENTIX] 抓取 {len(events)} 筆")
    return events

async def fetch_udn(session):
    logger.info("🚀 啟動 UDN...")
    urls = ["https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=77&kdid=cateList","https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=231&kdid=cateList"]
    events = []
    seen = set()
    
    for url in urls:
        await asyncio.sleep(1)
        html = await fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="UTK0201"]')
        
        for link in links:
            full_url = urljoin("https://tickets.udnfunlife.com", link.get('href'))
            if full_url in seen: continue
            
            # V34 Logic: Clean 'NT$'
            title = safe_get_text(link).split("NT$")[0].strip()
            ev = create_event_obj(title, full_url, "UDN售票網", None)
            if ev:
                events.append(ev)
                seen.add(full_url)
    logger.info(f"[UDN] 抓取 {len(events)} 筆")
    return events

async def fetch_fami(session):
    logger.info("🚀 啟動 FamiTicket...")
    html = await fetch_text(session, "https://www.famiticket.com.tw/Home")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    # V34: Specific selector
    links = soup.select("a[href*='Content/Home/Activity']")
    events = []
    seen = set()
    
    for link in links:
        full_url = urljoin("https://www.famiticket.com.tw", link.get('href'))
        if full_url in seen: continue
        
        title = link.get('title')
        if not title:
            img = link.find('img')
            if img: title = img.get('alt')
        if not title:
            # 嘗試找 card-text
            desc = link.find(class_='card-text') or link.find(class_='caption')
            if desc: title = safe_get_text(desc)
        
        ev = create_event_obj(title, full_url, "FamiTicket", None)
        if ev:
            events.append(ev)
            seen.add(full_url)
    logger.info(f"[FamiTicket] 抓取 {len(events)} 筆")
    return events

async def fetch_era(session):
    logger.info("🚀 啟動 年代...")
    # V34: Category 77
    html = await fetch_text(session, "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="UTK0201"]')
    events = []
    seen = set()
    
    for link in links:
        full_url = urljoin("https://ticket.com.tw", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "年代售票", None)
        if ev:
            events.append(ev)
            seen.add(full_url)
    logger.info(f"[年代] 抓取 {len(events)} 筆")
    return events

async def fetch_tixfun(session):
    logger.info("🚀 啟動 TixFun...")
    html = await fetch_text(session, "https://tixfun.com/UTK0101_?TYPE=1&CATEGORY=77")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="UTK0201"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://tixfun.com", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "TixFun售票網", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[TixFun] 抓取 {len(events)} 筆")
    return events

async def fetch_eventgo(session):
    logger.info("🚀 啟動 Event Go...")
    html = await fetch_text(session, "https://eventgo.bnextmedia.com.tw/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/detail"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://eventgo.bnextmedia.com.tw", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link.find('h3')) or safe_get_text(link.find(class_='title'))
        img = link.find('img')
        ev = create_event_obj(title, full_url, "Event Go", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[Event Go] 抓取 {len(events)} 筆")
    return events

async def fetch_beclass(session):
    logger.info("🚀 啟動 BeClass...")
    html = await fetch_text(session, "https://www.beclass.com/default.php?name=ShowList&op=recent")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='rid=']")
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.beclass.com", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "BeClass", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[BeClass] 抓取 {len(events)} 筆")
    return events

async def fetch_indievox(session):
    logger.info("🚀 啟動 iNDIEVOX...")
    html = await fetch_text(session, "https://www.indievox.com/activity/list")
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
        ev = create_event_obj(title, full_url, "iNDIEVOX", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[iNDIEVOX] 抓取 {len(events)} 筆")
    return events

async def fetch_ibon(session):
    logger.info("🚀 啟動 ibon...")
    html = await fetch_text(session, "https://ticket.ibon.com.tw/Activity/Index")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    # V37 改良: 直接抓 href
    links = soup.find_all('a', href=re.compile(r'ActivityDetail'))
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://ticket.ibon.com.tw", link.get('href'))
        if full_url in seen: continue
        # ibon 標題通常在 onclick 或內部 div
        title = link.get('title')
        if not title: title = safe_get_text(link.find(class_='virtual-title'))
        if not title: title = safe_get_text(link)
        
        img = link.find('img')
        ev = create_event_obj(title, full_url, "ibon", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[ibon] 抓取 {len(events)} 筆")
    return events

async def fetch_huashan(session):
    logger.info("🚀 啟動 華山...")
    html = await fetch_text(session, "https://www.huashan1914.com/w/huashan1914/exhibition")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('.card-body a')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.huashan1914.com", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link.find('h3')) or safe_get_text(link)
        ev = create_event_obj(title, full_url, "華山1914", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[華山] 抓取 {len(events)} 筆")
    return events

async def fetch_songshan(session):
    logger.info("🚀 啟動 松山...")
    html = await fetch_text(session, "https://www.songshanculturalpark.org/exhibition")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('.exhibition-list a')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.songshanculturalpark.org", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link.find('h3')) or safe_get_text(link)
        img = link.find('img')
        ev = create_event_obj(title, full_url, "松山文創", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[松山] 抓取 {len(events)} 筆")
    return events

async def fetch_stroll(session):
    logger.info("🚀 啟動 StrollTimes...")
    html = await fetch_text(session, "https://strolltimes.com/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('h3.post-title a')
    events = []
    seen = set()
    for link in links:
        full_url = link.get('href')
        if full_url in seen: continue
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "StrollTimes", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[StrollTimes] 抓取 {len(events)} 筆")
    return events

async def fetch_kidsclub(session):
    logger.info("🚀 啟動 KidsClub...")
    html = await fetch_text(session, "https://www.kidsclub.com.tw/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    # V37: 寬鬆 href
    links = soup.find_all('a', href=re.compile(r'product|courses'))
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.kidsclub.com.tw", link.get('href'))
        if full_url in seen: continue
        title = link.get('title') or safe_get_text(link.find(class_='woocommerce-loop-product__title'))
        img = link.find('img')
        ev = create_event_obj(title, full_url, "KidsClub", img.get('src') if img else None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[KidsClub] 抓取 {len(events)} 筆")
    return events

async def fetch_wtc(session):
    logger.info("🚀 啟動 台北世貿...")
    html = await fetch_text(session, "https://www.twtc.com.tw/exhibition_list.aspx")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="exhibition_detail"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.twtc.com.tw", link.get('href'))
        if full_url in seen: continue
        title = safe_get_text(link)
        ev = create_event_obj(title, full_url, "台北世貿", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[台北世貿] 抓取 {len(events)} 筆")
    return events

async def fetch_cksmh(session):
    logger.info("🚀 啟動 中正紀念堂...")
    # [修正] V37 中正紀念堂網址
    html = await fetch_text(session, "https://www.cksmh.gov.tw/activitybee_list.aspx?n=105")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="activitybee_"]')
    events = []
    seen = set()
    for link in links:
        full_url = urljoin("https://www.cksmh.gov.tw", link.get('href'))
        if full_url in seen: continue
        title = link.get('title') or safe_get_text(link)
        ev = create_event_obj(title, full_url, "中正紀念堂", None)
        if ev: events.append(ev); seen.add(full_url)
    logger.info(f"[中正紀念堂] 抓取 {len(events)} 筆")
    return events

# =========================
# 💾 存檔 & 通知
# =========================
async def send_line_notify(message):
    if not LINE_TOKEN: return
    async with aiohttp.ClientSession() as session:
        await session.post("https://notify-api.line.me/api/notify", headers={"Authorization": f"Bearer {LINE_TOKEN}"}, data={"message": message})

def load_existing_data():
    if not OUTPUT_FILE.exists(): return []
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return []

async def save_data_and_notify(new_events):
    existing_events = load_existing_data()
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
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📊 資料庫更新完畢 | 總筆數: {len(final_list)} | 🆕 新增: {len(added_events)} | 🔄 更新: {updated_count}")

    if added_events and LINE_TOKEN:
        logger.info(f"📨 準備發送 LINE 通知 ({len(added_events)} 筆)...")
        msg = f"\n🔥 發現 {len(added_events)} 個新活動！\n"
        for e in added_events[:5]:
            msg += f"\n📌 {e['title'][:30]}\n🔗 {e['url']}\n"
        if len(added_events) > 5:
            msg += f"\n...還有 {len(added_events)-5} 筆，請上網頁查看！"
        await send_line_notify(msg)

async def main():
    logger.info("🔥 爬蟲程式開始執行 (V38 Native Port)...")
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            fetch_kktix(session), fetch_accupass(session), fetch_tixcraft(session),
            fetch_kham(session), fetch_opentix(session), fetch_udn(session), fetch_fami(session),
            fetch_era(session), fetch_tixfun(session), fetch_eventgo(session), fetch_beclass(session),
            fetch_indievox(session), fetch_ibon(session), fetch_huashan(session), fetch_songshan(session),
            fetch_stroll(session), fetch_kidsclub(session), fetch_wtc(session), fetch_cksmh(session)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_new_events = []
        for res in results:
            if isinstance(res, list): all_new_events.extend(res)
            else: logger.error(f"❌ 任務失敗: {res}")

        logger.info(f"🔍 本輪爬取匯總: 共抓取到 {len(all_new_events)} 筆有效資料")
        await save_data_and_notify(all_new_events)

if __name__ == "__main__":
    asyncio.run(main())
