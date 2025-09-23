"""
A simple Android app that wraps the CLI in a GUI interface

Generated with ChatGPT's help
"""

# Add src to system path for relative imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import io
import re
import shlex
from cli import main, VERSION
from backend.logger import logging, LoggingLevel
from docopt import DocoptExit

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.text import Label as CoreLabel
from kivy.uix.image import Image


class CLIWrapper(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)

        # Header
        self.header = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        img = Image(source=self.image_path, size_hint_x=None)
        img.bind(on_texture=self.resize_image)
        label = Label(text=f"{VERSION} ~ https://github.com/HorridModz/Gameguardian-All-Updates-Scipt-Generator",
                      halign='left', valign='middle', size_hint_x=1, size_hint_y=None)
        label.bind(size=self.update_text_size, texture_size=self.update_label_height)
        # Set text_size width to the label’s width (to enable wrapping)
        label.text_size = (label.width, None)
        self.header.add_widget(img)
        self.header.add_widget(label)

        # Input
        self.input_scroll = ScrollView(size_hint_y=0.1, do_scroll_x=True, do_scroll_y=False,
                scroll_type=['bars', 'content'], bar_width=10, )
        self.input = TextInput(hint_text='Enter command (enter --help for help)', multiline=False, size_hint=(1, 1),
                width=1000, halign='left', font_size=16, cursor_width=1)
        self.input.size_hint_x = None
        self.input.width = max(self.input_scroll.width, 1000)
        self.input.bind(cursor=self.scroll_input_to_cursor)
        self.input_scroll.add_widget(self.input)
        # Output
        self.output_box = BoxLayout(size_hint_y=None, orientation='vertical')
        self.output_label = Label(text='', markup=True, size_hint_y=None, halign='left', valign='top',
                                  color=(1, 1, 1, 1))
        self.output_label.bind(texture_size=self.update_label_height_and_width)
        self.output_box.add_widget(self.output_label)
        self.scroll = self.scroll = ScrollView(size_hint=(1, 0.8),
                                               do_scroll_x=False,
                                               bar_width=10,
                                               scroll_type=['bars', 'content'],
                                               bar_color=(0.6, 0.6, 0.6, 1),
                                               bar_inactive_color=(0.3, 0.3, 0.3, 1), effect_cls='ScrollEffect')
        self.scroll.add_widget(self.output_box)
        # Run Button
        self.run_button = Button(text='Run', size_hint_y=0.1)
        self.run_button.bind(on_press=self.run_cli)

        # Construct GUI from elements

        self.add_widget(self.header)
        self.add_widget(self.input_scroll)
        self.add_widget(self.run_button)
        self.add_widget(self.scroll)
        self.running = False

    def scroll_input_to_cursor(self, *args):
        cursor_pos = self.input.cursor_pos[0]  # x position of cursor relative to TextInput
        sv_width = self.input_scroll.width
        ti_width = self.input.width

        if ti_width <= sv_width:
            self.input_scroll.scroll_x = 0  # No scrolling needed
            return

        # Compute scroll_x to keep cursor visible, bounded 0..1
        scrollable_width = ti_width - sv_width
        target_scroll_x = max(0, min(1, (cursor_pos - sv_width + 20) / scrollable_width))

        # Only update if scroll_x is significantly different to avoid jitter
        if abs(self.input_scroll.scroll_x - target_scroll_x) > 0.01:
            self.input_scroll.scroll_x = target_scroll_x

    def update_input_width(self, instance, text):
        # Measure text width using CoreLabel
        label = CoreLabel(text=text, font_size=self.input.font_size, font_name=self.input.font_name)
        label.refresh()
        width = label.texture.size[0] + 20  # Add padding
        self.input.width = max(self.input_scroll.width, width)

    def update_label_height_and_width(self, instance, size):
        # Stretch label to match scroll width
        self.output_label.text_size = (self.scroll.width - 20, None)
        self.output_label.size = self.output_label.texture_size
        self.output_box.height = self.output_label.height

    @staticmethod
    def resize_image(instance, value):
        instance.width = value[0]
        instance.height = value[1]

    @staticmethod
    def update_label_height(instance, value):
        instance.height = instance.texture_size[1]


    def update_text_size(self, instance, value):
        # Calculate available width for label: header width - image width - spacing
        header_width = self.header.width
        img_width = self.header.children[1].width
        spacing = self.header.spacing
        available_width = header_width - img_width - spacing
        instance.text_size = (available_width, None)

    def run_cli(self, instance):
        if self.running:
            return
        if self.input.text.strip() == "":
            return
        self.running = True
        captured_output = io.StringIO()
        sys_stdout = sys.stdout
        sys.stdout = captured_output

        try:
            args = shlex.split(self.input.text.strip())
            main(args)
        except DocoptExit as e:
            print(e)
        except SystemExit:
            pass
        except Exception as e:
            logging.warning(f"An error occurred: {e}", e.__class__, override=True)
        finally:
            sys.stdout = sys_stdout

        self.output_label.text = self.ansi_to_kivy_markup(captured_output.getvalue())
        self.running = False
    # noinspection IncorrectFormatting
    @staticmethod
    def ansi_to_kivy_markup(text):
        ANSI_COLOR_MAP = {'30': '000000',  # black
                '31':           'ff4444',  # red
                '32':           '44ff44',  # green
                '33':           'ffff55',  # yellow
                '34':           '5599ff',  # blue
                '35':           'ff55ff',  # magenta
                '36':           '55ffff',  # cyan
                '37':           'ffffff',  # white
                '90':           '888888',  # bright black (gray)
                '91':           'ff8888',  # bright red
                '92':           '88ff88',  # bright green
                '93':           'ffff88',  # bright yellow
                '94':           '88aaff',  # bright blue
                '95':           'ff88ff',  # bright magenta
                '96':           '88ffff',  # bright cyan
                '97':           'ffffff',  # bright white
        }

        def ansi_replacer(match):
            codes = match.group(1).split(';')
            color_code = next((c for c in reversed(codes) if c in ANSI_COLOR_MAP), None)
            if color_code:
                return f"[color={ANSI_COLOR_MAP[color_code]}]"
            else:
                return ''

        # Convert ANSI escape sequences to Kivy markup
        text = re.sub(r'\x1b\[([0-9;]+)m', ansi_replacer, text)
        text = text.replace('\x1b[0m', '[/color]')
        return text

    @property
    def image_path(self):
        from kivy.utils import platform
        if platform == "android":
            # Android APK (buildozer)
            return "resources/horridlogo.png"
        else:
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/horridlogo.png"))

class CLIApp(App):
    def build(self):
        self.title = "Gameguardian All Updates Script Generator"
        return CLIWrapper()

if __name__ == '__main__':
    CLIApp().run()
