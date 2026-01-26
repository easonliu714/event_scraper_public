# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import random
import json
import re
import time
import logging
from datetime import datetime
from urllib.parse import urljoin
from pathlib import Path
from bs4 import BeautifulSoup

# =========================
# 🛠️ 設定區 & 日誌配置
# =========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("docs")
OUTPUT_FILE = OUTPUT_DIR / "data.json"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
]

# 詳細頁網址白名單 (新增 V34 所有平台)
DETAIL_URL_WHITELIST = {
    "拓元售票": re.compile(r"^https?://(www\.)?tixcraft\.com/activity/detail/[A-Za-z0-9_-]+", re.I),
    "KKTIX": re.compile(r"^https?://[a-z0-9-]+\.kktix\.cc/events/[A-Za-z0-9-_]+", re.I),
    "OPENTIX": re.compile(r"^https?://(www\.)?opentix\.life/event/\d+", re.I),
    "年代售票": re.compile(r"^https?://(www\.)?ticket\.com\.tw/application/UTK02/UTK0201_\.aspx\?PRODUCT_ID=[A-Z0-9]+", re.I),
    "UDN售票網": re.compile(r"^https?://(www\.)?tickets\.udnfunlife\.com/application/UTK02/UTK0201_\.aspx\?PRODUCT_ID=[A-Z0-9]+", re.I),
    "TixFun售票網": re.compile(r"^https?://(www\.)?tixfun\.com/UTK0201_\?PRODUCT_ID=[A-Z0-9]+", re.I),
    "寬宏": re.compile(r"^https?://(www\.)?kham\.com\.tw/application/UTK02/UTK0201_\.aspx\?PRODUCT_ID=[A-Z0-9]+", re.I),
    "Event Go": re.compile(r"^https?://eventgo\.bnextmedia\.com\.tw/event/detail[^\s]*$", re.I),
    "iNDIEVOX": re.compile(r"^https?://(www\.)?indievox\.com/activity/detail/[0-9_]+", re.I),
    "ibon": re.compile(r"^https?://ticket\.ibon\.com\.tw/ActivityDetail/.*", re.I),
    "華山1914": re.compile(r"^https?://(www\.)?huashan1914\.com/w/huashan1914/exhibition.*", re.I),
    "松山文創": re.compile(r"^https?://(www\.)?songshanculturalpark\.org/exhibition.*", re.I),
    "KidsClub": re.compile(r"^https?://(www\.)?kidsclub\.com\.tw/.*", re.I),
    "StrollTimes": re.compile(r"^https?://strolltimes\.com/.*", re.I),
    "台北世貿": re.compile(r"^https?://(www\.)?twtc\.com\.tw/.*", re.I),
    "中正紀念堂": re.compile(r"^https?://(www\.)?cksmh\.gov\.tw/.*", re.I),
}

# =========================
# 🧩 輔助工具函式
# =========================
def get_headers(referer=None):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    if referer: headers['Referer'] = referer
    return headers

def safe_get_text(element, default="詳內文"):
    if element and hasattr(element, 'get_text'):
        text = element.get_text(strip=True)
        return text if text else default
    return default

def get_event_category_from_title(title):
    if not title: return "其他"
    title_lower = title.lower()
    category_mapping = {
        "音樂會/演唱會": ["音樂會", "演唱會", "獨奏會", "合唱", "交響", "管樂", "國樂", "弦樂", "鋼琴", "提琴", "巡演", "fan concert", "fancon", "音樂節", "爵士", "演奏", "歌手", "樂團", "tour", "live", "concert", "solo", "recital", "電音派對", "藝人見面會"],
        "音樂劇/歌劇": ["音樂劇", "歌劇", "musical", "opera"],
        "戲劇表演": ["戲劇", "舞台劇", "劇團", "劇場", "喜劇", "公演", "掌中戲", "歌仔戲", "豫劇", "話劇", "相聲", "布袋戲", "京劇", "崑劇", "藝文活動"],
        "舞蹈表演": ["舞蹈", "舞作", "舞團", "芭蕾", "舞劇", "現代舞", "民族舞", "踢踏舞", "zumba"],
        "展覽/博覽": ["展覽", "特展", "博物館", "美術館", "藝術展", "畫展", "攝影展", "文物展", "科學展", "博覽會", "動漫", "展出"],
        "親子活動": ["親子", "兒童", "寶寶", "家庭", "小朋友", "童話", "卡通", "動畫", "體驗"],
        "電影放映": ["電影", "影展", "數位修復", "放映", "首映", "紀錄片", "動畫電影"],
        "體育賽事": ["棒球", "籃球", "錦標賽", "運動會", "足球", "羽球", "網球", "馬拉松", "路跑", "游泳", "體操", "championship", "遊戲競賽"],
        "講座/工作坊": ["工作坊", "課程", "導讀", "沙龍", "講座", "體驗", "研習", "培訓", "論壇", "研討會", "座談", "workshop", "職場工作術", "資訊科技", "AI", "Python", "競賽", "創作", "纏繞"],
        "娛樂表演": ["脫口秀", "魔術", "雜技", "馬戲", "特技", "魔幻", "綜藝", "娛樂", "秀場", "表演秀", "社群活動", "派對", "市集"],
        "其他": ["旅遊", "美食", "公益"]
    }
    for category, keywords in category_mapping.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "其他"

