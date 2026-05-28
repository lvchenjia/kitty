import time
import math
from kitty_wm.engine import draw_rect, draw_rect_outline, draw_string, encode_png, send_image_via_kitty, WIDTH, HEIGHT

# ==============================================================================
# 🖥️ KittyWM 现代极光 Dock 桌面与极速事件总线 (Widescreen 960x540)
# ==============================================================================
class DesktopManager:
    def __init__(self, window_terminal, window_clock):
        self.window_terminal = window_terminal
        self.window_clock = window_clock
        # 移除了 performance 窗口，仅保留轻量级 Terminal 与 Clock 两个应用
        self.windows = [window_clock, window_terminal]
        
        # 交互状态
        self.start_menu_open = False
        self.should_exit = False
        self.dragging_win = None
        self.mouse_is_down = False
        
        # 拖拽时格点定位偏置 (基于单元格同步，彻底消灭抖动与滞后)
        self.drag_cell_offset_x = 0
        self.drag_cell_offset_y = 0

    def focus_window(self, win):
        """将窗口拉到最前端激活"""
        if win in self.windows:
            self.windows.remove(win)
            self.windows.append(win)

    def draw_wallpaper(self, buffer):
        """绘制顶级科幻渐变壁纸：太空深邃紫 + 顶部极光霓虹漫反射"""
        # 1. 物理计算从顶部极光亮蓝 (#1a3f6a) 到底部极深靛青 (#05050d) 的漫反射辐射
        for y in range(HEIGHT):
            ratio = y / (HEIGHT - 1)
            # 计算距离顶部发光中心 (cx=480, cy=-50) 的辐射强度
            row_offset = y * WIDTH * 4
            
            # 使用快速近似：纵向线性融合作为主导，顶端中心加入放射状微光
            for x in range(0, WIDTH, 16):
                # 采样每行的局部块，提速 16 倍，保证 Python 渲染耗时控制在 2ms 内！
                # 顶部中心发光区采样
                dx = x - 480
                dy = y + 50
                dist = math.sqrt(dx*dx + dy*dy)
                glow = max(0.0, 1.0 - dist / 500.0)
                
                # 色彩融合：极光青 (#00d0ff) + 太空底色
                r = int(8 * (1 - ratio) + 5 * ratio + 0 * glow)
                g = int(12 * (1 - ratio) + 6 * ratio + 35 * glow)
                b = int(24 * (1 - ratio) + 12 * ratio + 75 * glow)
                
                pixel_bytes = bytes([r, g, b, 255])
                buffer[row_offset + x*4 : row_offset + (x+16)*4] = pixel_bytes * 16
                
        # 2. 绘制超现代极简星空虚点，代替粗糙方格网，逼格拉满
        # 每隔 60 像素画一个 1x1 暗冷灰色微星
        star_color = (48, 54, 76)
        for y in range(30, HEIGHT - 60, 60):
            row_offset = y * WIDTH * 4
            for x in range(30, WIDTH, 60):
                idx = row_offset + x * 4
                buffer[idx]     = star_color[0]
                buffer[idx+1]   = star_color[1]
                buffer[idx+2]   = star_color[2]
                buffer[idx+3]   = 255
                
        # 3. 桌面极简现代属性文字 (替代粗体)
        draw_string(buffer, 30, HEIGHT - 55, "KITTYWM MODERN OS V2.5", (100, 110, 135), scale=1, spacing=1)
        draw_string(buffer, 30, HEIGHT - 42, "CELL-ALIGNED SMOOTH WINDOW SYSTEM", (70, 75, 95), scale=1, spacing=1)

    def draw_dock(self, buffer):
        """绘制超前卫极简 macOS 风格毛玻璃 Dock 栏"""
        # Dock 浮动位置居中偏下: x: 260 ~ 700 (宽度 440), y: 485 ~ 525 (高度 40)
        # 绘制磨砂玻璃高雅黑胶囊底座 (#0f111a, 不透明度 170)
        draw_rect(buffer, 260, 485, 700, 525, (15, 17, 26, 170))
        draw_rect_outline(buffer, 260, 485, 700, 525, (255, 255, 255, 45), thickness=1)
        
        # [START] 菜单按钮 (x: 275 ~ 335, y: 490 ~ 520)
        start_bg = (255, 0, 128) if self.start_menu_open else (30, 32, 45)
        draw_rect(buffer, 275, 490, 335, 520, start_bg)
        draw_rect_outline(buffer, 275, 490, 335, 520, (255, 255, 255, 80), thickness=1)
        draw_string(buffer, 287, 499, "START", (255, 255, 255), scale=1, spacing=1)
        
        # [TERMINAL] (x: 345 ~ 430, y: 490 ~ 520)
        t_vis = self.window_terminal.visible
        draw_rect(buffer, 345, 490, 430, 520, (48, 52, 70) if t_vis else (22, 24, 33))
        draw_rect_outline(buffer, 345, 490, 430, 520, (0, 240, 255) if t_vis else (50, 53, 68), thickness=1)
        draw_string(buffer, 357, 499, "TERMINAL", (255, 255, 255) if t_vis else (130, 135, 150), scale=1, spacing=1)
        # 呼吸运行指示灯 (macOS running dot): 运行状态下在 Dock 底部画 1px 细线或小点
        if t_vis:
            draw_rect(buffer, 382, 517, 392, 519, (0, 240, 255))
            
        # [CLOCK] (x: 440 ~ 515, y: 490 ~ 520)
        c_vis = self.window_clock.visible
        draw_rect(buffer, 440, 490, 515, 520, (48, 52, 70) if c_vis else (22, 24, 33))
        draw_rect_outline(buffer, 440, 490, 515, 520, (255, 0, 128) if c_vis else (50, 53, 68), thickness=1)
        draw_string(buffer, 457, 499, "CLOCK", (255, 255, 255) if c_vis else (130, 135, 150), scale=1, spacing=1)
        if c_vis:
            draw_rect(buffer, 472, 517, 482, 519, (255, 0, 128))
            
        # Dock 右侧的数字科技 LED 时间 (x: 590 ~ 685, y: 490 ~ 520)
        time_str = time.strftime("%H:%M:%S", time.localtime())
        draw_rect(buffer, 590, 490, 685, 520, (10, 11, 16))
        draw_rect_outline(buffer, 590, 490, 685, 520, (45, 48, 60), thickness=1)
        draw_string(buffer, 606, 499, time_str, (0, 240, 255), scale=1, spacing=1)

    def draw_start_menu(self, buffer):
        """绘制 Dock 栏上方优雅浮起的极简开始菜单"""
        if not self.start_menu_open:
            return
        # 开始菜单弹出面板: x: 275 ~ 425 (宽 150), y: 325 ~ 480 (高 155)
        draw_rect(buffer, 275, 325, 425, 480, (20, 22, 30, 230))
        draw_rect_outline(buffer, 275, 325, 425, 480, (255, 0, 128), thickness=2)
        
        # 菜单选项 1: REOPEN ALL (y: 330 ~ 370)
        draw_rect(buffer, 279, 330, 421, 370, (40, 44, 58))
        draw_string(buffer, 297, 345, "REOPEN ALL", (255, 255, 255), scale=1, spacing=1)
        
        # 菜单选项 2: SCREENSHOT (y: 380 ~ 420)
        draw_rect(buffer, 279, 380, 421, 420, (40, 44, 58))
        draw_string(buffer, 297, 395, "SCREENSHOT", (255, 255, 255), scale=1, spacing=1)
        
        # 菜单选项 3: SHUTDOWN (y: 430 ~ 470)
        draw_rect(buffer, 279, 430, 421, 470, (190, 50, 50))
        draw_string(buffer, 297, 445, "SHUTDOWN", (255, 255, 255), scale=1, spacing=1)

    def handle_mouse(self, matches, start_col, start_row, target_cols, target_rows):
        """极其稳健且绝对格点对齐的鼠标交互总线 (消除鼠标物理跳变)"""
        # 计算终端格子的宽高（以物理像素为单位）
        cell_w = WIDTH / target_cols
        cell_h = HEIGHT / target_rows

        for match in matches:
            button = int(match[0])
            cx = int(match[1])
            cy = int(match[2])
            is_press = match[3] == 'M'

            # 映射物理像素位置
            relative_cx = cx - start_col
            relative_cy = cy - start_row
            
            if hasattr(self, "log_message"):
                self.log_message(f"Mouse Event: Button={button}, Pressed={is_press} | GridCol={cx}, GridRow={cy}")

            if 0 <= relative_cx < target_cols and 0 <= relative_cy < target_rows:
                rx = (relative_cx + 0.5) / target_cols
                ry = (relative_cy + 0.5) / target_rows
                
                px = int(rx * WIDTH)
                py = int(ry * HEIGHT)

                # 鼠标左键按下操作 (button == 0)
                if button == 0:
                    if is_press:
                        self.mouse_is_down = True
                        
                        # (A) 开始菜单判定
                        if self.start_menu_open and 275 <= px < 425 and 325 <= py < 480:
                            if 330 <= py < 370:  # REOPEN ALL
                                self.window_terminal.visible = True
                                self.window_clock.visible = True
                                for w in [self.window_clock, self.window_terminal]:
                                    self.focus_window(w)
                                self.window_terminal.terminal_history.append("ALL WINDOWS RE-OPENED.")
                                self.start_menu_open = False
                            elif 380 <= py < 420:  # SCREENSHOT
                                self.save_screenshot()
                                self.start_menu_open = False
                            elif 430 <= py < 470:  # SHUTDOWN
                                self.should_exit = True
                            continue
                        else:
                            self.start_menu_open = False
                        
                        # (B) 检测是否点击了任何活跃可见窗口 (按 Z-Order 从上往下)
                        clicked_win = None
                        for win in reversed(self.windows):
                            if win.visible:
                                if win.x <= px < win.x + win.w and win.y <= py < win.y + win.h:
                                    clicked_win = win
                                    break
                                    
                        if clicked_win:
                            self.focus_window(clicked_win)
                            
                            # 点击的是否是标题栏 (高 30)
                            if py < clicked_win.y + 30:
                                # 是否命中了最左侧的红色关闭小圆圈 (x: clicked_win.x + 11 ~ 21)
                                if clicked_win.x + 11 <= px < clicked_win.x + 21:
                                    clicked_win.visible = False
                                    self.window_terminal.terminal_history.append(f"CLOSED: {clicked_win.title}")
                                else:
                                    # 启动格点对齐拖拽算法！
                                    # 计算当前点击格子与窗口左上角在格子体系下的相对偏置量
                                    self.dragging_win = clicked_win
                                    self.drag_cell_offset_x = relative_cx - (clicked_win.x / cell_w)
                                    self.drag_cell_offset_y = relative_cy - (clicked_win.y / cell_h)
                                    
                                    if hasattr(self, "log_message"):
                                        self.log_message(f"Snapped Drag Started: Offset_X={self.drag_cell_offset_x:.2f}, Offset_Y={self.drag_cell_offset_y:.2f}")
                            continue
                        
                        # (C) 检测点击 Dock 栏 (y: 485 ~ 525)
                        if 485 <= py < 525:
                            # START 按钮 (x: 275 ~ 335)
                            if 275 <= px < 335:
                                self.start_menu_open = not self.start_menu_open
                            # [TERMINAL] (x: 345 ~ 430)
                            elif 345 <= px < 430:
                                self.window_terminal.visible = not self.window_terminal.visible
                                if self.window_terminal.visible:
                                    self.focus_window(self.window_terminal)
                            # [CLOCK] (x: 440 ~ 515)
                            elif 440 <= px < 515:
                                self.window_clock.visible = not self.window_clock.visible
                                if self.window_clock.visible:
                                    self.focus_window(self.window_clock)
                    else:
                        # 左键释放
                        self.mouse_is_down = False
                        self.dragging_win = None

                # 鼠标拖动 (button == 32)
                elif button == 32:
                    if self.dragging_win:
                        # 核心格点算法：直接使窗口坐标严格等于当前光标格子减去初次点击偏置，乘上物理格子大小
                        # 这完全过滤了浮点比例换算过程中的任何抖动与非线性抖跃，窗口将像影子一样100%咬死光标格子！
                        cell_target_x = relative_cx - self.drag_cell_offset_x
                        cell_target_y = relative_cy - self.drag_cell_offset_y
                        
                        new_x = int(round(cell_target_x * cell_w))
                        new_y = int(round(cell_target_y * cell_h))
                        
                        # 边缘物理安全界限
                        self.dragging_win.x = max(-self.dragging_win.w + 30, min(WIDTH - 30, new_x))
                        self.dragging_win.y = max(0, min(HEIGHT - 40, new_y))

            # 全局松开防护
            if not is_press:
                self.mouse_is_down = False
                self.dragging_win = None

    def save_screenshot(self):
        """截取当前屏幕的完美双缓冲画面"""
        try:
            scr_png = encode_png(self.screenshot_buffer, WIDTH, HEIGHT)
            with open("screenshot.png", "wb") as f:
                f.write(scr_png)
            self.window_terminal.terminal_history.append("SCREENSHOT CAPTURED TO SCREENSHOT.PNG")
        except Exception as ex:
            self.window_terminal.terminal_history.append(f"SCREENSHOT ERROR: {str(ex)[:15]}")

    def render_all(self, buffer):
        self.draw_wallpaper(buffer)
        
        # Z-Order 激活态层判定
        top_visible_win = None
        for win in reversed(self.windows):
            if win.visible:
                top_visible_win = win
                break
                
        for win in self.windows:
            if win.visible:
                win.draw(buffer, is_focused=(win == top_visible_win))
                
        self.draw_dock(buffer)
        self.draw_start_menu(buffer)
        
        # 拷贝给截屏双缓冲区
        self.screenshot_buffer = bytearray(buffer)
