import cocos
from cocos.sprite import Sprite
from pyglet.window import key
import os
import pyglet
from .entity import Entity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_PATH = os.path.join(BASE_DIR, "assets", "images", "player")
ANIM_SCALE = 0.09  # Speed up animation slightly
LOCK_ACTION = [key.X, key.C, key.Z]

# Khai báo vòng lặp animation
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

# Width cho từng animation để crop chính xác (mượt hơn auto-crop)
animWidth = {
    "Run": 40, "Roll": 40, "Idle": 40,
    "Attack": 80, "Attack2": 80, "AttackNoMovement": 80,
    "Attack2NoMovement": 80, "AttackCombo": 80, "AttackComboNoMovement": 80,
    "Crouch": 40, "CrouchAttack": 80, "CrouchFull": 40, "CrouchTransition": 40, "CrouchWalk": 40,
    "Dash": 40, "Death": 40, "DeathNoMovement": 40, "Fall": 40,
    "Hit": 40, "Jump": 40, "JumpFallInbetween": 40,
    "Slide": 40, "SlideFull": 40, "SlideTransitionStart": 40, "SlideTransitionEnd": 40,
    "TurnAround": 40, "WallClimb": 40, "WallClimbNoMovement": 40, "WallHang": 40, "WallSlide": 40,
}

def load_animations(folder_path):
    """Load animations with fixed offset and width (smoother than auto-crop)"""
    animations = {}
    for filename in os.listdir(folder_path):
        if not filename.endswith(".png"):
            continue
        name = os.path.splitext(filename.replace("_", ""))[0]
        full_path = os.path.join(folder_path, filename)
        image = pyglet.image.load(full_path)

        frame_block = 120  # Each frame is 120px wide in sprite sheet
        frame_count = image.width // 120

        # Get width for this animation (default to 40 if not specified)
        width = animWidth.get(name, 40)

        # Crop frames with fixed offset (40px from left) and custom width
        frames = []
        for i in range(frame_count):
            frame_img = image.get_region(
                x=i * frame_block + 40,  # Fixed offset for cleaner crop
                y=0,
                width=width,
                height=80
            )
            # Set anchor to bottom-center so player stands on ground properly
            frame_img.anchor_x = width // 2
            frame_img.anchor_y = 0  # Bottom anchor for ground alignment
            frames.append(frame_img)

        animation = pyglet.image.Animation.from_image_sequence(
            frames, ANIM_SCALE, isLoop.get(name, True)
        )
        animations[name] = animation

    return animations

class PlayerSprite(Entity):
    is_event_handler = True

    def __init__(self, hp=100, mass=0):
        # Thiết lập animations
        self.animations = load_animations(ASSET_PATH)
        super(PlayerSprite, self).__init__(self.animations["Idle"])

        self.hp = hp
        self.mass = mass
        self.scale = 1.5

        # Hitbox nhỏ gọn, đứng đúng mặt đất
        self.hitbox_w = 30
        self.hitbox_h = 50
        self.locktimer = 0
        self.isGoingtoRight = True
        
        self.current_state = "Idle"
        self.keys = set()
        
        # Biến trạng thái chiến đấu
        self.is_invincible = False
        self.invincible_timer = 0
        self.is_attacking = False
        self.attack_rect = None # Vùng chém kiếm
        self.input_locked = False

    def set_input_locked(self, locked):
        self.input_locked = bool(locked)
        if self.input_locked:
            self.keys.clear()
            self.velocity_x = 0
        
    def play(self, state):
        if self.current_state != state:
            self.current_state = state
            self.image = self.animations[state]

    def on_key_press(self, symbol, modifiers):
        if self.input_locked:
            return
        self.keys.add(symbol)
        
        # Nhảy
        if symbol == key.SPACE and self.on_ground:
            self.velocity_y = self.jump_speed
            self.is_jumping = True
            self.on_ground = False

    def on_key_release(self, symbol, modifiers):
        if self.input_locked:
            return
        if symbol in self.keys:
            self.keys.remove(symbol)
            
        # Thả phím di chuyển thì fix trôi người
        if symbol == key.LEFT and self.velocity_x < 0:
            self.velocity_x = 0
        elif symbol == key.RIGHT and self.velocity_x > 0:
            self.velocity_x = 0

    def lock_action(self, dt):
        lock_action = False
        
        if self.locktimer > 0:
            self.locktimer = max(0, self.locktimer - dt)
            return True
            
        if key.X in self.keys:
            self.play("Attack")
            lock_action = True
            self.is_attacking = True
        elif key.C in self.keys:
            self.play("Attack2")
            lock_action = True
            self.is_attacking = True
        elif key.Z in self.keys:
            self.play("Dash")
            self.velocity_x = self.move_speed * 3 if self.isGoingtoRight else -self.move_speed * 3
            lock_action = True
            self.is_invincible = True # Bất tử tạm lúc Dash
            self.invincible_timer = 0.2

        if lock_action:
            self.locktimer = len(self.animations[self.current_state].frames) * ANIM_SCALE
            list(map(lambda x: self.on_key_release(x, None), LOCK_ACTION))
            
            # Gắn hitbox kiếm ở đằng trước nhân vật
            import cocos.rect
            at_w = 50  # Wider attack range for better feel
            at_h = 55
            offset_x = 45 if self.isGoingtoRight else -45
            self.attack_rect = cocos.rect.Rect(self.x + offset_x - at_w/2, self.y - at_h/2, at_w, at_h)
            
            return True
            
        return False
        
    def take_damage(self, amount):
        if self.is_invincible: return False
        self.hp -= amount
        self.is_invincible = True
        self.invincible_timer = 2.0 # Bất tử 2s khi bị đánh
        return True

    def update(self, dt, walls_layer):
        # Update trạng thái bất tử
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
            # Chớp nháy màu (Alpha) nếu bị đánh trúng
            self.opacity = 50 if (int(self.invincible_timer * 15) % 2 == 0) else 255
            if self.invincible_timer <= 0:
                self.is_invincible = False
                self.opacity = 255
                
        if self.input_locked:
            self.velocity_x = 0
            self.is_attacking = False
            self.attack_rect = None
            if self.on_ground:
                self.play("Idle")
            self.update_physics(dt, walls_layer)
            return

        # 1. KIỂM TRA ACTION KHOÁ (Tấn công, Dash...)
        if self.lock_action(dt):
            # Vẫn gọi update_physics để bị rớt tự do khi đang đánh trên không
            self.update_physics(dt, walls_layer)
            return
            
        self.locktimer = 0
        self.is_attacking = False
        self.attack_rect = None
        
        # 2. XỬ LÝ NHẬN INPUT DI CHUYỂN
        if key.RIGHT in self.keys:
            self.velocity_x = self.move_speed
            self.isGoingtoRight = True
            self.scale_x = 1.5
        elif key.LEFT in self.keys:
            self.velocity_x = -self.move_speed
            self.isGoingtoRight = False
            self.scale_x = -1.5
            
        # 3. MÁY TRẠNG THÁI ANIMATION (State Machine)
        if not self.on_ground:
            if self.velocity_y > 0:
                self.play("Jump")
            else:
                self.play("Fall")
        else:
            if self.velocity_x != 0:
                self.play("Run")
            else:
                self.play("Idle")
                
        # 4. GỌI VẬT LÝ VÀ VA CHẠM TỪ LỚP CHA
        self.update_physics(dt, walls_layer)
