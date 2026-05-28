#!/usr/bin/env python3
import sys
import os
import time
import select
import tty
import termios

from kitty_wm.engine import sgr_pattern, ansi_escape, encode_png, send_image_via_kitty, WIDTH, HEIGHT, BUFFER_SIZE
from kitty_wm.apps import TerminalWindow, ClockWindow
from kitty_wm.desktop import DesktopManager

# ==============================================================================
# 🚀 KDE/KittyWM 桌面系统主引擎启动口
# ==============================================================================
def start_desktop():
    # 清空并初始化日志文件
    log_path = "/Users/horse/Desktop/kitty/kitty_wm.log"
    try:
        with open(log_path, "w") as f:
            f.write(f"=== KITTYWM SYSTEM LOG START (LOCAL TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}) ===\n")
    except:
        pass

    def log_message(msg):
        try:
            with open(log_path, "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        except:
            pass

    log_message("System initialized. 16:9 canvas (960x540) active.")

    # 1. 全屏清屏，隐藏光标，开启 SGR 鼠标捕获
    sys.stdout.write("\033[?25l\033[2J\033[H")
    sys.stdout.write("\033[?1002h\033[?1006h")  # 只捕获 1002 (拖拽) 与 1006 (SGR 编码)
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    # 2. 初始化核心应用程序窗口 (自适应 960x540 宽屏物理像素)
    # 终端控制台: x=40, y=70, w=480, h=250
    window_terminal = TerminalWindow("terminal", "TERMINAL CONSOLE", 40, 70, 480, 250)
    
    # 指针数码时钟: x=560, y=70, w=340, h=210
    window_clock = ClockWindow("clock", "ANALOG DIGITAL CLOCK", 560, 70, 340, 210)

    # 桌面管理器实例化
    desktop = DesktopManager(window_terminal, window_clock)
    # 将日志句柄挂载到 desktop，方便它记录鼠标轨迹
    desktop.log_message = log_message
    
    frame_buffer = bytearray(BUFFER_SIZE)

    try:
        # 执行初次重绘
        desktop.render_all(frame_buffer)
        
        while not desktop.should_exit:
            # 移除了 performance 监视器心跳数据更新
            pass
            
            # 3. 动态获取物理终端尺寸，执行 16:9 高清宽屏缩放算法
            try:
                columns, rows = os.get_terminal_size()
            except OSError:
                columns, rows = 120, 40

            # 黄金比例缩放约束：每行物理高度约为宽度的 2 倍
            # 列数 : 行数 = 3.5 : 1 => 呈现物理完美的 16:9 比例画面
            target_rows = min(rows - 6, 26)
            if target_rows < 12:
                target_rows = 12
            target_cols = int(target_rows * 3.5)
            
            if target_cols > columns - 4:
                target_cols = columns - 4
                target_rows = int(target_cols / 3.5)
                
            start_row = 3
            start_col = max(1, (columns - target_cols) // 2)

            # 4. 极致稳定的 UNIX 非阻塞 os.read 读取方式 (防转义码切碎)
            rlist, _, _ = select.select([sys.stdin], [], [], 0.02)
            
            raw_input_data = ""
            if rlist:
                try:
                    # 一次性读出内核缓冲区中所有已达字节，不进行任何延时等待，完美保证转义帧的原子完整性
                    raw_input_data = os.read(fd, 4096).decode('utf-8', errors='ignore')
                    log_message(f"Raw Stdin Bytes: {repr(raw_input_data)}")
                except Exception as ex:
                    log_message(f"os.read Error: {str(ex)}")

            # 5. 键盘物理退出监听 ('q', 'Q' 或 Ctrl+C)
            if raw_input_data:
                if 'q' in raw_input_data or 'Q' in raw_input_data or '\x03' in raw_input_data:
                    break

            # 6. 获取并过滤纯文本键盘字符，流式分发至顶层聚焦的终端窗口
            clean_keys = ansi_escape.sub('', raw_input_data)
            focused_win = None
            for win in reversed(desktop.windows):
                if win.visible:
                    focused_win = win
                    break
                    
            if focused_win == window_terminal and window_terminal.visible and clean_keys:
                window_terminal.handle_keyboard(clean_keys, desktop)

            # 7. 解析 SGR 鼠标动作指令
            matches = sgr_pattern.findall(raw_input_data)
            if matches:
                desktop.handle_mouse(matches, start_col, start_row, target_cols, target_rows)

            # 8. 图层合并渲染
            desktop.render_all(frame_buffer)

            # 9. PNG 帧无损极速压缩并传输至显示层
            png_output = encode_png(frame_buffer, WIDTH, HEIGHT)
            sys.stdout.write(f"\033[{start_row};{start_col}H")
            send_image_via_kitty(png_output, target_cols, target_rows, image_id=10)
            sys.stdout.write("\033[H")

    finally:
        # 10. 恢复终端系统出厂设置与状态清除
        sys.stdout.write("\033[?1002l\033[?1006l")  # 停用鼠标追踪
        sys.stdout.write("\033[?25h\033[2J\033[H")  # 恢复文本光标并清屏
        sys.stdout.write("\033_Ga=d,i=10\033\\")    # 清理 Kitty 渲染显存
        sys.stdout.flush()
        
        termios.tcsetattr(fd, termios.TCSANOW, old_settings)
        print("💡 KittyWM 已安全退出。感谢您的体验！")

if __name__ == "__main__":
    start_desktop()
