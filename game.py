from cocos.director import director
from cocos.layer import Layer
from cocos.scene import Scene
from entities import *

WINDOW_SIZE = (800, 600)

class GameLayer(Layer):
    def __init__(self):
        super().__init__()

        player = PlayerSprite()
        player.position = (WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2)
        self.add(player)


def main():
    director.init(WINDOW_SIZE[0], WINDOW_SIZE[1])
    scene = Scene(GameLayer())
    director.run(scene)

if __name__ == "__main__":
    main()