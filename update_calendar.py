import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone
import calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 1872*1404 畫布與 HTML 精準比例控管 ====================
SCREEN_WIDTH = 1872
SCREEN_HEIGHT = 1404

TOPBAR_HEIGHT = 150   # 頂部月年份高度
DOW_HEIGHT = 120      # 星期列高度

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

font_title = get_scaled_font(85)   
font_week = get_scaled_font(56)    
font_date = get_scaled_font(52)    
font_event = get_scaled_font(26)   
font_info = get_scaled_font(24)    

# ==================== 3. Google API 資料讀取 ====================
CALENDAR_ID = 'dcyt122024@gmail.com'
API_KEY = 'AKfycbyiMdCmH_4MoCpOGkt4flb0luLreIjWh8NA3g7pEmbFaRbuG9P18kNF1Fqmy0L8sbjR'

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
                time_str = f"{t1}-{t2} " if t2 else f"{t1} "
                
            if day_key not in calendar_events:
                calendar_events[day_key] = []
            calendar_events[day_key].append((time_str, summary))
except Exception as e:
    print(f"API Error: {e}")

# ==================== 4. 繪製與排版 (切換為灰階模式) ====================
# 🌟 將模式從 "1" 改為 "L"，允許使用 0 (黑) ~ 255 (白) 之間的灰色
image = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 255) # 255 是純白背景
draw = ImageDraw.Draw(image)

# 顏色定義 (0為純黑，160為優雅淺灰，210為格線淡灰)
COLOR_BLACK = 0
COLOR_GRAY = 160
COLOR_LINE = 210

# 1. Topbar：July 2026 居中
title_text = "July 2026"
title_w = draw.textlength(title_text, font=font_title)
draw.text(((SCREEN_WIDTH - title_w) // 2, (TOPBAR_HEIGHT - 85) // 2), title_text, fill=COLOR_BLACK, font=font_title)

# 右上角更新時間
gen_time_str = f"Generated: {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}"
info_w = draw.textlength(gen_time_str, font=font_info)
draw.text((SCREEN_WIDTH - info_w - 30, (TOPBAR_HEIGHT - 24) // 2), gen_time_str, fill=COLOR_GRAY, font=font_info)

draw.line([(0, TOPBAR_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT)], fill=COLOR_BLACK, width=3)

# 2. 星期列 (Sun - Sat)
weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
for i, day_name in enumerate(weekdays):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    y = TOPBAR_HEIGHT + (DOW_HEIGHT - 56) // 2
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

def split_text_to_two_lines(text, font, max_width):
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
        
        # 繪製淡灰色網格線，視覺更輕盈
        if col < 6: draw.line([(x2, y1), (x2, y2)], fill=COLOR_LINE, width=2)
        draw.line([(x1, y2), (x2, y2)], fill=COLOR_LINE, width=2)
        
        # 🌟 判斷是否為本月，決定字體顏色 (本月=黑，非本月=淺灰)
        is_current_month = (cell_date.month == current_month)
        text_color = COLOR_BLACK if is_current_month else COLOR_GRAY
        
        # 日期數字
        date_text = str(cell_date.day)
        draw.text((x1 + 20, y1 + 15), date_text, fill=text_color, font=font_date)
            
        # 繪製行程列表
        if cell_date_str in calendar_events:
            y_offset = y1 + 75   
            line_height = 34     
            
            for time_prefix, event_title in calendar_events[cell_date_str]:
                full_text = f"{time_prefix}{event_title}"
                max_w = CELL_WIDTH - 35
                
                lines = split_text_to_two_lines(full_text, font_event, max_w)
                
                for line in lines:
                    if y_offset + line_height > y2 - 10:
                        break
                    # 🌟 這裡行程的文字也會跟著日子的屬性一起變淡或變黑，非常漂亮！
                    draw.text((x1 + 20, y_offset), line, fill=text_color, font=font_event)
                    y_offset += line_height
                    
                y_offset += 5

# 儲存
image.save("calendar.png")
print("🎉 Premium Grayscale Multi-line Calendar Generated!")
