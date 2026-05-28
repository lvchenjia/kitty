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
import math
import random

# ==============================================================================
# 🖥️ KittyWM: 终端图形化桌面与窗口管理器系统
# ==============================================================================
WIDTH, HEIGHT = 640, 640
BUFFER_SIZE = WIDTH * HEIGHT * 4

# 正则表达式定义
sgr_pattern = re.compile(r'\x1b\[<(\d+);(\d+);(\d+)([Mm])')
ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# ==============================================================================
# 🔠 5x7 极简像素字模库
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
    '/': [0x01, 0x02, 0x04, 0x08, 0x10, 0x10, 0x10],
    '\\': [0x10, 0x08, 0x04, 0x02, 0x01, 0x01, 0x01],
    '>': [0x10, 0x08, 0x04, 0x02, 0x04, 0x08, 0x10],
    '<': [0x01, 0x02, 0x04, 0x08, 0x04, 0x02, 0x01],
    '*': [0x04, 0x15, 0x0E, 0x04, 0x0E, 0x15, 0x04],
    '\'': [0x08, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00],
}

# ==============================================================================
# 🎨 核心绘图算法 (RGBA 字节缓存填充)
# ==============================================================================
def draw_rect(buffer, x0, y0, x1, y1, color):
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
    draw_rect(buffer, x0, y0, x1, y0 + thickness - 1, color)
    draw_rect(buffer, x0, y1 - thickness + 1, x1, y1, color)
    draw_rect(buffer, x0, y0, x0 + thickness - 1, y1, color)
    draw_rect(buffer, x1 - thickness + 1, y0, x1, y1, color)

def draw_circle(buffer, cx, cy, r, color):
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

def draw_line(buffer, x0, y0, x1, y1, color):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if 0 <= x0 < WIDTH and 0 <= y0 < HEIGHT:
            idx = (y0 * WIDTH + x0) * 4
            buffer[idx:idx+4] = color

        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

def draw_thick_line(buffer, x0, y0, x1, y1, color, thickness=1):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    if thickness <= 1:
        draw_line(buffer, x0, y0, x1, y1, color)
        return
        
    dx = x1 - x0
    dy = y1 - y0
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        draw_circle(buffer, x0, y0, int(thickness), color)
        return
        
    nx = -dy / length
    ny = dx / length
    
    half_t = (thickness - 1) / 2.0
    for offset in range(int(-half_t * 10), int(half_t * 10) + 1):
        k = offset / 10.0
        ox = k * nx
        oy = k * ny
        draw_line(buffer, x0 + ox, y0 + oy, x1 + ox, y1 + oy, color)

def draw_char(buffer, cx, cy, char, color, scale=2):
    bitmap = FONT.get(char.upper(), FONT[' '])
    for row_idx, row in enumerate(bitmap):
        for col_idx in range(5):
            if (row >> (4 - col_idx)) & 1:
                draw_rect(buffer, cx + col_idx * scale, cy + row_idx * scale,
                          cx + (col_idx + 1) * scale - 1, cy + (row_idx + 1) * scale - 1, color)

def draw_string(buffer, x, y, text, color, scale=2, spacing=2):
    curr_x = x
    for char in text:
        draw_char(buffer, curr_x, y, char, color, scale)
        curr_x += 5 * scale + spacing

# ==============================================================================
# 📦 Kitty PNG 压缩编码与输出
# ==============================================================================
def encode_png(rgba_data, width, height):
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr = b'IHDR' + ihdr_data
    ihdr_chunk = struct.pack(">I", len(ihdr) - 4) + ihdr + struct.pack(">I", zlib.crc32(ihdr))

    row_bytes = width * 4
    scanlines = [b'\x00' + rgba_data[r * row_bytes : (r + 1) * row_bytes] for r in range(height)]
    
    compressed_data = zlib.compress(b''.join(scanlines), level=1)
    idat = b'IDAT' + compressed_data
    idat_chunk = struct.pack(">I", len(idat) - 4) + idat + struct.pack(">I", zlib.crc32(idat))

    iend = b'IEND'
    iend_chunk = struct.pack(">I", 0) + iend + struct.pack(">I", zlib.crc32(iend))

    return b'\x89PNG\r\n\x1a\n' + ihdr_chunk + idat_chunk + iend_chunk

