from kitty_wm.engine import draw_rect, draw_rect_outline, draw_circle, draw_circle_outline, draw_string, WIDTH, HEIGHT

# ==============================================================================
# 🗔 KittyWM 窗口管理对象与底层渲染层
# ==============================================================================
class Window:
    def __init__(self, win_id, title, x, y, w, h, visible=True):
        self.id = win_id
        self.title = title
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = visible
        # 拖拽时相对于窗口左上角偏置
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def draw(self, buffer, is_focused):
        if not self.visible:
            return

        # 1. 精美的超拟真柔和重力半透明阴影 (Glassmorphic Shadow)
        # 向下向右平移 6 像素绘制半透明投影 (用暗系半色调或实体投影模拟)
        draw_rect(buffer, self.x + 6, self.y + 6, self.x + self.w + 5, self.y + self.h + 5, (10, 11, 16, 120))

        # 2. 玻璃态窗口工作区主体 (#1b1c26 - 超前卫毛玻璃高雅黑)
        body_color = (23, 24, 33)
        draw_rect(buffer, self.x, self.y, self.x + self.w - 1, self.y + self.h - 1, body_color)

        # 3. 超高对比度精美标题栏背景 (#2d3142 / #20222b)
        header_color = (40, 44, 58) if is_focused else (26, 28, 36)
        draw_rect(buffer, self.x, self.y, self.x + self.w - 1, self.y + 26, header_color)

        # 4. 电竞级霓虹微光分割线与外边框
        # 激活状态为高级电光青色 (#00d0ff)，非激活状态为冷灰 (#4e5264)
        border_color = (0, 208, 255) if is_focused else (65, 68, 88)
        draw_rect(buffer, self.x, self.y + 26, self.x + self.w - 1, self.y + 27, border_color)
        draw_rect_outline(buffer, self.x, self.y, self.x + self.w - 1, self.y + self.h - 1, border_color, thickness=2)

        # 5. 苹果 macOS 风格的三色交通灯控制球 (左侧对齐)
        # 红色 (关闭): cx=14, cy=13, r=5
        # 黄色 (最小化): cx=26, cy=13, r=5
        # 绿色 (缩放): cx=38, cy=13, r=5
        red_color = (255, 95, 87) if is_focused else (120, 50, 45)
        yel_color = (254, 188, 46) if is_focused else (110, 85, 30)
        grn_color = (40, 200, 64) if is_focused else (35, 95, 45)
        
        draw_circle(buffer, self.x + 16, self.y + 13, 5, red_color)
        draw_circle(buffer, self.x + 28, self.y + 13, 5, yel_color)
        draw_circle(buffer, self.x + 40, self.y + 13, 5, grn_color)

        # 6. 居中绘制优雅窗口标题 text
        # 标题栏有效宽度除去两端空间
        title_len = len(self.title)
        # 每个字宽 5 像素，缩放 1。总宽为 title_len * 5 + (title_len-1)*1
        text_w = title_len * 6
        center_x = self.x + (self.w - text_w) // 2
        title_color = (255, 255, 255) if is_focused else (130, 135, 150)
        draw_string(buffer, center_x, self.y + 8, self.title, title_color, scale=1, spacing=1)
