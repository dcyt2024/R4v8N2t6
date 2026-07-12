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

TOP_MARGIN = 240   # 🌟 大幅加高頂部留白，給予置中超級大標題足夠的空間
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
# 為了安全抓取當月完整行程
today = datetime.now(LOCAL_TZ).date()
start_of_month = datetime(today.year, today.month, 1).date()
end_of_month = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1]).date()

for component in gcal.walk():
    if component.name == "VEVENT":
        summary = str(component.get('summary', 'No Title'))
        dtstart = component.get('dtstart').dt
        dtend = component.get('dtend').dt
        
        time_str = "" 
        if isinstance(dtstart, datetime):
            local_start = dtstart.astimezone(LOCAL_TZ)
            event_date = local_start.date()
            
            # 🌟 核心修正：同時抓取並格式化開始與結束時間 (例如 10:00-11:30)
            start_time = local_start.strftime("%H:%M")
            if isinstance(dtend, datetime):
                local_end = dtend.astimezone(LOCAL_TZ)
                end_time = local_end.strftime("%H:%M")
                time_str = f"{start_time}-{end_time} "
            else:
                time_str = f"{start_time} "
        else:
            event_date = dtstart
            
        # 只記錄本月範圍內的活動
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

# 🌟 核心修正：字體全面終極放大，活動字體放大到 42 級！
font_title = ImageFont.truetype(font_path, 96) if font_path else ImageFont.load_default() # 54 -> 72 -> 96 (超級巨無霸標題)
font_week = ImageFont.truetype(font_path, 36) if font_path else ImageFont.load_default()  # 24 -> 32 -> 36
font_date = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default()  # 28 -> 40 -> 42
font_event = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default() # 22 -> 34 -> 42 (終極清晰大字)

# ==================== 4. 繪製頂部介面（置中超大標題） ====================
now = datetime.now(LOCAL_TZ)
current_year = now.year
current_month = now.month

# 🌟 核心修正：將月份標題（例如 "JULY 2026"）進行精確的水平中央置中
month_name = calendar.month_name[current_month].upper()
title_text = f"{month_name} {current_year}"
title_w = draw.textlength(title_text, font=font_title)
title_x = (SCREEN_WIDTH - title_w) // 2
draw.text((title_x, 40), title_text, fill=0, font=font_title)

# 星期標題
weekdays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
for i, day_name in enumerate(weekdays):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    draw.text((x, 185), day_name, fill=0, font=font_week)

# 頂部裝飾粗線
draw.line([(0, TOP_MARGIN), (SCREEN_WIDTH, TOP_MARGIN)], fill=0, width=6)

# ==================== 5. 繪製日曆格子與行程 ====================
first_weekday, num_days = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7 
start_of_calendar = datetime(current_year, current_month, 1, tzinfo=LOCAL_TZ) - timedelta(days=start_col)

MAX_TEXT_WIDTH = CELL_WIDTH - 24

for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        days_to_add = row * GRID_COLS + col
        cell_date = (start_of_calendar + timedelta(days=days_to_add)).date()
        cell_date_str = cell_date.strftime("%Y-%m-%d")
        
        x1 = col * CELL_WIDTH
        y1 = TOP_MARGIN + (row * CELL_HEIGHT)
        x2 = x1 + CELL_WIDTH
        y2 = y1 + CELL_HEIGHT
        
        # 畫日曆格子邊框
        draw.rectangle([(x1, y1), (x2, y2)], outline=0, width=1)
        
        # 🌟 核心修正：如果不是本月的日子（6月或8月），直接跳過不繪製任何數字和行程（格子留空）
        if cell_date.month != current_month:
            continue
            
        # 右上角繪製本月日期數字
        date_text = str(cell_date.day)
        text_w = draw.textlength(date_text, font=font_date)
        draw.text((x2 - text_w - 15, y1 + 12), date_text, fill=0, font=font_date)
        
        # 填入行程 (因字體極大，最多容納 2-3 個)
        if cell_date_str in calendar_events:
            # 排序：有時間的行程排前面
            sorted_events = sorted(calendar_events[cell_date_str], key=lambda x: x[0] if x[0] else "24:00")
            
            y_offset = y1 + 65  # 大字體起始高度
            line_height = 54    # 42級字體所需要的舒適安全行高
            
            for index, (time_prefix, event_title) in enumerate(sorted_events):
                # 超過 3 行（或空間不夠）則停止繪製，避免溢出格子
                if index >= 3 or (y_offset + line_height > y2):
                    break
                
                # 行程格式：例如 "10:00-11:30 Meeting"
                display_text = f"{time_prefix}{event_title}"
                
                # 如果是最後一行且後面還有活動，預留長度給 "..."
                current_max_width = MAX_TEXT_WIDTH
                if (index == 2 or y_offset + (line_height * 2) > y2) and len(sorted_events) > (index + 1):
                    current_max_width = MAX_TEXT_WIDTH - 50
                
                # 精確像素截斷
                if draw.textlength(display_text, font=font_event) > current_max_width:
                    while draw.textlength(display_text + "..", font=font_event) > current_max_width and len(display_text) > 0:
                        display_text = display_text[:-1]
                    display_text += ".."
                
                # 加上多餘活動的 "..." 提示
                if (index == 2 or y_offset + (line_height * 2) > y2) and len(sorted_events) > (index + 1):
                    display_text += "..."
                
                draw.text((x1 + 15, y_offset), display_text, fill=0, font=font_event)
                y_offset += line_height

# ==================== 6. 儲存圖片 ====================
image.save("calendar.png")
print("🎉 Masterpiece Calendar Image with Start-End Time Generated!")
