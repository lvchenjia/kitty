from kitty_wm.engine import draw_rect, draw_rect_outline, draw_circle, draw_circle_outline, draw_string, WIDTH, HEIGHT

# ==============================================================================
# 🗔 KittyWM 现代极简浅色玻璃态 (Light Frosted Glass) 窗口基类
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
        
        # 平滑缓动阻尼算法 (LERP Target Coords)
        self.target_x = x
        self.target_y = y
        
        # 拖拽临时偏置 (格点计算)
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def draw(self, buffer, is_focused):
        if not self.visible:
            return

        # 1. 极简浅色发光外阴影 (Soft Shadow / Pastel Glow)
        # 聚焦时渲染优雅的浅天蓝色外发光边框以凸显层级
        if is_focused:
            draw_rect_outline(buffer, int(self.x) - 1, int(self.y) - 1, int(self.x) + self.w, int(self.y) + self.h, (0, 150, 255, 60), thickness=1)
            draw_rect_outline(buffer, int(self.x) - 2, int(self.y) - 2, int(self.x) + self.w + 1, int(self.y) + self.h + 1, (0, 150, 255, 20), thickness=1)
            border_color = (0, 150, 255)  # 优雅现代天蓝色
        else:
            border_color = (195, 202, 218) # 浅灰蓝色

        # 2. 现代浅色毛玻璃主体 (#fafbfc, 半透明度 220/255)
        body_color = (250, 251, 253, 220)
        draw_rect(buffer, int(self.x), int(self.y), int(self.x) + self.w - 1, int(self.y) + self.h - 1, body_color)

        # 3. 极简浅灰色标题栏 (高度 30 像素)
        header_color = (235, 238, 245, 220) if is_focused else (250, 251, 253, 220)
        draw_rect(buffer, int(self.x), int(self.y), int(self.x) + self.w - 1, int(self.y) + 30, header_color)

        # 4. 仅有一像素的极窄底部分割线与全包边框
        draw_rect(buffer, int(self.x), int(self.y) + 30, int(self.x) + self.w - 1, int(self.y) + 31, border_color)
        draw_rect_outline(buffer, int(self.x), int(self.y), int(self.x) + self.w - 1, int(self.y) + self.h - 1, border_color, thickness=1.5)

        # 5. 纯净 macOS traffic lights 控制球 (红、黄、绿)
        red_color = (255, 95, 87) if is_focused else (200, 120, 115)
        yel_color = (254, 188, 46) if is_focused else (180, 150, 100)
        grn_color = (40, 200, 64) if is_focused else (120, 160, 130)
        
        draw_circle(buffer, int(self.x) + 16, int(self.y) + 15, 4, red_color)
        draw_circle(buffer, int(self.x) + 28, int(self.y) + 15, 4, yel_color)
        draw_circle(buffer, int(self.x) + 40, int(self.y) + 15, 4, grn_color)

        # 6. 居中排版轻量无衬线标题文字 (暗炭灰色 `#212529` / `#7a8090`)
        title_len = len(self.title)
        text_w = title_len * 6
        center_x = int(self.x) + (self.w - text_w) // 2
        
        title_color = (33, 37, 41) if is_focused else (120, 128, 144)
        draw_string(buffer, center_x, int(self.y) + 10, self.title, title_color, scale=1, spacing=1)
