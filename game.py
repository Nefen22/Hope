"""
game.py – Game chính
Tính năng:
  • Đồng bộ trục Y (ground_y từ walls_layer)
  • Megaman-style boss room transition (camera pan, door lock)
  • Switch puzzle: đạp 2 công tắc → mở cổng boss
  • Tích hợp SFX/BGM
  • Khởi chạy từ Menu
"""
import cocos
import random
import pyglet
from cocos.scene import Scene
from cocos.layer import ScrollableLayer
from cocos.director import director
from cocos.actions import (MoveTo, CallFunc, Delay, FadeIn, FadeOut)
from cocos.actions import sequence as Sequence
import cocos.rect

from maps.map   import GameMapManager
from entities.player import PlayerSprite
from entities.enemy  import GoblinWarrior, GoblinGiant, spawn_enemy
from entities.item   import Item
from entities.block  import Block
from entities.boss   import BossGoblin, BossMinotaur, Boss
from ui    import HUD
from sound import SoundManager

# ── Gen_map constants (phải khớp với gen_map.py) ──────────────────────────────
TILE_H        = 16
MAP_HEIGHT    = 40        # tiles
GROUND_ROW    = 36        # tile row mặt đất
GROUND_Y      = (MAP_HEIGHT - GROUND_ROW) * TILE_H   # = 64 px (cocos Y)
ENTITY_STAND_Y = GROUND_Y + 32   # entity đứng thêm nửa hitbox 60→30, block 32→16

# ── Phase hằng số ─────────────────────────────────────────────────────────────
PHASE_TRAVEL     = "travel"
PHASE_DOOR_LOCK  = "door_lock"    # đang cinematic khóa cửa
PHASE_BOSS1      = "boss1"
PHASE_TRANSITION = "transition"
PHASE_BOSS2      = "boss2"
PHASE_VICTORY    = "victory"

TRANSITION_DURATION  = 3.0
MINOTAUR_SPAWN_DELAY = 6.0
CAMERA_PAN_TIME      = 2.0   # giây camera pan vào boss room

# ── Puzzle ────────────────────────────────────────────────────────────────────
SWITCH_RADIUS = 24   # pixel, khoảng cách kích hoạt công tắc


class SwitchMarker(cocos.sprite.Sprite):
    """Thị giác công tắc (hình vuông màu đỏ → xanh khi kích hoạt)."""
    def __init__(self, x, y, switch_id):
        try:
            img = pyglet.image.load("assets/switch.png")
        except Exception:
            img = pyglet.image.SolidColorImagePattern((220, 60, 60, 255)).create_image(20, 20)
        super().__init__(img)
        self.position      = (x, y)
        self.switch_id     = switch_id
        self.is_activated  = False
        self._killed       = False

    def activate(self):
        if self.is_activated:
            return
        self.is_activated = True
        # Đổi màu sang xanh
        try:
            img = pyglet.image.SolidColorImagePattern((60, 220, 60, 255)).create_image(20, 20)
            self.image = img
        except Exception:
            pass
        SoundManager.play_sfx('switch')


