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
    """Load all PNGs in a folder as a pyglet Animation."""
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
        frames.append(pyglet.image.AnimationFrame(img, duration))
    if not loop:
        frames[-1].duration = None
    return pyglet.image.Animation(frames)

# ─── Goblin Warrior (70 %) ────────────────────────────────────────────────────

class GoblinWarrior(Entity):
    KIND = "warrior"

    def __init__(self, x, y, walk_range=180):
        root = os.path.join(BASE_DIR, "assets", "images", "enemy", "goblin warrior")

        self.anim_idle   = load_frames(os.path.join(root, "idle"),    duration=0.08,  loop=True)
        self.anim_walk   = load_frames(os.path.join(root, "walk"),    duration=0.07,  loop=True)
        self.anim_attack = load_frames(os.path.join(root, "attack2"), duration=0.07,  loop=False)
        self.anim_die    = load_frames(os.path.join(root, "die"),     duration=0.09,  loop=False)

        initial = self.anim_idle or \
            pyglet.image.SolidColorImagePattern((200, 80, 0, 255)).create_image(40, 50)

        super(GoblinWarrior, self).__init__(initial)
        self.position   = (x, y)
        self.scale      = 0.9   # nhỏ hơn player (1.5)

        # Stats
        self.hp         = 80
        self.move_speed = 110
        self.coin_drop  = 2
        self.is_dead    = False

        # Hitbox
        self.hitbox_w = 30
        self.hitbox_h = 50

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
            self.velocity_x = 0
            self.update_physics(dt, walls_layer)
            self._die_timer += dt
            if self._die_timer >= 1.0 and not self._killed:
                self._killed = True
                try:
                    self.kill()
                except Exception:
                    pass
            return

        # 1. Tính toán hướng dựa trên phạm vi tuần tra
        if self.x > self.start_x + self.walk_range:
            self.direction = -1 # Quay sang trái
        elif self.x < self.start_x - self.walk_range:
            self.direction = 1  # Quay sang phải

        # 2. Đồng nhất vận tốc: direction dương thì velocity dương
        self.velocity_x = self.move_speed * self.direction
        # Sprite mặc định nhìn sang TRÁI → direction=1 (đi phải) cần lật = scale_x âm
        # direction=-1 (đi trái) = scale_x dương (không lật)
        self.scale_x = -abs(self.scale) if self.direction == 1 else abs(self.scale)

        self._play("walk")
        old_x = self.x
        self.update_physics(dt, walls_layer)

        # 4. Xử lý va chạm tường: Nếu không di chuyển được thì đổi hướng ngay
        if abs(self.x - old_x) < 0.1 and self.velocity_x != 0:
            self.direction *= -1
            self.start_x = self.x # Reset mốc tuần tra tại điểm va chạm

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

    def __init__(self, x, y, walk_range=150):
        root = os.path.join(BASE_DIR, "assets", "images", "enemy", "goblin giant")

        self.anim_idle  = load_frames(os.path.join(root, "idle"),  duration=0.09,  loop=True)
        self.anim_walk  = load_frames(os.path.join(root, "walk"),  duration=0.08,  loop=True)
        self.anim_smash = load_frames(os.path.join(root, "smash"), duration=0.07,  loop=False)
        self.anim_die   = load_frames(os.path.join(root, "die"),   duration=0.09,  loop=False)

        initial = self.anim_idle or \
            pyglet.image.SolidColorImagePattern((0, 140, 60, 255)).create_image(54, 72)

        super(GoblinGiant, self).__init__(initial)
        self.position   = (x, y)
        self.scale      = 1.2   # to hơn warrior nhưng không quá lớn so với player

        # Stats (tougher than warrior)
        self.hp         = 200
        self.move_speed = 75
        self.coin_drop  = 5
        self.is_dead    = False

        # Hitbox
        self.hitbox_w = 44
        self.hitbox_h = 65

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
            self.velocity_x = 0
            self.update_physics(dt, walls_layer)
            self._die_timer += dt
            if self._die_timer >= 1.2 and not self._killed:
                self._killed = True
                try:
                    self.kill()
                except Exception:
                    pass
            return

        if self.x > self.start_x + self.walk_range:
            self.direction = -1
        elif self.x < self.start_x - self.walk_range:
            self.direction = 1

        self.velocity_x = self.move_speed * self.direction
        self.scale_x = -abs(self.scale) if self.direction == 1 else abs(self.scale)

        self._play("walk")
        old_x = self.x
        self.update_physics(dt, walls_layer)

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

def spawn_enemy(x, y, walk_range=180):
    """70% Goblin Warrior, 30% Goblin Giant."""
    if random.random() < 0.70:
        return GoblinWarrior(x, y, walk_range=walk_range)
    else:
        return GoblinGiant(x, y, walk_range=walk_range)

# Keep backward-compat alias
Enemy = GoblinWarrior
