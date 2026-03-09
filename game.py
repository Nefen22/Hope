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
        tile = self.map.layers[-1][0].get_at_pixel(x, y)
        if tile and tile.get("solid"):
            return True

        return False

    def collide(self, x, y):

        w = self.player.hitbox_w / 2
        h = self.player.hitbox_h / 2

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