async def fetch_text(session, url, headers=None, timeout_sec=15):
    if not headers: headers = get_headers()
    try:
        start_time = time.time()
        async with session.get(url, headers=headers, ssl=False, timeout=timeout_sec) as resp:
            duration = time.time() - start_time
            if resp.status != 200:
                logger.warning(f"❌ HTTP {resp.status} - {url}")
                return None
            text = await resp.text()
            return text
    except asyncio.TimeoutError:
        logger.error(f"⏳ 請求逾時: {url}")
        return None
    except Exception as e:
        logger.error(f"💥 請求異常: {url} - {e}")
        return None

def filter_links_for_platform(links, base_url, platform_name):
    events = []
    seen_urls = set()
    wl = DETAIL_URL_WHITELIST.get(platform_name)

    for link in links:
        href = link.get('href', '')
        if not href: continue
        full_url = urljoin(base_url, href).split('#')[0]

        if platform_name == "Event Go" and not full_url.startswith("https://eventgo.bnextmedia.com.tw/event/detail"): 
            continue
            
        if full_url in seen_urls: continue
        # 若該平台有白名單設定，則檢查是否符合
        if wl and not wl.match(full_url): continue

        if platform_name == "UDN售票網":
            title_text = safe_get_text(link, '')
            if "NT$" in title_text: 
                title_text = title_text.split("NT$")[0].strip()
            title = title_text
        else:
            title = link.get('title')
            if not title:
                img = link.find('img')
                if img: title = img.get('alt')
            if not title:
                title = safe_get_text(link)

        if title:
            title = title.strip()
            title = re.sub(r'\s+', ' ', title) 

        if not title or len(title) < 3 or title in ['更多', '詳情', '購票', '立即購買', '詳細資訊', 'Read More']:
            continue

        img_url = None
        img_tag = link.find('img')
        if img_tag: img_url = img_tag.get('src')
        
        # 圖片路徑修正
        if img_url and not img_url.startswith('http'):
            img_url = urljoin(base_url, img_url)

        events.append({
            'title': title,
            'url': full_url,
            'platform': platform_name,
            'img_url': img_url,
            'date': "詳內文",
            'type': get_event_category_from_title(title),
            'scraped_at': datetime.now().isoformat()
        })
        seen_urls.add(full_url)

    logger.info(f"[{platform_name}] 解析完成: 找到 {len(events)} 筆")
    return events

# =========================
# 🕷️ 各平台爬蟲函式 (V34 全收錄)
# =========================

# 1. KKTIX
async def fetch_kktix_events_list(session):
    logger.info("🚀 啟動 KKTIX 爬蟲...")
    base_url = "https://kktix.com/events"
    categories = [
        f"{base_url}?category_id=2", f"{base_url}?category_id=6",
        f"{base_url}?category_id=4", f"{base_url}?category_id=3",
        f"{base_url}?category_id=8", "https://kktix.com/"
    ]
    all_events = []
    seen = set()
    for url in categories:
        await asyncio.sleep(random.uniform(1.5, 3))
        html = await fetch_text(session, url, headers=get_headers('https://kktix.com/'))
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="/events/"], .event-item a, .event-card a')
        events = filter_links_for_platform(links, "https://kktix.com/", "KKTIX")
        for e in events:
            if e['url'] not in seen:
                all_events.append(e)
                seen.add(e['url'])
    return all_events

# 2. ACCUPASS
async def fetch_accupass_events_list(session):
    logger.info("🚀 啟動 ACCUPASS 爬蟲...")
    base_url = "https://www.accupass.com/search"
    target_urls = [
        f"{base_url}?q=音樂", f"{base_url}?q=藝文",
        f"{base_url}?q=學習", f"{base_url}?q=科技",
        "https://www.accupass.com/?area=north"
    ]
    all_events = []
    seen = set()

    for url in target_urls:
        await asyncio.sleep(random.uniform(2, 4))
        html = await fetch_text(session, url, headers=get_headers('https://www.accupass.com/'))
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        candidates = soup.find_all('a', href=re.compile(r'^/event/([A-Za-z0-9]+)'))
        for link in candidates:
            href = link.get('href')
            if not href or 'javascript' in href: continue
            full_url = urljoin("https://www.accupass.com", href).split('?')[0]
            if full_url in seen: continue
            
            title = safe_get_text(link.find('h3')) or safe_get_text(link)
            if len(title) < 2: continue
            
            img_tag = link.find('img')
            img_url = img_tag.get('src') if img_tag else None

            all_events.append({
                "title": title, "url": full_url, "platform": "ACCUPASS",
                "date": "詳內文", "img_url": img_url,
                "type": get_event_category_from_title(title),
                "scraped_at": datetime.now().isoformat()
            })
            seen.add(full_url)
    logger.info(f"[ACCUPASS] 總共抓取 {len(all_events)} 筆")
    return all_events

