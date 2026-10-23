# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import random
import time
import json
import os
import re
import schedule
import argparse
import urllib3
import subprocess  # [新增] 用於 Termux 通知
from datetime import datetime
from urllib.parse import urljoin
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import telegram
from telegram.constants import ParseMode

# =========================
# ⚙️ 使用者設定區 [新增]
# =========================
VERSION = "V44.2-CLOUD-GATE3"  # Notification opt-in; Actions single writer
MY_KEYWORDS = ["五月天", "周杰倫", "免費", "AI", "Python", "演唱會", "巨蛋", "tour", "concert", "鄧紫棋", "蔡依林", "Rain", "競賽", "創作", "禪繞", "公益", "zumba"]
# [新增] 標題黑名單關鍵字
BLACKLIST_KEYWORDS = ["文宣品放置", "團體特約導覽", "開放博物館"]

# =========================
# .env 載入（在讀 TOKEN/CHAT_ID 前執行）
# =========================
def load_env_from_file(env_path: str):
    p = Path(env_path).expanduser()
    if not p.exists():
        return
    try:
        with p.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val.endswith('>'):  # 修正 HTML 實體
                    val = val[:-1]
                if key and val and key not in os.environ:
                    os.environ[key] = val
    except Exception as e:
        print(f"載入 .env 失敗：{e}")

# 預設讀取常見路徑
load_env_from_file('~/my_project/.env')

# 舊鍵名相容
if 'TG_BOT_TOKEN' not in os.environ and 'TELEGRAM_TOKEN' in os.environ:
    os.environ['TG_BOT_TOKEN'] = os.environ['TELEGRAM_TOKEN']
if 'TG_CHAT_ID' not in os.environ and 'TELEGRAM_CHAT_ID' in os.environ:
    os.environ['TG_CHAT_ID'] = os.environ['TELEGRAM_CHAT_ID']

# =========================
# 設定區
# =========================

# [V43] TLS certificates remain verified; do not silence security warnings.

# [修改] 更新 User-Agent 列表以減少被擋機率
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
]

# [新增] Mobile User Agent
MOBILE_UA = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'

REQUEST_PARAMS = {'timeout': 20, 'allow_redirects': True}

# Telegram 設定
TOKEN = os.getenv('TG_BOT_TOKEN', 'REPLACE_ME')
CHAT_ID = os.getenv('TG_CHAT_ID', 'REPLACE_ME')

LOG_FILE = 'Show_News_log.json'
RUN_LOG = 'run.log'
FAILED_LOG = 'failed_messages.json'
STATS_LOG = 'connection_stats.json'

# [V44] Explicit opt-in: both notification channels default OFF. Only "1" enables.
ENABLE_TELEGRAM = os.environ.get('EVENT_RADAR_TELEGRAM', '0') == '1'
ENABLE_TERMUX = os.environ.get('EVENT_RADAR_TERMUX', '0') == '1'
PUBLISH_VIA_ACTIONS = os.environ.get('EVENT_RADAR_ACTIONS', '0') == '1'

bot = None
favorites_found_current_run = []  # [新增] 用於儲存本輪發現的關注活動

# =========================
# [新增] Termux 通知函式
# =========================
def send_termux_notification(title, content):
    # [V44] Do not invoke Termux API unless explicitly enabled in the shell.
    if not ENABLE_TERMUX:
        return False
    try:
        # 需安裝 Termux:API (pkg install termux-api) 並且在手機安裝 Termux:API App
        result = subprocess.run(["termux-notification", "--title", title, "--content", content], check=False, timeout=10)
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False

def check_is_favorite(title):
    if not title: return False
    for kw in MY_KEYWORDS:
        if kw.lower() in title.lower(): return True
    return False

# =========================
# 平台上下文
# =========================
class FetchContext:
    def __init__(self):
        self.ua = None
        self.cookies = {}
        self.last_referer = None
        self.consec_auth_fail = 0
        self.warmed = False

platform_contexts = {
    platform: FetchContext()
    for platform in [
        "拓元售票", "KKTIX", "OPENTIX", "寬宏", "年代售票", "UDN售票網", "TixFun售票網",
        "Event Go", "ACCUPASS", "BeClass", "FamiTicket",
        "華山1914", "松山文創", "台北世貿", "中正紀念堂",
        "KidsClub", "文化快遞", "Klook", "易遊網", "TaiwanPass", "便宜旅遊網", "StrollTimes",
        "ibon售票" # [新增]
    ]
}

# =========================
# requests Session
# =========================
def create_session():
    session = requests.Session()
    retry = Retry(total=2, read=2, connect=2, backoff_factor=0.6, status_forcelist=(429, 500, 502, 503, 504, 403, 401))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.6',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    })
    session.verify = True
    return session

session = create_session()

