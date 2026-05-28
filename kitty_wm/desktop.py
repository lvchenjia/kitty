import time
import math
from kitty_wm.engine import draw_rect, draw_rect_outline, draw_string, encode_png, send_image_via_kitty, WIDTH, HEIGHT

# ==============================================================================
# 🖥️ KittyWM 现代浅色极光 Dock 桌面与 LERP 阻尼滑动系统 (Widescreen 960x540)
# ==============================================================================
class DesktopManager:
    def __init__(self, window_terminal, window_clock):
        self.window_terminal = window_terminal
        self.window_clock = window_clock
        self.windows = [window_clock, window_terminal]
        
        # 交互状态
        self.start_menu_open = False
        self.should_exit = False
        self.dragging_win = None
        self.mouse_is_down = False
        
        # 拖拽时格点定位偏置
        self.drag_cell_offset_x = 0
        self.drag_cell_offset_y = 0

    def focus_window(self, win):
        """将窗口拉到最前端激活"""
        if win in self.windows:
            self.windows.remove(win)
            self.windows.append(win)

    def draw_wallpaper(self, buffer):
        """绘制超高级的浅色护眼极光微光壁纸 (冰晶蓝 #d7e6f5 到 纯净白 #fafbff)"""
        # 1. 模拟顶部漫反射极光圆心 (cx=480, cy=-100) 的白色微光渲染，向外扩散交融
        for y in range(HEIGHT):
            row_offset = y * WIDTH * 4
            ratio = y / (HEIGHT - 1)
            
            # 使用横向采样，16 像素块提速以确保 50 FPS 满帧流出
            for x in range(0, WIDTH, 16):
                dx = x - 480
                dy = y + 100
                dist = math.sqrt(dx*dx + dy*dy)
                glow = max(0.0, 1.0 - dist / 600.0)
                
                # 浅冰蓝色 (#d7e6f5) 与 纯净白 (#fafbfc) 的双线性放射融合
                r = int(215 * (1 - ratio) + 245 * ratio + 35 * glow)
                g = int(228 * (1 - ratio) + 248 * ratio + 22 * glow)
                b = int(245 * (1 - ratio) + 252 * ratio + 8 * glow)
                
                # 安全边界约束
                r = min(255, max(0, r))
                g = min(255, max(0, g))
                b = min(255, max(0, b))
                
                pixel_bytes = bytes([r, g, b, 255])
                buffer[row_offset + x*4 : row_offset + (x+16)*4] = pixel_bytes * 16
                
        # 2. 绘制极简淡灰色背景星点 (代替网格线)
        star_color = (185, 192, 210)
        for y in range(30, HEIGHT - 60, 60):
            row_offset = y * WIDTH * 4
            for x in range(30, WIDTH, 60):
                idx = row_offset + x * 4
                buffer[idx]     = star_color[0]
                buffer[idx+1]   = star_color[1]
                buffer[idx+2]   = star_color[2]
                buffer[idx+3]   = 255
                
        # 3. 浅色桌面下方极简属性水印
        draw_string(buffer, 30, HEIGHT - 55, "KITTYWM LIGHT OS V2.5", (125, 135, 155), scale=1, spacing=1)
        draw_string(buffer, 30, HEIGHT - 42, "FLUID SMOOTH LERP WINDOW MANAGER", (150, 158, 178), scale=1, spacing=1)

    def draw_dock(self, buffer):
        """绘制浅色极简毛玻璃 Dock 栏"""
        # Dock 浮动位置居中偏下: x: 260 ~ 700 (宽 440), y: 485 ~ 525 (高 40)
        # 白色磨砂半透明胶囊底座 (#ffffff, 不透明度 185)
        draw_rect(buffer, 260, 485, 700, 525, (255, 255, 255, 185))
        draw_rect_outline(buffer, 260, 485, 700, 525, (190, 195, 215, 100), thickness=1)
        
        # [START] 菜单按钮 (x: 275 ~ 335)
        start_bg = (0, 150, 255) if self.start_menu_open else (235, 238, 245)
        draw_rect(buffer, 275, 490, 335, 520, start_bg)
        draw_rect_outline(buffer, 275, 490, 335, 520, (190, 195, 215), thickness=1)
        
        start_txt_color = (255, 255, 255) if self.start_menu_open else (70, 75, 90)
        draw_string(buffer, 287, 499, "START", start_txt_color, scale=1, spacing=1)
        
        # [TERMINAL] (x: 345 ~ 430)
        t_vis = self.window_terminal.visible
        draw_rect(buffer, 345, 490, 430, 520, (230, 235, 248) if t_vis else (255, 255, 255))
        draw_rect_outline(buffer, 345, 490, 430, 520, (0, 150, 255) if t_vis else (200, 205, 220), thickness=1)
        draw_string(buffer, 357, 499, "TERMINAL", (33, 37, 41) if t_vis else (120, 125, 140), scale=1, spacing=1)
        # macOS 风格蓝色运行点
        if t_vis:
            draw_rect(buffer, 382, 517, 392, 519, (0, 150, 255))
            
        # [CLOCK] (x: 440 ~ 515)
        c_vis = self.window_clock.visible
        draw_rect(buffer, 440, 490, 515, 520, (230, 235, 248) if c_vis else (255, 255, 255))
        draw_rect_outline(buffer, 440, 490, 515, 520, (0, 150, 255) if c_vis else (200, 205, 220), thickness=1)
        draw_string(buffer, 457, 499, "CLOCK", (33, 37, 41) if c_vis else (120, 125, 140), scale=1, spacing=1)
        if c_vis:
            draw_rect(buffer, 472, 517, 482, 519, (0, 150, 255))
            
        # Dock 右侧的数字 LED 时间显示 (深灰色)
        time_str = time.strftime("%H:%M:%S", time.localtime())
        draw_rect(buffer, 590, 490, 685, 520, (245, 247, 250))
        draw_rect_outline(buffer, 590, 490, 685, 520, (200, 205, 220), thickness=1)
        draw_string(buffer, 606, 499, time_str, (0, 110, 160), scale=1, spacing=1)

    def draw_start_menu(self, buffer):
        """绘制浅色毛玻璃开始菜单"""
        if not self.start_menu_open:
            return
        # 开始菜单弹出面板: x: 275 ~ 425, y: 325 ~ 480
        draw_rect(buffer, 275, 325, 425, 480, (255, 255, 255, 230))
        draw_rect_outline(buffer, 275, 325, 425, 480, (0, 150, 255), thickness=2)
        
        # REOPEN ALL
        draw_rect(buffer, 279, 330, 421, 370, (240, 243, 250))
        draw_string(buffer, 297, 345, "REOPEN ALL", (33, 37, 41), scale=1, spacing=1)
        
        # SCREENSHOT
        draw_rect(buffer, 279, 380, 421, 420, (240, 243, 250))
        draw_string(buffer, 297, 395, "SCREENSHOT", (33, 37, 41), scale=1, spacing=1)
        
        # SHUTDOWN
        draw_rect(buffer, 279, 430, 421, 470, (255, 95, 87))
        draw_string(buffer, 297, 445, "SHUTDOWN", (255, 255, 255), scale=1, spacing=1)

    def handle_mouse(self, matches, start_col, start_row, target_cols, target_rows):
        """格点目标锁定触发总线"""
        cell_w = WIDTH / target_cols
        cell_h = HEIGHT / target_rows

        for match in matches:
            button = int(match[0])
            cx = int(match[1])
            cy = int(match[2])
            is_press = match[3] == 'M'

            relative_cx = cx - start_col
            relative_cy = cy - start_row
            
            if hasattr(self, "log_message"):
                self.log_message(f"Mouse Event: Button={button}, Pressed={is_press} | GridCol={cx}, GridRow={cy}")

            if 0 <= relative_cx < target_cols and 0 <= relative_cy < target_rows:
                rx = (relative_cx + 0.5) / target_cols
                ry = (relative_cy + 0.5) / target_rows
                
                px = int(rx * WIDTH)
                py = int(ry * HEIGHT)

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
                        
                        # (B) 检测击中可见窗口
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
                                # 击中了左侧的红色关闭小圆圈
                                if clicked_win.x + 11 <= px < clicked_win.x + 21:
                                    clicked_win.visible = False
                                    self.window_terminal.terminal_history.append(f"CLOSED: {clicked_win.title}")
                                else:
                                    # 启动绝对坐标阻尼格点对齐算法！
                                    # 锁定目标拖拽格点偏置量
                                    self.dragging_win = clicked_win
                                    self.drag_cell_offset_x = relative_cx - (clicked_win.x / cell_w)
                                    self.drag_cell_offset_y = relative_cy - (clicked_win.y / cell_h)
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
                        self.mouse_is_down = False
                        self.dragging_win = None

                # 鼠标拖动 (button == 32)
                elif button == 32:
                    if self.dragging_win:
                        # 锁定目标格点的精准像素位置为 target_x/target_y
                        cell_target_x = relative_cx - self.drag_cell_offset_x
                        cell_target_y = relative_cy - self.drag_cell_offset_y
                        
                        # 计算严格的目标格点像素，不直接写入 win.x/y 而是由 LERP 平滑缓动它！
                        target_x = int(round(cell_target_x * cell_w))
                        target_y = int(round(cell_target_y * cell_h))
                        
                        self.dragging_win.target_x = max(-self.dragging_win.w + 30, min(WIDTH - 30, target_x))
                        self.dragging_win.target_y = max(0, min(HEIGHT - 40, target_y))

            # 全局松开
            if not is_press:
                self.mouse_is_down = False
                self.dragging_win = None

    def save_screenshot(self):
        try:
            scr_png = encode_png(self.screenshot_buffer, WIDTH, HEIGHT)
            with open("screenshot.png", "wb") as f:
                f.write(scr_png)
            self.window_terminal.terminal_history.append("SCREENSHOT CAPTURED TO SCREENSHOT.PNG")
        except Exception as ex:
            self.window_terminal.terminal_history.append(f"SCREENSHOT ERROR: {str(ex)[:15]}")

    def render_all(self, buffer):
        # 1. 物理层平滑阻尼 LERP 缓动计算 (滑行动画的核心)
        # 本系统在主循环 50 FPS 的高频下运行，每帧窗口当前 x/y 向目标 x/y 滑动 25% 距离，
        # 这在视觉上以 sub-pixel 水平彻底消融了物理终端 11px/22px 的格点阶跃感，呈现流畅无比的苹果式果冻滑动！
        for win in self.windows:
            if win.visible:
                # 缓动推进公式
                win.x += (win.target_x - win.x) * 0.25
                win.y += (win.target_y - win.y) * 0.25
                # 微小偏置直接吸附
                if abs(win.x - win.target_x) < 0.5:
                    win.x = win.target_x
                if abs(win.y - win.target_y) < 0.5:
                    win.y = win.target_y

        self.draw_wallpaper(buffer)
        
        # Z-Order 判定
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
