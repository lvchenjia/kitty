import time
import math
import random
from kitty_wm.window import Window
from kitty_wm.engine import draw_rect, draw_rect_outline, draw_circle, draw_circle_outline, draw_line, draw_thick_line, draw_string

# ==============================================================================
# 📟 TERMINAL CONSOLE 窗口应用类
# ==============================================================================
class TerminalWindow(Window):
    def __init__(self, win_id, title, x, y, w, h):
        super().__init__(win_id, title, x, y, w, h)
        self.terminal_input = ""
        self.terminal_history = [
            "WELCOME TO KITTYWM WIDESCREEN DE V2.0",
            "TYPE 'HELP' FOR ALL AVAILABLE COMMANDS.",
            "",
        ]

    def execute_command(self, cmd, app_manager):
        cmd = cmd.strip()
        if not cmd:
            self.terminal_history.append("kitty> ")
            return
            
        self.terminal_history.append(f"kitty> {cmd}")
        parts = cmd.lower().split()
        base_cmd = parts[0]
        
        if base_cmd == "help":
            self.terminal_history.append("AVAILABLE COMMANDS:")
            self.terminal_history.append("  HELP     - DISPLAY GUIDE")
            self.terminal_history.append("  LS       - LIST DIRECTORY FILES")
            self.terminal_history.append("  NEOFETCH - SHOW SYSTEM STATS")
            self.terminal_history.append("  CLEAR    - WIPE SHELL OUTPUT")
            self.terminal_history.append("  CLOCK    - LAUNCH CLOCK WINDOW")
            self.terminal_history.append("  MONITOR  - OPEN SYSTEM MONITOR")
            self.terminal_history.append("  EXIT     - SHUTDOWN KITTYWM")
        elif base_cmd == "ls":
            self.terminal_history.append("DIRECTORY: DESKTOP/KITTY/")
            self.terminal_history.append("  CUBE.PY         PIXEL_DONUT.C")
            self.terminal_history.append("  PIXEL_CUBE.PY   PIXEL_DONUT.PY")
            self.terminal_history.append("  KITTY_WM/       README.MD")
        elif base_cmd == "neofetch":
            self.terminal_history.append("  .---.    OS: KITTYWM WIDESCREEN DE")
            self.terminal_history.append("  |o o|    HOST: MAC M4 PRO POWERED")
            self.terminal_history.append("  | - |    SHELL: KITTY-SH 2.0")
            self.terminal_history.append("  '---'    WM: KITTY-WINDOW-MGR")
            self.terminal_history.append("           RES: 960X540 WIDESCREEN")
        elif base_cmd == "clear":
            self.terminal_history.clear()
        elif base_cmd == "clock":
            app_manager.window_clock.visible = True
            app_manager.focus_window(app_manager.window_clock)
            self.terminal_history.append("CLOCK WINDOW RE-OPENED.")
        elif base_cmd == "monitor":
            app_manager.window_sysmon.visible = True
            app_manager.focus_window(app_manager.window_sysmon)
            self.terminal_history.append("MONITOR WINDOW RE-OPENED.")
        elif base_cmd == "exit":
            app_manager.should_exit = True
        else:
            self.terminal_history.append(f"ERROR: COMMAND NOT FOUND: '{base_cmd}'")
            
        # 截断历史输出，防止溢出视窗
        while len(self.terminal_history) > 13:
            self.terminal_history.pop(0)

    def handle_keyboard(self, clean_keys, app_manager):
        for char in clean_keys:
            if char == '\x7f' or char == '\x08':  # 退格
                if len(self.terminal_input) > 0:
                    self.terminal_input = self.terminal_input[:-1]
            elif char in ('\r', '\n'):  # 回车
                self.execute_command(self.terminal_input, app_manager)
                self.terminal_input = ""
            elif 32 <= ord(char) <= 126:  # 键盘键
                # 限制输入框的最大容纳字数以防溢出标题宽度
                if len(self.terminal_input) < 40:
                    self.terminal_input += char

    def draw_content(self, buffer, is_focused):
        # 终端文字工作区渲染 (起始偏移位 y=34)
        curr_y = self.y + 34
        for line in self.terminal_history:
            line_color = (130, 240, 130) if "os:" in line.lower() or "host:" in line.lower() or "res:" in line.lower() or "re-opened" in line.lower() else (220, 220, 230)
            if line.startswith("kitty>"):
                line_color = (0, 208, 255)
            draw_string(buffer, self.x + 12, curr_y, line, line_color, scale=1, spacing=1)
            curr_y += 13
            
        # 闪烁输入光标
        cursor_visible = (int(time.time() * 2) % 2 == 0) and is_focused
        prompt = f"kitty> {self.terminal_input}"
        draw_string(buffer, self.x + 12, curr_y, prompt, (0, 208, 255), scale=1, spacing=1)
        if cursor_visible:
            cx_pos = self.x + 12 + len(prompt) * 6
            draw_rect(buffer, cx_pos, curr_y, cx_pos + 5, curr_y + 8, (0, 208, 255))

    def draw(self, buffer, is_focused):
        if not self.visible:
            return
        super().draw(buffer, is_focused)
        self.draw_content(buffer, is_focused)


