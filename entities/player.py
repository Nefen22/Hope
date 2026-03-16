import cocos
from cocos.sprite import Sprite
from pyglet.window import key
import os
import pyglet
from .entity import Entity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_PATH = os.path.join(BASE_DIR, "assets", "images", "player")
ANIM_SCALE = 0.08
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
        x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y
    )
    return cropped

def load_animations(folder_path):
    animations = {}
    for filename in os.listdir(folder_path):
        if not filename.endswith(".png"): continue
        name = os.path.splitext(filename.replace("_", ""))[0]
        full_path = os.path.join(folder_path, filename)
        image = pyglet.image.load(full_path)

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
        # Thiết lập tạm thời animation đầu tiên
        self.animations = load_animations(ASSET_PATH)
        super(PlayerSprite, self).__init__(self.animations["Idle"])
        
        self.hp = hp
        self.mass = mass
        self.scale = 1.5
        
        self.hitbox_w = 40
        self.hitbox_h = 60
        self.locktimer = 0
        self.isGoingtoRight = True
        
        self.current_state = "Idle"
        self.keys = set()
        
        # Biến trạng thái chiến đấu
        self.is_invincible = False
        self.invincible_timer = 0
        self.is_attacking = False
        self.attack_rect = None # Vùng chém kiếm
        
    def play(self, state):
        if self.current_state != state:
            self.current_state = state
            self.image = self.animations[state]

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)
        
        # Nhảy
        if symbol == key.SPACE and self.on_ground:
            self.velocity_y = self.jump_speed
            self.is_jumping = True
            self.on_ground = False

    def on_key_release(self, symbol, modifiers):
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
            at_w = 40
            at_h = 60
            offset_x = 40 if self.isGoingtoRight else -40
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
