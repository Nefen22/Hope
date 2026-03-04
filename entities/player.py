import cocos
from cocos.sprite import Sprite
from cocos.layer import Layer
from cocos.scene import Scene
from cocos.director import director
import pyglet
from pyglet import gl
from pyglet.window import key
import os
from cocos.draw import Line


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_PATH = os.path.join(BASE_DIR, "assets", "images", "player")
SCREENW = 800
SCREENH = 600

isLoop = {
    "Run": True,
    "Roll": False,
    "Idle": True,

    "Attack": False,
    "Attack2": False,
    "AttackNoMovement": False,
    "Attack2NoMovement": False,
    "AttackCombo": False,
    "AttackComboNoMovement": False,

    "Crouch": True,
    "CrouchAttack": False,
    "CrouchFull": True,
    "CrouchTransition": False,
    "CrouchWalk": True,

    "Dash": False,

    "Death": False,
    "DeathNoMovement": False,

    "Fall": True,

    "Hit": False,

    "Jump": False,
    "JumpFallInbetween": False,

    "Slide": False,
    "SlideFull": False,
    "SlideTransitionStart": False,
    "SlideTransitionEnd": False,

    "TurnAround": False,

    "WallClimb": True,
    "WallClimbNoMovement": True,
    "WallHang": True,
    "WallSlide": True,
}

def auto_crop_image(image):
    image_data = image.get_image_data()
    raw = image_data.get_data('RGBA', image.width * 4)

    width = image.width
    height = image.height

    min_x = width
    max_x = 0
    min_y = height
    max_y = 0

    for y in range(height):
        for x in range(width):
            index = (y * width + x) * 4
            alpha = raw[index + 3]

            if alpha > 10:  # pixel không trong suốt
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    if min_x > max_x or min_y > max_y:
        return image  # ảnh rỗng

    cropped = image.get_region(
        x=min_x,
        y=min_y,
        width=max_x - min_x,
        height=max_y - min_y
    )

    return cropped

def load_animations(folder_path):
    animations = {}

    for filename in os.listdir(folder_path):
        if not filename.endswith(".png"):
            continue

        name = os.path.splitext(filename.replace("_", ""))[0]
        full_path = os.path.join(folder_path, filename)
        image = pyglet.image.load(full_path)


        frame_block = 120
        frame_count = image.width // 120

        frames = [
            auto_crop_image(
                image.get_region(
                    x=i * frame_block,
                    y=0,
                    width=120,
                    height=80,
                )
            )
            for i in range(frame_count)
        ]

        animation = pyglet.image.Animation.from_image_sequence(
            frames, 0.083, isLoop[name]
        )

        animations[name] = animation


    return animations

class PlayerSprite(Layer):
    is_event_handler = True
    def __init__(self):
        super().__init__()
        self.locked = False
        self.locktimer = 0
        self.isGoingtoRight = True
        self.animations = load_animations(ASSET_PATH)
        self.sprite = Sprite(self.animations["Idle"])
        self.sprite.scale = 2
        self.current_state = "Idle"
        self.add(self.sprite)
        self.keys = set()
        self.schedule(self.update)
        self.moving = 0

    def play(self, state):
        if self.current_state != state:
            self.current_state = state
            self.sprite.image = self.animations[state]

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)

    def on_key_release(self, symbol, modifiers):
        if symbol in self.keys:
            self.keys.remove(symbol)

    def update(self, dt):
        if (self.locked):
            self.locktimer += dt
            duration = len(self.animations[self.current_state].frames) * 0.083
            if self.locktimer >= duration:
                self.play("Idle")
                self.locked = False
                self.locktimer = 0
            else:
                self.sprite.x += self.moving
                return
        speed = 220 * dt

        shift_pressed = key.LSHIFT in self.keys or key.RSHIFT in self.keys
        if not self.locked:
            if not self.keys:
                self.play("Idle")
                pass
            if key.RIGHT in self.keys:
                self.sprite.x += speed
                self.sprite.scale_x = 1
                self.play("Run")
                self.moving = speed
            if key.LEFT in self.keys:
                self.sprite.x -= speed
                self.sprite.scale_x = -1
                self.play("Run")
                self.moving = speed
        if shift_pressed:
            self.sprite.x += speed * self.sprite.scale_x * 1.3
            self.play("Roll")
            self.locked = True
            self.moving = speed * self.sprite.scale_x * 1.3
