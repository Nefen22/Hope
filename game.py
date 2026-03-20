import cocos
from cocos.director import director
from cocos.layer import Layer
from cocos.scene import Scene
from cocos.sprite import Sprite
from maps.map import Map
from pyglet import gl
import pyglet
from entities import *

WINDOW_SIZE = (800, 600)


# Layer chuyên biệt để vẽ Hitbox Debug (luôn nằm trên cùng)
class DebugLayer(Layer):
    def __init__(self, collision_objects):
        super().__init__()
        self.collision_objects = collision_objects

    def draw(self):
        gl.glPushMatrix()
        gl.glLineWidth(2)
        gl.glColor4f(1, 0, 0, 1)  # Màu đỏ rực
        for obj in self.collision_objects:
            x1, y1 = obj.x, obj.y
            x2, y2 = obj.x + obj.width, obj.y + obj.height
            pyglet.graphics.draw(4, gl.GL_LINE_LOOP,
                                 ('v2f', (x1, y1, x2, y1, x2, y2, x1, y2)))
        gl.glPopMatrix()


class GameLayer(Layer):
    def __init__(self):
        super().__init__()
        # 1. Khởi tạo Map
        self.map = Map("assets/images/map/map.tmx")
        self.map.draw(self)

        # 2. Khởi tạo Player
        self.player = PlayerSprite(100, 2)
        self.player.position = (400, 300)
        # z=10 để nằm trên map, nhưng dưới debug_layer
        self.add(self.player, z=10)

        # 3. Khởi tạo Debug Layer (z cực cao để không bị đè)
        self.debug_layer = DebugLayer(self.map.collision_objects)
        self.add(self.debug_layer, z=999)

        self.schedule(self.update)

    def is_blocked(self, x, y):
        for obj in self.map.collision_objects:
            if (obj.x <= x <= obj.x + obj.width and
                    obj.y <= y <= obj.y + obj.height):
                return True
        return False

    def collide(self, x, y):
        # Hitbox nhân vật: chỉnh nhỏ hơn sprite một chút để mượt hơn
        w, h = 10, 40  # Half-width và Half-height
        points = [
            (x - w, y - h), (x + w, y - h),
            (x - w, y + h), (x + w, y + h),
            (x, y - h)  # Thêm điểm giữa chân
        ]
        for px, py in points:
            if self.is_blocked(px, py):
                return True
        return False

    def playerMove(self):
        vx, vy = self.player.vector
        new_x, new_y = self.player.x, self.player.y

        # TRỤC Y: Kiểm tra va chạm sàn/trần
        if self.collide(new_x, new_y + vy):
            step_y = 1 if vy > 0 else -1
            # Tìm vị trí sát nhất
            while not self.collide(new_x, new_y + step_y):
                new_y += step_y

            # Tính lại vy thực tế để mút sát sàn
            vy = new_y - self.player.y

        # Cập nhật tọa độ Y tạm thời để check X chính xác hơn
        temp_y = self.player.y + vy

        # TRỤC X: Kiểm tra va chạm tường
        if self.collide(new_x + vx, temp_y):
            step_x = 1 if vx > 0 else -1
            while not self.collide(new_x + step_x, temp_y):
                new_x += step_x

            vx = new_x - self.player.x

        # Gán lại vector đã xử lý va chạm
        self.player.vector = [vx, vy]
        # Cuối cùng mới di chuyển
        self.player.move()

    def update(self, dt):
        self.player.update(dt)
        self.playerMove()


def main():
    director.init(WINDOW_SIZE[0], WINDOW_SIZE[1])
    # Tắt khử răng cưa nếu muốn gạch sắc nét
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    scene = Scene(GameLayer())
    director.run(scene)


if __name__ == "__main__":
    main()