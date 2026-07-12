import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone
import calendar
from PIL import Image, ImageDraw, ImageFont
import os

# 強制清理舊檔案
if os.path.exists("calendar.png"):
    os.remove("calendar.png")

# ==================== 1. 設定與參數 ====================
SCREEN_WIDTH, SCREEN_HEIGHT = 1872, 1404
TOPBAR_HEIGHT, DOW_HEIGHT = 100, 70
GRID_ROWS, GRID_COLS = 5, 7
CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOPBAR_HEIGHT - DOW_HEIGHT) // GRID_ROWS
LOCAL_TZ = timezone(timedelta(hours=8))

# 載入字型 (使用 msjh.ttf)
def get_scaled_font(size):
    try: return ImageFont.truetype("msjh.ttf", size)
    except: return ImageFont.load_default()

font_title, font_week = get_scaled_font(70), get_scaled_font(44)
font_date, font_event, font_info = get_scaled_font(38), get_scaled_font(24), get_scaled_font(22)

# ==================== 2. API 資料讀取 ====================
CALENDAR_ID = 'dcyt122024@gmail.com'
API_KEY = 'AIzaSyAYBpOB6UoMYeAAmwTM_1KdYEzwtv6zXiE' # 保持你提供的 Key

calendar_events = {}
try:
    url = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(CALENDAR_ID)}/events"
    params = {'key': API_KEY, 'timeMin': "2026-07-01T00:00:00Z", 'timeMax': "2026-08-01T00:00:00Z", 'singleEvents': 'true', 'orderBy': 'startTime'}
    req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        for ev in data.get('items', []):
            start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date')
            day_key = start[:10]
            time_str = f"{start[11:16]} " if 'dateTime' in ev.get('start', {}) else ""
            if day_key not in calendar_events: calendar_events[day_key] = []
            calendar_events[day_key].append((time_str, ev.get('summary', '(No title)')))
except Exception as e: print(f"API Error: {e}")

# ==================== 3. 繪製邏輯 ====================
image = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 255)
draw = ImageDraw.Draw(image)

# Topbar
draw.text(((SCREEN_WIDTH - draw.textlength("July 2026", font=font_title)) // 2, 10), "July 2026", fill=0, font=font_title)
gen_str = f"Generated: {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}"
draw.text((SCREEN_WIDTH - draw.textlength(gen_str, font=font_info) - 30, TOPBAR_HEIGHT - 28), gen_str, fill=160, font=font_info)
draw.line([(0, TOPBAR_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT)], fill=0, width=3)

# 星期列
for i, name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
    draw.text((i * CELL_WIDTH + (CELL_WIDTH - draw.textlength(name, font=font_week))//2, TOPBAR_HEIGHT + 10), name, fill=0, font=font_week)
draw.line([(0, TOPBAR_HEIGHT + DOW_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=0, width=3)

# 日曆格子
start_date = datetime(2026, 7, 1) - timedelta(days=(datetime(2026, 7, 1).weekday() + 1) % 7)
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        curr = (start_date + timedelta(days=row*7 + col)).date()
        x, y = col * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT + row * CELL_HEIGHT
        draw.line([(x + CELL_WIDTH, y), (x + CELL_WIDTH, y + CELL_HEIGHT)], fill=210, width=2)
        draw.line([(x, y + CELL_HEIGHT), (x + CELL_WIDTH, y + CELL_HEIGHT)], fill=210, width=2)
        
        draw.text((x + 15, y + 10), str(curr.day), fill=0 if curr.month == 7 else 160, font=font_date)
        
        # 顯示最多 3 個活動
        y_off = y + 55 
        for time_pref, title in calendar_events.get(curr.strftime("%Y-%m-%d"), [])[:3]:
            event_text = f"{time_pref}{title}"
            # 簡化繪製，不進行複雜折行以節省空間，確保3個都能顯示
            draw.text((x + 15, y_off), event_text[:35], fill=0, font=font_event)
            y_off += 30 

image.save("calendar.png")
print("✅ 完成：已優化顯示 3 個活動")
