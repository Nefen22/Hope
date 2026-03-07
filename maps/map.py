import csv
import pyglet
from cocos.sprite import Sprite
from cocos.batch import BatchNode
from cocos.tiles import load, RectMapLayer
from cocos.layer import Layer

class Map():
    def __init__(self, path):
        self.layers = []
        map_ = load(path)
        map_ = map_.find(RectMapLayer)
        for index, layer in enumerate(map_):
            print(layer)
            ele = layer[1]
            ele.set_view(0, 0, ele.px_width, ele.px_height)
            ele.position = (0, 0)
            self.layers.append((ele, index))

    def draw(self, layer):
        for (ele, index) in self.layers:
            layer.add(ele, z=index)

    def get_tile_at_pixel(self, x, y):

        return [ele.get_at_pixel(x, y) for ele, index in self.layers if ele.get_at_pixel(x, y)]
