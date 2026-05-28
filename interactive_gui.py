#!/usr/bin/env python3
import sys
import os

# 将当前目录前置插入模块寻址路径，保障跨路径调用无虞
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kitty_wm.main import start_desktop

if __name__ == "__main__":
    start_desktop()
