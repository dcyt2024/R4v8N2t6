import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone
import calendar
from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 1. 設定與工具函式 (已修改為 A4 橫式與等比例格線) ====================
# A4 橫式 300 DPI 尺寸 (3508 x 2480)
SCREEN_WIDTH, SCREEN_HEIGHT = 3508, 2480

# 頂部欄與星期欄高度按比例放大 (原本為 100 和 70，放大約 1.87 倍)
TOPBAR_HEIGHT, DOW_HEIGHT = 187, 131

GRID_ROWS, GRID_COLS = 5, 7
CELL_WIDTH, CELL_HEIGHT = SCREEN_WIDTH // GRID_COLS, (SCREEN_HEIGHT - TOPBAR_HEIGHT - DOW_HEIGHT) // GRID_ROWS
LOCAL_TZ = timezone(timedelta(hours=8))

# 改為 RGB 色彩設定以支援橙色
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (160, 160, 160)
COLOR_LINE = (0, 160, 210)     # 藍色格線
COLOR_ORANGE = (242, 133, 0)   # 橙色 (用於標題有 [SH] 的 Event)
COLOR_WHITE = (255, 255, 255)

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

# 字型大小設定
font_title = get_scaled_font(70)
font_week = get_scaled_font(44)
font_date = get_scaled_font(38)
font_event = get_scaled_font(36) # 【Event 字體已放大至 36】
font_info = get_scaled_font(22)

