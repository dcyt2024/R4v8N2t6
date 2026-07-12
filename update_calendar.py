import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone
import calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 設定與工具函式 ====================
SCREEN_WIDTH, SCREEN_HEIGHT = 1872, 1404
TOPBAR_HEIGHT, DOW_HEIGHT = 100, 70
GRID_ROWS, GRID_COLS = 5, 7
CELL_WIDTH, CELL_HEIGHT = SCREEN_WIDTH // GRID_COLS, (SCREEN_HEIGHT - TOPBAR_HEIGHT - DOW_HEIGHT) // GRID_ROWS
LOCAL_TZ = timezone(timedelta(hours=8))
COLOR_BLACK, COLOR_GRAY, COLOR_LINE = 0, 160, 210

def get_scaled_font(font_size):
    font_sources = ["msjh.ttf", "C:/Windows/Fonts/msjh.ttc", "/System/Library/Fonts/STHeiti Light.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    if not os.path.exists("msjh.ttf"):
        try: urllib.request.urlretrieve("https://github.com/hanyuan-font/msjh/raw/master/msjh.ttf", "msjh.ttf")
        except: pass
    for path in font_sources:
        if os.path.exists(path) or path == "msjh.ttf":
            try: return ImageFont.truetype(path, font_size)
            except: continue
    return ImageFont.load_default(size=font_size)

font_title = get_scaled_font(70)
font_week = get_scaled_font(44)
font_date = get_scaled_font(38)
font_event = get_scaled_font(24)
font_info = get_scaled_font(22)

# ==================== 2. 完美繪圖邏輯 (封裝) ====================
def generate_perfect_calendar(year, month, events, filename):
    image = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 255)
    draw = ImageDraw.Draw(image)

    # 標題
    title_text = f"{calendar.month_name[month]} {year}"
    title_w = draw.textlength(title_text, font=font_title)
    draw.text(((SCREEN_WIDTH - title_w) // 2, (TOPBAR_HEIGHT - 70) // 2), title_text, fill=COLOR_BLACK, font=font_title)

    # 更新時間
    gen_time_str = f"Generated: {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}"
    info_w = draw.textlength(gen_time_str, font=font_info)
    draw.text((SCREEN_WIDTH - info_w - 30, TOPBAR_HEIGHT - 22 - 6), gen_time_str, fill=COLOR_GRAY, font=font_info)

    draw.line([(0, TOPBAR_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT)], fill=COLOR_BLACK, width=3)

    # 星期列
    weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day_name in enumerate(weekdays):
        w = draw.textlength(day_name, font=font_week)
        draw.text((i * CELL_WIDTH + (CELL_WIDTH - w) // 2, TOPBAR_HEIGHT + (DOW_HEIGHT - 44) // 2), day_name, fill=COLOR_BLACK, font=font_week)
        if i < 6: draw.line([((i + 1) * CELL_WIDTH, TOPBAR_HEIGHT), ((i + 1) * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=COLOR_LINE, width=2)
    draw.line([(0, TOPBAR_HEIGHT + DOW_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=COLOR_BLACK, width=3)

    # 格子與事件
    def split_event_to_lines(text, font, max_width):
        if draw.textlength(text, font=font) <= max_width: return [text]
        line1 = ""
        idx = 0
        while idx < len(text) and draw.textlength(line1 + text[idx], font=font) <= max_width:
            line1 += text[idx]; idx += 1
        line2 = text[idx:]
        if draw.textlength(line2, font=font) > max_width:
            while draw.textlength(line2 + "..", font=font) > max_width and len(line2) > 0: line2 = line2[:-1]
            line2 += ".."
        return [line1, line2]

    first_weekday, _ = calendar.monthrange(year, month)
    start_col = (first_weekday + 1) % 7
    start_of_calendar = datetime(year, month, 1) - timedelta(days=start_col)

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell_date = (start_of_calendar + timedelta(days=row * GRID_COLS + col)).date()
            x1, y1 = col * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT + (row * CELL_HEIGHT)
            x2, y2 = x1 + CELL_WIDTH, y1 + CELL_HEIGHT
            
            if col < 6: draw.line([(x2, y1), (x2, y2)], fill=COLOR_LINE, width=2)
            draw.line([(x1, y2), (x2, y2)], fill=COLOR_LINE, width=2)
            
            text_color = COLOR_BLACK if cell_date.month == month else COLOR_GRAY
            draw.text((x1 + 15, y1 + 12), str(cell_date.day), fill=text_color, font=font_date)
            
            if cell_date.strftime("%Y-%m-%d") in events:
                y_offset = y1 + 55
                for time_prefix, event_title in events[cell_date.strftime("%Y-%m-%d")]:
                    for line in split_event_to_lines(f"{time_prefix}{event_title}".strip(), font_event, CELL_WIDTH - 30):
                        if y_offset + 28 > y2 - 8: break
                        draw.text((x1 + 15, y_offset), line, fill=text_color, font=font_event)
                        y_offset += 28
                    y_offset += 4
    image.save(filename)

# ==================== 3. 主循環：產生 6 個月 ====================
API_KEY = 'AIzaSyAYBpOB6UoMYeAAmwTM_1KdYEzwtv6zXiE'
CALENDAR_ID = 'dcyt122024@gmail.com'

for i in range(6):
    target = datetime.now() + timedelta(days=i*30)
    y, m = target.year, target.month
    
    # API 讀取
    events = {}
    try:
        next_m = m + 1 if m < 12 else 1
        next_y = y if m < 12 else y + 1
        url = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(CALENDAR_ID)}/events?key={API_KEY}&timeMin={y}-{m:02d}-01T00:00:00Z&timeMax={next_y}-{next_m:02d}-01T00:00:00Z&singleEvents=true&orderBy=startTime&maxResults=250"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            for ev in data.get('items', []):
                start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date')
                day = start[:10]
                if day not in events: events[day] = []
                time_str = f"{start[11:16]} " if 'dateTime' in ev.get('start', {}) else ""
                events[day].append((time_str, ev.get('summary', '(No title)')))
    except Exception as e: print(f"API Error: {e}")
    
    generate_perfect_calendar(y, m, events, f"calendar{i+1}.png")
    print(f"✅ {y}-{m} 完美生成: calendar{i+1}.png")
