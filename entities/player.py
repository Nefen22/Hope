import cocos
from cocos.sprite import Sprite
from pyglet.window import key
import os
import pyglet
from .entity import Entity

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_PATH = os.path.join(BASE_DIR, "assets", "images", "player")
ANIM_SCALE = 0.08
LOCK_ACTION = [key.X, key.C, key.Z]

isLoop = {
    "Run": True, "Roll": False, "Idle": True,
    "Attack": False, "Attack2": False, "AttackNoMovement": False,
    "Attack2NoMovement": False, "AttackCombo": False, "AttackComboNoMovement": False,
    "Crouch": True, "CrouchAttack": False, "CrouchFull": True, "CrouchTransition": False, "CrouchWalk": True,
    "Dash": False, "Death": False, "DeathNoMovement": False, "Fall": True,
    "Hit": False, "Jump": False, "JumpFallInbetween": False,
    "Slide": False, "SlideFull": False, "SlideTransitionStart": False, "SlideTransitionEnd": False,
    "TurnAround": False, "WallClimb": True, "WallClimbNoMovement": True, "WallHang": True, "WallSlide": True,
}


def auto_crop_image(image):
    image_data = image.get_image_data()
    raw = image_data.get_data('RGBA', image.width * 4)
    width, height = image.width, image.height
    min_x, max_x = width, 0
    min_y, max_y = height, 0
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            if raw[idx + 3] > 10:
                min_x = min(min_x, x); max_x = max(max_x, x)
                min_y = min(min_y, y); max_y = max(max_y, y)
    if min_x > max_x or min_y > max_y:
        return image
    return image.get_region(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)


def load_animations(folder_path):
    animations = {}
    for filename in os.listdir(folder_path):
        if not filename.endswith(".png"): continue
        name      = os.path.splitext(filename.replace("_", ""))[0]
        full_path = os.path.join(folder_path, filename)
        image     = pyglet.image.load(full_path)
        frame_block = 120
        frame_count = image.width // 120
        frames = [
            auto_crop_image(image.get_region(x=i * frame_block, y=0, width=120, height=80))
            for i in range(frame_count)
        ]
        animation = pyglet.image.Animation.from_image_sequence(frames, ANIM_SCALE, isLoop.get(name, True))
        animations[name] = animation
    return animations


class PlayerSprite(Entity):
    is_event_handler = True

    def __init__(self, hp=100, mass=0):
        self.animations = load_animations(ASSET_PATH)
        super(PlayerSprite, self).__init__(self.animations["Idle"])

        self.hp    = hp
        self.mass  = mass
        self.scale = 1.5

        self.hitbox_w = 40
        self.hitbox_h = 60
        self.locktimer      = 0
        self.isGoingtoRight = True
        self.current_state  = "Idle"
        self.keys           = set()

        self.is_invincible    = False
        self.invincible_timer = 0
        self.is_attacking     = False
        self.attack_rect      = None
        self.hit_enemies      = set()

        self._was_on_ground   = True  # Phát hiện lần nhảy

    def play(self, state):
        if self.current_state != state:
            self.current_state = state
            self.image = self.animations[state]

    # ── Input ─────────────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)
        if symbol == key.SPACE and self.on_ground:
            self.velocity_y  = self.jump_speed
            self.is_jumping  = True
            self.on_ground   = False
            # SFX nhảy
            try:
                from sound import SoundManager
                SoundManager.play_sfx('jump')
            except Exception:
                pass

    def on_key_release(self, symbol, modifiers):
        if symbol in self.keys:
            self.keys.remove(symbol)
        if symbol == key.LEFT  and self.velocity_x < 0: self.velocity_x = 0
        if symbol == key.RIGHT and self.velocity_x > 0: self.velocity_x = 0

    # ── Lock action (attack / dash) ───────────────────────────────────────────
    def lock_action(self, dt):
        if self.locktimer > 0:
            self.locktimer = max(0, self.locktimer - dt)
            return True
        lock_action = False

        if key.X in self.keys:
            self.play("Attack");  lock_action = True; self.is_attacking = True
            self._play_sfx_once('attack')
        elif key.C in self.keys:
            self.play("Attack2"); lock_action = True; self.is_attacking = True
            self._play_sfx_once('attack')
        elif key.Z in self.keys:
            self.play("Dash")
            self.velocity_x      = self.move_speed * 3 if self.isGoingtoRight else -self.move_speed * 3
            lock_action          = True
            self.is_invincible   = True
            self.invincible_timer = 0.2

        if lock_action:
            self.locktimer = len(self.animations[self.current_state].frames) * ANIM_SCALE
            self.hit_enemies.clear()
            list(map(lambda x: self.on_key_release(x, None), LOCK_ACTION))
            import cocos.rect
            at_w, at_h = 40, 60
            offset_x  = 40 if self.isGoingtoRight else -40
            self.attack_rect = cocos.rect.Rect(self.x + offset_x - at_w / 2,
                                               self.y - at_h / 2, at_w, at_h)
            return True
        return False

    def _play_sfx_once(self, name):
        try:
            from sound import SoundManager
            SoundManager.play_sfx(name)
        except Exception:
            pass

    def take_damage(self, amount):
        if self.is_invincible: return False
        self.hp              -= amount
        self.is_invincible    = True
        self.invincible_timer = 2.0
        return True

    # ── Main update ───────────────────────────────────────────────────────────
    def update(self, dt, walls_layer):
        # Bất tử nhấp nháy
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
            self.opacity = 50 if (int(self.invincible_timer * 15) % 2 == 0) else 255
            if self.invincible_timer <= 0:
                self.is_invincible = False
                self.opacity       = 255

        if self.lock_action(dt):
            self.update_physics(dt, walls_layer)
            return

        self.locktimer   = 0
        self.is_attacking = False
        self.attack_rect  = None

        # Di chuyển
        if key.RIGHT in self.keys:
            self.velocity_x      = self.move_speed
            self.isGoingtoRight  = True
            self.scale_x         = 1.5
        elif key.LEFT in self.keys:
            self.velocity_x      = -self.move_speed
            self.isGoingtoRight  = False
            self.scale_x         = -1.5

        # Animation state machine
        if not self.on_ground:
            self.play("Jump") if self.velocity_y > 0 else self.play("Fall")
        else:
            self.play("Run") if self.velocity_x != 0 else self.play("Idle")

        self.update_physics(dt, walls_layer)
