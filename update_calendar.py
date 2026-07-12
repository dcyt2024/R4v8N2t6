import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone
import calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 1872*1404 畫布與空間解鎖控管 ====================
SCREEN_WIDTH = 1872
SCREEN_HEIGHT = 1404

TOPBAR_HEIGHT = 100   
DOW_HEIGHT = 70       

GRID_ROWS = 5
GRID_COLS = 7

CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOPBAR_HEIGHT - DOW_HEIGHT) // GRID_ROWS

LOCAL_TZ = timezone(timedelta(hours=8))

# ==================== 2. 安全字型載入 ====================
def get_scaled_font(font_size):
    font_sources = [
        "msjh.ttf",
        "C:/Windows/Fonts/msjh.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    if not os.path.exists("msjh.ttf"):
        try:
            urllib.request.urlretrieve("https://github.com/hanyuan-font/msjh/raw/master/msjh.ttf", "msjh.ttf")
        except:
            pass
    for path in font_sources:
        if os.path.exists(path) or path == "msjh.ttf":
            try:
                return ImageFont.truetype(path, font_size)
            except:
                continue
    return ImageFont.load_default(size=font_size)

font_title = get_scaled_font(70)   
font_week = get_scaled_font(44)    
font_date = get_scaled_font(38)    
font_event = get_scaled_font(24)   
font_info = get_scaled_font(22)    

# ==================== 3. Google API 資料讀取 ====================
CALENDAR_ID = 'dcyt122024@gmail.com'
API_KEY = 'AIzaSyAYBpOB6UoMYeAAmwTM_1KdYEzwtv6zXiE'

calendar_events = {}
try:
    url = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(CALENDAR_ID)}/events"
    params = {
        'key': API_KEY,
        'timeMin': "2026-07-01T00:00:00Z",
        'timeMax': "2026-08-01T00:00:00Z",
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
        items = data.get('items', [])
        
        for ev in items:
            start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date')
            end = ev.get('end', {}).get('dateTime') or ev.get('end', {}).get('date')
            summary = ev.get('summary', '(No title)')
            
            if not start: 
                continue
            
            day_key = start[:10]
            time_str = ""
            if 'dateTime' in ev.get('start', {}):
                t1 = start[11:16]
                t2 = end[11:16] if end else ""
                time_str = f"{t1}-{t2}" if t2 else f"{t1}"
                
            if day_key not in calendar_events:
                calendar_events[day_key] = []
            calendar_events[day_key].append((time_str, summary))
except Exception as e:
    print(f"API Error: {e}")

# ==================== 4. 繪製與排版 (灰階模式) ====================
image = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 255) 
draw = ImageDraw.Draw(image)

COLOR_BLACK = 0
COLOR_GRAY = 160
COLOR_LINE = 210

# 1. Topbar 主標題
title_text = "July 2026"
title_w = draw.textlength(title_text, font=font_title)
draw.text(((SCREEN_WIDTH - title_w) // 2, (TOPBAR_HEIGHT - 70) // 2), title_text, fill=COLOR_BLACK, font=font_title)

# 🌟 修正：讓 Generated 時間行精準「貼緊」下方黑線 (TOPBAR_HEIGHT - 字高 - 留白)
gen_time_str = f"Generated: {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}"
info_w = draw.textlength(gen_time_str, font=font_info)
draw.text((SCREEN_WIDTH - info_w - 30, TOPBAR_HEIGHT - 22 - 6), gen_time_str, fill=COLOR_GRAY, font=font_info)

draw.line([(0, TOPBAR_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT)], fill=COLOR_BLACK, width=3)

# 2. 星期列
weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
for i, day_name in enumerate(weekdays):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    y = TOPBAR_HEIGHT + (DOW_HEIGHT - 44) // 2
    draw.text((x, y), day_name, fill=COLOR_BLACK, font=font_week)
    if i < 6:
        draw.line([((i + 1) * CELL_WIDTH, TOPBAR_HEIGHT), ((i + 1) * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=COLOR_LINE, width=2)

draw.line([(0, TOPBAR_HEIGHT + DOW_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=COLOR_BLACK, width=3)

# 3. 日曆格子群
current_year, current_month = 2026, 7
first_weekday, _ = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7 
start_of_calendar = datetime(current_year, current_month, 1) - timedelta(days=start_col)

REAL_TOP = TOPBAR_HEIGHT + DOW_HEIGHT

def split_title_to_lines(text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return [text]
    line1 = ""
    for char in text:
        if draw.textlength(line1 + char, font=font) <= max_width:
            line1 += char
        else:
            break
    line2 = text[len(line1):]
    if draw.textlength(line2, font=font) > max_width:
        while draw.textlength(line2 + "..", font=font) > max_width and len(line2) > 0:
            line2 = line2[:-1]
        line2 += ".."
    return [line1, line2]

for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        days_to_add = row * GRID_COLS + col
        cell_date = (start_of_calendar + timedelta(days=days_to_add)).date()
        cell_date_str = cell_date.strftime("%Y-%m-%d")
        
        x1 = col * CELL_WIDTH
        y1 = REAL_TOP + (row * CELL_HEIGHT)
        x2 = x1 + CELL_WIDTH
        y2 = y1 + CELL_HEIGHT
        
        # 畫淡灰網格線
        if col < 6: draw.line([(x2, y1), (x2, y2)], fill=COLOR_LINE, width=2)
        draw.line([(x1, y2), (x2, y2)], fill=COLOR_LINE, width=2)
        
        is_current_month = (cell_date.month == current_month)
        text_color = COLOR_BLACK if is_current_month else COLOR_GRAY
        
        # 日期數字回到左上角
        date_text = str(cell_date.day)
        draw.text((x1 + 15, y1 + 12), date_text, fill=text_color, font=font_date)
            
        # 繪製行程列表 (全面垂直對齊，解鎖錯位)
        if cell_date_str in calendar_events:
            y_offset = y1 + 55   # 🌟 統一從日期下方 55px 開始一行行往下排
            line_height = 28    
            
            for time_prefix, event_title in calendar_events[cell_date_str]:
                max_w = CELL_WIDTH - 30
                
                # 1. 繪製時間行
                if time_prefix.strip():
                    if y_offset + line_height > y2 - 8: break
                    draw.text((x1 + 15, y_offset), time_prefix.strip(), fill=text_color, font=font_event)
                    y_offset += line_height
                
                # 2. 繪製標題行（支援長標題折行）
                title_lines = split_title_to_lines(event_title, font_event, max_w)
                for line in title_lines:
                    if y_offset + line_height > y2 - 8: break
                    draw.text((x1 + 15, y_offset), line, fill=text_color, font=font_event)
                    y_offset += line_height
                    
                # 行程之間的微小空隙
                y_offset += 4

# 儲存
image.save("calendar.png")
print("🎉 Perfect alignment version generated!")
