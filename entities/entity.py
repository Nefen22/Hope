import cocos
from cocos.sprite import Sprite
from cocos.layer import Layer

class Entity(Sprite):
    def __init__(self, image):
        super(Entity, self).__init__(image)
        # Thông số sinh tồn
        self.hp = 100
        
        # Trạng thái vật lý
        self.velocity_x = 0
        self.velocity_y = 0
        self.is_jumping = False
        self.on_ground = False
        
        # Hằng số vật lý mặc định (có thể ghi đè ở class con)
        self.gravity = -500
        self.move_speed = 200
        self.jump_speed = 300
        
    def kill(self):
        """Khắc phục lỗi Set changed size during iteration: hoãn lệnh xoá node."""
        import pyglet
        
        # Đánh dấu
        self._killed = True
        
        # Gọi kill thực sự từ lớp cha, an toàn ngoài vòng lặp update chính
        if getattr(self, '_kill_scheduled', False):
            return
        self._kill_scheduled = True
        
        def _safe_kill(dt):
            if self.parent:
                super(Entity, self).kill()
                
        pyglet.clock.schedule_once(_safe_kill, 0.0)
        
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
    
    def update_physics(self, dt, walls_layer):
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
        
        # Bắt va chạm tường bằng `get_in_region`
        if walls_layer:
            epsilon = 0.1
            tiles_x = list(walls_layer.get_in_region(new_rect_x.left + epsilon, new_rect_x.bottom + epsilon, new_rect_x.right - epsilon, new_rect_x.top - epsilon))
            collide_x = False
            for cell in tiles_x:
                if cell.tile and cell.tile.properties.get('solid'):
                    collide_x = True
                    if dx > 0:
                        self.x = cell.left - last_rect.width / 2
                    elif dx < 0:
                        self.x = cell.right + last_rect.width / 2
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
        
        if walls_layer:
            epsilon = 0.1
            tiles_y = list(walls_layer.get_in_region(new_rect_y.left + epsilon, new_rect_y.bottom + epsilon, new_rect_y.right - epsilon, new_rect_y.top - epsilon))
            for cell in tiles_y:
                if cell.tile and cell.tile.properties.get('solid'):
                    collide_y = True
                    if self.velocity_y < 0:
                        floor_hit = True 
                    break
            
        self.on_ground = False
        if collide_y:
            self.velocity_y = 0
            dy = 0
            if floor_hit:
                self.on_ground = True
                self.is_jumping = False
                floor_y = max(cell.top for cell in tiles_y if cell.tile and cell.tile.properties.get('solid'))
                self.y = floor_y + self.get_logical_rect().height / 2
            else:
                ceil_y = min(cell.bottom for cell in tiles_y if cell.tile and cell.tile.properties.get('solid'))
                self.y = ceil_y - self.get_logical_rect().height / 2
                
        # Áp dụng toạ độ mới cuối cùng
        self.position = (self.x + dx, self.y + dy)