import cocos
import pyglet
import os
from .entity import Entity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Block(Entity):
    """Thùng/hộp có thể phá để lấy item bên trong.

    Cách phá:
      - Kiếm tấn công (attack_rect chạm vào)
      - Nhảy đập đầu từ phía dưới (velocity_y > 0 + chạm đáy block)
      - Dash qua (xử lý trong game.py)
    """

    def __init__(self, x, y, item_type=None):
        img_path = os.path.join(BASE_DIR, "assets", "block.png")
        try:
            image = pyglet.image.load(img_path)
            image.anchor_x = image.width  // 2
            image.anchor_y = image.height // 2
        except Exception:
            image = pyglet.image.SolidColorImagePattern((139, 69, 19, 255)).create_image(32, 32)
            image.anchor_x = 16
            image.anchor_y = 16

        super(Block, self).__init__(image)
        self.position  = (x, y)
        self.gravity   = 0          # Block không rớt
        self.is_broken = False
        self.item_type = item_type

        # Hitbox dùng cho va chạm
        self.hitbox_w  = 28
        self.hitbox_h  = 28

    def break_block(self):
        """Phá block, trả về item_type bên trong (hoặc None)."""
        if self.is_broken:
            return None
        self.is_broken = True
        self._killed   = True
        self.kill()
        return self.item_type
