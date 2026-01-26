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
# 同時輸出到 Console 和 File
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

# 詳細頁網址白名單 (V34)
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
    "Klook": re.compile(r"^https?://(www\.)?klook\.com/.*", re.I),
}

# =========================
# 🧩 輔助工具函式
# =========================
def get_headers(referer=None):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
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
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "其他"

async def fetch_text(session, url, headers=None, timeout_sec=20):
    if not headers: headers = get_headers()
    try:
        async with session.get(url, headers=headers, ssl=False, timeout=timeout_sec) as resp:
            if resp.status != 200:
                logger.warning(f"❌ HTTP {resp.status} - {url}")
                return None
            # 自動偵測編碼，解決中文亂碼導致標題抓不到的問題
            content_type = resp.headers.get('Content-Type', '').lower()
            if 'charset' in content_type:
                return await resp.text()
            else:
                # 若無指定，嘗試讀取 bytes 並自動解碼
                data = await resp.read()
                try:
                    return data.decode('utf-8')
                except:
                    try:
                        return data.decode('big5') # 嘗試 Big5 (部分台灣舊網站)
                    except:
                        return data.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"💥 請求異常: {url} - {e}")
        return None

# =========================
# ★ 核心過濾邏輯 (完全移植 V34 並增強) ★
# =========================
def filter_links_for_platform(links, base_url, platform_name):
    events = []
    seen_urls = set()
    wl = DETAIL_URL_WHITELIST.get(platform_name)
    
    logger.info(f"[{platform_name}] 原始連結數: {len(links)}")

    for link in links:
        href = link.get('href', '')
        if not href: continue
        full_url = urljoin(base_url, href).split('#')[0]

        # 平台特殊排除
        if platform_name == "Event Go" and not full_url.startswith("https://eventgo.bnextmedia.com.tw/event/detail"): continue
            
        if full_url in seen_urls: continue
        if wl and not wl.match(full_url): 
            # logger.debug(f"跳過非白名單連結: {full_url}") # 太多雜訊先註解
            continue

        # --- 標題解析策略 (模仿 V34 + 增強) ---
        title = link.get('title')
        
        # V34 邏輯: 優先 title -> 圖片 alt -> 文字
        if not title or title.strip() in ['詳內文', '詳細資訊', '購票', 'Read More', 'More', '']:
            img = link.find('img')
            if img: title = img.get('alt') or img.get('title')
        
        if not title or title.strip() in ['詳內文', '詳細資訊', '購票', 'Read More', 'More', '']:
            # 嘗試找內部的標題標籤 (針對華山、松菸等結構)
            header_tag = link.find(['h3', 'h4', 'h5', 'div', 'span'], class_=re.compile(r'(title|name|header|subject)', re.I))
            if header_tag: 
                title = header_tag.get_text(strip=True)
            else:
                # 最後手段：抓取所有文字
                title = link.get_text(" ", strip=True)

        # 清理標題
        if title:
            # 移除常見無意義字詞
            noise_words = ['立即購票', '詳細內容', 'Read More', '活動詳情', '查看更多', '已結束', '報名', '詳細資訊', '購票', 'More']
            for noise in noise_words:
                title = title.replace(noise, "")
            # 移除日期格式 (例如 2026/01/01 或 2026-01-01)
            title = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', '', title)
            title = re.sub(r'\s+', ' ', title).strip()

        # 過濾太短或仍是無效的標題
        if not title or len(title) < 3:
            continue

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

    logger.info(f"[{platform_name}] 有效活動數: {len(events)}")
    return events

# =========================
# 🕷️ 各平台爬蟲函式 (19 平台 - V34 復刻)
# =========================

async def fetch_kktix_events_list(session):
    return await generic_fetch(session, "KKTIX", "https://kktix.com/events", 
                               [f"https://kktix.com/events?category_id={i}" for i in [2,6,4,3,8]] + ["https://kktix.com/"],
                               'a[href*="/events/"], .event-item a, .event-card a')

async def fetch_accupass_events_list(session):
    # ACCUPASS 特殊處理
    logger.info("🚀 啟動 ACCUPASS...")
    base_url = "https://www.accupass.com/search"
    target_urls = [f"{base_url}?q={k}" for k in ["音樂", "藝文", "學習", "科技", "展覽"]] + ["https://www.accupass.com/?area=north"]
    all_events = []
    seen = set()
    for url in target_urls:
        await asyncio.sleep(2)
        html = await fetch_text(session, url, headers=get_headers('https://www.accupass.com/'))
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        candidates = soup.find_all('a', href=re.compile(r'^/event/([A-Za-z0-9]+)'))
        
        logger.info(f"[ACCUPASS] URL {url} 找到 {len(candidates)} 個候選連結")
        
        for link in candidates:
            href = link.get('href')
            full_url = urljoin("https://www.accupass.com", href).split('?')[0]
            if full_url in seen: continue
            
            # 標題強化
            title = safe_get_text(link.find('h3'))
            if not title: title = safe_get_text(link.find(class_=re.compile(r'title', re.I)))
            if not title: title = safe_get_text(link)
            
            if len(title) < 2: continue
            
            img_tag = link.find('img')
            img_url = img_tag.get('src') if img_tag else None
            
            all_events.append({
                "title": title, "url": full_url, "platform": "ACCUPASS", "date": "詳內文", "img_url": img_url,
                "type": get_event_category_from_title(title), "scraped_at": datetime.now().isoformat()
            })
            seen.add(full_url)
    logger.info(f"[ACCUPASS] 總共抓取 {len(all_events)} 筆")
    return all_events