# =========================
# 統計與日誌
# =========================
def load_json_file(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

load_connection_stats = lambda: load_json_file(STATS_LOG)
save_connection_stats = lambda stats: save_json_file(stats, STATS_LOG)
load_log = lambda: load_json_file(LOG_FILE)
save_log = lambda log: save_json_file(log, LOG_FILE)
load_failed_log = lambda: load_json_file(FAILED_LOG)
save_failed_log = lambda log: save_json_file(log, FAILED_LOG)

def update_connection_stats(platform, url, success):
    stats = load_connection_stats()
    if platform not in stats:
        stats[platform] = {}
    if url not in stats[platform]:
        stats[platform][url] = {'success': 0, 'total': 0, 'success_rate': 0.0}
    stats[platform][url]['total'] += 1
    if success:
        stats[platform][url]['success'] += 1
    total = stats[platform][url]['total']
    succ = stats[platform][url]['success']
    stats[platform][url]['success_rate'] = succ / total if total > 0 else 0.0
    save_connection_stats(stats)

def append_log_run(msg):
    log_path = Path(RUN_LOG)
    mode = 'a' if log_path.exists() else 'w'
    with log_path.open(mode, encoding='utf-8') as f:
        f.write(f"[{datetime.now()}] {msg}\n")
    print(f"[DEBUG] {msg}")

def clean_failed_messages():
    failed_log = load_failed_log()
    main_log = load_log()
    cleaned_count = 0
    for url, failure_data in list(failed_log.items()):
        if failure_data.get('count', 0) >= 3:
            if url in main_log:
                del main_log[url]
            cleaned_count += 1
            append_log_run(f"清理持續失敗的活動: {failure_data.get('title', 'Unknown')}")
            del failed_log[url]
    if cleaned_count > 0:
        save_log(main_log)
        save_failed_log(failed_log)
        append_log_run(f"共清理 {cleaned_count} 筆持續發送失敗的活動記錄")

def save_data_to_docs(events):
    """[V43] Preserve historical rows/valid details, atomic write, no ageing-based bulk deletion."""
    output_dir = Path('docs')
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / 'data.json'
    existing = []
    if filepath.exists():
        try:
            with filepath.open('r', encoding='utf-8') as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                raise ValueError('unexpected existing JSON format')
        except Exception as exc:
            append_log_run('HOLD DATA: unreadable existing data.json ('+type(exc).__name__+')')
            return None
    data_map = {e['url']:dict(e) for e in existing if isinstance(e,dict) and e.get('url')}
    unique_new = {e['url']:e for e in events if isinstance(e,dict) and e.get('url') and e.get('title')}
    platforms = {e.get('platform') for e in unique_new.values() if e.get('platform')}
    # For a normal multi-source run, reject severely partial results before touching data.
    if len(unique_new) < 20 or len(platforms) < 3:
        append_log_run('HOLD DATA: insufficient events or platform coverage; preserved data.json')
        return None
    now = datetime.now().astimezone().isoformat()
    valid = lambda x: x is not None and str(x).strip() not in ('','詳內文','None','null','undefined','詳細資訊請點擊連結查看。')
    added = 0
    updated = 0
    for url, event in unique_new.items():
        row = data_map.get(url)
        if row is None:
            row = {}
            data_map[url] = row
            added += 1
        else:
            updated += 1
        # Preserve verified details when a later adapter has only placeholder fields.
        for key, value in event.items():
            if key in ('date','location','price','description','ticket_date','img_url') and not valid(value) and valid(row.get(key)):
                continue
            row[key] = value
        row['scraped_at'] = now
        row['region'] = get_event_region(row.get('platform',''), row.get('location',''), row.get('title',''))
    output = sorted(data_map.values(), key=lambda x:x.get('scraped_at',''), reverse=True)
    temp = filepath.with_name('data.json.'+str(os.getpid())+'.tmp')
    try:
        with temp.open('w',encoding='utf-8') as f:
            json.dump(output,f,ensure_ascii=False,indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp,filepath)
        append_log_run(f'PASS DATA: retained={len(output)}, new={added}, updated={updated}; historical rows preserved')
        return filepath
    finally:
        if temp.exists():
            temp.unlink()


def upload_docs_to_github():
    """[V43] Fail-closed non-force publish; refuse remote drift instead of merge."""
    def git(*args, check=True):
        return subprocess.run(["git", *args], capture_output=True, text=True, check=check)
    try:
        if git('branch', '--show-current').stdout.strip() != 'main':
            append_log_run('HOLD Git: not on main; refuse automatic publish')
            return False
        remote = git('remote', 'get-url', 'origin').stdout.strip()
        if not re.search(r'(?:github[.]com[:/])easonliu714/event_scraper_public(?:[.]git)?$',remote,re.I):
            append_log_run('HOLD Git: origin does not match event_scraper_public')
            return False
        status = git('status', '--porcelain', '--untracked-files=no').stdout.splitlines()
        if any(not line[3:].strip().replace('\\', '/') == 'docs/data.json' for line in status):
            append_log_run('HOLD Git: tracked files other than docs/data.json are dirty')
            return False
        git('fetch', 'origin', 'main')
        local_head = git('rev-parse', 'HEAD').stdout.strip()
        remote_head = git('rev-parse', 'FETCH_HEAD').stdout.strip()
        if local_head != remote_head:
            append_log_run('HOLD Git: origin/main moved; manual fast-forward reconciliation required')
            return False
        git('add', '--', 'docs/data.json')
        diff = git('diff', '--cached', '--quiet',check=False)
        if diff.returncode == 0:
            append_log_run('PASS Git: no data changes')
            return True
        if diff.returncode != 1:
            append_log_run('HOLD Git: index diff inspection failed')
            return False
        msg = 'Termux EventRadar V43: ' + datetime.now().strftime('%Y-%m-%d %H:%M')
        git('-c', 'user.name=Termux Event Radar', '-c', 'user.email=termux-event-radar@users.noreply.github.com', 'commit', '-m', msg)
        git('push', 'origin', 'HEAD:main')
        append_log_run('PASS Git: fast-forward push accepted')
        return True
    except Exception as e:
        append_log_run('HOLD Git: publication failed (' + type(e).__name__ + ')')
        return False


def clear_log():
    for f in [LOG_FILE, FAILED_LOG]:
        if os.path.exists(f):
            os.remove(f)
    append_log_run("已清空舊的活動日誌和失敗記錄")

def record_failed_message(event, error_msg):
    failed_log = load_failed_log()
    url = event.get('url', '')
    title = event.get('title', '未知活動')

    # 1. 如果是全新的錯誤連結，初始化它
    if url not in failed_log:
        failed_log[url] = {
            'title': title,
            'platform': event.get('platform', '未知平台'),
            'count': 0,
            'last_error': '',
            'first_failed': datetime.now().isoformat(),
            'error_types': []
        }

    # 2. [關鍵修改] 舊資料相容性檢查 (防崩潰)
    # 如果舊的 log 資料裡面沒有 'count' 或 'error_types'，先補上預設值
    if 'count' not in failed_log[url]:
        failed_log[url]['count'] = 0

    if 'error_types' not in failed_log[url]:
        failed_log[url]['error_types'] = []

    # 3. 安全地更新數據
    failed_log[url]['count'] += 1
    failed_log[url]['last_error'] = str(error_msg)
    failed_log[url]['last_failed'] = datetime.now().isoformat()

    # 錯誤類型分析邏輯
    error_lower = str(error_msg).lower()
    error_type = 'unknown'
    if any(e in error_lower for e in ['401', '403', 'unauthorized', 'forbidden']):
        error_type = 'auth_error'
    elif any(e in error_lower for e in ['timeout', 'connection', 'network']):
        error_type = 'network_error'
    elif 'quality' in error_lower or 'message is too long' in error_lower:
        error_type = 'quality_error'
    elif 'flood' in error_lower or 'rate limit' in error_lower:
        error_type = 'rate_limit'

    if error_type not in failed_log[url].get('error_types', []):
        failed_log[url].setdefault('error_types', []).append(error_type)

    save_failed_log(failed_log)

# =========================
# 輔助函式
# =========================
def safe_get_text(element, default=""):
    return element.get_text(strip=True) if element and hasattr(element, 'get_text') and element.get_text(strip=True) else default

def get_event_category_from_title(title):
    if not title:
        return "其他"
    title_lower = title.lower()
    category_mapping = {
        "音樂會/演唱會": ["音樂會", "演唱會", "獨奏會", "合唱", "交響", "管樂", "國樂", "弦樂", "鋼琴", "提琴", "巡演", "fan concert", "fancon", "音樂節", "爵士", "演奏", "歌手", "樂團", "tour", "concert", "solo", "recital", "電音派對", "藝人見面會"],
        "音樂劇/歌劇": ["音樂劇", "歌劇", "musical", "opera"],
        "戲劇表演": ["戲劇", "舞台劇", "劇團", "劇場", "喜劇", "公演", "掌中戲", "歌仔戲", "豫劇", "話劇", "相聲", "布袋戲", "京劇", "崑劇", "藝文活動"],
        "舞蹈表演": ["舞蹈", "舞作", "舞團", "芭蕾", "舞劇", "現代舞", "民族舞", "踢踏舞"],
        "展覽/博覽": ["展覽", "特展", "博物館", "美術館", "藝術展", "畫展", "攝影展", "文物展", "科學展", "博覽會", "動漫"],
        "親子活動": ["親子", "兒童", "寶寶", "家庭", "小朋友", "童話", "卡通", "動畫"],
        "電影放映": ["電影", "影展", "數位修復", "放映", "首映", "紀錄片", "動畫電影"],
        "體育賽事": ["棒球", "籃球", "錦標賽", "運動會", "足球", "羽球", "網球", "馬拉松", "路跑", "游泳", "體操", "championship", "遊戲競賽"],
        "講座/工作坊": ["工作坊", "課程", "導讀", "沙龍", "講座", "體驗", "研習", "培訓", "論壇", "研討會", "座談", "workshop", "職場工作術", "資訊科技", "AI", "Python", "直播"],
        "娛樂表演": ["脫口秀", "魔術", "雜技", "馬戲", "特技", "魔幻", "綜藝", "娛樂", "秀場", "表演秀", "社群活動"],
        "其他": ["旅遊", "美食", "公益"]
    }
    for category, keywords in category_mapping.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "其他"

def get_event_region(platform, location, title=""):
    """
    根據平台、地點與標題判斷區域
    回傳值: "North", "Central", "South", "East", "Islands" 或 "Unknown"
    """
    # 1. 平台直屬區域判定
    if platform in ["華山1914", "松山文創", "台北世貿", "中正紀念堂", "文化快遞"]:
        return "North"

    # 2. 準備檢查的字串 (地點 + 標題)
    # 將兩者合併檢查，增加命中率
    check_text = (str(location) + str(title)).replace("臺", "台")

    if not check_text or check_text == "詳內文":
        return "Unknown"

    # 北部關鍵字
    if any(k in check_text for k in ["台北", "新北", "基隆", "桃園", "中壢", "平鎮", "新竹", "竹北", "宜蘭", "淡水", "板橋", "鶯歌", "小巨蛋", "松山", "華山", "北流", "大巨蛋", "國父紀念館", "國家音樂廳", "國家兩廳院", "國家戲劇院", "陽明山", "大霸尖山", "觀音山"]):
        return "North"

    # 中部關鍵字
    if any(k in check_text for k in ["台中", "苗栗", "竹南", "頭份", "彰化", "南投", "雲林", "歌劇院", "東勢親子館"]):
        return "Central"

    # 南部關鍵字
    if any(k in check_text for k in ["嘉義", "台南", "高雄", "屏東", "高雄巨蛋", "駁二", "衛武營", "恆春", "阿里山", "大鵬灣", "六堆"]):
        # 注意："巨蛋" 通常指高雄巨蛋(南部)，但若標題只有巨蛋需小心，這裡假設高雄巨蛋較常簡稱巨蛋
        return "South"

    # 東部關鍵字
    if any(k in check_text for k in ["花蓮", "台東"]):
        return "East"

    # 外島關鍵字
    if any(k in check_text for k in ["澎湖", "金門", "馬祖", "連江"]):
        return "Islands"

    return "Unknown"

# =========================
# 詳細資訊擷取
# =========================
def extract_from_list_fallback(list_event):
    title = list_event.get("title", "")
    details = {
        'title': title or '詳內文',
        'date': '詳內文',
        'location': '詳內文',
        'ticket_date': '詳內文',
        'description': '詳細資訊請點擊連結查看。',
        'price': '詳內文'
    }
    date_match = re.search(r'(\d{4}[./]\d{1,2}[./]\d{1,2})', title)
    if date_match:
        details['date'] = date_match.group(1).strip()
    loc_match = re.search(r'[@＠]([^\s@#]+)', title)
    if loc_match:
        details['location'] = loc_match.group(1).strip()
    return details

def extract_event_details_simple(detail_url, platform_name, max_attempts=2, list_event=None):
    # [V31 修正] 標題黑名單：若抓到這些標題，代表抓錯了，應回退使用列表標題
    GENERIC_TITLES = [
        "FamiTicket全網購票網", "首頁", "列表", "更多", "活動列表",
        "台北世貿中心", "展演資訊 - 松山文創園區", "國立中正紀念堂",
        "活動列表 - 臺北市文化快遞", "線上展覽", "表演活動", "講座及研討會",
        "最新消息", "活動資訊", "詳細內容", "Ticket", "購票", "立即購票",
        "年代售票", "寬宏售票系統", "udn售票網", "TixFun", "全部活動", "熱門活動",
        "more", "MORE", "More"
    ]

    details = {
        'date': '詳內文', 'location': '詳內文', 'ticket_date': '詳內文',
        'description': '', 'title': '詳內文', 'price': '詳內文'
    }

    # 初始化：從列表資料繼承 (這是最可靠的來源)
    if list_event:
        if 'title' in list_event and list_event['title'] != '詳內文':
            details['title'] = list_event['title']
        if 'img_url' in list_event:
            details['img_url'] = list_event['img_url']

    # ==================== TixFun API 優先抓取 (v37增強版) ====================
    if platform_name == "TixFun售票網":
        try:
            product_id_match = re.search(r'PRODUCT_ID=([A-Z0-9]+)', detail_url)
            if product_id_match:
                product_id = product_id_match.group(1)
                api_url = f"https://tixfun.com/UTK0201_API?PRODUCT_ID={product_id}"

                # [V43] TLS verification on, JSON content-type checked
                api_response = session.get(api_url, verify=True, **REQUEST_PARAMS)

                # 如果回傳不是 JSON (例如回傳了 HTML 錯誤頁)，手動觸發錯誤進入 HTML 解析
                if "application/json" not in api_response.headers.get("Content-Type", ""):
                    raise ValueError("API Response is not JSON")

                api_data = api_response.json()

                details['title'] = api_data.get('NAME', (list_event or {}).get('title', '詳內文')).strip()
                details['date'] = api_data.get('SHOW_TIME_DISP', '詳內文').strip()
                details['location'] = api_data.get('SHOW_LOCATION_DISP', '詳內文').strip()

                price_text = api_data.get('PRICE_DISP', '詳內文').strip()
                cleaned_price = re.split(r'\s{2,}|;', price_text)[0].strip()
                if len(cleaned_price) > 50: cleaned_price = cleaned_price[:50] + "..."
                details['price'] = cleaned_price

                if 'MEMO' in api_data and api_data['MEMO']:
                    desc_soup = BeautifulSoup(api_data['MEMO'], 'html.parser')
                    desc_text = desc_soup.get_text(" ", strip=True)
                    if len(desc_text) > 200: desc_text = desc_text[:200] + "..."
                    details['description'] = desc_text

                if api_data.get('IMAGE_URL'):
                    details['img_url'] = f"https://tixfun.com{api_data.get('IMAGE_URL')}"

                append_log_run(f"TixFun API 提取成功: {details['title']}")
                return details
        except Exception as e:
            # 這裡不記錄 error traceback，避免 log 太亂，僅記錄轉 HTML 解析
            append_log_run(f"TixFun API 提取失敗 (轉 HTML 解析): {str(e)[:50]}")
    # ==================== API 抓取結束 ====================

    for attempt in range(max_attempts):
        try:
            time.sleep(random.uniform(1.0, 2.5))
            detail_response = session.get(detail_url, verify=True, **REQUEST_PARAMS)
            detail_response.raise_for_status()

            # [關鍵修正] 統一使用 replace 策略解碼，消除所有平台的編碼警告
            # 不再依賴 BeautifulSoup 的自動偵測，因為那會產生冗餘日誌
            detail_response.encoding = detail_response.apparent_encoding or detail_response.encoding or 'utf-8'
            html_content = detail_response.text
            detail_soup = BeautifulSoup(html_content, "html.parser")
            from event_details import parse_detail
            structured_details = parse_detail(html_content, detail_url)
            for key, value in structured_details.items():
                if value and key in details:
                    details[key] = value

            # [通用] 抓取 OG 圖片
            if not details.get('img_url'):
                og_img = detail_soup.find("meta", attrs={"property": "og:image"})
                if og_img: details['img_url'] = og_img.get('content')

            # [V31 修正] 標題抓取邏輯：增加過濾
            # [V36 增強] 加入 TixFun HTML 結構的 class 選擇器，解決 API 失敗時抓不到標題的問題
            title_candidates = [
                detail_soup.find("meta", attrs={"property": "og:title"}),
                detail_soup.find("title"),
                detail_soup.find("h1"),
                detail_soup.select_one(".product_name"), # TixFun 結構
                detail_soup.select_one(".info_title"),   # TixFun 結構
                detail_soup.select_one("h3.title"),      # 常見結構
                # [新增] 年代/TixFun 常見標題位置
                detail_soup.select_one("#prod-info-block h2"),
                detail_soup.select_one(".event-title")
            ]

            extracted_title = None
            for candidate in title_candidates:
                if candidate:
                    raw_t = candidate.get('content', '').strip() if candidate.name == 'meta' else safe_get_text(candidate)
                    if raw_t and len(raw_t) > 2:
                        # 檢查是否為黑名單標題
                        if any(bad in raw_t for bad in GENERIC_TITLES): continue
                        # 檢查是否只包含平台名稱 (太短通常是站名)
                        if platform_name in raw_t and len(raw_t) < len(platform_name) + 5: continue

                        extracted_title = raw_t
                        break

            # 只有當抓到的標題有效，才覆蓋列表的標題
            if extracted_title:
                # 若列表標題是預設值，直接覆蓋
                if details['title'] == '詳內文':
                    details['title'] = extracted_title
                # 若新標題與列表標題不同，且長度更長(通常代表資訊更多)，則覆蓋
                elif extracted_title != details['title'] and len(extracted_title) > len(details['title']):
                     details['title'] = extracted_title

            # 描述抓取 (保持不變)
            desc_selectors = [
                ("meta", {"property": "og:description"}), ("meta", {"name": "twitter:description"}),
                ("meta", {"name": "description"}), (".event-description", None), (".description", None)
            ]
            for selector, attrs in desc_selectors:
                elem = detail_soup.find(selector, attrs=attrs)
                if elem:
                    desc_text = elem.get('content', '').strip() if elem.name == 'meta' else safe_get_text(elem)
                    if len(desc_text) > 200: desc_text = desc_text[:200] + "..."
                    details['description'] = desc_text
                    break

            # 票價抓取 (保持不變)
            if details['price'] == '詳內文':
                page_text_for_price = detail_soup.get_text(" ", strip=True)
                price_label_match = re.search(r'(?:票價|售價|價格)\s*[:：]\s*([^\n\r]+)', page_text_for_price)
                if price_label_match:
                    price_text = price_label_match.group(1).strip()
                    cleaned_price = re.split(r'\s{2,}|;', price_text)[0].strip()
                    if len(cleaned_price) > 100: cleaned_price = cleaned_price[:100] + "..."
                    details['price'] = cleaned_price
                else:
                    price_pattern_match = re.search(r'(NT\$|TWD|NTD|NT)\s*[\d,]+\s*(?:~\s*[\d,]+)?', page_text_for_price, re.IGNORECASE)
                    if price_pattern_match:
                        details['price'] = price_pattern_match.group(0)

            # --- 平台專屬解析 (保持 V30 邏輯) ---
            if platform_name == "KKTIX":
                page_text = detail_soup.get_text(" ", strip=True).replace('\xa0', ' ')
                date_str, time_str = "", ""
                date_match = re.search(r'(?:活動|演出)日期\s*[:：]\s*([^\s]+)', page_text)
                if date_match: date_str = date_match.group(1).strip()
                time_match = re.search(r'(?:活動|演出)時間\s*[:：]\s*([^\s]+)', page_text)
                if time_match: time_str = time_match.group(1).strip()
                if date_str and time_str: details['date'] = f"{date_str} {time_str}"
                elif date_str: details['date'] = date_str

                # [修改] 地點擷取與截斷邏輯
                loc_match = re.search(r'(?:活動場地|演出地點)\s*[:：]\s*([^\n\r]+)', page_text)
                if loc_match:
                    raw_location = loc_match.group(1).strip()

                    # 設定截斷關鍵字
                    cutoff_keyword = "主辦單位"

                    if cutoff_keyword in raw_location:
                        # 找到 "主辦單位" 的位置，並只取到該處之前
                        idx = raw_location.find(cutoff_keyword)
                        location = raw_location[:idx].strip()
                        # 如果結尾有多餘的符號 (如 𖥔)，稍微清理一下
                        location = location.rstrip(" 𖥔")
                    else:
                        location = raw_location

                    # 補充地址 (如果有的話)
                    addr_match = re.search(r'(?:活動|演出)地址\s*[:：]\s*([^\n\r]+)', page_text)
                    if addr_match:
                        addr = addr_match.group(1).strip()
                        # 同樣對地址做截斷檢查
                        if cutoff_keyword in addr:
                            addr = addr[:addr.find(cutoff_keyword)].strip().rstrip(" 𖥔")

                        if addr not in location:
                            location += f" ({addr})"

                    details['location'] = location

                sale_match = re.search(r'(?:售票|啟售)時間\s*[:：]\s*([^\n\r]+)', page_text)
                if sale_match: details['ticket_date'] = sale_match.group(1).strip()

                price_match = re.search(r'票\s*價\s*[:：]\s*([\s\S]+?)(?=\s*(?:主辦單位|購票方式|注意事項|Fan Benefits)|$)', page_text)
                if price_match:
                    price_text = price_match.group(1).strip()
                    if len(price_text) > 100: price_text = price_text[:150] + "..."
                    details['price'] = price_text
                if details.get('description') and len(details['description']) > 150:
                    details['description'] = details['description'][:150] + "..."

            elif platform_name == "OPENTIX":
                meta_desc = detail_soup.find("meta", attrs={"property": "og:description"})
                if meta_desc and meta_desc.has_attr("content"):
                    content = meta_desc["content"]
                    info_patterns = [
                        (r'時間[:：]\s*([^,，]+)', 'date'), (r'地點[:：]\s*([^,，]+)', 'location'),
                        (r'售票時間[:：]\s*([^,，]+)', 'ticket_date'), (r'開賣時間[:：]\s*([^,，]+)', 'ticket_date')
                    ]
                    for pattern, field in info_patterns:
                        match = re.search(pattern, content)
                        if match and details[field] == '詳內文': details[field] = match.group(1).strip()

            elif platform_name in ["年代售票", "TixFun售票網"]:
                if details['title'] != '詳內文': details['title'] = details['title'].replace("年代售票 |", "").replace("TixFun |", "").strip()
                table = detail_soup.select_one(".event-table, .product_info, div#prod-info-block, .product-info-block")
                if table:
                    for row in table.find_all('tr'):
                        cells = [c.get_text(strip=True) for c in row.find_all('td')]
                        if len(cells) > 1:
                            if '演出時間' in cells[0] and details['date'] == '詳內文': details['date'] = cells[1]
                            if '演出地點' in cells[0] and details['location'] == '詳內文': details['location'] = cells[1]
                            if '票價' in cells[0] and details['price'] == '詳內文':
                                price_text = cells[1]
                                cleaned_price = re.split(r'\s{2,}|;', price_text)[0].strip()
                                if len(cleaned_price) > 50: cleaned_price = cleaned_price[:50] + "..."
                                details['price'] = cleaned_price

                if any(details[k] == '詳內文' for k in ['date', 'location', 'price']):
                    page_text = detail_soup.get_text(" ", strip=True)
                    if details['date'] == '詳內文':
                        date_match = re.search(r'(?:演出|活動)時間[:：]\s*([\s\S]+?)(?=\s*(?:演出地點|活動地點|票價|主辦單位|節目介紹)|$)', page_text)
                        if date_match:
                            date_text = date_match.group(1).strip()
                            if len(date_text) > 100: date_text = date_text[:100] + "..."
                            details['date'] = date_text
                    if details['location'] == '詳內文':
                        loc_match = re.search(r'(?:演出|活動)地點[:：]\s*([\s\S]+?)(?=\s*(?:時間|票價|注意事項|主辦單位)|$)', page_text)
                        if loc_match:
                            loc_text = loc_match.group(1).strip()
                            if len(loc_text) > 100: loc_text = loc_text[:100] + "..."
                            details['location'] = loc_text
                    if details['price'] == '詳內文':
                        price_match = re.search(r'票價\s*[:：]\s*([\s\S]+?)(?=\s*(?:節目介紹|注意事項|主辦單位|折扣優惠)|$)', page_text)
                        if price_match:
                            price_text = price_match.group(1).strip()
                            cleaned_price = re.split(r'\s{2,}|;', price_text)[0].strip()
                            if len(cleaned_price) > 50: cleaned_price = cleaned_price[:50] + "..."
                            details['price'] = cleaned_price

            # [V43] Structured data wins over page-wide regex guesses.
            for key, value in structured_details.items():
                if value:
                    details[key] = value
            return details

        except Exception as e:
            append_log_run(f"詳細頁面提取失敗 (第{attempt+1}次): {detail_url} - {e}")
            if attempt < max_attempts - 1:
                time.sleep(random.uniform(2.0, 4.0))

    append_log_run(f"{platform_name} 詳頁提取多次失敗，強制使用基本資訊降級：{detail_url}")
    return extract_from_list_fallback(list_event or {})

# =========================
# 第一階段：列表抓取
# =========================
DETAIL_URL_WHITELIST = {
    "拓元售票": re.compile(r"^https?://(www\.)?tixcraft\.com/activity/detail/[A-Za-z0-9_-]+", re.I),
    "KKTIX": re.compile(r"^https?://[a-z0-9-]+\.kktix\.cc/events/[A-Za-z0-9-_]+", re.I),
    "OPENTIX": re.compile(r"^https?://(www\.)?opentix\.life/event/\d+", re.I),
    "年代售票": re.compile(r"^https?://(www\.)?ticket\.com\.tw/application/UTK02/UTK0201_\.aspx\?PRODUCT_ID=[A-Z0-9]+", re.I),
    "UDN售票網": re.compile(r"^https?://(www\.)?tickets\.udnfunlife\.com/application/UTK02/UTK0201_\.aspx\?PRODUCT_ID=[A-Z0-9]+", re.I),
    "TixFun售票網": re.compile(r"^https?://(www\.)?tixfun\.com/UTK0201_\?PRODUCT_ID=[A-Z0-9]+", re.I),
    "寬宏": re.compile(r"^https?://(www\.)?kham\.com\.tw/application/UTK02/UTK0201_\.aspx\?PRODUCT_ID=[A-Z0-9]+", re.I),
    "Event Go": re.compile(r"^https?://eventgo\.bnextmedia\.com\.tw/event/detail[^\s]*$", re.I),
}

def filter_links_for_platform(links, base_url, platform_name):
    events, seen_urls = [], set()
    wl = DETAIL_URL_WHITELIST.get(platform_name)

    for link in links:
        href = link.get('href', '')
        if not href or href.startswith('javascript'): continue
        full_url = urljoin(base_url, href)

        if platform_name == "Event Go" and not full_url.startswith("https://eventgo.bnextmedia.com.tw/event/detail"): continue
        if full_url in seen_urls or (wl and not wl.match(full_url)): continue

        # [UDN 特殊邏輯保持不變]
        if platform_name == "UDN售票網":
            title_text = safe_get_text(link, '')
            if not title_text or len(title_text) < 10: continue
            price_match = re.search(r'NT\s*\$\s*[\d,]+\s*(?:~\s*[\d,]+)?', title_text)
            price = price_match.group(0).strip() if price_match else "詳內文"
            if price_match: title_text = title_text[:price_match.start()]
            date_pattern = r'(\d{4}[./]\d{1,2}[./]\d{1,2}(?:\s*~\s*\d{4}[./]\d{1,2}[./]\d{1,2})?)'
            date_match = re.search(date_pattern, title_text)
            date = date_match.group(1).strip() if date_match else "詳內文"
            if date_match:
                title = title_text[:date_match.start()].strip()
                location = title_text[date_match.end():].strip()
                location = re.sub(r'\.\.\.more.*$', '', location).strip(' ,')
                location = re.sub(r'\s+', ' ', location)
            else:
                title = re.sub(r'&amp;[a-zA-Z0-9#]+;', '', title_text).strip()
                location = "詳內文"
            if title.lower() in ['more', '更多', '詳情', '購票'] or not title: continue
            events.append({
                'title': title, 'url': full_url, 'platform': platform_name,
                'date': date, 'location': location, 'price': price,
                'type': get_event_category_from_title(title)
            })
            seen_urls.add(full_url)
            continue

        # [通用標題抓取升級]
        title = safe_get_text(link)

        # 1. 如果文字為空，嘗試找內部的圖片 Alt
        if not title:
            img = link.find('img')
            if img: title = img.get('alt', '').strip()

        # 2. 嘗試 title 屬性
        if not title:
            title = link.get('title', '').strip()

        # 3. 嘗試找內部的 header 標籤 (h3, h4)
        if not title:
            header_tag = link.find(['h3', 'h4', 'h5', 'div'])
            if header_tag: title = header_tag.get_text(strip=True)

        # [新增] 黑名單過濾
        if any(bk in title for bk in BLACKLIST_KEYWORDS):
            continue

        if not title or len(title) < 3: continue

        # 排除無效標題
        if title in ["詳情", "更多", "Read More", "購票", "立即購買"]: continue

        events.append({'title': title.strip(), 'url': full_url, 'platform': platform_name, 'type': get_event_category_from_title(title)})
        seen_urls.add(full_url)

    append_log_run(f"{platform_name} 過濾後剩餘 {len(events)} 個有效連結")
    return events

# [修正] 增加 encoding 參數支援
async def fetch_text(session: aiohttp.ClientSession, url: str, encoding=None, timeout_sec=15):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1'
    }
    try:
        # [V43] Keep TLS certificate validation enabled
        async with session.get(url, headers=headers, allow_redirects=True, ssl=True, timeout=timeout_sec) as resp:
            if resp.status != 200: raise Exception(f"HTTP {resp.status}")
            raw_data = await resp.read()

            # 優先使用指定的編碼
            if encoding:
                try: return raw_data.decode(encoding, errors='ignore')
                except: pass

            # 自動嘗試常見編碼
            try: return raw_data.decode('utf-8', errors='ignore')
            except: return raw_data.decode('big5', errors='ignore')

    except Exception as e:
        # 讓錯誤訊息更明確
        raise Exception(f"連線失敗: {str(e)}")

