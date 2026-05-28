import time
from kitty_wm.engine import draw_rect, draw_rect_outline, draw_string, encode_png, send_image_via_kitty, WIDTH, HEIGHT

# ==============================================================================
# 🖥️ KittyWM 桌面管理类 (壁纸、浮动 Dock、开始菜单、事件分发)
# ==============================================================================
class DesktopManager:
    def __init__(self, window_terminal, window_clock, window_sysmon):
        self.window_terminal = window_terminal
        self.window_clock = window_clock
        self.window_sysmon = window_sysmon
        self.windows = [window_sysmon, window_clock, window_terminal]
        
        # 状态变量
        self.start_menu_open = False
        self.should_exit = False
        self.dragging_win = None
        self.mouse_is_down = False

    def focus_window(self, win):
        """将选定窗口置顶激活"""
        if win in self.windows:
            self.windows.remove(win)
            self.windows.append(win)

    def draw_wallpaper(self, buffer):
        """绘制超炫的极光霓虹渐变桌面壁纸 (Widescreen 960x540)"""
        # 1. 绘制从深空蓝 (#0a0a14) 过渡到魅惑紫 (#2a103c) 的渐变
        for y in range(HEIGHT):
            ratio = y / (HEIGHT - 1)
            r = int(10 * (1 - ratio) + 38 * ratio)
            g = int(10 * (1 - ratio) + 12 * ratio)
            b = int(22 * (1 - ratio) + 52 * ratio)
            
            row_offset = y * WIDTH * 4
            pixel_bytes = bytes([r, g, b, 255])
            buffer[row_offset : row_offset + WIDTH * 4] = pixel_bytes * WIDTH
            
        # 2. 绘制深灰色的科幻网络交错虚线 (48像素网格间距)
        grid_color = (20, 21, 32)
        for y in range(0, HEIGHT, 48):
            draw_rect(buffer, 0, y, WIDTH - 1, y, grid_color)
        for x in range(0, WIDTH, 48):
            draw_rect(buffer, x, 0, x, HEIGHT - 1, grid_color)
            
        # 3. 桌面暗纹水印文字
        draw_string(buffer, 30, HEIGHT - 75, "KITTYWM OS V2.0", (75, 80, 105), scale=1, spacing=1)
        draw_string(buffer, 30, HEIGHT - 60, "WIDESCREEN DESKTOP ENVIRONMENT", (60, 64, 85), scale=1, spacing=1)

    def draw_dock(self, buffer):
        """绘制现代毛玻璃效果的浮动 Dock 工具栏 (浮动在底部)"""
        # Dock 主体位置: x: 120 ~ 840 (宽度 720), y: 490 ~ 530 (高度 40)
        # 绘制半透明磨砂质感背景
        draw_rect(buffer, 120, 490, 840, 530, (26, 28, 38, 160))
        # 霓虹电光青色圆润描边
        draw_rect_outline(buffer, 120, 490, 840, 530, (0, 208, 255, 180), thickness=2)
        
        # 1. 开始菜单按钮 (x: 130 ~ 200, y: 495 ~ 525)
        start_bg = (0, 208, 255) if self.start_menu_open else (38, 42, 58)
        draw_rect(buffer, 130, 495, 200, 525, start_bg)
        draw_rect_outline(buffer, 130, 495, 200, 525, (255, 255, 255), thickness=1)
        draw_string(buffer, 146, 504, "START", (255, 255, 255), scale=1, spacing=1)
        
        # 2. 快捷程序图标按钮
        # [TERMINAL] (x: 210 ~ 295, y: 495 ~ 525)
        t_vis = self.window_terminal.visible
        draw_rect(buffer, 210, 495, 295, 525, (50, 55, 75) if t_vis else (34, 37, 48))
        draw_rect_outline(buffer, 210, 495, 295, 525, (0, 208, 255) if t_vis else (60, 64, 80), thickness=1)
        draw_string(buffer, 222, 504, "TERMINAL", (255, 255, 255) if t_vis else (140, 140, 150), scale=1, spacing=1)
        
        # [CLOCK] (x: 305 ~ 380, y: 495 ~ 525)
        c_vis = self.window_clock.visible
        draw_rect(buffer, 305, 495, 380, 525, (50, 55, 75) if c_vis else (34, 37, 48))
        draw_rect_outline(buffer, 305, 495, 380, 525, (0, 208, 255) if c_vis else (60, 64, 80), thickness=1)
        draw_string(buffer, 322, 504, "CLOCK", (255, 255, 255) if c_vis else (140, 140, 150), scale=1, spacing=1)
        
        # [MONITOR] (x: 390 ~ 470, y: 495 ~ 525)
        m_vis = self.window_sysmon.visible
        draw_rect(buffer, 390, 495, 470, 525, (50, 55, 75) if m_vis else (34, 37, 48))
        draw_rect_outline(buffer, 390, 495, 470, 525, (0, 208, 255) if m_vis else (60, 64, 80), thickness=1)
        draw_string(buffer, 404, 504, "MONITOR", (255, 255, 255) if m_vis else (140, 140, 150), scale=1, spacing=1)
        
        # 3. 浮动 Dock 右侧的高级 LED 状态时钟 (x: 730 ~ 830, y: 495 ~ 525)
        time_str = time.strftime("%H:%M:%S", time.localtime())
        draw_rect(buffer, 730, 495, 830, 525, (16, 17, 22))
        draw_rect_outline(buffer, 730, 495, 830, 525, (45, 48, 60), thickness=1)
        draw_string(buffer, 746, 504, time_str, (0, 208, 255), scale=1, spacing=1)

    def draw_start_menu(self, buffer):
        """绘制浮动在 Dock 上方的开始菜单弹窗"""
        if not self.start_menu_open:
            return
        # 开始菜单弹出面板: x: 130 ~ 280 (宽度 150), y: 330 ~ 485 (高度 155)
        draw_rect(buffer, 130, 330, 280, 485, (30, 30, 38, 230))
        draw_rect_outline(buffer, 130, 330, 280, 485, (0, 208, 255), thickness=2)
        
        # 菜单子项 1: REOPEN ALL (y: 335 ~ 375)
        draw_rect(buffer, 134, 335, 276, 375, (45, 48, 64))
        draw_string(buffer, 152, 350, "REOPEN ALL", (255, 255, 255), scale=1, spacing=1)
        
        # 菜单子项 2: SCREENSHOT (y: 385 ~ 425)
        draw_rect(buffer, 134, 385, 276, 425, (45, 48, 64))
        draw_string(buffer, 152, 400, "SCREENSHOT", (255, 255, 255), scale=1, spacing=1)
        
        # 菜单子项 3: SHUTDOWN (y: 435 ~ 475)
        draw_rect(buffer, 134, 435, 276, 475, (190, 50, 50))
        draw_string(buffer, 152, 450, "SHUTDOWN", (255, 255, 255), scale=1, spacing=1)

    def handle_mouse(self, matches, start_col, start_row, target_cols, target_rows):
        """极其稳健的 Z-Order 鼠标点击与拖拽分发器 (带全量日志诊断)"""
        for match in matches:
            button = int(match[0])
            cx = int(match[1])
            cy = int(match[2])
            is_press = match[3] == 'M'

            # 映射物理像素坐标
            relative_cx = cx - start_col
            relative_cy = cy - start_row
            
            # 记录基础的 SGR 报文日志
            if hasattr(self, "log_message"):
                self.log_message(f"Mouse Event Parsed: Button={button}, Col={cx}, Row={cy}, Pressed={is_press} | RelCol={relative_cx}, RelRow={relative_cy}")

            if 0 <= relative_cx < target_cols and 0 <= relative_cy < target_rows:
                rx = (relative_cx + 0.5) / target_cols
                ry = (relative_cy + 0.5) / target_rows
                
                px = int(rx * WIDTH)
                py = int(ry * HEIGHT)

                if hasattr(self, "log_message"):
                    self.log_message(f"Mapped coordinates: px={px}, py={py}")

                # 鼠标左键操作
                if button == 0:
                    if is_press:
                        self.mouse_is_down = True
                        if hasattr(self, "log_message"):
                            self.log_message(f"Left Button Click (Press) at ({px}, {py})")

                        # (A) 开始菜单有效区域判定
                        if self.start_menu_open and 130 <= px < 280 and 330 <= py < 485:
                            if hasattr(self, "log_message"):
                                self.log_message("Click matched Start Menu.")
                            if 335 <= py < 375:  # REOPEN ALL
                                self.window_terminal.visible = True
                                self.window_clock.visible = True
                                self.window_sysmon.visible = True
                                for w in [self.window_sysmon, self.window_clock, self.window_terminal]:
                                    self.focus_window(w)
                                self.window_terminal.terminal_history.append("ALL WINDOWS RESTORED.")
                                self.start_menu_open = False
                            elif 385 <= py < 425:  # SCREENSHOT
                                self.save_screenshot()
                                self.start_menu_open = False
                            elif 435 <= py < 475:  # SHUTDOWN
                                self.should_exit = True
                            continue
                        else:
                            self.start_menu_open = False
                        
                        # (B) 遍历检测是否击中任何活跃可见窗口 (按照 Z-Order 从顶至底)
                        clicked_win = None
                        for win in reversed(self.windows):
                            if win.visible:
                                if win.x <= px < win.x + win.w and win.y <= py < win.y + win.h:
                                    clicked_win = win
                                    break
                                    
                        if clicked_win:
                            self.focus_window(clicked_win)
                            if hasattr(self, "log_message"):
                                self.log_message(f"Window Clicked: {clicked_win.title} (x={clicked_win.x}, y={clicked_win.y}, w={clicked_win.w}, h={clicked_win.h})")
                            
                            # 是否点击在标题栏内 (高 26 像素)
                            if py < clicked_win.y + 26:
                                # 检查是否击中了左侧的红色关闭圆圈 (x: clicked_win.x + 11 ~ 21)
                                if clicked_win.x + 11 <= px < clicked_win.x + 21:
                                    clicked_win.visible = False
                                    self.window_terminal.terminal_history.append(f"CLOSED: {clicked_win.title}")
                                    if hasattr(self, "log_message"):
                                        self.log_message(f"Window Closed via macOS red dot: {clicked_win.title}")
                                else:
                                    # 启动绝对安全的窗口拖拽机制
                                    self.dragging_win = clicked_win
                                    self.dragging_win.drag_offset_x = px - clicked_win.x
                                    self.dragging_win.drag_offset_y = py - clicked_win.y
                                    if hasattr(self, "log_message"):
                                        self.log_message(f"Drag Started on Window: {clicked_win.title} (Offsets: {clicked_win.drag_offset_x}, {clicked_win.drag_offset_y})")
                            continue
                        
                        # (C) 检测点击 Dock 栏区域 (y: 490 ~ 530)
                        if 490 <= py < 530:
                            if hasattr(self, "log_message"):
                                self.log_message("Click matched Dock area.")
                            # 开始按钮 (x: 130 ~ 200)
                            if 130 <= px < 200:
                                self.start_menu_open = not self.start_menu_open
                            # [TERMINAL] (x: 210 ~ 295)
                            elif 210 <= px < 295:
                                self.window_terminal.visible = not self.window_terminal.visible
                                if self.window_terminal.visible:
                                    self.focus_window(self.window_terminal)
                            # [CLOCK] (x: 305 ~ 380)
                            elif 305 <= px < 380:
                                self.window_clock.visible = not self.window_clock.visible
                                if self.window_clock.visible:
                                    self.focus_window(self.window_clock)
                            # [MONITOR] (x: 390 ~ 470)
                            elif 390 <= px < 470:
                                self.window_sysmon.visible = not self.window_sysmon.visible
                                if self.window_sysmon.visible:
                                    self.focus_window(self.window_sysmon)
                    else:
                        # 释放左键
                        if hasattr(self, "log_message"):
                            self.log_message("Left Button Released.")
                        self.mouse_is_down = False
                        self.dragging_win = None

                # 鼠标拖动 (button == 32)
                elif button == 32:
                    if self.dragging_win:
                        new_x = px - self.dragging_win.drag_offset_x
                        new_y = py - self.dragging_win.drag_offset_y
                        self.dragging_win.x = max(-self.dragging_win.w + 30, min(WIDTH - 30, new_x))
                        self.dragging_win.y = max(0, min(HEIGHT - 40, new_y))
                        if hasattr(self, "log_message"):
                            self.log_message(f"Dragging Window {self.dragging_win.title} -> NewPos: ({self.dragging_win.x}, {self.dragging_win.y})")

            # 任何松开事件，强制释放所有拖拽锚点，避免粘滞
            if not is_press:
                if hasattr(self, "log_message") and (self.mouse_is_down or self.dragging_win):
                    self.log_message("Global Mouse Release Triggered.")
                self.mouse_is_down = False
                self.dragging_win = None

    def save_screenshot(self):
        """保存全屏像素截图到本地文件"""
        try:
            scr_png = encode_png(self.screenshot_buffer, WIDTH, HEIGHT)
            with open("screenshot.png", "wb") as f:
                f.write(scr_png)
            self.window_terminal.terminal_history.append("SCREENSHOT SAVED TO SCREENSHOT.PNG")
        except Exception as ex:
            self.window_terminal.terminal_history.append(f"SCREENSHOT ERROR: {str(ex)[:15]}")

    def render_all(self, buffer):
        """组装整个画板图层并提供双缓冲备份 (供截屏使用)"""
        self.draw_wallpaper(buffer)
        
        # 激活最上层可见窗口标识
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
        
        # 将成品数据深度克隆一份，保证截屏瞬间抓取完美图像
        self.screenshot_buffer = bytearray(buffer)
