import cocos
import random
from cocos.scene import Scene
from cocos.layer import ScrollableLayer
from cocos.director import director

from maps.map import GameMapManager
from entities.player import PlayerSprite
from entities.enemy import GoblinWarrior, GoblinGiant, spawn_enemy
from entities.item import Item
from entities.block import Block
from entities.boss import BossGoblin, BossMinotaur, Boss
from ui import HUD

# ── Progression constants ─────────────────────────────────────────────────────
# States for the boss phase machine
PHASE_TRAVEL      = "travel"      # Player tiến về cuối map
PHASE_BOSS1       = "boss1"       # Đánh Boss Goblin
PHASE_TRANSITION  = "transition"  # Animation chuyển sang boss 2
PHASE_BOSS2       = "boss2"       # Đánh Boss Minotaur
PHASE_VICTORY     = "victory"     # Game cleared

TRANSITION_DURATION  = 3.0   # Thời gian hiển thị thông điệp chuyển màn
MINOTAUR_SPAWN_DELAY = 4.0   # Sau bao lâu kể từ khi Goblin Boss chết thì spawn Minotaur


class GameLayer(ScrollableLayer):
    is_event_handler = True

    # ──────────────────────────────────────────────────────────────────────────
    def __init__(self, map_manager, hud):
        super(GameLayer, self).__init__()

        self.map_manager  = map_manager
        self.walls_layer  = map_manager.get_walls_layer()
        self.hud          = hud
        self.items_collected = 0

        # Camera flag
        self.is_boss_room = False

        # Entity list
        self.entities: list = []

        # ── Player ────────────────────────────────────────────────────────────
        self.player = PlayerSprite()
        self.player.position = (42 * 16, 50 * 16)
        self.add(self.player, z=10)
        self.entities.append(self.player)

        # ── Static starter enemies / items / blocks (beginning of map) ───────
        self._spawn_starter_content()

        # ── Procedural content along the path (800 … boss_trigger_x - 400) ──
        self._spawn_path_content()

        # ── Boss management ───────────────────────────────────────────────────
        self.boss          = None    # active boss entity
        self.boss_spawned  = False
        self.boss2_spawned = False
        self.phase         = PHASE_TRAVEL
        self._transition_timer = 0.0

        # ── Register handlers ─────────────────────────────────────────────────
        director.window.push_handlers(self.player)
        self.schedule(self.update)

    # ──────────────────────────────────────────────────────────────────────────
    def _add_entity(self, entity, z=9):
        self.add(entity, z=z)
        self.entities.append(entity)

    def _spawn_starter_content(self):
        """Fixed enemies/items/blocks near start."""
        # One warrior on starter platform area
        w = GoblinWarrior(600, 300, walk_range=250)
        self._add_entity(w)

        # Starting coins for player to collect
        for item_x in [300, 500, 800]:
            self._add_entity(Item(item_x, 300, "Coin"), z=8)

        # Tutorial blocks
        self._add_entity(Block(400, 420, item_type="Invincible"), z=8)
        self._add_entity(Block(450, 420, item_type="Coin"), z=8)

    def _spawn_path_content(self):
        """Procedurally populate the entire path up to the boss room."""
        boss_dist   = self.map_manager.boss_trigger_x
        spawn_start = 800
        step        = 500  # Increased spacing for better pacing

        for x in range(spawn_start, int(boss_dist) - 400, step):
            # 2-4 enemies at staggered sub-positions for variety
            num_enemies = random.randint(2, 4)
            for _ in range(num_enemies):
                ex = x + random.randint(0, step - 100)
                self._add_entity(spawn_enemy(ex, 300, walk_range=200))

            # 3-5 coins + occasional Invincible
            num_items = random.randint(3, 5)
            for _ in range(num_items):
                ix = x + random.randint(30, step - 30)
                itype = random.choice(["Coin", "Coin", "Coin", "Coin", "Invincible"])
                self._add_entity(Item(ix, 300, itype), z=8)

            # 1-3 breakable blocks
            num_blocks = random.randint(1, 3)
            for _ in range(num_blocks):
                bx = x + random.randint(50, step - 50)
                btype = random.choice(["Coin", "Coin", "Invincible"])
                self._add_entity(Block(bx, 420, item_type=btype), z=8)

    # ──────────────────────────────────────────────────────────────────────────
    def spawn_item(self, x, y, item_type):
        item = Item(x, y, item_type)
        self.add(item, z=8)
        self.entities.append(item)

    # ──────────────────────────────────────────────────────────────────────────
    def _spawn_boss1(self):
        cx = self.map_manager.boss_room_center_x
        self.boss = BossGoblin(cx, 300)
        self._add_entity(self.boss)
        self.boss_spawned  = True
        self.phase         = PHASE_BOSS1
        self.hud.update_boss_hp(self.boss.hp, self.boss.max_hp, self.boss.NAME)

    def _spawn_boss2(self):
        # Minotaur xuất hiện ngay tại trung tâm boss room (cùng phòng nhưng boss mới)
        cx = self.map_manager.boss_room_center_x + 300
        self.boss = BossMinotaur(cx, 300)
        self._add_entity(self.boss)
        self.boss2_spawned = True
        self.phase         = PHASE_BOSS2
        self.hud.update_boss_hp(self.boss.hp, self.boss.max_hp, self.boss.NAME)

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
        # ── Purge fully killed entities ────────────────────────────────────────
        self.entities = [
            e for e in self.entities
            if not getattr(e, '_killed', False) or isinstance(e, PlayerSprite)
        ]

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


        # ── Progress bar ───────────────────────────────────────────────────────
        boss_dist   = self.map_manager.boss_trigger_x
        curr_dist   = min(self.player.x, boss_dist)
        percentage  = (curr_dist / boss_dist * 100) if boss_dist > 0 else 100

        if self.phase == PHASE_TRAVEL:
            self.hud.update_progress(percentage)

        # ── Phase machine ──────────────────────────────────────────────────────

        # Travel → spawn Boss 1
        if self.phase == PHASE_TRAVEL and percentage >= 100:
            self._spawn_boss1()

        # Boss 1 → transition
        elif self.phase == PHASE_BOSS1:
            if self.boss and self.boss.is_dead:
                self.phase = PHASE_TRANSITION
                self._transition_timer = 0.0
                self.hud.boss_defeated(BossGoblin.NAME)
                self.hud.show_transition(
                    "► GOBLIN KING defeated! The Minotaur is coming... ◄"
                )

        # Transition: đếm thời gian → tự động spawn Minotaur
        elif self.phase == PHASE_TRANSITION:
            self._transition_timer += dt
            if self._transition_timer >= TRANSITION_DURATION:
                self.hud.hide_transition()
                self.hud.show_transition("⏳ Prepare yourself... Minotaur incoming!")
            if not self.boss2_spawned and self._transition_timer >= MINOTAUR_SPAWN_DELAY:
                self.hud.hide_transition()
                self._spawn_boss2()

        # Boss 2 → victory
        elif self.phase == PHASE_BOSS2:
            if self.boss and self.boss.is_dead:
                self.phase = PHASE_VICTORY
                self.hud.boss_defeated(BossMinotaur.NAME)
                self.hud.show_transition("✦ YOU WIN! All Bosses Defeated! ✦")

        # ── Camera ────────────────────────────────────────────────────────────
        if self.parent:
            if self.phase in (PHASE_BOSS1, PHASE_BOSS2):
                # Camera khóa vào trung tâm boss room
                self.parent.set_focus(self.map_manager.boss_room_center_x, 300)
                # Soft wall: ngăn player lui
                if self.player.x < self.map_manager.boss_room_left_limit:
                    self.player.x = self.map_manager.boss_room_left_limit
            else:
                # Mario-style follow trong travel và transition
                self.parent.set_focus(self.player.x, self.player.y)


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    director.init(width=800, height=600, caption="Hope – Goblin King & Minotaur")

    hud_layer = HUD()
    map_mgr   = GameMapManager("assets/map21.tmx")
    scroller  = map_mgr.get_scrolling_manager()

    game_layer = GameLayer(map_mgr, hud_layer)
    scroller.add(game_layer, z=5)

    scene = Scene()
    scene.add(scroller,   z=0)
    scene.add(hud_layer, z=10)

    director.run(scene)


if __name__ == '__main__':
    main()