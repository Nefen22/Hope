import cocos
from cocos.text import Label
from cocos.layer import Layer, ColorLayer
from cocos.director import director
from cocos.scene import Scene
import pyglet

class MainMenu(Layer):
    is_event_handler = True

    def __init__(self):
        super(MainMenu, self).__init__()
        w, h = director.get_window_size()

        # Background
        self.bg = ColorLayer(20, 20, 40, 255, width=w, height=h)
        self.add(self.bg, z=0)

        # Game Title
        self.title_label = Label(
            "HOPE",
            font_name='Arial', font_size=48, bold=True,
            color=(255, 215, 0, 255),
            x=w / 2, y=h - 100,
            anchor_x='center', anchor_y='center'
        )
        self.add(self.title_label, z=10)

        self.subtitle_label = Label(
            "Goblin King & Minotaur",
            font_name='Arial', font_size=20, bold=False,
            color=(200, 200, 200, 255),
            x=w / 2, y=h - 140,
            anchor_x='center', anchor_y='center'
        )
        self.add(self.subtitle_label, z=10)

        # Menu buttons
        self.button_width = 250
        self.button_height = 50
        self.button_spacing = 70
        self.start_y = h // 2 + 50

        self.buttons = {}
        self.button_labels = {}
        
        button_texts = [
            ("NEW GAME", self.start_new_game),
            ("OPTIONS", self.show_options),
            ("ABOUT", self.show_about),
            ("EXIT", self.exit_game)
        ]

        for i, (text, callback) in enumerate(button_texts):
            y_pos = self.start_y - (i * self.button_spacing)
            
            # Button background
            button = ColorLayer(60, 120, 60, 255, width=self.button_width, height=self.button_height)
            button.position = (w // 2 - self.button_width // 2, y_pos - self.button_height // 2)
            self.add(button, z=5)
            self.buttons[text] = button

            # Button text
            label = Label(
                text,
                font_name='Arial', font_size=18, bold=True,
                color=(255, 255, 255, 255),
                x=w // 2, y=y_pos,
                anchor_x='center', anchor_y='center'
            )
            self.add(label, z=10)
            self.button_labels[text] = label

        # Store callbacks
        self.callbacks = {text: callback for text, callback in button_texts}
        
        # Highlight effect
        self.selected_button = None
        self.original_colors = {}

    def on_mouse_motion(self, x, y, dx, dy):
        """Handle mouse hover effects"""
        w, h = director.get_window_size()
        
        for text, button in self.buttons.items():
            bx, by = button.position
            bw, bh = button.width, button.height
            
            in_button = bx <= x <= bx + bw and by <= y <= by + bh
            
            if in_button:
                if self.selected_button != text:
                    # Reset previous button
                    if self.selected_button and self.selected_button in self.buttons:
                        self.buttons[self.selected_button].color = (60, 120, 60)
                    
                    # Highlight new button
                    button.color = (80, 160, 80)
                    self.selected_button = text
            elif self.selected_button == text:
                button.color = (60, 120, 60)
                self.selected_button = None

    def on_mouse_press(self, x, y, buttons, modifiers):
        """Handle button clicks"""
        if buttons & pyglet.window.mouse.LEFT:
            for text, button in self.buttons.items():
                bx, by = button.position
                bw, bh = button.width, button.height
                
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    if text in self.callbacks:
                        self.callbacks[text]()
                    return True
        return False

    def start_new_game(self):
        """Start a new game"""
        from game import build_game_scene
        director.replace(build_game_scene())

    def show_options(self):
        """Show options menu"""
        director.replace(OptionsMenu.get_scene())

    def show_about(self):
        """Show about menu"""
        director.replace(AboutMenu.get_scene())

    def exit_game(self):
        """Exit the game"""
        director.window.close()

    @staticmethod
    def get_scene():
        """Create and return a scene with the main menu"""
        scene = Scene()
        menu_layer = MainMenu()
        scene.add(menu_layer, z=1)
        return scene


class OptionsMenu(Layer):
    is_event_handler = True

    def __init__(self):
        super(OptionsMenu, self).__init__()
        w, h = director.get_window_size()

        # Background
        self.bg = ColorLayer(20, 20, 40, 255, width=w, height=h)
        self.add(self.bg, z=0)

        # Title
        self.title_label = Label(
            "OPTIONS",
            font_name='Arial', font_size=36, bold=True,
            color=(255, 215, 0, 255),
            x=w / 2, y=h - 80,
            anchor_x='center', anchor_y='center'
        )
        self.add(self.title_label, z=10)

        # Back button
        self.back_button = ColorLayer(120, 60, 60, 255, width=200, height=40)
        self.back_button.position = (w // 2 - 100, 50)
        self.add(self.back_button, z=5)

        self.back_label = Label(
            "BACK",
            font_name='Arial', font_size=16, bold=True,
            color=(255, 255, 255, 255),
            x=w // 2, y=70,
            anchor_x='center', anchor_y='center'
        )
        self.add(self.back_label, z=10)

        # Options content
        self.options_text = Label(
            "Game Options:\n\n"
            "• Use Arrow Keys or WASD to move\n"
            "• Press SPACE to attack\n"
            "• Collect coins for score\n"
            "• Avoid or defeat enemies\n"
            "• Reach the boss area to progress\n\n"
            "Tips:\n"
            "• Jump on enemies' heads to defeat them\n"
            "• Break blocks for power-ups\n"
            "• Stay alive during boss fights!",
            font_name='Arial', font_size=14, bold=False,
            color=(220, 220, 220, 255),
            x=w // 2, y=h // 2,
            anchor_x='center', anchor_y='center',
            width=w - 100, multiline=True, align='center'
        )
        self.add(self.options_text, z=10)

    def on_mouse_press(self, x, y, buttons, modifiers):
        """Handle back button click"""
        if buttons & pyglet.window.mouse.LEFT:
            bx, by = self.back_button.position
            bw, bh = self.back_button.width, self.back_button.height
            
            if bx <= x <= bx + bw and by <= y <= by + bh:
                director.replace(MainMenu.get_scene())
                return True
        return False

    @staticmethod
    def get_scene():
        """Create and return a scene with the options menu"""
        scene = Scene()
        options_layer = OptionsMenu()
        scene.add(options_layer, z=1)
        return scene


class AboutMenu(Layer):
    is_event_handler = True

    def __init__(self):
        super(AboutMenu, self).__init__()
        w, h = director.get_window_size()

        # Background
        self.bg = ColorLayer(20, 20, 40, 255, width=w, height=h)
        self.add(self.bg, z=0)

        # Title
        self.title_label = Label(
            "ABOUT",
            font_name='Arial', font_size=36, bold=True,
            color=(255, 215, 0, 255),
            x=w / 2, y=h - 80,
            anchor_x='center', anchor_y='center'
        )
        self.add(self.title_label, z=10)

        # Back button
        self.back_button = ColorLayer(120, 60, 60, 255, width=200, height=40)
        self.back_button.position = (w // 2 - 100, 50)
        self.add(self.back_button, z=5)

        self.back_label = Label(
            "BACK",
            font_name='Arial', font_size=16, bold=True,
            color=(255, 255, 255, 255),
            x=w // 2, y=70,
            anchor_x='center', anchor_y='center'
        )
        self.add(self.back_label, z=10)

        # About content
        self.about_text = Label(
            "HOPE - Goblin King & Minotaur\n\n"
            "Version 1.0\n\n"
            "A 2D platformer adventure game\n"
            "where you journey through dangerous lands\n"
            "to defeat powerful bosses.\n\n"
            "Features:\n"
            "• Multiple enemy types\n"
            "• Epic boss battles\n"
            "• Power-ups and collectibles\n"
            "• Progressive difficulty\n\n"
            "Created with Python and Cocos2d\n"
            "© 2024 Game Development Project",
            font_name='Arial', font_size=14, bold=False,
            color=(220, 220, 220, 255),
            x=w // 2, y=h // 2,
            anchor_x='center', anchor_y='center',
            width=w - 100, multiline=True, align='center'
        )
        self.add(self.about_text, z=10)

    def on_mouse_press(self, x, y, buttons, modifiers):
        """Handle back button click"""
        if buttons & pyglet.window.mouse.LEFT:
            bx, by = self.back_button.position
            bw, bh = self.back_button.width, self.back_button.height
            
            if bx <= x <= bx + bw and by <= y <= by + bh:
                director.replace(MainMenu.get_scene())
                return True
        return False

    @staticmethod
    def get_scene():
        """Create and return a scene with the about menu"""
        scene = Scene()
        about_layer = AboutMenu()
        scene.add(about_layer, z=1)
        return scene
