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
            return cocos.rect.Rect(self.x - hit_w/2, self.y - hit_h/2, hit_w, hit_h)
            
        # Fallback: Trả về bounding box (Rect) của ảnh, luôn có rect dương
        r = self.get_rect()
        left = min(r.left, r.right)
        right = max(r.left, r.right)
        bottom = min(r.bottom, r.top)
        top = max(r.bottom, r.top)
        return type(r)(left, bottom, right - left, top - bottom)
    
    def update_physics(self, dt, hitboxes):
        """Xử lý di chuyển, trọng lực và chống va chạm gạch cơ bản"""
        # Áp dụng trọng lực thay đổi vận tốc trục Y
        self.velocity_y += self.gravity * dt
        
        # Tính toán quãng đường di chuyển dự kiến
        dx = self.velocity_x * dt
        dy = self.velocity_y * dt
        
        last_rect = self.get_logical_rect()
        
        # KIỂM TRA VA CHẠM TRỤC X
        new_rect_x = last_rect.copy()
        new_rect_x.x += dx
        
        collide_x = False
        import cocos.rect
        if hitboxes:
            for obj in hitboxes:
                obj_name = (getattr(obj, "name", "") or "").lower()
                if obj_name == "boss_trigger":
                    continue
                # cocos object layers usually have x, y at bottom-left if parsed by cocos
                obj_w = getattr(obj, "width", 0)
                obj_h = getattr(obj, "height", 0)
                if obj_w == 0 or obj_h == 0:
                    continue
                obj_rect = cocos.rect.Rect(obj.x, obj.y, obj_w, obj_h)
                
                if new_rect_x.intersects(obj_rect):
                    collide_x = True
                    if dx > 0:
                        self.x = obj_rect.left - last_rect.width / 2
                    elif dx < 0:
                        self.x = obj_rect.right + last_rect.width / 2
                    break
                    
        if collide_x:
            self.velocity_x = 0
            dx = 0
            
        # KIỂM TRA VA CHẠM TRỤC Y
        new_rect_y = self.get_logical_rect().copy()
        new_rect_y.x += dx 
        new_rect_y.y += dy
        
        collide_y = False
        floor_hit = False
        
        if hitboxes:
            for obj in hitboxes:
                obj_name = (getattr(obj, "name", "") or "").lower()
                if obj_name == "boss_trigger":
                    continue
                obj_w = getattr(obj, "width", 0)
                obj_h = getattr(obj, "height", 0)
                if obj_w == 0 or obj_h == 0:
                    continue
                obj_rect = cocos.rect.Rect(obj.x, obj.y, obj_w, obj_h)
                
                if new_rect_y.intersects(obj_rect):
                    collide_y = True
                    if self.velocity_y < 0:
                        floor_hit = True 
                        # Nếu rớt xuống trúng mặt đất, y dời lên
                        self.y = obj_rect.top + new_rect_y.height / 2
                    elif self.velocity_y > 0:
                        # Đụng đầu trần nhà
                        self.y = obj_rect.bottom - new_rect_y.height / 2
                    break
            
        self.on_ground = False
        if collide_y:
            self.velocity_y = 0
            dy = 0
            if floor_hit:
                self.on_ground = True
                self.is_jumping = False
                
        # Áp dụng toạ độ mới cuối cùng
        self.position = (self.x + dx, self.y + dy)