import cocos
import pyglet
import os
import random
from .entity import Entity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── Utility ─────────────────────────────────────────────────────────────────

def _sort_key(filename):
    """Sort files by the trailing number in the name."""
    try:
        base = os.path.splitext(filename)[0]
        return int(base.split('_')[-1])
    except (ValueError, IndexError):
        return 0

def load_frames(folder_path, duration=0.08, loop=True):
    """Load all PNGs in a folder as a pyglet Animation with anchor set."""
    if not os.path.exists(folder_path):
        return None
    files = sorted(
        [f for f in os.listdir(folder_path) if f.endswith('.png')],
        key=_sort_key
    )
    if not files:
        return None
    frames = []
    for f in files:
        img = pyglet.image.load(os.path.join(folder_path, f))
        # Set anchor to bottom-center so sprites stand on ground properly
        img.anchor_x = img.width // 2
        img.anchor_y = 0  # Bottom anchor for ground alignment
        frames.append(pyglet.image.AnimationFrame(img, duration))
    if not loop:
        frames[-1].duration = None
    return pyglet.image.Animation(frames)

# ─── Goblin Warrior (70 %) ────────────────────────────────────────────────────

class GoblinWarrior(Entity):
    KIND = "warrior"

    def __init__(self, x, y, walk_range=250):  # Increased walk range
        root = os.path.join(BASE_DIR, "assets", "images", "enemy", "goblin warrior")

        self.anim_idle   = load_frames(os.path.join(root, "idle"),    duration=0.08,  loop=True)
        self.anim_walk   = load_frames(os.path.join(root, "walk"),    duration=0.07,  loop=True)
        self.anim_attack = load_frames(os.path.join(root, "attack2"), duration=0.07,  loop=False)
        self.anim_die    = load_frames(os.path.join(root, "die"),     duration=0.09,  loop=False)

        initial = self.anim_idle or \
            pyglet.image.SolidColorImagePattern((200, 80, 0, 255)).create_image(40, 50)

        super(GoblinWarrior, self).__init__(initial)
        self.position   = (x, y)
        self.scale      = 1.0

        # Stats - 50 HP như yêu cầu
        self.hp         = 50
        self.move_speed = 120
        self.coin_drop  = 3
        self.is_dead    = False

        # Hitbox nhỏ gọn
        self.hitbox_w = 28
        self.hitbox_h = 45

        # Patrol
        self.start_x    = x
        self.walk_range = walk_range
        self.direction  = 1
        self.velocity_x = self.move_speed

        # State
        self._state = "walk"
        self._attack_timer = 0.0
        self._die_timer    = 0.0
        self._killed       = False  # guard chống double-kill

    # ------------------------------------------------------------------
    def _play(self, state):
        if self._state == state:
            return
        self._state = state
        anim_map = {
            "idle":   self.anim_idle,
            "walk":   self.anim_walk,
            "attack": self.anim_attack,
            "die":    self.anim_die,
        }
        anim = anim_map.get(state)
        if anim:
            self.image = anim

    def update(self, dt, walls_layer):
        if self.is_dead:
            self._die_timer += dt
            if self._die_timer >= 1.0 and not self._killed:
                self._killed = True
                try:
                    self.kill()
                except Exception:
                    pass
            return

        # Update patrol direction based on walk range
        if self.x > self.start_x + self.walk_range:
            self.direction = -1  # Turn left
        elif self.x < self.start_x - self.walk_range:
            self.direction = 1   # Turn right

        # Update velocity based on direction
        self.velocity_x = self.move_speed * self.direction

        # Flip sprite: Goblin sprite faces RIGHT by default
        #   Moving RIGHT (dir=1) → normal (scale_x positive)
        #   Moving LEFT (dir=-1) → flip (scale_x negative)
        if self.direction == 1:  # Moving right
            self.scale_x = abs(self.scale)   # Normal orientation
        else:  # Moving left (direction == -1)
            self.scale_x = -abs(self.scale)  # Flip horizontally

        self._play("walk")
        old_x = self.x
        self.update_physics(dt, walls_layer)

        # Handle wall collision: if can't move, reverse direction
        if abs(self.x - old_x) < 0.1 and self.velocity_x != 0:
            self.direction *= -1
            self.start_x = self.x  # Reset patrol anchor at collision point

    def take_damage(self, amount):
        if self.is_dead:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.is_dead = True
            self._play("die")

