import cocos
from cocos.tiles import load
from cocos.layer import ScrollingManager

# Quản lý chức năng nạp Map và setup ScrollingManager
class GameMapManager:
    def __init__(self, tmx_path):
        self.tmx_path = tmx_path
        self.tilemap = load(tmx_path)
        
        # Phân tách layer theo chuẩn
        self.bg_layer = self.tilemap['background']
        self.walls_layer = self.tilemap['walls']
        
        # Quét Object Layer (Boss Room trigger)
        self.boss_trigger_x = 3000
        self.boss_room_left_limit = 3000
        self.boss_room_center_x = 3400
        
        if 'objects' in self.tilemap:
            objects_layer = self.tilemap['objects']

            # Some TMX files define an "objects" tile layer instead of an object layer.
            # Only iterate when the layer actually exposes object entries.
            layer_objects = getattr(objects_layer, 'objects', None)
            if layer_objects:
                for obj in layer_objects:
                    if getattr(obj, 'name', None) == 'boss_trigger':
                        self.boss_trigger_x = obj.x
                        self.boss_room_left_limit = obj.x + (obj.width if obj.width else 0)
                        self.boss_room_center_x = self.boss_room_left_limit + 400
                        break
        
        # Thiết lập camera cuộn Manager chung
        self.scroller = ScrollingManager()
        
        # Nhét 2 layer đồ hoạ vào trước
        self.scroller.add(self.bg_layer, z=0)
        self.scroller.add(self.walls_layer, z=1)
        
    def get_scrolling_manager(self):
        return self.scroller
        
    def get_walls_layer(self):
        return self.walls_layer
