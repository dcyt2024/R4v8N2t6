import urllib.request
from datetime import datetime, timedelta
import calendar
from icalendar import Calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 1872*1404 高級排版設定 ====================
# ⚠️ 請替換成你 Google 日曆的「不公開 iCal 網址」
ICAL_URL = "https://calendar.google.com/calendar/ical/dcyt122024%40gmail.com/public/basic.ics"

SCREEN_WIDTH = 1872
SCREEN_HEIGHT = 1404
GRID_ROWS = 5
GRID_COLS = 7

TOP_MARGIN = 160   # 加大上方留白，讓標題更優雅
CELL_WIDTH = SCREEN_WIDTH // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - TOP_MARGIN) // GRID_ROWS

# ==================== 2. 下載並解析 Google 日曆 ====================
print("正在從 Google 抓取日曆資料...")
try:
    req = urllib.request.Request(ICAL_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        gcal = Calendar.from_ical(response.read())
except Exception as e:
    print(f"抓取日曆失敗: {e}")
    gcal = []

calendar_events = {}
today = datetime.now().date()
end_date = today + timedelta(days=35)

for component in gcal.walk():
    if component.name == "VEVENT":
        summary = str(component.get('summary', '無標題'))
        dtstart = component.get('dtstart').dt
        
        # 🌟 提取時間邏輯
        time_str = "" # 預設全天行程不顯示時間
        if isinstance(dtstart, datetime):
            event_date = dtstart.date()
            # 轉換為在地時間（這裡簡單取時分，例如 10:00）
            time_str = dtstart.strftime("%H:%M ")
        else:
            event_date = dtstart
            
        if today <= event_date <= end_date:
            date_str = event_date.strftime("%Y-%m-%d")
            if date_str not in calendar_events:
                calendar_events[date_str] = []
            # 儲存結構變成 (時間, 標題)
            calendar_events[date_str].append((time_str, summary))

# ==================== 3. 初始化畫布與下載「思源黑體」 ====================
image = Image.new("1", (SCREEN_WIDTH, SCREEN_HEIGHT), 1)
draw = ImageDraw.Draw(image)

# 🌟 改用下載高質感的繁體中文字型（思源黑體），徹底解決豆腐塊亂碼問題
font_url = "https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/TraditionalChinese/SourceHanSansTC-Regular.otf"
font_path = "SourceHanSansTC-Regular.otf"
if not os.path.exists(font_path):
    print("正在下載思源繁體中文字型（較大，請稍候）...")
    try:
        # 如果思源黑體太慢，改用微軟正黑體相容字型
        backup_url = "https://github.com/asFont/Fonts/raw/master/ttf/Microsoft-YaHei-Regular.ttf"
        urllib.request.urlretrieve(backup_url, font_path)
    except Exception as e:
        print(f"字型下載失敗: {e}")
        font_path = None

# 精緻字體大小設定
font_title = ImageFont.truetype(font_path, 54) if font_path else ImageFont.load_default()
font_week = ImageFont.truetype(font_path, 26) if font_path else ImageFont.load_default()
font_date = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
font_event_time = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default() # 時間用細字或稍小
font_event_title = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()

# ==================== 4. 繪製精美頂部 ====================
now = datetime.now()
current_year = now.year
current_month = now.month

# 畫上方主標題（大氣排版）
draw.text((50, 40), f"{current_year} 年 {current_month} 月", fill=0, font=font_title)

# 畫星期欄位（精準計算置中）
weekdays = ["SUN 星期日", "MON 星期一", "TUE 星期二", "WED 星期三", "THU 星期四", "FRI 星期五", "SAT 星期六"]
for i, day_name in enumerate(weekdays):
    w = draw.textlength(day_name, font=font_week)
    x = i * CELL_WIDTH + (CELL_WIDTH - w) // 2
    draw.text((x, 115), day_name, fill=0, font=font_week)

# 頂部粗裝飾線
draw.line([(0, TOP_MARGIN), (SCREEN_WIDTH, TOP_MARGIN)], fill=0, width=4)

# ==================== 5. 繪製日曆格子與行程 ====================
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
        
        # 畫細緻的灰色質感邊框（墨水屏一般用細線較美觀）
        draw.rectangle([(x1, y1), (x2, y2)], outline=0, width=1)
        
        # 日期標籤
        date_text = str(cell_date.day)
        # 如果不是本月，字體用括號淡化
        if cell_date.month != current_month:
            date_text = f"[{date_text}]"
            
        # 右上角對齊日期
        text_w = draw.textlength(date_text, font=font_date)
        draw.text((x2 - text_w - 15, y1 + 12), date_text, fill=0, font=font_date)
        
        # 🌟 填入帶有時間的行程
        if cell_date_str in calendar_events:
            # 排序行程（讓有時間的排在前面，全天排後面）
            sorted_events = sorted(calendar_events[cell_date_str], key=lambda x: x[0] if x[0] else "24:00")
            
            y_offset = y1 + 55  # 從日期下方開始排
            for time_prefix, event_title in sorted_events:
                if y_offset + 28 > y2:
                    draw.text((x1 + 15, y_offset), "...", fill=0, font=font_event_title)
                    break
                
                # 建立漂亮的顯示格式： "10:00 團隊會議"
                display_text = f"{time_prefix}{event_title}"
                
                # 自動截斷太長的字
                if len(display_text) > 13:
                    display_text = display_text[:12] + ".."
                
                # 繪製行程
                draw.text((x1 + 15, y_offset), display_text, fill=0, font=font_event_title)
                y_offset += 28  # 行高舒適留白

# ==================== 6. 儲存圖片 ====================
image.save("calendar.png")
print("🎉 高質感、帶時間的墨水屏圖片生成成功！")
