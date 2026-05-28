# Kitty 🐱

一个基于 **Kitty 终端图形协议** 和传统字符终端的 **3D 实时渲染图形学与窗口管理器系统**。

## 🎬 演示视频 (Demo)

<video src="demo.mp4" controls autoplay loop muted width="100%"></video>

---

## 📂 核心功能与文件

- **`interactive_gui.py`**：基于 Kitty 图像与鼠标追踪协议的**图形化桌面与窗口管理器 (KittyWM)**。包含时钟、交互式终端控制台、性能监视器、任务栏及开始菜单，支持窗口鼠标拖拽、聚焦与关闭。
- **`pixel_donut.c` / `pixel_donut.py`**：基于 Kitty 协议的 3D 光影甜甜圈。C 语言版本支持 **电影级黏土** 和 **水晶玻璃** 双材质切换（按空格键），能以 60 FPS 流畅渲染。
- **`pixel_cube.py`**：基于 Kitty 协议的高清 3D 线框立方体，支持 WASD/QE/IJKL 键盘实时调整相机位置与旋转。
- **`cube.py`**：传统字符终端下的 ASCII 3D 线框立方体。

---

## 🚀 快速开始

> ⚠️ **注意**：除字符版 `cube.py` 外，像素级渲染及窗口管理器均需要使用支持 **Kitty 图像协议** 的终端（例如 [Kitty](https://sw.kovidgoyal.net/kitty/), [WezTerm](https://wezfurlong.org/wezterm/), [Ghostty](https://ghostty.org/) 等）来运行，否则会显示 Base64 乱码。

### 1. 启动桌面窗口管理器 (KittyWM)
```bash
python3 interactive_gui.py
```

### 2. 编译并运行高性能 C 版甜甜圈
```bash
# 编译
gcc -O3 pixel_donut.c -o pixel_donut -lm -lz

# 运行
./pixel_donut
```

### 3. 运行其他 Python 图形脚本
```bash
# 像素级 3D 甜甜圈 (Python 版)
python3 pixel_donut.py

# 像素级 3D 立方体 (支持键盘交互)
python3 pixel_cube.py
```
