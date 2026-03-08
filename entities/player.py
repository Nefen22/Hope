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
from .entity import Entity


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_PATH = os.path.join(BASE_DIR, "assets", "images", "player")
SCREENW = 800
SCREENH = 600
SPEED = 1
ANIM_SCALE = 0.08
LOCK_ACTION = [key.X, key.C, key.Z]

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
            frames, ANIM_SCALE, isLoop[name]
        )

        animations[name] = animation


    return animations

class PlayerSprite(Entity):
    is_event_handler = True
    def __init__(self, hp, mass):
        super().__init__(hp, mass)
        self.locked = False
        self.hitbox_w = 40
        self.hitbox_h = 60
        self.locktimer = 0
        self.isGoingtoRight = True
        self.animations = load_animations(ASSET_PATH)
        self.sprite = Sprite(self.animations["Idle"])
        self.current_state = "Idle"
        self.add(self.sprite)
        self.keys = set()
        self.dashCD = 0
        self.jumpCheck = False

    def play(self, state):
        if self.current_state != state:
            self.current_state = state
            self.sprite.image = self.animations[state]

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)

    def on_key_release(self, symbol, modifiers):
        if symbol in self.keys:
            self.keys.remove(symbol)
    def lock_action(self, dt):
        print(self.locktimer)
        lock_action = False
        if self.vector[1] == -self.mass * 0.4 and self.current_state != "Dash":
            self.vector[0] = 0
        if self.locktimer > 0:
            self.locktimer = max(0, self.locktimer - dt)
            return True
        if key.X in self.keys:
            self.play("Attack")
            lock_action = True

        if key.C in self.keys:
            self.play("Attack2")
            lock_action = True

        if key.Z in self.keys:
            self.play("Dash")
            self.vector[0] = SPEED*3 if self.isGoingtoRight else -SPEED*3
            lock_action = True

        if lock_action:
            self.locktimer = len(self.animations[self.current_state].frames) * ANIM_SCALE
            list(map(lambda x: self.on_key_release(x, None), LOCK_ACTION))
            return True
        return False

    def update(self, dt):
        vx = self.vector[0]
        self.massEfected()
        vy = self.vector[1]
        if self.lock_action(dt):
            return
        self.locktimer = 0
        if key.RIGHT in self.keys:
            vx = SPEED
            if self.current_state not in ["Jump", "JumpFallInbetween"]:
                self.play("Run")
            else:
                self.play("JumpFallInbetween")
            self.isGoingtoRight = True
            self.sprite.scale_x = 1
        elif key.LEFT in self.keys:
            vx = -SPEED
            if self.current_state not in ["Jump", "JumpFallInbetween"]:
                self.play("Run")
            else:
                self.play("JumpFallInbetween")
            self.isGoingtoRight = False
            self.sprite.scale_x = -1
        if key.SPACE in self.keys:
            if self.vector[1] == -self.mass * 0.4:
                vy = SPEED*3
                self.jumpCheck = True
                self.play("Jump")

        if vy < -self.mass * 0.4:
            self.play("Fall")
            self.vector = [vx, vy]
            return
        if not self.keys:
            vx = 0
            self.jumpCheck = False
            self.play("Idle")
        self.vector = [vx, vy]

