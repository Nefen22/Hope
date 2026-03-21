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
        self.scale = 1.8

        # Stats - 500 HP như yêu cầu (25-50 sword hits với random 10-20 dmg)
        self.hp      = 500
        self.max_hp  = 500
        self.move_speed = 120

        # Hitbox to hơn nhưng realistic
        self.hitbox_w = 65
        self.hitbox_h = 95

        self.direction = -1  # -1 = left, 1 = right
        # BossGoblin sprite faces RIGHT by default (same as normal goblins)
        self.scale_x = -abs(self.scale)  # Flip when facing left initially

        self._state          = "idle"
        self._attack_timer   = 0.0
        self._attack_cooldown = 1.5  # Reduced for more aggressive boss
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
                self._attack_cooldown = 1.2  # Faster cooldown for aggressive boss
                self._play("idle")
            self.update_physics(dt, walls_layer)
            return

        # Calculate distance and direction to player
        dist     = player.x - self.x
        abs_dist = abs(dist)
        self.direction = 1 if dist > 0 else -1

        # Flip sprite: Boss Goblin faces RIGHT by default (same as normal goblins)
        #   Facing RIGHT (dir=1) → normal
        #   Facing LEFT (dir=-1) → flip
        if self.direction == 1:  # Facing right
            self.scale_x = abs(self.scale)   # Normal
        else:  # Facing left
            self.scale_x = -abs(self.scale)  # Flip

        # AI behavior based on distance
        if abs_dist < 100 and self._attack_cooldown <= 0:
            self._is_attacking   = True
            self._attack_timer   = 0.0
            self._attack_cooldown = 2.5  # Prevent spam
            self._play("attack")
            self.velocity_x = 0
        elif abs_dist > 80:
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
            "die":    load_frames(os.path.join(root, "die"), duration=0.10, loop=False),  # Added die animation
        }

        initial = self.animations["idle"] or \
            pyglet.image.SolidColorImagePattern((128, 0, 128, 255)).create_image(80, 100)

        super(BossMinotaur, self).__init__(initial)
        self.position = (x, y)
        self.scale = 2.0  # Larger than Goblin Boss - final boss presence

        # Final boss - 700 HP (harder than Goblin Boss)
        self.hp      = 700
        self.max_hp  = 700
        self.move_speed = 110

        # Hitbox to nhất nhưng realistic
        self.hitbox_w = 70
        self.hitbox_h = 100

        self.direction = 1  # Minotaur faces RIGHT by default (different from goblins)
        self.scale_x = abs(self.scale)  # Normal when facing right

        self._state           = "idle"
        self._attack_timer    = 0.0
        self._attack_cooldown = 1.5  # Aggressive final boss
        self._is_attacking    = False
        self._is_dying        = False
        self._die_timer       = 0.0
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

        if self._is_dying:
            self._die_timer += dt
            if self._die_timer >= 1.5:  # Longer death animation for final boss
                self.is_dead = True
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
                self._attack_cooldown = 1.2  # Fast cooldown for challenge
                self._play("idle")
            self.update_physics(dt, walls_layer)
            return

        # Calculate distance and direction to player
        dist     = player.x - self.x
        abs_dist = abs(dist)
        self.direction = 1 if dist > 0 else -1

        # Flip sprite: Minotaur faces RIGHT by default (opposite of goblins)
        #   Facing RIGHT (dir=1) → normal
        #   Facing LEFT (dir=-1) → flip
        if self.direction == 1:  # Facing right
            self.scale_x = abs(self.scale)   # Normal
        else:  # Facing left
            self.scale_x = -abs(self.scale)  # Flip

        # AI behavior - more aggressive than Goblin Boss
        if abs_dist < 100 and self._attack_cooldown <= 0:
            self._is_attacking    = True
            self._attack_timer    = 0.0
            self._attack_cooldown = 2.0
            self._play("attack")
            self.velocity_x = 0
        elif abs_dist > 80:
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
            if self.animations.get("die"):
                self._play("die")
            # Don't kill immediately - let die animation play
            # Game will detect is_dead after animation completes


# Backward-compat alias (game.py imports "Boss")
Boss = BossGoblin
