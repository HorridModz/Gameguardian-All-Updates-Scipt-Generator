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
from cli import main
from backend.logger import logging, LoggingLevel
from docopt import DocoptExit

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label


class CLIWrapper(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)

        # Input
        self.input = TextInput(hint_text='Enter command (enter --help for help)', multiline=False, size_hint_y=0.1)
        # Output
        self.output_box = BoxLayout(size_hint_y=None, orientation='vertical')
        self.output_label = Label(text='', markup=True, size_hint_y=None, halign='left', valign='top',
                                  color=(1, 1, 1, 1))
        self.output_label.bind(texture_size=self.update_label_height_and_width)
        self.output_box.add_widget(self.output_label)
        self.scroll = ScrollView(size_hint=(1, 0.8), do_scroll_x=False)
        self.scroll.add_widget(self.output_box)
        # Run Button
        self.run_button = Button(text='Run', size_hint_y=0.1)
        self.run_button.bind(on_press=self.run_cli)

        # Construct GUI from elements
        self.add_widget(Label(text='Gameguardian All Updates Script Generator', size_hint_y=0.1))
        self.add_widget(self.input)
        self.add_widget(self.run_button)
        self.add_widget(self.scroll)
        self.running = False

    def update_label_height_and_width(self, instance, size):
        # Stretch label to match scroll width
        self.output_label.text_size = (self.scroll.width - 20, None)
        self.output_label.size = self.output_label.texture_size
        self.output_box.height = self.output_label.height

    def run_cli(self, instance):
        if self.running:
            return
        if self.input.text.strip() == "":
            return
        self.running = True

        args = self.input.text.strip().split()

        captured_output = io.StringIO()
        sys_stdout = sys.stdout
        sys.stdout = captured_output

        try:
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

    @staticmethod
    def ansi_to_kivy_markup(text):
        ANSI_COLOR_MAP = {'30': '000000',  # black
                          '31': 'ff4444',  # red
                          '32': '44ff44',  # green
                          '33': 'ffff55',  # yellow
                          '34': '5599ff',  # blue
                          '35': 'ff55ff',  # magenta
                          '36': '55ffff',  # cyan
                          '37': 'ffffff',  # white
                          }

        def replace_color(match):
            code = match.group(1)
            return f"[color={ANSI_COLOR_MAP.get(code, 'ffffff')}]"

        # Replace ANSI color codes
        text = re.sub(r'\x1b\[([0-9]+)m', replace_color, text)
        text = text.replace('\x1b[0m', '[/color]')  # Reset code
        return text

class CLIApp(App):
    def build(self):
        return CLIWrapper()

if __name__ == '__main__':
    CLIApp().run()
