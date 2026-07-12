import urllib.request
from datetime import datetime, timedelta, timezone
import calendar
from icalendar import Calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 1872*1404 排版設定 ====================
# ⚠️ 請替換成你 Google 日曆的「不公開 iCal 網址」
ICAL_URL = "https://calendar.google.com/calendar/ical/dcyt122024%40gmail.com/public/basic.ics"

SCREEN_WIDTH = 1872
SCREEN_HEIGHT = 1404
GRID_ROWS = 5
GRID_COLS = 7

TOP_MARGIN = 180   # 稍微加高頂部，留給更大的標題
CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOP_MARGIN) // GRID_ROWS

# 設定在地時區為 GMT+8 (香港/台灣時間)
LOCAL_TZ = timezone(timedelta(hours=8))

# ==================== 2. 下載並解析 Google 日曆 ====================
print("Fetching data from Google Calendar...")
try:
    req = urllib.request.Request(ICAL_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        gcal = Calendar.from_ical(response.read())
except Exception as e:
    print(f"Failed to fetch calendar: {e}")
    gcal = []

calendar_events = {}
today = datetime.now(LOCAL_TZ).date()
end_date = today + timedelta(days=35)

for component in gcal.walk():
    if component.name == "VEVENT":
        summary = str(component.get('summary', 'No Title'))
        dtstart = component.get('dtstart').dt
        
        time_str = "" 
        if isinstance(dtstart, datetime):
            local_dt = dtstart.astimezone(LOCAL_TZ)
            event_date = local_dt.date()
            time_str = local_dt.strftime("%H:%M ")
        else:
            event_date = dtstart
            
        if today <= event_date <= end_date:
            date_str = event_date.strftime("%Y-%m-%d")
            if date_str not in calendar_events:
                calendar_events[date_str] = []
            calendar_events[date_str].append((time_str, summary))

# ==================== 3. 初始化畫布與下載字型 ====================
image = Image.new("1", (SCREEN_WIDTH, SCREEN_HEIGHT), 1)
draw = ImageDraw.Draw(image)

# 強制下載支援繁中與英文的高畫質字型（微軟正黑體相容版）
font_url = "https://github.com/hanyuan-font/msjh/raw/master/msjh.ttf"
font_path = "msjh.ttf"

if not os.path.exists(font_path):
    print("Downloading font...")
    try:
        urllib.request.urlretrieve(font_url, font_path)
    except:
        font_path = None

# 🌟 核心修正：全面大幅度放大字體大小
font_title = ImageFont.truetype(font_path, 72) if font_path else ImageFont.load_default() # 原 54 -> 72
font_week = ImageFont.truetype(font_path, 32) if font_path else ImageFont.load_default()  # 原 24 -> 32
font_date = ImageFont.truetype(font_path, 40) if font_path else ImageFont.load_default()  # 原 28 -> 40
font_event = ImageFont.truetype(font_path, 34) if font_path else ImageFont.load_default() # 原 22 -> 34 (超清晰大字)

# ==================== 4. 繪製頂部介面 ====================
now = datetime.now(LOCAL_TZ)
current_year = now.year
current_month = now.month

# 標題 (例如 "JULY 2026")
month_name = calendar.month_name[current_month].upper()
draw.text((50, 35), f"{month_name} {current_year}", fill=0, font=font_title)

# 星期標題
weekdays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
for i, day_name in enumerate(weekdays):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    draw.text((x, 125), day_name, fill=0, font=font_week)

# 頂部裝飾線
draw.line([(0, TOP_MARGIN), (SCREEN_WIDTH, TOP_MARGIN)], fill=0, width=5)

# ==================== 5. 繪製日曆格子與行程 ====================
first_weekday, num_days = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7 
start_of_calendar = datetime(current_year, current_month, 1, tzinfo=LOCAL_TZ) - timedelta(days=start_col)

# 左右留白保護區
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
        
        # 畫格子邊框
        draw.rectangle([(x1, y1), (x2, y2)], outline=0, width=1)
        
        # 日期文字 (右上角)
        date_text = str(cell_date.day)
        if cell_date.month != current_month:
            date_text = f"[{date_text}]"
            
        text_w = draw.textlength(date_text, font=font_date)
        draw.text((x2 - text_w - 15, y1 + 15), date_text, fill=0, font=font_date)
        
        # 填入行程 (最多 3 個)
        if cell_date_str in calendar_events:
            sorted_events = sorted(calendar_events[cell_date_str], key=lambda x: x[0] if x[0] else "24:00")
            
            # 🌟 核心修正：行高與起點重新計算，以適應 34 級大字
            y_offset = y1 + 65  # 日期下方的起點
            line_height = 46    # 大字體的舒適舒適行距
            
            for index, (time_prefix, event_title) in enumerate(sorted_events):
                # 🌟 如果已經到第 4 個活動，或是空間不夠了，就在前一行結尾加 "..." 並強行中斷
                if index >= 3:
                    break
                
                display_text = f"{time_prefix}{event_title}"
                
                # 如果是第 3 個活動，且後面還有更多行程，預留長度給 "..."
                current_max_width = MAX_TEXT_WIDTH
                if index == 2 and len(sorted_events) > 3:
                    current_max_width = MAX_TEXT_WIDTH - 40
                
                # 精確像素寬度截斷
                if draw.textlength(display_text, font=font_event) > current_max_width:
                    while draw.textlength(display_text + "..", font=font_event) > current_max_width and len(display_text) > 0:
                        display_text = display_text[:-1]
                    display_text += ".."
                
                # 如果有第 4 個活動，我們在第 3 個活動後方加上 "..." 提示
                if index == 2 and len(sorted_events) > 3:
                    display_text += "..."
                
                draw.text((x1 + 15, y_offset), display_text, fill=0, font=font_event)
                y_offset += line_height

# ==================== 6. 儲存圖片 ====================
image.save("calendar.png")
print("🎉 Large Font Calendar Image Generated!")
