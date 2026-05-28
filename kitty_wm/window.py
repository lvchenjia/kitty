from kitty_wm.engine import draw_rect, draw_rect_outline, draw_circle, draw_circle_outline, draw_string, WIDTH, HEIGHT

# ==============================================================================
# 🗔 KittyWM 现代极简 Glassmorphic 窗口基类
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
        # 拖拽临时偏置 (格点计算)
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def draw(self, buffer, is_focused):
        if not self.visible:
            return

        # 1. 现代双层外发光霓虹边框 (Layered Neon Glow Effect)
        # 聚焦状态下，向外渲染 2 像素层层淡出的电光青色微光 (#00f0ff)
        # 非聚焦状态下，仅渲染极简暗灰边框
        if is_focused:
            # 第一层微弱外发光 (x向外扩1px, 浓度 70/255)
            draw_rect_outline(buffer, self.x - 1, self.y - 1, self.x + self.w, self.y + self.h, (0, 240, 255, 70), thickness=1)
            # 第二层微弱外发光 (x向外扩2px, 浓度 25/255)
            draw_rect_outline(buffer, self.x - 2, self.y - 2, self.x + self.w + 1, self.y + self.h + 1, (0, 240, 255, 25), thickness=1)
            
            border_color = (0, 240, 255)  # 电光青色
        else:
            border_color = (60, 65, 85)   # 极简暗灰

        # 2. 现代极简毛玻璃主体 (#0c0e16, 半透明度 210/255)
        body_color = (12, 14, 22, 210)
        draw_rect(buffer, self.x, self.y, self.x + self.w - 1, self.y + self.h - 1, body_color)

        # 3. 极简现代扁平标题栏 (高度 30 像素)
        # 聚焦状态下带有极轻微的背景高亮
        header_color = (20, 24, 36, 210) if is_focused else (12, 14, 22, 210)
        draw_rect(buffer, self.x, self.y, self.x + self.w - 1, self.y + 30, header_color)

        # 4. 仅有一像素的极窄底部分割线
        draw_rect(buffer, self.x, self.y + 30, self.x + self.w - 1, self.y + 31, border_color)
        # 窗口整体包边描边
        draw_rect_outline(buffer, self.x, self.y, self.x + self.w - 1, self.y + self.h - 1, border_color, thickness=1.5)

        # 5. 精致间距的苹果 macOS 圆形按钮 (无多余粗糙边框，纯净填色)
        # 红 (关闭) cx=16, 黄 (最小化) cx=28, 绿 (放大) cx=40. cy=15, 半径=4 (直径8)
        red_color = (255, 95, 87) if is_focused else (120, 50, 45)
        yel_color = (254, 188, 46) if is_focused else (110, 85, 30)
        grn_color = (40, 200, 64) if is_focused else (35, 95, 45)
        
        draw_circle(buffer, self.x + 16, self.y + 15, 4, red_color)
        draw_circle(buffer, self.x + 28, self.y + 15, 4, yel_color)
        draw_circle(buffer, self.x + 40, self.y + 15, 4, grn_color)

        # 6. 居中排版轻量无衬线标题文字
        title_len = len(self.title)
        text_w = title_len * 6
        center_x = self.x + (self.w - text_w) // 2
        
        title_color = (255, 255, 255) if is_focused else (120, 125, 140)
        draw_string(buffer, center_x, self.y + 10, self.title, title_color, scale=1, spacing=1)
