import cocos
from cocos.sprite import Sprite
from cocos.layer import Layer

class Entity(Sprite):
    def __init__(self, image):
        super(Entity, self).__init__(image)
        # Thông số sinh tồn
        self.hp = 500

        # Trạng thái vật lý
        self.velocity_x = 0
        self.velocity_y = 0
        self.is_jumping = False
        self.on_ground = False

        # Hằng số vật lý mặc định (có thể ghi đè ở class con)
        self.gravity = -500
        self.move_speed = 200
        self.jump_speed = 400

    def get_logical_rect(self):
        """Trả về bounding box cố định nếu có thiết lập, tránh rung lắc hitbox do crop ảnh."""
        hit_w = getattr(self, 'hitbox_w', None)
        hit_h = getattr(self, 'hitbox_h', None)

        if hit_w is not None and hit_h is not None:
            # Tạo Rect bao quanh toạ độ chính tâm x, y
            import cocos.rect
            return cocos.rect.Rect(self.x - hit_w / 2, self.y - hit_h / 2, hit_w, hit_h)

        # Fallback: Trả về bounding box (Rect) của ảnh, luôn có rect dương
        r = self.get_rect()
        left = min(r.left, r.right)
        right = max(r.left, r.right)
        bottom = min(r.bottom, r.top)
        top = max(r.bottom, r.top)
        return type(r)(left, bottom, right - left, top - bottom)

    def update_physics(self, dt, hitboxes):
        EPS = 0.1  # chống dính collision ảo

        # ── 1. Gravity ─────────────────────────────────────────────
        self.velocity_y += self.gravity * dt

        dx = self.velocity_x * dt
        dy = self.velocity_y * dt

        # ── 2. MOVE X ─────────────────────────────────────────────
        self.x += dx
        player_rect = self.get_logical_rect()

        for rect in hitboxes:
            if player_rect.intersects(rect):
                overlap_x = min(player_rect.right, rect.right) - max(player_rect.left, rect.left)
                overlap_y = min(player_rect.top, rect.top) - max(player_rect.bottom, rect.bottom)

                # Chỉ coi là đâm vào TƯỜNG nếu mức độ xuyên thấu X nhỏ hơn Y
                if overlap_x > 0 and overlap_y > 0 and overlap_x < overlap_y:
                    if dx > 0:
                        self.x = rect.left - player_rect.width / 2 - EPS
                    elif dx < 0:
                        self.x = rect.right + player_rect.width / 2 + EPS

                    self.velocity_x = 0
                    player_rect = self.get_logical_rect()

        # ── 3. MOVE Y ─────────────────────────────────────────────
        self.on_ground = False
        self.y += dy
        player_rect = self.get_logical_rect()

        for rect in hitboxes:
            if player_rect.intersects(rect):
                overlap_x = min(player_rect.right, rect.right) - max(player_rect.left, rect.left)
                overlap_y = min(player_rect.top, rect.top) - max(player_rect.bottom, rect.bottom)

                # Chỉ coi là chạm SÀN/TRẦN nếu mức độ xuyên thấu Y nhỏ hơn hoặc bằng X
                if overlap_x > 0 and overlap_y > 0 and overlap_y <= overlap_x:
                    # rơi xuống → chạm đất
                    if self.velocity_y < 0:
                        self.y = rect.top + player_rect.height / 2 + EPS
                        self.velocity_y = 0
                        self.on_ground = True
                        self.is_jumping = False

                    # bay lên → đập đầu
                    elif self.velocity_y > 0:
                        self.y = rect.bottom - player_rect.height / 2 - EPS
                        self.velocity_y = 0

                    player_rect = self.get_logical_rect()

        # ── 4. APPLY POSITION ─────────────────────────────────────
        self.position = (self.x, self.y)