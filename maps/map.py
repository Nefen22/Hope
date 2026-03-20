import cocos
from cocos.tiles import load
from cocos.layer import ScrollingManager

# Hằng số map (phải đồng bộ với gen_map.py)
TILE_H     = 16
MAP_HEIGHT = 40
GROUND_ROW = 36
GROUND_Y   = (MAP_HEIGHT - GROUND_ROW) * TILE_H   # 64 px (cocos Y)


class GameMapManager:
    def __init__(self, tmx_path):
        self.tmx_path   = tmx_path
        self.tilemap    = load(tmx_path)

        self.bg_layer    = self.tilemap['bg3']
        self.walls_layer = self.tilemap['bg3']

        # Mặc định (override từ object layer bên dưới)
        self.boss_trigger_x      = 880 * TILE_H   # fallback
        self.boss_room_left_limit = self.boss_trigger_x + 32
        self.boss_room_center_x   = self.boss_room_left_limit + 400

        # Lưu danh sách objects để GameLayer truy cập
        self._objects = []

        if 'objects' in self.tilemap:
            objects_layer = self.tilemap['objects']
            for obj in objects_layer.objects:
                self._objects.append(obj)
                if obj.name == 'boss_trigger':
                    self.boss_trigger_x       = obj.x
                    obj_w = obj.width if obj.width else 0
                    self.boss_room_left_limit = obj.x + obj_w
                    self.boss_room_center_x   = self.boss_room_left_limit + 400

        # ScrollingManager
        self.scroller = ScrollingManager()
        self.scroller.add(self.bg_layer,    z=0)
        self.scroller.add(self.walls_layer, z=1)

    # ──────────────────────────────────────────────────────────────────────────
    def get_scrolling_manager(self):
        return self.scroller

    def get_walls_layer(self):
        return self.walls_layer

    def get_objects(self):
        """Trả về list tất cả objects từ object-group layer."""
        return self._objects

    @staticmethod
    def get_ground_y():
        """Pixel Y mặt đất theo cocos2d (gốc tọa độ dưới-trái)."""
        return GROUND_Y