class BossDoor(cocos.sprite.Sprite):
    """Cổng trước boss room – bị xóa khi cả 2 switch được kích hoạt."""
    def __init__(self, x, y, h_px):
        try:
            img = pyglet.image.load("assets/door.png")
        except Exception:
            img = pyglet.image.SolidColorImagePattern((80, 40, 10, 240)).create_image(32, h_px)
        super().__init__(img)
        self.position = (x + 16, y + h_px // 2)
        self.is_open  = False
        self._killed  = False

    def open_door(self):
        if self.is_open:
            return
        self.is_open = True
        SoundManager.play_sfx('door_open')
        self.do(Sequence(FadeOut(0.5), CallFunc(self._remove)))

    def _remove(self):
        self._killed = True
        try:
            self.kill()
        except Exception:
            pass


class GameLayer(ScrollableLayer):
    is_event_handler = True

    # ──────────────────────────────────────────────────────────────────────────
    def __init__(self, map_manager, hud):
        super(GameLayer, self).__init__()

        self.map_manager   = map_manager
        self.walls_layer   = map_manager.get_walls_layer()
        self.hud           = hud
        self.items_collected = 0

        # Trạng thái
        self.phase             = PHASE_TRAVEL
        self.boss              = None
        self.boss_spawned      = False
        self.boss2_spawned     = False
        self._transition_timer = 0.0
        self._camera_locked    = False
        self._player_locked    = False   # True khi cinematic
        self._msg_shown        = False

        # Puzzle
        self._switch_a = None
        self._switch_b = None
        self._boss_door: BossDoor | None = None
        self._puzzle_solved = False

        # Entity list
        self.entities: list = []

        # ── Player ────────────────────────────────────────────────────────────
        self.player = PlayerSprite()
        self.player.position = (100, ENTITY_STAND_Y)
        self.add(self.player, z=10)
        self.entities.append(self.player)

        # ── Nội dung đầu map ──────────────────────────────────────────────────
        self._spawn_starter_content()
        self._spawn_path_content()
        self._setup_puzzle()

        director.window.push_handlers(self.player)
        self.schedule(self.update)

    # ──────────────────────────────────────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────────────────────────────────────
    def _add_entity(self, entity, z=9):
        self.add(entity, z=z)
        self.entities.append(entity)

    @staticmethod
    def _ground_y_for(hitbox_h=60):
        """Pixel Y để entity đứng đúng mặt đất."""
        return GROUND_Y + hitbox_h // 2

    # ──────────────────────────────────────────────────────────────────────────
    #  SPAWN CONTENT
    # ──────────────────────────────────────────────────────────────────────────
    def _spawn_starter_content(self):
        gy = self._ground_y_for(50)
        w = GoblinWarrior(600, gy, walk_range=200)
        self._add_entity(w)
        for ix in [300, 500, 800]:
            self._add_entity(Item(ix, gy + 10, "Coin"), z=8)
        self._add_entity(Block(400, gy + 64, item_type="Invincible"), z=8)
        self._add_entity(Block(450, gy + 64, item_type="Coin"),       z=8)

    def _spawn_path_content(self):
        boss_dist   = self.map_manager.boss_trigger_x
        spawn_start = 800
        step        = 480

        for x in range(spawn_start, int(boss_dist) - 300, step):
            gy = self._ground_y_for(random.choice([50, 65]))
            for _ in range(random.randint(1, 3)):
                ex = x + random.randint(0, step - 80)
                self._add_entity(spawn_enemy(ex, gy, walk_range=160))

            for _ in range(random.randint(2, 4)):
                ix    = x + random.randint(20, step - 20)
                itype = random.choice(["Coin", "Coin", "Coin", "Invincible"])
                self._add_entity(Item(ix, gy + 10, itype), z=8)

            for _ in range(random.randint(1, 2)):
                bx    = x + random.randint(40, step - 40)
                btype = random.choice(["Coin", "Invincible"])
                self._add_entity(Block(bx, gy + 64, item_type=btype), z=8)

    def _setup_puzzle(self):
        """Đặt 2 công tắc và cổng boss từ object layer."""
        objs = self.map_manager.get_objects()
        sa_pos = sb_pos = None
        door_pos = door_h = None

        for obj in objs:
            if obj.name == 'switch_a':
                sa_pos = (obj.x, obj.y)
            elif obj.name == 'switch_b':
                sb_pos = (obj.x, obj.y)
            elif obj.name == 'boss_door':
                door_pos = (obj.x, obj.y)
                door_h   = int(getattr(obj, 'height', 160))

        # Fallback nếu object layer thiếu
        if sa_pos is None:  sa_pos = (840 * 16, GROUND_Y)
        if sb_pos is None:  sb_pos = (860 * 16, GROUND_Y)
        if door_pos is None:
            bx = self.map_manager.boss_trigger_x
            door_pos = (bx, GROUND_Y)
            door_h   = 160

        self._switch_a = SwitchMarker(*sa_pos, switch_id='a')
        self._switch_b = SwitchMarker(*sb_pos, switch_id='b')
        self._boss_door = BossDoor(door_pos[0], GROUND_Y, door_h)

        self.add(self._switch_a, z=8)
        self.add(self._switch_b, z=8)
        self.add(self._boss_door, z=11)

    # ──────────────────────────────────────────────────────────────────────────
    #  BOSS SPAWNING
    # ──────────────────────────────────────────────────────────────────────────
    def _spawn_boss1(self):
        cx = self.map_manager.boss_room_center_x
        gy = self._ground_y_for(90)
        self.boss = BossGoblin(cx, gy)
        self._add_entity(self.boss)
        self.boss_spawned = True
        self.phase        = PHASE_BOSS1
        self.hud.update_boss_hp(self.boss.hp, self.boss.max_hp, self.boss.NAME)
        SoundManager.play_bgm('boss')

    def _spawn_boss2(self):
        cx = self.map_manager.boss_room_center_x + 300
        gy = self._ground_y_for(88)
        self.boss = BossMinotaur(cx, gy)
        self._add_entity(self.boss)
        self.boss2_spawned = True
        self.phase         = PHASE_BOSS2
        self.hud.update_boss_hp(self.boss.hp, self.boss.max_hp, self.boss.NAME)

    # ──────────────────────────────────────────────────────────────────────────
    #  BOSS ROOM ENTRANCE (Megaman style)
    # ──────────────────────────────────────────────────────────────────────────
    def _trigger_boss_entrance(self):
        """Bắt đầu chuỗi cinematic: khóa player, pan camera, khởi boss."""
        if self.phase != PHASE_TRAVEL:
            return
        self.phase          = PHASE_DOOR_LOCK
        self._player_locked = True

        # Dừng player
        self.player.velocity_x = 0
        self.player.velocity_y = 0

        cx = self.map_manager.boss_room_center_x
        # Camera pan action thông qua schedule
        self._pan_target_x  = cx
        self._pan_timer      = 0.0
        self._pan_start_x    = self.player.x
        self.hud.show_transition("⚠  BOSS ROOM AHEAD ⚠")
        SoundManager.play_sfx('boss_enter')

    def _update_boss_entrance(self, dt):
        self._pan_timer += dt
        progress = min(self._pan_timer / CAMERA_PAN_TIME, 1.0)
        focus_x  = self._pan_start_x + (self._pan_target_x - self._pan_start_x) * progress
        if self.parent:
            self.parent.set_focus(focus_x, ENTITY_STAND_Y)

        if progress >= 1.0:
            # Chuỗi hoàn thành: khởi boss
            self.hud.hide_transition()
            self._player_locked = False
            self._spawn_boss1()

    # ──────────────────────────────────────────────────────────────────────────
    #  ITEM SPAWNING
    # ──────────────────────────────────────────────────────────────────────────
    def spawn_item(self, x, y, item_type):
        item = Item(x, y, item_type)
        self.add(item, z=8)
        self.entities.append(item)

    # ──────────────────────────────────────────────────────────────────────────
    #  COLLISIONS
    # ──────────────────────────────────────────────────────────────────────────
    def check_collisions(self):
        player_rect = self.player.get_logical_rect()
        attack_rect = getattr(self.player, 'attack_rect', None)

        for entity in list(self.entities):

            # ── Item pickup ───────────────────────────────────────────────────
            if isinstance(entity, Item) and not entity.is_collected:
                if entity.check_pickup(self.player):
                    if entity.item_type == "Coin":
                        self.items_collected += 1
                        self.hud.update_score(self.items_collected)
                        SoundManager.play_sfx('coin')
                    elif entity.item_type == "Invincible":
                        self.player.is_invincible    = True
                        self.player.invincible_timer = 5.0
                        SoundManager.play_sfx('coin')

            # ── Block break ───────────────────────────────────────────────────
            if isinstance(entity, Block) and not entity.is_broken:
                block_rect = entity.get_logical_rect()
                if attack_rect and attack_rect.intersects(block_rect):
                    drop = entity.break_block()
                    if drop:
                        self.spawn_item(entity.x, entity.y, drop)
                    SoundManager.play_sfx('block_break')
                elif (player_rect.intersects(block_rect)
                      and self.player.velocity_y > 0
                      and player_rect.top >= block_rect.bottom - 10):
                    drop = entity.break_block()
                    if drop:
                        self.spawn_item(entity.x, entity.y + 32, drop)
                        self.player.velocity_y = -100
                    SoundManager.play_sfx('block_break')

            # ── Enemy collision ────────────────────────────────────────────────
            if isinstance(entity, (GoblinWarrior, GoblinGiant)) and not entity.is_dead:
                enemy_rect = entity.get_logical_rect()
                if attack_rect and attack_rect.intersects(enemy_rect) and entity not in self.player.hit_enemies:
                    entity.take_damage(50)
                    self.player.hit_enemies.add(entity)
                    SoundManager.play_sfx('enemy_hit')
                elif player_rect.intersects(enemy_rect):
                    if (player_rect.bottom >= enemy_rect.top - 10
                            and self.player.velocity_y < 0):
                        entity.take_damage(entity.hp)
                        self.player.velocity_y = 300
                        self.items_collected  += entity.coin_drop
                        self.hud.update_score(self.items_collected)
                        SoundManager.play_sfx('enemy_hit')
                    else:
                        dmg = 10 if isinstance(entity, GoblinWarrior) else 20
                        if self.player.take_damage(dmg):
                            self.hud.update_hp(self.player.hp)
                            SoundManager.play_sfx('player_hit')

            # ── Boss collision ─────────────────────────────────────────────────
            if isinstance(entity, (BossGoblin, BossMinotaur)):
                if entity.is_dead:
                    continue
                boss_rect = entity.get_logical_rect()
                if attack_rect and attack_rect.intersects(boss_rect) and entity not in self.player.hit_enemies:
                    entity.take_damage(50)
                    self.player.hit_enemies.add(entity)
                    self.hud.update_boss_hp(entity.hp, entity.max_hp, entity.NAME)
                    SoundManager.play_sfx('boss_hit')
                elif player_rect.intersects(boss_rect):
                    dmg = 25 if isinstance(entity, BossGoblin) else 35
                    if self.player.take_damage(dmg):
                        self.hud.update_hp(self.player.hp)
                        SoundManager.play_sfx('player_hit')

        # ── Puzzle: kiểm tra player đạp switch ───────────────────────────────
        self._check_switches(player_rect)

    def _check_switches(self, player_rect):
        if self._puzzle_solved:
            return
        for sw in (self._switch_a, self._switch_b):
            if sw and not sw.is_activated:
                dist = ((self.player.x - sw.x)**2 + (self.player.y - sw.y)**2)**0.5
                if dist < SWITCH_RADIUS:
                    sw.activate()

        if (self._switch_a and self._switch_a.is_activated
                and self._switch_b and self._switch_b.is_activated):
            self._puzzle_solved = True
            if self._boss_door:
                self._boss_door.open_door()
            self.hud.show_transition("✔ Gate opened!")
            self.do(Sequence(Delay(2.0), CallFunc(self.hud.hide_transition)))

    # ──────────────────────────────────────────────────────────────────────────
    #  MAIN UPDATE
    # ──────────────────────────────────────────────────────────────────────────
    def update(self, dt):
        # Purge dead entities
        self.entities = [
            e for e in self.entities
            if not getattr(e, '_killed', False) or isinstance(e, PlayerSprite)
        ]

        # Cập nhật entity
        for entity in list(self.entities):
            if hasattr(entity, 'is_collected') and entity.is_collected: continue
            if hasattr(entity, 'is_broken')   and entity.is_broken:    continue
            if self._player_locked and isinstance(entity, PlayerSprite):
                continue   # Không di chuyển player khi cinematic
            if isinstance(entity, (BossGoblin, BossMinotaur)):
                entity.update(dt, self.walls_layer, self.player)
            elif isinstance(entity, (GoblinWarrior, GoblinGiant)):
                entity.update(dt, self.walls_layer)
            elif isinstance(entity, PlayerSprite):
                entity.update(dt, self.walls_layer)

        self.check_collisions()

        # ── Phase machine ─────────────────────────────────────────────────────
        boss_dist  = self.map_manager.boss_trigger_x
        curr_dist  = min(self.player.x, boss_dist)
        percentage = (curr_dist / boss_dist * 100) if boss_dist > 0 else 100

        if self.phase == PHASE_TRAVEL:
            self.hud.update_progress(percentage)
            # Kích hoạt entrance khi puzzle đã giải và player chạm trigger
            if percentage >= 100 and self._puzzle_solved:
                self._trigger_boss_entrance()
            elif percentage >= 100 and not self._puzzle_solved:
                self.hud.show_transition("❗ Find and activate both switches first!")
                self.do(Sequence(Delay(2.5), CallFunc(self.hud.hide_transition)))

        elif self.phase == PHASE_DOOR_LOCK:
            self._update_boss_entrance(dt)

        elif self.phase == PHASE_BOSS1:
            if self.boss and self.boss.is_dead:
                self.phase             = PHASE_TRANSITION
                self._transition_timer = 0.0
                self._msg_shown        = False
                self.hud.boss_defeated(BossGoblin.NAME)
                self.hud.show_transition("► GOBLIN KING defeated! The Minotaur is coming... ◄")
                SoundManager.play_bgm('main')

        elif self.phase == PHASE_TRANSITION:
            self._transition_timer += dt
            if not self._msg_shown and self._transition_timer >= TRANSITION_DURATION:
                self.hud.hide_transition()
                self.hud.show_transition("⏳ Prepare yourself... Minotaur incoming!")
                self._msg_shown = True
            if not self.boss2_spawned and self._transition_timer >= MINOTAUR_SPAWN_DELAY:
                self.hud.hide_transition()
                self._spawn_boss2()

        elif self.phase == PHASE_BOSS2:
            if self.boss and self.boss.is_dead:
                self.phase = PHASE_VICTORY
                self.hud.boss_defeated(BossMinotaur.NAME)
                self.hud.show_transition("✦ YOU WIN! All Bosses Defeated! ✦")
                SoundManager.stop_bgm()
                SoundManager.play_sfx('victory')

        # ── Camera ────────────────────────────────────────────────────────────
        if self.parent and self.phase not in (PHASE_DOOR_LOCK,):
            if self.phase in (PHASE_BOSS1, PHASE_BOSS2):
                self.parent.set_focus(self.map_manager.boss_room_center_x, ENTITY_STAND_Y)
                if self.player.x < self.map_manager.boss_room_left_limit:
                    self.player.x = self.map_manager.boss_room_left_limit
            else:
                self.parent.set_focus(self.player.x, self.player.y)

    # ──────────────────────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        if self._player_locked:
            return True   # Chặn input khi cinematic


# ── Entry point ───────────────────────────────────────────────────────────────

def create_game_scene():
    hud_layer = HUD()
    map_mgr   = GameMapManager("assets/map.tmx")
    scroller  = map_mgr.get_scrolling_manager()

    game_layer = GameLayer(map_mgr, hud_layer)
    scroller.add(game_layer, z=5)

    scene = Scene()
    scene.add(scroller,  z=0)
    scene.add(hud_layer, z=10)
    
    return scene

def main():
    SoundManager.init()
    director.init(width=800, height=600, caption="Hope – Goblin Kingdom")

    scene = create_game_scene()
    SoundManager.play_bgm('main')
    director.replace(scene)


if __name__ == '__main__':
    from cocos.director import director
    director.init(width=800, height=600, caption="Hope – Goblin Kingdom")
    SoundManager.init()

    from menu import create_menu_scene
    director.run(create_menu_scene())