# [新增/確認] 除錯輔助：印出 HTML 檔頭 (V28 增強版)
def debug_html_sample(soup, platform_name, raw_html=None):
    links = soup.find_all('a', href=True)
    append_log_run(f"[{platform_name} DEBUG] 頁面共發現 {len(links)} 個連結")

    # 如果完全沒連結，印出 HTML 前 500 字檢查是否被擋 (Access Denied / 403)
    if len(links) == 0 and raw_html:
        clean_head = raw_html[:500].replace('\n', ' ')
        append_log_run(f"[{platform_name} HTML HEAD] {clean_head}")
        return

    # 印出前 3 個連結結構供分析
    for i, link in enumerate(links[:3]):
        href = link.get('href')
        text = link.get_text(strip=True)[:20]
        append_log_run(f"[{platform_name} SAMPLE {i}] href={href} | text={text}")

async def generic_category_fetcher(session, platform_name, category_map, selectors):
    all_events = []
    async def fetch_category(url, category):
        try:
            html = await fetch_text(session, url)
            soup = BeautifulSoup(html, "html.parser")
            links = []
            for selector in selectors:
                links = soup.select(selector)
                if links: break
            events = filter_links_for_platform(links, url, platform_name)
            for event in events: event['type'] = category
            return events
        except Exception as e:
            append_log_run(f"{platform_name} 分類頁面抓取失敗 {url}: {e}")
            return []
    tasks = [fetch_category(url, category) for url, category in category_map.items()]
    results = await asyncio.gather(*tasks)
    for event_list in results: all_events.extend(event_list)
    return all_events

