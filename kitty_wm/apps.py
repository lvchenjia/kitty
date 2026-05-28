import time
import math
import random
from kitty_wm.window import Window
from kitty_wm.engine import draw_rect, draw_rect_outline, draw_circle, draw_circle_outline, draw_line, draw_thick_line, draw_string

# ==============================================================================
# 📟 MODERN LIGHT MODE TERMINAL 窗口应用类
# ==============================================================================
class TerminalWindow(Window):
    def __init__(self, win_id, title, x, y, w, h):
        super().__init__(win_id, title, x, y, w, h)
        self.terminal_input = ""
        self.terminal_history = [
            "KITTYWM MODERN LIGHT OS [VERSION 2.5]",
            "(C) 2026 ANTIGRAVITY ENGINE. ALL RIGHTS RESERVED.",
            "TYPE 'HELP' FOR SYSTEM INSTRUCTIONS.",
            "",
        ]

    def execute_command(self, cmd, app_manager):
        cmd = cmd.strip()
        if not cmd:
            self.terminal_history.append("guest@kittywm ~ %")
            return
            
        self.terminal_history.append(f"guest@kittywm ~ % {cmd}")
        parts = cmd.lower().split()
        base_cmd = parts[0]
        
        if base_cmd == "help":
            self.terminal_history.append("SYSTEM UTILITIES:")
            self.terminal_history.append("  HELP     - DISPLAY GUIDE")
            self.terminal_history.append("  LS       - SHOW FILE STRUCTURE")
            self.terminal_history.append("  NEOFETCH - RENDER SYSTEM INFO")
            self.terminal_history.append("  CLEAR    - WIPE SCREEN BUFFER")
            self.terminal_history.append("  CLOCK    - TOGGLE CLOCK APP")
            self.terminal_history.append("  EXIT     - SHUTDOWN LIGHT OS")
        elif base_cmd == "ls":
            self.terminal_history.append("PATH: /home/guest/kitty/")
            self.terminal_history.append("  cube.py         pixel_donut.c")
            self.terminal_history.append("  pixel_cube.py   pixel_donut.py")
            self.terminal_history.append("  kitty_wm/       readme.md")
        elif base_cmd == "neofetch":
            self.terminal_history.append("  *  /\\  *     OS: KittyWM Light OS")
            self.terminal_history.append("    /  \\       HOST: Apple M4 Pro Powerhouse")
            self.terminal_history.append("   /____\\      SHELL: zsh (kitty-sh)")
            self.terminal_history.append("  *      *     GRAPHICS: Kitty Protocol")
            self.terminal_history.append("               THEME: Ice-Blue Light Mode")
        elif base_cmd == "clear":
            self.terminal_history.clear()
        elif base_cmd == "clock":
            app_manager.window_clock.visible = not app_manager.window_clock.visible
            if app_manager.window_clock.visible:
                app_manager.focus_window(app_manager.window_clock)
            self.terminal_history.append("CLOCK WINDOW TOGGLED.")
        elif base_cmd == "exit":
            app_manager.should_exit = True
        else:
            self.terminal_history.append(f"shell: command not found: '{base_cmd}'")
            
        while len(self.terminal_history) > 13:
            self.terminal_history.pop(0)

    def handle_keyboard(self, clean_keys, app_manager):
        for char in clean_keys:
            if char == '\x7f' or char == '\x08':  # Backspace
                if len(self.terminal_input) > 0:
                    self.terminal_input = self.terminal_input[:-1]
            elif char in ('\r', '\n'):  # Enter
                self.execute_command(self.terminal_input, app_manager)
                self.terminal_input = ""
            elif 32 <= ord(char) <= 126:  # Printable chars
                if len(self.terminal_input) < 40:
                    self.terminal_input += char

    def draw_content(self, buffer, is_focused):
        # 极简浅色护眼文本配色 (起点 y=36)
        curr_y = int(self.y) + 36
        for line in self.terminal_history:
            # 浅色系科学配色：指令提示符为优雅深红紫色，系统反馈为高级天蓝/靛蓝，普通文本为深灰色
            line_color = (0, 110, 160) if "os:" in line.lower() or "host:" in line.lower() or "theme:" in line.lower() else (45, 55, 75)
            if line.startswith("guest@kittywm"):
                line_color = (190, 20, 110)  # 优雅紫红色 Prompt
            draw_string(buffer, int(self.x) + 16, curr_y, line, line_color, scale=1, spacing=1)
            curr_y += 13
            
        cursor_visible = (int(time.time() * 2) % 2 == 0) and is_focused
        prompt = f"guest@kittywm ~ % {self.terminal_input}"
        draw_string(buffer, int(self.x) + 16, curr_y, prompt, (190, 20, 110), scale=1, spacing=1)
        if cursor_visible:
            cx_pos = int(self.x) + 16 + len(prompt) * 6
            # 纤细现代黑色竖线光标
            draw_rect(buffer, cx_pos, curr_y, cx_pos + 1, curr_y + 8, (33, 37, 41))

    def draw(self, buffer, is_focused):
        if not self.visible:
            return
        super().draw(buffer, is_focused)
        self.draw_content(buffer, is_focused)


