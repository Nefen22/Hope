import cocos
import pyglet
import os
import math
from .entity import Entity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_colored_image(color, w, h):
    return pyglet.image.SolidColorImagePattern(color).create_image(w, h)


class Item(Entity):
    """Các loại item có thể nhặt:
      - Coin     : +1 điểm
      - Star     : +1 điểm + buff tốc độ 5s
      - Invincible: bất tử 5s
    """

    # Thông tin mỗi loại item: (màu fallback, w, h)
    _TYPE_INFO = {
        "Coin":       ((255, 215,   0, 255), 14, 14),
        "Star":       ((255, 255,  50, 255), 18, 18),
        "Invincible": ((  0, 255, 255, 255), 16, 16),
    }

    def __init__(self, x, y, item_type="Coin"):
        self.item_type = item_type

        color, w, h = self._TYPE_INFO.get(item_type, ((255, 255, 255, 255), 16, 16))

        # Thử load ảnh, fallback sang màu trơn
        img_path = os.path.join(BASE_DIR, "assets", f"{item_type.lower()}.png")
        try:
            image = pyglet.image.load(img_path)
            image.anchor_x = image.width  // 2
            image.anchor_y = image.height // 2
        except Exception:
            image = _make_colored_image(color, w, h)
            image.anchor_x = w // 2
            image.anchor_y = h // 2

        super(Item, self).__init__(image)
        self.position    = (x, y)
        self.gravity     = 0          # Item lơ lửng
        self.is_collected = False

        # Hiệu ứng bob lên xuống
        self._bob_time   = 0.0
        self._bob_amp    = 5.0        # biên độ (pixel)
        self._bob_speed  = 2.5        # rad/s
        self._base_y     = y

    # ------------------------------------------------------------------
    def update(self, dt, walls_layer=None):
        """Bob animation – được gọi từ game._update nếu cần."""
        self._bob_time += dt
        self.y = self._base_y + self._bob_amp * math.sin(self._bob_time * self._bob_speed)

    def check_pickup(self, player):
        if self.is_collected:
            return False
        dist_x = abs(self.x - player.x)
        dist_y = abs(self.y - player.y)
        if dist_x < 32 and dist_y < 48:
            self.is_collected = True
            self._killed      = True
            self.kill()
            return True
        return False
