import random
import math
import pyglet

from cocos.scene import Scene

from cocos.layer import ScrollableLayer

from cocos.director import director



from maps.map import GameMapManager

from entities.player import PlayerSprite

from entities.enemy import GoblinWarrior, GoblinGiant, spawn_enemy

from entities.item import Item

from entities.block import Block

from entities.boss import BossGoblin, BossMinotaur

from ui import HUD



# ── Progression constants ───────────────────────────────────────────────────

PHASE_TRAVEL      = "travel"

PHASE_SWITCH_MAP  = "switch_map"

PHASE_BOSS1       = "boss1"

PHASE_TRANSITION  = "transition"

PHASE_BOSS2       = "boss2"

PHASE_VICTORY     = "victory"



TRANSITION_DURATION  = 3.0

MINOTAUR_SPAWN_DELAY = 4.0

MAP_SWITCH_DELAY     = 1.9

FALL_DEATH_Y         = -180



TRAVEL_MAP_PATH = "assets/map21.tmx"

BOSS_MAP_PATH = "assets/map.tmx"


# ── Map21 spawn zones — phân tích từ objectgroup "Landable" trong map21.tmx ──
# Map: 160×64 tiles × 16px = 2560 × 1024 px.
# Cocos2d dùng hệ y đáy lên (bottom-up):  cocos_y = 1024 − tmx_y_surface
#
# Objectgroup "Landable" (các đoạn mặt đất thực):
#  obj2 : tmx x=239,  tmx_y=431→524  → cocos_y_top ≈ 500   (sàn 1, x=239–845)
#  obj7 : tmx x=880,  tmx_y=400→527  → cocos_y_top ≈ 497   (sàn 1 nối tiếp, x=845–977)
#  obj10: tmx x=658,  tmx_y=175→192  → cocos_y_top ≈ 832   (TẦNG 2, platform x=658–864)
#  obj11: tmx x=912,  tmx_y=241→256  → cocos_y_top ≈ 768   (TẦNG 2, platform x=816–1008)
#  obj12: tmx x=1040, tmx_y=303→320  → cocos_y_top ≈ 704   (nền bậc x=1040–1248)
#  obj13: tmx x=1296, tmx_y=240→256  → cocos_y_top ≈ 768   (TẦNG 2, platform x=1296–1392)
#  obj14: tmx x=1424, tmx_y=160→176  → cocos_y_top ≈ 848   (TẦNG 2, platform x=1424–1488)
#  obj15: tmx x=1552, tmx_y=160→176  → cocos_y_top ≈ 848   (TẦNG 2, platform x=1552–1616)
#  obj16: tmx x=1696, tmx_y=160→176  → cocos_y_top ≈ 848   (TẦNG 2, platform x=1696–1760)
#  obj18: tmx x=976,  tmx_y=400→544  → cocos_y_top ≈ 480   (sàn 1 slope, x=976–1904)
#  obj21: tmx x=1904, tmx_y=448→592  → cocos_y_top ≈ 432   (tường/bậc cuối sàn 1)
#
# Mỗi entry: (x_min, x_max, cocos_y_spawn, "floor1"|"floor2")
# y_spawn = cocos_y_top + 8 (đứng ngay trên bề mặt)

SPAWN_ZONES = [
    # ── TẦNG 1 (sàn chính, thấp) ──────────────────────────────────────────────
    # obj2: x=239–845, cocos_y≈500
    (280,  650,  508,  "floor1"),   # Sàn chính trái, rộng
    (650,  845,  508,  "floor1"),   # Sàn chính giữa trái
    # obj7+18: x=845–977 nối sàn, cocos_y≈497
    (870,  975,  505,  "floor1"),   # Khu giữa nối tiếp
    # obj18 slope x=976–1904, cocos_y≈480
    (980,  1300, 488,  "floor1"),   # Sàn 1 khu giữa phải
    (1300, 1620, 488,  "floor1"),   # Sàn 1 khu xa
    (1620, 1900, 488,  "floor1"),   # Sàn 1 trước bậc cuối

    # ── TẦNG 2 (platforms cao) ─────────────────────────────────────────────────
    # Hạ thấp y_ground khoảng 60-80px để item không bị bay lơ lửng quá cao
    (660,  860,  770,  "floor2"),   # Platform cao khu đầu
    (820,  1005, 710,  "floor2"),   # Platform trung gian
    (1300, 1390, 710,  "floor2"),   # Platform nhỏ phải
    (1428, 1615, 780,  "floor2"),   # Các platform cao liên tiếp
    (1616, 1758, 780,  "floor2"),   # Platform cao cuối
]


