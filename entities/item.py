import cocos
import pyglet
from .entity import Entity

class Item(Entity):
    def __init__(self, x, y, item_type="Coin"):
        self.item_type = item_type
        
        # Chọn màu/ảnh tuỳ theo Item Type
        if item_type == "Coin":
            color = (255, 215, 0, 255) # Vàng
        elif item_type == "Invincible":
            color = (0, 255, 255, 255) # Cyan ngọc
        else:
            color = (255, 255, 255, 255)
            
        try:
            image = pyglet.image.load(f"assets/{item_type.lower()}.png")
        except Exception:
            image = pyglet.image.SolidColorImagePattern(color).create_image(16, 16)
            
        super(Item, self).__init__(image)
        self.position = (x, y)
        self.gravity = 0  # Item có thể trôi nổi không rớt
        self.is_collected = False
        
    def check_pickup(self, player):
        if self.is_collected:
            return False
            
        # Kiểm tra khoảng cách hoặc rect overlaps đơn giản
        dist_x = abs(self.x - player.x)
        dist_y = abs(self.y - player.y)
        
        if dist_x < 30 and dist_y < 40:
            self.is_collected = True
            self._killed = True
            self.kill() # Xoá khỏi Scene Graph
            return True
            
        return False
