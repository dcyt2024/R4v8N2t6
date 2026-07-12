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

# --- 設定 ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1872, 1404
TOPBAR_HEIGHT, DOW_HEIGHT = 100, 70
GRID_ROWS, GRID_COLS = 5, 7
CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOPBAR_HEIGHT - DOW_HEIGHT) // GRID_ROWS
LOCAL_TZ = timezone(timedelta(hours=8))

# 載入字型
def get_font(size):
    try: return ImageFont.truetype("msjh.ttf", size)
    except: return ImageFont.load_default()

font_title, font_week = get_font(70), get_font(44)
font_date, font_event = get_font(38), get_font(24)
font_info = get_font(22)

# API 請求
calendar_events = {}
API_KEY = 'AIzaSyAYBpOB6UoMYeAAmwTM_1KdYEzwtv6zXiE'
url = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote('dcyt122024@gmail.com')}/events"
params = {'key': API_KEY, 'timeMin': "2026-07-01T00:00:00Z", 'timeMax': "2026-08-01T00:00:00Z", 'singleEvents': 'true', 'orderBy': 'startTime'}

try:
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}") as response:
        data = json.loads(response.read().decode('utf-8'))
        for ev in data.get('items', []):
            start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date')
            day = start[:10]
            if day not in calendar_events: calendar_events[day] = []
            # 儲存時間(如果有)與標題
            time_prefix = f"{start[11:16]} " if 'dateTime' in ev.get('start', {}) else ""
            calendar_events[day].append(f"{time_prefix}{ev.get('summary', '')}")
except Exception as e: print(f"API Error: {e}")

# 繪圖
image = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 255)
draw = ImageDraw.Draw(image)
draw.text(((SCREEN_WIDTH - draw.textlength("July 2026", font=font_title)) // 2, 10), "July 2026", fill=0, font=font_title)

# 更新時間（貼底線）
gen_str = f"Generated: {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}"
draw.text((SCREEN_WIDTH - draw.textlength(gen_str, font=font_info) - 30, TOPBAR_HEIGHT - 28), gen_str, fill=160, font=font_info)
draw.line([(0, TOPBAR_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT)], fill=0, width=3)

# 格子繪製演算法
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        d = (datetime(2026, 7, 1) - timedelta(days=(calendar.monthrange(2026, 7)[0] + 1) % 7) + timedelta(days=row*7 + col)).date()
        x, y = col * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT + row * CELL_HEIGHT
        
        # 畫格線
        draw.line([(x + CELL_WIDTH, y), (x + CELL_WIDTH, y + CELL_HEIGHT)], fill=210, width=2)
        draw.line([(x, y + CELL_HEIGHT), (x + CELL_WIDTH, y + CELL_HEIGHT)], fill=210, width=2)
        
        # 繪製日期
        col_fill = 0 if d.month == 7 else 160
        draw.text((x + 15, y + 10), str(d.day), fill=col_fill, font=font_date)
        
        # 繪製事件 (優化：空間檢查更寬鬆，且強制換行確保文字不擠壓)
        y_off = y + 50
        events = calendar_events.get(d.strftime("%Y-%m-%d"), [])
        
        for event in events:
            # 強制換行處理
            max_w = CELL_WIDTH - 30
            lines = []
            if draw.textlength(event, font=font_event) <= max_w:
                lines = [event]
            else:
                # 簡單的折行邏輯
                words = event.split(' ')
                line = ""
                for w in words:
                    if draw.textlength(line + w + " ", font=font_event) < max_w:
                        line += w + " "
                    else:
                        lines.append(line)
                        line = w + " "
                lines.append(line)
            
            # 寫入文字
            for line in lines:
                if y_off < y + CELL_HEIGHT - 20:
                    draw.text((x + 15, y_off), line.strip(), fill=col_fill, font=font_event)
                    y_off += 26 # 稍微縮小行高，確保3個活動放得下
            y_off += 4

image.save("calendar.png")
print("✅ 繪製完成")