async def fetch_kktix_events_list(session):
    # KKTIX (強化版 Cloudscraper：多重偽裝)
    base_url = "https://kktix.com/events"
    categories = [
        f"{base_url}?category_id=1",  # 演唱會
        f"{base_url}?category_id=2",  # 課程講座
        f"{base_url}?category_id=3",  # 社群活動
        f"{base_url}?category_id=4",  # 展覽
        f"{base_url}?category_id=5",  # 研討會
        f"{base_url}?category_id=6",  # 音樂會
        f"{base_url}?category_id=7",  # 見面會
        f"{base_url}?category_id=8",  # 電影
        f"{base_url}?category_id=11", # 藝文活動
        f"{base_url}?category_id=13", # 音樂
        f"{base_url}?category_id=14", # 戲劇
        "https://kktix.com/"          # 首頁 (精選)
    ]
    all_events = []
    seen_urls = set()

    # 嘗試初始化 cloudscraper
    scraper = None
    try:
        import cloudscraper
        # 嘗試使用不同的瀏覽器指紋
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'android', # 偽裝成 Android 手機，可能更適合 Termux 環境
                'desktop': False
            }
        )
    except ImportError:
        append_log_run("⚠️ 未安裝 cloudscraper，KKTIX 容易 403。請執行: pip install cloudscraper")

    # 定義同步抓取函式
    def fetch_sync(target_url):
        # 隨機 User-Agent 列表
        ua_list = [
            'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]

        headers = {
            'User-Agent': random.choice(ua_list),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/', # 偽裝從 Google 搜尋進來
            'Origin': 'https://kktix.com',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Upgrade-Insecure-Requests': '1'
        }

        if scraper:
            # Cloudscraper 雖然強，但有時會被 Termux 的 SSL 環境拖累
            # 這裡我們嘗試用它，如果失敗就捕捉錯誤
            try:
                resp = scraper.get(target_url, headers=headers, timeout=25)
                if resp.status_code == 200: return resp.text
            except Exception:
                pass

        # Fallback: 使用 requests
        import requests
        resp = requests.get(target_url, headers=headers, timeout=20)
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code}")
        return resp.text

    loop = asyncio.get_running_loop()

    for url in categories:
        try:
            # 增加延遲，讓伺服器放鬆戒心
            await asyncio.sleep(random.uniform(3.0, 6.0))

            try:
                html = await loop.run_in_executor(None, fetch_sync, url)
            except Exception as req_err:
                append_log_run(f"KKTIX 請求被拒 ({url}): {req_err}")
                continue

            soup = BeautifulSoup(html, "html.parser")

            links = soup.select('a[href*="/events/"]')
            if not links: links = soup.select('.event-item a')

            cat_count = 0
            for link in links:
                href = link.get('href')
                if not href: continue

                full_url = urljoin("https://kktix.com", href)

                if "/events/" not in full_url: continue
                if full_url in seen_urls: continue

                title = link.get('title')
                if not title:
                    title = link.get_text(strip=True)
                    if not title:
                        img = link.find('img')
                        if img: title = img.get('alt', '').strip()
                    if not title:
                        card = link.find_parent(class_=lambda x: x and 'event' in x)
                        if card:
                            t_tag = card.select_one('h2, h3, .name, .title')
                            if t_tag: title = t_tag.get_text(strip=True)

                if not title or len(title) < 2: continue
                if any(bk in title for bk in BLACKLIST_KEYWORDS): continue

                all_events.append({
                    'title': title,
                    'url': full_url,
                    'platform': "KKTIX",
                    'type': "藝文活動",
                    'location': "詳內文"
                })
                seen_urls.add(full_url)
                cat_count += 1

            # append_log_run(f"KKTIX 分類抓取: {cat_count} 筆")

        except Exception as e:
            append_log_run(f"KKTIX 解析錯誤 ({url}): {e}")
            continue

    append_log_run(f"KKTIX 總計抓取: {len(all_events)} 筆")
    return all_events

async def fetch_tixcraft_events_list(session):
    try:
        # 使用 v2 驗證過的 URL 和 Headers
        urls = ["https://tixcraft.com/activity", "https://tixcraft.com/activity/list/select_type/all"]
        all_events_dict = {} # 使用 Dict 以 URL 為 Key 進行去重

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://tixcraft.com/',
        }

        for url in urls:
            await asyncio.sleep(random.uniform(1.0, 2.0)) # 禮貌性延遲
            try:
                async with session.get(url, headers=headers, ssl=True, timeout=15) as resp:
                    if resp.status != 200:
                        append_log_run(f"拓元請求失敗 {url}: {resp.status}")
                        continue
                    html = await resp.text()
            except Exception as e:
                append_log_run(f"拓元連線錯誤: {e}")
                continue

            soup = BeautifulSoup(html, "html.parser")
            links = soup.select('a[href*="/activity/detail/"]')

            for link in links:
                href = link.get('href')
                if not href: continue
                full_url = urljoin("https://tixcraft.com/", href).split('#')[0]

                # 標題獲取邏輯 (v2 版本)
                title = link.get('title')
                if not title:
                    img = link.find('img')
                    if img: title = img.get('alt')
                if not title:
                    title = link.get_text(strip=True)

                if not title or len(title) < 2 or title in ["詳情", "立即購票", "購買"]:
                    continue

                # 去重複與保留最長標題
                if full_url in all_events_dict:
                    if len(title) > len(all_events_dict[full_url]['title']):
                        all_events_dict[full_url]['title'] = title.strip()
                else:
                    all_events_dict[full_url] = {
                        'title': title.strip(),
                        'url': full_url,
                        'platform': "拓元售票",
                        'type': get_event_category_from_title(title),
                        'price': '詳內文'
                    }

        events = list(all_events_dict.values())
        append_log_run(f"拓元售票 列表擷取成功: {len(events)} 筆 (已去重)")
        return events

    except Exception as e:
        append_log_run(f"拓元售票列表擷取錯誤: {e}")
        return []

async def fetch_opentix_events_list(session):
    try:
        html = await fetch_text(session, "https://www.opentix.life/event")
        soup = BeautifulSoup(html, "html.parser")
        return filter_links_for_platform(soup.select('a[href*="/event/"]'), "https://www.opentix.life/", "OPENTIX")
    except Exception as e:
        append_log_run(f"OPENTIX列表擷取錯誤: {e}")
        return []

async def fetch_kham_events_list(session):
    # 擴充寬宏的分類對照表
    category_map = {
        # 演唱會
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=205": "音樂會/演唱會",
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77": "音樂會/演唱會",
        # 音樂劇 / 戲劇
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=80": "音樂劇/歌劇",
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=116": "戲劇表演",
        # 展覽 / 親子
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=231": "展覽/博覽",
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=129": "親子活動",
        # 舞蹈 / 體育
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=100": "舞蹈表演",
        "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=218": "體育賽事"
    }

    # 寬宏伺服器有時較慢，使用通用 fetcher，它會並行處理
    return await generic_category_fetcher(session, "寬宏", category_map, ['a[href*="UTK0201"]'])

async def fetch_era_events_list(session):
    # 年代售票 - 正式版 (含標題優化與過濾)
    category_map = {
        # 將兩個音樂分類合併為同一名稱，程式會自動去重
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77": "音樂會/演唱會",
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=205": "音樂會/演唱會", # [修正] 改回原名
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=129": "親子活動",
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=188": "電影放映",
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=100": "舞蹈表演",
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=116": "戲劇表演",
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=218": "體育賽事",
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=163": "講座/工作坊",
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=231": "展覽/博覽",
        "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=229": "其他"
    }

    all_events = []
    seen_urls = set()

    # 這裡不需要印出 debug 訊息了
    # append_log_run(f"開始抓取年代售票...")

    for url, category in category_map.items():
        try:
            await asyncio.sleep(random.uniform(0.5, 1.0))
            async with session.get(url, ssl=True, timeout=20) as resp:
                if resp.status != 200:
                    append_log_run(f"年代售票 {category} 請求失敗: {resp.status}")
                    continue
                html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # 使用放寬的選擇器以確保不漏抓
            raw_links = soup.select('a[href]')

            cat_found = 0

            for link in raw_links:
                href = link.get('href', '')
                if not href or href.startswith('#') or href.startswith('javascript'): continue

                # 過濾非產品連結
                if "PRODUCT_ID=" not in href and "UTK0201" not in href:
                    continue

                full_url = urljoin(url, href)

                # 取得 ID 用於保底標題
                pid_match = re.search(r'PRODUCT_ID=([A-Z0-9]+)', full_url)
                pid = pid_match.group(1) if pid_match else "NoID"

                # 1. 去重檢查
                if full_url in seen_urls:
                    continue

                # === 標題抓取邏輯 (保留除錯版的強力邏輯) ===
                title = ""
                img = link.find('img')
                if img and img.get('alt'): title = img.get('alt').strip()
                if not title and link.get('title'): title = link.get('title').strip()
                if not title:
                    text = link.get_text(strip=True)
                    # 過濾無效文字
                    if text and text not in ["詳內文", "More", "更多資訊", "購票", "詳細資訊", "更多詳情 »", "»"]:
                        title = text
                if not title:
                    # 往上找父層 (Parent Search)
                    parent = link.find_parent(['li', 'div', 'td'])
                    if parent:
                        t_cand = parent.select_one('.title, .program-title, .prod-name, h3, h4')
                        if t_cand: title = t_cand.get_text(strip=True)

                if not title: title = f"[無標題] ID:{pid}"

                # === 嚴格過濾無效標題 ===
                if "更多詳情" in title or title == "»" or title in ["詳內文", "More", "更多資訊", "購票", "詳細資訊"]:
                    continue

                # 排除過短且包含平台名的雜訊
                if "年代售票" in title and len(title) < 6: continue

                # 黑名單過濾
                if any(bk in title for bk in BLACKLIST_KEYWORDS):
                    continue

                all_events.append({
                    'title': title,
                    'url': full_url,
                    'platform': "年代售票",
                    'type': category,
                    'location': "詳內文", # 列表頁通常無地點
                    'region': "Unknown"
                })
                seen_urls.add(full_url)
                cat_found += 1

            # 只有當該分類沒抓到任何東西時才記錄，避免日誌太長
            if cat_found == 0:
                append_log_run(f"年代售票 {category} 未抓取到活動 (可能無檔期)")

        except Exception as e:
            append_log_run(f"年代售票 {category} 發生錯誤: {e}")
            continue

    append_log_run(f"年代售票 總計抓取: {len(all_events)} 筆有效活動")
    return all_events

async def fetch_udn_events_list(session):
    category_map = {
        "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=231&kdid=cateList": "展覽/博覽", "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=77&kdid=cateList": "音樂會/演唱會",
        "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=116&kdid=cateList": "戲劇表演", "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=100&kdid=cateList": "舞蹈表演",
        "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=129&kdid=cateList": "親子活動", "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=205&kdid=cateList": "音樂會/演唱會",
        "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=218&kdid=cateList": "體育賽事", "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=163&kdid=cateList": "講座/工作坊",
        "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=101&kdid=cateList": "電影放映"
    }
    return await generic_category_fetcher(session, "UDN售票網", category_map, ['a[href*="UTK0201"]'])

async def fetch_tixfun_events_list(session):
    # [V37 修正] 改用 UTK0102_ 並擴充類別 (解決缺漏與分類錯誤問題)
    # 棄用 UTK0101_ 以避免重複抓取與效能浪費
    category_map = {
        "https://tixfun.com/UTK0102_?TYPE=1&CATEGORY=77": "音樂會/演唱會",
        "https://tixfun.com/UTK0102_?TYPE=1&CATEGORY=205": "音樂會/演唱會", # 新增
        "https://tixfun.com/UTK0102_?TYPE=1&CATEGORY=116": "戲劇表演",
        "https://tixfun.com/UTK0102_?TYPE=1&CATEGORY=80": "音樂劇/歌劇",   # 新增
        "https://tixfun.com/UTK0102_?TYPE=1&CATEGORY=100": "舞蹈表演",
        "https://tixfun.com/UTK0102_?TYPE=1&CATEGORY=129": "親子活動",
        "https://tixfun.com/UTK0102_?TYPE=1&CATEGORY=231": "展覽/博覽",
        "https://tixfun.com/UTK0102_?TYPE=1&CATEGORY=234": "展覽/博覽",   # 新增
        "https://tixfun.com/UTK0102_?TYPE=1&CATEGORY=218": "體育賽事",
    }

    # 先抓取資料
    events = await generic_category_fetcher(session, "TixFun售票網", category_map, ['a[href*="UTK0201"]'])

    # [V37 新增] 二次校正邏輯：解決「體育賽事」誤判問題
    # 如果標題包含明確關鍵字 (如: 音樂劇)，則覆蓋原本依照網址判定的類別
    for event in events:
        # 使用現有的 helper 函式分析標題
        detected_type = get_event_category_from_title(event['title'])

        # 如果標題偵測出的類型不是 "其他"，且與原類型不同，則以標題偵測為準
        if detected_type != "其他" and detected_type != event['type']:
            event['type'] = detected_type

    return events

async def fetch_eventgo_events_list(session):
    # Event Go (修正版：針對 list 頁面分頁)
    base_url = "https://eventgo.bnextmedia.com.tw/event/list"

    events = []
    seen_urls = set()
    # 爬取前 5 頁，確保抓滿 100 筆以上
    max_pages = 5

    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://eventgo.bnextmedia.com.tw/', # 加入 Referer 避免被判定為機器人
    }

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        try:
            if page > 1: await asyncio.sleep(random.uniform(1.5, 2.5))

            async with session.get(url, headers=headers, ssl=True, timeout=20) as resp:
                if resp.status != 200:
                    append_log_run(f"Event Go 第 {page} 頁 HTTP {resp.status}")
                    break
                html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            links = soup.select("a[href*='/event/detail']")
            if not links: break

            page_new_count = 0
            for link in links:
                href = link.get('href')
                full_url = urljoin("https://eventgo.bnextmedia.com.tw", href)
                if full_url in seen_urls: continue

                title = link.get_text(strip=True)
                if not title:
                    img = link.find('img')
                    if img: title = img.get('alt', '').strip()
                if not title: title = link.get('title', '').strip()

                location = "詳內文"
                card = link.find_parent(['div', 'article'], class_=lambda x: x and ('card' in x or 'item' in x))
                if card:
                    card_text = card.get_text(strip=True)
                    if "線上" in card_text: location = "線上活動"
                    else:
                        for city in ["台北", "新北", "基隆", "桃園", "新竹", "台中", "台南", "高雄", "宜蘭", "花蓮"]:
                            if city in card_text: location = city; break

                if not title or len(title) < 2: continue
                if any(bk in title for bk in BLACKLIST_KEYWORDS): continue

                events.append({
                    'title': title, 'url': full_url, 'platform': "Event Go",
                    'type': get_event_category_from_title(title), 'location': location
                })
                seen_urls.add(full_url)
                page_new_count += 1

            if page_new_count == 0: break

        except Exception as e:
            append_log_run(f"Event Go 第 {page} 頁失敗: {e}")
            break

    append_log_run(f"Event Go 總計抓取: {len(events)} 筆")
    return events


