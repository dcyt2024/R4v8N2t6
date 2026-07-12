import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone, date
import calendar
from icalendar import Calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 1872*1404 排版設定 ====================
# ⚠️ 請確保這是你 Google 日曆的「不公開網址 (iCal 格式)」
ICAL_URL = "https://calendar.google.com/calendar/u/4/r/settings/calendar/ZGN5dDEyMjAyNEBnbWFpbC5jb20"

SCREEN_WIDTH = 1872
SCREEN_HEIGHT = 1404
GRID_ROWS = 5
GRID_COLS = 7

# 🌟 頂部高度維持緊湊，釋放 1284 像素的高度給 5 排格子（每排格子高達 256 像素！）
TOP_MARGIN = 120   
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
    print(f"⚠️【網址錯誤警告】無法取得日曆資料: {e}")
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

# ==================== 3. 初始化畫布與下載字型 ====================
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

# 🌟 終極放大版字體設定
font_title = ImageFont.truetype(font_path, 130) if font_path else ImageFont.load_default() # 64 -> 130 (巨字)
font_week = ImageFont.truetype(font_path, 50) if font_path else ImageFont.load_default()   # 32 -> 50
font_date = ImageFont.truetype(font_path, 70) if font_path else ImageFont.load_default()   # 54 -> 70 (清晰大數字)
font_event = ImageFont.truetype(font_path, 55) if font_path else ImageFont.load_default()  # 46 -> 55 (行程超清晰)

# ==================== 4. 繪製頂部介面（滿版排版） ====================
now = datetime.now(LOCAL_TZ)
current_year = now.year
current_month = now.month

# 將月份與年份分開排版，或者直接並排，我們這裡稍微往左與往右微調讓空間最有效利用
month_name = calendar.month_name[current_month].upper()
title_text = f"{month_name} {current_year}"
title_w = draw.textlength(title_text, font=font_title)
title_x = (SCREEN_WIDTH - title_w) // 2
# 稍微重疊上一點點沒關係，把 y 設在 -25 讓超大字能塞進 120 像素內
draw.text((title_x, -25), title_text, fill=0, font=font_title) 

weekdays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
for i, day_name in enumerate(weekdays):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    draw.text((x, 70), day_name, fill=0, font=font_week) 

draw.line([(0, TOP_MARGIN), (SCREEN_WIDTH, TOP_MARGIN)], fill=0, width=5)

# ==================== 5. 繪製日曆格子與行程 ====================
first_weekday, num_days = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7 
start_of_calendar = datetime(current_year, current_month, 1, tzinfo=LOCAL_TZ) - timedelta(days=start_col)

MAX_TEXT_WIDTH = CELL_WIDTH - 30

for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        days_to_add = row * GRID_COLS + col
        cell_date = (start_of_calendar + timedelta(days=days_to_add)).date()
        cell_date_str = cell_date.strftime("%Y-%m-%d")
        
        x1 = col * CELL_WIDTH
        y1 = TOP_MARGIN + (row * CELL_HEIGHT)
        x2 = x1 + CELL_WIDTH
        y2 = y1 + CELL_HEIGHT
        
        draw.rectangle([(x1, y1), (x2, y2)], outline=0, width=1)
        
        if cell_date.month != current_month:
            continue
            
        # 繪製日期大數字
        date_text = str(cell_date.day)
        text_w = draw.textlength(date_text, font=font_date)
        draw.text((x2 - text_w - 20, y1 + 10), date_text, fill=0, font=font_date)
        
        if cell_date_str in calendar_events:
            sorted_events = sorted(calendar_events[cell_date_str], key=lambda x: x[0] if x[0] else "24:00")
            
            # 配合大字體，下移初始行程位置與加大行高
            y_offset = y1 + 90  
            line_height = 65    # 大字體需要 65 像素行高才不會重疊
            
            for index, (time_prefix, event_title) in enumerate(sorted_events):
                if index >= 2 or (y_offset + line_height > y2): # 超大字體下一格最多顯示 2~3 條
                    break
                
                display_text = f"{time_prefix}{event_title}"
                current_max_width = MAX_TEXT_WIDTH
                if (index == 1 or y_offset + (line_height * 2) > y2) and len(sorted_events) > (index + 1):
                    current_max_width = MAX_TEXT_WIDTH - 60
                
                if draw.textlength(display_text, font=font_event) > current_max_width:
                    while draw.textlength(display_text + "..", font=font_event) > current_max_width and len(display_text) > 0:
                        display_text = display_text[:-1]
                    display_text += ".."
                
                if (index == 1 or y_offset + (line_height * 2) > y2) and len(sorted_events) > (index + 1):
                    display_text += "..."
                
                draw.text((x1 + 20, y_offset), display_text, fill=0, font=font_event)
                y_offset += line_height

# 儲存本地圖片
image.save("calendar.png")
print("🎉 GIANT Font & Compact Top Bar Calendar Generated!")
