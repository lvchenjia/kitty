import time
import math
import random
from kitty_wm.window import Window
from kitty_wm.engine import draw_rect, draw_rect_outline, draw_circle, draw_circle_outline, draw_line, draw_thick_line, draw_string

# ==============================================================================
# 📟 MODERN TERMINAL CONSOLE 窗口应用类 (极简现代风格)
# ==============================================================================
class TerminalWindow(Window):
    def __init__(self, win_id, title, x, y, w, h):
        super().__init__(win_id, title, x, y, w, h)
        self.terminal_input = ""
        self.terminal_history = [
            "KITTYWM MODERN OS [VERSION 2.5]",
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
            self.terminal_history.append("  NEOFETCH - RENDER MODERN SYS INFO")
            self.terminal_history.append("  CLEAR    - WIPE SCREEN BUFFER")
            self.terminal_history.append("  CLOCK    - TOGGLE CLOCK APP")
            self.terminal_history.append("  EXIT     - SHUTDOWN MODERN OS")
        elif base_cmd == "ls":
            self.terminal_history.append("PATH: /home/guest/kitty/")
            self.terminal_history.append("  cube.py         pixel_donut.c")
            self.terminal_history.append("  pixel_cube.py   pixel_donut.py")
            self.terminal_history.append("  kitty_wm/       readme.md")
        elif base_cmd == "neofetch":
            self.terminal_history.append("  *  /\\  *     OS: KittyWM Modern OS")
            self.terminal_history.append("    /  \\       HOST: Apple M4 Pro Powerhouse")
            self.terminal_history.append("   /____\\      SHELL: zsh (kitty-sh)")
            self.terminal_history.append("  *      *     GRAPHICS: Kitty Protocol")
            self.terminal_history.append("               THEME: Cyber-Cyan & Electric-Magenta")
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
            
        # 约束行数，防止字符越出下边框
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
        # 现代 IDE 风格暗黑终端底色
        curr_y = self.y + 36
        for line in self.terminal_history:
            # 现代配色体系：指令显示为电光粉，成功/路径为电光青，其它为优雅暖白
            line_color = (0, 240, 255) if "os:" in line.lower() or "host:" in line.lower() or "theme:" in line.lower() else (230, 235, 245)
            if line.startswith("guest@kittywm"):
                line_color = (255, 0, 128)  # 霓虹电光粉 Prompt
            draw_string(buffer, self.x + 16, curr_y, line, line_color, scale=1, spacing=1)
            curr_y += 13
            
        # 呼吸输入提示符
        cursor_visible = (int(time.time() * 2) % 2 == 0) and is_focused
        prompt = f"guest@kittywm ~ % {self.terminal_input}"
        draw_string(buffer, self.x + 16, curr_y, prompt, (255, 0, 128), scale=1, spacing=1)
        if cursor_visible:
            cx_pos = self.x + 16 + len(prompt) * 6
            # 现代纤细竖线光标，代替粗方块
            draw_rect(buffer, cx_pos, curr_y, cx_pos + 1, curr_y + 8, (255, 255, 255))

    def draw(self, buffer, is_focused):
        if not self.visible:
            return
        super().draw(buffer, is_focused)
        self.draw_content(buffer, is_focused)


# ==============================================================================
# 🕰️ MINIMALIST NEON CLOCK 窗口应用类 (极简现代太空风格)
# ==============================================================================
class ClockWindow(Window):
    def __init__(self, win_id, title, x, y, w, h):
        super().__init__(win_id, title, x, y, w, h)

    def draw_content(self, buffer, is_focused):
        t_struct = time.localtime()
        time_str = time.strftime("%H:%M:%S", t_struct)
        
        # 1. 极简 LED 数字面板
        draw_string(buffer, self.x + self.w // 2 - 32, self.y + 36, time_str, (0, 240, 255), scale=1, spacing=1)
        
        # 2. 极简太空感表盘面 (y-offset ~ self.y + self.h - 55)
        cx = self.x + self.w // 2
        cy = self.y + self.h - 55
        
        # 外表盘：超细霓虹粉光环
        draw_circle_outline(buffer, cx, cy, 42, (255, 0, 128), thickness=1)
        draw_circle(buffer, cx, cy, 2, (255, 255, 255))
        
        # 表盘 12, 3, 6, 9 点极简刻度点
        draw_rect(buffer, cx - 1, cy - 38, cx + 1, cy - 36, (0, 240, 255)) # 12
        draw_rect(buffer, cx - 1, cy + 36, cx + 1, cy + 38, (0, 240, 255)) # 6
        draw_rect(buffer, cx + 36, cy - 1, cx + 38, cy + 1, (0, 240, 255)) # 3
        draw_rect(buffer, cx - 38, cy - 1, cx - 36, cy + 1, (0, 240, 255)) # 9
        
        h, m, s = t_struct.tm_hour, t_struct.tm_min, t_struct.tm_sec
        theta_h = 2.0 * math.pi * (h % 12 + m / 60.0) / 12.0
        theta_m = 2.0 * math.pi * m / 60.0
        theta_s = 2.0 * math.pi * s / 60.0
        
        # 极薄现代色指针
        # 时针: 霓虹青色
        hx = int(cx + 18 * math.sin(theta_h))
        hy = int(cy - 18 * math.cos(theta_h))
        draw_thick_line(buffer, cx, cy, hx, hy, (0, 240, 255), thickness=1.5)
        
        # 分针: 白色
        mx = int(cx + 28 * math.sin(theta_m))
        my = int(cy - 28 * math.cos(theta_m))
        draw_line(buffer, cx, cy, mx, my, (255, 255, 255))
        
        # 秒针: 超细霓虹粉色
        sx = int(cx + 34 * math.sin(theta_s))
        sy = int(cy - 34 * math.cos(theta_s))
        draw_line(buffer, cx, cy, sx, sy, (255, 0, 128))

    def draw(self, buffer, is_focused):
        if not self.visible:
            return
        super().draw(buffer, is_focused)
        self.draw_content(buffer, is_focused)
