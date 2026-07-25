import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone
import calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 設定 ====================
SCREEN_WIDTH, SCREEN_HEIGHT = 3508, 2480
TOPBAR_HEIGHT, DOW_HEIGHT = 187, 131
GRID_ROWS, GRID_COLS = 5, 7
CELL_WIDTH, CELL_HEIGHT = SCREEN_WIDTH // GRID_COLS, (SCREEN_HEIGHT - TOPBAR_HEIGHT - DOW_HEIGHT) // GRID_ROWS
LOCAL_TZ = timezone(timedelta(hours=8))

COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (160, 160, 160)
COLOR_RED = (255, 0, 0)        # 假期紅色
COLOR_LINE = (0, 160, 210)
COLOR_ORANGE = (242, 133, 0)   # [SH] 橙色
COLOR_WHITE = (255, 255, 255)

def get_scaled_font(font_size):
    # 簡化字體加載，優先嘗試本地路徑
    font_path = "msjh.ttf"
    if not os.path.exists(font_path):
        try: urllib.request.urlretrieve("https://github.com/hanyuan-font/msjh/raw/master/msjh.ttf", font_path)
        except: pass
    try: return ImageFont.truetype(font_path, font_size)
    except: return ImageFont.load_default()

font_title = get_scaled_font(70)
font_week = get_scaled_font(44)
font_date = get_scaled_font(38)
font_event = get_scaled_font(36)
font_info = get_scaled_font(22)

# ==================== 2. 繪圖邏輯 ====================
def generate_perfect_calendar(year, month, events, holiday_dates, filename):
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), COLOR_WHITE)
    draw = ImageDraw.Draw(image)

    # 標題與日期
    title_text = f"{calendar.month_name[month]} {year}"
    title_w = draw.textlength(title_text, font=font_title)
    draw.text(((SCREEN_WIDTH - title_w) // 2, (TOPBAR_HEIGHT - 70) // 2), title_text, fill=COLOR_BLACK, font=font_title)

    # 繪製格線與內容
    first_weekday, _ = calendar.monthrange(year, month)
    start_col = (first_weekday + 1) % 7
    start_of_calendar = datetime(year, month, 1) - timedelta(days=start_col)

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell_date = (start_of_calendar + timedelta(days=row * GRID_COLS + col)).date()
            x1, y1 = col * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT + (row * CELL_HEIGHT)
            x2, y2 = x1 + CELL_WIDTH, y1 + CELL_HEIGHT
            
            # 畫框線
            draw.rectangle([x1, y1, x2, y2], outline=COLOR_LINE, width=2)
            
            # 日期數字
            is_holiday = (cell_date.strftime("%Y-%m-%d") in holiday_dates)
            date_color = COLOR_RED if is_holiday else (COLOR_BLACK if cell_date.month == month else COLOR_GRAY)
            draw.text((x1 + 15, y1 + 12), str(cell_date.day), fill=date_color, font=font_date)
            
            # 行程文字
            if cell_date.strftime("%Y-%m-%d") in events:
                y_offset = y1 + 65
                for time_prefix, event_title, is_holiday_event in events[cell_date.strftime("%Y-%m-%d")]:
                    # --- 顏色邏輯修正：[SH] 優先為橙色，假期為紅色 ---
                    if is_holiday_event:
                        event_color = COLOR_RED
                    elif "[SH]" in event_title:
                        event_color = COLOR_ORANGE
                    else:
                        event_color = COLOR_BLACK if cell_date.month == month else COLOR_GRAY
                        
                    draw.text((x1 + 15, y_offset), f"{time_prefix}{event_title}", fill=event_color, font=font_event)
                    y_offset += 45
    image.save(filename)

# ==================== 3. 主循環 ====================
API_KEY = 'AIzaSyAYBpOB6UoMYeAAmwTM_1KdYEzwtv6zXiE' # 請確保這裡已填入
CALENDAR_CONFIG = [
    ('dcyt122024@gmail.com', False), 
    ('de06ed3354bfa3472551deb2e49510d6cb42c9870578bc7d54de341448565f73@group.calendar.google.com', True) 
]

for i in range(6):
    target = datetime.now() + timedelta(days=i*30)
    y, m = target.year, target.month
    start_date = datetime(y, m, 1) - timedelta(days=7)
    end_date = (datetime(y, m, 1) + timedelta(days=40))
    
    events = {}
    holiday_dates = set() 
    
    for cal_id, is_holiday_cal in CALENDAR_CONFIG:
        url = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(cal_id)}/events?key={API_KEY}&timeMin={start_date.strftime('%Y-%m-%dT00:00:00Z')}&timeMax={end_date.strftime('%Y-%m-%dT00:00:00Z')}&singleEvents=true&orderBy=startTime&maxResults=250"
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                for ev in data.get('items', []):
                    start_dt = ev.get('start', {}).get('dateTime')
                    end_dt = ev.get('end', {}).get('dateTime')
                    day = (start_dt or ev.get('start', {}).get('date'))[:10]
                    if day not in events: events[day] = []
                    if is_holiday_cal: holiday_dates.add(day)
                    
                    time_str = f"{start_dt[11:16]}-{end_dt[11:16]} " if start_dt and end_dt else ""
                    events[day].append((time_str, ev.get('summary', '(No title)'), is_holiday_cal))
        except: continue
    
    # 排序：假期永遠在最上面
    for day in events: events[day].sort(key=lambda x: x[2], reverse=True)
    generate_perfect_calendar(y, m, events, holiday_dates, f"calendar{i+1}.png")
