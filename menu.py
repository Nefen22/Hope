"""
menu.py – Màn hình Menu chính dùng cocos.menu.Menu
Buttons: New Game | Options | About | Exit
"""
import cocos
import pyglet
from cocos.scene import Scene
from cocos.layer import ColorLayer, Layer
from cocos.director import director
from cocos.text import Label
import cocos.menu
from sound import SoundManager


# ─── Màn About ───────────────────────────────────────────────────────────────

class AboutLayer(ColorLayer):
    is_event_handler = True

    def __init__(self):
        super().__init__(10, 10, 30, 230)
        w, h = director.get_window_size()
        lines = [
            "HOPE – The Goblin Kingdom",
            "",
            "A side-scrolling action platformer.",
            "Fight through hordes of goblins,",
            "solve switch puzzles and defeat",
            "the Goblin King and the Minotaur!",
            "",
            "Controls:",
            "  Arrow Keys – Move",
            "  SPACE      – Jump",
            "  X          – Attack 1",
            "  C          – Attack 2",
            "  Z          – Dash",
            "",
            "Press ESC to go back.",
        ]
        for i, line in enumerate(lines):
            lbl = Label(
                line,
                font_name='Arial', font_size=15,
                color=(220, 220, 255, 255),
                x=w // 2, y=h - 80 - i * 26,
                anchor_x='center', anchor_y='center'
            )
            self.add(lbl)

    def on_enter(self):
        """Called when layer enters scene"""
        try:
            super().on_enter()
            director.window.push_handlers(self)
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def on_exit(self):
        """Called when layer exits scene"""
        director.window.pop_handlers()
        super().on_exit()

    def on_key_press(self, symbol, modifiers):
        try:
            if symbol == pyglet.window.key.ESCAPE:
                director.pop()
                return True
        except Exception as e:
            import traceback
            traceback.print_exc()
        return False
    
    def on_key_release(self, symbol, modifiers):
        return False


# ─── Màn Options ─────────────────────────────────────────────────────────────