def send_image_via_kitty(png_data, target_cols, target_rows, image_id=10):
    b64_data = base64.b64encode(png_data).decode('ascii')
    chunk_size = 4096
    
    # 彻底擦除历史图像帧，避开排版缓存堆叠
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
# 🗔 窗口对象架构定义
# ==============================================================================
class Window:
    def __init__(self, win_id, title, x, y, w, h, visible=True):
        self.id = win_id
        self.title = title
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = visible
        # 拖拽临时定位偏置
        self.drag_offset_x = 0
        self.drag_offset_y = 0

# ==============================================================================
# 🚀 KDE 主桌面运行系统
# ==============================================================================
def main():
    # 1. 隐藏光标，全屏清屏，启动 SGR 鼠标检测
    sys.stdout.write("\033[?25l\033[2J\033[H")
    sys.stdout.write("\033[?1000h\033[?1002h\033[?1006h")
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    # 2. 创建三大系统窗口：终端、时钟、系统监视器
    window_terminal = Window("terminal", "TERMINAL CONSOLE", 30, 80, 340, 220, visible=True)
    window_clock = Window("clock", "ANALOG DIGITAL CLOCK", 390, 80, 210, 180, visible=True)
    window_sysmon = Window("sysmon", "SYSTEM PERFORMANCE", 180, 330, 260, 160, visible=True)

    # Z-Order 窗口堆栈 (列表尾部为最顶端渲染层/激活层)
    windows = [window_sysmon, window_clock, window_terminal]

    # 终端输入变量与历史消息缓存
    terminal_input = ""
    terminal_history = [
        "WELCOME TO KITTYWM DE V1.0",
        "TYPE 'HELP' FOR ALL AVAILABLE COMMANDS.",
        "",
    ]

    # 系统监视器 CPU 负载仿真变量 (滚动数组)
    cpu_history = [0.12] * 20
    
    # 交互状态变量
    dragging_win = None
    start_menu_open = False
    should_exit = False
    
    # 统一帧缓冲区
    frame_buffer = bytearray(BUFFER_SIZE)

    # 执行命令函数
    def execute_terminal_command(cmd):
        cmd = cmd.strip()
        if not cmd:
            terminal_history.append("kitty> ")
            return
            
        terminal_history.append(f"kitty> {cmd}")
        parts = cmd.lower().split()
        base_cmd = parts[0]
        
        if base_cmd == "help":
            terminal_history.append("AVAILABLE COMMANDS:")
            terminal_history.append("  HELP     - DISPLAY GUIDE")
            terminal_history.append("  LS       - LIST DIRECTORY FILES")
            terminal_history.append("  NEOFETCH - SHOW SYSTEM STATS")
            terminal_history.append("  CLEAR    - WIPE SHELL OUTPUT")
            terminal_history.append("  CLOCK    - LAUNCH CLOCK WINDOW")
            terminal_history.append("  EXIT     - SHUTDOWN KITTYWM")
        elif base_cmd == "ls":
            terminal_history.append("DIRECTORY: DESKTOP/KITTY/")
            terminal_history.append("  CUBE.PY         PIXEL_DONUT.C")
            terminal_history.append("  PIXEL_CUBE.PY   PIXEL_DONUT.PY")
            terminal_history.append("  INTERACTIVE.PY  README.MD")
        elif base_cmd == "neofetch":
            terminal_history.append("  .---.    OS: KITTYWM DE V1.0")
            terminal_history.append("  |o o|    HOST: MAC M4 PRO")
            terminal_history.append("  | - |    SHELL: KITTY-SH 2.0")
            terminal_history.append("  '---'    WM: KITTY-WINDOW-MGR")
            terminal_history.append("           RES: 640X640 PIXELS")
        elif base_cmd == "clear":
            terminal_history.clear()
        elif base_cmd == "clock":
            window_clock.visible = True
            if window_clock in windows:
                windows.remove(window_clock)
                windows.append(window_clock)
            terminal_history.append("CLOCK WINDOW RE-OPENED.")
        elif base_cmd == "exit":
            nonlocal should_exit
            should_exit = True
        else:
            terminal_history.append(f"ERROR: COMMAND NOT FOUND: '{base_cmd}'")
            
        # 裁剪超出视窗的历史行
        while len(terminal_history) > 12:
            terminal_history.pop(0)

    # 绘制系统桌面壁纸 (渐变 + 科技风网格线)
    def draw_wallpaper():
        # 1. 绘制紫蓝色至暗红色的科技感渐变背景
        for y in range(HEIGHT):
            ratio = y / (HEIGHT - 1)
            r = int(14 * (1 - ratio) + 38 * ratio)
            g = int(18 * (1 - ratio) + 12 * ratio)
            b = int(36 * (1 - ratio) + 44 * ratio)
            
            row_offset = y * WIDTH * 4
            pixel_bytes = bytes([r, g, b, 255])
            frame_buffer[row_offset : row_offset + WIDTH * 4] = pixel_bytes * WIDTH
            
        # 2. 绘制深灰色虚拟桌面网格线 (间距 40 像素)
        grid_color = (25, 26, 35)
        for y in range(0, HEIGHT, 40):
            draw_rect(frame_buffer, 0, y, WIDTH - 1, y, grid_color)
        for x in range(0, WIDTH, 40):
            draw_rect(frame_buffer, x, 0, x, HEIGHT - 1, grid_color)
            
        # 3. 绘制系统属性水印
        draw_string(frame_buffer, 20, 560, "KITTYWM V1.0 - MULTI-WINDOW TERMINAL SYSTEM", (85, 90, 115), scale=1, spacing=1)

    # 模拟更新 CPU 历史曲线 (50ms 级别随机漫步)
    def update_cpu():
        prev = cpu_history[-1]
        change = random.uniform(-0.1, 0.1)
        new_val = max(0.05, min(0.95, prev + change))
        cpu_history.append(new_val)
        if len(cpu_history) > 30:
            cpu_history.pop(0)

    # 绘制单个窗口组件
    def draw_window(win, is_focused):
        if not win.visible:
            return
            
        # A. 软立体投影效果 (向右下平移 4px 绘制暗色块)
        draw_rect(frame_buffer, win.x + 4, win.y + 4, win.x + win.w + 3, win.y + win.h + 3, (8, 8, 12))
        
        # B. 填充窗口工作区背景 (#15161e)
        body_color = (21, 22, 30)
        draw_rect(frame_buffer, win.x, win.y, win.x + win.w - 1, win.y + win.h - 1, body_color)
        
        # C. 绘制标题栏面板 (#252836)
        header_color = (37, 40, 54) if is_focused else (28, 30, 40)
        draw_rect(frame_buffer, win.x, win.y, win.x + win.w - 1, win.y + 24, header_color)
        
        # D. 绘制边框与标题栏分割霓虹线 (聚焦状态为亮青色，非聚焦为暗灰色)
        border_color = (0, 172, 193) if is_focused else (55, 60, 75)
        draw_rect(frame_buffer, win.x, win.y + 24, win.x + win.w - 1, win.y + 25, border_color)
        draw_rect_outline(frame_buffer, win.x, win.y, win.x + win.w - 1, win.y + win.h - 1, border_color, thickness=2)
        
        # E. 标题文字
        title_color = (255, 255, 255) if is_focused else (140, 145, 160)
        draw_string(frame_buffer, win.x + 8, win.y + 7, win.title, title_color, scale=1, spacing=1)
        
        # F. 绘制右上角 [X] 关闭按钮
        close_bg = (190, 50, 50) if is_focused else (110, 40, 40)
        draw_rect(frame_buffer, win.x + win.w - 20, win.y + 4, win.x + win.w - 5, win.y + 20, close_bg)
        draw_string(frame_buffer, win.x + win.w - 15, win.y + 7, "X", (255, 255, 255), scale=1, spacing=1)
        
        # G. 渲染各个窗口独占的特殊内容
        if win.id == "terminal":
            # 显示 Shell 输出历史
            curr_y = win.y + 32
            for line in terminal_history:
                line_color = (130, 240, 130) if "os:" in line.lower() or "wm:" in line.lower() or "stats" in line.lower() else (220, 220, 230)
                if line.startswith("kitty>"):
                    line_color = (0, 220, 255)
                draw_string(frame_buffer, win.x + 10, curr_y, line, line_color, scale=1, spacing=1)
                curr_y += 13
                
            # 绘制当前正在输入的命令行 & 呼吸闪烁光标
            cursor_visible = (int(time.time() * 2) % 2 == 0) and is_focused
            prompt = f"kitty> {terminal_input}"
            draw_string(frame_buffer, win.x + 10, curr_y, prompt, (0, 220, 255), scale=1, spacing=1)
            if cursor_visible:
                cx_pos = win.x + 10 + len(prompt) * 6
                draw_rect(frame_buffer, cx_pos, curr_y, cx_pos + 5, curr_y + 8, (0, 220, 255))
                
        elif win.id == "clock":
            t_struct = time.localtime()
            time_str = time.strftime("%H:%M:%S", t_struct)
            
            # 绘制数码时钟
            draw_string(frame_buffer, win.x + win.w // 2 - 32, win.y + 32, time_str, (253, 216, 53), scale=1, spacing=1)
            
            # 绘制指针盘面圆环与轴针
            cx = win.x + win.w // 2
            cy = win.y + win.h - 55
            draw_circle_outline(frame_buffer, cx, cy, 40, (100, 110, 130), thickness=2)
            draw_circle(frame_buffer, cx, cy, 2, (255, 255, 255))
            
            # 时分秒刻度标志点
            draw_rect(frame_buffer, cx - 1, cy - 38, cx + 1, cy - 34, (255, 255, 255)) # 12点
            draw_rect(frame_buffer, cx - 1, cy + 34, cx + 1, cy + 38, (255, 255, 255)) # 6点
            draw_rect(frame_buffer, cx + 34, cy - 1, cx + 38, cy + 1, (255, 255, 255)) # 3点
            draw_rect(frame_buffer, cx - 38, cy - 1, cx - 34, cy + 1, (255, 255, 255)) # 9点
            
            # 计算三角函数指针偏角
            h, m, s = t_struct.tm_hour, t_struct.tm_min, t_struct.tm_sec
            theta_h = 2.0 * math.pi * (h % 12 + m / 60.0) / 12.0
            theta_m = 2.0 * math.pi * m / 60.0
            theta_s = 2.0 * math.pi * s / 60.0
            
            # 指针拉伸线段
            hx = int(cx + 18 * math.sin(theta_h))
            hy = int(cy - 18 * math.cos(theta_h))
            draw_thick_line(frame_buffer, cx, cy, hx, hy, (70, 130, 180), thickness=2) # 时针
            
            mx = int(cx + 28 * math.sin(theta_m))
            my = int(cy - 28 * math.cos(theta_m))
            draw_thick_line(frame_buffer, cx, cy, mx, my, (76, 175, 80), thickness=2)  # 分针
            
            sx = int(cx + 32 * math.sin(theta_s))
            sy = int(cy - 32 * math.cos(theta_s))
            draw_line(frame_buffer, cx, cy, sx, sy, (229, 57, 53))                      # 秒针

        elif win.id == "sysmon":
            draw_string(frame_buffer, win.x + 10, win.y + 32, "CPU LOAD:", (255, 255, 255), scale=1, spacing=1)
            
            # 绘制示波器网格区域
            chart_x = win.x + 10
            chart_y = win.y + 44
            chart_w = win.w - 20
            chart_h = 60
            draw_rect(frame_buffer, chart_x, chart_y, chart_x + chart_w, chart_y + chart_h, (12, 14, 18))
            draw_rect_outline(frame_buffer, chart_x, chart_y, chart_x + chart_w, chart_y + chart_h, (45, 50, 65), thickness=1)
            
            # 水平刻度线
            for offset in (15, 30, 45):
                draw_rect(frame_buffer, chart_x, chart_y + offset, chart_x + chart_w, chart_y + offset, (20, 24, 30))
                
            # 折线绘制
            if len(cpu_history) >= 2:
                step = chart_w / (len(cpu_history) - 1)
                for i in range(len(cpu_history) - 1):
                    x0 = int(chart_x + i * step)
                    y0 = int(chart_y + chart_h - cpu_history[i] * chart_h)
                    x1 = int(chart_x + (i + 1) * step)
                    y1 = int(chart_y + chart_h - cpu_history[i+1] * chart_h)
                    draw_line(frame_buffer, x0, y0, x1, y1, (0, 255, 128))
                    
            latest_val = int(cpu_history[-1] * 100)
            draw_string(frame_buffer, win.x + 80, win.y + 32, f"{latest_val}%", (0, 255, 128), scale=1, spacing=1)
            
            # 绘制内存物理占用度量条 (40% 静态)
            ram_y = win.y + 115
            draw_string(frame_buffer, win.x + 10, ram_y, "RAM: 6.4 GB / 16.0 GB (40%)", (255, 255, 255), scale=1, spacing=1)
            draw_rect(frame_buffer, win.x + 10, ram_y + 12, win.x + win.w - 10, ram_y + 24, (30, 32, 42))
            draw_rect_outline(frame_buffer, win.x + 10, ram_y + 12, win.x + win.w - 10, ram_y + 24, (55, 60, 75), thickness=1)
            
            fill_w = int((win.w - 22) * 0.40)
            # 青色到蓝色的渐变进度条
            draw_rect(frame_buffer, win.x + 11, ram_y + 13, win.x + 11 + fill_w, ram_y + 23, (0, 172, 193))

    # 绘制系统任务栏 (Taskbar)
    def draw_taskbar():
        # y: 600 ~ 640 面板底座 (#181920)
        draw_rect(frame_buffer, 0, 600, WIDTH - 1, HEIGHT - 1, (24, 25, 32))
        draw_rect(frame_buffer, 0, 600, WIDTH - 1, 601, (0, 172, 193)) # 分割霓虹线
        
        # 1. 开始按钮 (Start Menu Button)
        start_bg = (0, 172, 193) if start_menu_open else (30, 32, 42)
        draw_rect(frame_buffer, 10, 605, 80, 635, start_bg)
        draw_rect_outline(frame_buffer, 10, 605, 80, 635, (255, 255, 255), thickness=1)
        draw_string(frame_buffer, 22, 614, "START", (255, 255, 255), scale=1, spacing=1)
        
        # 2. 窗口显示控制图标
        # [TERMINAL]
        t_vis = window_terminal.visible
        draw_rect(frame_buffer, 90, 605, 175, 635, (48, 52, 70) if t_vis else (30, 32, 42))
        draw_rect_outline(frame_buffer, 90, 605, 175, 635, (0, 172, 193) if t_vis else (50, 52, 65), thickness=1)
        draw_string(frame_buffer, 102, 614, "TERMINAL", (255, 255, 255) if t_vis else (140, 140, 150), scale=1, spacing=1)
        
        # [CLOCK]
        c_vis = window_clock.visible
        draw_rect(frame_buffer, 185, 605, 255, 635, (48, 52, 70) if c_vis else (30, 32, 42))
        draw_rect_outline(frame_buffer, 185, 605, 255, 635, (0, 172, 193) if c_vis else (50, 52, 65), thickness=1)
        draw_string(frame_buffer, 200, 614, "CLOCK", (255, 255, 255) if c_vis else (140, 140, 150), scale=1, spacing=1)
        
        # [MONITOR]
        m_vis = window_sysmon.visible
        draw_rect(frame_buffer, 265, 605, 345, 635, (48, 52, 70) if m_vis else (30, 32, 42))
        draw_rect_outline(frame_buffer, 265, 605, 345, 635, (0, 172, 193) if m_vis else (50, 52, 65), thickness=1)
        draw_string(frame_buffer, 276, 614, "MONITOR", (255, 255, 255) if m_vis else (140, 140, 150), scale=1, spacing=1)
        
        # 3. 任务栏右侧本地物理时钟
        t_struct = time.localtime()
        time_str = time.strftime("%H:%M:%S", t_struct)
        draw_rect(frame_buffer, 530, 605, 630, 635, (16, 17, 22))
        draw_rect_outline(frame_buffer, 530, 605, 630, 635, (45, 48, 60), thickness=1)
        draw_string(frame_buffer, 546, 614, time_str, (0, 220, 255), scale=1, spacing=1)

    # 绘制开始菜单弹窗
    def draw_start_menu():
        if not start_menu_open:
            return
        # 开始菜单弹出面板 (x: 10 ~ 160, y: 445 ~ 599)
        draw_rect(frame_buffer, 10, 445, 160, 599, (30, 30, 38))
        draw_rect_outline(frame_buffer, 10, 445, 160, 599, (0, 172, 193), thickness=2)
        
        # 菜单子选项区绘制
        # 选项1: REOPEN ALL (y: 450~495)
        draw_rect(frame_buffer, 14, 450, 156, 490, (40, 42, 54))
        draw_string(frame_buffer, 26, 464, "REOPEN ALL", (255, 255, 255), scale=1, spacing=1)
        
        # 选项2: SCREENSHOT (y: 500~540)
        draw_rect(frame_buffer, 14, 500, 156, 540, (40, 42, 54))
        draw_string(frame_buffer, 26, 514, "SCREENSHOT", (255, 255, 255), scale=1, spacing=1)
        
        # 选项3: SHUTDOWN (y: 548~590)
        draw_rect(frame_buffer, 14, 548, 156, 590, (190, 50, 50))
        draw_string(frame_buffer, 26, 562, "SHUTDOWN", (255, 255, 255), scale=1, spacing=1)

    try:
        # 初始画壁纸与窗口渲染推送
        draw_wallpaper()
        for win in windows:
            draw_window(win, is_focused=(win == windows[-1]))
        draw_taskbar()
        
        # 建立初始显示视窗
        columns, rows = 80, 40
        try:
            columns, rows = os.get_terminal_size()
        except OSError:
            pass
        target_rows = min(rows - 6, 26)
        if target_rows < 12:
            target_rows = 12
        target_cols = target_rows * 2
        start_row = 3
        start_col = max(1, (columns - target_cols) // 2)
        
        png_data = encode_png(frame_buffer, WIDTH, HEIGHT)
        sys.stdout.write(f"\033[{start_row};{start_col}H")
        send_image_via_kitty(png_data, target_cols, target_rows, image_id=10)
        
        # 监听变量
        mouse_is_down = False
        
        # 9. 交互事件无线轮询循环 (20ms)
        while not should_exit:
            # CPU 数据波形向前推移
            update_cpu()
            
            # 检测 stdin 数据是否就绪
            rlist, _, _ = select.select([sys.stdin], [], [], 0.02)
            
            raw_input_data = ""
            if rlist:
                raw_input_data = sys.stdin.read(1)
                if raw_input_data == '\x1b':
                    seq = '\x1b'
                    # 加大时延读取窗口，防止 SGR 数据流被拼抢切碎
                    while select.select([sys.stdin], [], [], 0.005)[0]:
                        seq += sys.stdin.read(1)
                    raw_input_data = seq
                else:
                    while select.select([sys.stdin], [], [], 0.0)[0]:
                        raw_input_data += sys.stdin.read(1)

            # A. 键盘硬退出热键检测 (仅包含字符 'q', 'Q' 或 Ctrl+C)
            if raw_input_data:
                if 'q' in raw_input_data or 'Q' in raw_input_data or '\x03' in raw_input_data:
                    break

            # B. 过滤解析出纯键盘操作，分发给处于最顶层(激活聚焦)的 Terminal 窗口
            clean_keys = ansi_escape.sub('', raw_input_data)
            focused_win = None
            # 寻找到当前处于最顶端的可见窗口
            for win in reversed(windows):
                if win.visible:
                    focused_win = win
                    break
                    
            if focused_win == window_terminal and window_terminal.visible and clean_keys:
                for char in clean_keys:
                    if char == '\x7f' or char == '\x08': # 退格键
                        if len(terminal_input) > 0:
                            terminal_input = terminal_input[:-1]
                    elif char in ('\r', '\n'): # 回车键
                        execute_terminal_command(terminal_input)
                        terminal_input = ""
                    elif 32 <= ord(char) <= 126: # 基础 ASCII 打印字符输入
                        if len(terminal_input) < 32:
                            terminal_input += char

            # C. SGR 鼠标交互行为解析
            matches = sgr_pattern.findall(raw_input_data)
            for match in matches:
                button = int(match[0])
                cx = int(match[1])
                cy = int(match[2])
                is_press_event = match[3] == 'M'

                # 映射像素桌面坐标
                relative_cx = cx - start_col
                relative_cy = cy - start_row
                
                if 0 <= relative_cx < target_cols and 0 <= relative_cy < target_rows:
                    rx = (relative_cx + 0.5) / target_cols
                    ry = (relative_cy + 0.5) / target_rows
                    
                    px = int(rx * WIDTH)
                    py = int(ry * HEIGHT)

                    # 左键按下操作
                    if button == 0:
                        if is_press_event:
                            mouse_is_down = True
                            
                            # (1) 检查是否点击在开始菜单内部
                            if start_menu_open and 10 <= px < 160 and 445 <= py < 599:
                                if 450 <= py < 490: # REOPEN ALL
                                    window_terminal.visible = True
                                    window_clock.visible = True
                                    window_sysmon.visible = True
                                    # 全部带到最前方
                                    for w in [window_sysmon, window_clock, window_terminal]:
                                        if w in windows:
                                            windows.remove(w)
                                            windows.append(w)
                                    start_menu_open = False
                                    terminal_history.append("ALL WINDOWS RESTORED.")
                                elif 500 <= py < 540: # SCREENSHOT
                                    try:
                                        scr_png = encode_png(frame_buffer, WIDTH, HEIGHT)
                                        with open("screenshot.png", "wb") as f:
                                            f.write(scr_png)
                                        terminal_history.append("SCREENSHOT SAVED TO SCREENSHOT.PNG")
                                    except Exception as ex:
                                        terminal_history.append(f"ERROR: {str(ex)[:15]}")
                                    start_menu_open = False
                                elif 548 <= py < 590: # SHUTDOWN
                                    should_exit = True
                                continue
                            else:
                                # 点击其他位置，自动关闭开始菜单
                                start_menu_open = False
                            
                            # (2) 检查是否点击在任何活跃窗口的躯体内
                            clicked_win = None
                            for win in reversed(windows):
                                if win.visible:
                                    if win.x <= px < win.x + win.w and win.y <= py < win.y + win.h:
                                        clicked_win = win
                                        break
                                        
                            if clicked_win:
                                # 点击了该窗口，立刻提焦至最前端堆栈
                                windows.remove(clicked_win)
                                windows.append(clicked_win)
                                
                                # 点击位置在标题栏 (高度 24)
                                if py < clicked_win.y + 24:
                                    # 检查是否命中了右上角 [X] 关闭按钮
                                    if clicked_win.x + clicked_win.w - 20 <= px < clicked_win.x + clicked_win.w - 4:
                                        clicked_win.visible = False
                                        terminal_history.append(f"CLOSED: {clicked_win.title}")
                                    else:
                                        # 启动窗口拖拽
                                        dragging_win = clicked_win
                                        dragging_win.drag_offset_x = px - clicked_win.x
                                        dragging_win.drag_offset_y = py - clicked_win.y
                                continue
                            
                            # (3) 检查是否点击了底部任务栏 (y >= 600)
                            if py >= 600:
                                # 开始按钮点击
                                if 10 <= px < 80:
                                    start_menu_open = not start_menu_open
                                # 快捷启动栏：[TERMINAL] (90~175)
                                elif 90 <= px < 175:
                                    window_terminal.visible = not window_terminal.visible
                                    if window_terminal.visible:
                                        windows.remove(window_terminal)
                                        windows.append(window_terminal)
                                # [CLOCK] (185~255)
                                elif 185 <= px < 255:
                                    window_clock.visible = not window_clock.visible
                                    if window_clock.visible:
                                        windows.remove(window_clock)
                                        windows.append(window_clock)
                                # [MONITOR] (265~345)
                                elif 265 <= px < 345:
                                    window_sysmon.visible = not window_sysmon.visible
                                    if window_sysmon.visible:
                                        windows.remove(window_sysmon)
                                        windows.append(window_sysmon)
                        else:
                            # 鼠标左键释放
                            mouse_is_down = False
                            dragging_win = None
                            
                    # 拖拽移动窗口
                    elif button == 32:
                        if mouse_is_down and dragging_win:
                            new_x = px - dragging_win.drag_offset_x
                            new_y = py - dragging_win.drag_offset_y
                            
                            # 边界强约束限制，防止拖拽越出屏幕死角
                            dragging_win.x = max(-dragging_win.w + 30, min(WIDTH - 30, new_x))
                            dragging_win.y = max(0, min(HEIGHT - 40, new_y))

            # D. UI 图层拼装渲染
            draw_wallpaper()
            
            # 按 Z-Order 顺序由底向上拼装渲染可见窗口
            focused_win_top = None
            for win in reversed(windows):
                if win.visible:
                    focused_win_top = win
                    break
                    
            for win in windows:
                if win.visible:
                    draw_window(win, is_focused=(win == focused_win_top))
                    
            draw_taskbar()
            draw_start_menu()

            # E. PNG 压缩后整流发送至终端渲染
            png_output = encode_png(frame_buffer, WIDTH, HEIGHT)
            
            sys.stdout.write(f"\033[{start_row};{start_col}H")
            send_image_via_kitty(png_output, target_cols, target_rows, image_id=10)
            sys.stdout.write("\033[H")

    finally:
        # 10. 恢复终端出厂设置，抹除图像缓存
        sys.stdout.write("\033[?1000l\033[?1002l\033[?1006l")
        sys.stdout.write("\033[?25h\033[2J\033[H")
        sys.stdout.write("\033_Ga=d,i=10\033\\")
        sys.stdout.flush()
        
        termios.tcsetattr(fd, termios.TCSANOW, old_settings)
        print("💡 KittyWM 已安全关闭。")

if __name__ == "__main__":
    main()
