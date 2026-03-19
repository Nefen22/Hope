import cocos
from cocos.text import Label
from cocos.layer import Layer
from cocos.director import director
import pyglet

class HUD(Layer):
    def __init__(self):
        super(HUD, self).__init__()
        w, h = director.get_window_size()

        # ── Player HP ──────────────────────────────────────────────────────
        self.hp_label = Label(
            "HP: 100",
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

        for lbl in (self.hp_label, self.score_label, self.progress_label,
                    self.boss_name_label, self.transition_label):
            self.add(lbl)
            
        self.add(self.boss_hp_bg)
        self.add(self.boss_hp_fg)

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
