from cocos.director import director
from cocos.layer import Layer
from cocos.scene import Scene
from cocos.tiles import load, RectMapLayer
from cocos.layer import ColorLayer
from cocos.sprite import Sprite
from maps.map import Map
import os
from entities import *
import pyglet

WINDOW_SIZE = (800, 600)
import cocos
import pyglet
import pprint

class GameLayer(Layer):
    def __init__(self):
        super().__init__()
        self.map = Map("assets/images/map/map.tmx")
        self.map.draw(self)
        self.player = PlayerSprite(100, 2)
        self.player.position = (WINDOW_SIZE[0]/2, WINDOW_SIZE[1]/2 + 80)
        self.add(self.player, z = len(self.map.layers))
        self.schedule(self.update)

    def is_blocked(self, x, y):
        # 1. Lấy thông tin Tile tại vị trí pixel đó
        tile = self.map.layers[-1][0].get_at_pixel(x, y)

        if tile:
            # 2. Tìm các vật thể va chạm (objects) được vẽ trong Tiled cho Tile này
            # Trong Cocos2d-python, nó thường nằm trong tile.objects
            collision_shapes = tile.get('objects', [])

            if collision_shapes:
                # Tọa độ gốc của ô Tile (góc dưới bên trái)
                tile_x = (x // 32) * 32
                tile_y = (y // 32) * 32

                # 3. Kiểm tra xem điểm (x, y) có nằm trong bất kỳ hình vẽ nào không
                for shape in collision_shapes:
                    # Tiled lưu tọa độ Y từ trên xuống, nhưng Cocos từ dưới lên
                    # Cần lưu ý tùy vào phiên bản bộ nạp map, thường shape là một Rect

                    # Giả sử shape là một đối tượng có x, y, width, height:
                    # Lưu ý: Tọa độ của shape là tọa độ tương đối bên trong ô 32x32
                    hit_x_min = tile_x + shape.x
                    hit_x_max = hit_x_min + shape.width
                    hit_y_min = tile_y + (32 - shape.y - shape.height)  # Đảo ngược trục Y nếu cần
                    hit_y_max = hit_y_min + shape.height

                    if hit_x_min <= x <= hit_x_max and hit_y_min <= y <= hit_y_max:
                        return True

        return False

    def collide(self, x, y):

        w = 40 // 2
        h = 80 // 2

        points = [
            (x - w, y - h),
            (x + w, y - h),
            (x - w, y + h),
            (x + w, y + h)
        ]

        for px, py in points:
            if self.is_blocked(px, py):
                return True

        return False

    def playerMove(self):
        vx, vy = self.player.vector
        # Giá trị dùng để tính pixel cần để char xuống đất
        subVx, subVy = 0, 0
        if self.collide(self.player.x, self.player.y + vy):
            while not self.collide(self.player.x, self.player.y + subVy):
                subVy += (1 if vy > 0 else -1)
            else:
                subVy -= (1 if vy > 0 else -1)
                vy = 0
        print(vx, vy)
        if self.collide(self.player.x + vx, self.player.y):
            while not self.collide(self.player.x + subVx, self.player.y):
                subVx += (1 if vx > 0 else -1)
            else:
                subVx -= (1 if vx > 0 else -1)
                vx = 0
        print(vx, vy, subVx)
        self.player.vector = [vx + subVx, vy + subVy]
        self.player.move()

    def update(self, dt):
        self.player.update(dt)
        self.playerMove()


def main():
    director.init(WINDOW_SIZE[0], WINDOW_SIZE[1])
    scene = Scene(GameLayer())
    director.run(scene)

if __name__ == "__main__":
    main()