# 通用抓取器
async def generic_fetch(session, name, base_url, urls, selector, delay=1):
    logger.info(f"🚀 啟動 {name}...")
    if isinstance(urls, str): urls = [urls]
    all_events = []
    seen = set()
    for url in urls:
        await asyncio.sleep(delay)
        html = await fetch_text(session, url)
        if not html: continue
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select(selector)
        logger.info(f"[{name}] URL {url} 選擇器 '{selector}' 找到 {len(links)} 個原始連結")
        events = filter_links_for_platform(links, base_url, name)
        for e in events:
            if e['url'] not in seen:
                all_events.append(e)
                seen.add(e['url'])
    return all_events

# 各平台定義
async def fetch_tixcraft(s): return await generic_fetch(s, "拓元售票", "https://tixcraft.com", ["https://tixcraft.com/activity", "https://tixcraft.com/activity/list/select_type/all"], 'a[href*="/activity/detail/"]')
async def fetch_kham(s): return await generic_fetch(s, "寬宏", "https://kham.com.tw", [f"https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY={i}" for i in [205,231,116,129]], 'a[href*="UTK0201"]')
async def fetch_opentix(s): return await generic_fetch(s, "OPENTIX", "https://www.opentix.life", "https://www.opentix.life/event", 'a[href*="/event/"]')
async def fetch_udn(s): return await generic_fetch(s, "UDN售票網", "https://tickets.udnfunlife.com", ["https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=77&kdid=cateList","https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=231&kdid=cateList"], 'a[href*="UTK0201"]')
async def fetch_fami(s): return await generic_fetch(s, "FamiTicket", "https://www.famiticket.com.tw", "https://www.famiticket.com.tw/Home", "a[href*='Content/Home/Activity']")
async def fetch_era(s): return await generic_fetch(s, "年代售票", "https://ticket.com.tw", "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77", 'a[href*="UTK0201"]')
async def fetch_tixfun(s): return await generic_fetch(s, "TixFun售票網", "https://tixfun.com", "https://tixfun.com/UTK0101_?TYPE=1&CATEGORY=77", 'a[href*="UTK0201"]')
async def fetch_eventgo(s): return await generic_fetch(s, "Event Go", "https://eventgo.bnextmedia.com.tw", "https://eventgo.bnextmedia.com.tw/", 'a[href*="/event/detail"]')
async def fetch_beclass(s): return await generic_fetch(s, "BeClass", "https://www.beclass.com", "https://www.beclass.com/default.php?name=ShowList&op=recent", "a[href*='rid=']")
async def fetch_indievox(s): return await generic_fetch(s, "iNDIEVOX", "https://www.indievox.com", "https://www.indievox.com/activity/list", 'a[href*="/activity/detail"]')
async def fetch_ibon(s): return await generic_fetch(s, "ibon", "https://ticket.ibon.com.tw", "https://ticket.ibon.com.tw/Activity/Index", 'a[href*="ActivityDetail"]')
async def fetch_huashan(s): return await generic_fetch(s, "華山1914", "https://www.huashan1914.com", "https://www.huashan1914.com/w/huashan1914/exhibition", '.card-body a') 
async def fetch_songshan(s): return await generic_fetch(s, "松山文創", "https://www.songshanculturalpark.org", "https://www.songshanculturalpark.org/exhibition", '.exhibition-list a')
async def fetch_stroll(s): return await generic_fetch(s, "StrollTimes", "https://strolltimes.com", "https://strolltimes.com/", 'h3.post-title a') 
async def fetch_kidsclub(s): return await generic_fetch(s, "KidsClub", "https://kidsclub.com.tw", "https://kidsclub.com.tw/", 'a[href*="/product/"], a[href*="/courses/"]') 
async def fetch_wtc(s): return await generic_fetch(s, "台北世貿", "https://www.twtc.com.tw", "https://www.twtc.com.tw/exhibition_list.aspx", 'a[href*="exhibition_detail"]')
async def fetch_cksmh(s): return await generic_fetch(s, "中正紀念堂", "https://www.cksmh.gov.tw", "https://www.cksmh.gov.tw/activitybee_list.aspx?n=105", 'a[href*="activitybee_"]')

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
    logger.info("🔥 爬蟲程式開始執行 (V35 Fix)...")
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            fetch_kktix_events_list(session), fetch_accupass_events_list(session), fetch_tixcraft(session),
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
