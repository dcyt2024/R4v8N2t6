import urllib.request
from datetime import datetime, timedelta
import calendar
from icalendar import Calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 1872*1404 專屬設定 ====================
# ⚠️ 請替換成你 Google 日曆的「不公開 iCal 網址」
ICAL_URL = "https://calendar.google.com/calendar/ical/dcyt122024%40gmail.com/public/basic.ics"

SCREEN_WIDTH = 1872
SCREEN_HEIGHT = 1404
GRID_ROWS = 5
GRID_COLS = 7

# 放大留白與格子尺寸，完美利用大螢幕
TOP_MARGIN = 120   # 上方留 120px 畫大標題
CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOP_MARGIN) // GRID_ROWS

# ==================== 2. 下載並解析 Google 日曆 ====================
print("正在從 Google 抓取日曆資料...")
try:
    req = urllib.request.Request(ICAL_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        gcal = Calendar.from_ical(response.read())
except Exception as e:
    print(f"抓取日曆失敗: {e}，將使用空日曆繼續。")
    gcal = []

calendar_events = {}
today = datetime.now().date()
end_date = today + timedelta(days=35)

for component in gcal.walk():
    if component.name == "VEVENT":
        summary = str(component.get('summary', '無標題'))
        dtstart = component.get('dtstart').dt
        if isinstance(dtstart, datetime):
            event_date = dtstart.date()
        else:
            event_date = dtstart
            
        if today <= event_date <= end_date:
            date_str = event_date.strftime("%Y-%m-%d")
            if date_str not in calendar_events:
                calendar_events[date_str] = []
            calendar_events[date_str].append(summary)

# ==================== 3. 初始化黑白畫布 ====================
image = Image.new("1", (SCREEN_WIDTH, SCREEN_HEIGHT), 1)
draw = ImageDraw.Draw(image)

# 自動下載中文字型
font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
font_path = "font.ttf"
if not os.path.exists(font_path):
    print("正在下載中文字型...")
    try:
        urllib.request.urlretrieve(font_url, font_path)
    except:
        font_path = None

# 🌟 大幅放大字型大小，確保高解析度下清晰可讀
font_title = ImageFont.truetype(font_path, 48) if font_path else ImageFont.load_default()
font_week = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
font_date = ImageFont.truetype(font_path, 32) if font_path else ImageFont.load_default()
font_event = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()

# ==================== 4. 開始繪製月曆外框 ====================
now = datetime.now()
current_year = now.year
current_month = now.month

# 畫上方大標題
draw.text((40, 25), f"📅 {current_year} 年 {current_month} 月", fill=0, font=font_title)

# 畫星期欄位標題 (加大字體與間距)
weekdays = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
for i, day_name in enumerate(weekdays):
    # 計算置中位置
    x = i * CELL_WIDTH + (CELL_WIDTH // 2) - 40
    draw.text((x, 80), day_name, fill=0, font=font_week)

# 劃出一條水平分割線 (加粗至 3 像素)
draw.line([(0, TOP_MARGIN), (SCREEN_WIDTH, TOP_MARGIN)], fill=0, width=3)

# ==================== 5. 計算並填充 7x5 格子內容 ====================
first_weekday, num_days = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7 
start_of_calendar = datetime(current_year, current_month, 1) - timedelta(days=start_col)

for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        days_to_add = row * GRID_COLS + col
        cell_date = start_of_calendar + timedelta(days=days_to_add)
        cell_date_str = cell_date.strftime("%Y-%m-%d")
        
        x1 = col * CELL_WIDTH
        y1 = TOP_MARGIN + (row * CELL_HEIGHT)
        x2 = x1 + CELL_WIDTH
        y2 = y1 + CELL_HEIGHT
        
        # 畫格子的框線 (加粗邊框線)
        draw.rectangle([(x1, y1), (x2, y2)], outline=0, width=2)
        
        # 日期文字
        date_text = str(cell_date.day)
        if cell_date.month != current_month:
            date_text = f"({date_text})"
            
        # 在格子左上角寫上日期
        draw.text((x1 + 12, y1 + 12), date_text, fill=0, font=font_date)
        
        # 填充 Google 日曆活動
        if cell_date_str in calendar_events:
            y_offset = y1 + 60  # 下移留出空間給日期
            for event_title in calendar_events[cell_date_str]:
                # 如果格子空間不夠塞了，就顯示 ...
                if y_offset + 25 > y2:
                    draw.text((x1 + 15, y_offset - 5), "...", fill=0, font=font_event)
                    break
                
                # 因為格子變寬了（約 267px），行程名稱可以容納更長（大約 11 個中文字）
                if len(event_title) > 12:
                    event_title = event_title[:11] + ".."
                    
                # 畫出活動文字
                draw.text((x1 + 15, y_offset), f"• {event_title}", fill=0, font=font_event)
                y_offset += 26  # 行距放大到 26 像素

# ==================== 6. 儲存圖片 ====================
image.save("calendar.png")
print("🎉 1872*1404 高畫質墨水屏圖片生成成功！")
