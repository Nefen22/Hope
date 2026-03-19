"""
gen_map.py – Tạo map TMX với:
  • 1000+ tiles chiều ngang (Mario style)
  • Thuật toán phong phú: nền tảng nhảy, hố, tường, bục đa tầng
  • Boss room tường chắn cuối map
  • Switch puzzle (2 công tắc → mở cổng)
  • Trục Y mặt đất cố định = GROUND_ROW, tính pixel = get_ground_y()
"""
import random

# ─── Kích thước bản đồ ────────────────────────────────────────────────────────
WIDTH  = 1000   # tiles (mỗi tile = 16 px)  → 16 000 px chiều ngang
HEIGHT = 40     # tiles
TILE_W = 16
TILE_H = 16

# ─── Hằng số tiện ích ─────────────────────────────────────────────────────────
GROUND_ROW = 36          # tile row đất (0 = top, HEIGHT-1 = bottom)

def get_ground_y():
    """Trả về toạ độ pixel Y mặt đất (điểm đứng của entity).
    Trong cocos2d trục Y ngược với tile-row: row 36 = (HEIGHT - 36)*TILE_H"""
    return (HEIGHT - GROUND_ROW) * TILE_H  # 64 px

GROUND_PX = get_ground_y()   # = 64  (entity đứng thêm nửa hitbox)

# ─── Màu tile (index trong tileset Swampset 5×5) ──────────────────────────────
SOLID_TILE   = 24   # tile đất / tường (id=23, firstgid=1 → value=24)
EMPTY        = 0

# ─── Bộ sinh ngẫu nhiên với seed cố định  → map giống nhau mỗi lần chạy ─────
rng = random.Random(42)

# ===========================================================================
# 1. NỀN (background layer) – chỉ trang trí, không cần solid
# ===========================================================================
background_csv_rows = []
for y in range(HEIGHT):
    row = []
    for x in range(WIDTH):
        row.append('12' if (x + y) % 3 == 0 else '11')
    background_csv_rows.append(','.join(row) + ',')

# ===========================================================================
# 2. WALLS layer – terrain chính
# ===========================================================================
walls = [[EMPTY] * WIDTH for _ in range(HEIGHT)]

# 2a. Dải đất phía dưới (row 36 → 39)
for y in range(GROUND_ROW, HEIGHT):
    for x in range(WIDTH):
        walls[y][x] = SOLID_TILE

# 2b. Sinh bục nhảy ngẫu nhiên kiểu Mario ─────────────────────────────────────
#   Mỗi "segment" 6-10 tiles tạo 0-2 công trình
PLATFORM_LAYERS = [
    (32, 4, 7),   # (row, min_len, max_len)  – thấp
    (29, 3, 6),   # giữa
    (26, 2, 5),   # cao
    (23, 2, 4),   # rất cao
]

segment_x = 8
while segment_x < WIDTH - 80:
    seg_w = rng.randint(6, 10)
    # Chọn 0-2 platform rows trong segment này
    chosen_rows = rng.sample(PLATFORM_LAYERS, k=rng.randint(0, 2))
    for (row, mn, mx) in chosen_rows:
        plen = rng.randint(mn, mx)
        px   = segment_x + rng.randint(0, max(0, seg_w - plen))
        px   = min(px, WIDTH - 80)  # không vào boss room
        for tx in range(px, min(px + plen, WIDTH - 80)):
            walls[row][tx] = SOLID_TILE
    segment_x += seg_w

# 2c. Hố trên mặt đất (pit) – tạo khoảng hở 3-5 tiles ────────────────────────
pit_x = 30
while pit_x < WIDTH - 100:
    gap   = rng.randint(3, 5)
    for tx in range(pit_x, pit_x + gap):
        for ty in range(GROUND_ROW, HEIGHT):
            walls[ty][tx] = EMPTY
    pit_x += rng.randint(18, 35)

# 2d. Tường đứng (chướng ngại vật nhỏ) ────────────────────────────────────────
wall_x = 50
while wall_x < WIDTH - 100:
    wh = rng.randint(2, 4)   # chiều cao tường
    wx = wall_x + rng.randint(0, 4)
    for ty in range(GROUND_ROW - wh, GROUND_ROW):
        walls[ty][wx] = SOLID_TILE
    wall_x += rng.randint(25, 50)

# 2e. BOSS ROOM – cuối bản đồ ─────────────────────────────────────────────────
#   Boss room từ tile x = BOSS_ROOM_START đến hết map
BOSS_ROOM_START = 880   # px = 880*16 = 14 080