# ─── Goblin Giant (30 %) ─────────────────────────────────────────────────────

class GoblinGiant(Entity):
    KIND = "giant"

    def __init__(self, x, y, walk_range=250):  # Increased walk range
        root = os.path.join(BASE_DIR, "assets", "images", "enemy", "goblin giant")

        self.anim_idle  = load_frames(os.path.join(root, "idle"),  duration=0.09,  loop=True)
        self.anim_walk  = load_frames(os.path.join(root, "walk"),  duration=0.08,  loop=True)
        self.anim_smash = load_frames(os.path.join(root, "smash"), duration=0.07,  loop=False)
        self.anim_die   = load_frames(os.path.join(root, "die"),   duration=0.09,  loop=False)

        initial = self.anim_idle or \
            pyglet.image.SolidColorImagePattern((0, 140, 60, 255)).create_image(54, 72)

        super(GoblinGiant, self).__init__(initial)
        self.position   = (x, y)
        self.scale      = 1.3

        # Stats - 100 HP như yêu cầu (mini-boss)
        self.hp         = 100
        self.move_speed = 80
        self.coin_drop  = 8
        self.is_dead    = False

        # Hitbox lớn hơn warrior
        self.hitbox_w = 42
        self.hitbox_h = 62

        # Patrol
        self.start_x    = x
        self.walk_range = walk_range
        self.direction  = 1
        self.velocity_x = self.move_speed

        # State
        self._state     = "walk"
        self._die_timer = 0.0
        self._killed    = False  # guard chống double-kill

    # ------------------------------------------------------------------
    def _play(self, state):
        if self._state == state:
            return
        self._state = state
        anim_map = {
            "idle":  self.anim_idle,
            "walk":  self.anim_walk,
            "smash": self.anim_smash,
            "die":   self.anim_die,
        }
        anim = anim_map.get(state)
        if anim:
            self.image = anim

    def update(self, dt, walls_layer):
        if self.is_dead:
            self._die_timer += dt
            if self._die_timer >= 1.2 and not self._killed:
                self._killed = True
                try:
                    self.kill()
                except Exception:
                    pass
            return

        # Update patrol direction based on walk range
        if self.x > self.start_x + self.walk_range:
            self.direction = -1  # Turn left
        elif self.x < self.start_x - self.walk_range:
            self.direction = 1   # Turn right

        # Update velocity based on direction
        self.velocity_x = self.move_speed * self.direction

        # Flip sprite: Goblin Giant faces RIGHT by default (same as warrior)
        if self.direction == 1:  # Moving right
            self.scale_x = abs(self.scale)   # Normal orientation
        else:  # Moving left
            self.scale_x = -abs(self.scale)  # Flip horizontally

        self._play("walk")
        old_x = self.x
        self.update_physics(dt, walls_layer)

        # Handle wall collision
        if abs(self.x - old_x) < 0.1 and self.velocity_x != 0:
            self.direction *= -1
            self.start_x = self.x

    def take_damage(self, amount):
        if self.is_dead:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.is_dead = True
            self._play("die")

# ─── Factory (70 / 30) ───────────────────────────────────────────────────────

def spawn_enemy(x, y, walk_range=250):
    """70% Goblin Warrior, 30% Goblin Giant."""
    if random.random() < 0.70:
        return GoblinWarrior(x, y, walk_range=walk_range)
    else:
        return GoblinGiant(x, y, walk_range=walk_range)

# Keep backward-compat alias
Enemy = GoblinWarrior
