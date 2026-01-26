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

# LINE Notify Token (從 GitHub Secrets 讀取)
LINE_TOKEN = os.environ.get("LINE_TOKEN")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
]

# 詳細頁網址白名單
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
    "中正紀念堂": re.compile(r"^https?://(www\.)?cksmh\.gov\.tw/activitybee_.*", re.I),
    "Klook": re.compile(r"^https?://(www\.)?klook\.com/.*", re.I), # 保留擴充性
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

        if full_url in seen_urls: continue
        if wl and not wl.match(full_url): continue

        # --- 強化版標題解析邏輯 ---
        title = None
        
        # 1. 優先從 title 屬性獲取
        title = link.get('title')
        
        # 2. 獲取內部圖片的 alt
        if not title or title.strip() in ['詳內文', '詳細資訊', '購票']:
            img = link.find('img')
            if img: title = img.get('alt') or img.get('title')
            
        # 3. 獲取所有內部文字並清理
        if not title or title.strip() in ['詳內文', '詳細資訊', '購票']:
            # 合併內部所有 span, div 的文字，並過濾掉純數字(票價)或短詞
            title = link.get_text(" ", strip=True)
            
        # 4. 終極清理：移除雜訊
        if title:
            # 移除常見的輔助文字
            noise = ['立即購票', '詳細內容', 'Read More', '活動詳情', '查看更多', '已結束']
            for n in noise:
                title = title.replace(n, "")
            # 移除日期格式 (例如 2026/01/01)
            title = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', '', title)
            title = title.strip()

        # 如果還是抓不到，或者抓到太短的東西，則放棄該連結
        if not title or len(title) < 4:
            continue

        # 圖片抓取
        img_url = None
        img_tag = link.find('img')
        if img_tag: img_url = img_tag.get('src')
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

    logger.info(f"[{platform_name}] 強化解析完成: 找到 {len(events)} 筆")
    return events

# =========================
# 🕷️ 各平台爬蟲函式 (19平台全收錄)
# =========================

async def fetch_kktix_events_list(session):
    logger.info("🚀 啟動 KKTIX 爬蟲...")
    base_url = "https://kktix.com/events"
    categories = [f"{base_url}?category_id={i}" for i in [2, 6, 4, 3, 8]] + ["https://kktix.com/"]
    all_events = []
    seen = set()
    for url in categories:
        await asyncio.sleep(random.uniform(1, 2))
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

async def fetch_accupass_events_list(session):
    logger.info("🚀 啟動 ACCUPASS 爬蟲...")
    base_url = "https://www.accupass.com/search"
    target_urls = [f"{base_url}?q={k}" for k in ["音樂", "藝文", "學習", "科技"]] + ["https://www.accupass.com/?area=north"]
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
                "title": title, "url": full_url, "platform": "ACCUPASS", "date": "詳內文", "img_url": img_url,
                "type": get_event_category_from_title(title), "scraped_at": datetime.now().isoformat()
            })
            seen.add(full_url)
    return all_events

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
            if e['url'] not in seen: all_events.append(e); seen.add(e['url'])
    return all_events

async def fetch_kham_events_list(session):
    logger.info("🚀 啟動 寬宏售票 爬蟲...")
    cats = {"205": "音樂會", "231": "展覽", "116": "戲劇", "129": "親子"}
    all_events = []
    seen = set()
    for cat_id, cat_name in cats.items():
        url = f"https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY={cat_id}"
        await asyncio.sleep(1)
        html = await fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select('a[href*="UTK0201"]')
        events = filter_links_for_platform(links, "https://kham.com.tw/", "寬宏")
        for e in events:
            if e['url'] not in seen:
                e['type'] = cat_name
                all_events.append(e); seen.add(e['url'])
    return all_events

async def fetch_opentix_events_list(session):
    logger.info("🚀 啟動 OPENTIX 爬蟲...")
    html = await fetch_text(session, "https://www.opentix.life/event")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/"]')
    return filter_links_for_platform(links, "https://www.opentix.life/", "OPENTIX")

async def fetch_udn_events_list(session):
    logger.info("🚀 啟動 UDN售票 爬蟲...")
    urls = ["https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=77&kdid=cateList", 
            "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=231&kdid=cateList"]
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
            if e['url'] not in seen: all_events.append(e); seen.add(e['url'])
    return all_events

async def fetch_famiticket_events_list(session):
    logger.info("🚀 啟動 FamiTicket 爬蟲...")
    html = await fetch_text(session, "https://www.famiticket.com.tw/Home")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='Content/Home/Activity']")
    return filter_links_for_platform(links, "https://www.famiticket.com.tw", "FamiTicket")

async def fetch_era_events_list(session):
    logger.info("🚀 啟動 年代售票 爬蟲...")
    html = await fetch_text(session, "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="UTK0201"]')
    return filter_links_for_platform(links, "https://ticket.com.tw", "年代售票")

async def fetch_tixfun_events_list(session):
    logger.info("🚀 啟動 TixFun 爬蟲...")
    html = await fetch_text(session, "https://tixfun.com/UTK0101_?TYPE=1&CATEGORY=77")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="UTK0201"]')
    return filter_links_for_platform(links, "https://tixfun.com", "TixFun售票網")

async def fetch_eventgo_events_list(session):
    logger.info("🚀 啟動 Event Go 爬蟲...")
    html = await fetch_text(session, "https://eventgo.bnextmedia.com.tw/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/event/detail"]')
    return filter_links_for_platform(links, "https://eventgo.bnextmedia.com.tw/", "Event Go")

