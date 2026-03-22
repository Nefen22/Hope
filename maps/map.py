import cocos.rect
from cocos.tiles import load, RectMapLayer, TmxObjectLayer, Resource
from cocos.layer import ScrollingManager

class GameMapManager:
    def __init__(self, tmx_path):
        self.tmx_path = tmx_path
        self.tilemap: Resource = load(tmx_path)
        self.scroller = ScrollingManager()

        self.solid_rects = []
        self.hitboxes = []

        tile_w = getattr(self.tilemap, "tilewidth", 16)
        map_w = getattr(self.tilemap, "width", 160)
        self.map_pixel_width = int(map_w * tile_w)

        self.boss_trigger_x = int(self.map_pixel_width * 0.78)
        self.boss_room_left_limit = int(self.map_pixel_width * 0.80)
        self.boss_room_center_x = int(self.map_pixel_width * 0.86)

        for idx, (name, layer) in enumerate(self.tilemap.find(RectMapLayer)):
            self.scroller.add(layer, z=idx)

        for _, obj_layer in self.tilemap.find(TmxObjectLayer):
            layer_name = (getattr(obj_layer, "name", "") or "").lower()
            
            for obj in getattr(obj_layer, "objects", []):
                self.hitboxes.append(obj)
                obj_name = (getattr(obj, "name", "") or "").lower()
                
                if obj_name == "boss_trigger":
                    self.boss_trigger_x = int(getattr(obj, "x", self.boss_trigger_x))
                    obj_w = int(getattr(obj, "width", 0) or 0)
                    self.boss_room_left_limit = self.boss_trigger_x + max(120, obj_w)
                    self.boss_room_center_x = self.boss_room_left_limit + 350
                
                # Trích xuất collision box từ object layer "landable"
                if layer_name == "landable":
                    x = getattr(obj, "x", 0)
                    y = getattr(obj, "y", 0)
                    w = getattr(obj, "width", 0)
                    h = getattr(obj, "height", 0)
                    self.solid_rects.append(cocos.rect.Rect(x, y, w, h))

        self.boss_trigger_x = max(self.boss_trigger_x + 260, int(self.map_pixel_width * 0.75))
        self.boss_trigger_x = max(900, min(self.boss_trigger_x, self.map_pixel_width - 420))
        self.boss_room_left_limit = max(self.boss_trigger_x + 80, min(self.boss_room_left_limit, self.map_pixel_width - 260))
        self.boss_room_center_x = max(self.boss_room_left_limit + 120, min(self.boss_room_center_x, self.map_pixel_width - 140))

    def get_scrolling_manager(self):
        return self.scroller

    def get_walls_layer(self):
        # Trả về danh sách hitbox tĩnh thay vì layer map
        return self.solid_rects

    def get_map_pixel_width(self):
        return self.map_pixel_width