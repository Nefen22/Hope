import cocos
from cocos.tiles import load, RectMapLayer, TmxObjectLayer
from cocos.layer import ScrollingManager
class GameMapManager:
    def __init__(self, tmx_path):
        self.tmx_path = tmx_path
        self.tilemap = load(tmx_path)
        self.scroller = ScrollingManager()
        
        self.walls_layer = None
        
        # Danh sách chứa các hitbox để check va chạm sau này
        self.hitboxes = []
        
        # Các thông số Boss Room mặc định
        self.boss_trigger_x = 3000
        self.boss_room_left_limit = 3000
        self.boss_room_center_x = 3400

        # Duyệt qua tất cả layer có trong file TMX
        for idx, (name, layer) in enumerate(self.tilemap.find(RectMapLayer)):
            if name in ["Landable", "Objects", "Collisions"]:
                layer_objects = getattr(layer, 'objects', None)
                if layer_objects:
                    for obj in layer_objects:
                        # Thêm vào danh sách va chạm
                        self.hitboxes.append(obj)
                        
                        # Xử lý Boss Trigger
                        if obj.name == 'boss_trigger':
                            self.boss_trigger_x = obj.x
                            # Tính toán giới hạn phòng Boss
                            self.boss_room_left_limit = obj.x + getattr(obj, 'width', 0)
                            self.boss_room_center_x = self.boss_room_left_limit + 400
                continue 
            elif name == "Fore":
                self.walls_layer = layer
            # Các layer hình ảnh (Background, Walls, Decor...)
            self.scroller.add(layer, z=idx)
        # for name, layer  in self.tilemap.find(TmxObjectLayer):
        #     for obj in layer.objects:
        #         self.walls_layer.append(obj)

        
    def get_scrolling_manager(self):
        return self.scroller
        
    def get_walls_layer(self):
        return self.walls_layer