# Cổng/tường chắn (Megaman style): 2 tile cao, tường kín từ y=26→35
DOOR_X = BOSS_ROOM_START  # là cột tile phân cách
for ty in range(26, GROUND_ROW):
    walls[ty][DOOR_X]     = SOLID_TILE
    walls[ty][DOOR_X + 1] = SOLID_TILE

# Đánh dấu là "door tile" – ta sẽ dùng object  layer để quản lý
# Đặt nền bằng phẳng trong boss room; xóa các platform ngẫu nhiên đã sinh
for y in range(0, GROUND_ROW):
    for x in range(BOSS_ROOM_START, WIDTH):
        walls[y][x] = EMPTY

# Vẫn giữ đất trong boss room
for y in range(GROUND_ROW, HEIGHT):
    for x in range(BOSS_ROOM_START, WIDTH):
        walls[y][x] = SOLID_TILE

# 2f. Puzzle: 2 công tắc + cổng trước boss room ──────────────────────────────
#   Công tắc (switch) là 2 nền đặc biệt thấp ở row GROUND_ROW-1 tại x=840, x=860
SWITCH_A_X = 840
SWITCH_B_X = 860
for ty in range(GROUND_ROW - 1, GROUND_ROW):
    walls[ty][SWITCH_A_X] = SOLID_TILE
    walls[ty][SWITCH_B_X] = SOLID_TILE

# ===========================================================================
# 3. Ghi CSV
# ===========================================================================
walls_csv_rows = []
for y in range(HEIGHT):
    walls_csv_rows.append(','.join(str(v) for v in walls[y]) + ',')

bg_data    = '\n'.join(background_csv_rows)[:-1]
walls_data = '\n'.join(walls_csv_rows)[:-1]

# ===========================================================================
# 4. Tileset XML (chỉ định solid/collidable cho tất cả tile)
# ===========================================================================
TILESET_TILES = []
for tid in range(25):   # 0-24
    TILESET_TILES.append(f'''\
  <tile id="{tid}">
   <properties>
    <property name="solid" type="bool" value="true"/>
    <property name="collidable" type="bool" value="true"/>
   </properties>
  </tile>''')

tileset_xml = '\n'.join(TILESET_TILES)

# ===========================================================================
# 5. Boss trigger & Switch objects trong ObjectGroup
# ===========================================================================
boss_trigger_x_px   = DOOR_X   * TILE_W          # px
boss_trigger_y_px   = (HEIGHT - 26) * TILE_H       # top của tường (cocos coords)
boss_room_width_px  = (WIDTH - DOOR_X - 2) * TILE_W

switch_a_px_x = SWITCH_A_X * TILE_W
switch_b_px_x = SWITCH_B_X * TILE_W
switch_y_px   = (HEIGHT - GROUND_ROW) * TILE_H    # mặt đất (cocos Y)

# ===========================================================================
# 6. Viết file TMX
# ===========================================================================
map_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.11.2" orientation="orthogonal" renderorder="right-down" width="{WIDTH}" height="{HEIGHT}" tilewidth="{TILE_W}" tileheight="{TILE_H}" infinite="0" nextlayerid="5" nextobjectid="10">
 <tileset firstgid="1" name="Swampset" tilewidth="{TILE_W}" tileheight="{TILE_H}" tilecount="25" columns="5">
  <image source="Swampset.png" width="80" height="80"/>
{tileset_xml}
 </tileset>
 <layer id="1" name="background" width="{WIDTH}" height="{HEIGHT}">
  <data encoding="csv">
{bg_data}
  </data>
 </layer>
 <layer id="2" name="walls" width="{WIDTH}" height="{HEIGHT}">
  <data encoding="csv">
{walls_data}
  </data>
 </layer>
 <objectgroup id="3" name="objects">
  <object id="1" name="boss_trigger" x="{boss_trigger_x_px}" y="{boss_trigger_y_px}" width="32" height="{(GROUND_ROW - 26) * TILE_H}"/>
  <object id="2" name="switch_a" x="{switch_a_px_x}" y="{switch_y_px}" width="16" height="16"/>
  <object id="3" name="switch_b" x="{switch_b_px_x}" y="{switch_y_px}" width="16" height="16"/>
  <object id="4" name="boss_door" x="{boss_trigger_x_px}" y="{boss_trigger_y_px}" width="32" height="{(GROUND_ROW - 26) * TILE_H}"/>
 </objectgroup>
</map>
'''

import os
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'map.tmx')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(map_xml)

print(f"[gen_map] Map {WIDTH}×{HEIGHT} tiles written to {out_path}")
print(f"[gen_map] Ground Y (pixel, cocos): {GROUND_PX}")
print(f"[gen_map] Boss room starts at tile {BOSS_ROOM_START} = {BOSS_ROOM_START * TILE_W} px")
print(f"[gen_map] Door tile column: {DOOR_X}")