# ==============================================================================
# 🕰️ ANALOG & DIGITAL CLOCK 窗口应用类
# ==============================================================================
class ClockWindow(Window):
    def __init__(self, win_id, title, x, y, w, h):
        super().__init__(win_id, title, x, y, w, h)

    def draw_content(self, buffer, is_focused):
        t_struct = time.localtime()
        time_str = time.strftime("%H:%M:%S", t_struct)
        
        # 1. 绘制高清 LED 数码时钟
        draw_string(buffer, self.x + self.w // 2 - 32, self.y + 34, time_str, (254, 188, 46), scale=1, spacing=1)
        
        # 2. 绘制钟表底面轮廓与高亮指针线 (y-offset ~ self.y + self.h - 55)
        cx = self.x + self.w // 2
        cy = self.y + self.h - 55
        draw_circle_outline(buffer, cx, cy, 42, (95, 100, 125), thickness=2)
        draw_circle(buffer, cx, cy, 2, (255, 255, 255))
        
        # 绘制刻度钟点 (12, 3, 6, 9)
        draw_rect(buffer, cx - 1, cy - 40, cx + 1, cy - 36, (255, 255, 255)) # 12
        draw_rect(buffer, cx - 1, cy + 36, cx + 1, cy + 40, (255, 255, 255)) # 6
        draw_rect(buffer, cx + 36, cy - 1, cx + 40, cy + 1, (255, 255, 255)) # 3
        draw_rect(buffer, cx - 40, cy - 1, cx - 36, cy + 1, (255, 255, 255)) # 9
        
        # 获取时分秒数据
        h, m, s = t_struct.tm_hour, t_struct.tm_min, t_struct.tm_sec
        theta_h = 2.0 * math.pi * (h % 12 + m / 60.0) / 12.0
        theta_m = 2.0 * math.pi * m / 60.0
        theta_s = 2.0 * math.pi * s / 60.0
        
        # 时针 (粗, 钢蓝色)
        hx = int(cx + 18 * math.sin(theta_h))
        hy = int(cy - 18 * math.cos(theta_h))
        draw_thick_line(buffer, cx, cy, hx, hy, (0, 208, 255), thickness=2)
        
        # 分针 (中等, 浅绿色)
        mx = int(cx + 28 * math.sin(theta_m))
        my = int(cy - 28 * math.cos(theta_m))
        draw_thick_line(buffer, cx, cy, mx, my, (76, 175, 80), thickness=2)
        
        # 秒针 (细, 鲜红色)
        sx = int(cx + 34 * math.sin(theta_s))
        sy = int(cy - 34 * math.cos(theta_s))
        draw_line(buffer, cx, cy, sx, sy, (255, 95, 87))

    def draw(self, buffer, is_focused):
        if not self.visible:
            return
        super().draw(buffer, is_focused)
        self.draw_content(buffer, is_focused)


# ==============================================================================
# 📈 SYSTEM PERFORMANCE 监控窗口应用类
# ==============================================================================
class SysmonWindow(Window):
    def __init__(self, win_id, title, x, y, w, h):
        super().__init__(win_id, title, x, y, w, h)
        self.cpu_history = [0.15] * 28

    def update_stats(self):
        prev = self.cpu_history[-1]
        change = random.uniform(-0.12, 0.12)
        new_val = max(0.04, min(0.96, prev + change))
        self.cpu_history.append(new_val)
        if len(self.cpu_history) > 42:
            self.cpu_history.pop(0)

    def draw_content(self, buffer, is_focused):
        draw_string(buffer, self.x + 12, self.y + 34, "CPU LOAD:", (255, 255, 255), scale=1, spacing=1)
        
        # 示波显示视窗网格区域画出
        chart_x = self.x + 12
        chart_y = self.y + 46
        chart_w = self.w - 24
        chart_h = 60
        draw_rect(buffer, chart_x, chart_y, chart_x + chart_w, chart_y + chart_h, (12, 14, 18))
        draw_rect_outline(buffer, chart_x, chart_y, chart_x + chart_w, chart_y + chart_h, (45, 50, 65), thickness=1)
        
        # 绘制示波器中心刻度线
        for offset in (15, 30, 45):
            draw_rect(buffer, chart_x, chart_y + offset, chart_x + chart_w, chart_y + offset, (20, 24, 30))
            
        # 绘制心电波形绿色曲线
        if len(self.cpu_history) >= 2:
            step = chart_w / (len(self.cpu_history) - 1)
            for i in range(len(self.cpu_history) - 1):
                x0 = int(chart_x + i * step)
                y0 = int(chart_y + chart_h - self.cpu_history[i] * chart_h)
                x1 = int(chart_x + (i + 1) * step)
                y1 = int(chart_y + chart_h - self.cpu_history[i+1] * chart_h)
                draw_line(buffer, x0, y0, x1, y1, (0, 255, 128))
                
        # 右上角 CPU 百分比度量文字
        latest_val = int(self.cpu_history[-1] * 100)
        draw_string(buffer, self.x + 85, self.y + 34, f"{latest_val}%", (0, 255, 128), scale=1, spacing=1)
        
        # 绘制 RAM 物理负载条
        ram_y = self.y + 115
        draw_string(buffer, self.x + 12, ram_y, "RAM: 6.4 GB / 16.0 GB (40%)", (255, 255, 255), scale=1, spacing=1)
        draw_rect(buffer, self.x + 12, ram_y + 12, self.x + self.w - 12, ram_y + 24, (30, 32, 42))
        draw_rect_outline(buffer, self.x + 12, ram_y + 12, self.x + self.w - 12, ram_y + 24, (55, 60, 75), thickness=1)
        
        fill_w = int((self.w - 26) * 0.40)
        draw_rect(buffer, self.x + 13, ram_y + 13, self.x + 13 + fill_w, ram_y + 23, (0, 208, 255))

    def draw(self, buffer, is_focused):
        if not self.visible:
            return
        super().draw(buffer, is_focused)
        self.draw_content(buffer, is_focused)
