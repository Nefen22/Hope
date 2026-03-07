from cocos.sprite import Sprite
from cocos.layer import Layer

class Entity(Layer):
    def __init__(self, hp, mass):
        super().__init__()
        self.vector = [0,0]
        self.hp = hp
        self.mass = mass
    def massEfected(self):
        self.vector[1] -= 0.4 * self.mass

    def move(self):
        self.x += self.vector[0]
        self.y += self.vector[1]
    def update(self):
        pass
    def draw(self):
        pass