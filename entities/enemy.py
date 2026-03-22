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
        img.anchor_x = img.width // 2
        img.anchor_y = 0  # Bottom anchor for ground alignment
        frames.append(pyglet.image.AnimationFrame(img, duration))
    if not loop:
        frames[-1].duration = None
    return pyglet.image.Animation(frames)

# ─── Goblin Warrior (70 %) ────────────────────────────────────────────────────

class GoblinWarrior(Entity):
    KIND = "warrior"

    # Khoảng cách để kích hoạt tấn công (pixel)
    ATTACK_RANGE   = 60
    # Thời gian hồi chiêu tấn công (giây)
    ATTACK_COOLDOWN = 1.2

    def __init__(self, x, y, walk_range=250):
        root = os.path.join(BASE_DIR, "assets", "images", "enemy", "goblin warrior")

        self.anim_idle   = load_frames(os.path.join(root, "idle"),    duration=0.08,  loop=True)
        self.anim_walk   = load_frames(os.path.join(root, "walk"),    duration=0.07,  loop=True)
        self.anim_attack = load_frames(os.path.join(root, "attack2"), duration=0.07,  loop=False)
        self.anim_hurt   = load_frames(os.path.join(root, "hurt"),    duration=0.07,  loop=False)
        self.anim_die    = load_frames(os.path.join(root, "die"),     duration=0.09,  loop=False)

        initial = self.anim_idle or \
            pyglet.image.SolidColorImagePattern((200, 80, 0, 255)).create_image(40, 50)

        super(GoblinWarrior, self).__init__(initial)
        self.position   = (x, y)
        self.scale      = 1.0

        # Stats
        self.hp         = 50
        self.max_hp     = 50
        self.move_speed = 120
        self.coin_drop  = 3
        self.is_dead    = False

        # Hitbox
        self.hitbox_w = 28
        self.hitbox_h = 45

        # Patrol
        self.start_x    = x
        self.walk_range = walk_range
        self.direction  = 1
        self.velocity_x = self.move_speed

        # State - khởi tạo là "idle" để phù hợp với animation ban đầu
        self._state          = "idle"
        self._attack_timer   = 0.0
        self._hurt_timer     = 0.0
        self._die_timer      = 0.0
        self._killed         = False
        self._is_attacking   = False
        self._is_hurt        = False

        # Gán animation idle ngay
        if self.anim_idle:
            self.image = self.anim_idle

    # ------------------------------------------------------------------
    def _play(self, state):
        if self._state == state:
            return
        self._state = state
        anim_map = {
            "idle":   self.anim_idle,
            "walk":   self.anim_walk,
            "attack": self.anim_attack,
            "hurt":   self.anim_hurt,
            "die":    self.anim_die,
        }
        anim = anim_map.get(state)
        if anim:
            self.image = anim

    def update(self, dt, walls_layer, player=None):
        if self.is_dead:
            self._die_timer += dt
            if self._die_timer >= 1.0 and not self._killed:
                self._killed = True
                try:
                    self.kill()
                except Exception:
                    pass
            return

        # Hurt flash
        if self._is_hurt:
            self._hurt_timer -= dt
            if self._hurt_timer <= 0:
                self._is_hurt = False
            return  # Đứng yên khi bị đánh

        # Cooldown tấn công
        if self._attack_timer > 0:
            self._attack_timer -= dt

        # Nếu có player và gần thì tấn công
        if player is not None:
            dist = abs(self.x - player.x)
            if dist < self.ATTACK_RANGE and abs(self.y - player.y) < 60:
                # Quay mặt về phía player
                self.direction = 1 if player.x > self.x else -1
                self.scale_x = abs(self.scale) * self.direction

                if self._attack_timer <= 0 and not self._is_attacking:
                    self._play("attack")
                    self._is_attacking = True
                    self._attack_timer = self.ATTACK_COOLDOWN

                # Trong lúc tấn công không di chuyển
                if self._is_attacking:
                    self.velocity_x = 0
                    # Kiểm tra animation attack đã xong chưa
                    if self._state == "attack":
                        anim_duration = len(self.anim_attack.frames) * 0.07 if self.anim_attack else 0.5
                        if self._attack_timer < self.ATTACK_COOLDOWN - anim_duration:
                            self._is_attacking = False
                            self._play("walk")
                    self.update_physics(dt, walls_layer)
                    return

        # Patrol logic
        if self.x > self.start_x + self.walk_range:
            self.direction = -1
        elif self.x < self.start_x - self.walk_range:
            self.direction = 1

        self.velocity_x = self.move_speed * self.direction

        if self.direction == 1:
            self.scale_x = abs(self.scale)
        else:
            self.scale_x = -abs(self.scale)

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
            self._is_attacking = False
            self._play("die")
        else:
            # Phát animation bị thương
            if not self._is_hurt:
                self._is_hurt = True
                self._hurt_timer = 0.3
                self._play("hurt")

    def is_attacking_player(self):
        """Trả về True nếu đang trong frame tấn công có thể gây damage."""
        return self._is_attacking and self._attack_timer > self.ATTACK_COOLDOWN - 0.4

