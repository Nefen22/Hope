import cocos
import pyglet
import os
from .entity import Entity
from .enemy import load_frames

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── Goblin Boss ─────────────────────────────────────────────────────────────

class BossGoblin(Entity):
    NAME = "GOBLIN KING"

    def __init__(self, x, y):
        root = os.path.join(BASE_DIR, "assets", "images", "boss goblin")

        self.animations = {
            "idle":   load_frames(os.path.join(root, "idle"),    duration=0.075, loop=True),
            "walk":   load_frames(os.path.join(root, "walk1"),   duration=0.07,  loop=True),
            "attack": load_frames(os.path.join(root, "attack1"), duration=0.06,  loop=False),
            "die":    load_frames(os.path.join(root, "die"),     duration=0.09,  loop=False),
        }

        initial = self.animations["idle"] or \
            pyglet.image.SolidColorImagePattern((0, 180, 0, 255)).create_image(80, 100)

        super(BossGoblin, self).__init__(initial)
        self.position = (x, y)
        self.scale = 1.2   # hơn enemy nhưng tương đương player

        self.hp      = 4000
        self.max_hp  = 4000
        self.move_speed = 100

        self.hitbox_w = 60
        self.hitbox_h = 90

        self.direction = -1
        # BossGoblin mặc định nhìn TRÁI → giống goblin enemy
        self.scale_x = abs(self.scale)

        self._state          = "idle"
        self._attack_timer   = 0.0
        self._attack_cooldown = 2.0
        self._is_attacking   = False
        self._is_dying       = False
        self._die_timer      = 0.0
        self.is_dead         = False
        self._killed         = False

    def _play(self, state):
        if self._state == state:
            return
        self._state = state
        anim = self.animations.get(state)
        if anim:
            self.image = anim

    def update(self, dt, walls_layer, player):
        if self.is_dead:
            self._die_timer += dt
            return

        if self._is_dying:
            self._die_timer += dt
            if self._die_timer >= 1.2:
                self.is_dead = True
            return

        if self._attack_cooldown > 0:
            self._attack_cooldown -= dt

        if self._is_attacking:
            self.velocity_x = 0
            self._attack_timer += dt
            # attack1 has 23 frames @ 0.06s ≈ 1.38 s
            if self._attack_timer >= 1.5:
                self._is_attacking   = False
                self._attack_timer   = 0.0
                self._attack_cooldown = 1.8
                self._play("idle")
            self.update_physics(dt, walls_layer)
            return

        dist    = player.x - self.x
        abs_dist = abs(dist)

        self.direction = 1 if dist > 0 else -1
        # Sprite nhìn TRÁI mặc định: đi phải(+1) = lật âm, đi trái(-1) = không lật
        self.scale_x = -abs(self.scale) if self.direction == 1 else abs(self.scale)

        if abs_dist < 90 and self._attack_cooldown <= 0:
            self._is_attacking   = True
            self._attack_timer   = 0.0
            self._attack_cooldown = 3.5
            self._play("attack")
            self.velocity_x = 0
        elif abs_dist > 70:
            self.velocity_x = self.move_speed * self.direction
            self._play("walk")
        else:
            self.velocity_x = 0
            self._play("idle")

        self.update_physics(dt, walls_layer)

    def take_damage(self, amount):
        if self.is_dead or self._is_dying:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self._is_dying = True
            self._die_timer = 0.0
            self._play("die")


# ─── Minotaur Boss ────────────────────────────────────────────────────────────

class BossMinotaur(Entity):
    NAME = "MINOTAUR"

    def __init__(self, x, y):
        root = os.path.join(BASE_DIR, "assets", "images", "boss minotaur")

        self.animations = {
            "idle":   load_frames(os.path.join(root, "idle"), duration=0.075, loop=True),
            "walk":   load_frames(os.path.join(root, "walk"), duration=0.07,  loop=True),
            "attack": load_frames(os.path.join(root, "atk_1"), duration=0.06, loop=False),
        }

        initial = self.animations["idle"] or \
            pyglet.image.SolidColorImagePattern((128, 0, 128, 255)).create_image(80, 100)

        super(BossMinotaur, self).__init__(initial)
        self.position = (x, y)
        self.scale = 1.1   # tương đương player, nhưng nhìn ngầu hơn

        self.hp      = 5000
        self.max_hp  = 5000
        self.move_speed = 90

        self.hitbox_w = 60
        self.hitbox_h = 88

        self.direction = -1
        self.scale_x = -abs(self.scale)

        self._state           = "idle"
        self._attack_timer    = 0.0
        self._attack_cooldown = 2.0
        self._is_attacking    = False
        self.is_dead          = False
        self._killed          = False

    def _play(self, state):
        if self._state == state:
            return
        self._state = state
        anim = self.animations.get(state)
        if anim:
            self.image = anim

    def update(self, dt, walls_layer, player):
        if self.is_dead:
            return

        if self._attack_cooldown > 0:
            self._attack_cooldown -= dt

        if self._is_attacking:
            self.velocity_x = 0
            self._attack_timer += dt
            # atk_1 has 16 frames @ 0.06s ≈ 0.96 s
            if self._attack_timer >= 1.0:
                self._is_attacking    = False
                self._attack_timer    = 0.0
                self._attack_cooldown = 1.8
                self._play("idle")
            self.update_physics(dt, walls_layer)
            return

        dist     = player.x - self.x
        abs_dist = abs(dist)

        self.direction = 1 if dist > 0 else -1
        # Minotaur nhìn PHẢI mặc định: đi phải(+1) = không lật, đi trái(-1) = lật
        self.scale_x = abs(self.scale) if self.direction == 1 else -abs(self.scale)

        if abs_dist < 90 and self._attack_cooldown <= 0:
            self._is_attacking    = True
            self._attack_timer    = 0.0
            self._attack_cooldown = 3.0
            self._play("attack")
            self.velocity_x = 0
        elif abs_dist > 70:
            self.velocity_x = self.move_speed * self.direction
            self._play("walk")
        else:
            self.velocity_x = 0
            self._play("idle")

        self.update_physics(dt, walls_layer)

    def take_damage(self, amount):
        if self.is_dead:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            if not self._killed:
                self._killed = True
                try:
                    self.kill()
                except Exception:
                    pass


# Backward-compat alias (game.py imports "Boss")
Boss = BossGoblin
