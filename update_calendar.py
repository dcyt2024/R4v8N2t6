import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone, date
import calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 1872*1404 排版設定 ====================
SCREEN_WIDTH = 1872
SCREEN_HEIGHT = 1404
GRID_ROWS = 5
GRID_COLS = 7

# 大幅拉高頂部安全區（從 140 提高到 220），保證 July 2026 與星期絕對不會被格子遮擋！
TOP_MARGIN = 220   
CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOP_MARGIN) // GRID_ROWS

LOCAL_TZ = timezone(timedelta(hours=8)) 

# ==================== 2. 100% 同步 HTML 的 Google API 讀取邏輯 ====================
# 自動帶入你在 HTML 裡設定的憑證與時區
CALENDAR_ID = 'dcyt122024@gmail.com'
API_KEY = 'AIzaSyAYBpOB6UoMYeAAmwTM_1KdYEzwtv6zXiE'

# 設定 2026 年 7 月的範圍
timeMin = "2026-07-01T00:00:00Z"
timeMax = "2026-08-01T00:00:00Z"

calendar_events = {}

print("Connecting to Google Calendar API...")
try:
    url = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(CALENDAR_ID)}/events"
    params = {
        'key': API_KEY,
        'timeMin': timeMin,
        'timeMax': timeMax,
        'singleEvents': 'true',
        'orderBy': 'startTime',
        'maxResults': '250'
    }
    url_parts = list(urllib.parse.urlparse(url))
    url_parts[4] = urllib.parse.urlencode(params)
    final_url = urllib.parse.urlunparse(url_parts)
    
    req = urllib.request.Request(final_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        
        for ev in data.get('items', []):
            start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date')
            end = ev.get('end', {}).get('dateTime') or ev.get('end', {}).get('date')
            summary = ev.get('summary', '(No title)')
            
            if not start:
                continue
                
            day_key = start[:10] # 取得 YYYY-MM-DD
            
            # 計算時間字串 (例如 "14:00-14:30")
            time_str = ""
            if 'dateTime' in ev.get('start', {}):
                # 解析並轉為本地時間
                dt_start = datetime.strptime(start[:19], "%Y-%m-%dT%H:%M:%S")
                t1 = dt_start.strftime("%H:%M")
                if 'dateTime' in ev.get('end', {}):
                    dt_end = datetime.strptime(end[:19], "%Y-%m-%dT%H:%M:%S")
                    t2 = dt_end.strftime("%H:%M")
                    time_str = f"{t1}-{t2} "
                else:
                    time_str = f"{t1} "
            else:
                time_str = "All day "
                
            if day_key not in calendar_events:
                calendar_events[day_key] = []
            calendar_events[day_key].append((time_str, summary))
            
    print(f"🎉 成功讀取到行程資料！總共 {len(calendar_events)} 天有活動。")
except Exception as e:
    print(f"⚠️ Google API 讀取失敗: {e}")

# ==================== 3. 初始化畫布與字型 ====================
image = Image.new("1", (SCREEN_WIDTH, SCREEN_HEIGHT), 1)
draw = ImageDraw.Draw(image)

font_url = "https://github.com/hanyuan-font/msjh/raw/master/msjh.ttf"
font_path = "msjh.ttf"

if not os.path.exists(font_path):
    print("Downloading font...")
    try:
        urllib.request.urlretrieve(font_url, font_path)
    except:
        font_path = None

# 精準等比放大：大字體、極佳的可讀性
font_title = ImageFont.truetype(font_path, 85) if font_path else ImageFont.load_default() 
font_week = ImageFont.truetype(font_path, 46) if font_path else ImageFont.load_default()  
font_date = ImageFont.truetype(font_path, 54) if font_path else ImageFont.load_default()  
font_event = ImageFont.truetype(font_path, 38) if font_path else ImageFont.load_default() 

# ==================== 4. 繪製頂部介面 ====================
# 固定繪製 2026 年 7 月 (與你的 HTML 同步)
current_year = 2026
current_month = 7

title_text = "July 2026"
title_w = draw.textlength(title_text, font=font_title)
title_x = (SCREEN_WIDTH - title_w) // 2
draw.text((title_x, 25), title_text, fill=0, font=font_title) # 置中大標題

# 頂部基礎橫線
draw.line([(0, TOP_MARGIN), (SCREEN_WIDTH, TOP_MARGIN)], fill=0, width=4)

# ==================== 5. 繪製日曆格子與行程 ====================
# 固定計算 2026 7 月的日曆排版
first_weekday, num_days = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7 
# 日曆格子第一格的日期 (2026-06-28)
start_of_calendar = datetime(current_year, current_month, 1, tzinfo=LOCAL_TZ) - timedelta(days=start_col)

# 繪製星期欄位 (Sun - Sat)
DOW_HEIGHT = 70
for i, day_name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    draw.text((x, TOP_MARGIN + (DOW_HEIGHT - 46) // 2), day_name, fill=0, font=font_week)

REAL_TOP = TOP_MARGIN + DOW_HEIGHT
REAL_CELL_HEIGHT = (SCREEN_HEIGHT - REAL_TOP) // GRID_ROWS

# 今天日期（用於畫 badge 圈圈）
today_str = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")

for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        days_to_add = row * GRID_COLS + col
        cell_date = (start_of_calendar + timedelta(days=days_to_add)).date()
        cell_date_str = cell_date.strftime("%Y-%m-%d")
        
        x1 = col * CELL_WIDTH
        y1 = REAL_TOP + (row * REAL_CELL_HEIGHT)
        x2 = x1 + CELL_WIDTH
        y2 = y1 + REAL_CELL_HEIGHT
        
        # 繪製外框線
        draw.rectangle([(x1, y1), (x2, y2)], outline=0, width=2)
        
        # 繪製置中日期數字
        date_text = str(cell_date.day)
        text_w = draw.textlength(date_text, font=font_date)
        date_x = x1 + (CELL_WIDTH - text_w) // 2
        
        # 如果不是本月的日子，字體一樣顯示 (如同 HTML 的 .other)
        draw.text((date_x, y1 + 15), date_text, fill=0, font=font_date)
        
        # 如果是今天，畫一個精美的圓圈外框
        if cell_date_str == today_str:
            draw.arc([date_x - 15, y1 + 10, date_x + text_w + 15, y1 + 70], 0, 360, fill=0, width=4)
        
        # 繪製行程資料
        if cell_date_str in calendar_events:
            events_in_day = calendar_events[cell_date_str]
            
            y_offset = y1 + 85   
            box_height = 58     
            gap = 8            
            
            for index, (time_prefix, event_title) in enumerate(events_in_day):
                if y_offset + box_height > y2 - 10:
                    break
                
                # 繪製行程卡片外框
                draw.rectangle([(x1 + 10, y_offset), (x2 - 10, y_offset + box_height)], outline=0, width=1)
                
                display_text = f"{time_prefix}{event_title}"
                max_text_width = CELL_WIDTH - 40
                
                if draw.textlength(display_text, font=font_event) > max_text_width:
                    while draw.textlength(display_text + "..", font=font_event) > max_text_width and len(display_text) > 0:
                        display_text = display_text[:-1]
                    display_text += ".."
                
                # 置中文字填入
                draw.text((x1 + 20, y_offset + (box_height - 38) // 2), display_text, fill=0, font=font_event)
                y_offset += box_height + gap

# 儲存
image.save("calendar.png")
print("🎉 API-Linked Perfect Calendar Generated!")
