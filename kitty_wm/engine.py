import math
import zlib
import struct
import base64
import sys

# ==============================================================================
# 🖥️ KittyWM 核心图形渲染引擎
# ==============================================================================
WIDTH, HEIGHT = 960, 540  # 16:9 黄金宽屏比例
BUFFER_SIZE = WIDTH * HEIGHT * 4

# SGR 鼠标报告与 ANSI 码正则
import re
sgr_pattern = re.compile(r'\x1b\[<(\d+);(\d+);(\d+)([Mm])')
ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# Handcrafted 5x7 Pixel Font Dictionary
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
    '(': [0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02],
    ')': [0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08],
    '+': [0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00],
}

def draw_rect(buffer, x0, y0, x1, y1, color):
    """绘制填充矩形 (带边界裁剪保护)"""
    x0, y0 = max(0, min(WIDTH-1, int(x0))), max(0, min(HEIGHT-1, int(y0)))
    x1, y1 = max(0, min(WIDTH-1, int(x1))), max(0, min(HEIGHT-1, int(y1)))
    for y in range(y0, y1 + 1):
        row_offset = y * WIDTH * 4
        for x in range(x0, x1 + 1):
            idx = row_offset + x * 4
            buffer[idx]     = color[0]
            buffer[idx+1]   = color[1]
            buffer[idx+2]   = color[2]
            buffer[idx+3]   = 255 if len(color) < 4 else color[3]

def draw_rect_outline(buffer, x0, y0, x1, y1, color, thickness=1):
    """绘制空心矩形边框"""
    draw_rect(buffer, x0, y0, x1, y0 + thickness - 1, color)
    draw_rect(buffer, x0, y1 - thickness + 1, x1, y1, color)
    draw_rect(buffer, x0, y0, x0 + thickness - 1, y1, color)
    draw_rect(buffer, x1 - thickness + 1, y0, x1, y1, color)

def draw_circle(buffer, cx, cy, r, color):
    """绘制实心圆"""
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
                buffer[idx+3]   = 255 if len(color) < 4 else color[3]

def draw_circle_outline(buffer, cx, cy, r, color, thickness=2):
    """绘制圆圈边框"""
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
                buffer[idx+3]   = 255 if len(color) < 4 else color[3]

def draw_line(buffer, x0, y0, x1, y1, color):
    """绘制 Bresenham 单像素线条 (百分之百防 bytearray 长度收缩)"""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if 0 <= x0 < WIDTH and 0 <= y0 < HEIGHT:
            idx = (y0 * WIDTH + x0) * 4
            buffer[idx]     = color[0]
            buffer[idx+1]   = color[1]
            buffer[idx+2]   = color[2]
            buffer[idx+3]   = 255 if len(color) < 4 else color[3]

        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

def draw_thick_line(buffer, x0, y0, x1, y1, color, thickness=2):
    """画一条具有物理厚度的线"""
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
    """画单个像素字符"""
    bitmap = FONT.get(char.upper(), FONT[' '])
    for row_idx, row in enumerate(bitmap):
        for col_idx in range(5):
            if (row >> (4 - col_idx)) & 1:
                draw_rect(buffer, cx + col_idx * scale, cy + row_idx * scale,
                          cx + (col_idx + 1) * scale - 1, cy + (row_idx + 1) * scale - 1, color)

def draw_string(buffer, x, y, text, color, scale=2, spacing=2):
    """画字符串"""
    curr_x = x
    for char in text:
        draw_char(buffer, curr_x, y, char, color, scale)
        curr_x += 5 * scale + spacing

# ==============================================================================
# 📦 PNG 压缩编码与 Kitty 图像协议传输
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
    
    # 静默擦除旧纹理，防止排版错位与泄漏
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