# --- [新增] 新平台 Fetcher ---
async def fetch_accupass_events_list(session):
    # 定義 ACCUPASS 的主題頁面
    theme_urls = [
        "https://www.accupass.com/search?t=this-weekend&utm_source=accupass&utm_medium=web_header&utm_campaign=accu_web_header", # 週末出遊
        "https://www.accupass.com/search?p=free&utm_source=accupass&utm_medium=web_header&utm_campaign=accu_web_header", # 免費活動
        "https://www.accupass.com/search?c=charitable&utm_source=accupass&utm_medium=web_header&utm_campaign=accu_web_header",   # 公益
        "https://www.accupass.com/search?c=learning&utm_source=accupass&utm_medium=web_header&utm_campaign=accu_web_header", # 學習
        "https://www.accupass.com/search?c=arts&utm_source=accupass&utm_medium=web_header&utm_campaign=accu_web_header" #藝文
        "https://www.accupass.com/search?c=travel&utm_source=accupass&utm_medium=web_header&utm_campaign=accu_web_header" #戶外體驗
        "https://www.accupass.com/?area=north"       # 北部活動 (首頁分頁)
    ]

    all_events = []
    seen_urls = set()

    for url in theme_urls:
        await asyncio.sleep(random.uniform(2.0, 4.0)) # 禮貌性延遲
        try:
            # 必須使用像真人的 Headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Referer': 'https://www.accupass.com/'
            }
            async with session.get(url, headers=headers, ssl=True, timeout=15) as resp:
                html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # 抓取 href 包含 /event/ 的連結
            candidates = soup.find_all('a', href=re.compile(r'^/event/([A-Za-z0-9]+)'))

            current_batch = 0
            for link in candidates:
                href = link.get('href')
                # 排除 javascript 連結或錨點
                if not href or 'javascript' in href or '#' in href: continue

                # 處理相對路徑
                full_url = urljoin("https://www.accupass.com", href)
                # 移除 URL 參數以利去重
                full_url = full_url.split('?')[0]

                if full_url in seen_urls: continue

                # 抓取標題 (Accupass 結構多變，嘗試多種方式)
                title_tag = link.find('h3')
                if not title_tag:
                     title_tag = link.find('div', class_=lambda x: x and 'title' in x.lower())

                title = title_tag.get_text(strip=True) if title_tag else link.get_text(strip=True)

                if title and len(title) > 2:
                    img_tag = link.find('img')
                    img_url = img_tag.get('src') if img_tag else None

                    all_events.append({
                        'title': title,
                        'url': full_url,
                        'platform': 'ACCUPASS',
                        'img_url': img_url,
                        'date': '詳內文',
                        'location': '詳內文',
                        'price': '詳內文',
                        'type': get_event_category_from_title(title)
                    })
                    seen_urls.add(full_url)
                    current_batch += 1

            append_log_run(f"ACCUPASS 主題抓取: {url.split('/')[-1]} -> {current_batch} 筆")

        except Exception as e:
            append_log_run(f"ACCUPASS 抓取失敗 {url}: {e}")

    return all_events

async def fetch_beclass_events_list(session):
    # BeClass (修正版：使用 ShowRegist 模式 + 分頁 + UTF-8 強制解碼)
    # 使用使用者提供的 op=ShowRegist 參數，這能列出更完整的報名清單
    base_url = "https://www.beclass.com/default.php?name=ShowList&op=ShowRegist&od="

    events = []
    seen_urls = set()
    taiwan_cities = ["台北", "新北", "基隆", "桃園", "新竹", "苗栗", "台中", "彰化", "南投", "雲林", "嘉義", "台南", "高雄", "屏東", "宜蘭", "花蓮", "台東", "澎湖", "金門", "馬祖"]

    # 設定爬取頁數：前 20 頁 (每頁約 20 筆，足以覆蓋近期活動)
    max_pages = 20

    for page in range(1, max_pages + 1):
        url = f"{base_url}&page={page}"
        try:
            if page > 1: await asyncio.sleep(random.uniform(1.0, 2.0))

            async with session.get(url, ssl=True, timeout=20) as resp:
                if resp.status != 200: break
                # [關鍵修正] 強制使用 utf-8 解碼並忽略錯誤，解決亂碼問題
                raw_data = await resp.read()
                html = raw_data.decode('utf-8', errors='replace')

            soup = BeautifulSoup(html, "html.parser")

            # ShowRegist 模式的連結通常包含 rid=
            links = soup.select("a[href*='rid=']")
            if not links: break

            page_new_count = 0
            for link in links:
                href = link.get('href')
                if not href: continue

                full_url = urljoin("https://www.beclass.com", href)
                if full_url in seen_urls: continue

                title = link.get_text(strip=True)
                if not title: title = link.get('title', '').strip()

                # 地點解析 (嘗試從整列文字中提取)
                location = "詳內文"
                parent = link.find_parent(['tr', 'div', 'li'])
                if parent:
                    row_text = parent.get_text(strip=True)
                    for city in taiwan_cities:
                        if city in row_text:
                            location = city
                            break

                if not title or len(title) < 2: continue
                if any(bk in title for bk in BLACKLIST_KEYWORDS): continue

                events.append({
                    'title': title,
                    'url': full_url,
                    'platform': "BeClass",
                    'type': get_event_category_from_title(title),
                    'location': location
                })
                seen_urls.add(full_url)
                page_new_count += 1

            # 如果這頁沒有新資料，提早結束
            if page_new_count == 0: break

        except Exception as e:
            append_log_run(f"BeClass 第 {page} 頁失敗: {e}")
            break

    append_log_run(f"BeClass 總計抓取: {len(events)} 筆")
    return events

async def fetch_famiticket_events_list(session):
    base_url = "https://www.famiticket.com.tw"
    events = []
    seen_urls = set()
    category_links = set()

    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://www.famiticket.com.tw/'
    }

    def parse_link(link_element, source_url):
        href = link_element.get('href')
        if not href or "Activity/Info" not in href: return

        full_url = urljoin(base_url, href)
        if full_url in seen_urls: return

        title = None
        # [V31 修正] 針對 FamiTicket 卡片結構精準抓取
        # 1. 嘗試往上找卡片容器
        card = link_element.find_parent(class_=['card', 'col-md-4', 'col-sm-6', 'activity-card'])
        if card:
            # 在卡片內找標題
            title_tag = card.select_one('.card-title, .caption h3, .caption h4, h3, h4')
            if title_tag: title = title_tag.get_text(strip=True)

        # 2. 備用：圖片 alt
        if not title:
            img = link_element.find('img')
            if img: title = img.get('alt')

        # 3. 備用：連結本身的文字 (但在 Fami 往往是空的或 "購票")
        if not title:
            text = link_element.get_text(strip=True)
            if text and "購票" not in text and "詳細" not in text: title = text

        # 過濾無效標題
        if not title or "FamiTicket" in title or "全網購票網" in title: return

        title = title.strip()
        if len(title) > 2:
            events.append({
                'title': title,
                'url': full_url,
                'platform': "FamiTicket",
                'type': get_event_category_from_title(title),
                'price': '詳內文'
            })
            seen_urls.add(full_url)

    try:
        async with session.get(base_url, headers=headers, ssl=True, timeout=15) as resp:
            html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")

        # 直接抓取所有活動連結
        all_links = soup.select('a[href*="Activity/Info"]')
        for link in all_links: parse_link(link, base_url)

        # 抓分類連結
        cat_links_tags = soup.select('a[href*="Activity/Search"]')
        for cl in cat_links_tags: category_links.add(urljoin(base_url, cl['href']))

        append_log_run(f"FamiTicket 首頁掃描: 發現 {len(events)} 個直接活動，{len(category_links)} 個分類入口")

    except Exception as e:
        append_log_run(f"FamiTicket 首頁失敗: {e}")

    # 深入爬取前 6 個分類
    target_categories = list(category_links)[:6]
    for cat_url in target_categories:
        try:
            await asyncio.sleep(random.uniform(1.0, 2.0))
            async with session.get(cat_url, headers=headers, ssl=True, timeout=15) as resp:
                html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            links = soup.select("a[href*='Activity/Info']")
            for link in links:
                parse_link(link, base_url)
        except Exception:
            pass

    append_log_run(f"FamiTicket 總計抓取: {len(events)} 筆")
    return events

# =========================
# 新增平台 Fetchers (V31 修復版)
# =========================
async def fetch_huashan_events_list(session):
    url = "https://www.huashan1914.com/w/huashan1914/exhibition"
    base_url = "https://www.huashan1914.com"

    try:
        # 嘗試抓取
        html = await fetch_text(session, url)
    except Exception as e:
        append_log_run(f"華山1914 連線異常: {e}")
        return []

    if not html: return []

    try:
        soup = BeautifulSoup(html, "html.parser")
        events = []
        seen = set()

        links = soup.select("a[href*='exhibition_']")

        for link in links:
            href = link.get('href')
            full_url = urljoin(base_url, href)
            if full_url in seen: continue

            raw_title = link.get_text(strip=True) or link.get('title')
            if not raw_title: continue

            # 清理標題
            title = re.sub(r'\d{4}[./]\d{2}[./]\d{2}.*', '', raw_title).strip()
            if len(title) < 2: continue

            events.append({
                'title': title,
                'url': full_url,
                'platform': "華山1914",
                'type': "展覽/博覽",
                'price': "詳內文"
            })
            seen.add(full_url)

        append_log_run(f"華山1914 抓取: {len(events)} 筆")
        return events
    except Exception as e:
        append_log_run(f"華山1914 解析異常: {e}")
        return []

async def fetch_songshan_events_list(session):
    # 松山文創園區 - 展覽與活動
    base_url = "https://www.songshanculturalpark.org/exhibition"
    all_events = []
    seen_urls = set()
    page = 1
    max_pages = 5  # 松山活動頁數通常不多，設定 5 頁綽綽有餘

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    while page <= max_pages:
        # 處理分頁網址
        url = f"{base_url}?page={page}"

        try:
            async with session.get(url, headers=headers, ssl=True, timeout=15) as resp:
                if resp.status != 200:
                    append_log_run(f"松山文創 請求異常 {url}: {resp.status}")
                    break # 遇到錯誤通常代表沒有更多頁面或伺服器問題

                html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # 根據松山官網結構，活動卡片通常在特定的列表中
            # 這裡使用較寬鬆的選擇器以防改版，但配合嚴格的標題過濾
            links = soup.find_all('a', href=True)

            current_page_count = 0

            # 檢查本頁是否有有效連結，若無則視為結束
            valid_links_found = False

            for link in links:
                href = link['href']

                # 過濾非活動頁面的連結 (松山活動通常包含 /exhibition/ 或 /event/)
                if "/exhibition/" not in href and "/event/" not in href:
                    continue

                # 排除列表頁本身 (避免抓到「回列表」之類的按鈕)
                if href.strip() == "/exhibition" or href.endswith("?page="):
                    continue

                full_url = urljoin("https://www.songshanculturalpark.org", href)

                if full_url in seen_urls: continue

                # [關鍵修正] 標題抓取與過濾 "看更多"
                title = ""

                # 1. 優先嘗試抓取連結內的標題標籤 (h3, h4, div.title)
                header_tag = link.find(['h3', 'h4', 'div'], class_=lambda x: x and 'title' in x.lower())
                if header_tag:
                    title = header_tag.get_text(strip=True)

                # 2. 其次抓取圖片 alt
                if not title:
                    img = link.find('img')
                    if img:
                        title = img.get('alt', '').strip()

                # 3. 最後才使用連結文字，但要過濾 "看更多"
                if not title:
                    text = link.get_text(strip=True)
                    if "看更多" not in text and "Read More" not in text:
                        title = text

                # [過濾] 再次確認標題不是 "看更多" 或無效字串
                if not title or title in ["看更多", "See More", "Read More", "詳細資訊"]:
                    continue

                # [過濾] 黑名單過濾 (配合 V39 的新功能)
                if any(bk in title for bk in BLACKLIST_KEYWORDS):
                    continue

                all_events.append({
                    'title': title,
                    'url': full_url,
                    'platform': "松山文創",
                    'type': "展覽",
                    'location': "松山文創園區" # V39版後端會自動歸類為 North
                })
                seen_urls.add(full_url)
                current_page_count += 1
                valid_links_found = True

            append_log_run(f"松山文創 第 {page} 頁抓取: {current_page_count} 筆")

            # 如果這頁完全沒抓到有效活動，很可能是因為頁碼超出範圍 (松山官網有時超過頁數會顯示空列表而非404)
            if not valid_links_found:
                break

            page += 1
            await asyncio.sleep(1)

        except Exception as e:
            append_log_run(f"松山文創 第 {page} 頁發生錯誤: {e}")
            break

    return all_events