# ─── Goblin Giant (30 %) ─────────────────────────────────────────────────────

class GoblinGiant(Entity):
    KIND = "giant"

    ATTACK_RANGE    = 80
    ATTACK_COOLDOWN = 2.0

    def __init__(self, x, y, walk_range=250):
        root = os.path.join(BASE_DIR, "assets", "images", "enemy", "goblin giant")

        self.anim_idle  = load_frames(os.path.join(root, "idle"),  duration=0.09,  loop=True)
        self.anim_walk  = load_frames(os.path.join(root, "walk"),  duration=0.08,  loop=True)
        self.anim_smash = load_frames(os.path.join(root, "smash"), duration=0.07,  loop=False)
        self.anim_hurt  = load_frames(os.path.join(root, "hurt"),  duration=0.07,  loop=False)
        self.anim_die   = load_frames(os.path.join(root, "die"),   duration=0.09,  loop=False)

        initial = self.anim_idle or \
            pyglet.image.SolidColorImagePattern((0, 140, 60, 255)).create_image(54, 72)

        super(GoblinGiant, self).__init__(initial)
        self.position   = (x, y)
        self.scale      = 1.3

        # Stats - Giant khó hơn
        self.hp         = 100
        self.max_hp     = 100
        self.move_speed = 80
        self.coin_drop  = 8
        self.is_dead    = False

        # Hitbox
        self.hitbox_w = 42
        self.hitbox_h = 62

        # Patrol
        self.start_x    = x
        self.walk_range = walk_range
        self.direction  = 1
        self.velocity_x = self.move_speed

        # State - khởi tạo là "idle" để phù hợp với animation ban đầu
        self._state        = "idle"
        self._attack_timer = 0.0
        self._hurt_timer   = 0.0
        self._die_timer    = 0.0
        self._killed       = False
        self._is_attacking = False
        self._is_hurt      = False

        # Gán animation idle ngay
        if self.anim_idle:
            self.image = self.anim_idle

    # ------------------------------------------------------------------
    def _play(self, state):
        if self._state == state:
            return
        self._state = state
        anim_map = {
            "idle":  self.anim_idle,
            "walk":  self.anim_walk,
            "smash": self.anim_smash,
            "hurt":  self.anim_hurt,
            "die":   self.anim_die,
        }
        anim = anim_map.get(state)
        if anim:
            self.image = anim

    def update(self, dt, walls_layer, player=None):
        if self.is_dead:
            self._die_timer += dt
            if self._die_timer >= 1.2 and not self._killed:
                self._killed = True
                try:
                    self.kill()
                except Exception:
                    pass
            return

        # Hurt flash
        if self._is_hurt:
            self._hurt_timer -= dt
            if self._hurt_timer <= 0:
                self._is_hurt = False
            return

        if self._attack_timer > 0:
            self._attack_timer -= dt

        # Tấn công player nếu gần
        if player is not None:
            dist = abs(self.x - player.x)
            if dist < self.ATTACK_RANGE and abs(self.y - player.y) < 80:
                self.direction = 1 if player.x > self.x else -1
                self.scale_x = abs(self.scale) * self.direction

                if self._attack_timer <= 0 and not self._is_attacking:
                    self._play("smash")
                    self._is_attacking = True
                    self._attack_timer = self.ATTACK_COOLDOWN

                if self._is_attacking:
                    self.velocity_x = 0
                    if self._state == "smash":
                        anim_duration = len(self.anim_smash.frames) * 0.07 if self.anim_smash else 0.7
                        if self._attack_timer < self.ATTACK_COOLDOWN - anim_duration:
                            self._is_attacking = False
                            self._play("walk")
                    self.update_physics(dt, walls_layer)
                    return

        # Patrol
        if self.x > self.start_x + self.walk_range:
            self.direction = -1
        elif self.x < self.start_x - self.walk_range:
            self.direction = 1

        self.velocity_x = self.move_speed * self.direction

        if self.direction == 1:
            self.scale_x = abs(self.scale)
        else:
            self.scale_x = -abs(self.scale)

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
            self._is_attacking = False
            self._play("die")
        else:
            if not self._is_hurt:
                self._is_hurt = True
                self._hurt_timer = 0.4
                self._play("hurt")

    def is_attacking_player(self):
        """Trả về True nếu đang trong frame tấn công có thể gây damage."""
        return self._is_attacking and self._attack_timer > self.ATTACK_COOLDOWN - 0.5

# ─── Factory (60 / 40) ───────────────────────────────────────────────────────

def spawn_enemy(x, y, walk_range=250):
    """70% Goblin Warrior, 30% Goblin Giant."""
    if random.random() < 0.60:
        return GoblinWarrior(x, y, walk_range=walk_range)
    else:
        return GoblinGiant(x, y, walk_range=walk_range)

# Keep backward-compat alias
Enemy = GoblinWarrior