# ==============================================================================
# 🕰️ MINIMALIST LIGHT CLOCK 窗口应用类
# ==============================================================================
class ClockWindow(Window):
    def __init__(self, win_id, title, x, y, w, h):
        super().__init__(win_id, title, x, y, w, h)

    def draw_content(self, buffer, is_focused):
        t_struct = time.localtime()
        time_str = time.strftime("%H:%M:%S", t_struct)
        
        # 1. 优雅数字时间面板 (深靛蓝色)
        draw_string(buffer, int(self.x) + self.w // 2 - 32, int(self.y) + 36, time_str, (0, 110, 160), scale=1, spacing=1)
        
        # 2. 指针表盘 (y-offset ~ self.y + self.h - 55)
        cx = int(self.x) + self.w // 2
        cy = int(self.y) + self.h - 55
        
        # 极细的外圆盘环线 (优雅天蓝 #0096ff)
        draw_circle_outline(buffer, cx, cy, 42, (0, 150, 255), thickness=1)
        draw_circle(buffer, cx, cy, 2, (33, 37, 41))
        
        # 12, 3, 6, 9 极简刻度
        draw_rect(buffer, cx - 1, cy - 38, cx + 1, cy - 36, (0, 150, 255))
        draw_rect(buffer, cx - 1, cy + 36, cx + 1, cy + 38, (0, 150, 255))
        draw_rect(buffer, cx + 36, cy - 1, cx + 38, cy + 1, (0, 150, 255))
        draw_rect(buffer, cx - 38, cy - 1, cx - 36, cy + 1, (0, 150, 255))
        
        h, m, s = t_struct.tm_hour, t_struct.tm_min, t_struct.tm_sec
        theta_h = 2.0 * math.pi * (h % 12 + m / 60.0) / 12.0
        theta_m = 2.0 * math.pi * m / 60.0
        theta_s = 2.0 * math.pi * s / 60.0
        
        # 时针 (天蓝色)
        hx = int(cx + 18 * math.sin(theta_h))
        hy = int(cy - 18 * math.cos(theta_h))
        draw_thick_line(buffer, cx, cy, hx, hy, (0, 150, 255), thickness=1.5)
        
        # 分针 (深石墨灰)
        mx = int(cx + 28 * math.sin(theta_m))
        my = int(cy - 28 * math.cos(theta_m))
        draw_line(buffer, cx, cy, mx, my, (70, 75, 90))
        
        # 秒针 (优雅粉红紫)
        sx = int(cx + 34 * math.sin(theta_s))
        sy = int(cy - 34 * math.cos(theta_s))
        draw_line(buffer, cx, cy, sx, sy, (190, 20, 110))

    def draw(self, buffer, is_focused):
        if not self.visible:
            return
        super().draw(buffer, is_focused)
        self.draw_content(buffer, is_focused)