class OptionsLayer(ColorLayer):
    is_event_handler = True

    def __init__(self):
        super().__init__(10, 30, 10, 230)
        
        w, h = director.get_window_size()

        self._bgm_vol   = SoundManager.bgm_volume
        self._sfx_vol   = SoundManager.sfx_volume

        self._lbl_title = Label("OPTIONS", font_name='Arial', font_size=28, bold=True,
                                color=(255, 200, 50, 255),
                                x=w // 2, y=h - 100, anchor_x='center')
        
        self._lbl_bgm = Label(self._bgm_text(), font_name='Arial', font_size=18,
                              color=(200, 220, 255, 255),
                              x=w // 2, y=h - 200, anchor_x='center')
        
        self._lbl_sfx = Label(self._sfx_text(), font_name='Arial', font_size=18,
                              color=(200, 220, 255, 255),
                              x=w // 2, y=h - 250, anchor_x='center')
        
        self._lbl_hint = Label("↑↓ Select  ←→ Adjust  ESC Back",
                               font_name='Arial', font_size=13,
                               color=(150, 150, 180, 255),
                               x=w // 2, y=60, anchor_x='center')
        
        for l in (self._lbl_title, self._lbl_bgm, self._lbl_sfx, self._lbl_hint):
            self.add(l)

        self._focus = 0   # 0=BGM, 1=SFX
        self._update_highlight()
        
        self._update_count = 0
        
    
    def on_enter(self):
        """Called when layer enters scene"""
        try:
            super().on_enter()
            director.window.push_handlers(self)
            
            self.schedule(self._update_loop)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def on_exit(self):
        """Called when layer exits scene"""
        try:
            director.window.pop_handlers()
            super().on_exit()
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _update_loop(self, dt):
        """Keep layer active - print counter every N frames"""
        try:
            self._update_count += 1
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _bgm_text(self):
        return f"BGM Volume: {'█' * int(self._bgm_vol * 10):10s} {int(self._bgm_vol * 100)}%"

    def _sfx_text(self):
        return f"SFX Volume: {'█' * int(self._sfx_vol * 10):10s} {int(self._sfx_vol * 100)}%"

    def _update_highlight(self):
        cols = [(255, 255, 80, 255), (200, 220, 255, 255)]
        try:
            self._lbl_bgm.color = cols[0] if self._focus == 0 else cols[1]
            self._lbl_sfx.color = cols[0] if self._focus == 1 else cols[1]
        except Exception as e:
            print(f"[ERROR] Update highlight failed: {e}")

    def on_key_press(self, symbol, modifiers):
        try:
            k = pyglet.window.key
            if symbol == k.ESCAPE:
                director.pop()
                return True
            try:
                if symbol == k.UP:
                    self._focus = 0
                    self._update_highlight()
                    return True
                elif symbol == k.DOWN:
                    self._focus = 1
                    self._update_highlight()
                    return True
                elif symbol == k.RIGHT:
                    if self._focus == 0:
                        self._bgm_vol = min(1.0, self._bgm_vol + 0.1)
                        SoundManager.set_bgm_volume(self._bgm_vol)
                        try:
                            self._lbl_bgm.element.text = self._bgm_text()
                        except:
                            pass
                    else:
                        self._sfx_vol = min(1.0, self._sfx_vol + 0.1)
                        SoundManager.sfx_volume = self._sfx_vol
                        try:
                            self._lbl_sfx.element.text = self._sfx_text()
                        except:
                            pass
                    return True
                elif symbol == k.LEFT:
                    if self._focus == 0:
                        self._bgm_vol = max(0.0, self._bgm_vol - 0.1)
                        SoundManager.set_bgm_volume(self._bgm_vol)
                        try:
                            self._lbl_bgm.element.text = self._bgm_text()
                        except:
                            pass
                    else:
                        self._sfx_vol = max(0.0, self._sfx_vol - 0.1)
                        SoundManager.sfx_volume = self._sfx_vol
                        try:
                            self._lbl_sfx.element.text = self._sfx_text()
                        except:
                            pass
                    return True
            except Exception as e:
                print(f"[ERROR] Key processing failed: {e}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"[ERROR] on_key_press outer exception: {e}")
            import traceback
            traceback.print_exc()
        return False
    
    def on_key_release(self, symbol, modifiers):
        return False


# ─── Background decorative layer cho menu ────────────────────────────────────

class MenuBG(ColorLayer):
    def __init__(self):
        super().__init__(8, 8, 24, 255)
        w, h = director.get_window_size()

        # Tiêu đề game
        title = Label(
            "HOPE",
            font_name='Arial', font_size=72, bold=True,
            color=(255, 180, 30, 255),
            x=w // 2, y=h - 120,
            anchor_x='center', anchor_y='center'
        )
        sub = Label(
            "The Goblin Kingdom",
            font_name='Arial', font_size=20,
            color=(180, 160, 120, 255),
            x=w // 2, y=h - 175,
            anchor_x='center', anchor_y='center'
        )
        self.add(title)
        self.add(sub)


# ─── Main Menu ────────────────────────────────────────────────────────────────

class MainMenu(cocos.menu.Menu):
    def __init__(self):
        super().__init__('')

        self.menu_valign   = cocos.menu.CENTER
        self.menu_halign   = cocos.menu.CENTER

        normal_style = {
            'font_name': 'Arial',
            'font_size': 28,
            'bold':      True,
            'color':     (200, 200, 220, 255),
        }
        selected_style = {
            'font_name': 'Arial',
            'font_size': 32,
            'bold':      True,
            'color':     (255, 220, 50, 255),
        }

        items = [
            cocos.menu.MenuItem('New Game', self.on_new_game),
            cocos.menu.MenuItem('Options',  self.on_options),
            cocos.menu.MenuItem('About',    self.on_about),
            cocos.menu.MenuItem('Exit',     self.on_exit),
        ]

        self.create_menu(items,
                         selected_effect=cocos.menu.zoom_in(),
                         unselected_effect=cocos.menu.zoom_out(),
                         layout_strategy=cocos.menu.fixedPositionMenuLayout(
                             self._positions()))

    def _positions(self):
        w, h = director.get_window_size()
        return [
            (w // 2, h // 2 + 60),
            (w // 2, h // 2),
            (w // 2, h // 2 - 60),
            (w // 2, h // 2 - 120),
        ]

    def on_new_game(self):
        try:
            SoundManager.play_sfx('menu_select')
        except Exception as e:
            print(f"[ERROR] play_sfx failed: {e}")
        try:
            from game import create_game_scene
            SoundManager.play_bgm('main')
            director.replace(create_game_scene())
        except Exception as e:
            import traceback
            traceback.print_exc()
            with open("crash.log", "w", encoding="utf-8") as f:
                f.write(str(e) + "\n")
                f.write(traceback.format_exc())
            import pyglet
            pyglet.app.exit()

    def on_options(self):
        try:
            SoundManager.play_sfx('menu_select')
        except Exception as e:
            print(f"[ERROR] play_sfx failed: {e}")
        try:
            layer = OptionsLayer()
            scene = Scene(layer)
            director.push(scene)
        except Exception as e:
            import traceback
            traceback.print_exc()
            with open("crash.log", "w", encoding="utf-8") as f:
                f.write(str(e) + "\n")
                f.write(traceback.format_exc())

    def on_about(self):
        try:
            SoundManager.play_sfx('menu_select')
        except Exception as e:
            print(f"[ERROR] play_sfx failed: {e}")
        try:
            layer = AboutLayer()
            scene = Scene(layer)
            director.push(scene)
        except Exception as e:
            import traceback
            traceback.print_exc()
            with open("crash.log", "w", encoding="utf-8") as f:
                f.write(str(e) + "\n")
                f.write(traceback.format_exc())

    def on_exit(self):
        import pyglet
        pyglet.app.exit()

# ─── Tạo Scene Menu ───────────────────────────────────────────────────────────

def create_menu_scene():
    scene = Scene()
    scene.add(MenuBG(),   z=0)
    scene.add(MainMenu(), z=1)
    return scene
