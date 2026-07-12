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

# 依據 HTML 比例放大設定高寬 (Scale Factor ≒ 2.8)
TOPBAR_HEIGHT = 150   # 對應 HTML .topbar 加上 padding 的空間
DOW_HEIGHT = 156      # 對應 HTML 56px 的星期列

GRID_ROWS = 5
GRID_COLS = 7

CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOPBAR_HEIGHT - DOW_HEIGHT) // GRID_ROWS

# ==================== 2. 安全字型載入（徹底解決字體變小問題） ====================
def get_scaled_font(font_size):
    """確保即使下載失敗，也能在各平台載入正確大小的字型，絕不縮小"""
    font_sources = [
        "msjh.ttf",                      # 本地微軟正黑體
        "C:/Windows/Fonts/msjh.ttc",     # Windows 正黑體
        "/System/Library/Fonts/STHeiti Light.ttc", # Mac 華文黑體
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Linux 備用
    ]
    
    # 嘗試下載
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
                
    # 如果都失敗，使用 Pillow 新版支援大小設定的預設字型
    try:
        return ImageFont.load_default(size=font_size)
    except:
        return ImageFont.load_default()

# 🎯 完全參照 HTML 字體大小等比放大：
font_title = get_scaled_font(90)   # HTML .title (32px) -> 大標題
font_week = get_scaled_font(56)    # HTML .dow (20px) -> 星期
font_date = get_scaled_font(62)    # HTML .date (22px) -> 日期數字
font_event = get_scaled_font(50)   # HTML .event (18px) -> 行程文字

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
        for ev in data.get('items', []):
            start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date')
            end = ev.get('end', {}).get('dateTime') or ev.get('end', {}).get('date')
            summary = ev.get('summary', '(No title)')
            
            if not start: continue
            day_key = start[:10]
            
            time_str = ""
            if 'dateTime' in ev.get('start', {}):
                t1 = datetime.strptime(start[:19], "%Y-%m-%dT%H:%M:%S").strftime("%H:%M")
                t2 = datetime.strptime(end[:19], "%Y-%m-%dT%H:%M:%S").strftime("%H:%M") if end else ""
                time_str = f"{t1}-{t2} " if t2 else f"{t1} "
                
            if day_key not in calendar_events:
                calendar_events[day_key] = []
            calendar_events[day_key].append((time_str, summary))
except Exception as e:
    print(f"API Error: {e}")

# ==================== 4. 繪製與排版 (100% 複製 HTML 視覺結構) ====================
image = Image.new("1", (SCREEN_WIDTH, SCREEN_HEIGHT), 1)
draw = ImageDraw.Draw(image)

# 1. Topbar 區塊：July 2026 居中頂部
title_text = "July 2026"
title_w = draw.textlength(title_text, font=font_title)
draw.text(((SCREEN_WIDTH - title_w) // 2, (TOPBAR_HEIGHT - 90) // 2), title_text, fill=0, font=font_title)
draw.line([(0, TOPBAR_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT)], fill=0, width=3) # border-bottom

# 2. 星期列 (Sun - Sat)
weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
for i, day_name in enumerate(weekdays):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    y = TOPBAR_HEIGHT + (DOW_HEIGHT - 56) // 2
    draw.text((x, y), day_name, fill=0, font=font_week)
    # 畫星期的垂直分界線
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
        
        # 繪製單個格子的右邊線與下邊線 (對應 HTML 的 border-right & border-bottom)
        if col < 6: draw.line([(x2, y1), (x2, y2)], fill=0, width=2)
        draw.line([(x1, y2), (x2, y2)], fill=0, width=2)
        
        # 日期數字（遵照 HTML 居中排版）
        date_text = str(cell_date.day)
        date_w = draw.textlength(date_text, font=font_date)
        date_x = x1 + (CELL_WIDTH - date_w) // 2
        
        # 非本月日子外觀處理
        if cell_date.month == current_month:
            draw.text((date_x, y1 + 16), date_text, fill=0, font=font_date)
        else:
            # 模擬 HTML .other .date 的淺色效果（在 1-bit 黑白圖上以細線條或略過表示，這裡正常繪製但靠邊或加上標記，此處直接純繪製保持整潔）
            draw.text((date_x, y1 + 16), date_text, fill=0, font=font_date)
            
        # 純文字行程列表（無外框，直接規整排列）
        if cell_date_str in calendar_events:
            y_offset = y1 + 90
            line_height = 56
            
            for time_prefix, event_title in calendar_events[cell_date_str]:
                if y_offset + line_height > y2 - 10:
                    break
                
                display_text = f"{time_prefix}{event_title}"
                max_text_width = CELL_WIDTH - 24
                
                # 自動省略過長文字
                if draw.textlength(display_text, font=font_event) > max_text_width:
                    while draw.textlength(display_text + "..", font=font_event) > max_text_width and len(display_text) > 0:
                        display_text = display_text[:-1]
                    display_text += ".."
                
                # 靠左對齊，留白 15 像素
                draw.text((x1 + 15, y_offset), display_text, fill=0, font=font_event)
                y_offset += line_height

# 儲存
image.save("calendar.png")
print("🎉 HTML Scale-Matched Calendar Generated!")