async def fetch_twtc_events_list(session):
    urls = ["https://www.twtc.com.tw/exhibition?p=home"]
    events = []
    for url in urls:
        try:
            html = await fetch_text(session, url)
            soup = BeautifulSoup(html, "html.parser")
            base_url = "https://www.twtc.com.tw/"

            # [V33 修正] 優化表格抓取策略
            rows = soup.select("tr")
            for row in rows:
                link = row.select_one("a[href*='detail'], a[href*='id=']")
                if not link: continue

                href = link['href']

                # 策略 1: 優先使用連結本身的文字
                raw_title = link.get_text(strip=True)

                # 策略 2: 如果連結文字無效 (如 "more", "詳細"), 才去掃描同列其他欄位
                if not raw_title or raw_title.lower() in ['more', 'top', '詳細內容', '交通資訊']:
                    candidates = []
                    for td in row.find_all('td'):
                        txt = td.get_text(strip=True)
                        # 排除日期、電話、短字串
                        if re.match(r'^[\d/\-\.:\s]+$', txt): continue # 純數字/日期
                        if "886-" in txt or "02-" in txt: continue # 電話
                        if len(txt) < 4: continue
                        candidates.append(txt)

                    # 從候選中選最長的 (通常是標題)
                    if candidates:
                        raw_title = max(candidates, key=len)

                # [關鍵修正] 清理標題
                # 1. 去除結尾的 "more" (不分大小寫)
                title = re.sub(r'more$', '', raw_title, flags=re.IGNORECASE).strip()
                # 2. 去除日期前綴
                title = re.sub(r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}', '', title).strip()

                # 最終過濾
                if not title or "台北世貿" in title or len(title) < 3: continue
                # 過濾誤判為標題的電話號碼 (純數字或長度過短的數字組合)
                if re.search(r'\d{4,}', title) and len(title) < 15: continue

                events.append({
                    'title': title, 'url': urljoin(base_url, href),
                    'platform': "台北世貿", 'type': "展覽/博覽", 'price': '詳內文'
                })
        except Exception: pass

    # 去重
    seen, unique = set(), []
    for e in events:
        if e['url'] not in seen:
            unique.append(e)
            seen.add(e['url'])
    return unique

async def fetch_cksmh_events_list(session):
    # 包含列表頁與當期展覽頁
    urls = [
        "https://www.cksmh.gov.tw/News_Actives_photo.aspx?n=6067&sms=14954",
        "https://www.cksmh.gov.tw/News_Actives_photo.aspx?n=9029&sms=14954",
        "https://www.cksmh.gov.tw/exhibition_photo.aspx?n=6058&sms=14929"
    ]
    events, base_url = [], "https://www.cksmh.gov.tw/"

    # [V33 修正] 擴充黑名單與網址過濾邏輯
    IGNORE_TITLES = [
        "線上展覽", "表演活動", "講座及研討會", "其他活動", "電影欣賞",
        "近3年展覽回顧", "近3年活動回顧", "自辦展覽", "自辦活動", "線上典藏展", "合辦展覽",
        "回首頁", "友善連結", "網站導覽", "English", "常見問答",
        "最新消息", "活動資訊", "交通資訊", "行政透明", "政府資訊公開",
        "活動查詢", "創藝學園", "我要報名", "新春親子活動", "文化藝術及文化創意研習班"
    ]

    for url in urls:
        try:
            html = await fetch_text(session, url)
            soup = BeautifulSoup(html, "html.parser")

            # 鎖定內容區塊 (根據觀察通常在 #main 或 .center_block)
            main_area = soup.select_one("#main, .center_block, .content, .white-background")
            target_soup = main_area if main_area else soup

            links = target_soup.find_all('a', href=True)
            for link in links:
                href = link['href']

                # [關鍵修正] 網址白名單策略
                VALID_KEYWORDS = ["Content.aspx", "Detail", "reg", "openmuseum.tw"]
                is_valid_url = any(k in href for k in VALID_KEYWORDS)

                # [新增] 網址黑名單：排除「無障礙」或「數位發展部」的連結
                # 這能解決抓到 accessibility.moda.gov.tw 的問題
                if "moda.gov.tw" in href or "accessibility" in href:
                    continue

                # 特別排除列表頁 (防止迴圈)
                if "News_Actives_photo" in href or "exhibition_photo" in href:
                    is_valid_url = False

                if not is_valid_url: continue

                title = link.get('title', '').strip() or link.get_text(strip=True)

                # 標題過濾
                if not title or len(title) < 3: continue
                if title in IGNORE_TITLES: continue
                if any(bad in title for bad in ["上一頁", "下一頁", "Go", "更多", "TOP"]): continue

                # [新增] 檢查全域黑名單
                if any(bk in title for bk in BLACKLIST_KEYWORDS): continue

                full_url = urljoin(base_url, href)

                events.append({
                    'title': title, 'url': full_url,
                    'platform': "中正紀念堂",
                    'type': get_event_category_from_title(title),
                    'price': '詳內文'
                })
        except Exception: pass

    seen, unique = set(), []
    for e in events:
        if e['url'] not in seen:
            unique.append(e)
            seen.add(e['url'])
    return unique

async def fetch_kidsclub_events_list(session):
    base_url = "https://kidsclub.com.tw/courses/"
    all_events = []
    seen_urls = set()
    page = 1
    max_pages = 15  # 設定一個安全上限，避免無限迴圈

    # 建立專屬 Header，模擬真實瀏覽器行為
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://kidsclub.com.tw/'
    }

    while page <= max_pages:
        # 組合分頁網址：第1頁與後續頁面網址結構可能不同
        url = base_url if page == 1 else f"{base_url}page/{page}/"

        try:
            async with session.get(url, headers=headers, ssl=True, timeout=15) as resp:
                # 如果遇到 404 代表頁面沒了，正常結束
                if resp.status == 404:
                    append_log_run(f"KidsClub 分頁結束: 第 {page} 頁不存在")
                    break
                if resp.status != 200:
                    append_log_run(f"KidsClub 請求異常 {url}: {resp.status}")
                    break

                html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # 1. 抓取所有產品區塊 (WooCommerce 標準結構)
            # 通常 class 會包含 'product' 和 'type-product'
            products = soup.select("li.product, div.product")

            if not products:
                append_log_run(f"KidsClub 第 {page} 頁無內容，停止抓取")
                break

            current_page_count = 0
            for prod in products:
                # 抓取連結
                link_tag = prod.find("a", href=True)
                if not link_tag: continue
                href = link_tag['href']

                # [關鍵修正] 精準抓取標題
                # 優先抓取 h2.woocommerce-loop-product__title (標準標題)
                # 備用抓取 .product-title 或 h3
                title_tag = prod.select_one(".woocommerce-loop-product__title, .product-title, h2, h3")

                if title_tag:
                    title = title_tag.get_text(strip=True)
                else:
                    # 若真的找不到，才勉強用圖片 alt 或連結文字，但要過濾 "Sale"
                    img = prod.find("img")
                    title = img.get("alt", "").strip() if img else link_tag.get_text(strip=True)

                # 二次清理標題：去除可能殘留的 "Sale" 或 "特價" 字眼
                clean_title = re.sub(r'^(Sale|特價)\s*', '', title, flags=re.IGNORECASE).strip()

                # 過濾無效資料
                if not clean_title or len(clean_title) < 3: continue

                # [新增] 票價精準抓取
                # WooCommerce 列表頁通常會有 .price 結構
                price_text = "詳內文"
                price_tag = prod.select_one(".price")
                if price_tag:
                    # 嘗試抓取特價 (ins) 或一般價格
                    ins_tag = price_tag.select_one("ins .amount")
                    if ins_tag:
                        price_text = ins_tag.get_text(strip=True)
                    else:
                        # 抓取所有價格文字 (例如 "$100 – $200" 或 "$100")
                        amount_tag = price_tag.select_one(".amount")
                        if amount_tag:
                            price_text = price_tag.get_text(strip=True)

                full_url = href
                if not full_url.startswith("http"):
                    full_url = urljoin("https://kidsclub.com.tw", href)

                if full_url in seen_urls: continue

                all_events.append({
                    'title': clean_title,
                    'url': full_url,
                    'platform': "KidsClub",
                    'type': "親子活動",  # KidsClub 專注於親子課程
                    'price': price_text, # 使用列表抓到的正確價格
                    'location': "詳內文"
                })
                seen_urls.add(full_url)
                current_page_count += 1

            append_log_run(f"KidsClub 第 {page} 頁抓取: {current_page_count} 筆")

            # 檢查是否有「下一頁」按鈕，如果沒有就提早結束
            next_btn = soup.select_one(".next.page-numbers, a.next")
            if not next_btn and page > 1:
                break

            page += 1
            await asyncio.sleep(random.uniform(0.5, 1.5)) # 禮貌性延遲

        except Exception as e:
            append_log_run(f"KidsClub 第 {page} 頁發生錯誤: {e}")
            break

    return all_events

async def fetch_culture_express_events_list(session):
    url = "https://cultureexpress.taipei/"
    try:
        html = await fetch_text(session, url)
        soup = BeautifulSoup(html, "html.parser")

        events = []
        seen = set()

        # [V31 修正] 精準抓取活動內容連結
        links = soup.select("a[href*='EventContent']")

        for link in links:
            href = link['href']
            full_url = urljoin(url, href)
            if full_url in seen: continue

            # 嘗試抓標題
            title = link.get('title')
            if not title:
                # 找圖片 alt
                img = link.find('img')
                if img: title = img.get('alt')
            if not title:
                title = link.get_text(strip=True)

            # 過濾
            if not title or len(title) < 2 or "更多" in title or "文化快遞" in title or "活動列表" in title: continue

            events.append({
                'title': title, 'url': full_url,
                'platform': "文化快遞", 'type': get_event_category_from_title(title), 'price': '詳內文'
            })
            seen.add(full_url)

        return events
    except Exception as e:
        append_log_run(f"文化快遞 抓取失敗: {e}")
        return []

async def fetch_cheap_events_list(session):
    # [V30 修復] 二層式抓取 + cp950 編碼解決亂碼
    base_url = "https://www.cheap.com.tw/"
    index_url = "https://www.cheap.com.tw/index.asp"

    # 步驟 1: 抓首頁取得分類
    html = await fetch_text(session, index_url, encoding='cp950')
    if not html: return []

    soup = BeautifulSoup(html, "html.parser")
    # 抓取前 3 個分類連結
    cat_links = [urljoin(base_url, a['href']) for a in soup.select("a[href*='ticket-list.asp']")][:3]

    events = []
    seen = set()

    for cat_url in cat_links:
        try:
            await asyncio.sleep(0.5)
            cat_html = await fetch_text(session, cat_url, encoding='cp950')
            if not cat_html: continue
            cat_soup = BeautifulSoup(cat_html, "html.parser")

            # 尋找產品連結 (優先找 content.asp)
            prod_links = cat_soup.select("a[href*='content.asp']")

            # 如果分類頁沒有直接產品，嘗試找子分類 (product-list.asp)
            if not prod_links:
                sub_cats = cat_soup.select("a[href*='product-list.asp']")
                for sub in sub_cats[:2]: # 只抓前2個子分類避免過久
                     sub_url = urljoin(base_url, sub['href'])
                     sub_html = await fetch_text(session, sub_url, encoding='cp950')
                     if sub_html:
                         sub_soup = BeautifulSoup(sub_html, "html.parser")
                         prod_links.extend(sub_soup.select("a[href*='content.asp']"))

            for link in prod_links:
                href = link.get('href')
                full_url = urljoin(base_url, href)
                if full_url in seen: continue

                title = link.get_text(strip=True) or link.get('title')
                if not title:
                     img = link.find('img')
                     if img: title = img.get('alt')

                if title and len(title) > 3 and "詳細" not in title:
                    events.append({
                        'title': title,
                        'url': full_url,
                        'platform': "便宜旅遊網",
                        'type': "其他",
                        'price': "詳內文"
                    })
                    seen.add(full_url)
        except: pass

    append_log_run(f"便宜旅遊網 抓取: {len(events)} 筆")
    return events

async def fetch_strolltimes_events_list(session):
    # StrollTimes (優化版：忽略解碼錯誤，保持分頁抓取)
    base_url = "https://strolltimes.com/"
    events = []
    seen_urls = set()
    max_pages = 4

    for page in range(1, max_pages + 1):
        url = base_url if page == 1 else f"{base_url}page/{page}/"
        try:
            if page > 1: await asyncio.sleep(1)

            async with session.get(url, ssl=True, timeout=20) as resp:
                if resp.status != 200: break
                # [關鍵修正] 使用 ignore 忽略編碼錯誤，消除紅字警告
                raw_data = await resp.read()
                html = raw_data.decode('utf-8', errors='ignore')

            soup = BeautifulSoup(html, "html.parser")
            links = soup.select("article h2 a")
            if not links: break

            page_new_count = 0
            for link in links:
                href = link.get('href')
                full_url = urljoin(base_url, href)
                if full_url in seen_urls: continue

                title = link.get_text(strip=True)

                location = "詳內文"
                article = link.find_parent("article")
                if article:
                    article_text = article.get_text(strip=True)
                    for city in ["台北", "新北", "桃園", "台中", "台南", "高雄", "宜蘭", "花蓮", "台東"]:
                        if city in article_text: location = city; break

                if not title: continue
                if any(bk in title for bk in BLACKLIST_KEYWORDS): continue

                events.append({
                    'title': title, 'url': full_url, 'platform': "StrollTimes",
                    'type': get_event_category_from_title(title), 'location': location
                })
                seen_urls.add(full_url)
                page_new_count += 1

            if page_new_count == 0: break

        except Exception as e:
            # 只有第一頁失敗才視為嚴重錯誤
            if page == 1: append_log_run(f"StrollTimes 首頁失敗: {e}")
            break

    append_log_run(f"StrollTimes 總計抓取: {len(events)} 筆")
    return events

