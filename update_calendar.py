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

# 🌟 極限壓縮頂部：只留 100 像素給標題與星期，把所有空間還給格子
TOP_MARGIN = 100   
CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOP_MARGIN) // GRID_ROWS

LOCAL_TZ = timezone(timedelta(hours=8)) 

# ==================== 2. Google API 讀取邏輯 ====================
CALENDAR_ID = 'dcyt122024@gmail.com'
API_KEY = 'AIzaSyAYBpOB6UoMYeAAmwTM_1KdYEzwtv6zXiE'

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
                
            day_key = start[:10]
            
            time_str = ""
            if 'dateTime' in ev.get('start', {}):
                dt_start = datetime.strptime(start[:19], "%Y-%m-%dT%H:%M:%S")
                t1 = dt_start.strftime("%H:%M")
                if 'dateTime' in ev.get('end', {}):
                    dt_end = datetime.strptime(end[:19], "%Y-%m-%dT%H:%M:%S")
                    t2 = dt_end.strftime("%H:%M")
                    time_str = f"{t1}-{t2} "
                else:
                    time_str = f"{t1} "
            else:
                time_str = ""
                
            if day_key not in calendar_events:
                calendar_events[day_key] = []
            calendar_events[day_key].append((time_str, summary))
            
except Exception as e:
    print(f"⚠️ Google API 錯誤: {e}")

# ==================== 3. 初始化畫布與真實字型 ====================
image = Image.new("1", (SCREEN_WIDTH, SCREEN_HEIGHT), 1)
draw = ImageDraw.Draw(image)

font_path = "msjh.ttf"
if not os.path.exists(font_path):
    try:
        urllib.request.urlretrieve("https://github.com/hanyuan-font/msjh/raw/master/msjh.ttf", font_path)
    except:
        font_path = None

# 🌟 真正有感的特大字體設定
font_title = ImageFont.truetype(font_path, 54) if font_path else ImageFont.load_default() # 主標題
font_week = ImageFont.truetype(font_path, 32) if font_path else ImageFont.load_default()  # 星期
font_date = ImageFont.truetype(font_path, 46) if font_path else ImageFont.load_default()  # 日期數字
font_event = ImageFont.truetype(font_path, 36) if font_path else ImageFont.load_default() # 活動文字

# ==================== 4. 繪製頂部介面（與星期合併，極致緊湊） ====================
current_year = 2026
current_month = 7

# 月份與年份放左上角
draw.text((30, 20), "July 2026", fill=0, font=font_title)

# 星期直接在右手邊一字排開（同一排）
weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
for i, day_name in enumerate(weekdays):
    # 讓星期精準對齊底下的格子中線
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    draw.text((x, 38), day_name, fill=0, font=font_week)

# 頂部跟格子分界的橫線
draw.line([(0, TOP_MARGIN), (SCREEN_WIDTH, TOP_MARGIN)], fill=0, width=4)

# ==================== 5. 繪製日曆格子與行程 ====================
first_weekday, num_days = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7 
start_of_calendar = datetime(current_year, current_month, 1) - timedelta(days=start_col)

for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        days_to_add = row * GRID_COLS + col
        cell_date = (start_of_calendar + timedelta(days=days_to_add)).date()
        cell_date_str = cell_date.strftime("%Y-%m-%d")
        
        x1 = col * CELL_WIDTH
        y1 = TOP_MARGIN + (row * CELL_HEIGHT)
        x2 = x1 + CELL_WIDTH
        y2 = y1 + CELL_HEIGHT
        
        # 畫格線
        draw.rectangle([(x1, y1), (x2, y2)], outline=0, width=3)
        
        # 繪製左上角大日期數字
        date_text = str(cell_date.day)
        draw.text((x1 + 20, y1 + 15), date_text, fill=0, font=font_date)
        
        # 繪製行程資料（純文字、無外框、大字體）
        if cell_date_str in calendar_events:
            events_in_day = calendar_events[cell_date_str]
            
            y_offset = y1 + 75   # 從日期下方開始排
            line_height = 46     # 大字體行高
            
            for time_prefix, event_title in events_in_day:
                if y_offset + line_height > y2 - 10:
                    break
                
                # 乾淨的純文字組合
                display_text = f"{time_prefix}{event_title}"
                max_text_width = CELL_WIDTH - 30
                
                # 超長截斷
                if draw.textlength(display_text, font=font_event) > max_text_width:
                    while draw.textlength(display_text + "..", font=font_event) > max_text_width and len(display_text) > 0:
                        display_text = display_text[:-1]
                    display_text += ".."
                
                # 直接寫入文字
                draw.text((x1 + 20, y_offset), display_text, fill=0, font=font_event)
                y_offset += line_height

# 儲存
image.save("calendar.png")
print("🎉 Clean & Clear Large Font Calendar Generated!")