async def fetch_beclass_events_list(session):
    logger.info("🚀 啟動 BeClass 爬蟲...")
    html = await fetch_text(session, "https://www.beclass.com/default.php?name=ShowList&op=recent")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='rid=']")
    return filter_links_for_platform(links, "https://www.beclass.com", "BeClass")

async def fetch_indievox_events_list(session):
    logger.info("🚀 啟動 iNDIEVOX 爬蟲...")
    html = await fetch_text(session, "https://www.indievox.com/activity/list")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="/activity/detail"]')
    return filter_links_for_platform(links, "https://www.indievox.com", "iNDIEVOX")

async def fetch_ibon_events_list(session):
    logger.info("🚀 啟動 ibon 爬蟲...")
    html = await fetch_text(session, "https://ticket.ibon.com.tw/Activity/Index")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="ActivityDetail"]')
    return filter_links_for_platform(links, "https://ticket.ibon.com.tw", "ibon")

async def fetch_huashan_events_list(session):
    logger.info("🚀 啟動 華山1914 爬蟲...")
    html = await fetch_text(session, "https://www.huashan1914.com/w/huashan1914/exhibition")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('.card-body a')
    return filter_links_for_platform(links, "https://www.huashan1914.com", "華山1914")

async def fetch_songshan_events_list(session):
    logger.info("🚀 啟動 松山文創 爬蟲...")
    html = await fetch_text(session, "https://www.songshanculturalpark.org/exhibition")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('.exhibition-list a')
    return filter_links_for_platform(links, "https://www.songshanculturalpark.org", "松山文創")

async def fetch_stroll_events_list(session):
    logger.info("🚀 啟動 StrollTimes 爬蟲...")
    html = await fetch_text(session, "https://strolltimes.com/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href]')
    return filter_links_for_platform(links, "https://strolltimes.com", "StrollTimes")

async def fetch_kidsclub_events_list(session):
    logger.info("🚀 啟動 KidsClub 爬蟲...")
    html = await fetch_text(session, "https://www.kidsclub.com.tw/")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href]')
    return filter_links_for_platform(links, "https://www.kidsclub.com.tw", "KidsClub")

async def fetch_wtc_events_list(session):
    logger.info("🚀 啟動 台北世貿 爬蟲...")
    html = await fetch_text(session, "https://www.twtc.com.tw/exhibition_list.aspx")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="exhibition_detail"]')
    return filter_links_for_platform(links, "https://www.twtc.com.tw", "台北世貿")

async def fetch_cksmh_events_list(session):
    logger.info("🚀 啟動 中正紀念堂 爬蟲...")
    # [修正] V34 原始網址 404，改用新網址
    url = "https://www.cksmh.gov.tw/activitybee_list.aspx?n=105" 
    html = await fetch_text(session, url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="activitybee_"]')
    return filter_links_for_platform(links, "https://www.cksmh.gov.tw", "中正紀念堂")

# =========================
# 💾 資料處理 & LINE 通知
# =========================
async def send_line_notify(message):
    if not LINE_TOKEN: return
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    data = {"message": message}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as resp:
            if resp.status == 200: logger.info("✅ LINE 通知發送成功")
            else: logger.error(f"❌ LINE 通知失敗: {resp.status}")

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
    
    for event in new_events:
        url = event['url']
        if url not in existing_map:
            existing_map[url] = event
            added_events.append(event)
        else:
            existing_map[url].update(event)
    
    # 存檔
    final_list = list(existing_map.values())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📊 總筆數: {len(final_list)} | 🆕 新增: {len(added_events)}")

    # LINE 通知邏輯 (僅通知新增的)
    if added_events and LINE_TOKEN:
        logger.info(f"📨 準備發送 LINE 通知 ({len(added_events)} 筆)...")
        # 為了避免洗版，只取前 5 筆 + 摘要
        msg = f"\n🔥 發現 {len(added_events)} 個新活動！\n"
        for e in added_events[:5]:
            msg += f"\n📌 {e['title'][:20]}...\n🔗 {e['url']}\n"
        if len(added_events) > 5:
            msg += f"\n...還有 {len(added_events)-5} 筆，請上網頁查看！"
        
        await send_line_notify(msg)

async def main():
    logger.info("🔥 爬蟲程式開始執行 (Web V34 Full + LINE)...")
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            fetch_kktix_events_list(session), fetch_accupass_events_list(session),
            fetch_tixcraft_events_list(session), fetch_kham_events_list(session),
            fetch_opentix_events_list(session), fetch_udn_events_list(session),
            fetch_famiticket_events_list(session), fetch_era_events_list(session),
            fetch_tixfun_events_list(session), fetch_eventgo_events_list(session),
            fetch_beclass_events_list(session), fetch_indievox_events_list(session),
            fetch_ibon_events_list(session), fetch_huashan_events_list(session),
            fetch_songshan_events_list(session), fetch_stroll_events_list(session),
            fetch_kidsclub_events_list(session), fetch_wtc_events_list(session),
            fetch_cksmh_events_list(session)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_new = []
        for res in results:
            if isinstance(res, list): all_new.extend(res)
            else: logger.error(f"❌ 任務失敗: {res}")

        logger.info(f"🔍 共抓取到 {len(all_new)} 筆有效資料")
        await save_data_and_notify(all_new)

if __name__ == "__main__":
    asyncio.run(main())