async def fetch_indievox_events_list(session):
    # iNDIEVOX (增強版：整合一般列表、最新開賣、與全表格模式)
    # 策略：同時抓取三個來源，互補不足，最大化活動數量

    # [新增] 產生今日日期參數 (格式: YYYY%2FMM%2FDD)
    # 用於來源 3，確保抓取從今天開始的活動
    today_param = datetime.now().strftime('%Y%%2F%m%%2F%d')

    sources = [
        # 來源 1: 一般列表 (Card View)
        {"url": "https://www.indievox.com/activity/list", "param": "?page="},
        # 來源 2: 最新開賣 (Table View)
        {"url": "https://www.indievox.com/activity/latest?type=table", "param": "&page="},
        # 來源 3: [新增] 列表表格模式 (帶日期參數) - 這是最完整的清單
        {"url": f"https://www.indievox.com/activity/list?type=table&startDate={today_param}&endDate=", "param": "&page="}
    ]

    events = []
    seen_urls = set()

    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://www.indievox.com/',
    }

    for source in sources:
        base_url = source['url']
        param_str = source['param']
        max_pages = 4 # 每個來源各抓 4 頁，總計可掃描 12 頁

        for page in range(1, max_pages + 1):
            try:
                full_request_url = f"{base_url}{param_str}{page}"

                if page > 1: await asyncio.sleep(random.uniform(1.0, 2.0))

                async with session.get(full_request_url, headers=headers, ssl=True, timeout=15) as resp:
                    if resp.status != 200: break
                    html = await resp.text()

                soup = BeautifulSoup(html, "html.parser")

                # 通用選擇器: 尋找指向詳細頁的連結
                links = soup.select("a[href*='/activity/detail/']")
                if not links: break

                page_new_count = 0
                for link in links:
                    href = link.get('href')
                    full_url = urljoin("https://www.indievox.com", href)
                    if full_url in seen_urls: continue

                    # 標題解析
                    title = link.get('title') or link.get_text(strip=True)
                    if not title:
                         # Card 模式: 嘗試找父層標題
                         card = link.find_parent(class_=lambda x: x and 'card' in x)
                         if card:
                             t_tag = card.select_one('h5, h4, .title')
                             if t_tag: title = t_tag.get_text(strip=True)

                    # 地點解析
                    location = "詳內文"
                    # 1. 嘗試找容器 (Card 或 Table Row)
                    container = link.find_parent(['div', 'tr'], class_=lambda x: x and ('card' in x or 'table' in x))
                    # 2. 如果沒找到特定 class 的容器，就找最近的 tr (針對純表格)
                    if not container:
                        container = link.find_parent('tr')

                    if container:
                        txt = container.get_text(strip=True)
                        # 掃描常見場館或城市
                        if "Legacy" in txt: location = "Legacy Live House"
                        elif "Revolver" in txt: location = "Revolver"
                        elif "Pipe" in txt: location = "Pipe Live Music"
                        else:
                            for city in ["台北", "台中", "高雄", "台東", "宜蘭", "花蓮", "桃園", "新竹"]:
                                if city in txt: location = city; break

                    if not title or len(title) < 2: continue
                    if any(bk in title for bk in BLACKLIST_KEYWORDS): continue

                    events.append({
                        'title': title, 'url': full_url, 'platform': "iNDIEVOX",
                        'type': "音樂會/演唱會", 'location': location
                    })
                    seen_urls.add(full_url)
                    page_new_count += 1

                # 如果這頁沒抓到新資料，可能是分頁到底了
                if page_new_count == 0: break

            except Exception as e:
                append_log_run(f"iNDIEVOX 分頁失敗 ({base_url}): {e}")
                break

    append_log_run(f"iNDIEVOX 總計抓取: {len(events)} 筆")
    return events


# [V30 調整] 以下平台因網站架構高度動態或防火牆阻擋，暫時停用以保持系統穩定
async def fetch_ibon_events_list(session): return []
async def fetch_klook_events_list(session): return []
async def fetch_eztravel_events_list(session): return []
async def fetch_taiwanpass_events_list(session): return []
async def fetch_funcard_events_list(session): return []

