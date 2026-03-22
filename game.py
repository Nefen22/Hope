import random
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
        self.player.position = (42 * 16, 50 * 16) if mode == "travel" else (20 * 16, 30 * 16)
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

        self.hud.hide_endgame()
        self.hud.hide_transition()

        if self.mode == "travel":
            self._spawn_starter_content()
            self._spawn_path_content()
        else:
            self.hud.play_screen_transition("⚔ BOSS MAP ⚔", duration=1.8, peak_alpha=190)
            self._spawn_boss1()

        director.window.push_handlers(self.player)
        self.schedule(self.update)

    def _add_entity(self, entity, z=9):
        self.add(entity, z=z)
        self.entities.append(entity)

    def _spawn_starter_content(self):
        w = GoblinWarrior(600, 300, walk_range=250)
        self._add_entity(w)

        for item_x in [300, 500, 800]:
            self._add_entity(Item(item_x, 300, "Coin"), z=8)

        self._add_entity(Block(400, 420, item_type="Invincible"), z=8)
        self._add_entity(Block(450, 420, item_type="Coin"), z=8)

    def _spawn_path_content(self):
        boss_dist = self.map_manager.boss_trigger_x
        spawn_start = 700
        spawn_end = max(int(boss_dist) - 250, 1800)
        step = 320

        for x in range(spawn_start, spawn_end, step):
            num_enemies = random.randint(2, 4)
            for _ in range(num_enemies):
                ex = x + random.randint(0, step - 100)
                self._add_entity(spawn_enemy(ex, 300, walk_range=200))

            num_items = random.randint(3, 5)
            for _ in range(num_items):
                ix = x + random.randint(30, step - 30)
                itype = random.choice(["Coin", "Coin", "Coin", "Coin", "Invincible"])
                self._add_entity(Item(ix, 300, itype), z=8)

            num_blocks = random.randint(1, 3)
            for _ in range(num_blocks):
                bx = x + random.randint(50, step - 50)
                btype = random.choice(["Coin", "Coin", "Invincible"])
                self._add_entity(Block(bx, 420, item_type=btype), z=8)

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
        self.boss = BossGoblin(cx, 300)
        self._add_entity(self.boss)
        self.boss_spawned  = True
        self.phase         = PHASE_BOSS1
        self.hud.update_boss_hp(self.boss.hp, self.boss.max_hp, self.boss.NAME)
        self.hud.play_screen_transition("⚔ BOSS FIGHT: GOBLIN KING ⚔", duration=2.0)

    def _spawn_boss2(self):
        cx = int(self.map_manager.get_map_pixel_width() * 0.76)
        self.boss = BossMinotaur(cx, 300)
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

        for entity in self.entities:

            # ── Item pickup ───────────────────────────────────────────────────
            if isinstance(entity, Item) and not entity.is_collected:
                if entity.check_pickup(self.player):
                    if entity.item_type == "Coin":
                        self.items_collected += 1
                        self.hud.update_score(self.items_collected)
                    elif entity.item_type == "Invincible":
                        self.player.is_invincible   = True
                        self.player.invincible_timer = 5.0

            # ── Block break ───────────────────────────────────────────────────
            if isinstance(entity, Block) and not entity.is_broken:
                block_rect = entity.get_logical_rect()
                if attack_rect and attack_rect.intersects(block_rect):
                    drop = entity.break_block()
                    if drop:
                        self.spawn_item(entity.x, entity.y, drop)
                elif (player_rect.intersects(block_rect)
                      and self.player.velocity_y > 0
                      and player_rect.top >= block_rect.bottom - 10):
                    drop = entity.break_block()
                    if drop:
                        self.spawn_item(entity.x, entity.y + 32, drop)
                        self.player.velocity_y = -100

            # ── Enemy collision ────────────────────────────────────────────
            if isinstance(entity, (GoblinWarrior, GoblinGiant)) and not entity.is_dead:
                enemy_rect = entity.get_logical_rect()

                if attack_rect and attack_rect.intersects(enemy_rect):
                    # Random damage 10-20 per sword hit
                    damage = random.randint(10, 20)
                    entity.take_damage(damage)

                elif player_rect.intersects(enemy_rect):
                    # Stomp mechanic - jumping on enemy's head
                    if (player_rect.bottom >= enemy_rect.top - 10
                            and self.player.velocity_y < 0):
                        entity.take_damage(entity.hp)  # instant kill on head-stomp
                        self.player.velocity_y = 300   # bounce player up
                        self.items_collected += entity.coin_drop
                        self.hud.update_score(self.items_collected)
                    else:
                        # Touch damage from enemies
                        dmg = 15 if isinstance(entity, GoblinWarrior) else 25  # Balanced damage
                        if self.player.take_damage(dmg):
                            self.hud.update_hp(self.player.hp)

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

        # ── Entity update ──────────────────────────────────────────────────────
        for entity in list(self.entities):
            if hasattr(entity, 'is_collected') and entity.is_collected: continue
            if hasattr(entity, 'is_broken')   and entity.is_broken:    continue
            if isinstance(entity, (BossGoblin, BossMinotaur)):
                entity.update(dt, self.walls_layer, self.player)
            elif isinstance(entity, (GoblinWarrior, GoblinGiant)):
                entity.update(dt, self.walls_layer)
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