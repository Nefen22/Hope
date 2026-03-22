import cocos
from cocos.text import Label
from cocos.layer import Layer, ColorLayer
from cocos.director import director
import pyglet

class HUD(Layer):
    is_event_handler = True

    def __init__(self):
        super(HUD, self).__init__()
        w, h = director.get_window_size()

        # Full-screen black overlay used for boss scene transitions.
        self.transition_overlay = ColorLayer(0, 0, 0, 0, width=w, height=h)
        self.add(self.transition_overlay, z=-1)

        self._transition_active = False
        self._transition_timer = 0.0
        self._transition_duration = 0.0
        self._transition_peak_alpha = 170
        self._restart_callback = None
        self._endgame_visible = False

        # ── Player HP ──────────────────────────────────────────────────────
        self.hp_label = Label(
            "HP: 200",
            font_name='Arial', font_size=16, bold=True,
            color=(255, 80, 80, 255),
            x=20, y=h - 30
        )

        # ── Score / Items ──────────────────────────────────────────────────
        self.score_label = Label(
            "Items: 0",
            font_name='Arial', font_size=16, bold=True,
            color=(255, 215, 0, 255),
            x=20, y=h - 55
        )

        # ── Progress ───────────────────────────────────────────────────────
        self.progress_label = Label(
            "Progress: 0%",
            font_name='Arial', font_size=14, bold=True,
            color=(100, 220, 255, 255),
            x=w / 2, y=h - 25,
            anchor_x='center'
        )

        # ── Boss Name ──────────────────────────────────────────────────────
        self.boss_name_label = Label(
            "",
            font_name='Arial', font_size=18, bold=True,
            color=(255, 60, 60, 255),
            x=w / 2, y=55,
            anchor_x='center'
        )

        # ── Boss HP bar (Progress Bar) ─────────────────────────────────────────────
        bg_img = pyglet.image.SolidColorImagePattern((80, 0, 0, 255)).create_image(400, 16)
        self.boss_hp_bg = cocos.sprite.Sprite(bg_img, anchor=(0, 0))
        self.boss_hp_bg.position = (w / 2 - 200, 30)
        self.boss_hp_bg.visible = False

        fg_img = pyglet.image.SolidColorImagePattern((255, 40, 40, 255)).create_image(400, 16)
        self.boss_hp_fg = cocos.sprite.Sprite(fg_img, anchor=(0, 0))
        self.boss_hp_fg.position = (w / 2 - 200, 30)
        self.boss_hp_fg.visible = False

        # ── Transition message (center screen) ────────────────────────────
        self.transition_label = Label(
            "",
            font_name='Arial', font_size=22, bold=True,
            color=(255, 230, 80, 255),
            x=w / 2, y=h / 2,
            anchor_x='center', anchor_y='center'
        )

        # ── Endgame overlay + restart button ──────────────────────────────
        self.endgame_overlay = ColorLayer(0, 0, 0, 180, width=w, height=h)
        self.endgame_overlay.visible = False

        self.endgame_label = Label(
            "",
            font_name='Arial', font_size=30, bold=True,
            color=(255, 255, 255, 255),
            x=w / 2, y=h / 2 + 70,
            anchor_x='center', anchor_y='center'
        )

        self.endgame_sub_label = Label(
            "",
            font_name='Arial', font_size=16, bold=False,
            color=(220, 220, 220, 255),
            x=w / 2, y=h / 2 + 30,
            anchor_x='center', anchor_y='center'
        )

        self.retry_button = ColorLayer(30, 140, 60, 255, width=220, height=56)
        self.retry_button.position = (w / 2 - 110, h / 2 - 28)
        self.retry_button.visible = False

        self.retry_label = Label(
            "CHOI LAI",
            font_name='Arial', font_size=18, bold=True,
            color=(255, 255, 255, 255),
            x=w / 2, y=h / 2,
            anchor_x='center', anchor_y='center'
        )
        self.retry_label.visible = False

        for lbl in (self.hp_label, self.score_label, self.progress_label,
                self.boss_name_label, self.transition_label):
            self.add(lbl)
            
        self.add(self.endgame_overlay, z=50)
        self.add(self.retry_button, z=60)
        self.add(self.endgame_label, z=70)
        self.add(self.endgame_sub_label, z=70)
        self.add(self.retry_label, z=70)
        self.add(self.boss_hp_bg)
        self.add(self.boss_hp_fg)
        self.schedule(self._update_transition)

    def _update_transition(self, dt):
        if not self._transition_active:
            return

        self._transition_timer += dt
        duration = max(0.01, self._transition_duration)
        progress = min(1.0, self._transition_timer / duration)

        if progress < 0.5:
            alpha = int(self._transition_peak_alpha * (progress / 0.5))
        else:
            alpha = int(self._transition_peak_alpha * (1.0 - (progress - 0.5) / 0.5))

        self.transition_overlay.opacity = max(0, min(255, alpha))

        if progress >= 1.0:
            self._transition_active = False
            self.transition_overlay.opacity = 0
            self.hide_transition()

    # ──────────────────────────────────────────────────────────────────────────
    def update_hp(self, hp):
        self.hp_label.element.text = f"HP: {max(0, hp)}"

    def update_score(self, score):
        self.score_label.element.text = f"Items: {score}"

    def update_progress(self, percent):
        self.progress_label.element.text = f"Progress: {int(min(percent, 100))}%"

    def update_boss_hp(self, hp, max_hp, name="BOSS"):
        self.boss_name_label.element.text = name
        
        if max_hp <= 0:
            return
            
        self.boss_hp_bg.visible = True
        self.boss_hp_fg.visible = True
        
        pct = max(0.0, min(1.0, float(hp) / max_hp))
        self.boss_hp_fg.scale_x = pct

    def boss_defeated(self, name="BOSS"):
        self.boss_name_label.element.text = f"{name} DEFEATED!"
        self.boss_hp_bg.visible = False
        self.boss_hp_fg.visible = False

    def show_transition(self, text):
        self.transition_label.element.text = text

    def hide_transition(self):
        self.transition_label.element.text = ""

    def play_screen_transition(self, text, duration=2.0, peak_alpha=170):
        self.show_transition(text)
        self._transition_active = True
        self._transition_timer = 0.0
        self._transition_duration = max(0.2, float(duration))
        self._transition_peak_alpha = max(0, min(255, int(peak_alpha)))

    def is_transition_playing(self):
        return self._transition_active

    def show_endgame(self, title, reason, on_restart=None):
        self._endgame_visible = True
        self._restart_callback = on_restart

        self.endgame_overlay.visible = True
        self.retry_button.visible = True
        self.retry_label.visible = True

        self.endgame_label.element.text = title
        self.endgame_sub_label.element.text = reason

    def hide_endgame(self):
        self._endgame_visible = False
        self.endgame_overlay.visible = False
        self.retry_button.visible = False
        self.retry_label.visible = False
        self.endgame_label.element.text = ""
        self.endgame_sub_label.element.text = ""

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self._endgame_visible:
            return False

        bx, by = self.retry_button.position
        bw = self.retry_button.width
        bh = self.retry_button.height
        in_button = bx <= x <= bx + bw and by <= y <= by + bh
        if in_button and callable(self._restart_callback):
            self._restart_callback()
            return True
        return False
