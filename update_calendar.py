import urllib.request, urllib.parse, json, os, calendar
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

# ==================== 1. 核心繪圖函數 ====================
def generate_one_month(year, month, events, filename):
    SCREEN_WIDTH, SCREEN_HEIGHT = 1872, 1404
    TOPBAR_HEIGHT, DOW_HEIGHT = 100, 70
    GRID_ROWS, GRID_COLS = 5, 7
    CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
    CELL_HEIGHT = (SCREEN_HEIGHT - TOPBAR_HEIGHT - DOW_HEIGHT) // GRID_ROWS
    
    # 載入字型
    font_path = "msjh.ttf"
    f_title = ImageFont.truetype(font_path, 70) if os.path.exists(font_path) else ImageFont.load_default()
    f_date = ImageFont.truetype(font_path, 38) if os.path.exists(font_path) else ImageFont.load_default()
    f_event = ImageFont.truetype(font_path, 24) if os.path.exists(font_path) else ImageFont.load_default()

    image = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 255)
    draw = ImageDraw.Draw(image)
    
    # 繪製標題
    title_text = f"{year}-{month}"
    draw.text(((SCREEN_WIDTH - draw.textlength(title_text, font=f_title)) // 2, 10), title_text, fill=0, font=f_title)
    draw.line([(0, TOPBAR_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT)], fill=0, width=3)

    # 繪製格子與日期
    start_of_month = datetime(year, month, 1)
    start_col = (start_of_month.weekday() + 1) % 7
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            d = (start_of_month - timedelta(days=start_col) + timedelta(days=row*7 + col)).date()
            if d.month == month:
                x, y = col * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT + row * CELL_HEIGHT
                draw.text((x + 15, y + 10), str(d.day), fill=0, font=f_date)
                
                # 顯示該日期的前 3 個活動
                y_off = y + 55
                for time_pref, title in events.get(d.strftime("%Y-%m-%d"), [])[:3]:
                    draw.text((x + 15, y_off), f"{time_pref}{title}"[:35], fill=0, font=f_event)
                    y_off += 30
    image.save(filename)

# ==================== 2. 主循環：生成接下來 6 個月 ====================
API_KEY = 'AIzaSyAYBpOB6UoMYeAAmwTM_1KdYEzwtv6zXiE'
CALENDAR_ID = 'dcyt122024@gmail.com'

for i in range(6):
    target_date = datetime.now() + timedelta(days=i*30)
    y, m = target_date.year, target_date.month
    
    # 抓取 API 資料
    events = {}
    try:
        t_min = f"{y}-{m:02d}-01T00:00:00Z"
        next_m = m + 1 if m < 12 else 1
        next_y = y if m < 12 else y + 1
        t_max = f"{next_y}-{next_m:02d}-01T00:00:00Z"
        
        url = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(CALENDAR_ID)}/events?key={API_KEY}&timeMin={t_min}&timeMax={t_max}&singleEvents=true"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            for ev in data.get('items', []):
                start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date')
                day = start[:10]
                if day not in events: events[day] = []
                time_pref = f"{start[11:16]} " if 'dateTime' in ev.get('start', {}) else ""
                events[day].append((time_pref, ev.get('summary', '')))
    except: pass
    
    # 生成檔案 calendar1.png 到 calendar6.png
    generate_one_month(y, m, events, f"calendar{i+1}.png")
    print(f"✅ calendar{i+1}.png 已生成")