# 3. 拓元
async def fetch_tixcraft_events_list(session):
    logger.info("🚀 啟動 拓元售票 爬蟲...")
    urls = ["https://tixcraft.com/activity", "https://tixcraft.com/activity/list/select_type/all"]
    all_events = []
    seen = set()
    for url in urls:
        await asyncio.sleep(1.5)
        html = await fetch_text(session, url, headers=get_headers('https://tixcraft.com/'))
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="/activity/detail/"]')
        events = filter_links_for_platform(links, "https://tixcraft.com/", "拓元售票")
        for e in events:
            if e['url'] not in seen:
                all_events.append(e)
                seen.add(e['url'])
    return all_events

# 4. 寬宏 (修正選擇器)
async def fetch_kham_events_list(session):
    logger.info("🚀 啟動 寬宏售票 爬蟲...")
    category_map = {
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=205": "音樂會/演唱會", 
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=231": "展覽/博覽",
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=116": "戲劇表演",
    }
    all_events = []
    seen = set()
    for url, cat in category_map.items():
        await asyncio.sleep(1)
        html = await fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="UTK0201"]') # V34 原始選擇器
        events = filter_links_for_platform(links, "https://kham.com.tw/", "寬宏")
        for e in events:
            if e['url'] not in seen:
                e['type'] = cat 
                all_events.append(e)
                seen.add(e['url'])
    return all_events

# 5. OPENTIX
async def fetch_opentix_events_list(session):
    logger.info("🚀 啟動 OPENTIX 爬蟲...")
    url = "https://www.opentix.life/event"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/"]')
    return filter_links_for_platform(links, "https://www.opentix.life/", "OPENTIX")

# 6. UDN
async def fetch_udn_events_list(session):
    logger.info("🚀 啟動 UDN售票 爬蟲...")
    urls = [
        "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=77&kdid=cateList", 
        "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=231&kdid=cateList"
    ]
    all_events = []
    seen = set()
    for url in urls:
        await asyncio.sleep(1)
        html = await fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="UTK0201"]')
        events = filter_links_for_platform(links, "https://tickets.udnfunlife.com/", "UDN售票網")
        for e in events:
            if e['url'] not in seen:
                all_events.append(e)
                seen.add(e['url'])
    return all_events

# 7. FamiTicket
async def fetch_famiticket_events_list(session):
    logger.info("🚀 啟動 FamiTicket 爬蟲...")
    url = "https://www.famiticket.com.tw/Home"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='Content/Home/Activity']")
    return filter_links_for_platform(links, "https://www.famiticket.com.tw", "FamiTicket")

# 8. 年代
async def fetch_era_events_list(session):
    logger.info("🚀 啟動 年代售票 爬蟲...")
    url = "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77" 
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="UTK0201"]')
    return filter_links_for_platform(links, "https://ticket.com.tw", "年代售票")

# 9. TixFun
async def fetch_tixfun_events_list(session):
    logger.info("🚀 啟動 TixFun 爬蟲...")
    url = "https://tixfun.com/UTK0101_?TYPE=1&CATEGORY=77"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="UTK0201"]')
    return filter_links_for_platform(links, "https://tixfun.com", "TixFun售票網")

# 10. Event Go
async def fetch_eventgo_events_list(session):
    logger.info("🚀 啟動 Event Go 爬蟲...")
    url = "https://eventgo.bnextmedia.com.tw/"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/detail"]')
    return filter_links_for_platform(links, url, "Event Go")

# 11. BeClass
async def fetch_beclass_events_list(session):
    logger.info("🚀 啟動 BeClass 爬蟲...")
    url = "https://www.beclass.com/default.php?name=ShowList&op=recent"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='rid=']")
    return filter_links_for_platform(links, "https://www.beclass.com", "BeClass")

# 12. iNDIEVOX
async def fetch_indievox_events_list(session):
    logger.info("🚀 啟動 iNDIEVOX 爬蟲...")
    url = "https://www.indievox.com/activity/list"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/activity/detail"]')
    return filter_links_for_platform(links, "https://www.indievox.com", "iNDIEVOX")

