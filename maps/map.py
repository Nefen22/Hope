from cocos.tiles import load, RectMapLayer, TmxObjectLayer


class Map():
    def __init__(self, path):
        self.layers = []
        self.collision_objects = []

        # 1. Load resource
        self.tmx_data = load(path)

        # 2. Tìm đối tượng bản đồ thực sự (Bỏ qua các Tileset)
        main_map = None
        for item in self.tmx_data.contents.values():
            # Kiểm tra nếu đối tượng này có thuộc tính px_height (đặc trưng của Map Layer)
            if hasattr(item, 'px_height'):
                main_map = item
                break

        if main_map is None:
            # Nếu vẫn không tìm thấy, thử lấy thông tin từ tmx_data trực tiếp
            # (tùy phiên bản cocos)
            print("Cảnh báo: Không tìm thấy Map Layer chính để lấy chiều cao!")
            map_h = 600  # Giá trị mặc định nếu hỏng hoàn toàn
        else:
            map_h = main_map.px_height

        # 3. Duyệt tìm các Layer hình ảnh để vẽ
        for index, (name, layer) in enumerate(self.tmx_data.find(RectMapLayer)):
            layer.set_view(0, 0, layer.px_width, layer.px_height)
            layer.position = (0, 0)
            self.layers.append((layer, index))

        ## Trong maps/map.py
        for name, layer in self.tmx_data.find(TmxObjectLayer):
            if name == 'objects':
                for obj in layer.objects:
                    self.collision_objects.append(obj)

    def draw(self, container_layer):
        for (ele, index) in self.layers:
            container_layer.add(ele, z=index)