# =========================
# Telegram 發送
# =========================
async def send_initial_summary_message(platform_stats, new_count):
    # [V44] Notification is OFF by default, including the initial summary.
    if not ENABLE_TELEGRAM:
        return False
    try:
        # [修改] 標題加入 VERSION 變數
        lines = [f"📊{VERSION} 活動爬取統計（階段一預估）"]
        for platform, count in platform_stats.items(): lines.append(f"{'✅' if count > 0 else '❌'} {platform}: {count} 筆活動")
        lines.extend(["", f"📈 總計: {sum(platform_stats.values())} 筆活動", f"🆕 預估新活動: {new_count} 筆", f"⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "ℹ️ 備註：預估值，最終以處理完成摘要為準"])
        await bot.send_message(chat_id=CHAT_ID, text="\n".join(lines))
        return True
    except Exception as err:
        append_log_run(f"初始統計訊息發送失敗：{err}")
        return False

async def send_final_summary_message(platform_stats, new_count, sent_count, failed_count, details_stats):
    if not ENABLE_TELEGRAM:
        return False
    PLATFORM_URLS = {
        "拓元售票": "https://tixcraft.com",
        "KKTIX": "https://kktix.com",
        "OPENTIX": "https://www.opentix.life",
        "寬宏": "https://kham.com.tw",
        "年代售票": "https://ticket.com.tw",
        "UDN售票網": "https://tickets.udnfunlife.com",
        "TixFun售票網": "https://tixfun.com",
        "Event Go": "https://eventgo.bnextmedia.com.tw",
        "ACCUPASS": "https://www.accupass.com",
        "BeClass": "https://www.beclass.com",
        "FamiTicket": "https://www.famiticket.com.tw",
        # 新增平台連結
        "華山1914": "https://www.huashan1914.com",
        "松山文創": "https://www.songshanculturalpark.org",
        "indievox": "https://www.indievox.com",
        "台北世貿": "https://www.twtc.com.tw",
        "中正紀念堂": "https://www.cksmh.gov.tw",
        "KidsClub": "https://kidsclub.com.tw",
        "文化快遞": "https://cultureexpress.taipei",
        "Klook": "https://www.klook.com",
        "易遊網": "https://activity.eztravel.com.tw",
        "TaiwanPass": "https://www.funcard.tw",
        "便宜旅遊網": "https://www.cheap.com.tw",
        "StrollTimes": "https://strolltimes.com",
        "ibon售票": "https://ticket.ibon.com.tw"
    }

    try:
        # MarkdownV2 特殊字元跳脫 helper
        def esc(text):
            return escape_markdown_v2(str(text))
        # [修改] 標題加入 VERSION 變數
        lines = [f"📋{VERSION} *活動處理完成摘要*", "", "📊 *列表階段:*"]

        for platform, count in platform_stats.items():
            status = '✅' if count > 0 else '❌'
            url = PLATFORM_URLS.get(platform, "")
            # 注意：列表符號 - 必須跳脫為 \-
            # 平台連結本身不需跳脫，但標籤外的符號需要
            platform_str = f"[{platform}]({url})" if url else platform
            lines.append(f" \\- {platform_str}: {esc(count)} 筆 {status}")

        # [修改] 標題加入 VERSION 變數
        lines.append(f"\n📈{VERSION} *詳頁處理統計:*")
        for p, st in details_stats.items():
            if st.get('candidates', 0) > 0:
                lines.append(f" \\- {p}: 候選 {esc(st.get('candidates',0))} / 成功 {esc(st.get('success',0))}")

        lines.extend([
            "",
            f"🆕 新活動: `{esc(new_count)}` 筆",
            f"✅ 發送成功: `{esc(sent_count)}` 筆",
            f"❌ 發送失敗: `{esc(failed_count)}` 筆"
        ])

        if (sent_count + failed_count) > 0:
            rate = (sent_count / (sent_count + failed_count)) * 100
            lines.append(f"📊 成功率: `{esc(f'{rate:.1f}')}%`")

        # 關注活動列表
        if favorites_found_current_run:
            lines.append("\n🌟 *本輪關注活動:*")
            for fav in favorites_found_current_run:
                raw_title = fav['title'][:25] + "..." if len(fav['title']) > 25 else fav['title']
                # 標題必須跳脫
                title_short = esc(raw_title)
                fav_url = fav.get('url', '')
                lines.append(f"• [{title_short}]({fav_url})")

        lines.extend([
            "",
            f"⏰ 完成時間: {esc(datetime.now().strftime('%H:%M:%S'))}",
            "🔄 下次檢查: 依排程"
        ])

        await bot.send_message(chat_id=CHAT_ID, text="\n".join(lines), parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
        return True
    except Exception as err:
        append_log_run(f"最終統計訊息發送失敗：{err}")
        return False

def escape_markdown_v2(text: str) -> str:
    if not isinstance(text, str): text = str(text)
    escape_chars = r'_*[]()~`>#+=|{}.!-'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def send_telegram_message_with_retry(event, is_init=False, downgraded=False, max_retries=1):
    if not ENABLE_TELEGRAM:
        return False, 'TELEGRAM_DISABLED'
    title_raw = event.get('title', '')
    is_fav = check_is_favorite(title_raw)
    if is_fav:
        favorites_found_current_run.append(event)
        if not is_init:
            send_termux_notification("🔥 發現關注活動", title_raw)

    for attempt in range(max_retries):
        try:
            # [修改] 標題加入 VERSION 變數
            header = f"🔄{VERSION} 首輪測試活動" if is_init else "🆕 新增活動通知"
            if is_fav: header = f"🔥 {header}"

            # 預先處理各欄位，確保內容安全轉義
            def get_esc(key): return escape_markdown_v2(event.get(key, '詳內文'))

            title = get_esc('title')
            event_type = get_esc('type')
            event_date = get_esc('date')
            event_location = get_esc('location')
            event_platform = get_esc('platform')
            event_price = get_esc('price')
            event_ticket_date = get_esc('ticket_date')
            event_desc = get_esc('description')

            # 【關鍵修正】網址本身不需要轉義，否則 Telegram 會無法點擊
            raw_url = event.get('url', '')

            # 組合基礎訊息
            lines = [
                header,
                f"🎫 *{title}*",
                f"📍 類型：{event_type}",
                f"📅 日期：{event_date}",
                f"🗺 地點：{event_location}"
            ]

            if event.get('ticket_date') and event.get('ticket_date') != '詳內文':
                lines.append(f"🗓️ 開賣：{event_ticket_date}")
            if event.get('price') and event.get('price') != '詳內文':
                lines.append(f"💰 票價：{event_price}")

            lines.append(f"🧾 平台：{event_platform}")

            # 只有在非降級且有描述時才加入簡短描述
            if not downgraded and event.get('description'):
                lines.append(f"\n📝 簡介：{event_desc}")

            if downgraded:
                lines.append("\n⚠️ 詳頁資訊受限，請點擊連結查看")

            # 組合最後的連結行
            # 這裡使用 raw_url 確保網址正確
            lines.append(f"\n📌 [點我查看詳情]({raw_url})")

            full_msg = "\n".join(lines)

            # --- 長度限制處理 ---
            img_url = event.get('img_url')

            if img_url:
                # 圖片說明限制 1024 字元
                if len(full_msg) > 1000:
                    # 截斷時保留 header 和 title，移除描述
                    short_lines = lines[:lines.index(f"🧾 平台：{event_platform}")+1]
                    short_lines.append(f"\n📌 [點我查看詳情]({raw_url})")
                    truncated_msg = "\n".join(short_lines)
                else:
                    truncated_msg = full_msg

                try:
                    await bot.send_photo(chat_id=CHAT_ID, photo=img_url, caption=truncated_msg, parse_mode=ParseMode.MARKDOWN_V2)
                    return True, None
                except Exception as e:
                    append_log_run(f"圖片發送失敗，嘗試純文字降級: {str(e)}")

            # 純文字消息限制 4096 字元
            if len(full_msg) > 4000:
                full_msg = full_msg[:3950] + f"\n\\.\\.\\.\n📌 [點我查看詳情]({raw_url})"

            await bot.send_message(chat_id=CHAT_ID, text=full_msg, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=False)
            return True, None

        except Exception as err:
            error_msg = str(err)
            append_log_run(f"發送失敗 (第{attempt+1}次)：{event.get('title','(無標題)')} => {error_msg}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            return False, error_msg

# =========================
# 主要流程
# =========================
async def stage1_fetch_lists(limit_per_platform=None, target_platform=None):
    connector = aiohttp.TCPConnector(ssl=True, limit=10, family=0)
    async with aiohttp.ClientSession(connector=connector) as aio_sess:
        # 定義所有爬蟲任務 (函式, 平台名稱)
        crawlers = [
            (fetch_kktix_events_list, "KKTIX"),
            (fetch_tixcraft_events_list, "拓元售票"),
            (fetch_opentix_events_list, "OPENTIX"),
            (fetch_kham_events_list, "寬宏"),
            (fetch_era_events_list, "年代售票"),
            (fetch_udn_events_list, "UDN售票網"),
            (fetch_tixfun_events_list, "TixFun售票網"),
            (fetch_eventgo_events_list, "Event Go"),
            (fetch_accupass_events_list, "ACCUPASS"),
            (fetch_beclass_events_list, "BeClass"),
            (fetch_famiticket_events_list, "FamiTicket"),
            (fetch_huashan_events_list, "華山1914"),
            (fetch_songshan_events_list, "松山文創"),
            (fetch_twtc_events_list, "台北世貿"),
            (fetch_cksmh_events_list, "中正紀念堂"),
            (fetch_kidsclub_events_list, "KidsClub"),
            (fetch_culture_express_events_list, "文化快遞"),
            (fetch_indievox_events_list, "iNDIEVOX"),
            (fetch_klook_events_list, "Klook"),
            (fetch_eztravel_events_list, "易遊網"),
            (fetch_cheap_events_list, "便宜旅遊網"),
            (fetch_strolltimes_events_list, "StrollTimes"),
            (fetch_ibon_events_list, "ibon售票"),
            (fetch_taiwanpass_events_list, "TaiwanPass")
        ]

        tasks = []
        platforms = []

        # 動態建立任務列表
        for func, name in crawlers:
            # 如果有指定平台，且名稱不符，則跳過
            if target_platform and target_platform not in name:
                continue
            tasks.append(func(aio_sess))
            platforms.append(name)

        if not tasks:
            append_log_run(f"⚠️ 找不到符合 '{target_platform}' 的平台爬蟲")
            return [], {}

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_events, platform_stats = [], {}

        for idx, res in enumerate(results):
            if idx >= len(platforms): break

            name = platforms[idx]
            if isinstance(res, Exception):
                append_log_run(f"{name} 列表擷取發生錯誤: {res}")
                platform_stats[name] = 0
            else:
                events = res or []
                if limit_per_platform: events = events[:limit_per_platform]
                platform_stats[name] = len(events)
                all_events.extend(events)

    return [e for e in all_events if e.get('title') and e.get('url')], platform_stats

# V44.1: Queue selection is independent of notification history.
# When a detail request fails, remember its attempt time so older untried events
# are processed on the next scheduled run instead of starving indefinitely.
def plan_detail_updates(all_list_events, saved, new_budget, repair_budget,
                        force_update=False, first_mode=False):
    def needs_repair(prior):
        return any(not prior.get(k) or prior.get(k) == '詳內文'
                   for k in ('date', 'location', 'price', 'description'))

    fresh = [e for e in all_list_events if e.get('url') not in saved]
    if first_mode:
        fresh = fresh[:10]
    repairs = [e for e in all_list_events
               if e.get('url') in saved and needs_repair(saved[e['url']])]
    # Empty attempt timestamp comes first; old unsuccessful attempts rotate to
    # the back without losing the entry or overwriting any known-good fields.
    repairs.sort(key=lambda e: (str(saved[e['url']].get('detail_checked_at') or ''),
                                e['url']))
    chosen = (all_list_events[:new_budget] if force_update else fresh[:new_budget])
    if not force_update:
        chosen += repairs[:repair_budget]
    return list({e['url']: e for e in chosen}.values()), len(fresh), len(repairs)


async def stage2_fetch_details_and_notify(all_list_events, first_run=False, first_mode=False, force_update=False, suppress_notify=False):
    """[V44] Bounded detail requests, saved-data novelty, opt-in notifications only.

    GitHub Actions gets a fresh checkout on every run, so its untracked notification
    log is not authoritative for determining whether an activity has been seen.
    The committed docs/data.json is the stable seen-URL reference.
    """
    log_data = load_log()
    try:
        db_rows = json.loads(Path('docs/data.json').read_text(encoding='utf-8'))
        if not isinstance(db_rows, list):
            raise ValueError('unexpected data format')
        saved = {e.get('url'): e for e in db_rows if isinstance(e, dict) and e.get('url')}
    except FileNotFoundError:
        saved = {}
    except (OSError, ValueError, TypeError) as exc:
        append_log_run('HOLD DETAIL: cannot inspect saved data ('+type(exc).__name__+')')
        raise

    # V44.1: FIFO-with-retry rotation across scheduled runs.
    new_budget = max(0, min(80, int(os.environ.get('DETAIL_NEW_LIMIT', '24'))))
    repair_budget = max(0, min(80, int(os.environ.get('DETAIL_REPAIR_LIMIT', '16'))))
    events_to_process, fresh_count, repair_count = plan_detail_updates(
        all_list_events, saved, new_budget, repair_budget, force_update, first_mode)
    from collections import defaultdict
    grouped = defaultdict(list)
    for e in events_to_process:
        grouped[e['platform']].append(e)
    details_stats = {p: {'candidates': len(rows), 'success': 0, 'failed': 0} for p, rows in grouped.items()}
    loop = asyncio.get_running_loop()
    sent_count, failed_count = 0, 0
    for platform, events in grouped.items():
        for event in events:
            try:
                details = await loop.run_in_executor(
                    None, extract_event_details_simple, event['url'], platform, 1, event)
                useful = 0
                for key, value in (details or {}).items():
                    if value and str(value).strip() not in ('詳內文', 'None', '詳細資訊請點擊連結查看。'):
                        if key in ('date', 'location', 'price', 'description', 'ticket_date'):
                            useful += 1
                        event[key] = value
                event['region'] = get_event_region(event.get('platform'), event.get('location'), event.get('title'))
                if useful:
                    details_stats[platform]['success'] += 1
                else:
                    details_stats[platform]['failed'] += 1
            except Exception as err:
                details_stats[platform]['failed'] += 1
                append_log_run('DETAIL_FAIL platform='+platform+' reason='+type(err).__name__)
            finally:
                # Persist on the corresponding event even after an HTTP/parser failure.
                # Next run gives priority to older or untried repair candidates.
                event['detail_checked_at'] = datetime.now().astimezone().isoformat()

            # [V44] Termux may be enabled alone, independently of Telegram.
            if (ENABLE_TERMUX and not ENABLE_TELEGRAM and not suppress_notify
                    and event['url'] not in saved and check_is_favorite(event.get('title', ''))):
                send_termux_notification('🔥 發現關注活動', event.get('title', ''))

            # [V44] Previously seen URLs must not generate a new message.
            # When Telegram is OFF we do not access bot, Token or Chat ID.
            if suppress_notify or not ENABLE_TELEGRAM or event['url'] in log_data or event['url'] in saved:
                continue
            ok, error = await send_telegram_message_with_retry(event, is_init=first_run or first_mode)
            if ok:
                sent_count += 1
                log_data[event['url']] = {'title': event.get('title', '無標題')}
            else:
                failed_count += 1
                record_failed_message(event, error)
            await asyncio.sleep(random.uniform(1.0, 2.0))
    if ENABLE_TELEGRAM:
        save_log(log_data)
    append_log_run(f"DETAIL_SUMMARY selected={len(events_to_process)} fresh={fresh_count} repair_candidates={repair_count} sent={sent_count} failed={failed_count}")
    return fresh_count, sent_count, failed_count, details_stats

async def check_and_notify(first_run=False, first_mode=False, target_platform=None):
    global favorites_found_current_run
    favorites_found_current_run = []

    log_msg = f"{VERSION} 開始執行活動檢查"
    if target_platform: log_msg += f" (單一平台模式: {target_platform})"
    append_log_run(log_msg)

    if ENABLE_TELEGRAM and not first_run and not target_platform: clean_failed_messages()
    if ENABLE_TELEGRAM and first_run: clear_log()

    limit = 10 if first_mode else None

    # Stage 1
    all_list_events, platform_stats = await stage1_fetch_lists(limit_per_platform=limit, target_platform=target_platform)

    seen_urls = set()
    filtered_events = [e for e in all_list_events if e.get('url') not in seen_urls and not seen_urls.add(e.get('url'))]
    try:
        existing_rows = json.loads(Path('docs/data.json').read_text(encoding='utf-8'))
        existing_urls = {row.get('url') for row in existing_rows if isinstance(row, dict)}
    except FileNotFoundError:
        existing_urls = set()
    prelim_new_count = sum(1 for e in filtered_events if e['url'] not in existing_urls)

    # [修正] 只有在非單一平台模式下，才發送初始統計
    if not target_platform:
        await send_initial_summary_message(platform_stats, prelim_new_count)
    else:
        append_log_run(f"單一平台模式：跳過初始統計發送 (預計新增 {prelim_new_count} 筆)")

    is_force = True if target_platform else False
    is_suppress = True if target_platform else False

    # Stage 2
    new_count, sent_count, failed_count, details_stats = await stage2_fetch_details_and_notify(
        filtered_events,
        first_run=first_run,
        first_mode=first_mode,
        force_update=is_force,
        suppress_notify=is_suppress
    )

    # [修正] 只有在非單一平台模式下，才發送最終統計
    if not target_platform:
        await send_final_summary_message(platform_stats, new_count, sent_count, failed_count, details_stats)

    append_log_run(f"處理完成：新活動 {new_count}，成功發送 {sent_count}，失敗 {failed_count}")

    # 儲存資料庫
    if all_list_events and target_platform:
        append_log_run('PASS PREVIEW: single-source run does not publish to protect multi-platform data')
    elif all_list_events:
        saved_path = save_data_to_docs(all_list_events)
        if saved_path:
            if PUBLISH_VIA_ACTIONS:
                append_log_run('PASS ACTIONS_WRITER: generated data; GitHub workflow owns publication')
            else:
                upload_docs_to_github()
    else:
        append_log_run('HOLD DATA: zero events; no Git publication')

async def run_schedule():
    while True:
        schedule.run_pending()
        await asyncio.sleep(10)

def run_daemon():
    append_log_run("啟動背景監控模式")
    schedule.every().day.at("09:00").do(lambda: asyncio.create_task(check_and_notify()))
    schedule.every().day.at("15:00").do(lambda: asyncio.create_task(check_and_notify()))
    schedule.every().day.at("21:00").do(lambda: asyncio.create_task(check_and_notify()))
    append_log_run("已設定每日 09:00,15:00, 21:00 自動檢查")

async def main():
    global bot
    # [V44] Optional Telegram credentials must not block data collection.
    if ENABLE_TELEGRAM:
        if not TOKEN or TOKEN == 'REPLACE_ME' or not CHAT_ID or CHAT_ID == 'REPLACE_ME':
            raise RuntimeError('TELEGRAM_ENABLED_BUT_SECRETS_MISSING')
        bot = telegram.Bot(token=TOKEN)
    parser = argparse.ArgumentParser(description='活動爬蟲程式')
    parser.add_argument('--init', action='store_true', help='初始化模式')
    parser.add_argument('--first', action='store_true', help='快速首輪模式')
    parser.add_argument('--test', action='store_true', help='正常測試模式')
    parser.add_argument('--once', action='store_true', help='一次執行（GitHub Actions 建議）')
    parser.add_argument('--daemon', action='store_true', help='背景模式')
    parser.add_argument('--clean-failed', action='store_true', help='清理持續失敗的訊息記錄')
    # [新增] 平台指定參數
    parser.add_argument('--platform', type=str, help='指定單一平台強制更新詳情 (例如: "年代", "寬宏")')

    args = parser.parse_args()

    # [新增] 優先處理單一平台模式
    if args.platform:
        # 單一平台更新：不視為 first_run，但開啟 target_platform 參數會自動觸發靜音更新
        await check_and_notify(first_run=False, first_mode=False, target_platform=args.platform)
        return

    action_map = {
        'clean_failed': (clean_failed_messages, "清理持續失敗的訊息記錄"),
        'init': (lambda: check_and_notify(first_run=True, first_mode=False), "執行初始化模式"),
        'first': (lambda: check_and_notify(first_run=False, first_mode=True), "執行快速首輪模式"),
        'test': (lambda: check_and_notify(first_run=False, first_mode=False), "執行正常測試模式"),
        'once': (lambda: check_and_notify(first_run=False, first_mode=False), "雲端單次執行"),
        'daemon': (run_daemon, "執行背景模式")
    }
    executed = False
    for arg, (func, msg) in action_map.items():
        if getattr(args, arg):
            append_log_run(msg)
            if arg == 'daemon':
                func()
                await run_schedule()
            elif asyncio.iscoroutinefunction(func): await func()
            else:
                result = func()
                if asyncio.iscoroutine(result): await result
            executed = True
            break
    if not executed: parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