class GameLayer(ScrollableLayer):

    is_event_handler = True



    def __init__(self, map_manager, hud, mode="travel", player_hp=100, start_score=0):

        super(GameLayer, self).__init__()



        self.map_manager  = map_manager

        self.walls_layer  = map_manager.get_walls_layer()

        self.hud          = hud

        self.mode = mode

        self.items_collected = start_score

        self.hud.update_score(self.items_collected)



        self.entities: list = []



        self.player = PlayerSprite(hp=player_hp)

        if mode == "travel":
            self.player.position = (42 * 16, 50 * 16)
        else:
            # Spawn player near Boss Goblin
            boss_x = int(map_manager.get_map_pixel_width() * 0.60)
            self.player.position = (boss_x - 300, 500)

        self.add(self.player, z=10)

        self.entities.append(self.player)

        self.hud.update_hp(self.player.hp)



        self.boss          = None

        self.boss_spawned  = False

        self.boss2_spawned = False

        self.phase         = PHASE_TRAVEL if mode == "travel" else PHASE_BOSS1

        self._transition_timer = 0.0

        self._map_switch_timer = 0.0

        self.game_over = False

        # Cooldown chống double-damage từ enemy attack
        self._enemy_attack_cooldown = 0.0



        self.hud.hide_endgame()

        self.hud.hide_transition()



        if self.mode == "travel":

            self._spawn_map_content()

        else:

            self.hud.play_screen_transition("⚔ BOSS MAP ⚔", duration=1.8, peak_alpha=190)

            self._spawn_boss1()



        director.window.push_handlers(self.player)

        self.schedule(self.update)



    def _add_entity(self, entity, z=9):

        self.add(entity, z=z)

        self.entities.append(entity)



    # ── Spawn dựa theo vùng map thực tế ─────────────────────────────────────

    def _spawn_map_content(self):
        """Spawn enemy, item, block theo từng vùng ground thực tế của map21.
        SPAWN_ZONES chứa cả tầng 1 (floor1) lẫn tầng 2 (floor2).
        """
        boss_x = self.map_manager.boss_trigger_x

        for zone_idx, (zx_min, zx_max, y_ground, floor_tag) in enumerate(SPAWN_ZONES):
            # Bỏ qua vùng vượt quá boss trigger
            if zx_min >= boss_x:
                continue

            zx_max = min(zx_max, int(boss_x) - 100)
            if zx_max <= zx_min + 40:
                continue

            zone_width = zx_max - zx_min
            # Platform nhỏ (floor2) spawn ít hơn
            is_platform = (floor_tag == "floor2")

            # ── Enemy ──────────────────────────────────────────────────────
            num_enemies = random.randint(1, 2) if is_platform else random.randint(2, 4)
            for _ in range(num_enemies):
                ex = random.randint(zx_min + 30, zx_max - 30)
                wr = min(150 if is_platform else 200, zone_width // 2)
                self._add_entity(spawn_enemy(ex, y_ground, walk_range=wr))

            # ── Coin ───────────────────────────────────────────────────────
            min_c = 1 if is_platform else 2
            max_c = min(3 if is_platform else 5, max(min_c, (zone_width - 40) // 40))
            num_coins = random.randint(min_c, max_c)
            if zone_width > 80:
                coin_xs = sorted(random.sample(
                    range(zx_min + 20, zx_max - 20, 1),
                    min(num_coins, zone_width // 40)
                ))
                for cx in coin_xs:
                    self._add_entity(Item(cx, y_ground + 28, "Coin"), z=8)

            # ── Star (tỉ lệ 25% mỗi vùng) ─────────────────────────────────
            if random.random() < 0.25:
                sx = random.randint(zx_min + 30, max(zx_min + 31, zx_max - 30))
                self._add_entity(Item(sx, y_ground + 50, "Star"), z=8)

            # ── Invincible (15% mỗi vùng) ─────────────────────────────────
            if random.random() < 0.15:
                ix = random.randint(zx_min + 25, max(zx_min + 26, zx_max - 25))
                self._add_entity(Item(ix, y_ground + 28, "Invincible"), z=8)

            # ── Block (thùng trên platform cao hơn mặt đất 80px) ──────────
            num_blocks = random.randint(1, 2) if is_platform else random.randint(1, 3)
            for _ in range(num_blocks):
                bx = random.randint(zx_min + 20, max(zx_min + 21, zx_max - 20))
                by = y_ground + 80   # Đặt block nổi trên sàn
                btype = random.choice(["Coin", "Coin", "Coin", "Star", "Invincible"])
                self._add_entity(Block(bx, by, item_type=btype), z=8)

    # ── Legacy spawn (dùng khi không có zone data) ───────────────────────────

    def _spawn_starter_content(self):

        w = GoblinWarrior(600, 720, walk_range=250)

        self._add_entity(w)



        for item_x in [300, 500, 800]:

            self._add_entity(Item(item_x, 750, "Coin"), z=8)



        self._add_entity(Block(400, 800, item_type="Invincible"), z=8)

        self._add_entity(Block(450, 800, item_type="Star"), z=8)



    def _spawn_path_content(self):

        boss_dist = self.map_manager.boss_trigger_x

        spawn_start = 700

        spawn_end = max(int(boss_dist) - 250, 1800)

        step = 320



        for x in range(spawn_start, spawn_end, step):

            num_enemies = random.randint(2, 4)

            for _ in range(num_enemies):

                ex = x + random.randint(0, step - 100)

                self._add_entity(spawn_enemy(ex, 720, walk_range=200))



            num_items = random.randint(3, 5)

            for _ in range(num_items):

                ix = x + random.randint(30, step - 30)

                itype = random.choice(["Coin", "Coin", "Coin", "Star", "Invincible"])

                self._add_entity(Item(ix, 750, itype), z=8)



            num_blocks = random.randint(1, 3)

            for _ in range(num_blocks):

                bx = x + random.randint(50, step - 50)

                btype = random.choice(["Coin", "Coin", "Star", "Invincible"])

                self._add_entity(Block(bx, 820, item_type=btype), z=8)



    def _transition_to_boss_map(self):

        hp = max(1, self.player.hp)

        director.replace(build_game_scene(BOSS_MAP_PATH, mode="boss", player_hp=hp, score=self.items_collected))



    # ──────────────────────────────────────────────────────────────────────────

    def spawn_item(self, x, y, item_type):

        item = Item(x, y, item_type)

        self.add(item, z=8)

        self.entities.append(item)



    # ──────────────────────────────────────────────────────────────────────────

    def _spawn_boss1(self):
        cx = int(self.map_manager.get_map_pixel_width() * 0.60)
        self.boss = BossGoblin(cx, 500)
        self._add_entity(self.boss)
        self.boss_spawned  = True
        self.phase         = PHASE_BOSS1
        self.hud.update_boss_hp(self.boss.hp, self.boss.max_hp, self.boss.NAME)
        self.hud.play_screen_transition("⚔ BOSS FIGHT: GOBLIN KING ⚔", duration=2.0)


    def _spawn_boss2(self):
        cx = int(self.map_manager.get_map_pixel_width() * 0.76)
        self.boss = BossMinotaur(cx, 500)
        self._add_entity(self.boss)

        self.boss2_spawned = True

        self.phase         = PHASE_BOSS2



        self.player.x = max(280, cx - 300)

        self.player.y = max(self.player.y, 300)

        self.player.velocity_x = 0

        self.player.velocity_y = 0



        self.hud.update_boss_hp(self.boss.hp, self.boss.max_hp, self.boss.NAME)

        self.hud.play_screen_transition("☠ FINAL BOSS: MINOTAUR ☠", duration=2.2, peak_alpha=190)



    def _set_player_input_locked(self, locked):

        self.player.set_input_locked(locked)



    def _trigger_game_over(self, reason):

        if self.game_over:

            return

        self.game_over = True

        self._set_player_input_locked(True)

        self.hud.show_endgame("END GAME", reason, on_restart=self.restart_game)



    def restart_game(self):

        director.replace(build_game_scene())



    # ──────────────────────────────────────────────────────────────────────────

    def check_collisions(self):

        player_rect = self.player.get_logical_rect()

        attack_rect = getattr(self.player, 'attack_rect', None)

        # Kiểm tra player có đang dash hay không
        is_dashing = (self.player.current_state == "Dash" and
                      getattr(self.player, 'is_attacking', False))

        if self._enemy_attack_cooldown > 0:
            self._enemy_attack_cooldown -= 0  # sẽ trừ trong update

        for entity in self.entities:



            # ── Item pickup ───────────────────────────────────────────────────

            if isinstance(entity, Item) and not entity.is_collected:

                if entity.check_pickup(self.player):

                    if entity.item_type == "Coin":

                        self.items_collected += 1

                        self.hud.update_score(self.items_collected)

                    elif entity.item_type == "Star":
                        # Star: +1 điểm + buff tốc độ ngắn hạn
                        self.items_collected += 1
                        self.hud.update_score(self.items_collected)
                        # Buff tốc độ 4 giây
                        self.player.move_speed = int(self.player.move_speed * 1.4)
                        pyglet.clock.unschedule(self._reset_speed)
                        pyglet.clock.schedule_once(self._reset_speed, 4.0)

                    elif entity.item_type == "Invincible":

                        self.player.is_invincible   = True

                        self.player.invincible_timer = 5.0



            # ── Block break ───────────────────────────────────────────────────

            if isinstance(entity, Block) and not entity.is_broken:

                block_rect = entity.get_logical_rect()

                broke = False

                if attack_rect and attack_rect.intersects(block_rect):
                    # Đánh kiếm vỡ block
                    broke = True

                elif (player_rect.intersects(block_rect)
                      and self.player.velocity_y > 0
                      and player_rect.top >= block_rect.bottom - 10):
                    # Nhảy đập đầu từ phía dưới
                    broke = True
                    self.player.velocity_y = -100

                elif (is_dashing and player_rect.intersects(block_rect)):
                    # Dash phá block
                    broke = True

                if broke:
                    drop = entity.break_block()
                    if drop:
                        self.spawn_item(entity.x, entity.y + 32, drop)
                    # Phá block luôn +1 điểm
                    self.items_collected += 1
                    self.hud.update_score(self.items_collected)



            # ── Enemy collision ────────────────────────────────────────────

            if isinstance(entity, (GoblinWarrior, GoblinGiant)) and not entity.is_dead:

                enemy_rect = entity.get_logical_rect()



                # Kiếm chém
                if attack_rect and attack_rect.intersects(enemy_rect):

                    damage = random.randint(10, 20)

                    entity.take_damage(damage)

                    if entity.is_dead:
                        self.items_collected += entity.coin_drop
                        self.hud.update_score(self.items_collected)

                # Dash đâm vào địch → giết ngay
                elif is_dashing and player_rect.intersects(enemy_rect):
                    entity.take_damage(entity.hp)   # instant kill
                    if entity.is_dead:
                        self.items_collected += entity.coin_drop
                        self.hud.update_score(self.items_collected)
                    self.player.velocity_y = 100    # nảy nhẹ

                elif player_rect.intersects(enemy_rect):

                    # ── Giẫm đầu ──────────────────────────────────────────
                    if (player_rect.bottom >= enemy_rect.top - 12
                            and self.player.velocity_y < 0):

                        entity.take_damage(entity.hp)  # instant kill
                        self.player.velocity_y = 320   # nảy lên
                        if entity.is_dead:
                            self.items_collected += entity.coin_drop
                            self.hud.update_score(self.items_collected)

                    else:
                        # ── Bị chạm: enemy attack gây damage ──────────────
                        # Chỉ gây damage khi enemy đang trong frame tấn công
                        # hoặc chạm thường (cooldown chia đều)
                        if self._enemy_attack_cooldown <= 0:
                            dmg = 15 if isinstance(entity, GoblinWarrior) else 25
                            if self.player.take_damage(dmg):
                                self.hud.update_hp(self.player.hp)
                                self._enemy_attack_cooldown = 1.0



            # ── Boss collision ─────────────────────────────────────────────────

            if isinstance(entity, (BossGoblin, BossMinotaur)):

                if entity.is_dead:

                    continue

                boss_rect = entity.get_logical_rect()



                if attack_rect and attack_rect.intersects(boss_rect):

                    entity.take_damage(50)

                    self.hud.update_boss_hp(entity.hp, entity.max_hp, entity.NAME)



                elif player_rect.intersects(boss_rect):

                    dmg = 25 if isinstance(entity, BossGoblin) else 35

                    if self.player.take_damage(dmg):

                        self.hud.update_hp(self.player.hp)

    def _reset_speed(self, dt=0):
        """Callback: reset tốc độ player sau khi buff Star hết hạn."""
        from entities.entity import Entity as E_
        self.player.move_speed = 200  # giá trị mặc định trong Entity

    # ──────────────────────────────────────────────────────────────────────────

    def update(self, dt):

        if self.game_over:

            return



        # ── Purge fully killed entities ────────────────────────────────────────

        self.entities = [

            e for e in self.entities

            if not getattr(e, '_killed', False) or isinstance(e, PlayerSprite)

        ]



        transition_lock = self.hud.is_transition_playing() or self.phase in (PHASE_TRANSITION, PHASE_SWITCH_MAP)

        self._set_player_input_locked(transition_lock)

        # Giảm cooldown tiếp xúc enemy
        if self._enemy_attack_cooldown > 0:
            self._enemy_attack_cooldown = max(0.0, self._enemy_attack_cooldown - dt)



        # ── Entity update ──────────────────────────────────────────────────────

        for entity in list(self.entities):

            if hasattr(entity, 'is_collected') and entity.is_collected: continue

            if hasattr(entity, 'is_broken')   and entity.is_broken:    continue

            if isinstance(entity, (BossGoblin, BossMinotaur)):

                entity.update(dt, self.walls_layer, self.player)

            elif isinstance(entity, (GoblinWarrior, GoblinGiant)):
                # Truyền player để enemy có thể tấn công
                entity.update(dt, self.walls_layer, self.player)

            elif isinstance(entity, Item):
                # Bob animation
                entity.update(dt)

            elif isinstance(entity, PlayerSprite):

                entity.update(dt, self.walls_layer)



        self.check_collisions()



        # ── Endgame conditions ─────────────────────────────────────────────────

        if self.player.hp <= 0:

            self.hud.update_hp(0)

            self._trigger_game_over("Ban da het mau.")

            return

        if self.player.y <= FALL_DEATH_Y:

            self._trigger_game_over("Ban da roi khoi map.")

            return



        if self.mode == "travel":

            boss_dist = self.map_manager.boss_trigger_x

            curr_dist = min(self.player.x, boss_dist)

            percentage = (curr_dist / boss_dist * 100) if boss_dist > 0 else 100

            self.hud.update_progress(percentage)



            if self.phase == PHASE_TRAVEL and percentage >= 100:

                self.phase = PHASE_SWITCH_MAP

                self._map_switch_timer = 0.0

                self.hud.play_screen_transition("► ENTERING BOSS MAP ◄", duration=2.1, peak_alpha=210)



            elif self.phase == PHASE_SWITCH_MAP:

                self._map_switch_timer += dt

                if self._map_switch_timer >= MAP_SWITCH_DELAY:

                    self._transition_to_boss_map()

                    return

        else:

            if self.phase == PHASE_BOSS1:

                if self.boss and self.boss.is_dead:

                    self.phase = PHASE_TRANSITION

                    self._transition_timer = 0.0

                    self.hud.boss_defeated(BossGoblin.NAME)

                    self.hud.play_screen_transition(

                        "► GOBLIN KING defeated! The Minotaur is coming... ◄",

                        duration=2.4,

                        peak_alpha=185

                    )



            elif self.phase == PHASE_TRANSITION:

                self._transition_timer += dt

                if (self._transition_timer >= TRANSITION_DURATION

                        and self._transition_timer < TRANSITION_DURATION + dt):

                    self.hud.play_screen_transition(

                        "⏳ Prepare yourself... Minotaur incoming!",

                        duration=1.8,

                        peak_alpha=170

                    )

                if not self.boss2_spawned and self._transition_timer >= MINOTAUR_SPAWN_DELAY:

                    self._spawn_boss2()



            elif self.phase == PHASE_BOSS2:

                if self.boss and self.boss.is_dead:

                    self.phase = PHASE_VICTORY

                    self.hud.boss_defeated(BossMinotaur.NAME)

                    self.hud.play_screen_transition(

                        "✦ YOU WIN! All Bosses Defeated! ✦",

                        duration=3.0,

                        peak_alpha=210

                    )



        if self.parent:

            if self.mode == "boss":

                focus_x = self.boss.x if self.boss else self.player.x

                self.parent.set_focus(focus_x, 320)

            else:

                self.parent.set_focus(self.player.x, self.player.y)




# ── Entry point ──────────────────────────────────────────────────────────────



def build_game_scene(map_path=TRAVEL_MAP_PATH, mode="travel", player_hp=100, score=0):

    hud_layer = HUD()

    map_mgr   = GameMapManager(map_path)

    scroller  = map_mgr.get_scrolling_manager()



    game_layer = GameLayer(map_mgr, hud_layer, mode=mode, player_hp=player_hp, start_score=score)

    scroller.add(game_layer, z=5)



    scene = Scene()

    scene.add(scroller,   z=0)

    scene.add(hud_layer, z=10)



    return scene




def main():

    director.init(width=800, height=600, caption="Hope – Goblin King & Minotaur")



    director.run(build_game_scene())




if __name__ == '__main__':

    main()