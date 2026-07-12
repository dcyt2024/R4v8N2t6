import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone, date
import calendar
from icalendar import Calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 1872*1404 排版設定 ====================
ICAL_URL = "https://calendar.google.com/calendar/u/4/r/settings/calendar/ZGN5dDEyMjAyNEBnbWFpbC5jb20"

SCREEN_WIDTH = 1872
SCREEN_HEIGHT = 1404
GRID_ROWS = 5
GRID_COLS = 7

# 參考 HTML 的 Topbar 與格子比例等比放大
TOP_MARGIN = 140   
CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOP_MARGIN) // GRID_ROWS

LOCAL_TZ = timezone(timedelta(hours=8)) 

# ==================== 2. 下載與解析 Google 日曆 ====================
print("Fetching data from Google Calendar...")
gcal = None
try:
    req = urllib.request.Request(ICAL_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        gcal = Calendar.from_ical(response.read())
except Exception as e:
    print(f"⚠️無法取得日曆資料: {e}")
    gcal = None

calendar_events = {}
today = datetime.now(LOCAL_TZ).date()
start_of_month = datetime(today.year, today.month, 1).date()
end_of_month = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1]).date()

if gcal is not None:
    for component in gcal.walk():
        if component.name == "VEVENT":
            summary = str(component.get('summary', 'No Title'))
            dtstart = component.get('dtstart').dt if component.get('dtstart') else None
            dtend = component.get('dtend').dt if component.get('dtend') else None
            
            if not dtstart:
                continue
                
            time_str = "" 
            if isinstance(dtstart, datetime):
                local_start = dtstart.astimezone(LOCAL_TZ)
                event_date = local_start.date()
                start_time = local_start.strftime("%H:%M")
                
                if isinstance(dtend, datetime):
                    local_end = dtend.astimezone(LOCAL_TZ)
                    end_time = local_end.strftime("%H:%M")
                    time_str = f"{start_time}-{end_time} "
                else:
                    time_str = f"{start_time} "
            elif isinstance(dtstart, date):
                event_date = dtstart
                time_str = "" 
            
            if start_of_month <= event_date <= end_of_month:
                date_str = event_date.strftime("%Y-%m-%d")
                if date_str not in calendar_events:
                    calendar_events[date_str] = []
                calendar_events[date_str].append((time_str, summary))

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

# 🌟 對照 HTML 比例做 1872 解析度下的最完美縮放：
font_title = ImageFont.truetype(font_path, 80) if font_path else ImageFont.load_default() # 放大版 .title (32px)
font_week = ImageFont.truetype(font_path, 48) if font_path else ImageFont.load_default()  # 放大版 .dow (20px)
font_date = ImageFont.truetype(font_path, 52) if font_path else ImageFont.load_default()  # 放大版 .date (22px)
font_event = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default() # 放大版 .event (18px)

# ==================== 4. 繪製頂部介面 ====================
now = datetime.now(LOCAL_TZ)
current_year = now.year
current_month = now.month

month_name = calendar.month_name[current_month].upper()
title_text = f"{month_name} {current_year}"
title_w = draw.textlength(title_text, font=font_title)
title_x = (SCREEN_WIDTH - title_w) // 2
draw.text((title_x, 25), title_text, fill=0, font=font_title) 

# 頂部橫線
draw.line([(0, TOP_MARGIN), (SCREEN_WIDTH, TOP_MARGIN)], fill=0, width=4)

# ==================== 5. 繪製日曆格子與行程 ====================
first_weekday, num_days = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7 
start_of_calendar = datetime(current_year, current_month, 1, tzinfo=LOCAL_TZ) - timedelta(days=start_col)

# 星期欄位高度（56px 等比放大）
DOW_HEIGHT = 60
for i, day_name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    draw.text((x, TOP_MARGIN + (DOW_HEIGHT - 48) // 2), day_name, fill=0, font=font_week)

# 真正的格子起點要扣掉星期欄位
REAL_TOP = TOP_MARGIN + DOW_HEIGHT
REAL_CELL_HEIGHT = (SCREEN_HEIGHT - REAL_TOP) // GRID_ROWS

for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        days_to_add = row * GRID_COLS + col
        cell_date = (start_of_calendar + timedelta(days=days_to_add)).date()
        cell_date_str = cell_date.strftime("%Y-%m-%d")
        
        x1 = col * CELL_WIDTH
        y1 = REAL_TOP + (row * REAL_CELL_HEIGHT)
        x2 = x1 + CELL_WIDTH
        y2 = y1 + REAL_CELL_HEIGHT
        
        # 畫日曆外框
        draw.rectangle([(x1, y1), (x2, y2)], outline=0, width=2)
        
        if cell_date.month != current_month:
            continue
            
        # 繪製置中日期數字 (.date)
        date_text = str(cell_date.day)
        text_w = draw.textlength(date_text, font=font_date)
        date_x = x1 + (CELL_WIDTH - text_w) // 2
        draw.text((date_x, y1 + 15), date_text, fill=0, font=font_date)
        
        # 當天加一個小底圈 (等同於今天的 .date-badge)
        if cell_date == today:
            draw.arc([date_x - 10, y1 + 10, date_x + text_w + 10, y1 + 65], 0, 360, fill=0, width=3)
        
        # 繪製行程 (.events)
        if cell_date_str in calendar_events:
            sorted_events = sorted(calendar_events[cell_date_str], key=lambda x: x[0] if x[0] else "24:00")
            
            y_offset = y1 + 80   # 保留上方給日期數字
            box_height = 56     # 行程外框盒子的高度
            gap = 10            # 盒子之間的間距
            
            for index, (time_prefix, event_title) in enumerate(sorted_events):
                # 確保格子裝得下，裝不下才不顯示
                if y_offset + box_height > y2 - 10:
                    break
                
                # 🌟 模擬 HTML 的 .event 邊框盒
                # 畫出行程背景的小邊框
                draw.rectangle([(x1 + 12, y_offset), (x2 - 12, y_offset + box_height)], outline=0, width=1)
                
                # 準備文字
                display_text = f"{time_prefix}{event_title}"
                max_text_width = CELL_WIDTH - 48 # 扣掉左右邊距
                
                # 自動截斷超長文字
                if draw.textlength(display_text, font=font_event) > max_text_width:
                    while draw.textlength(display_text + "..", font=font_event) > max_text_width and len(display_text) > 0:
                        display_text = display_text[:-1]
                    display_text += ".."
                
                # 填入文字到盒子內 (靠左微調垂直置中)
                draw.text((x1 + 24, y_offset + (box_height - 42) // 2), display_text, fill=0, font=font_event)
                
                y_offset += box_height + gap

# 儲存
image.save("calendar.png")
print("🎉 HTML-Balanced Calendar Generated!")
