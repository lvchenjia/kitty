#!/usr/bin/env python3
import sys
import os
import time
import select
import tty
import termios
import struct
import zlib
import base64
import re

# ==============================================================================
# 🎨 640x640 高级交互式像素画板 (Kitty Pixel Painter)
# ==============================================================================
WIDTH, HEIGHT = 640, 640
BUFFER_SIZE = WIDTH * HEIGHT * 4

# SGR 鼠标协议正则表达式
# 格式: \x1b[<button;x;y;M (按下/拖拽) 或 \x1b[<button;x;y;m (释放)
sgr_pattern = re.compile(r'\x1b\[<(\d+);(\d+);(\d+)([Mm])')

# ==============================================================================
# 🔠 5x7 极简像素字模库 (纯手工打造，支持完整大写英文字母与基础符号)
# ==============================================================================
FONT = {
    'A': [0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11],
    'B': [0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E],
    'C': [0x0F, 0x10, 0x10, 0x10, 0x10, 0x10, 0x0F],
    'D': [0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E],
    'E': [0x1F, 0x10, 0x10, 0x1C, 0x10, 0x10, 0x1F],
    'F': [0x1F, 0x10, 0x10, 0x1C, 0x10, 0x10, 0x10],
    'G': [0x0F, 0x10, 0x10, 0x17, 0x11, 0x11, 0x0F],
    'H': [0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11],
    'I': [0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E],
    'J': [0x0F, 0x04, 0x04, 0x04, 0x04, 0x14, 0x0C],
    'K': [0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11],
    'L': [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F],
    'M': [0x11, 0x1B, 0x15, 0x11, 0x11, 0x11, 0x11],
    'N': [0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11],
    'O': [0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
    'P': [0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10],
    'Q': [0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D],
    'R': [0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11],
    'S': [0x0F, 0x10, 0x0E, 0x01, 0x01, 0x11, 0x0E],
    'T': [0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04],
    'U': [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
    'V': [0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04],
    'W': [0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11],
    'X': [0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11],
    'Y': [0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04],
    'Z': [0x1F, 0x02, 0x04, 0x08, 0x10, 0x10, 0x1F],
    '0': [0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E],
    '1': [0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E],
    '2': [0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F],
    '3': [0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E],
    '4': [0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02],
    '5': [0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E],
    '6': [0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E],
    '7': [0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08],
    '8': [0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E],
    '9': [0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    '-': [0x00, 0x00, 0x00, 0x1C, 0x00, 0x00, 0x00],
    ':': [0x00, 0x08, 0x00, 0x00, 0x00, 0x08, 0x00],
    '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08],
    '|': [0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04],
}

# ==============================================================================
# 🎨 核心绘图基础 API (RGBA 像素缓冲区操作)
# ==============================================================================
def draw_rect(buffer, x0, y0, x1, y1, color):
    """绘制填充矩形"""
    x0, y0 = max(0, min(WIDTH-1, int(x0))), max(0, min(HEIGHT-1, int(y0)))
    x1, y1 = max(0, min(WIDTH-1, int(x1))), max(0, min(HEIGHT-1, int(y1)))
    for y in range(y0, y1 + 1):
        row_offset = y * WIDTH * 4
        for x in range(x0, x1 + 1):
            idx = row_offset + x * 4
            buffer[idx]     = color[0]
            buffer[idx+1]   = color[1]
            buffer[idx+2]   = color[2]
            buffer[idx+3]   = 255

def draw_rect_outline(buffer, x0, y0, x1, y1, color, thickness=1):
    """绘制矩形描边"""
    draw_rect(buffer, x0, y0, x1, y0 + thickness - 1, color) # 上边
    draw_rect(buffer, x0, y1 - thickness + 1, x1, y1, color) # 下边
    draw_rect(buffer, x0, y0, x0 + thickness - 1, y1, color) # 左边
    draw_rect(buffer, x1 - thickness + 1, y0, x1, y1, color) # 右边

def draw_circle(buffer, cx, cy, r, color):
    """绘制填充圆形"""
    x0 = max(0, cx - r)
    x1 = min(WIDTH - 1, cx + r)
    y0 = max(0, cy - r)
    y1 = min(HEIGHT - 1, cy + r)
    r2 = r * r
    for y in range(y0, y1 + 1):
        dy2 = (y - cy) * (y - cy)
        row_offset = y * WIDTH * 4
        for x in range(x0, x1 + 1):
            dx2 = (x - cx) * (x - cx)
            if dx2 + dy2 <= r2:
                idx = row_offset + x * 4
                buffer[idx]     = color[0]
                buffer[idx+1]   = color[1]
                buffer[idx+2]   = color[2]
                buffer[idx+3]   = 255

def draw_circle_outline(buffer, cx, cy, r, color, thickness=2):
    """绘制圆形描边"""
    x0 = max(0, cx - r - thickness)
    x1 = min(WIDTH - 1, cx + r + thickness)
    y0 = max(0, cy - r - thickness)
    y1 = min(HEIGHT - 1, cy + r + thickness)
    r_inner = r - thickness
    r2_inner = r_inner * r_inner
    r2_outer = r * r
    for y in range(y0, y1 + 1):
        dy2 = (y - cy) * (y - cy)
        row_offset = y * WIDTH * 4
        for x in range(x0, x1 + 1):
            dx2 = (x - cx) * (x - cx)
            dist2 = dx2 + dy2
            if r2_inner < dist2 <= r2_outer:
                idx = row_offset + x * 4
                buffer[idx]     = color[0]
                buffer[idx+1]   = color[1]
                buffer[idx+2]   = color[2]
                buffer[idx+3]   = 255

def draw_char(buffer, cx, cy, char, color, scale=2):
    """利用字模绘制单个像素字符"""
    bitmap = FONT.get(char.upper(), FONT[' '])
    for row_idx, row in enumerate(bitmap):
        for col_idx in range(5):
            if (row >> (4 - col_idx)) & 1:
                # 按照缩放因子绘制小矩形块
                draw_rect(buffer, cx + col_idx * scale, cy + row_idx * scale,
                          cx + (col_idx + 1) * scale - 1, cy + (row_idx + 1) * scale - 1, color)

def draw_string(buffer, x, y, text, color, scale=2, spacing=2):
    """绘制字符串"""
    curr_x = x
    for char in text:
        draw_char(buffer, curr_x, y, char, color, scale)
        curr_x += 5 * scale + spacing

# ==============================================================================
# 📦 PNG 压缩编码与 Kitty 图像协议传输
# ==============================================================================
def encode_png(rgba_data, width, height):
    """内存级 PNG 无损高压编码器 (无外部依赖)"""
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr = b'IHDR' + ihdr_data
    ihdr_chunk = struct.pack(">I", len(ihdr) - 4) + ihdr + struct.pack(">I", zlib.crc32(ihdr))

    row_bytes = width * 4
    scanlines = [b'\x00' + rgba_data[r * row_bytes : (r + 1) * row_bytes] for r in range(height)]
    
    # 极速无损压缩 (level=1)
    compressed_data = zlib.compress(b''.join(scanlines), level=1)
    idat = b'IDAT' + compressed_data
    idat_chunk = struct.pack(">I", len(idat) - 4) + idat + struct.pack(">I", zlib.crc32(idat))

    iend = b'IEND'
    iend_chunk = struct.pack(">I", 0) + iend + struct.pack(">I", zlib.crc32(iend))

    return b'\x89PNG\r\n\x1a\n' + ihdr_chunk + idat_chunk + iend_chunk

def send_image_via_kitty(png_data, target_cols, target_rows, image_id=10):
    """利用 Kitty 图像协议发送 PNG 数据到指定视口"""
    b64_data = base64.b64encode(png_data).decode('ascii')
    chunk_size = 4096
    
    # 清理历史帧纹理，避免显存泄漏与排版残留
    sys.stdout.write(f"\033_Ga=d,i={image_id}\033\\")
    
    if len(b64_data) <= chunk_size:
        sys.stdout.write(f"\033_Gf=100,a=T,i={image_id},q=2,c={target_cols},r={target_rows},m=0;{b64_data}\033\\\n")
    else:
        sys.stdout.write(f"\033_Gf=100,a=T,i={image_id},q=2,c={target_cols},r={target_rows},m=1;{b64_data[:chunk_size]}\033\\")
        idx = chunk_size
        while idx < len(b64_data) - chunk_size:
            sys.stdout.write(f"\033_Gm=1;{b64_data[idx:idx+chunk_size]}\033\\")
            idx += chunk_size
        sys.stdout.write(f"\033_Gm=0;{b64_data[idx:]}\033\\\n")
    sys.stdout.flush()

# ==============================================================================
# 🎨 调色板颜色定义
# ==============================================================================
COLORS = [
    (229, 57, 53),     # 0: 红色
    (251, 140, 0),     # 1: 橙色
    (253, 216, 53),    # 2: 黄色
    (76, 175, 80),     # 3: 绿色
    (0, 172, 193),     # 4: 青蓝色
    (142, 36, 170),    # 5: 紫色
    (33, 33, 33),      # 6: 深炭灰 (黑色)
    (255, 255, 255),   # 7: 纯白
]

# ==============================================================================
# 🕹️ 主运行逻辑
# ==============================================================================
def main():
    # 1. 隐藏光标，清屏，开启鼠标追踪 (允许 SGR 鼠标报告)
    sys.stdout.write("\033[?25l\033[2J\033[H")
    sys.stdout.write("\033[?1000h\033[?1002h\033[?1006h")
    sys.stdout.flush()

    # 2. 将控制台置于 Raw (非阻塞且无回显) 模式
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    # 3. 初始化程序数据状态
    grid_size = 16
    # 16x16 画板画布，默认纯白
    grid_data = [[(255, 255, 255) for _ in range(grid_size)] for _ in range(grid_size)]
    selected_color_idx = 0
    undo_stack = []
    
    # 状态通知管理器
    status_message = "CLICK GRID TO PAINT | CLICK COLOR TO SELECT"
    status_expiry = 0.0

    # 缓存帧缓冲区内存
    frame_buffer = bytearray(BUFFER_SIZE)

    # 撤销压栈辅助函数
    def push_undo():
        nonlocal undo_stack
        grid_copy = [row[:] for row in grid_data]
        undo_stack.append(grid_copy)
        if len(undo_stack) > 20:
            undo_stack.pop(0)

    # 状态消息设置辅助函数
    def set_status(msg, duration=1.5):
        nonlocal status_message, status_expiry
        status_message = msg
        status_expiry = time.time() + duration

    # 4. 点击判定与交互逻辑
    def handle_click(px, py, is_press, is_drag):
        nonlocal selected_color_idx, grid_data

        # (A) 判定是否在 16x16 像素网格区域内 (x: 80~560, y: 80~560)
        if 80 <= px < 560 and 80 <= py < 560:
            grid_c = (px - 80) // 30
            grid_r = (py - 80) // 30
            if 0 <= grid_c < grid_size and 0 <= grid_r < grid_size:
                current_color = COLORS[selected_color_idx]
                if grid_data[grid_r][grid_c] != current_color:
                    if is_press and not is_drag:
                        # 新的一笔按下瞬间，记录撤销历史
                        push_undo()
                    grid_data[grid_r][grid_c] = current_color

        # 以下按钮只在鼠标“首次按下(Press)”时触发，拖拽时不触发
        if is_press and not is_drag:
            # (B) 判定是否在底部的调色板圆圈区域 (y: 570~620, cx_i: 145 + i*50)
            if 570 <= py < 620:
                for i in range(len(COLORS)):
                    cx = 145 + i * 50
                    cy = 595
                    # 半径 18 像素
                    if (px - cx)**2 + (py - cy)**2 <= 18**2:
                        selected_color_idx = i
                        set_status(f"SELECTED COLOR - {i+1}")
                        break

            # (C) 判定左侧功能按钮区 (x: 10~70)
            if 10 <= px < 70:
                # 撤销 UNDO (y: 190~230)
                if 190 <= py < 230:
                    if undo_stack:
                        grid_data = undo_stack.pop()
                        set_status("UNDO APPLIED!", 1.2)
                    else:
                        set_status("NOTHING TO UNDO!", 1.0)
                # 清空 CLEAR (y: 250~290)
                elif 250 <= py < 290:
                    push_undo()
                    grid_data = [[(255, 255, 255) for _ in range(grid_size)] for _ in range(grid_size)]
                    set_status("CANVAS CLEARED!", 1.2)
                # 保存 SAVE (y: 310~350)
                elif 310 <= py < 350:
                    try:
                        # 导出 256x256 高品质 PNG 图像
                        save_width, save_height = 256, 256
                        save_buffer = bytearray(save_width * save_height * 4)
                        for r in range(grid_size):
                            for c in range(grid_size):
                                color = grid_data[r][c]
                                # 每个网格像素拉伸为 16x16 像素块
                                for py_block in range(16):
                                    for px_block in range(16):
                                        sx = c * 16 + px_block
                                        sy = r * 16 + py_block
                                        s_idx = (sy * save_width + sx) * 4
                                        save_buffer[s_idx]     = color[0]
                                        save_buffer[s_idx+1]   = color[1]
                                        save_buffer[s_idx+2]   = color[2]
                                        save_buffer[s_idx+3]   = 255
                        png_file_data = encode_png(save_buffer, save_width, save_height)
                        with open("artwork.png", "wb") as f:
                            f.write(png_file_data)
                        set_status("SAVED TO ARTWORK.PNG!", 3.0)
                    except Exception as e:
                        set_status(f"SAVE ERROR: {str(e)[:15]}", 2.0)

            # (D) 判定右侧功能按钮区 (x: 570~630)
            if 570 <= px < 630:
                # 填充 FILL (y: 190~230)
                if 190 <= py < 230:
                    push_undo()
                    fill_color = COLORS[selected_color_idx]
                    grid_data = [[fill_color for _ in range(grid_size)] for _ in range(grid_size)]
                    set_status("CANVAS FILLED!", 1.2)
                # 退出 EXIT (y: 250~290)
                elif 250 <= py < 290:
                    return True # 退出标志
                # 信息 INFO (y: 310~350)
                elif 310 <= py < 350:
                    set_status("KITTY PIXEL PAINTER V1.0", 3.0)

        return False

    try:
        # 记录拖拽点击状态
        mouse_is_down = False
        
        while True:
            # 5. 动态检测终端尺寸并居中图像视口
            try:
                columns, rows = os.get_terminal_size()
            except OSError:
                columns, rows = 80, 40

            # 约束界面大小以获得接近完美的物理方形比例
            target_rows = min(rows - 6, 26)
            if target_rows < 12:
                target_rows = 12
            target_cols = target_rows * 2 # 宽字符补偿 2:1 比例

            start_row = 3
            start_col = max(1, (columns - target_cols) // 2)

            # 6. 非阻塞轮询读取 Standard Input (20ms 级低开销等待)
            rlist, _, _ = select.select([sys.stdin], [], [], 0.02)
            
            raw_input_data = ""
            if rlist:
                # 读取全部缓冲流数据
                raw_input_data = sys.stdin.read(1)
                if raw_input_data == '\x1b':
                    seq = '\x1b'
                    while select.select([sys.stdin], [], [], 0.002)[0]:
                        seq += sys.stdin.read(1)
                    raw_input_data = seq
                else:
                    while select.select([sys.stdin], [], [], 0.0)[0]:
                        raw_input_data += sys.stdin.read(1)

            # 7. 检测键盘强制退出热键 ('q'、'Q' 或 Ctrl+C)
            if raw_input_data:
                # 确保排除 SGR 鼠标序列自身的 \x1b
                if 'q' in raw_input_data or 'Q' in raw_input_data or '\x03' in raw_input_data or ( '\x1b' in raw_input_data and '\x1b[<' not in raw_input_data ):
                    break

            # 8. 解析 SGR 鼠标动作数据并触发交互
            matches = sgr_pattern.findall(raw_input_data)
            should_exit = False
            for match in matches:
                button = int(match[0])
                cx = int(match[1])
                cy = int(match[2])
                is_press_event = match[3] == 'M'

                # 映射物理网格坐标
                relative_cx = cx - start_col
                relative_cy = cy - start_row
                
                # 只要坐标落在指定范围内，计算相应的百分比映射
                if 0 <= relative_cx < target_cols and 0 <= relative_cy < target_rows:
                    rx = (relative_cx + 0.5) / target_cols
                    ry = (relative_cy + 0.5) / target_rows
                    
                    px = int(rx * WIDTH)
                    py = int(ry * HEIGHT)

                    # 鼠标左键按下 & 拖拽处理
                    if button == 0:
                        if is_press_event:
                            mouse_is_down = True
                            should_exit = handle_click(px, py, is_press=True, is_drag=False)
                        else:
                            mouse_is_down = False
                    elif button == 32: # 左键拖拽中
                        if mouse_is_down and is_press_event:
                            should_exit = handle_click(px, py, is_press=True, is_drag=True)

            if should_exit:
                break

            # 9. 状态文字自动衰减还原为默认说明
            if time.time() > status_expiry:
                status_message = "CLICK GRID TO PAINT | CLICK COLOR TO SELECT"

            # 10. UI 界面图层合成与渲染
            # (A) 填充底板金属灰背景色 (#121216)
            bg_color = (18, 18, 22)
            for y in range(HEIGHT):
                row_offset = y * WIDTH * 4
                for x in range(WIDTH):
                    idx = row_offset + x * 4
                    frame_buffer[idx]     = bg_color[0]
                    frame_buffer[idx+1]   = bg_color[1]
                    frame_buffer[idx+2]   = bg_color[2]
                    frame_buffer[idx+3]   = 255

            # (B) 绘制顶部控制面板顶栏 (#1e1e26) 与分割霓虹边框
            draw_rect(frame_buffer, 0, 0, WIDTH - 1, 60, (30, 30, 38))
            draw_rect(frame_buffer, 0, 60, WIDTH - 1, 62, (0, 172, 193)) # 青色霓虹线

            # (C) 绘制精美标题 "KITTY PIXEL PAINTER" 与动态状态文字
            draw_string(frame_buffer, 160, 12, "KITTY PIXEL PAINTER", (0, 220, 255), scale=3, spacing=1)
            # 状态消息：根据剩余时间赋予不同高亮颜色
            status_color = (255, 255, 255)
            if status_message.startswith("ARTWORK SAVED"):
                status_color = (76, 175, 80) # 绿色成功高亮
            elif status_message.startswith("UNDO") or status_message.startswith("CANVAS"):
                status_color = (253, 216, 53) # 黄色状态高亮
            draw_string(frame_buffer, 320 - (len(status_message) * 6) // 2, 42, status_message, status_color, scale=1, spacing=1)

            # (D) 绘制画板网格边框及方格像素内容
            draw_rect_outline(frame_buffer, 76, 76, 564, 564, (60, 60, 75), thickness=4) # 边框
            # 绘制 1px 间距的网格暗部背景
            draw_rect(frame_buffer, 80, 80, 560, 560, (40, 40, 40))
            for r in range(grid_size):
                for c in range(grid_size):
                    cell_color = grid_data[r][c]
                    # 绘制 28x28 的带间距网格单元
                    draw_rect(frame_buffer, 
                              80 + c * 30 + 1, 
                              80 + r * 30 + 1, 
                              80 + (c + 1) * 30 - 1, 
                              80 + (r + 1) * 30 - 1, 
                              cell_color)

            # (E) 绘制底部调色板栏 (#1e1e26)
            draw_rect(frame_buffer, 110, 570, 530, 625, (30, 30, 38))
            draw_rect_outline(frame_buffer, 110, 570, 530, 625, (50, 50, 65), thickness=2)
            for i, color in enumerate(COLORS):
                cx = 145 + i * 50
                cy = 595
                draw_circle(frame_buffer, cx, cy, 18, color)
                # 勾勒黑色小内边，以分离纯白色块与背景
                if color == (255, 255, 255):
                    draw_circle_outline(frame_buffer, cx, cy, 18, (100, 100, 100), thickness=1)
                
                # 为当前选中的颜色绘制高亮白圈
                if i == selected_color_idx:
                    draw_circle_outline(frame_buffer, cx, cy, 21, (255, 255, 255), thickness=2)

            # (F) 绘制左侧控制按钮 (UNDO, CLEAR, SAVE)
            # UNDO 按钮
            draw_rect(frame_buffer, 10, 190, 70, 230, (70, 80, 95))
            draw_rect_outline(frame_buffer, 10, 190, 70, 230, (110, 125, 145), thickness=2)
            draw_string(frame_buffer, 28, 206, "UNDO", (255, 255, 255), scale=1, spacing=1)
            
            # CLEAR 按钮
            draw_rect(frame_buffer, 10, 250, 70, 290, (180, 50, 50))
            draw_rect_outline(frame_buffer, 10, 250, 70, 290, (230, 90, 90), thickness=2)
            draw_string(frame_buffer, 31, 266, "CLR", (255, 255, 255), scale=1, spacing=1)

            # SAVE 按钮
            draw_rect(frame_buffer, 10, 310, 70, 350, (70, 130, 180))
            draw_rect_outline(frame_buffer, 10, 310, 70, 350, (120, 180, 230), thickness=2)
            draw_string(frame_buffer, 28, 326, "SAVE", (255, 255, 255), scale=1, spacing=1)

            # (G) 绘制右侧控制按钮 (FILL, EXIT, INFO)
            # FILL 按钮
            draw_rect(frame_buffer, 570, 190, 630, 230, (50, 150, 100))
            draw_rect_outline(frame_buffer, 570, 190, 630, 230, (90, 200, 140), thickness=2)
            draw_string(frame_buffer, 588, 206, "FILL", (255, 255, 255), scale=1, spacing=1)

            # EXIT 按钮
            draw_rect(frame_buffer, 570, 250, 630, 290, (80, 80, 80))
            draw_rect_outline(frame_buffer, 570, 250, 630, 290, (120, 120, 120), thickness=2)
            draw_string(frame_buffer, 588, 266, "EXIT", (255, 255, 255), scale=1, spacing=1)

            # INFO 按钮
            draw_rect(frame_buffer, 570, 310, 630, 350, (140, 90, 170))
            draw_rect_outline(frame_buffer, 570, 310, 630, 350, (190, 130, 220), thickness=2)
            draw_string(frame_buffer, 588, 326, "INFO", (255, 255, 255), scale=1, spacing=1)

            # 11. 将整帧画面进行 PNG 压缩编码并推送
            png_output = encode_png(frame_buffer, WIDTH, HEIGHT)
            
            # 定位光标，原地打印替换 (完美的双缓冲机制)
            sys.stdout.write(f"\033[{start_row};{start_col}H")
            send_image_via_kitty(png_output, target_cols, target_rows, image_id=10)
            sys.stdout.write("\033[H") # 重置光标至最上端

    finally:
        # 12. 程序退出时绝对安全恢复终端默认属性：
        #     - 关闭鼠标位置监听
        #     - 显示控制台文本光标
        #     - 擦除 Kitty 图像渲染缓存
        #     - 还原终端属性与清屏
        sys.stdout.write("\033[?1000l\033[?1002l\033[?1006l")
        sys.stdout.write("\033[?25h\033[2J\033[H")
        sys.stdout.write("\033_Ga=d,i=10\033\\")
        sys.stdout.flush()
        
        termios.tcsetattr(fd, termios.TCSANOW, old_settings)
        print("💡 交互式画板已安全退出。您的创作可以通过 [SAVE] 保存为本地 artwork.png 文件！")

if __name__ == "__main__":
    main()