# 13. ibon (V34 邏輯)
async def fetch_ibon_events_list(session):
    logger.info("🚀 啟動 ibon 爬蟲...")
    url = "https://ticket.ibon.com.tw/Activity/Index"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="ActivityDetail"]')
    return filter_links_for_platform(links, "https://ticket.ibon.com.tw", "ibon")

# 14. 華山1914 (新增)
async def fetch_huashan_events_list(session):
    logger.info("🚀 啟動 華山1914 爬蟲...")
    url = "https://www.huashan1914.com/w/huashan1914/exhibition"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('.card-body a') # 依V34習慣
    return filter_links_for_platform(links, "https://www.huashan1914.com", "華山1914")

# 15. 松山文創 (新增)
async def fetch_songshan_events_list(session):
    logger.info("🚀 啟動 松山文創 爬蟲...")
    url = "https://www.songshanculturalpark.org/exhibition"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('.exhibition-list a')
    return filter_links_for_platform(links, "https://www.songshanculturalpark.org", "松山文創")

# 16. StrollTimes (新增)
async def fetch_stroll_events_list(session):
    logger.info("🚀 啟動 StrollTimes 爬蟲...")
    url = "https://strolltimes.com/"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href]')
    # StrollTimes 網址過濾較寬鬆，依賴白名單
    return filter_links_for_platform(links, "https://strolltimes.com", "StrollTimes")

# 17. KidsClub (新增)
async def fetch_kidsclub_events_list(session):
    logger.info("🚀 啟動 KidsClub 爬蟲...")
    url = "https://www.kidsclub.com.tw/"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href]')
    return filter_links_for_platform(links, "https://www.kidsclub.com.tw", "KidsClub")

# 18. 台北世貿 (新增)
async def fetch_wtc_events_list(session):
    logger.info("🚀 啟動 台北世貿 爬蟲...")
    url = "https://www.twtc.com.tw/exhibition_list.aspx"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="exhibition_detail"]')
    return filter_links_for_platform(links, "https://www.twtc.com.tw", "台北世貿")

# 19. 中正紀念堂 (新增)
async def fetch_cksmh_events_list(session):
    logger.info("🚀 啟動 中正紀念堂 爬蟲...")
    url = "https://www.cksmh.gov.tw/activitybee_list.aspx?n=105"
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="activitybee_"]')
    return filter_links_for_platform(links, "https://www.cksmh.gov.tw", "中正紀念堂")


# =========================
# 💾 核心邏輯：資料處理與存檔
# =========================
def load_existing_data():
    if not OUTPUT_FILE.exists():
        logger.info("⚠️ 找不到現有資料庫，將建立新檔案")
        return []
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"📂 成功讀取現有資料庫: {len(data)} 筆")
            return data
    except Exception as e:
        logger.error(f"❌ 讀取資料庫失敗: {e}，將建立新檔案")
        return []

def save_data(new_events):
    existing_events = load_existing_data()
    existing_map = {e['url']: e for e in existing_events}
    
    added_count = 0
    updated_count = 0

    for event in new_events:
        url = event['url']
        if url not in existing_map:
            existing_map[url] = event
            added_count += 1
        else:
            existing_map[url].update(event) 
            updated_count += 1
    
    final_list = list(existing_map.values())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 資料庫更新完成")
    logger.info(f"📊 總筆數: {len(final_list)} | 🆕 新增: {added_count} | 🔄 更新: {updated_count}")

async def main():
    logger.info("🔥 爬蟲程式開始執行 (Web Version V34 Full)...")
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            fetch_kktix_events_list(session),
            fetch_accupass_events_list(session),
            fetch_tixcraft_events_list(session),
            fetch_kham_events_list(session),
            fetch_opentix_events_list(session),
            fetch_udn_events_list(session),
            fetch_famiticket_events_list(session),
            fetch_era_events_list(session),
            fetch_tixfun_events_list(session),
            fetch_eventgo_events_list(session),
            fetch_beclass_events_list(session),
            fetch_indievox_events_list(session),
            fetch_ibon_events_list(session),
            fetch_huashan_events_list(session), # 新增
            fetch_songshan_events_list(session), # 新增
            fetch_stroll_events_list(session), # 新增
            fetch_kidsclub_events_list(session), # 新增
            fetch_wtc_events_list(session), # 新增
            fetch_cksmh_events_list(session) # 新增
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_new_events = []
        for res in results:
            if isinstance(res, list):
                all_new_events.extend(res)
            else:
                logger.error(f"❌ 某平台任務失敗: {res}")

        logger.info(f"🔍 本輪爬取匯總: 共抓取到 {len(all_new_events)} 筆有效資料")
        save_data(all_new_events)

if __name__ == "__main__":
    asyncio.run(main())