# ==================== 2. 完美繪圖邏輯 (封裝) ====================
def generate_perfect_calendar(year, month, events, filename):
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), COLOR_WHITE)
    draw = ImageDraw.Draw(image)

    # 標題
    title_text = f"{calendar.month_name[month]} {year}"
    title_w = draw.textlength(title_text, font=font_title)
    draw.text(((SCREEN_WIDTH - title_w) // 2, (TOPBAR_HEIGHT - 70) // 2), title_text, fill=COLOR_BLACK, font=font_title)

    # 更新時間
    gen_time_str = f"Generated: {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}"
    info_w = draw.textlength(gen_time_str, font=font_info)
    draw.text((SCREEN_WIDTH - info_w - 30, TOPBAR_HEIGHT - 22 - 15), gen_time_str, fill=COLOR_GRAY, font=font_info)

    # 頂部粗分割線 (width=6)
    draw.line([(0, TOPBAR_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT)], fill=COLOR_BLACK, width=6)

    # 星期列與外框線
    weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day_name in enumerate(weekdays):
        w = draw.textlength(day_name, font=font_week)
        draw.text((i * CELL_WIDTH + (CELL_WIDTH - w) // 2, TOPBAR_HEIGHT + (DOW_HEIGHT - 44) // 2), day_name, fill=COLOR_BLACK, font=font_week)
        # 繪製星期列內部分割線
        if i < 6: 
            draw.line([((i + 1) * CELL_WIDTH, TOPBAR_HEIGHT), ((i + 1) * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=COLOR_LINE, width=4)
            
    # 星期列最左、最右側邊界線
    draw.line([(0, TOPBAR_HEIGHT), (0, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=COLOR_LINE, width=4)
    draw.line([(SCREEN_WIDTH - 2, TOPBAR_HEIGHT), (SCREEN_WIDTH - 2, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=COLOR_LINE, width=4)
    
    # 星期列底部粗分割線 (width=6)
    draw.line([(0, TOPBAR_HEIGHT + DOW_HEIGHT), (SCREEN_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT)], fill=COLOR_BLACK, width=6)

    # 智慧型英文不中斷折行函式 (此處只負責切分字串，對齊由下方繪圖 X 座標控制)
    def split_event_smart(time_prefix, event_title, font, max_width, time_width):
        full_text = f"{time_prefix}{event_title}".strip()
        
        # 如果整行塞得下，直接回傳單行，且不需要偏移第二行
        if draw.textlength(full_text, font=font) <= max_width:
            return [(full_text, False)]
        
        # 進行單字/中文字元拆分
        words = []
        current_word = ""
        for char in event_title:
            if char.isspace():
                if current_word:
                    words.append(current_word)
                    current_word = ""
                words.append(" ")
            elif ord(char) < 128:  # 英文/半形字元
                current_word += char
            else:                  # 中文字元獨立切分
                if current_word:
                    words.append(current_word)
                    current_word = ""
                words.append(char)
        if current_word:
            words.append(current_word)
            
        # 第一行建構 (含時間)
        line1 = time_prefix
        word_idx = 0
        while word_idx < len(words):
            next_word = words[word_idx]
            test_line = line1 + next_word
            if draw.textlength(test_line, font=font) <= max_width:
                line1 += next_word
                word_idx += 1
            else:
                break
        
        # 第二行建構 (不含時間，僅含剩餘標題)
        line2 = ""
        has_added_content = False
        # 第二行的可用寬度需扣除時間的寬度，才能在右移後不爆框
        line2_max_width = max_width - time_width
        
        while word_idx < len(words):
            next_word = words[word_idx]
            if next_word == " " and not has_added_content:
                word_idx += 1
                continue
                
            test_line = line2 + next_word
            if draw.textlength(test_line, font=font) <= line2_max_width:
                line2 += next_word
                has_added_content = True
                word_idx += 1
            else:
                # 超過可用長度，切斷並加上省略號
                while draw.textlength(line2 + "..", font=font) > line2_max_width and len(line2) > 0:
                    line2 = line2[:-1]
                line2 += ".."
                break
                
        # 回傳格式：[(第一行內容, 是否需要右移), (第二行內容, 是否需要右移)]
        return [(line1.rstrip(), False), (line2.strip(), True)]

    first_weekday, _ = calendar.monthrange(year, month)
    start_col = (first_weekday + 1) % 7
    start_of_calendar = datetime(year, month, 1) - timedelta(days=start_col)

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell_date = (start_of_calendar + timedelta(days=row * GRID_COLS + col)).date()
            x1, y1 = col * CELL_WIDTH, TOPBAR_HEIGHT + DOW_HEIGHT + (row * CELL_HEIGHT)
            x2, y2 = x1 + CELL_WIDTH, y1 + CELL_HEIGHT
            
            # 【補齊最左與最右格線】
            # 每格右側線 (最後一格 col=6 時，x2 即為最右邊界，這樣就能畫出最右側邊框)
            draw.line([(x2, y1), (x2, y2)], fill=COLOR_LINE, width=4)
            # 每格底部線
            draw.line([(x1, y2), (x2, y2)], fill=COLOR_LINE, width=4)
            # 第一格額外畫最左邊界線
            if col == 0:
                draw.line([(x1, y1), (x1, y2)], fill=COLOR_LINE, width=4)
            
            # 日期顏色
            date_color = COLOR_BLACK if cell_date.month == month else COLOR_GRAY
            draw.text((x1 + 15, y1 + 12), str(cell_date.day), fill=date_color, font=font_date)
            
            if cell_date.strftime("%Y-%m-%d") in events:
                y_offset = y1 + 65 
                for time_prefix, event_title in events[cell_date.strftime("%Y-%m-%d")]:
                    
                    # 判斷標題是否含有 "[SH]"
                    if "[SH]" in event_title:
                        event_color = COLOR_ORANGE
                    else:
                        event_color = COLOR_BLACK if cell_date.month == month else COLOR_GRAY
                    
                    # 精準計算時間寬度
                    time_width = draw.textlength(time_prefix, font=font_event) if time_prefix else 0
                    
                    # 呼叫拆行函式
                    lines_info = split_event_smart(time_prefix, event_title, font_event, CELL_WIDTH - 30, time_width)
                    
                    for text_line, should_indent in lines_info:
                        if not text_line:
                            continue
                        # 36pt 字體高約 42 像素，預留安全間距
                        if y_offset + 42 > y2 - 8: 
                            break
                        
                        # 關鍵對齊修改：如果是第二行，X 座標直接加上時間寬度（完美像素級對齊）
                        draw_x = x1 + 15 + time_width if should_indent else x1 + 15
                        
                        draw.text((draw_x, y_offset), text_line, fill=event_color, font=font_event)
                        y_offset += 42
                    y_offset += 6
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
                end = ev.get('end', {}).get('dateTime') or ev.get('end', {}).get('date')
                day = start[:10]
                if day not in events: events[day] = []
                
                # 同時處理開始與結束時間
                time_str = ""
                if 'dateTime' in ev.get('start', {}):
                    t1 = start[11:16]
                    t2 = end[11:16] if end else ""
                    time_str = f"{t1}-{t2} " if t2 else f"{t1} "
                
                events[day].append((time_str, ev.get('summary', '(No title)')))
    except Exception as e: print(f"API Error: {e}")
    
    generate_perfect_calendar(y, m, events, f"calendar{i+1}.png")
    print(f"✅ {y}-{m} 完美生成: calendar{i+1}.png")
