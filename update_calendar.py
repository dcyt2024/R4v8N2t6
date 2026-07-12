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

# 🌟 大字體調整：確保字體夠大清晰
font_title = get_scaled_font(85)   
font_week = get_scaled_font(56)    
font_date = get_scaled_font(56)    # 日期字體
font_event = get_scaled_font(44)   # 🌟 行程文字放大到 44px

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
        
        # 偵測是否成功拿到 items
        items = data.get('items', [])
        print(f"成功連線！拿到 {len(items)} 個原始事件。")
        
        for ev in items:
            start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date')
            end = ev.get('end', {}).get('dateTime') or ev.get('end', {}).get('date')
            summary = ev.get('summary', '(No title)')
            
            if not start: 
                continue
            
            # 安全截取 YYYY-MM-DD
            day_key = start[:10]
            
            time_str = ""
            if 'dateTime' in ev.get('start', {}):
                try:
                    # 考慮到可能帶有時區，安全切取時分
                    # "2026-07-12T14:00:00+08:00" -> "14:00"
                    t1 = start[11:16]
                    t2 = end[11:16] if end else ""
                    time_str = f"{t1}-{t2} " if t2 else f"{t1} "
                except Exception as e:
                    time_str = ""
                
            if day_key not in calendar_events:
                calendar_events[day_key] = []
            calendar_events[day_key].append((time_str, summary))
            
    print(f"解析完成，共有 {len(calendar_events)} 天有排程。內容：", calendar_events)
except Exception as e:
    # 🌟 這裡如果報錯，會在畫面直接印出詳細原因，方便我們除錯！
    print(f"❌ 發生致命錯誤!! Google API 讀取失敗: {e}")

# ==================== 4. 繪製與排版 ====================
image = Image.new("1", (SCREEN_WIDTH, SCREEN_HEIGHT), 1)
draw = ImageDraw.Draw(image)

# 1. Topbar：July 2026 居中
title_text = "July 2026"
title_w = draw.textlength(title_text, font=font_title)
draw.text(((SCREEN_WIDTH - title_w) // 2, (TOPBAR_HEIGHT - 85) // 2), title_text, fill=0, font=font_title)
draw.line([(0, TOPBAR_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT)], fill=0, width=3)

# 2. 星期列 (Sun - Sat)
weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
for i, day_name in enumerate(weekdays):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    y = TOPBAR_HEIGHT + (DOW_HEIGHT - 56) // 2
    draw.text((x, y), day_name, fill=0, font=font_week)
    if i < 6:
        draw.line([((i + 1) * CELL_WIDTH, TOPBAR_HEIGHT), ((i + 1) * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=0, width=2)

draw.line([(0, TOPBAR_HEIGHT + DOW_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=0, width=3)

# 3. 日曆格子群
current_year, current_month = 2026, 7
first_weekday, _ = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7 
start_of_calendar = datetime(current_year, current_month, 1) - timedelta(days=start_col)

REAL_TOP = TOPBAR_HEIGHT + DOW_HEIGHT

for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        days_to_add = row * GRID_COLS + col
        cell_date = (start_of_calendar + timedelta(days=days_to_add)).date()
        cell_date_str = cell_date.strftime("%Y-%m-%d")
        
        x1 = col * CELL_WIDTH
        y1 = REAL_TOP + (row * CELL_HEIGHT)
        x2 = x1 + CELL_WIDTH
        y2 = y1 + CELL_HEIGHT
        
        # 繪製邊框
        if col < 6: draw.line([(x2, y1), (x2, y2)], fill=0, width=2)
        draw.line([(x1, y2), (x2, y2)], fill=0, width=2)
        
        # 🌟 修正：日期數字不再死板置中，改成挪到左上角 (留白20px)，挪出空間給活動文字
        date_text = str(cell_date.day)
        draw.text((x1 + 20, y1 + 15), date_text, fill=0, font=font_date)
            
        # 繪製純文字行程列表（大字體、靠左對齊、無外框）
        if cell_date_str in calendar_events:
            y_offset = y1 + 80  # 從日期下方開始排
            line_height = 50    # 每行高度
            
            for time_prefix, event_title in calendar_events[cell_date_str]:
                if y_offset + line_height > y2 - 10:
                    break
                
                display_text = f"{time_prefix}{event_title}"
                max_text_width = CELL_WIDTH - 30
                
                # 自動截斷過長文字
                if draw.textlength(display_text, font=font_event) > max_text_width:
                    while draw.textlength(display_text + "..", font=font_event) > max_text_width and len(display_text) > 0:
                        display_text = display_text[:-1]
                    display_text += ".."
                
                # 寫入行程
                draw.text((x1 + 20, y_offset), display_text, fill=0, font=font_event)
                y_offset += line_height

# 儲存
image.save("calendar.png")
print("🎉 Calendar Updated!")
