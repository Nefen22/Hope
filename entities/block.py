import cocos
import pyglet
from .entity import Entity

class Block(Entity):
    def __init__(self, x, y, item_type=None):
        # Khối hộp màu nâu
        try:
            image = pyglet.image.load("assets/block.png")
        except Exception:
            image = pyglet.image.SolidColorImagePattern((139, 69, 19, 255)).create_image(32, 32)
            
        super(Block, self).__init__(image)
        self.position = (x, y)
        self.gravity = 0 # Block lơ lửng không rớt
        self.is_broken = False
        self.item_type = item_type
        
    def break_block(self):
        if self.is_broken:
            return None
        self.is_broken = True
        self._killed = True
        self.kill() # Huỷ khối
        return self.item_type # Trả về loại item đang chứa
