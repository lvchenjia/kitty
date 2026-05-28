# Kitty Terminal 3D Graphics Engine | 终端 3D 图形引擎

这是一个基于 **Kitty 终端图像协议 (Kitty Graphics Protocol)** 和传统字符终端的 **3D 实时渲染图形学项目**。

## 📂 文件清单及功能说明

项目内的文件及具体功能如下：

*   **`cube.py`**
    *   **类型**：Python 脚本
    *   **作用**：在传统终端中，使用 ASCII 字符（`█` 与空格）通过布雷森汉姆直线算法光栅化并显示一个旋转的 3D 线框立方体。

*   **`pixel_cube.py`**
    *   **类型**：Python 脚本
    *   **作用**：基于 Kitty 终端图像协议的高清 3D 线框立方体渲染程序。支持通过键盘实时调整相机位置（WASD/QE 键进行三维平移）和旋转角度（IJKL/UO 键进行三维旋转）。

*   **`pixel_donut.py`**
    *   **类型**：Python 脚本
    *   **作用**：基于 Kitty 终端图像协议的 3D 光影甜甜圈（Torus）渲染程序。通过纯 Python 自建的 PNG-zlib 压缩引擎，在终端上以约 30 FPS 渲染具有素描明暗灰阶的 3D 甜甜圈。

*   **`pixel_donut.c`**
    *   **类型**：C 语言源文件
    *   **作用**：高性能 C 语言版本的 3D 甜甜圈渲染程序。利用系统级 `zlib` 物理压缩及 Base64 编码，实现流畅稳定的 60 FPS 渲染。内置双光源半兰伯特、Blinn-Phong 镜面高光和菲涅尔边缘光，支持按**空格键**在 **电影级黏土 (Clay)** 和 **水晶玻璃 (Glass)** 双材质之间实时切换。

*   **`.gitignore`**
    *   **类型**：Git 配置文件
    *   **作用**：配置 Git 忽略编译生成的二进制文件 `pixel_donut`、macOS 系统残留 `.DS_Store` 以及 Python 缓存目录 `__pycache__/`。

---

## 🚀 快速运行与编译

### 1. 运行 Python 文件（零依赖）
```bash
# 运行字符版立方体
python3 cube.py

# 运行交互像素级立方体 (需支持 Kitty 协议的终端，如 Kitty, WezTerm)
python3 pixel_cube.py

# 运行像素级甜甜圈 (需支持 Kitty 协议的终端)
python3 pixel_donut.py
```

### 2. 编译并运行高性能 C 版本
```bash
# 编译 (链接数学库与 zlib 库)
gcc -O3 pixel_donut.c -o pixel_donut -lm -lz

# 运行
./pixel_donut
```
*(注：像素版本 `pixel_` 需在 Kitty、WezTerm、Ghostty 等支持 Kitty 图像协议的终端下运行，否则可能会显示 Base64 乱码。)*
