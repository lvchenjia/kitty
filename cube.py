#!/usr/bin/env python3
import math
import time
import os
import sys

def main():
    # 3D 立方体的 8 个顶点坐标
    vertices = [
        [-1.0, -1.0, -1.0],
        [ 1.0, -1.0, -1.0],
        [ 1.0,  1.0, -1.0],
        [-1.0,  1.0, -1.0],
        [-1.0, -1.0,  1.0],
        [ 1.0, -1.0,  1.0],
        [ 1.0,  1.0,  1.0],
        [-1.0,  1.0,  1.0]
    ]

    # 连接 8 个顶点的 12 条棱 (边)
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0), # 后表面
        (4, 5), (5, 6), (6, 7), (7, 4), # 前表面
        (0, 4), (1, 5), (2, 6), (3, 7)  # 连接前后的棱
    ]

    # 旋转角度初始化
    angle_x = 0.0
    angle_y = 0.0
    angle_z = 0.0

    # 终端文字的宽高比校正系数 (通常终端字符高度是宽度的 2 倍左右)
    ASPECT_CORRECTION = 2.0

    # 隐藏光标的 ANSI 转义码
    print("\033[?25l", end="")

    try:
        while True:
            # 动态获取当前终端视口大小，自适应缩放
            try:
                columns, rows = os.get_terminal_size()
            except OSError:
                columns, rows = 80, 40

            width = columns
            height = rows - 2  # 预留底行空间

            # 创建空白帧缓冲区 (以空格填充)
            buffer = [[" " for _ in range(width)] for _ in range(height)]

            # 计算旋转矩阵的三角函数值
            cos_x, sin_x = math.cos(angle_x), math.sin(angle_x)
            cos_y, sin_y = math.cos(angle_y), math.sin(angle_y)
            cos_z, sin_z = math.cos(angle_z), math.sin(angle_z)

            # 旋转并投影所有的 3D 顶点到 2D 屏幕
            projected_vertices = []
            for vertex in vertices:
                x, y, z = vertex[0], vertex[1], vertex[2]

                # 1. 绕 X 轴旋转
                y1 = y * cos_x - z * sin_x
                z1 = y * sin_x + z * cos_x

                # 2. 绕 Y 轴旋转
                x2 = x * cos_y + z1 * sin_y
                z2 = -x * sin_y + z1 * cos_y

                # 3. 绕 Z 轴旋转
                x3 = x2 * cos_z - y1 * sin_z
                y3 = x2 * sin_z + y1 * cos_z

                # 4. 透视投影计算 (增加 Z 轴距离防止除以零)
                distance = 3.0
                z_depth = z2 + distance
                
                # 投影公式，缩放系数自适应屏幕尺寸
                scale = min(width, height) * 0.4
                proj_x = int(width / 2 + (x3 * scale * ASPECT_CORRECTION) / z_depth)
                proj_y = int(height / 2 + (y3 * scale) / z_depth)

                projected_vertices.append((proj_x, proj_y))

            # 使用布雷森汉姆直线算法 (Bresenham's Line Algorithm) 绘制 12 条棱
            for edge in edges:
                p1 = projected_vertices[edge[0]]
                p2 = projected_vertices[edge[1]]
                
                x0, y0 = p1[0], p1[1]
                x1, y1 = p2[0], p2[1]

                dx = abs(x1 - x0)
                dy = abs(y1 - y0)
                sx = 1 if x0 < x1 else -1
                sy = 1 if y0 < y1 else -1
                err = dx - dy

                while True:
                    if 0 <= x0 < width and 0 <= y0 < height:
                        buffer[y0][x0] = "█" # 使用高亮度方块字符作为线框像素

                    if x0 == x1 and y0 == y1:
                        break

                    e2 = 2 * err
                    if e2 > -dy:
                        err -= dy
                        x0 += sx
                    if e2 < dx:
                        err += dx
                        y0 += sy

            # 渲染帧缓冲区到终端屏幕
            output = []
            for row in buffer:
                output.append("".join(row))
            
            # 使用 ANSI 转义码将光标移动到左上角 (0, 0)，进行无闪烁平滑重绘
            sys.stdout.write("\033[H" + "\n".join(output))
            sys.stdout.flush()

            # 递增旋转角度
            angle_x += 0.03
            angle_y += 0.04
            angle_z += 0.01

            # 控制帧率在 30 FPS 左右
            time.sleep(0.033)

    except KeyboardInterrupt:
        # 退出时恢复终端光标显示，并清屏
        print("\033[?25h\033[2J\033[H")
        print("💡 3D 渲染演示结束，已安全退出。")

if __name__ == "__main__":
    main()
